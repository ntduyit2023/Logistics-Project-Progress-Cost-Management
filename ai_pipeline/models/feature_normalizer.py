import torch
import torch.nn as nn

class FeatureNormalizer(nn.Module):
    """
    Module chuẩn hóa dữ liệu 72-Dimension cho mạng GNN, 
    áp dụng các chiến lược Scale khác nhau dựa trên kiểu phân phối (Range).
    """
    def __init__(self, feature_dim=72):
        super(FeatureNormalizer, self).__init__()
        self.feature_dim = feature_dim
        
        # 1. Nhóm Log1p: Giá trị lớn, right-skewed (Tiền tệ, Thời gian, Số đếm)
        self.log1p_indices = [
            0, 1, 2, 3, 4, 
            7, 8, 9, 10, 11, 12, 13, 14, 
            16, 17, 18, 19, 20, 
            21, 22, 23, 24, 
            25, 26, 27, 28, 29, 30, 31, 
            32, 33, 34, 35, 36, 
            37, 38, 
            45, 46, 
            49, 50, 
            53, 54, 55, 56, 57, 58, 59, 
            61, 62, 63, 64, 
            66, 67, 68, 69
        ]
        
        # 2. Nhóm Pass-through: Đã chuẩn [0, 1] hoặc Boolean (Không đổi)
        self.passthrough_indices = [
            5, 6, 15, 41, 44, 47, 48, 60, 65
        ]
        
        # 3. Nhóm Div100: Phần trăm [0, 100] -> [0, 1]
        self.div100_indices = [
            39, 40, 43, 51, 52
        ]
        
        # 4. Nhóm MinMax: Thang điểm cố định [1, 5] -> [0, 1]
        self.minmax_indices = [
            42
        ]
        
        # 5. Nhóm Clamp + Scale: Chỉ số hiệu suất EVM xoay quanh 1.0 (CPI, SPI)
        self.clamp_scale_indices = [
            70, 71
        ]
        
        # Kiểm tra sanity check: Tổng số features = 72?
        total_indices = len(self.log1p_indices) + len(self.passthrough_indices) + \
                        len(self.div100_indices) + len(self.minmax_indices) + len(self.clamp_scale_indices)
        assert total_indices == self.feature_dim, f"Tổng số features không khớp! ({total_indices} != {self.feature_dim})"

    def forward(self, x):
        """
        x: Tensor [batch_size, 72]
        """
        # Tạo clone để tránh lỗi in-place trên autograd
        x_norm = x.clone()
        
        # 1. Log1p: x' = log(1 + x)
        if len(self.log1p_indices) > 0:
            x_norm[:, self.log1p_indices] = torch.log1p(torch.clamp(x[:, self.log1p_indices], min=0.0))
            
        # 2. Pass-through: Do nothing
        pass
        
        # 3. Div100: x' = x / 100
        if len(self.div100_indices) > 0:
            x_norm[:, self.div100_indices] = x[:, self.div100_indices] / 100.0
            
        # 4. MinMax: x' = (x - 1) / 4 (Ép thang điểm 1-5 về 0-1)
        if len(self.minmax_indices) > 0:
            x_norm[:, self.minmax_indices] = (x[:, self.minmax_indices] - 1.0) / 4.0
            
        # 5. Clamp + Scale: x' = clamp(x, 0, 3) / 3
        if len(self.clamp_scale_indices) > 0:
            x_norm[:, self.clamp_scale_indices] = torch.clamp(x[:, self.clamp_scale_indices], min=0.0, max=3.0) / 3.0
            
        return x_norm
