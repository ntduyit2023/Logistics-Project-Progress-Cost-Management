import torch
import torch.nn as nn

class FeatureNormalizer(nn.Module):
    """
    Module chuẩn hóa dữ liệu 72-Dimension cho mạng GNN, 
    áp dụng các chiến lược Scale khác nhau dựa trên kiểu phân phối (Range).
    """
    def __init__(self, feature_dim=36):
        super(FeatureNormalizer, self).__init__()
        self.feature_dim = feature_dim
        
        # 1. Nhóm Log1p: Giá trị lớn, right-skewed (Tiền tệ, Thời gian, Số đếm)
        self.log1p_indices = [
            0, 1, 2, 3,  # Thời gian
            5, 6, 7, 8, 9, 10,  # Direct Cost
            11, 12, 13, 14,  # Indirect Cost
            15, 16, 17,  # Contractual Cost
            19, 20, 21,  # Risk Cost
            22, 23, 24, 25, 26,  # Logistics Cost
            27, 28,  # Time & Schedule
            29, 30, 32, 33,  # Topology (demands, res, preds, succs)
            34, 35  # G8 Resources (demand, cost_estimate)
        ]
        
        # 2. Nhóm Pass-through: Đã chuẩn [0, 1] hoặc Boolean (Không đổi)
        self.passthrough_indices = [
            4,   # calendar_type_247
            18,  # complexity
            31   # is_critical
        ]
        
        # 3. Nhóm Div100: Phần trăm [0, 100] -> [0, 1]
        self.div100_indices = []
        
        # 4. Nhóm MinMax: Thang điểm cố định [1, 5] -> [0, 1]
        self.minmax_indices = []
        
        # 5. Nhóm Clamp + Scale: Chỉ số hiệu suất EVM xoay quanh 1.0 (CPI, SPI)
        self.clamp_scale_indices = []
        
        # Kiểm tra sanity check: Tổng số features = 72?
        total_indices = len(self.log1p_indices) + len(self.passthrough_indices) + \
                        len(self.div100_indices) + len(self.minmax_indices) + len(self.clamp_scale_indices)
        assert total_indices == self.feature_dim, f"Tổng số features không khớp! ({total_indices} != {self.feature_dim})"
        
        # Layer Normalization: Chống lạm phát quy mô dự án (Scale Invariance)
        self.layer_norm = nn.LayerNorm(feature_dim)

    def forward(self, x):
        """
        x: Tensor [batch_size, 72]
        """
        # Tạo clone để tránh lỗi in-place trên autograd
        x_norm = x.clone()
        
        # 1. Log1p: x' = log(1 + x)
        if len(self.log1p_indices) > 0:
            x_norm[:, self.log1p_indices] = torch.log1p(torch.clamp(x[:, self.log1p_indices], min=0.0))
            
        # 2. Graph-level MinMax Scaling cho Topology & Resource features (29, 30, 32, 33, 34)
        graph_minmax_cols = [29, 30, 32, 33, 34]
        for c in graph_minmax_cols:
            max_v = torch.max(torch.abs(x_norm[:, c]))
            if max_v > 1e-6:
                x_norm[:, c] = x_norm[:, c] / max_v
        
        # 3. Div100: x' = x / 100
        if len(self.div100_indices) > 0:
            x_norm[:, self.div100_indices] = x[:, self.div100_indices] / 100.0
            
        # 4. MinMax: x' = (x - 1) / 4 (Ép thang điểm 1-5 về 0-1)
        if len(self.minmax_indices) > 0:
            x_norm[:, self.minmax_indices] = (x[:, self.minmax_indices] - 1.0) / 4.0
            
        # 5. Clamp + Scale: x' = clamp(x, 0, 3) / 3
        if len(self.clamp_scale_indices) > 0:
            x_norm[:, self.clamp_scale_indices] = torch.clamp(x[:, self.clamp_scale_indices], min=0.0, max=3.0) / 3.0
            
        # Áp dụng Layer Normalization để ép về phân phối chuẩn
        x_norm = self.layer_norm(x_norm)
            
        return x_norm
