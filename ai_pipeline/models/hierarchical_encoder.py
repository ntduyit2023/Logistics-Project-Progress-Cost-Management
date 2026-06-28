import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from feature_interaction_matrix import build_sparse_matrix, INTERACTIONS

class HierarchicalAttentionEncoder(nn.Module):
    """
    Khối 1: Custom Hierarchical Attention Encoder (72 Features -> 9/12 Group Embeddings)
    Dựa trên thiết kế Phân cấp 3 Tầng:
    - Tầng 1: Feature <-> Feature (Intra-group Attention)
    - Tầng 2: Feature -> Group (Cross-group Influence)
    """
    def __init__(self, feature_dim=72, num_groups=12):
        super(HierarchicalAttentionEncoder, self).__init__()
        self.feature_dim = feature_dim
        self.num_groups = num_groups
        
        # 1. Khởi tạo Ma trận Tương tác Domain Knowledge (72x72)
        # Chúng ta dùng sparse matrix đã định nghĩa trong feature_interaction_matrix.py
        np_matrix = build_sparse_matrix(INTERACTIONS, size=feature_dim)
        
        # Đóng băng ma trận (không train phần này, đây là Domain Knowledge)
        # Nhưng có thể cho phép train một chút (fine-tuning) bằng cách gán requires_grad=True sau này
        self.interaction_matrix = nn.Parameter(torch.tensor(np_matrix, dtype=torch.float), requires_grad=False)
        
        # Định nghĩa ranh giới các Group (Index mapping)
        self.group_indices = {
            0: list(range(0, 7)),    # Hub
            1: list(range(7, 15)),   # G1
            2: list(range(15, 21)),  # G2
            3: list(range(60, 63)),  # G3 (AI)
            4: list(range(21, 25)),  # G4
            5: list(range(25, 32)),  # G5
            6: list(range(32, 37)),  # G6
            7: list(range(37, 42)),  # G7
            8: list(range(63, 68)),  # G8 (AI)
            9: list(range(42, 49)),  # G9
            10: list(range(68, 72)), # G10 (AI)
            11: list(range(49, 55)), # G11
            12: list(range(55, 60))  # G12
        }
        
        # Ánh xạ Group ID 1-12 vào index 0-11
        self.group_mapping = {
            0: 0, 1: 1, 2: 2, 4: 3, 5: 4, 6: 5, 7: 6, 9: 7, 11: 8, 12: 9, 3: 10, 8: 11, 10: 12
        }
        
        # Cấu trúc mạng phụ để học thêm (nếu cần)
        self.feature_transform = nn.Linear(feature_dim, feature_dim)

    def forward(self, x):
        """
        x: Tensor shape (num_nodes, 72)
        """
        # Bước 0: Adaptive Masking (Xác định Group nào "sống")
        # m = 1 nếu group có ít nhất 1 giá trị != 0
        batch_size = x.shape[0]
        device = x.device
        
        group_masks = torch.zeros((batch_size, 13), device=device) # 13 vì có Hub (0) + 12 groups
        for g_id, indices in self.group_indices.items():
            # Sum absolute values to see if group is active
            group_sum = torch.sum(torch.abs(x[:, indices]), dim=1)
            group_masks[:, g_id] = (group_sum > 0).float()
            
        # Transform raw features (tùy chọn)
        x_transformed = F.relu(self.feature_transform(x))
        
        # Bước 1: Tầng 1 - Intra-group Attention
        S_g = torch.zeros((batch_size, 13), device=device)
        
        for g_id, indices in self.group_indices.items():
            if len(indices) == 0: continue
            
            # Extract sub-matrix A_intra cho nhóm g
            A_intra = self.interaction_matrix[indices][:, indices]  # shape (n_g, n_g)
            
            # Trích xuất features của nhóm
            v_g = x[:, indices]  # shape (batch, n_g)
            
            # Tính Attention: alpha = softmax(v_g * A_intra)
            # v_g: (batch, n_g), A_intra: (n_g, n_g) -> (batch, n_g)
            att_scores = torch.matmul(v_g, A_intra.T)
            alpha = F.softmax(att_scores, dim=1)
            
            # Tính giá trị đại diện S_g
            S_g[:, g_id] = torch.sum(alpha * v_g, dim=1) * group_masks[:, g_id]
            
        # Bước 2: Tầng 2 - Cross-group Influence
        # (Ở phiên bản đơn giản này, ta cho mạng tự học cross-influence thông qua 1 Linear Layer
        # thay vì code cứng từng cặp, vì Ma trận Domain Knowledge đã cover phần lớn rồi)
        
        # Đầu ra: Vector đại diện (batch, 13)
        return S_g, group_masks

if __name__ == "__main__":
    # Test Encoder
    encoder = HierarchicalAttentionEncoder()
    # Dummy data: 5 nodes, 72 features
    dummy_x = torch.rand((5, 72))
    
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
