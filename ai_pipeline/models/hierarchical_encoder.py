import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from feature_interaction_matrix import build_sparse_matrix, INTERACTIONS

class HierarchicalAttentionEncoder(nn.Module):
    """
    Mô tả (Description):
        Khối 1: Custom Hierarchical Attention Encoder (Bộ mã hóa dựa trên sự chú ý phân cấp).
        Biến đổi 72 Tính năng (Features) của mỗi Đỉnh thành 13 Vector Đại diện (Group Embeddings)
        dựa trên thiết kế Phân cấp 3 Tầng:
        - Tầng 1: Feature <-> Feature (Intra-group Attention): Tính toán sự tương tác nội bộ nhóm.
        - Tầng 2: Feature -> Group (Cross-group Influence): Tính toán ảnh hưởng giữa các nhóm.
        
    Đầu vào (Args):
        feature_dim (int): Tổng số lượng tính năng đầu vào (mặc định 72).
        num_groups (int): Số lượng nhóm tính năng (mặc định 12 nhóm Spoke + 1 Hub = 13 nhóm).
        
    Thuộc tính (Attributes):
        interaction_matrix (nn.Parameter): Ma trận Tương tác (Domain Knowledge) 72x72 không huấn luyện.
        group_indices (dict): Từ điển lưu trữ ranh giới (chỉ số) của từng nhóm trong mảng 72.
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
        
        # Xây dựng Ma trận Tương tác Tầng 2: F-G (Feature to Group) từ Ma trận Tầng 1 (72x72)
        # Kích thước: (72 features, 13 groups)
        # X_{f->g} = Tổng các tương tác từ feature f tới tất cả features trong nhóm g
        X_fg = torch.zeros((72, 13))
        for f in range(72):
            for g_id, indices in self.group_indices.items():
                if f not in indices and len(indices) > 0: # f không thuộc nhóm g
                    X_fg[f, g_id] = float(np_matrix[f, indices].sum())
                    
        # Đóng băng ma trận F-G (Domain Knowledge)
        self.X_fg = nn.Parameter(X_fg, requires_grad=False)

    def forward(self, x):
        """
        Mô tả (Description):
            Hàm tính toán truyền tiến (Forward Pass) của mô hình.
            Áp dụng Intra-group Attention để gom các feature riêng lẻ thành 13 con số đại diện.
            Đồng thời áp dụng Masking để vô hiệu hóa (set về 0) các nhóm không có dữ liệu (toàn số 0).
            
        Đầu vào (Args):
            x (torch.Tensor): Tensor chứa tính năng các Đỉnh, kích thước (batch_size, 72).
            
        Đầu ra (Returns):
            S_g (torch.Tensor): Vector đại diện của 13 Nhóm, kích thước (batch_size, 13).
            group_masks (torch.Tensor): Ma trận lưu trạng thái đóng/mở của các Nhóm (1.0 là mở, 0.0 là đóng), kích thước (batch_size, 13).
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
            
        # Bước 2: Tầng 2 - Feature ↔ Group (Cross-group Feature Influence)
        # S_g đang chứa 13 giá trị đại diện từ Tầng 1.
        # Ta cần tính S'_g = S_g * (1 + ảnh hưởng từ các feature nằm ngoài nhóm)
        
        # Tính tổng ảnh hưởng của tất cả features lên từng group: (batch_size, 72) x (72, 13) -> (batch_size, 13)
        fg_influence = torch.matmul(x, self.X_fg)
        
        # Áp dụng công thức khuếch đại / triệt tiêu: S'_g = S_g * (1 + tanh(influence))
        S_prime_g = S_g * (1.0 + F.tanh(fg_influence))
        
        # Áp dụng Mask để dập tắt các Nhóm đã bị vô hiệu hóa
        S_prime_g = S_prime_g * group_masks
        
        # Tầng 3 (G-G) KHÔNG nằm ở đây. Tầng 3 (Tính Tổng Chi phí TGC) sẽ được xử lý 
        # bởi Môi trường PPO (Reward Function). Mạng Nơ-ron chỉ dừng ở Tầng 2 (S'_g).
        
        # Đầu ra: Vector đại diện đã chứa tương tác F-G (batch, 13)
        return S_prime_g, group_masks

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
