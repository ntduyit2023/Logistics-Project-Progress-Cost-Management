"""
Unit tests cho Tích hợp Đa Loại hình Dự án & Joint Multi-Graph Batching (GLPO):
  1. EncoderRegistry DB Type Mapping (ITLG, CON, PRO)
  2. Data Loader project_meta.json Parsing
  3. Joint Multi-Graph Batching với PyTorch Geometric
"""

import os
import sys
import torch
import json
import tempfile
import shutil

# Ensure ai_pipeline is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.project_encoders import EncoderRegistry
from ai_pipeline.models.data_loader import GlPoProjectGraph, GlPoDataset
from ai_pipeline.models.sequential_glpo_model import SequentialGLPOModel
from torch_geometric.data import Data, Batch


def test_encoder_registry_db_mapping():
    """Test 1: Kiểm tra ánh xạ mã DB (ITLG, CON, PRO) trong EncoderRegistry."""
    db_types = ['ITLG', 'CON', 'PRO', 'it_logistics', 'civil_construction', 'professional_services']
    
    for db_type in db_types:
        encoder, num_groups = EncoderRegistry.get_encoder(db_type, latent_dim=64)
        assert encoder is not None, f"Encoder for {db_type} should not be None"
        assert num_groups == 8, f"num_groups for {db_type} should be 8, got {num_groups}"
        
        # Check forward pass
        dummy_x = torch.randn(10, 36)
        out = encoder(dummy_x)
        assert out.shape == (10, 64), f"Encoder output shape for {db_type} must be (10, 64), got {out.shape}"
        
    print("  [OK] test_encoder_registry_db_mapping PASSED")


def test_project_meta_loading():
    """Test 2: GlPoProjectGraph nạp đúng project_type từ project_meta.json."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create dummy tasks.csv and predecessors.csv
        tasks_csv = os.path.join(temp_dir, 'tasks.csv')
        with open(tasks_csv, 'w', encoding='utf-8') as f:
            f.write("id,task_name,duration_days,internal_labor_cost\n1,Task 1,5,1000\n2,Task 2,10,2000\n")
            
        preds_csv = os.path.join(temp_dir, 'predecessors.csv')
        with open(preds_csv, 'w', encoding='utf-8') as f:
            f.write("predecessor_task_id,successor_task_id\n1,2\n")
            
        meta_json = os.path.join(temp_dir, 'project_meta.json')
        with open(meta_json, 'w', encoding='utf-8') as f:
            json.dump({"project_id": "test_proj", "project_type": "civil_construction"}, f)
            
        graph = GlPoProjectGraph(temp_dir)
        assert graph.project_type == "civil_construction", f"Expected project_type 'civil_construction', got '{graph.project_type}'"
        print("  [OK] test_project_meta_loading PASSED")
    finally:
        shutil.rmtree(temp_dir)


def test_joint_multigraph_batching():
    """Test 3: Joint Multi-Graph Batching gộp nhiều đồ thị dự án thành Siêu Đồ Thị PyG."""
    # Build 3 dummy PyG graphs
    g1 = Data(x=torch.randn(5, 36), edge_index=torch.tensor([[0, 1], [1, 2]], dtype=torch.long), edge_attr=torch.randn(2, 8))
    g2 = Data(x=torch.randn(8, 36), edge_index=torch.tensor([[0, 2], [1, 3]], dtype=torch.long), edge_attr=torch.randn(2, 8))
    g3 = Data(x=torch.randn(12, 36), edge_index=torch.tensor([[0, 4], [2, 5]], dtype=torch.long), edge_attr=torch.randn(2, 8))
    
    batch_data = Batch.from_data_list([g1, g2, g3])
    
    assert batch_data.num_nodes == 5 + 8 + 12 # 25 nodes
    assert batch_data.num_edges == 6
    
    # Model forward pass on batched data
    model = SequentialGLPOModel(project_type="civil_construction", gat_hidden_dim=64, gat_out_dim=32, dagnn_out_dim=32)
    out = model(batch_data)
    
    assert out['node_embeddings'].shape == (25, 32)
    assert not torch.isnan(out['node_embeddings']).any()
    print("  [OK] test_joint_multigraph_batching PASSED")


if __name__ == "__main__":
    print("=== Running Multi-Type & Multi-Graph Batching Unit Tests ===")
    test_encoder_registry_db_mapping()
    test_project_meta_loading()
    test_joint_multigraph_batching()
    print("\n[SUCCESS] ALL MULTI-TYPE INTEGRATION UNIT TESTS PASSED SUCCESSFULLY!")
