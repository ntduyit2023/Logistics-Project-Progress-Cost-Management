"""
Native Heterogeneous Graph Transformer với Hybrid Readout Pooling (Mean + Max)
==============================================================================
Thư mục: ai_pipeline/models/moi/hgt_model.py

Chức năng:
    Mô hình Heterogeneous Graph Transformer (HGT) tinh gọn xử lý 3 loại nút:
        - Nút: ['task', 'resource', 'shift']
        - Cạnh quan hệ:
            - ('task', 'precedes', 'task')
            - ('task', 'uses', 'resource')
            - ('task', 'constrained_by', 'shift')
    
    Tích hợp tầng Hybrid Readout Pooling (Mean + Max Pooling) gom ngữ cảnh dự án toàn cục
    và lớp toán học PyTorch Geometric HGTConv.
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
        
        # Metadata Đồ thị Dị thể Tinh gọn (3 Node Types: task, resource, shift)
        node_types = ['task', 'resource', 'shift']
        edge_types = [
            ('task', 'precedes', 'task'),
            ('task', 'uses', 'resource'),
            ('task', 'constrained_by', 'shift')
        ]
        self.metadata = (node_types, edge_types)
        
        # 1. Linear Projection cho từng loại nút đưa về hidden_dim = 128
        self.proj_dict = nn.ModuleDict()
        for node_type in node_types:
            default_dim = 39 if node_type == 'task' else (6 if node_type == 'resource' else 5)
            in_dim = in_channels_dict.get(node_type, default_dim)
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
            
        # 3. Layer Fusion kết hợp Task Embeddings với Global Project Context (Hybrid Mean + Max Pooling)
        self.fusion_layer = nn.Sequential(
            Linear(hidden_dim * 3, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU()
        )

        # 4. Task Decoder Head (Dự đoán 3 đầu ra)
        self.task_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            Linear(hidden_dim, 3) # [duration_factor, expected_delay, uncertainty_sigma]
        )
        
        # 5. Feature Reconstruction Head cho Masked Autoencoder (Phase 0) với LayerNorm & GELU
        task_in_dim = in_channels_dict.get('task', 39)
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

        # 4. Global Readout Pooling (Hybrid Mean + Max Pooling) tổng hợp Ngữ cảnh Dự án
        if task_embed.size(0) > 0:
            mean_pool = torch.mean(task_embed, dim=0, keepdim=True)
            max_pool, _ = torch.max(task_embed, dim=0, keepdim=True)
            global_context = torch.cat([mean_pool, max_pool], dim=-1) # [1, 2 * hidden_dim]
        else:
            global_context = torch.zeros((1, 2 * self.hidden_dim), dtype=task_embed.dtype, device=task_embed.device)

        # 5. Hợp nhất Ngữ cảnh Toàn cục (Global Context) vào từng Nút Công việc
        global_context_expanded = global_context.expand(task_embed.size(0), -1)
        fused_task_embed = torch.cat([task_embed, global_context_expanded], dim=-1) # [N, 3 * hidden_dim]
        fused_task_embed = self.fusion_layer(fused_task_embed)                     # [N, hidden_dim]

        preds = self.task_head(fused_task_embed)
        reconstructed_x = self.recon_head(fused_task_embed)
        
        duration_factor = F.softplus(preds[:, 0]) + 0.5 # Khoảng [0.5, inf)
        expected_delay = F.relu(preds[:, 1])            # >= 0
        uncertainty_sigma = F.softplus(preds[:, 2]) + 0.01 # > 0
        
        return {
            'duration_factor': duration_factor,
            'expected_delay': expected_delay,
            'uncertainty_sigma': uncertainty_sigma,
            'task_embeddings': fused_task_embed,
            'global_project_context': global_context,
            'reconstructed_x': reconstructed_x
        }
