"""
Mô-đun Tầng 3: Hàm Tổng Chi phí Quy đổi (Total Generalized Cost - TGC)
=========================================================================
Dự án: GLPO - Graph Logistics Project Optimization

Mô tả:
    Tầng cuối cùng trong kiến trúc đánh giá phân cấp 3 tầng.
    Nhận đầu vào S'_g (13 giá trị đại diện nhóm đã qua Tầng 1 & Tầng 2)
    từ HierarchicalAttentionEncoder, và tính toán Tổng Chi phí Quy đổi (TGC)
    bao gồm cả phần tuyến tính (Σ β·S'_g) và phần phi tuyến (Σ γ·S'_g·S'_h).

Công thức chính (có Masking):
    TGC_i = Σ m_{i,g} · β_g · S'_g  +  Σ_{g<h} m_{i,g} · m_{i,h} · γ_{g,h} · S'_g · S'_h

Nguồn tham chiếu:
    docs/22-6/hierarchical_3level_evaluation.md (Version 2.0)
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Optional, Tuple

# ============================================================================
# HẰNG SỐ: TÊN VÀ CHỈ SỐ CÁC NHÓM TRONG ENCODER (13 nhóm)
# ============================================================================
# Chỉ số trong vector S'_g (output của HierarchicalAttentionEncoder)
# Khớp với group_indices trong hierarchical_encoder.py
GROUP_NAMES = {
    0:  "Hub (Core Temporal)",
    1:  "G1 (Direct Costs)",
    2:  "G2 (Indirect Costs)",
    3:  "G3 (Opportunity Cost) [AI]",
    4:  "G4 (Contractual)",
    5:  "G5 (Logistics & SCM)",
    6:  "G6 (Temporal Extended)",
    7:  "G7 (Resources)",
    8:  "G8 (Network Topology) [AI]",
    9:  "G9 (Risks)",
    10: "G10 (Earned Value) [AI]",
    11: "G11 (Human & Org)",
    12: "G12 (ESG)",
}

NUM_GROUPS = 13  # Hub + G1-G12

# ============================================================================
# MA TRẬN TƯƠNG TÁC LIÊN NHÓM γ (13 × 13)
# ============================================================================
# Nguồn: Bảng quan hệ liên nhóm trong hierarchical_3level_evaluation.md
# Quy ước:
#   📈 Khuếch đại (Amplifying)   = +0.8
#   🤝 Bổ trợ (Complementary)     = +0.5
#   ⚔️ Cạnh tranh (Competitive)   = -0.5
#   ·  Không tương tác             = 0.0
#
# Ma trận đối xứng: γ[g,h] = γ[h,g]
# Đường chéo = 0 (một nhóm không tương tác với chính nó ở Tầng 3)
#
# Thứ tự: Hub, G1, G2, G3, G4, G5, G6, G7, G8, G9, G10, G11, G12
#          [0]  [1] [2] [3] [4] [5] [6] [7] [8] [9] [10] [11] [12]

def _build_gamma_matrix() -> np.ndarray:
    """
    Xây dựng ma trận hệ số tương tác liên nhóm γ (13×13).

    Hub (index 0) được thiết lập với mối quan hệ khuếch đại đặc biệt
    tới G2, G6, G9 — vì thời gian kéo dài ảnh hưởng trực tiếp đến
    chi phí gián tiếp, thời gian mở rộng, và rủi ro.

    Returns:
        Ma trận numpy 13×13 chứa các hệ số γ.
    """
    gamma = np.zeros((NUM_GROUPS, NUM_GROUPS), dtype=np.float32)

    # --- Hub (0) tương tác với các nhóm khác ---
    # Hub → G2: Duration kéo dài → Chi phí gián tiếp tăng (📈)
    gamma[0, 2] = gamma[2, 0] = 0.8
    # Hub → G6: Duration kéo dài → Thời gian mở rộng tăng (📈)
    gamma[0, 6] = gamma[6, 0] = 0.8
    # Hub → G9: Duration kéo dài → Rủi ro tăng (📈)
    gamma[0, 9] = gamma[9, 0] = 0.5

    # --- G1 (1) - Chi phí Trực tiếp ---
    gamma[1, 2]  = gamma[2, 1]  = 0.5   # G1 🤝 G2
    gamma[1, 3]  = gamma[3, 1]  = -0.5  # G1 ⚔️ G3
    gamma[1, 4]  = gamma[4, 1]  = 0.5   # G1 🤝 G4
    gamma[1, 5]  = gamma[5, 1]  = 0.5   # G1 🤝 G5
    gamma[1, 6]  = gamma[6, 1]  = 0.8   # G1 📈 G6
    gamma[1, 7]  = gamma[7, 1]  = 0.8   # G1 📈 G7
    gamma[1, 10] = gamma[10, 1] = -0.5  # G1 ⚔️ G10
    gamma[1, 11] = gamma[11, 1] = 0.8   # G1 📈 G11

    # --- G2 (2) - Chi phí Gián tiếp ---
    gamma[2, 6] = gamma[6, 2] = 0.8     # G2 📈 G6

    # --- G3 (3) - Cơ hội [AI] ---
    gamma[3, 10] = gamma[10, 3] = -0.5  # G3 ⚔️ G10

    # --- G4 (4) - Hợp đồng ---
    gamma[4, 5]  = gamma[5, 4]  = 0.5   # G4 🤝 G5
    gamma[4, 6]  = gamma[6, 4]  = 0.8   # G4 📈 G6
    gamma[4, 9]  = gamma[9, 4]  = 0.8   # G4 📈 G9
    gamma[4, 10] = gamma[10, 4] = -0.5  # G4 ⚔️ G10
    gamma[4, 12] = gamma[12, 4] = 0.5   # G4 🤝 G12

    # --- G5 (5) - Logistics ---
    gamma[5, 6]  = gamma[6, 5]  = 0.8   # G5 📈 G6
    gamma[5, 7]  = gamma[7, 5]  = 0.8   # G5 📈 G7
    gamma[5, 9]  = gamma[9, 5]  = 0.8   # G5 📈 G9
    gamma[5, 12] = gamma[12, 5] = 0.5   # G5 🤝 G12

    # --- G6 (6) - Thời gian Mở rộng ---
    gamma[6, 7]  = gamma[7, 6]  = 0.8   # G6 📈 G7
    gamma[6, 8]  = gamma[8, 6]  = 0.8   # G6 📈 G8
    gamma[6, 9]  = gamma[9, 6]  = 0.8   # G6 📈 G9
    gamma[6, 11] = gamma[11, 6] = 0.8   # G6 📈 G11

    # --- G7 (7) - Tài nguyên ---
    gamma[7, 9]  = gamma[9, 7]  = 0.8   # G7 📈 G9
    gamma[7, 11] = gamma[11, 7] = 0.8   # G7 📈 G11

    # --- G8 (8) - Topology [AI] ---
    gamma[8, 9]  = gamma[9, 8]  = 0.8   # G8 📈 G9
    gamma[8, 10] = gamma[10, 8] = 0.8   # G8 📈 G10

    # --- G9 (9) - Rủi ro ---
    gamma[9, 10] = gamma[10, 9] = -0.5  # G9 ⚔️ G10
    gamma[9, 11] = gamma[11, 9] = 0.8   # G9 📈 G11
    gamma[9, 12] = gamma[12, 9] = 0.8   # G9 📈 G12

    # --- G10 (10) - Earned Value [AI] ---
    gamma[10, 11] = gamma[11, 10] = 0.8  # G10 📈 G11
    gamma[10, 12] = gamma[12, 10] = 0.5  # G10 🤝 G12

    # --- G11 (11) - Con người & Tổ chức ---
    gamma[11, 12] = gamma[12, 11] = 0.5  # G11 🤝 G12

    return gamma


# ============================================================================
# TRỌNG SỐ TẦM QUAN TRỌNG β (Mặc định - có thể điều chỉnh / học)
# ============================================================================
# Trọng số tầm quan trọng mặc định cho 13 nhóm.
# Giá trị cao hơn = nhóm đó ảnh hưởng lớn hơn đến TGC tổng.
# Hub được đặt cao nhất vì thời gian là yếu tố cốt lõi nhất.
DEFAULT_BETA = np.array([
    1.5,   # [0]  Hub: Core Temporal — yếu tố chi phối
    1.0,   # [1]  G1:  Direct Costs — chi phí chính
    0.7,   # [2]  G2:  Indirect Costs — chi phí gián tiếp
    0.5,   # [3]  G3:  Opportunity Cost [AI]
    0.6,   # [4]  G4:  Contractual — hợp đồng
    0.8,   # [5]  G5:  Logistics — chuỗi cung ứng
    1.2,   # [6]  G6:  Temporal Extended — thời gian mở rộng
    0.9,   # [7]  G7:  Resources — tài nguyên
    0.8,   # [8]  G8:  Network Topology [AI]
    1.0,   # [9]  G9:  Risks — rủi ro
    0.6,   # [10] G10: Earned Value [AI]
    0.7,   # [11] G11: Human & Org
    0.5,   # [12] G12: ESG
], dtype=np.float32)


# ============================================================================
# LỚP TÍNH TOÁN TGC TẦNG 3 (PyTorch Module)
# ============================================================================
class TGCLayer3(nn.Module):
    """
    Mô tả (Description):
        Lớp tính toán Tầng 3 của kiến trúc đánh giá phân cấp.
        Nhận đầu vào S'_g (13 giá trị đại diện nhóm đã qua Tầng 1 & 2)
        cùng với mặt nạ nhóm (group_masks) từ HierarchicalAttentionEncoder,
        và tính ra Tổng Chi phí Quy đổi (TGC) cho từng task trong batch.

    Công thức (Masked):
        TGC_i = Σ_g  m_{i,g} · β_g · S'_g
              + Σ_{g<h}  m_{i,g} · m_{i,h} · γ_{g,h} · S'_g · S'_h

    Đầu vào (Args):
        num_groups (int): Số lượng nhóm (mặc định 13).
        beta_init (np.ndarray): Vector trọng số β khởi tạo (13,).
            Nếu None, sử dụng DEFAULT_BETA.
        learnable_beta (bool): Nếu True, cho phép AI tự tinh chỉnh β
            trong quá trình huấn luyện. Mặc định False.
        learnable_gamma (bool): Nếu True, cho phép AI tự tinh chỉnh γ
            trong quá trình huấn luyện. Mặc định False.

    Đầu ra / Thuộc tính (Outputs / Attributes):
        beta (nn.Parameter hoặc buffer): Vector trọng số tầm quan trọng (13,).
        gamma (nn.Parameter hoặc buffer): Ma trận tương tác liên nhóm (13, 13).
    """
    def __init__(
        self,
        num_groups: int = NUM_GROUPS,
        beta_init: Optional[np.ndarray] = None,
        learnable_beta: bool = False,
        learnable_gamma: bool = False,
    ):
        super(TGCLayer3, self).__init__()
        self.num_groups = num_groups

        # Khởi tạo β
        beta_np = beta_init if beta_init is not None else DEFAULT_BETA.copy()
        beta_tensor = torch.tensor(beta_np, dtype=torch.float32)
        if learnable_beta:
            self.beta = nn.Parameter(beta_tensor)
        else:
            self.register_buffer('beta', beta_tensor)

        # Khởi tạo γ
        gamma_np = _build_gamma_matrix()
        gamma_tensor = torch.tensor(gamma_np, dtype=torch.float32)
        if learnable_gamma:
            self.gamma = nn.Parameter(gamma_tensor)
        else:
            self.register_buffer('gamma', gamma_tensor)

        # Tạo trước chỉ số của cặp (g, h) với g < h để tính tích chéo hiệu quả
        pairs_g = []
        pairs_h = []
        for g in range(num_groups):
            for h in range(g + 1, num_groups):
                pairs_g.append(g)
                pairs_h.append(h)
        self.register_buffer('pairs_g', torch.tensor(pairs_g, dtype=torch.long))
        self.register_buffer('pairs_h', torch.tensor(pairs_h, dtype=torch.long))

    def forward(
        self,
        S_prime_g: torch.Tensor,
        group_masks: torch.Tensor,
    ) -> torch.Tensor:
        """
        Mô tả (Description):
            Tính toán TGC cho từng task trong batch.

        Đầu vào (Args):
            S_prime_g (torch.Tensor): Giá trị đại diện nhóm đã qua Tầng 2.
                Kích thước: (batch_size, 13).
            group_masks (torch.Tensor): Mặt nạ đóng/mở nhóm.
                Kích thước: (batch_size, 13). Giá trị 1.0 = sống, 0.0 = chết.

        Đầu ra (Returns):
            tgc (torch.Tensor): Tổng Chi phí Quy đổi cho từng task.
                Kích thước: (batch_size,).
        """
        # --- Phần tuyến tính: Σ m_{i,g} · β_g · S'_g ---
        # S_prime_g: (batch, 13), beta: (13,), group_masks: (batch, 13)
        linear_term = torch.sum(
            group_masks * self.beta.unsqueeze(0) * S_prime_g,
            dim=1
        )  # (batch,)

        # --- Phần phi tuyến (Tích chéo): Σ_{g<h} m·m·γ·S'_g·S'_h ---
        # Lấy giá trị S' và mask theo các cặp (g, h)
        S_g = S_prime_g[:, self.pairs_g]  # (batch, num_pairs)
        S_h = S_prime_g[:, self.pairs_h]  # (batch, num_pairs)
        m_g = group_masks[:, self.pairs_g]  # (batch, num_pairs)
        m_h = group_masks[:, self.pairs_h]  # (batch, num_pairs)

        # Lấy hệ số γ cho từng cặp
        gamma_pairs = self.gamma[self.pairs_g, self.pairs_h]  # (num_pairs,)

        # Tính tích chéo có mask
        cross_products = m_g * m_h * gamma_pairs.unsqueeze(0) * S_g * S_h  # (batch, num_pairs)
        cross_term = torch.sum(cross_products, dim=1)  # (batch,)

        # TGC = Phần tuyến tính + Phần phi tuyến
        tgc = linear_term + cross_term

        return tgc

    def forward_detailed(
        self,
        S_prime_g: torch.Tensor,
        group_masks: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Mô tả (Description):
            Phiên bản chi tiết của hàm forward, trả về các thành phần trung gian
            để phục vụ phân tích và gỡ lỗi.

        Đầu vào (Args):
            S_prime_g (torch.Tensor): Kích thước (batch_size, 13).
            group_masks (torch.Tensor): Kích thước (batch_size, 13).

        Đầu ra (Returns):
            Dict chứa:
                - 'tgc': Tổng chi phí quy đổi (batch,).
                - 'linear_term': Phần tuyến tính (batch,).
                - 'cross_term': Phần phi tuyến (batch,).
                - 'group_contributions': Đóng góp tuyến tính của mỗi nhóm (batch, 13).
                - 'top_synergies': Dict chứa cặp nhóm có tích chéo lớn nhất (phân tích).
        """
        # Phần tuyến tính chi tiết
        group_contributions = group_masks * self.beta.unsqueeze(0) * S_prime_g  # (batch, 13)
        linear_term = torch.sum(group_contributions, dim=1)

        # Phần phi tuyến chi tiết
        S_g = S_prime_g[:, self.pairs_g]
        S_h = S_prime_g[:, self.pairs_h]
        m_g = group_masks[:, self.pairs_g]
        m_h = group_masks[:, self.pairs_h]
        gamma_pairs = self.gamma[self.pairs_g, self.pairs_h]

        cross_products = m_g * m_h * gamma_pairs.unsqueeze(0) * S_g * S_h
        cross_term = torch.sum(cross_products, dim=1)

        tgc = linear_term + cross_term

        # Phân tích: tìm 5 cặp nhóm có tích chéo lớn nhất (trung bình trên batch)
        mean_cross = cross_products.mean(dim=0)  # (num_pairs,)
        top_k = min(5, len(mean_cross))
        top_vals, top_idxs = torch.topk(mean_cross.abs(), top_k)
        top_synergies = []
        for rank, idx in enumerate(top_idxs):
            g_id = int(self.pairs_g[idx])
            h_id = int(self.pairs_h[idx])
            val = float(mean_cross[idx])
            top_synergies.append({
                'rank': rank + 1,
                'group_g': GROUP_NAMES.get(g_id, f"G{g_id}"),
                'group_h': GROUP_NAMES.get(h_id, f"G{h_id}"),
                'cross_value': val,
                'gamma': float(gamma_pairs[idx]),
                'effect': "Khuếch đại" if val > 0 else "Triệt tiêu",
            })

        return {
            'tgc': tgc,
            'linear_term': linear_term,
            'cross_term': cross_term,
            'group_contributions': group_contributions,
            'top_synergies': top_synergies,
        }


