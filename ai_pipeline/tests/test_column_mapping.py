"""
Unit tests cho DataValidator, Column Mapping, FeatureNormalizer và HierarchicalAttentionEncoder.
"""
import os
import sys
import tempfile
import pandas as pd
import torch

# Ensure ai_pipeline is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.data_validator import ProjectDataValidator, ValidationReport
from ai_pipeline.models.data_loader import GlPoProjectGraph, COLUMN_ALIASES, _get_col
from ai_pipeline.models.feature_normalizer import FeatureNormalizer
from ai_pipeline.models.hierarchical_encoder import HierarchicalAttentionEncoder


def test_column_mapping_aliases():
    """Kiểm tra helper _get_col trích xuất đúng giá trị từ cả CSV gốc và DB-style."""
    row_csv = {
        'g1_labor': 1920.0,
        'g1_material': 4500.0,
        'g7_dur_months': 2.0,
        'g5_complexity': 0.3
    }
    row_db = {
        'internal_labor_cost': 1920.0,
        'material_cost': 4500.0,
        'duration_months': 2.0,
        'complexity': 0.3
    }
    
    assert _get_col(row_csv, 'internal_labor_cost') == 1920.0
    assert _get_col(row_db, 'internal_labor_cost') == 1920.0
    assert _get_col(row_csv, 'material_cost') == 4500.0
    assert _get_col(row_db, 'material_cost') == 4500.0
    assert _get_col(row_csv, 'duration_months') == 2.0
    assert _get_col(row_db, 'duration_months') == 2.0
    assert _get_col(row_csv, 'complexity') == 0.3
    assert _get_col(row_db, 'complexity') == 0.3
    assert _get_col(row_csv, 'non_existent_col', default=99.0) == 99.0


def test_c2019_16_non_zero_features():
    """Kiểm tra dự án C2019-16 thực tế không bị load 0.0 cho cost features."""
    c2019_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed', 'C2019-16')
    if os.path.exists(c2019_dir):
        graph = GlPoProjectGraph(c2019_dir)
        x = graph.data.x # [32 tasks, 36 dim]
        
        # Internal labor cost (col 5) của Task 1 (g1_labor = 1920.0)
        assert x[0, 5].item() == 1920.0, f"Task 1 labor cost = {x[0, 5].item()}, expected 1920.0"
        
        # Material cost (col 9) của Task 3 (g1_material = 4500.0)
        assert x[2, 9].item() == 4500.0, f"Task 3 material cost = {x[2, 9].item()}, expected 4500.0"
        
        # Verify feature vector is not all zeros for costs
        costs = x[:, 5:27]
        total_costs = float(torch.sum(torch.abs(costs)))
        assert total_costs > 0.0, "Cost features should NOT be all zeros!"
        print(f"   * C2019-16 Non-zero cost check PASSED! Sum of costs = ${total_costs:,.2f}")


def test_validator_detects_self_loop():
    """Kiểm tra validator phát hiện và xóa self-loop."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tasks_df = pd.DataFrame([
            {'task_id': '1', 'task_name': 'Task 1', 'g7_dur_days': 1.0},
            {'task_id': '2', 'task_name': 'Task 2', 'g7_dur_days': 2.0}
        ])
        edges_df = pd.DataFrame([
            {'predecessor_task_id': '1', 'successor_task_id': '2'},
            {'predecessor_task_id': '1', 'successor_task_id': '1'} # Self-loop
        ])
        
        tasks_df.to_csv(os.path.join(tmp_dir, 'tasks.csv'), index=False)
        edges_df.to_csv(os.path.join(tmp_dir, 'predecessors.csv'), index=False)
        
        validator = ProjectDataValidator()
        report = validator.validate(tmp_dir)
        
        assert report.is_valid is True
        assert len(report.warnings) > 0
        assert any("self-loop" in w.lower() for w in report.warnings)
        assert len(report.sanitized_edges_df) == 1


def test_validator_detects_cycle():
    """Kiểm tra validator phát hiện và gỡ chu trình (1->2->3->1)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tasks_df = pd.DataFrame([
            {'task_id': '1', 'task_name': 'Task 1', 'g7_dur_days': 1.0},
            {'task_id': '2', 'task_name': 'Task 2', 'g7_dur_days': 2.0},
            {'task_id': '3', 'task_name': 'Task 3', 'g7_dur_days': 3.0}
        ])
        edges_df = pd.DataFrame([
            {'predecessor_task_id': '1', 'successor_task_id': '2'},
            {'predecessor_task_id': '2', 'successor_task_id': '3'},
            {'predecessor_task_id': '3', 'successor_task_id': '1'} # Cycle!
        ])
        
        tasks_df.to_csv(os.path.join(tmp_dir, 'tasks.csv'), index=False)
        edges_df.to_csv(os.path.join(tmp_dir, 'predecessors.csv'), index=False)
        
        validator = ProjectDataValidator()
        report = validator.validate(tmp_dir)
        
        assert report.is_valid is True
        assert any("chu tr" in w.lower() or "cycle" in w.lower() for w in report.warnings)
        assert len(report.sanitized_edges_df) < 3


def test_feature_normalizer_and_encoder():
    """Kiểm tra FeatureNormalizer và HierarchicalAttentionEncoder không bị NaN/Inf."""
    norm = FeatureNormalizer(feature_dim=36)
    encoder = HierarchicalAttentionEncoder(feature_dim=36, num_groups=8)
    
    # Random raw features with high costs (1e6)
    x = torch.rand((10, 36)) * 100.0
    x[:, 5] = 1_000_000.0 # High internal labor cost
    
    x_norm = norm(x)
    assert not torch.isnan(x_norm).any(), "Normalized output contains NaN"
    assert not torch.isinf(x_norm).any(), "Normalized output contains Inf"
    
    s_g, mask = encoder(x)
    assert s_g.shape == (10, 8)
    assert not torch.isnan(s_g).any(), "Encoder output S_g contains NaN"
    assert not torch.isinf(s_g).any(), "Encoder output S_g contains Inf"


if __name__ == "__main__":
    print("=== Running Unit Tests ===")
    test_column_mapping_aliases()
    print("  [OK] test_column_mapping_aliases PASSED")
    test_c2019_16_non_zero_features()
    print("  [OK] test_c2019_16_non_zero_features PASSED")
    test_validator_detects_self_loop()
    print("  [OK] test_validator_detects_self_loop PASSED")
    test_validator_detects_cycle()
    print("  [OK] test_validator_detects_cycle PASSED")
    test_feature_normalizer_and_encoder()
    print("  [OK] test_feature_normalizer_and_encoder PASSED")
    print("\n[SUCCESS] ALL UNIT TESTS PASSED SUCCESSFULLY!")
