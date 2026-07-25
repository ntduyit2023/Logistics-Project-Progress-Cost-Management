"""
Native Heterogeneous Graph Transformer (HGT Core Model with HGTConv)
====================================================================
Thư mục: ai_pipeline/models/moi/hgt_model.py

Chức năng:
    Mô hình Heterogeneous Graph Transformer (HGT) native xử lý 4 loại nút:
        - Nút: ['task', 'resource', 'time_agenda', 'project']
        - Cạnh quan hệ:
            - ('task', 'precedes', 'task')
            - ('task', 'uses', 'resource')
            - ('task', 'constrained_by', 'time_agenda')
            - ('task', 'belongs_to', 'project')
    
    Sử dụng lớp toán học PyTorch Geometric HGTConv với ma trận Query/Key/Value & Relation Attention riêng biệt cho từng loại thực thể.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HGTConv, Linear


class HGTTaskPredictor(nn.Module):
    """
    Mô hình Native Heterogeneous Graph Transformer (HGTConv).
    """
    def __init__(self, in_channels_dict, hidden_dim=128, num_heads=4, num_layers=2):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # Metadata Đồ thị Dị thể (4 Node Types, 4 Edge Relation Triplets)
        node_types = ['task', 'resource', 'time_agenda', 'project']
        edge_types = [
            ('task', 'precedes', 'task'),
            ('task', 'uses', 'resource'),
            ('task', 'constrained_by', 'time_agenda'),
            ('task', 'belongs_to', 'project')
        ]
        self.metadata = (node_types, edge_types)
        
        # 1. Linear Projection cho từng loại nút đưa về hidden_dim = 128
        self.proj_dict = nn.ModuleDict()
        for node_type in node_types:
            in_dim = in_channels_dict.get(node_type, 72 if node_type == 'task' else 4)
            self.proj_dict[node_type] = nn.Sequential(
                Linear(in_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU()
            )
            
        # 2. Native HGTConv Layers (Chuyên biệt cho Heterogeneous Graph Transformer)
        self.hgt_layers = nn.ModuleList()
        for _ in range(num_layers):
            self.hgt_layers.append(
                HGTConv(hidden_dim, hidden_dim, metadata=self.metadata, heads=num_heads)
            )
            
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
        # 1. Biến đổi tuyến tính ban đầu cho từng loại nút
        h_dict = {}
        for node_type, x in x_dict.items():
            if node_type in self.proj_dict:
                h_dict[node_type] = self.proj_dict[node_type](x)
            else:
                h_dict[node_type] = x
                
        # 2. Native HGT Attention Message Passing với Residual Connection
        for hgt_layer in self.hgt_layers:
            out_h_dict = hgt_layer(h_dict, edge_index_dict)
            for node_type, h in out_h_dict.items():
                if node_type in h_dict:
                    h_dict[node_type] = F.gelu(h + h_dict[node_type])
                else:
                    h_dict[node_type] = F.gelu(h)
                
        # 3. Trích xuất biểu diễn nút Task
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
