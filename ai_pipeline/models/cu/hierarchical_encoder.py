import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from .feature_interaction_matrix import build_sparse_matrix, get_interactions, get_feature_group_map
from .feature_normalizer import FeatureNormalizer

class HierarchicalAttentionEncoder(nn.Module):
    """
    Mô tả (Description):
        Khối 1: Custom Hierarchical Attention Encoder (Bộ mã hóa dựa trên sự chú ý phân cấp).
        Biến đổi 36 Tính năng (Features) của mỗi Đỉnh thành 8 Vector Đại diện (Group Embeddings)
        dựa trên thiết kế Phân cấp 3 Tầng:
        - Tầng 1: Feature <-> Feature (Intra-group Attention): Tính toán sự tương tác nội bộ nhóm.
        - Tầng 2: Feature -> Group (Cross-group Influence): Tính toán ảnh hưởng giữa các nhóm.
        
    Đầu vào (Args):
        feature_dim (int): Tổng số lượng tính năng đầu vào (mặc định 36).
        num_groups (int): Số lượng nhóm tính năng (mặc định 8 nhóm).
        
    Thuộc tính (Attributes):
        interaction_matrix (nn.Parameter): Ma trận Tương tác (Domain Knowledge) 36x36 không huấn luyện.
        group_indices (dict): Từ điển lưu trữ ranh giới (chỉ số) của từng nhóm trong mảng 36.
    """
    def __init__(self, feature_dim=36, num_groups=8, project_type="Logistics"):
        super(HierarchicalAttentionEncoder, self).__init__()
        self.feature_dim = feature_dim
        self.num_groups = num_groups
        self.project_type = project_type
        
        # 1. Khởi tạo Ma trận Tương tác Domain Knowledge (36x36)
        interactions = get_interactions(project_type)
        np_matrix = build_sparse_matrix(interactions, size=feature_dim)
        
        # Đóng băng ma trận (không train phần này, đây là Domain Knowledge)
        self.interaction_matrix = nn.Parameter(torch.tensor(np_matrix, dtype=torch.float), requires_grad=False)
        
        # Thêm Learnable Interaction (Residual Priors)
        self.learnable_interaction = nn.Parameter(torch.zeros_like(self.interaction_matrix), requires_grad=True)
        
        # Định nghĩa ranh giới các Group (Index mapping)
        self.group_indices = get_feature_group_map(project_type)
        
        # Ánh xạ Group ID 0-7 vào index 0-7
        self.group_mapping = {i: i for i in range(num_groups)}
        
        # Cấu trúc mạng phụ để học thêm (nếu cần)
        self.feature_transform = nn.Linear(feature_dim, feature_dim)
        
        # Xây dựng Ma trận Tương tác Tầng 2: F-G (Feature to Group) từ Ma trận Tầng 1
        # Kích thước: (36 features, 8 groups)
        X_fg = torch.zeros((feature_dim, num_groups))
        for f in range(feature_dim):
            for g_id, indices in self.group_indices.items():
                if f not in indices and len(indices) > 0: # f không thuộc nhóm g
                    X_fg[f, g_id] = float(np_matrix[f, indices].sum())
                    
        # Đóng băng ma trận F-G (Domain Knowledge)
        self.X_fg = nn.Parameter(X_fg, requires_grad=True)
        
        self.normalizer = FeatureNormalizer(feature_dim)

    def forward(self, x):
        """
        Mô tả (Description):
            Hàm tính toán truyền tiến (Forward Pass) của mô hình.
            Áp dụng Intra-group Attention để gom các feature riêng lẻ thành 8 con số đại diện.
            Đồng thời áp dụng Masking để vô hiệu hóa (set về 0) các nhóm không có dữ liệu (toàn số 0).
            
        Đầu vào (Args):
            x (torch.Tensor): Tensor chứa tính năng các Đỉnh, kích thước (batch_size, 36).
            
        Đầu ra (Returns):
            S_g (torch.Tensor): Vector đại diện của 8 Nhóm, kích thước (batch_size, 8).
            group_masks (torch.Tensor): Ma trận lưu trạng thái đóng/mở của các Nhóm (1.0 là mở, 0.0 là đóng), kích thước (batch_size, 8).
        """
        # Chuẩn hóa dữ liệu trước khi tính toán (Log1p + Graph MinMax + LayerNorm)
        x_norm = self.normalizer(x)
        
        # Bước 0: Adaptive Masking (Xác định Group nào "sống")
        batch_size = x.shape[0]
        device = x.device
        
        group_masks = torch.zeros((batch_size, self.num_groups), device=device)
        for g_id, indices in self.group_indices.items():
            # Sum absolute values to see if group is active
            group_sum = torch.sum(torch.abs(x_norm[:, indices]), dim=1)
            group_masks[:, g_id] = (group_sum > 0).float()
            
        # Transform raw features (tùy chọn)
        x_transformed = F.relu(self.feature_transform(x_norm))
        
        # Bước 1: Tầng 1 - Intra-group Attention
        S_g = torch.zeros((batch_size, self.num_groups), device=device)
        
        for g_id, indices in self.group_indices.items():
            if len(indices) == 0: continue
            
            # Extract sub-matrix A_intra cho nhóm g (Kết hợp Domain Knowledge và Learnable Prior)
            combined_matrix = self.interaction_matrix + self.learnable_interaction
            A_intra = combined_matrix[indices][:, indices]  # shape (n_g, n_g)
            
            # Trích xuất features của nhóm
            v_g = x_norm[:, indices]  # shape (batch, n_g)
            
            # Tính Attention: alpha = softmax(v_g * A_intra)
            att_scores = torch.matmul(v_g, A_intra.T)
            alpha = F.softmax(att_scores, dim=1)
            
            # Tính giá trị đại diện S_g
            S_g[:, g_id] = torch.sum(alpha * v_g, dim=1) * group_masks[:, g_id]
            
        # Bước 2: Tầng 2 - Feature ↔ Group (Cross-group Feature Influence)
        # Tính tổng ảnh hưởng của tất cả features lên từng group: (batch_size, 36) x (36, 8) -> (batch_size, 8)
        fg_influence = torch.matmul(x_norm, self.X_fg)
        
        # Áp dụng công thức khuếch đại / triệt tiêu: S'_g = S_g * (1 + tanh(influence))
        S_prime_g = S_g * (1.0 + F.tanh(fg_influence))
        
        # Áp dụng Mask để dập tắt các Nhóm đã bị vô hiệu hóa
        S_prime_g = S_prime_g * group_masks
        
        # Đầu ra: Vector đại diện đã chứa tương tác F-G (batch, 8)
        return S_prime_g, group_masks

if __name__ == "__main__":
    # Test Encoder
    encoder = HierarchicalAttentionEncoder()
    # Dummy data: 5 nodes, 36 features
    dummy_x = torch.rand((5, 36))
    
    # Ép một số group thành 0 để test Masking
    dummy_x[:, encoder.group_indices[2]] = 0.0 # Ép G2 = 0
    dummy_x[:, encoder.group_indices[4]] = 0.0 # Ép G4 = 0
    
    S_g, masks = encoder(dummy_x)
    
    print("=== TEST HIERARCHICAL ENCODER ===")
    print(f"Input X shape: {dummy_x.shape}")
    print(f"Group Mask shape: {masks.shape}")
    print(f"S_g (Representative Scores) shape: {S_g.shape}")
    print(f"Mask for Node 0: {masks[0]}")
    print(f"S_g cho Node 0: {S_g[0]}")
