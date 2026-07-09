"""
Mô-đun pretraining_losses: Các hàm Loss phục vụ Tiền huấn luyện Tự giám sát (Self-Supervised Pretraining)
================================================================================================
Dự án: GLPO - Graph Logistics Project Optimization

Mô tả:
    Triển khai các thành phần hàm Loss bao gồm:
    - GAE Loss (Graph AutoEncoder Loss) & DGI Loss (Deep Graph Infomax Loss) cho GAT.
    - CPM Loss, Masked Duration Loss, và Topological Distance Loss cho DAGNN.
    - MultiTaskLoss (cho GAT) và DAGNNMultiTaskLoss (cho DAGNN).
"""

import torch
import torch.nn as nn
from typing import Tuple


# ============================================================================
# HÀM LOSS CHO GAT (GRAPH AUTOENCODER & DEEP GRAPH INFOMAX)
# ============================================================================

class GAELoss(nn.Module):
    """
    Graph AutoEncoder (GAE) Loss cho việc phục dựng ma trận kề (Adjacency Reconstruction).
    Sử dụng hàm tích vô hướng làm Decoder để dự đoán sự tồn tại của cạnh.
    """
    def __init__(self, eps: float = 1e-15):
        super(GAELoss, self).__init__()
        self.eps = eps

    def decode(self, z: torch.Tensor, edge_index: torch.Tensor, sigmoid: bool = True) -> torch.Tensor:
        value = (z[edge_index[0]] * z[edge_index[1]]).sum(dim=-1)
        if sigmoid:
            return torch.sigmoid(value)
        return value

    def forward(self, z: torch.Tensor, pos_edge_index: torch.Tensor, neg_edge_index: torch.Tensor) -> torch.Tensor:
        pos_scores = self.decode(z, pos_edge_index, sigmoid=True)
        neg_scores = self.decode(z, neg_edge_index, sigmoid=True)

        pos_loss = -torch.log(pos_scores + self.eps).mean()
        neg_loss = -torch.log(1.0 - neg_scores + self.eps).mean()
        
        return pos_loss + neg_loss


class DGILoss(nn.Module):
    """
    Deep Graph Infomax (DGI) Loss.
    Tối đa hóa Mutual Information giữa biểu diễn cục bộ (Node Embedding) và biểu diễn toàn cục (Graph Summary).
    """
    def __init__(self):
        super(DGILoss, self).__init__()
        self.bce = nn.BCEWithLogitsLoss()

    def forward(
        self,
        z: torch.Tensor,
        z_corrupted: torch.Tensor,
        summary: torch.Tensor,
        discriminator: nn.Module
    ) -> torch.Tensor:
        logits_pos = discriminator(z, summary)  # [N]
        logits_neg = discriminator(z_corrupted, summary)  # [N]

        labels_pos = torch.ones_like(logits_pos)
        labels_neg = torch.zeros_like(logits_neg)

        loss_pos = self.bce(logits_pos, labels_pos)
        loss_neg = self.bce(logits_neg, labels_neg)

        return loss_pos + loss_neg