# ============================================================================
# HÀM TÍNH TGC THUẦN PYTHON (Không cần PyTorch — dùng trong PPO Reward)
# ============================================================================
def compute_tgc_numpy(
    S_prime_g: np.ndarray,
    group_masks: np.ndarray,
    beta: Optional[np.ndarray] = None,
    gamma: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Mô tả (Description):
        Phiên bản NumPy thuần của hàm tính TGC Tầng 3.
        Dùng khi không cần gradient (ví dụ: tính Reward trong PPO Environment).

    Đầu vào (Args):
        S_prime_g (np.ndarray): Giá trị đại diện nhóm từ Tầng 2. Kích thước (N, 13) hoặc (13,).
        group_masks (np.ndarray): Mặt nạ nhóm. Kích thước tương ứng (N, 13) hoặc (13,).
        beta (np.ndarray): Vector trọng số β (13,). Nếu None → dùng DEFAULT_BETA.
        gamma (np.ndarray): Ma trận γ (13, 13). Nếu None → dùng ma trận mặc định.

    Đầu ra (Returns):
        tgc (np.ndarray): Tổng chi phí quy đổi. Kích thước (N,) hoặc scalar.
    """
    if beta is None:
        beta = DEFAULT_BETA.copy()
    if gamma is None:
        gamma = _build_gamma_matrix()

    # Xử lý vector đơn lẻ (1 task)
    single = False
    if S_prime_g.ndim == 1:
        S_prime_g = S_prime_g.reshape(1, -1)
        group_masks = group_masks.reshape(1, -1)
        single = True

    N = S_prime_g.shape[0]
    G = S_prime_g.shape[1]

    # Phần tuyến tính
    linear_term = np.sum(group_masks * beta[np.newaxis, :] * S_prime_g, axis=1)

    # Phần phi tuyến (tích chéo)
    cross_term = np.zeros(N, dtype=np.float64)
    for g in range(G):
        for h in range(g + 1, G):
            gamma_gh = gamma[g, h]
            if gamma_gh == 0.0:
                continue  # Bỏ qua cặp không tương tác (tối ưu tốc độ)
            cross_term += (
                group_masks[:, g] * group_masks[:, h]
                * gamma_gh
                * S_prime_g[:, g] * S_prime_g[:, h]
            )

    tgc = linear_term + cross_term

    if single:
        return float(tgc[0])
    return tgc


# ============================================================================
# HÀM TÍNH REWARD CHO PPO (Bao gồm TGC + Phạt ràng buộc)
# ============================================================================
def compute_reward(
    S_prime_g: np.ndarray,
    group_masks: np.ndarray,
    raw_features: np.ndarray,
    schedule_info: Optional[Dict] = None,
    project_constraints: Optional[Dict] = None,
    beta: Optional[np.ndarray] = None,
    gamma: Optional[np.ndarray] = None,
    penalty_weight: float = 1e6,
) -> Dict[str, float]:
    """
    Mô tả (Description):
        Hàm tính phần thưởng (Reward) cho PPO Agent.
        Reward = -TGC - Tổng_Phạt_Vi_Phạm_Ràng_Buộc.

        Nếu lịch trình hợp lệ (Feasible):  Reward = -TGC (âm, nhưng gần 0 hơn là tốt).
        Nếu vi phạm ràng buộc (Infeasible): Reward = -TGC - penalty_weight (rất âm → PPO tránh xa).

    Đầu vào (Args):
        S_prime_g (np.ndarray): Giá trị đại diện nhóm (13,) cho 1 task.
        group_masks (np.ndarray): Mặt nạ nhóm (13,).
        raw_features (np.ndarray): Vector đặc trưng thô 72 chiều của task.
        schedule_info (dict): Thông tin lịch trình hiện tại của task:
            - 'finish_time': Thời gian kết thúc
            - 'active_resource_usage': Dict tài nguyên đang sử dụng tại thời điểm hiện tại
        project_constraints (dict): Các ràng buộc cấp dự án:
            - 'total_budget': Ngân sách tổng cho phép
            - 'deadline': Hạn chót dự án
            - 'carbon_cap': Hạn mức phát thải carbon
            - 'resource_capacities': Dict giới hạn tài nguyên {id: capacity}
            - 'min_quality': Ngưỡng chất lượng tối thiểu (EV/PV)
            - 'cumulative_tgc': Tổng TGC tích lũy đến thời điểm hiện tại
            - 'cumulative_env_impact': Tổng phát thải tích lũy
            - 'cumulative_ev': Tổng EV tích lũy
            - 'cumulative_pv': Tổng PV tích lũy
        beta, gamma: Tham số TGC (mặc định nếu None).
        penalty_weight: Hệ số phạt khi vi phạm ràng buộc.

    Đầu ra (Returns):
        Dict chứa:
            - 'reward': Giá trị phần thưởng cuối cùng (float).
            - 'tgc': Giá trị TGC thô trước phạt (float).
            - 'is_feasible': True nếu không vi phạm ràng buộc nào.
            - 'violations': Danh sách các ràng buộc bị vi phạm.
            - 'total_penalty': Tổng giá trị phạt.
    """
    # 1. Tính TGC
    tgc = compute_tgc_numpy(S_prime_g, group_masks, beta, gamma)
    if isinstance(tgc, np.ndarray):
        tgc = float(tgc)

    # 2. Kiểm tra ràng buộc
    violations = []
    total_penalty = 0.0

    if project_constraints is not None:
        constraints = project_constraints

        # ① Ràng buộc Ngân sách Tổng (Tầng 3)
        total_budget = constraints.get('total_budget', float('inf'))
        cumulative_tgc = constraints.get('cumulative_tgc', 0.0)
        if total_budget > 0.0 and cumulative_tgc + tgc > total_budget:
            excess = (cumulative_tgc + tgc) - total_budget
            violations.append({
                'type': 'BUDGET_EXCEEDED',
                'description': f"Tổng TGC ({cumulative_tgc + tgc:.2f}) vượt ngân sách ({total_budget:.2f})",
                'excess': excess,
            })
            total_penalty += penalty_weight * (excess / max(total_budget, 1.0))

        # ② Ràng buộc Deadline Dự án (Tầng 3)
        if schedule_info is not None:
            deadline = constraints.get('deadline', float('inf'))
            finish_time = schedule_info.get('finish_time', 0.0)
            if finish_time > deadline:
                excess = finish_time - deadline
                violations.append({
                    'type': 'DEADLINE_EXCEEDED',
                    'description': f"Thời gian kết thúc ({finish_time:.2f}) vượt deadline ({deadline:.2f})",
                    'excess': excess,
                })
                total_penalty += penalty_weight * (excess / max(deadline, 1.0))

        # ③ Ràng buộc ESG / Carbon (Tầng 3)
        carbon_cap = constraints.get('carbon_cap', float('inf'))
        cumulative_env = constraints.get('cumulative_env_impact', 0.0)
        # environmental_impact nằm ở index 55 trong vector 72 chiều
        current_env = float(raw_features[55]) if len(raw_features) > 55 else 0.0
        if cumulative_env + current_env > carbon_cap:
            excess = (cumulative_env + current_env) - carbon_cap
            violations.append({
                'type': 'CARBON_EXCEEDED',
                'description': f"Phát thải tích lũy ({cumulative_env + current_env:.2f}) vượt hạn mức ({carbon_cap:.2f})",
                'excess': excess,
            })
            total_penalty += penalty_weight * 0.5 * (excess / max(carbon_cap, 1.0))

        # ④ Ràng buộc Sức chứa Tài nguyên (Tầng 3)
        if schedule_info is not None:
            resource_caps = constraints.get('resource_capacities', {})
            active_usage = schedule_info.get('active_resource_usage', {})
            for res_id, capacity in resource_caps.items():
                usage = active_usage.get(res_id, 0.0)
                if usage > capacity:
                    excess = usage - capacity
                    violations.append({
                        'type': 'RESOURCE_OVERLOAD',
                        'description': f"Tài nguyên '{res_id}' quá tải ({usage:.1f}/{capacity:.1f})",
                        'excess': excess,
                    })
                    total_penalty += penalty_weight * (excess / max(capacity, 1.0))

        # ⑤ Ràng buộc Chất lượng Tối thiểu (Tầng 3)
        min_quality = constraints.get('min_quality', 0.0)
        cumulative_ev = constraints.get('cumulative_ev', 0.0)
        cumulative_pv = constraints.get('cumulative_pv', 0.0)
        if cumulative_pv > 0 and min_quality > 0:
            quality_ratio = cumulative_ev / cumulative_pv
            if quality_ratio < min_quality:
                deficit = min_quality - quality_ratio
                violations.append({
                    'type': 'QUALITY_BELOW_THRESHOLD',
                    'description': f"Chỉ số chất lượng EV/PV ({quality_ratio:.3f}) dưới ngưỡng ({min_quality:.3f})",
                    'deficit': deficit,
                })
                total_penalty += penalty_weight * deficit

        # ⑥ Ràng buộc Tài nguyên cấp task (Tầng 1 — G7)
        # request_quantity ở index 37, capacity kiểm tra ở trên
        request_qty = float(raw_features[37]) if len(raw_features) > 37 else 0.0
        allocated_qty = float(raw_features[38]) if len(raw_features) > 38 else 0.0
        if allocated_qty > 0 and request_qty > allocated_qty:
            violations.append({
                'type': 'TASK_RESOURCE_SHORTAGE',
                'description': f"Nhu cầu tài nguyên ({request_qty:.1f}) vượt phân bổ ({allocated_qty:.1f})",
                'excess': request_qty - allocated_qty,
            })
            # Phạt nhẹ hơn vì đây là vi phạm cấp task, không cấp dự án
            total_penalty += penalty_weight * 0.1

    # 3. Tính Reward
    is_feasible = len(violations) == 0
    reward = -tgc - total_penalty

    return {
        'reward': reward,
        'tgc': tgc,
        'is_feasible': is_feasible,
        'violations': violations,
        'total_penalty': total_penalty,
    }


# ============================================================================
# KHỐI KIỂM TRA (Unit Test)
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("  KIỂM TRA MÔ-ĐUN TGC TẦNG 3")
    print("=" * 70)

    # 1. Kiểm tra ma trận γ
    gamma_matrix = _build_gamma_matrix()
    print(f"\n[1] Ma trận γ (13×13):")
    print(f"    Kích thước: {gamma_matrix.shape}")
    print(f"    Đối xứng: {np.allclose(gamma_matrix, gamma_matrix.T)}")
    print(f"    Số cặp có tương tác (γ ≠ 0): {np.count_nonzero(gamma_matrix) // 2}")
    print(f"    Số cặp khuếch đại (γ > 0): {np.sum(gamma_matrix > 0) // 2}")
    print(f"    Số cặp triệt tiêu (γ < 0): {np.sum(gamma_matrix < 0) // 2}")

    # 2. Kiểm tra TGC bằng NumPy
    print(f"\n[2] Kiểm tra hàm compute_tgc_numpy:")
    # Giả lập 3 task với S'_g ngẫu nhiên
    np.random.seed(42)
    S_test = np.random.rand(3, 13).astype(np.float32)
    m_test = np.ones((3, 13), dtype=np.float32)
    # Tắt một số nhóm cho task 0 (giả lập masking)
    m_test[0, [2, 3, 4, 10, 11]] = 0.0

    tgc_values = compute_tgc_numpy(S_test, m_test)
    for i in range(3):
        active = int(m_test[i].sum())
        print(f"    Task {i}: TGC = {tgc_values[i]:.4f} (nhóm hoạt động: {active}/13)")

    # 3. Kiểm tra TGC bằng PyTorch Module
    print(f"\n[3] Kiểm tra TGCLayer3 (PyTorch):")
    tgc_module = TGCLayer3()
    S_torch = torch.tensor(S_test)
    m_torch = torch.tensor(m_test)

    with torch.no_grad():
        tgc_torch = tgc_module(S_torch, m_torch)
    print(f"    TGC (PyTorch): {tgc_torch.numpy()}")
    print(f"    TGC (NumPy):   {tgc_values}")
    print(f"    Khớp nhau: {np.allclose(tgc_torch.numpy(), tgc_values, atol=1e-4)}")

    # 4. Kiểm tra phiên bản chi tiết
    print(f"\n[4] Kiểm tra forward_detailed:")
    with torch.no_grad():
        detailed = tgc_module.forward_detailed(S_torch, m_torch)
    print(f"    Phần tuyến tính (trung bình): {detailed['linear_term'].mean():.4f}")
    print(f"    Phần phi tuyến (trung bình):  {detailed['cross_term'].mean():.4f}")
    print(f"    Top cặp tương tác mạnh nhất:")
    for syn in detailed['top_synergies']:
        print(f"      #{syn['rank']}: {syn['group_g']} × {syn['group_h']}"
              f" = {syn['cross_value']:.4f} ({syn['effect']}, γ={syn['gamma']:.1f})")

    # 5. Kiểm tra hàm Reward
    print(f"\n[5] Kiểm tra hàm compute_reward:")
    raw_feat_ok = np.zeros(72, dtype=np.float32)  # Dữ liệu sạch, không kích hoạt ràng buộc
    result_ok = compute_reward(
        S_test[0], m_test[0], raw_feat_ok,
        schedule_info={'finish_time': 100.0, 'active_resource_usage': {}},
        project_constraints={
            'total_budget': 1e8,
            'deadline': 200.0,
            'carbon_cap': 1e6,
            'resource_capacities': {},
            'min_quality': 0.0,
            'cumulative_tgc': 0.0,
            'cumulative_env_impact': 0.0,
        },
    )
    print(f"    Kịch bản hợp lệ: reward={result_ok['reward']:.4f}, "
          f"feasible={result_ok['is_feasible']}, violations={len(result_ok['violations'])}")

    raw_feat_bad = np.random.rand(72).astype(np.float32)
    result_bad = compute_reward(
        S_test[0], m_test[0], raw_feat_bad,
        schedule_info={'finish_time': 300.0, 'active_resource_usage': {'R1': 15.0}},
        project_constraints={
            'total_budget': 0.5,
            'deadline': 200.0,
            'carbon_cap': 0.1,
            'resource_capacities': {'R1': 10.0},
            'min_quality': 0.9,
            'cumulative_tgc': 0.0,
            'cumulative_env_impact': 0.0,
            'cumulative_ev': 50.0,
            'cumulative_pv': 100.0,
        },
        penalty_weight=1e4,
    )
    print(f"    Kịch bản vi phạm: reward={result_bad['reward']:.2f}, "
          f"feasible={result_bad['is_feasible']}, violations={len(result_bad['violations'])}")
    for v in result_bad['violations']:
        print(f"      ❌ {v['type']}: {v['description']}")

    print(f"\n{'=' * 70}")
    print("  HOÀN TẤT KIỂM TRA MÔ-ĐUN TGC TẦNG 3")
    print(f"{'=' * 70}")
