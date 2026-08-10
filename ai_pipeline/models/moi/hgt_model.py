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

    Mô hình này áp dụng kiến trúc Transformer chuyên biệt cho đồ thị đa hình.
    Nó thực hiện Message Passing (Truyền tin) qua các nút (Task, Resource, Shift)
    để học biểu diễn không gian nhúng (Embeddings) của toàn bộ dự án.

    Kiến trúc gồm:
        1. Projection Layers: Đưa các features đầu vào thô về cùng chiều hidden_dim (128).
        2. HGT Layers: Nhiều lớp Graph Transformer kết nối các nút lại với nhau.
        3. Global Context Pooling (Mean + Max): Trích xuất bối cảnh (Context) chung của cả dự án.
        4. Prediction Heads (MLP): Đưa ra 3 dự báo chính cho TỪNG công việc.

    Dự báo đầu ra:
        - duration_factor (Scale thay đổi thời lượng thi công).
        - expected_delay (Thời gian trễ hạn tính bằng Log-hours).
        - uncertainty_sigma (Mức độ bất định/rủi ro biến động).
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
            default_dim = 41 if node_type == 'task' else (6 if node_type == 'resource' else 5)
            in_dim = in_channels_dict.get(node_type, default_dim)
            self.proj_dict[node_type] = nn.Sequential(
                Linear(in_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU()
            )
            
        # =========================================================================
        # BƯỚC 2: MESSAGE PASSING QUA CÁC TẦNG HETEROGENEOUS GRAPH TRANSFORMER
        # ========================================================================= (Chuyên biệt cho Heterogeneous Graph Transformer)
        self.hgt_layers = nn.ModuleList()
        for _ in range(num_layers):
            self.hgt_layers.append(
                HGTConv(hidden_dim, hidden_dim, metadata=self.metadata, heads=num_heads)
            )
            
        # =========================================================================
        # BƯỚC 3: HYBRID READOUT POOLING (TẠO NGỮ CẢNH GLOBAL CHO DỰ ÁN)
        # ========================================================================= (Hybrid Mean + Max Pooling)
        self.fusion_layer = nn.Sequential(
            Linear(hidden_dim * 3, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU()
        )

        # 4. Task Decoder Head (Dự đoán 3 đầu ra) - Đã tách nhánh để tránh Gradient Interference
        self.dfac_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(0.2),
            Linear(hidden_dim // 2, 1) # [duration_factor]
        )
        
        self.delay_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(0.2),
            Linear(hidden_dim // 2, 2) # [expected_delay, uncertainty_sigma]
        )
        
        # 5. Feature Reconstruction Head cho Masked Autoencoder (Phase 0) với LayerNorm & GELU
        task_in_dim = in_channels_dict.get('task', 41)
        self.recon_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            Linear(hidden_dim, task_in_dim)
        )

    def forward(self, x_dict, edge_index_dict):
        """
        Forward Pass (Truyền xuôi) của mô hình HGT.

        Args:
            x_dict (Dict[str, Tensor]): Từ điển chứa tensor đặc trưng của từng loại Node.
            edge_index_dict (Dict[Tuple, Tensor]): Từ điển chứa ma trận cạnh giữa các loại Node.

        Returns:
            Dict[str, Tensor]: Từ điển kết quả dự báo và Embeddings trích xuất (Dùng cho Botttleneck Attention).
        """
        # =========================================================================
        # BƯỚC 1: CHIẾU (PROJECTION) CÁC NODE VỀ CÙNG SỐ CHIỀU (128-DIM)
        # ========================================================================= đầu cho từng loại nút
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

    Mô hình này áp dụng kiến trúc Transformer chuyên biệt cho đồ thị đa hình.
    Nó thực hiện Message Passing (Truyền tin) qua các nút (Task, Resource, Shift)
    để học biểu diễn không gian nhúng (Embeddings) của toàn bộ dự án.

    Kiến trúc gồm:
        1. Projection Layers: Đưa các features đầu vào thô về cùng chiều hidden_dim (128).
        2. HGT Layers: Nhiều lớp Graph Transformer kết nối các nút lại với nhau.
        3. Global Context Pooling (Mean + Max): Trích xuất bối cảnh (Context) chung của cả dự án.
        4. Prediction Heads (MLP): Đưa ra 3 dự báo chính cho TỪNG công việc.

    Dự báo đầu ra:
        - duration_factor (Scale thay đổi thời lượng thi công).
        - expected_delay (Thời gian trễ hạn tính bằng Log-hours).
        - uncertainty_sigma (Mức độ bất định/rủi ro biến động).
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
            default_dim = 41 if node_type == 'task' else (6 if node_type == 'resource' else 5)
            in_dim = in_channels_dict.get(node_type, default_dim)
            self.proj_dict[node_type] = nn.Sequential(
                Linear(in_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU()
            )
            
        # =========================================================================
        # BƯỚC 2: MESSAGE PASSING QUA CÁC TẦNG HETEROGENEOUS GRAPH TRANSFORMER
        # ========================================================================= (Chuyên biệt cho Heterogeneous Graph Transformer)
        self.hgt_layers = nn.ModuleList()
        for _ in range(num_layers):
            self.hgt_layers.append(
                HGTConv(hidden_dim, hidden_dim, metadata=self.metadata, heads=num_heads)
            )
            
        # =========================================================================
        # BƯỚC 3: HYBRID READOUT POOLING (TẠO NGỮ CẢNH GLOBAL CHO DỰ ÁN)
        # ========================================================================= (Hybrid Mean + Max Pooling)
        self.fusion_layer = nn.Sequential(
            Linear(hidden_dim * 3, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU()
        )

        # 4. Task Decoder Head (Dự đoán 3 đầu ra) - Đã tách nhánh để tránh Gradient Interference
        self.dfac_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(0.2),
            Linear(hidden_dim // 2, 1) # [duration_factor]
        )
        
        self.delay_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(0.2),
            Linear(hidden_dim // 2, 2) # [expected_delay, uncertainty_sigma]
        )
        
        # 5. Feature Reconstruction Head cho Masked Autoencoder (Phase 0) với LayerNorm & GELU
        task_in_dim = in_channels_dict.get('task', 41)
        self.recon_head = nn.Sequential(
            Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            Linear(hidden_dim, task_in_dim)
        )

    def forward(self, x_dict, edge_index_dict):
        """
        Forward Pass (Truyền xuôi) của mô hình HGT.

        Args:
            x_dict (Dict[str, Tensor]): Từ điển chứa tensor đặc trưng của từng loại Node.
            edge_index_dict (Dict[Tuple, Tensor]): Từ điển chứa ma trận cạnh giữa các loại Node.

        Returns:
            Dict[str, Tensor]: Từ điển kết quả dự báo và Embeddings trích xuất (Dùng cho Botttleneck Attention).
        """
        # =========================================================================
        # BƯỚC 1: CHIẾU (PROJECTION) CÁC NODE VỀ CÙNG SỐ CHIỀU (128-DIM)
        # ========================================================================= đầu cho từng loại nút
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

        # 6. Phân nhánh Dự báo Đa nhiệm (Multi-Task Learning)
        if task_embed.size(0) > 0:
            dfac_out = self.dfac_head(fused_task_embed).squeeze(-1) # [N]
            delay_out = self.delay_head(fused_task_embed) # [N, 2]
            
            # Khống chế giá trị sigma không bao giờ sụp đổ về 0 (ngăn chặn NLL Loss tiến tới âm vô cực)
            pred_sigma = F.softplus(delay_out[:, 1]) + 0.1
            
            reconstructed_x = self.recon_head(fused_task_embed)
            
            return {
                'duration_factor': dfac_out,
                'expected_delay': delay_out[:, 0],
                'uncertainty_sigma': pred_sigma,
                'task_embeddings': fused_task_embed,
                'resource_embeddings': h_dict.get('resource'),
                'global_project_context': global_context,
                'reconstructed_x': reconstructed_x
            }
        else:
            return {
                'duration_factor': torch.empty(0, device=task_embed.device),
                'expected_delay': torch.empty(0, device=task_embed.device),
                'uncertainty_sigma': torch.empty(0, device=task_embed.device),
                'task_embeddings': fused_task_embed,
                'resource_embeddings': h_dict.get('resource'),
                'global_project_context': global_context,
                'reconstructed_x': torch.empty(0, device=task_embed.device)
            }