class MultiTaskLoss(nn.Module):
    """
    Multi-task Loss kết hợp GAE và DGI để tối ưu hóa đồng thời GAT.
    L = lambda_gae * L_GAE + lambda_dgi * L_DGI
    """
    def __init__(self, lambda_gae: float = 0.5, lambda_dgi: float = 0.5):
        super(MultiTaskLoss, self).__init__()
        self.lambda_gae = lambda_gae
        self.lambda_dgi = lambda_dgi
        self.gae_loss_fn = GAELoss()
        self.dgi_loss_fn = DGILoss()

    def forward(
        self,
        z: torch.Tensor,
        z_corrupted: torch.Tensor,
        summary: torch.Tensor,
        discriminator: nn.Module,
        pos_edge_index: torch.Tensor,
        neg_edge_index: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        gae_loss = self.gae_loss_fn(z, pos_edge_index, neg_edge_index)
        dgi_loss = self.dgi_loss_fn(z, z_corrupted, summary, discriminator)
        
        total_loss = self.lambda_gae * gae_loss + self.lambda_dgi * dgi_loss
        return total_loss, gae_loss, dgi_loss


# ============================================================================
# HÀM LOSS CHO DAGNN (CPM + MASKED DURATION + TOPO DISTANCE)
# ============================================================================

class CPMLoss(nn.Module):
    """
    CPM Loss: Dự đoán các thuộc tính đường găng tĩnh của DAG.
    Kết hợp MSE có trọng số cho 6 thuộc tính liên tục và BCE cho nhãn Critical Flag nhị phân.
    
    Tối ưu hóa R² bằng cách tăng trọng số cho Early Start (ES) và Early Finish (EF) lên 3.0.
    
    Các thuộc tính (7 chiều):
        - Index 0: Early Start (trọng số 3.0)
        - Index 1: Early Finish (trọng số 3.0)
        - Index 2: Late Start (trọng số 1.0)
        - Index 3: Late Finish (trọng số 1.0)
        - Index 4: Total Float (trọng số 1.0)
        - Index 5: Is Critical (binary flag - BCE)
        - Index 6: Longest Path Distance (trọng số 1.0)
    """
    def __init__(self):
        super(CPMLoss, self).__init__()
        # Trọng số tương ứng cho 6 thuộc tính liên tục (ES, EF, LS, LF, TF, PL)
        self.register_buffer('weights', torch.tensor([3.0, 3.0, 1.0, 1.0, 1.0, 1.0], dtype=torch.float32))
        self.bce = nn.BCEWithLogitsLoss()

    def forward(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        continuous_indices = [0, 1, 2, 3, 4, 6]
        pred_cont = predictions[:, continuous_indices]
        true_cont = targets[:, continuous_indices]
        
        # Tính weighted MSE
        diff_sq = (pred_cont - true_cont) ** 2
        weighted_mse = (diff_sq * self.weights).mean()
        
        loss_binary = self.bce(predictions[:, 5], targets[:, 5])
        
        # Đặt trọng số cao hơn cho nhãn Critical (đường găng) để đảm bảo tính an toàn
        return weighted_mse + 2.0 * loss_binary


class CPNTTripletLoss(nn.Module):
    """
    Critical Path Node Triplet Loss (CPNT Loss) cho GAT.
    Ép các nút nằm trên đường găng có biểu diễn embedding đứng gần nhau trong không gian nhúng cấu trúc.
    
    Công thức:
        L_CPNT = max(0, ||z_a - z_p||² - ||z_a - z_n||² + margin)
    """
    def __init__(self, margin: float = 0.5):
        super(CPNTTripletLoss, self).__init__()
        self.triplet_loss = nn.TripletMarginLoss(margin=margin, p=2)

    def forward(self, z: torch.Tensor, anchors: torch.Tensor, positives: torch.Tensor, negatives: torch.Tensor) -> torch.Tensor:
        if anchors.numel() == 0 or positives.numel() == 0 or negatives.numel() == 0:
            return torch.tensor(0.0, device=z.device)
        return self.triplet_loss(z[anchors], z[positives], z[negatives])


class MaskedDurationLoss(nn.Module):
    """
    Masked Duration Loss: Chỉ tính sai số MSE dự đoán thời lượng (Duration) 
    trên các node đã bị che khuất (masked).
    """
    def __init__(self):
        super(MaskedDurationLoss, self).__init__()
        self.mse = nn.MSELoss()

    def forward(self, predicted_durations: torch.Tensor, true_durations: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        if not mask.any():
            return torch.tensor(0.0, device=predicted_durations.device)
        return self.mse(predicted_durations[mask], true_durations[mask])


class TopologicalDistanceLoss(nn.Module):
    """
    Topological Distance Loss (PCR Loss): Tính toán sai số MSE giữa khoảng cách tích lũy (PCR) thực tế
    và khoảng cách dự đoán giữa các cặp node ngẫu nhiên.
    """
    def __init__(self):
        super(TopologicalDistanceLoss, self).__init__()
        self.mse = nn.MSELoss()

    def forward(self, predicted_distances: torch.Tensor, true_distances: torch.Tensor) -> torch.Tensor:
        return self.mse(predicted_distances, true_distances)


class DAGNNMultiTaskLoss(nn.Module):
    """
    DAGNN Multi-task Loss phối hợp 3 mục tiêu:
        L_DAGNN = lambda_cpm * L_CPM + lambda_mask * L_MASK + lambda_topo * L_PCR
    """
    def __init__(self, lambda_cpm: float = 0.4, lambda_mask: float = 0.3, lambda_topo: float = 0.3):
        super(DAGNNMultiTaskLoss, self).__init__()
        self.lambda_cpm = lambda_cpm
        self.lambda_mask = lambda_mask
        self.lambda_topo = lambda_topo
        self.cpm_loss_fn = CPMLoss()
        self.mask_loss_fn = MaskedDurationLoss()
        self.topo_loss_fn = TopologicalDistanceLoss()

    def forward(
        self,
        cpm_preds: torch.Tensor,
        cpm_targets: torch.Tensor,
        duration_preds: torch.Tensor,
        duration_targets: torch.Tensor,
        duration_mask: torch.Tensor,
        topo_preds: torch.Tensor,
        topo_targets: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        cpm_loss = self.cpm_loss_fn(cpm_preds, cpm_targets)
        mask_loss = self.mask_loss_fn(duration_preds, duration_targets, duration_mask)
        topo_loss = self.topo_loss_fn(topo_preds, topo_targets)
        
        total_loss = (
            self.lambda_cpm * cpm_loss
            + self.lambda_mask * mask_loss
            + self.lambda_topo * topo_loss
        )
        return total_loss, cpm_loss, mask_loss, topo_loss
