"""
Mô-đun pretraining_utils: Các hàm tiện ích bổ trợ cho Tiền huấn luyện Tự giám sát (Self-Supervised Pretraining)
==================================================================================================
Dự án: GLPO - Graph Logistics Project Optimization

Mô tả:
    Cung cấp các hàm bổ trợ cho Deep Graph Infomax (DGI) và các nhiệm vụ tự giám sát của DAGNN bao gồm:
    - Xáo trộn đặc trưng (Feature Shuffling) để tạo đồ thị bị nhiễu (Corrupted Graph).
    - Tạo vector đại diện đồ thị (Graph Summary Vector) qua các phương pháp Global Pooling.
    - Bộ phân biệt song tuyến tính (Bilinear Discriminator).
    - Che khuất thời lượng công việc (Duration Masking) cho Masked Duration Prediction.
    - Tìm đường đi ngắn nhất trên DAG (Shortest Path Computation) và lấy mẫu các cặp node (Node Pair Sampling)
      cho Topological Distance Prediction.
"""

import torch
import torch.nn as nn
import numpy as np
import random
from collections import defaultdict, deque
from typing import Optional, Tuple, List


class BilinearDiscriminator(nn.Module):
    """
    Bộ phân biệt song tuyến tính (Bilinear Discriminator) dùng trong Deep Graph Infomax.
    Tính toán xác suất tương quan (Mutual Information) giữa cục bộ (node embedding) và toàn cục (graph summary).
    
    Công thức toán học:
        D(h_i, s) = sigmoid(h_i^T * W * s)
    Trong đó:
        h_i: Node embedding [dim]
        s: Graph summary embedding [dim]
        W: Trọng số học được [dim, dim]
    """
    def __init__(self, dim: int):
        super(BilinearDiscriminator, self).__init__()
        self.weight = nn.Parameter(torch.Tensor(dim, dim))
        self.reset_parameters()

    def reset_parameters(self):
        """Khởi tạo trọng số bằng phân phối Xavier Uniform."""
        nn.init.xavier_uniform_(self.weight)

    def forward(self, h: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
        """
        Tính điểm số (raw logits) trước khi đưa qua sigmoid.
        """
        if s.dim() == 2:
            if s.size(0) == 1:
                s = s.squeeze(0)
            else:
                s_proj = torch.matmul(s, self.weight.t())  # [N, dim]
                return (h * s_proj).sum(dim=-1)

        s_proj = torch.matmul(self.weight, s)  # [dim]
        return torch.matmul(h, s_proj)


def corrupt_features_shuffling(x: torch.Tensor) -> torch.Tensor:
    """
    Xáo trộn các dòng của ma trận đặc trưng node (node features).
    Giúp giữ nguyên phân phối đặc trưng nhưng phá hủy mối liên kết cấu trúc đồ thị.
    """
    num_nodes = x.size(0)
    perm = torch.randperm(num_nodes, device=x.device)
    return x[perm]


def corrupt_graph(x: torch.Tensor, edge_index: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Tạo đồ thị bị nhiễu (corrupted graph) cho DGI bằng cách xáo trộn đặc trưng node.
    Giữ nguyên cấu trúc liên kết cạnh (edge_index).
    """
    return corrupt_features_shuffling(x), edge_index


def compute_graph_summary(z: torch.Tensor, batch: Optional[torch.Tensor] = None, pooling: str = 'mean') -> torch.Tensor:
    """
    Tính toán vector đại diện đồ thị (Graph Summary Vector) từ các node embeddings.
    """
    if batch is None:
        batch = torch.zeros(z.size(0), dtype=torch.long, device=z.device)
        
    if pooling == 'mean':
        from torch_geometric.nn import global_mean_pool
        return global_mean_pool(z, batch)
    elif pooling == 'add':
        from torch_geometric.nn import global_add_pool
        return global_add_pool(z, batch)
    elif pooling == 'max':
        from torch_geometric.nn import global_max_pool
        return global_max_pool(z, batch)
    else:
        raise ValueError(f"Không hỗ trợ phương thức pooling: {pooling}.")


# ============================================================================
# CÁC HÀM TIỆN ÍCH CHO TIỀN HUẤN LUYỆN DAGNN (CPM + MASK + TOPO)
# ============================================================================

def mask_node_duration(x: torch.Tensor, mask_ratio: Optional[float] = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Randomly masks the duration attributes (columns index 3: duration_days and 4: duration_hours)
    of approximately `mask_ratio` nodes by setting them to 0.0.
    
    Args:
        x: Tensor đặc trưng thô [N, 72]
        mask_ratio: Tỉ lệ che khuất. Nếu None hoặc bằng 0.15 (mặc định cũ), 
                    sẽ tính toán thích ứng dựa trên số lượng node N:
                    mask_ratio = clip(0.30 - 0.006 * N, min=0.10, max=0.35)
        
    Returns:
        masked_x: Đặc trưng sau khi che khuất duration [N, 72]
        mask: Tensor boolean chỉ ra node nào bị che [N]
        true_durations: Thời lượng gốc (ngày * 8 + giờ) [N]
    """
    num_nodes = x.size(0)
    
    # Tính tỷ lệ mask thích ứng nếu không được truyền hoặc truyền mặc định 0.15
    if mask_ratio is None or mask_ratio == 0.15:
        # clip(0.30 - 0.006 * N, min=0.10, max=0.35)
        calculated_ratio = 0.30 - 0.006 * num_nodes
        mask_ratio = max(0.10, min(0.35, calculated_ratio))
        
    # Tính thời lượng gốc: index 3 (ngày) * 8 + index 4 (giờ)
    true_durations = x[:, 3] * 8.0 + x[:, 4]
    
    # Tạo mask ngẫu nhiên
    rand = torch.rand(num_nodes, device=x.device)
    mask = (rand < mask_ratio)
    
    # Đảm bảo có ít nhất 1 node bị mask để tránh lỗi tính toán
    if not mask.any():
        idx = torch.randint(0, num_nodes, (1,), device=x.device)
        mask[idx] = True
        
    masked_x = x.clone()
    masked_x[mask, 3] = 0.0
    masked_x[mask, 4] = 0.0
    
    return masked_x, mask, true_durations


def compute_shortest_path_distances(edge_index: torch.Tensor, num_nodes: int) -> np.ndarray:
    """
    Tính khoảng cách đường đi ngắn nhất (Shortest Path Distance) giữa mọi cặp node trên DAG (có hướng).
    Nếu không có đường đi, trả về một giá trị mặc định lớn đại diện (ví dụ: num_nodes + 1).
    
    Sử dụng thuật toán BFS từ từng node vì đồ thị nhỏ (|V| <= 437).
    """
    adj = defaultdict(list)
    if edge_index.numel() > 0:
        srcs = edge_index[0].cpu().tolist()
        dsts = edge_index[1].cpu().tolist()
        for s, d in zip(srcs, dsts):
            adj[s].append(d)
            
    # Khoảng cách mặc định là num_nodes + 1 (unreachable)
    unreachable_val = float(num_nodes + 1)
    dist_matrix = np.full((num_nodes, num_nodes), unreachable_val, dtype=np.float32)
    for i in range(num_nodes):
        dist_matrix[i, i] = 0.0
        
    # Chạy BFS từ từng node
    for start in range(num_nodes):
        queue = deque([start])
        visited = {start}
        while queue:
            u = queue.popleft()
            d = dist_matrix[start, u]
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    dist_matrix[start, v] = d + 1.0
                    queue.append(v)
                    
    return dist_matrix


def sample_node_pairs(dist_matrix: np.ndarray, num_samples: int = 200) -> Tuple[List[int], List[int], List[float]]:
    """
    Lấy mẫu các cặp node để dự đoán khoảng cách topo.
    Chuẩn hóa nhãn giả khoảng cách topo về đoạn [0, 1] để tối ưu hóa việc học đa nhiệm.
    
    Args:
        dist_matrix: Ma trận khoảng cách [N, N]
        num_samples: Số lượng cặp cần lấy mẫu
        
    Returns:
        u_indices: Danh sách node nguồn
        v_indices: Danh sách node đích
        distances: Danh sách khoảng cách topo đã chuẩn hóa về [0, 1]
    """
    num_nodes = dist_matrix.shape[0]
    unreachable_val = float(num_nodes + 1)
    
    reachable_pairs = []
    unreachable_pairs = []
    
    for u in range(num_nodes):
        for v in range(num_nodes):
            if u == v:
                continue
            d = dist_matrix[u, v]
            if d < unreachable_val:
                # Chuẩn hóa về [0, 1)
                norm_d = float(d) / unreachable_val
                reachable_pairs.append((u, v, norm_d))
            else:
                # Không nối tới nhau -> đặt là 1.0 (mức tối đa)
                unreachable_pairs.append((u, v, 1.0))
                
    # Phối hợp 70% reachable và 30% unreachable
    n_reachable = min(int(num_samples * 0.7), len(reachable_pairs))
    n_unreachable = num_samples - n_reachable
    n_unreachable = min(n_unreachable, len(unreachable_pairs))
    
    sampled_reachable = random.sample(reachable_pairs, n_reachable) if reachable_pairs else []
    sampled_unreachable = random.sample(unreachable_pairs, n_unreachable) if unreachable_pairs else []
    
    all_samples = sampled_reachable + sampled_unreachable
    random.shuffle(all_samples)
    
    u_indices, v_indices, distances = [], [], []
    for u, v, d in all_samples:
        u_indices.append(u)
        v_indices.append(v)
        distances.append(d)
        
    return u_indices, v_indices, distances


def compute_longest_path_durations(edge_index: torch.Tensor, durations: np.ndarray, num_nodes: int) -> np.ndarray:
    """
    Tính thời lượng đường đi dài nhất (Longest Path Duration) giữa mọi cặp node trên DAG.
    Sử dụng quy hoạch động trên thứ tự tô-pô.
    """
    # Xây dựng danh sách kề
    adj = defaultdict(list)
    in_degree = defaultdict(int)
    if edge_index.numel() > 0:
        srcs = edge_index[0].cpu().tolist()
        dsts = edge_index[1].cpu().tolist()
        for s, d in zip(srcs, dsts):
            adj[s].append(d)
            in_degree[d] += 1

    # Topological Sort
    topo_order = []
    queue = deque([i for i in range(num_nodes) if in_degree[i] == 0])
    while queue:
        u = queue.popleft()
        topo_order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    visited = set(topo_order)
    for i in range(num_nodes):
        if i not in visited:
            topo_order.append(i)

    # dist_matrix[u, v] là thời lượng đường đi dài nhất từ u tới v.
    # Sử dụng giá trị -1.0 để biểu diễn unreachable
    dist_matrix = np.full((num_nodes, num_nodes), -1.0, dtype=np.float32)
    for i in range(num_nodes):
        dist_matrix[i, i] = 0.0

    # Với mỗi nút xuất phát start_node
    for start in range(num_nodes):
        # Ta chỉ tính toán cho các nút xuất hiện sau start trong topo order
        start_idx = topo_order.index(start)
        dp = np.full(num_nodes, -1.0, dtype=np.float32)
        dp[start] = 0.0
        
        for u in topo_order[start_idx:]:
            if dp[u] >= 0.0:
                for v in adj[u]:
                    # Thời lượng từ u tới v = dp[u] + duration[u]
                    dp[v] = max(dp[v], dp[u] + durations[u])
                    
        dist_matrix[start, :] = dp
        
    return dist_matrix


def sample_node_pairs_duration(dist_matrix: np.ndarray, num_samples: int = 200) -> Tuple[List[int], List[int], List[float]]:
    """
    Lấy mẫu các cặp node và trả về thời lượng đường đi dài nhất đã chuẩn hóa.
    """
    num_nodes = dist_matrix.shape[0]
    
    reachable_pairs = []
    unreachable_pairs = []
    
    # Tìm giá trị lớn nhất của đường đi để chuẩn hóa
    max_val = np.max(dist_matrix)
    if max_val <= 0:
        max_val = 1.0
        
    for u in range(num_nodes):
        for v in range(num_nodes):
            if u == v:
                continue
            d = dist_matrix[u, v]
            if d >= 0.0:
                # Chuẩn hóa về [0, 1]
                reachable_pairs.append((u, v, float(d / max_val)))
            else:
                unreachable_pairs.append((u, v, 1.0))
                
    n_reachable = min(int(num_samples * 0.7), len(reachable_pairs))
    n_unreachable = num_samples - n_reachable
    n_unreachable = min(n_unreachable, len(unreachable_pairs))
    
    sampled_reachable = random.sample(reachable_pairs, n_reachable) if reachable_pairs else []
    sampled_unreachable = random.sample(unreachable_pairs, n_unreachable) if unreachable_pairs else []
    
    all_samples = sampled_reachable + sampled_unreachable
    random.shuffle(all_samples)
    
    u_indices, v_indices, distances = [], [], []
    for u, v, d in all_samples:
        u_indices.append(u)
        v_indices.append(v)
        distances.append(d)
        
    return u_indices, v_indices, distances


def sample_gat_triplets(cpm_targets: torch.Tensor, num_samples: int = 150) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Lấy mẫu triplet (Anchor, Positive, Negative) cho GAT:
    - Anchor (a): Nút găng (is_critical == 1)
    - Positive (p): Nút găng khác (is_critical == 1)
    - Negative (n): Nút không găng (is_critical == 0)
    """
    # targets[:, 5] là is_critical
    is_critical = cpm_targets[:, 5].cpu().numpy()
    critical_indices = np.where(is_critical == 1.0)[0]
    non_critical_indices = np.where(is_critical == 0.0)[0]
    
    # Fallback nếu không đủ nút găng hoặc nút không găng
    num_nodes = len(is_critical)
    if len(critical_indices) < 2 or len(non_critical_indices) < 1:
        # Trả về các tensor rỗng
        device = cpm_targets.device
        return (torch.tensor([], dtype=torch.long, device=device), 
                torch.tensor([], dtype=torch.long, device=device), 
                torch.tensor([], dtype=torch.long, device=device))
        
    anchors = []
    positives = []
    negatives = []
    
    for _ in range(num_samples):
        a = random.choice(critical_indices)
        
        # Chọn positive khác anchor
        p_candidates = [idx for idx in critical_indices if idx != a]
        p = random.choice(p_candidates) if p_candidates else a
        
        n = random.choice(non_critical_indices)
        
        anchors.append(a)
        positives.append(p)
        negatives.append(n)
        
    device = cpm_targets.device
    return (torch.tensor(anchors, dtype=torch.long, device=device),
            torch.tensor(positives, dtype=torch.long, device=device),
            torch.tensor(negatives, dtype=torch.long, device=device))
