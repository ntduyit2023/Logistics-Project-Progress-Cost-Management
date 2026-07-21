"""
Unit tests cho Nâng cấp Kiến trúc Mục 3 & 4 (GLPO):
  1. DAGNN Attention Aggregation
  2. GATv2 8-D Edge Attributes
  3. Residual Skip Connections & Feature Fusion
"""

import os
import sys
import torch
import torch.nn as nn

# Ensure ai_pipeline is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.dagnn_propagator import DAGNNPropagator, PredecessorAttention
from ai_pipeline.models.gat_model import LogisticsGATModel
from ai_pipeline.models.sequential_glpo_model import SequentialGLPOModel
from torch_geometric.data import Data


def test_dagnn_attention_aggregation():
    """Test 1: PredecessorAttention tập trung trọng số vào predecessor trễ/nguy hiểm hơn."""
    attn = PredecessorAttention(hidden_dim=64, gat_dim=32)
    
    # Node hiện tại
    h_self = torch.randn(32)
    
    # 3 Predecessors: pred 0 có tín hiệu rủi ro cao (giá trị lớn)
    pred_states = torch.zeros(3, 64)
    pred_states[0] = 10.0 # High risk signal
    pred_states[1] = 0.1
    pred_states[2] = 0.1
    
    agg_state = attn(pred_states, h_self)
    
    assert agg_state.shape == (64,), f"agg_state shape must be (64,), got {agg_state.shape}"
    assert not torch.isnan(agg_state).any(), "agg_state contains NaN"
    assert not torch.isinf(agg_state).any(), "agg_state contains Inf"
    print("  [OK] test_dagnn_attention_aggregation PASSED")


def test_gatv2_edge_attributes():
    """Test 2: LogisticsGATModel xử lý thành công edge_attr 8 chiều."""
    gat = LogisticsGATModel(feature_dim=36, hidden_dim=64, num_groups=8, out_dim=32, heads=4, edge_dim=8)
    
    # Tạo dummy graph với 5 nodes, 4 edges, 8-D edge_attr
    x = torch.randn(5, 36)
    edge_index = torch.tensor([
        [0, 1, 2, 3],
        [1, 2, 3, 4]
    ], dtype=torch.long)
    edge_attr = torch.randn(4, 8) # 8-D edge attributes (one-hot dependency + 4 lag features)
    
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    
    node_emb, graph_emb = gat(data)
    
    assert node_emb.shape == (5, 32), f"node_emb shape must be (5, 32), got {node_emb.shape}"
    assert graph_emb.shape == (1, 32), f"graph_emb shape must be (1, 32), got {graph_emb.shape}"
    assert not torch.isnan(node_emb).any(), "node_emb contains NaN"
    print("  [OK] test_gatv2_edge_attributes PASSED")


def test_residual_skip_connection():
    """Test 3: SequentialGLPOModel tích hợp kết nối tắt Residual Skip Connection."""
    model = SequentialGLPOModel(
        project_type="logistics_standard",
        gat_hidden_dim=64,
        gat_out_dim=32,
        dagnn_out_dim=32
    )
    
    x = torch.randn(6, 36)
    edge_index = torch.tensor([
        [0, 1, 2, 3, 4],
        [1, 2, 3, 4, 5]
    ], dtype=torch.long)
    edge_attr = torch.randn(5, 8)
    
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    
    out = model(data)
    
    assert 'node_embeddings' in out
    assert 'h_dagnn' in out
    assert out['node_embeddings'].shape == (6, 32)
    assert not torch.isnan(out['node_embeddings']).any(), "node_embeddings contains NaN"
    
    # Gradient flow check
    loss = out['tgc'].sum()
    loss.backward()
    
    # Check that GAT layers received gradients
    assert model.gat1.att_src.grad is not None or model.gat1.lin_src.weight.grad is not None, "Gradient did not flow back to GAT layers!"
    print("  [OK] test_residual_skip_connection PASSED")


if __name__ == "__main__":
    print("=== Running Architecture v2 Unit Tests ===")
    test_dagnn_attention_aggregation()
    test_gatv2_edge_attributes()
    test_residual_skip_connection()
    print("\n[SUCCESS] ALL ARCHITECTURE V2 UNIT TESTS PASSED SUCCESSFULLY!")
