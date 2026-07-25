"""
Heterogeneous Graph Transformer (HGT Core Model - Enhanced Architecture)
===========================================================================
Thư mục: ai_pipeline/models/moi/hgt_model.py

Chức năng:
    Mô hình GNN dị thể (HGT) xử lý 4 loại nút (task, resource, time_agenda, project)
    Hỗ trợ 128-dim hidden representation, GELU activations, LayerNorm & Residual Connections.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, GATConv, Linear


class HGTTaskPredictor(nn.Module):
    """
    Mô hình Heterogeneous Graph Transformer nâng cấp (128-dim latent space).
    """
    def __init__(self, in_channels_dict, hidden_dim=128, num_heads=4, num_layers=2):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # 1. Linear Projection cho từng loại nút đưa về hidden_dim = 128
        self.proj_dict = nn.ModuleDict()
        for node_type, in_dim in in_channels_dict.items():
            self.proj_dict[node_type] = nn.Sequential(
                Linear(in_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU()
            )
            
        # 2. HeteroConv / GATConv cho từng quan hệ đồ thị
        self.layers = nn.ModuleList()
        for _ in range(num_layers):
            conv_dict = {
                ('task', 'precedes', 'task'): GATConv(hidden_dim, hidden_dim // num_heads, heads=num_heads, concat=True, add_self_loops=False),
                ('task', 'uses', 'resource'): GATConv(hidden_dim, hidden_dim // num_heads, heads=num_heads, concat=True, add_self_loops=False),
                ('task', 'constrained_by', 'time_agenda'): GATConv(hidden_dim, hidden_dim // num_heads, heads=num_heads, concat=True, add_self_loops=False),
                ('task', 'belongs_to', 'project'): GATConv(hidden_dim, hidden_dim // num_heads, heads=num_heads, concat=True, add_self_loops=False)
            }
            self.layers.append(HeteroConv(conv_dict, aggr='sum'))
            
        # 3. Task Decoder Head (Dự đoán 3 đầu ra)
        self.task_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            Linear(hidden_dim, 3) # [duration_factor, expected_delay, uncertainty_sigma]
        )
        
        # 4. Feature Reconstruction Head cho Masked Autoencoder (Phase 0) với LayerNorm & GELU
        task_in_dim = in_channels_dict.get('task', 72)
        self.recon_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            Linear(hidden_dim, task_in_dim)
        )

    def forward(self, x_dict, edge_index_dict):
        # Biến đổi tuyến tính đầu vào
        h_dict = {}
        for node_type, x in x_dict.items():
            if node_type in self.proj_dict:
                h_dict[node_type] = self.proj_dict[node_type](x)
            else:
                h_dict[node_type] = x
                
        # Lan truyền thông điệp HeteroConv với Residual Connection
        for layer in self.layers:
            out_h_dict = layer(h_dict, edge_index_dict)
            for node_type, h in out_h_dict.items():
                h_dict[node_type] = F.gelu(h + h_dict[node_type])
                
        # Trích xuất biểu diễn nút Task
        task_embed = h_dict['task']
        preds = self.task_head(task_embed)
        reconstructed_x = self.recon_head(task_embed)
        
        duration_factor = F.softplus(preds[:, 0]) + 0.5 # Khoảng [0.5, inf)
        expected_delay = F.relu(preds[:, 1])            # >= 0
        uncertainty_sigma = F.softplus(preds[:, 2]) + 0.01 # > 0
        
        return {
            'duration_factor': duration_factor,
            'expected_delay': expected_delay,
            'uncertainty_sigma': uncertainty_sigma,
            'task_embeddings': task_embed,
            'reconstructed_x': reconstructed_x
        }
