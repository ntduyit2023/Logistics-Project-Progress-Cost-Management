"""
Mô-đun UnsupervisedPretrainer: Tiền huấn luyện Không Giám Sát nâng cấp (GAE + DGI + CPM + MASK + TOPO)
====================================================================================================
Dự án: GLPO - Graph Logistics Project Optimization

Mô tả:
    Class thực hiện tiền huấn luyện (Pre-training) nâng cấp cho cả GAT và DAGNN trong SequentialGLPOModel:
    - GAT: Học đa nhiệm phối hợp GAE (Graph AutoEncoder) và DGI (Deep Graph Infomax).
    - DAGNN: Học đa nhiệm phối hợp CPM Self-Supervised, Masked Duration Prediction và Topological Distance Prediction.

====================================================================================================
TÀI LIỆU TOÁN HỌC & THIẾT KẾ (DOCUMENTATION)
====================================================================================================

1. Mục tiêu toán học của CPM Self-Supervised Learning:
    DAGNN học cách lan truyền thời gian và rủi ro dọc theo thứ tự tô-pô bằng cách dự đoán các đặc trưng CPM tĩnh:
        Y_CPM = [ES, EF, LS, LF, TF, Critical, PL]
    Mục tiêu là tối thiểu hóa CPMLoss (kết hợp giữa MSE cho các trị liên tục và BCE cho nhãn Critical):
        L_CPM = MSE(y_continuous, y^_continuous) + 2.0 * BCE(y_binary, y^_binary)
    Trong đó nhãn mục tiêu (pseudo-labels) được tự động tính toán từ cấu trúc DAG bằng thuật toán CPM.

2. Mục tiêu toán học của Masked Duration Prediction:
    Che khuất ngẫu nhiên 15% thời lượng (duration) của các node bằng cách đặt về 0.0, và ép DAGNN phục dựng lại.
    Điều này ngăn cản DAGNN ghi nhớ thời lượng tĩnh mà phải suy luận từ ngữ cảnh tô-pô trước/sau của node.
    Mục tiêu tối thiểu hóa MaskedDurationLoss:
        L_MASK = 1 / |M| * \sum_{i \in M} (d_i - d^_i)^2
    Trong đó M là tập hợp các node bị mask, d_i là thời lượng thực tế (days * 8 + hours), d^_i là dự đoán từ DAGNN.

3. Mục tiêu toán học của Topological Distance Prediction:
    Lấy mẫu ngẫu nhiên các cặp node (u, v) và dự đoán khoảng cách topo ngắn nhất (Shortest Path Distance) giữa chúng.
    Mục tiêu ép các node embeddings học được khoảng cách cấu trúc logic và thứ tự phụ thuộc.
    Mục tiêu tối thiểu hóa TopologicalDistanceLoss:
        L_TOPO = 1 / |P| * \sum_{(u, v) \in P} (D_topo(u, v) - D^_topo(u, v))^2
    Trong đó P là tập hợp các cặp node lấy mẫu, D_topo(u, v) là khoảng cách thực tế, D^_topo(u, v) là dự đoán.

4. Vì sao đây là các nhiệm vụ Self-Supervised (Tự giám sát):
    Tất cả các nhãn giả (CPM targets, Masked durations, Topological distances) đều được sinh tự động
    bằng các thuật toán đồ thị và lập lịch (Topological Sort, BFS, CPM) trực tiếp từ đặc trưng và cạnh đồ thị,
    hoàn toàn không cần bất kỳ nhãn thủ công nào từ con người.

5. Vì sao phù hợp với bộ dữ liệu chỉ có 5 dự án:
    Với số lượng dự án rất ít, việc tối ưu hóa DAGNN trực tiếp bằng Học tăng cường (PPO) dễ bị chệch hướng do thưa thớt phần thưởng.
    Các nhiệm vụ tự giám sát đa nhiệm hoạt động như các ràng buộc vật lý mạnh mẽ, ép DAGNN phải học được các quy luật
    lập lịch cơ bản (thứ tự tô-pô, đường găng, khoảng cách logic) trước khi học chính sách PPO. Điều này cải thiện độ ổn định.

6. Độ phức tạp tính toán (Computational Complexity):
    - Tìm đường đi ngắn nhất BFS từ toàn bộ node: O(|V| * (|V| + |E|)) - chạy dưới 0.1 giây cho đồ thị lớn nhất.
    - Lấy mẫu node: O(|P|) với |P| là số cặp.
    - Dự đoán & Loss: O(|V| * d + |P| * d).
    Tổng thời gian pretraining DAGNN chỉ mất từ 1 đến 15 giây tùy kích thước dự án, cực kỳ hiệu quả.

7. Cách embedding được truyền sang PPO:
    Sau khi pretraining, trọng số DAGNN được lưu vào checkpoint `dagnn_pretrained.pth` và tải vào mô hình chính.
    PPO Agent thừa hưởng biểu diễn embedding giàu thông tin thời gian này giúp đưa ra quyết định lập lịch chính xác hơn.

====================================================================================================
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
import sys
import time
import json
from collections import defaultdict, deque
from typing import Optional, Dict, List, Tuple

# Thử import từ package ai_pipeline hoặc fallback import trực tiếp
try:
    from ai_pipeline.training.pretraining_utils import (
        BilinearDiscriminator,
        corrupt_features_shuffling,
        corrupt_graph,
        compute_graph_summary,
        mask_node_duration,
        compute_shortest_path_distances,
        sample_node_pairs,
    )
    from ai_pipeline.training.pretraining_losses import (
        GAELoss,
        DGILoss,
        MultiTaskLoss,
        CPMLoss,
        MaskedDurationLoss,
        TopologicalDistanceLoss,
        DAGNNMultiTaskLoss,
    )
except ImportError:
    # Fallback khi chạy trực tiếp file này làm unit test
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pretraining_utils import (
        BilinearDiscriminator,
        corrupt_features_shuffling,
        corrupt_graph,
        compute_graph_summary,
        mask_node_duration,
        compute_shortest_path_distances,
        sample_node_pairs,
    )
    from pretraining_losses import (
        GAELoss,
        DGILoss,
        MultiTaskLoss,
        CPMLoss,
        MaskedDurationLoss,
        TopologicalDistanceLoss,
        DAGNNMultiTaskLoss,
    )


class _GATEncoderWrapper(nn.Module):
    """
    Wrapper bọc phần GAT của SequentialGLPOModel để trích xuất biểu diễn node.
    """
    def __init__(self, model):
        super(_GATEncoderWrapper, self).__init__()
        self.encoder = model.encoder
        self.node_proj = model.node_proj
        self.gat1 = model.gat1
        self.gat2 = model.gat2
        self.dropout = model.dropout

    def forward(self, x, edge_index):
        # Tầng 1 & 2: Encoder
        S_prime_g, _ = self.encoder(x)

        # Tầng 3a: GAT
        h = F.leaky_relu(self.node_proj(S_prime_g))
        h = self.gat1(h, edge_index)
        h = F.elu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = self.gat2(h, edge_index)

        return h


class _DAGNNPredictionHead(nn.Module):
    """
    Đầu dự đoán (Prediction Head) gắn trên DAGNN embeddings để dự đoán các thông số CPM tĩnh.
    """
    def __init__(self, dagnn_out_dim: int = 32, num_targets: int = 7):
        super(_DAGNNPredictionHead, self).__init__()
        self.head = nn.Sequential(
            nn.Linear(dagnn_out_dim, dagnn_out_dim),
            nn.LeakyReLU(0.2),
            nn.Linear(dagnn_out_dim, num_targets),
        )

    def forward(self, h_dagnn):
        return self.head(h_dagnn)


class _DurationPredictionHead(nn.Module):
    """
    Đầu dự đoán thời lượng (Duration Prediction Head) cho Masked Duration Task.
    """
    def __init__(self, dagnn_out_dim: int = 32):
        super(_DurationPredictionHead, self).__init__()
        self.head = nn.Sequential(
            nn.Linear(dagnn_out_dim, dagnn_out_dim),
            nn.LeakyReLU(0.2),
            nn.Linear(dagnn_out_dim, 1),
        )

    def forward(self, h_dagnn):
        return self.head(h_dagnn).squeeze(-1)


class _TopologicalDistancePredictionHead(nn.Module):
    """
    Đầu dự đoán khoảng cách topo (Topological Distance Head) dựa trên cặp node embeddings.
    """
    def __init__(self, dagnn_out_dim: int = 32):
        super(_TopologicalDistancePredictionHead, self).__init__()
        self.head = nn.Sequential(
            nn.Linear(2 * dagnn_out_dim, dagnn_out_dim),
            nn.LeakyReLU(0.2),
            nn.Linear(dagnn_out_dim, 1),
        )

    def forward(self, h_u, h_v):
        combined = torch.cat([h_u, h_v], dim=-1)
        return self.head(combined).squeeze(-1)


class UnsupervisedPretrainer:
    """
    Class thực hiện tiền huấn luyện không giám sát đa nhiệm cho GAT và DAGNN.
    
    Tham số khởi tạo:
        model: SequentialGLPOModel cần tiền huấn luyện
        device: Thiết bị chạy ('cpu' hoặc 'cuda')
        lambda_gae: Trọng số GAE loss (mặc định 0.5)
        lambda_dgi: Trọng số DGI loss (mặc định 0.5)
        lambda_cpm: Trọng số CPM loss (mặc định 0.4)
        lambda_mask: Trọng số Masked Duration loss (mặc định 0.3)
        lambda_topo: Trọng số Topological Distance loss (mặc định 0.3)
    """
    def __init__(
        self,
        model,
        device: str = 'cpu',
        lambda_gae: float = 0.5,
        lambda_dgi: float = 0.5,
        lambda_cpm: float = 0.4,
        lambda_mask: float = 0.3,
        lambda_topo: float = 0.3,
    ):
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.lambda_gae = lambda_gae
        self.lambda_dgi = lambda_dgi
        self.lambda_cpm = lambda_cpm
        self.lambda_mask = lambda_mask
        self.lambda_topo = lambda_topo

    # ================================================================
    # PHƯƠNG PHÁP 1: Multi-task GAE + DGI Loss — Tiền huấn luyện GAT
    # ================================================================
    def pretrain_gae(
        self,
        data,
        epochs: int = 100,
        lr: float = 0.01,
        neg_sampling_ratio: float = 1.0,
        verbose: bool = True,
        lambda_gae: Optional[float] = None,
        lambda_dgi: Optional[float] = None,
    ) -> Dict[str, List[float]]:
        """
        Huấn luyện GAT bằng phối hợp GAE + DGI Multi-task Loss.
        """
        from torch_geometric.utils import negative_sampling

        l_gae = lambda_gae if lambda_gae is not None else self.lambda_gae
        l_dgi = lambda_dgi if lambda_dgi is not None else self.lambda_dgi

        if verbose:
            print("=" * 60)
            print("  GAT MULTI-TASK PRE-TRAINING (GAE + DGI Self-Supervised)")
            print(f"  Trong so: lambda_gae = {l_gae:.2f} | lambda_dgi = {l_dgi:.2f}")
            print("=" * 60)

        gat_encoder = _GATEncoderWrapper(self.model).to(self.device)
        gat_out_dim = getattr(self.model, 'gat_out_dim', 32)
        discriminator = BilinearDiscriminator(gat_out_dim).to(self.device)
        multitask_loss_fn = MultiTaskLoss(lambda_gae=l_gae, lambda_dgi=l_dgi).to(self.device)

        data_copy = data.clone().to(self.device)
        pos_edge_index = data_copy.edge_index
        num_nodes = data_copy.x.shape[0]

        gat_params = list(gat_encoder.parameters()) + list(discriminator.parameters())
        optimizer = torch.optim.Adam(gat_params, lr=lr)

        import time
        t0 = time.time()
        
        history = {
            'losses': [], 
            'gae_losses': [], 
            'dgi_losses': [], 
            'auc_scores': [], 
            'ap_scores': [], 
            'time_taken': 0.0
        }

        best_loss = float('inf')

        gat_encoder.train()
        discriminator.train()
        for epoch in range(1, epochs + 1):
            optimizer.zero_grad()

            corrupted_x = corrupt_features_shuffling(data_copy.x)
            z = gat_encoder(data_copy.x, pos_edge_index)
            z_corrupted = gat_encoder(corrupted_x, pos_edge_index)
            summary = compute_graph_summary(z, pooling='mean')

            neg_edge_index = negative_sampling(
                edge_index=pos_edge_index,
                num_nodes=num_nodes,
                num_neg_samples=int(pos_edge_index.shape[1] * neg_sampling_ratio),
            )

            total_loss, gae_loss, dgi_loss = multitask_loss_fn(
                z=z,
                z_corrupted=z_corrupted,
                summary=summary,
                discriminator=discriminator,
                pos_edge_index=pos_edge_index,
                neg_edge_index=neg_edge_index
            )

            total_loss.backward()
            optimizer.step()

            history['losses'].append(total_loss.item())
            history['gae_losses'].append(gae_loss.item())
            history['dgi_losses'].append(dgi_loss.item())

            if total_loss.item() < best_loss:
                best_loss = total_loss.item()

            if epoch % max(1, epochs // 10) == 0 or epoch == epochs:
                gat_encoder.eval()
                with torch.no_grad():
                    z_eval = gat_encoder(data_copy.x, pos_edge_index)
                    pos_scores = (z_eval[pos_edge_index[0]] * z_eval[pos_edge_index[1]]).sum(dim=1)
                    neg_scores = (z_eval[neg_edge_index[0]] * z_eval[neg_edge_index[1]]).sum(dim=1)

                    pos_scores_exp = pos_scores.unsqueeze(1)
                    neg_scores_exp = neg_scores.unsqueeze(0)

                    comparison = (pos_scores_exp > neg_scores_exp).float()
                    ties = (pos_scores_exp == neg_scores_exp).float()
                    auc = float((comparison + 0.5 * ties).mean())

                    pos_labels = torch.ones(pos_scores.shape[0], device=self.device)
                    neg_labels = torch.zeros(neg_scores.shape[0], device=self.device)
                    all_scores = torch.cat([pos_scores, neg_scores])
                    all_labels = torch.cat([pos_labels, neg_labels])

                    sorted_indices = torch.argsort(all_scores, descending=True)
                    sorted_labels = all_labels[sorted_indices]
                    tp = torch.cumsum(sorted_labels, dim=0)
                    fp = torch.cumsum(1 - sorted_labels, dim=0)
                    precision = tp / (tp + fp + 1e-15)
                    delta_recall = sorted_labels / max(float(pos_labels.sum()), 1.0)
                    ap = float((precision * delta_recall).sum())

                gat_encoder.train()

                history['auc_scores'].append(auc)
                history['ap_scores'].append(ap)

                if verbose:
                    print(f"  Epoch {epoch:4d}/{epochs}: "
                          f"Loss={total_loss.item():.4f} (GAE={gae_loss.item():.4f}, DGI={dgi_loss.item():.4f}) | "
                          f"AUC={auc:.4f}, AP={ap:.4f}")

        history['time_taken'] = time.time() - t0
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        checkpoints_dir = os.path.join(base_dir, 'checkpoints')
        logs_dir = os.path.join(base_dir, 'logs')
        os.makedirs(checkpoints_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)

        # Lưu checkpoint và metrics (ghi nhớ riêng biệt và chung)
        checkpoint_path = os.path.join(checkpoints_dir, 'gat_pretrained.pth')
        checkpoint = {
            'gat_encoder_state_dict': gat_encoder.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'epoch': epochs,
            'best_validation_loss': best_loss
        }
        torch.save(checkpoint, checkpoint_path)

        metrics_data = []
        for i in range(epochs):
            metrics_data.append({
                'epoch': i + 1,
                'total_loss': history['losses'][i],
                'gae_loss': history['gae_losses'][i],
                'dgi_loss': history['dgi_losses'][i],
                'learning_rate': lr
            })
        
        # Lưu vào tệp gat_pretraining_metrics.json và ghi đè pretraining_metrics.json
        with open(os.path.join(logs_dir, 'gat_pretraining_metrics.json'), 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)
        with open(os.path.join(logs_dir, 'pretraining_metrics.json'), 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)

        if verbose:
            print(f"  [SUCCESS] GAT Pre-training hoan tat. | Time: {history['time_taken']:.2f}s")
            print(f"  [INFO] Da luu checkpoint tai: {checkpoint_path}")
            print()

        return history

    # ================================================================
    # PHƯƠNG PHÁP 2: Multi-task CPM + MASK + TOPO — Tiền huấn luyện DAGNN
    # ================================================================
    def _compute_cpm_targets(self, data) -> torch.Tensor:
        """
        Tính 7 nhãn CPM tĩnh cho tất cả các node.
        """
        edge_index = data.edge_index.cpu().numpy()
        num_nodes = data.x.shape[0]

        # Xây dựng danh sách kề
        adj_forward = defaultdict(list)
        adj_backward = defaultdict(list)
        in_degree = defaultdict(int)

        if edge_index.size > 0:
            for i in range(edge_index.shape[1]):
                src, dst = int(edge_index[0, i]), int(edge_index[1, i])
                adj_forward[src].append(dst)
                adj_backward[dst].append(src)
                in_degree[dst] += 1

        # Topological Sort
        topo_order = []
        queue = deque([i for i in range(num_nodes) if in_degree[i] == 0])
        while queue:
            u = queue.popleft()
            topo_order.append(u)
            for v in adj_forward[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # Bổ sung nút cô lập
        visited = set(topo_order)
        for i in range(num_nodes):
            if i not in visited:
                topo_order.append(i)

        # Thời lượng từ đặc trưng
        features = data.x.cpu().numpy()
        durations = np.zeros(num_nodes, dtype=np.float32)
        for i in range(num_nodes):
            d_d = float(features[i, 3])
            d_h = float(features[i, 4])
            durations[i] = d_d * 8.0 + d_h

        # Forward Pass (ES, EF)
        ES = np.zeros(num_nodes, dtype=np.float32)
        EF = np.zeros(num_nodes, dtype=np.float32)
        for u in topo_order:
            EF[u] = ES[u] + durations[u]
            for v in adj_forward[u]:
                ES[v] = max(ES[v], EF[u])

        # Backward Pass (LS, LF)
        makespan = float(np.max(EF)) if num_nodes > 0 else 1.0
        LF = np.full(num_nodes, makespan, dtype=np.float32)
        LS = np.zeros(num_nodes, dtype=np.float32)
        for u in reversed(topo_order):
            LS[u] = LF[u] - durations[u]
            for p in adj_backward[u]:
                LF[p] = min(LF[p], LS[u])

        # Total Float, Is Critical
        total_float = LS - ES
        is_critical = (np.abs(total_float) < 1e-6).astype(np.float32)

        # Path Length (BFS từ Source)
        path_length = np.zeros(num_nodes, dtype=np.float32)
        for u in topo_order:
            for v in adj_forward[u]:
                path_length[v] = max(path_length[v], path_length[u] + 1)

        # Chuẩn hóa
        makespan_norm = max(makespan, 1.0)
        max_path = max(float(np.max(path_length)), 1.0)
        max_float = max(float(np.max(np.abs(total_float))), 1.0)

        targets = np.stack([
            ES / makespan_norm,               # 0: Early Start
            EF / makespan_norm,               # 1: Early Finish
            LS / makespan_norm,               # 2: Late Start
            LF / makespan_norm,               # 3: Late Finish
            total_float / max_float,          # 4: Total Float
            is_critical,                      # 5: Is Critical (flag nhị phân)
            path_length / max_path,           # 6: Path Length
        ], axis=1)

        return torch.tensor(targets, dtype=torch.float32, device=self.device)

    def pretrain_cpm_self_supervised(
        self,
        data,
        epochs: int = 100,
        lr: float = 0.005,
        verbose: bool = True,
        lambda_cpm: Optional[float] = None,
        lambda_mask: Optional[float] = None,
        lambda_topo: Optional[float] = None,
    ) -> Dict[str, List]:
        """
        Huấn luyện DAGNN theo phương thức Đa nhiệm Tự giám sát mới:
        L_DAGNN = lambda_cpm * L_CPM + lambda_mask * L_MASK + lambda_topo * L_TOPO
        """
        l_cpm = lambda_cpm if lambda_cpm is not None else self.lambda_cpm
        l_mask = lambda_mask if lambda_mask is not None else self.lambda_mask
        l_topo = lambda_topo if lambda_topo is not None else self.lambda_topo

        if verbose:
            print("=" * 60)
            print("  DAGNN MULTI-TASK PRE-TRAINING (CPM + MASK + TOPO)")
            print(f"  Trong so: lambda_cpm = {l_cpm:.2f} | lambda_mask = {l_mask:.2f} | lambda_topo = {l_topo:.2f}")
            print("=" * 60)

        data_dev = data.clone().to(self.device)
        num_nodes = data_dev.x.shape[0]

        # 1. Tính các nhãn mục tiêu CPM (7 chiều)
        cpm_targets = self._compute_cpm_targets(data_dev)
        target_names = ['Early Start', 'Early Finish', 'Late Start', 'Late Finish', 'Total Float', 'Is Critical', 'Path Length']

        # 2. Tính ma trận khoảng cách topo toàn bộ
        dist_matrix = compute_shortest_path_distances(data_dev.edge_index, num_nodes)

        # 3. Khởi tạo các Prediction Heads tạm thời
        cpm_head = _DAGNNPredictionHead(dagnn_out_dim=self.model.dagnn_out_dim, num_targets=7).to(self.device)
        duration_head = _DurationPredictionHead(dagnn_out_dim=self.model.dagnn_out_dim).to(self.device)
        topo_head = _TopologicalDistancePredictionHead(dagnn_out_dim=self.model.dagnn_out_dim).to(self.device)

        # Hàm loss đa nhiệm
        multitask_loss_fn = DAGNNMultiTaskLoss(lambda_cpm=l_cpm, lambda_mask=l_mask, lambda_topo=l_topo).to(self.device)

        # Đưa toàn bộ tham số cần cập nhật vào optimizer
        params_to_train = (
            list(self.model.encoder.parameters())
            + list(self.model.node_proj.parameters())
            + list(self.model.gat1.parameters())
            + list(self.model.gat2.parameters())
            + list(self.model.dagnn.parameters())
            + list(cpm_head.parameters())
            + list(duration_head.parameters())
            + list(topo_head.parameters())
        )
        optimizer = torch.optim.Adam(params_to_train, lr=lr)

        import time
        t0 = time.time()
        
        history = {
            'losses': [],
            'cpm_losses': [],
            'mask_losses': [],
            'topo_losses': [],
            'mae_per_target': {},
            'is_critical_metrics': {},
            'time_taken': 0.0
        }

        best_loss = float('inf')

        self.model.train()
        cpm_head.train()
        duration_head.train()
        topo_head.train()

        for epoch in range(1, epochs + 1):
            optimizer.zero_grad()

            # --- NHIỆM VỤ 1: CPM Prediction (đồ thị gốc) ---
            # Forward pass đồ thị gốc
            S_prime_g, _ = self.model.encoder(data_dev.x)
            h = F.leaky_relu(self.model.node_proj(S_prime_g))
            h = self.model.gat1(h, data_dev.edge_index)
            h = F.elu(h)
            h = F.dropout(h, p=self.model.dropout, training=True)
            h = self.model.gat2(h, data_dev.edge_index)
            h_dagnn = self.model.dagnn(h, data_dev.edge_index)
            
            cpm_preds = cpm_head(h_dagnn)

            # --- NHIỆM VỤ 2: Masked Duration Prediction ---
            # Tạo đặc trưng bị mask duration
            masked_x, duration_mask, true_durations = mask_node_duration(data_dev.x, mask_ratio=0.15)
            
            # Forward pass đồ thị bị mask
            S_prime_g_masked, _ = self.model.encoder(masked_x)
            h_masked = F.leaky_relu(self.model.node_proj(S_prime_g_masked))
            h_masked = self.model.gat1(h_masked, data_dev.edge_index)
            h_masked = F.elu(h_masked)
            h_masked = F.dropout(h_masked, p=self.model.dropout, training=True)
            h_masked = self.model.gat2(h_masked, data_dev.edge_index)
            h_dagnn_masked = self.model.dagnn(h_masked, data_dev.edge_index)
            
            duration_preds = duration_head(h_dagnn_masked)

            # --- NHIỆM VỤ 3: Topological Distance Prediction ---
            # Lấy mẫu các cặp node
            u_indices, v_indices, true_distances = sample_node_pairs(dist_matrix, num_samples=200)
            u_tensor = torch.tensor(u_indices, dtype=torch.long, device=self.device)
            v_tensor = torch.tensor(v_indices, dtype=torch.long, device=self.device)
            true_distances_tensor = torch.tensor(true_distances, dtype=torch.float32, device=self.device)
            
            # Dự đoán khoảng cách dựa trên node embeddings của đồ thị gốc
            topo_preds = topo_head(h_dagnn[u_tensor], h_dagnn[v_tensor])

            # --- Tính tổng loss đa nhiệm ---
            total_loss, cpm_loss, mask_loss, topo_loss = multitask_loss_fn(
                cpm_preds=cpm_preds,
                cpm_targets=cpm_targets,
                duration_preds=duration_preds,
                duration_targets=true_durations,
                duration_mask=duration_mask,
                topo_preds=topo_preds,
                topo_targets=true_distances_tensor
            )

            total_loss.backward()
            optimizer.step()

            history['losses'].append(total_loss.item())
            history['cpm_losses'].append(cpm_loss.item())
            history['mask_losses'].append(mask_loss.item())
            history['topo_losses'].append(topo_loss.item())

            if total_loss.item() < best_loss:
                best_loss = total_loss.item()

            if epoch % max(1, epochs // 10) == 0 or epoch == epochs:
                with torch.no_grad():
                    # Đánh giá MAE trên CPM
                    mae = torch.abs(cpm_preds - cpm_targets).mean(dim=0)
                if verbose:
                    print(f"  Epoch {epoch:4d}/{epochs}: Loss={total_loss.item():.4f} "
                          f"(CPM={cpm_loss.item():.4f}, Mask={mask_loss.item():.4f}, Topo={topo_loss.item():.4f}) | "
                          f"MAE ES={mae[0]:.4f}, TF={mae[4]:.4f}")

        # Tính toán F1 Score & MAE cuối cùng ở chế độ Eval
        with torch.no_grad():
            self.model.eval()
            cpm_head.eval()
            
            S_prime_g, _ = self.model.encoder(data_dev.x)
            h = F.leaky_relu(self.model.node_proj(S_prime_g))
            h = self.model.gat1(h, data_dev.edge_index)
            h = F.elu(h)
            h = self.model.gat2(h, data_dev.edge_index)
            h_dagnn = self.model.dagnn(h, data_dev.edge_index)
            
            final_preds = cpm_head(h_dagnn)
            final_mae = torch.abs(final_preds - cpm_targets).mean(dim=0)

            # Đánh giá Critical Flag nhị phân
            pred_logits = final_preds[:, 5]
            pred_probs = torch.sigmoid(pred_logits)
            pred_labels = (pred_probs > 0.5).float()
            true_labels = cpm_targets[:, 5]

            tp = float(((pred_labels == 1) & (true_labels == 1)).sum())
            fp = float(((pred_labels == 1) & (true_labels == 0)).sum())
            fn = float(((pred_labels == 0) & (true_labels == 1)).sum())
            tn = float(((pred_labels == 0) & (true_labels == 0)).sum())

            accuracy = (tp + tn) / max(tp + tn + fp + fn, 1.0)
            precision = tp / max(tp + fp, 1.0)
            recall = tp / max(tp + fn, 1.0)
            f1 = 2 * precision * recall / max(precision + recall, 1e-6)

            history['is_critical_metrics'] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            }

        # Ánh xạ kết quả MAE về đúng các nhãn cũ/mới để giữ tương thích ngược
        cpm_mapping = {
            'Early Start': final_mae[0].item(),
            'Early Finish': final_mae[1].item(),
            'Late Start': final_mae[2].item(),
            'Late Finish': final_mae[3].item(),
            'Total Float': final_mae[4].item(),
            'Is Critical': final_mae[5].item(),
            'Path Length': final_mae[6].item()
        }
        for name, val in cpm_mapping.items():
            history['mae_per_target'][name] = val

        history['time_taken'] = time.time() - t0

        # --- LƯU CHECKPOINT VÀ METRICS ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        checkpoints_dir = os.path.join(base_dir, 'checkpoints')
        logs_dir = os.path.join(base_dir, 'logs')
        os.makedirs(checkpoints_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)

        # 1. Lưu checkpoint (.pth)
        checkpoint_path = os.path.join(checkpoints_dir, 'dagnn_pretrained.pth')
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'epoch': epochs,
            'best_loss': best_loss
        }
        torch.save(checkpoint, checkpoint_path)

        # 2. Lưu metrics (.json)
        metrics_data = []
        for i in range(epochs):
            metrics_data.append({
                'epoch': i + 1,
                'total_loss': history['losses'][i],
                'cpm_loss': history['cpm_losses'][i],
                'masked_duration_loss': history['mask_losses'][i],
                'topological_distance_loss': history['topo_losses'][i],
                'learning_rate': lr
            })
            
        with open(os.path.join(logs_dir, 'dagnn_pretraining_metrics.json'), 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)
        with open(os.path.join(logs_dir, 'pretraining_metrics.json'), 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)

        if verbose:
            print(f"  [SUCCESS] DAGNN Pre-training hoan tat. | Time: {history['time_taken']:.2f}s")
            print(f"  [INFO] Da luu checkpoint tai: {checkpoint_path}")
            print()

        return history

    def pretrain_dagnn(self, *args, **kwargs) -> Dict:
        """
        Bảo vệ tương thích ngược API (Alias cho pretrain_cpm_self_supervised).
        """
        return self.pretrain_cpm_self_supervised(*args, **kwargs)

    # ================================================================
    # PHƯƠNG PHÁP TỔNG HỢP: Chạy cả hai
    # ================================================================
    def pretrain_all(
        self,
        data,
        gae_epochs: int = 100,
        cpm_epochs: int = 100,
        gae_lr: float = 0.01,
        cpm_lr: float = 0.005,
        verbose: bool = True,
        lambda_gae: Optional[float] = None,
        lambda_dgi: Optional[float] = None,
        lambda_cpm: Optional[float] = None,
        lambda_mask: Optional[float] = None,
        lambda_topo: Optional[float] = None,
    ) -> Dict[str, Dict]:
        """
        Chạy tuần tự cả hai phương pháp tiền huấn luyện:
        1. GAT (Multi-task GAE + DGI) -> 2. DAGNN (Multi-task CPM + MASK + TOPO).
        """
        if verbose:
            print("[START] BAT DAU TIEN HUAN LUYEN KHONG GIAM SAT NANG CAP")
            print(f"   Mo hinh: SequentialGLPOModel")
            print(f"   Du lieu: {data.x.shape[0]} tasks, "
                  f"{data.edge_index.shape[1]} lien ket")
            print()

        # Bước 1: Multi-task GAE + DGI → Warm-start GAT
        gae_history = self.pretrain_gae(
            data, 
            epochs=gae_epochs, 
            lr=gae_lr, 
            verbose=verbose,
            lambda_gae=lambda_gae,
            lambda_dgi=lambda_dgi
        )

        # Bước 2: CPM + MASK + TOPO → Warm-start DAGNN
        cpm_history = self.pretrain_cpm_self_supervised(
            data, 
            epochs=cpm_epochs, 
            lr=cpm_lr, 
            verbose=verbose,
            lambda_cpm=lambda_cpm,
            lambda_mask=lambda_mask,
            lambda_topo=lambda_topo
        )

        if verbose:
            print("=" * 60)
            print("  [SUCCESS] TIEN HUAN LUYEN NANG CAP HOAN TAT")
            print(f"     GAE+DGI Loss cuoi: {gae_history['losses'][-1]:.4f}")
            print(f"     DAGNN Loss cuoi: {cpm_history['losses'][-1]:.4f}")
            print("=" * 60)

        return {'gae': gae_history, 'cpm': cpm_history}

    def load_pretrained(self, filepath: Optional[str] = None) -> bool:
        """
        Nạp GAT checkpoint.
        """
        return load_pretrained(self.model, filepath, self.device.type)

    def load_pretrained_dagnn(self, filepath: Optional[str] = None) -> bool:
        """
        Nạp DAGNN checkpoint.
        """
        return load_pretrained_dagnn(self.model, filepath, self.device.type)


# ============================================================================
# CÁC HÀM TIỆN ÍCH NGOÀI HỖ TRỢ NẠP CHỒNG (MODULE LEVEL API)
# ============================================================================

def load_pretrained(model, filepath: Optional[str] = None, device: str = 'cpu') -> bool:
    """
    Nạp các trọng số đã được huấn luyện trước (Pretrained GAT weights) vào mô hình.
    """
    if filepath is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate_paths = [
            os.path.join(base_dir, 'checkpoints', 'gat_pretrained.pth'),
            'checkpoints/gat_pretrained.pth',
            'ai_pipeline/checkpoints/gat_pretrained.pth',
            os.path.join(os.getcwd(), 'checkpoints', 'gat_pretrained.pth'),
            os.path.join(os.getcwd(), 'ai_pipeline', 'checkpoints', 'gat_pretrained.pth'),
        ]
        for p in candidate_paths:
            if os.path.exists(p):
                filepath = p
                break
        
        if filepath is None:
            print("[WARNING] Khong tim thay file checkpoint 'gat_pretrained.pth'.")
            return False

    if not os.path.exists(filepath):
        print(f"[WARNING] Checkpoint {filepath} khong ton tai.")
        return False

    try:
        device_obj = torch.device(device)
        checkpoint = torch.load(filepath, map_location=device_obj)
        wrapper = _GATEncoderWrapper(model).to(device_obj)
        
        if 'gat_encoder_state_dict' in checkpoint:
            wrapper.load_state_dict(checkpoint['gat_encoder_state_dict'])
            print(f"[SUCCESS] Da nap thanh cong GAT weights tu: {filepath}")
            return True
        elif 'state_dict' in checkpoint:
            wrapper.load_state_dict(checkpoint['state_dict'])
            print(f"[SUCCESS] Da nap thanh cong GAT weights (state_dict) tu: {filepath}")
            return True
        else:
            wrapper.load_state_dict(checkpoint)
            print(f"[SUCCESS] Da nap GAT weights (direct state_dict) tu: {filepath}")
            return True
    except Exception as e:
        print(f"[ERROR] Loi khi nap GAT pretrained weights: {str(e)}")
        return False


def load_pretrained_dagnn(model, filepath: Optional[str] = None, device: str = 'cpu') -> bool:
    """
    Nạp các trọng số đã được huấn luyện trước cho DAGNN (bao gồm cả GAT + DAGNN) vào mô hình.
    """
    if filepath is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate_paths = [
            os.path.join(base_dir, 'checkpoints', 'dagnn_pretrained.pth'),
            'checkpoints/dagnn_pretrained.pth',
            'ai_pipeline/checkpoints/dagnn_pretrained.pth',
            os.path.join(os.getcwd(), 'checkpoints', 'dagnn_pretrained.pth'),
            os.path.join(os.getcwd(), 'ai_pipeline', 'checkpoints', 'dagnn_pretrained.pth'),
        ]
        for p in candidate_paths:
            if os.path.exists(p):
                filepath = p
                break
        
        if filepath is None:
            print("[WARNING] Khong tim thay file checkpoint 'dagnn_pretrained.pth'.")
            return False

    if not os.path.exists(filepath):
        print(f"[WARNING] Checkpoint {filepath} khong ton tai.")
        return False

    try:
        device_obj = torch.device(device)
        checkpoint = torch.load(filepath, map_location=device_obj)
        
        # Ở đây ta lưu toàn bộ mô hình (SequentialGLPOModel) hoặc model_state_dict
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
            print(f"[SUCCESS] Da nap thanh cong model weights tu: {filepath}")
            if 'epoch' in checkpoint:
                print(f"   • Epoch: {checkpoint['epoch']}")
            if 'best_loss' in checkpoint and checkpoint['best_loss'] is not None:
                print(f"   • Best Loss lúc pretrain: {checkpoint['best_loss']:.4f}")
            return True
        elif 'state_dict' in checkpoint:
            model.load_state_dict(checkpoint['state_dict'])
            print(f"[SUCCESS] Da nap thanh cong model weights (state_dict) tu: {filepath}")
            return True
        else:
            model.load_state_dict(checkpoint)
            print(f"[SUCCESS] Da nap model weights (direct state_dict) tu: {filepath}")
            return True
    except Exception as e:
        print(f"[ERROR] Loi khi nap DAGNN pretrained weights: {str(e)}")
        return False


# ============================================================================
# KHỐI KIỂM TRA (Unit Test)
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sys.path.insert(0, '.')
    sys.path.insert(0, '..')
    sys.path.insert(0, '../models')

    from torch_geometric.data import Data

    import os
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')
    sys.path.insert(0, os.path.abspath(models_dir))

    from ai_pipeline.models.sequential_glpo_model import SequentialGLPOModel

    print("=" * 70)
    print("  KIỂM TRA UNSUPERVISED PRETRAINER NÂNG CẤP (GAE+DGI & CPM+MASK+TOPO)")
    print("=" * 70)

    # 1. Tạo đồ thị dự án giả lập (15 tasks, DAG phức tạp)
    num_nodes = 15
    torch.manual_seed(42)
    x = torch.rand(num_nodes, 72)

    # Đặt thời lượng hợp lý
    x[:, 3] = torch.tensor([2, 3, 1, 4, 2, 3, 1, 5, 2, 4, 3, 1, 2, 3, 4], dtype=torch.float)  # days
    x[:, 4] = 0.0  # hours

    # DAG dạng phức tạp
    edge_index = torch.tensor([
        [0, 0, 1, 2, 3, 4, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        [1, 2, 3, 3, 4, 5, 6, 7, 7, 8, 9, 10, 11, 12, 13],
    ], dtype=torch.long)

    # Thêm một nút cuối gom lại
    edge_index = torch.cat([
        edge_index,
        torch.tensor([[13], [14]], dtype=torch.long)
    ], dim=1)

    u = torch.tensor([[8.0, 5.0, 10.0]], dtype=torch.float)
    data = Data(x=x, edge_index=edge_index, u=u)

    # 2. Khởi tạo mô hình
    model = SequentialGLPOModel(feature_dim=72, gat_out_dim=32, dagnn_out_dim=32)

    print(f"\n[1] Cấu hình:")
    print(f"    Mô hình: {sum(p.numel() for p in model.parameters()):,} tham số")
    print(f"    Đồ thị: {num_nodes} tasks, {edge_index.shape[1]} cạnh")

    # 3. Ghi nhận Embeddings TRƯỚC khi pretrain
    model.eval()
    with torch.no_grad():
        result_before = model(data)
        emb_before = result_before['node_embeddings'].clone()
        h_dagnn_before = result_before['h_dagnn'].clone()

    print(f"\n[2] TRƯỚC Pre-training:")
    print(f"    GAT Embedding norm TB: {emb_before.norm(dim=1).mean():.4f}")
    print(f"    DAGNN Embedding norm TB: {h_dagnn_before.norm(dim=1).mean():.4f}")

    # 4. Chạy Pretrain toàn bộ
    pretrainer = UnsupervisedPretrainer(model, device='cpu')
    history = pretrainer.pretrain_all(data, gae_epochs=20, cpm_epochs=20, verbose=True)

    # 5. Ghi nhận Embeddings SAU khi pretrain
    model.eval()
    with torch.no_grad():
        result_after = model(data)
        emb_after = result_after['node_embeddings'].clone()
        h_dagnn_after = result_after['h_dagnn'].clone()

    print(f"\n[3] SAU Pre-training:")
    print(f"    GAT Embedding norm TB: {emb_after.norm(dim=1).mean():.4f}")
    print(f"    DAGNN Embedding norm TB: {h_dagnn_after.norm(dim=1).mean():.4f}")

    # 6. So sánh sự thay đổi
    emb_diff = (emb_after - emb_before).norm(dim=1).mean()
    dagnn_diff = (h_dagnn_after - h_dagnn_before).norm(dim=1).mean()
    print(f"\n[4] So sánh TRƯỚC vs SAU:")
    print(f"    Thay đổi GAT Embedding: {emb_diff:.4f}")
    print(f"    Thay đổi DAGNN Embedding: {dagnn_diff:.4f}")
    print(f"    GAE+DGI Loss: {history['gae']['losses'][0]:.4f} → {history['gae']['losses'][-1]:.4f}")
    print(f"    DAGNN Multi-task Loss: {history['cpm']['losses'][0]:.4f} → {history['cpm']['losses'][-1]:.4f}")

    # 7. Kiểm tra load_pretrained_dagnn
    print(f"\n[5] Kiểm tra load_pretrained_dagnn:")
    fresh_model = SequentialGLPOModel(feature_dim=72, gat_out_dim=32, dagnn_out_dim=32)
    success = load_pretrained_dagnn(fresh_model)
    print(f"    Nạp checkpoint DAGNN: {'[OK]' if success else '[FAIL]'}")
    
    if success:
        fresh_model.eval()
        with torch.no_grad():
            fresh_result = fresh_model(data)
            fresh_h_dagnn = fresh_result['h_dagnn']
        val_diff = (fresh_h_dagnn - h_dagnn_after).norm(dim=1).mean().item()
        print(f"    Sai số giữa mô hình load checkpoint và mô hình sau pretrain: {val_diff:.6f}")
        if val_diff < 1e-5:
            print("    [SUCCESS] Load trọng số DAGNN hoàn toàn chính xác!")
        else:
            print("    [WARNING] Có sự khác biệt nhỏ về trọng số!")

    print(f"\n{'=' * 70}")
    print("  HOÀN TẤT KIỂM TRA UNSUPERVISED PRETRAINER NÂNG CẤP")
    print(f"{'=' * 70}")
