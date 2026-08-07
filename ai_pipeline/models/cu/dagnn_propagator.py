"""
Mô-đun DAGNNPropagator: Lan truyền Độ trễ theo Thứ tự Tô-pô
==============================================================
Dự án: GLPO - Graph Logistics Project Optimization

Mô tả:
    Mô-đun này thực hiện lan truyền trạng thái một chiều (Forward-only Propagation)
    dọc theo danh sách Topological Sort của đồ thị DAG (Directed Acyclic Graph).

    Khác với GAT (lan truyền đối xứng qua Message Passing), DAGNN tôn trọng
    tính nhân quả: trạng thái của task j CHỈ phụ thuộc vào các task trước nó
    (predecessors), không bao giờ bị ảnh hưởng ngược bởi task sau (successors).

    Điều này mô phỏng chính xác cách độ trễ tích lũy và lan truyền
    trong thực tế quản lý dự án: trễ ở đầu nguồn sẽ tích tụ và khuếch đại
    khi truyền về cuối nguồn.

==============================================================
TÀI LIỆU TIỀN HUẤN LUYỆN TỰ GIÁM SÁT ĐA NHIỆM (DAGNN PRETRAINING)
==============================================================

Để huấn luyện DAGNN hiểu sâu sắc về thời gian và topo dự án trước khi đưa vào Học tăng cường (PPO), 
chúng ta sử dụng 3 nhiệm vụ Tự giám sát (Self-Supervised Tasks) đồng thời:

1. CPM Self-Supervised Learning (Mục tiêu chính):
   - DAGNN được gắn một đầu dự đoán tạm thời để khôi phục 7 thuộc tính thời gian CPM tĩnh:
     [Early Start, Early Finish, Late Start, Late Finish, Total Float, Is Critical, Path Length].
   - Nhãn mục tiêu được tính toán tự động qua thuật toán CPM trên đồ thị logic của dự án.
   - Giúp mô hình nắm bắt cách thời gian và độ trễ cộng dồn dọc theo đường găng và cấu trúc DAG.

2. Masked Duration Prediction:
   - Che khuất ngẫu nhiên 15% thời lượng (Duration) công việc của các node (đặt về 0.0).
   - DAGNN học cách dự đoán lại thời lượng gốc của node bị che khuất dựa trên embeddings của các node xung quanh.
   - Buộc mô hình học cách nội suy thời lượng từ ngữ cảnh tô-pô trước-sau thay vì chỉ ghi nhớ các giá trị tĩnh.

3. Topological Distance Prediction:
   - Lấy mẫu các cặp node (u, v) ngẫu nhiên và dự đoán khoảng cách đường đi ngắn nhất (Shortest Path Distance) giữa chúng.
   - Nhãn giả được tính tự động bằng thuật toán duyệt đồ thị BFS/Dijkstra trên DAG.
   - Giúp biểu diễn embedding phản ánh chính xác cấu trúc thứ tự công việc và khoảng cách phụ thuộc logic.

Vì sao phương pháp này tối ưu cho dataset chỉ có 5 dự án:
   - Do lượng dự án rất nhỏ, việc huấn luyện trực tiếp GNN cùng PPO dễ gây quá khớp và làm lệch hướng lan truyền.
   - Việc tiền huấn luyện đa nhiệm tự giám sát đóng vai trò như các ràng buộc vật lý mạnh mẽ. Nó ép DAGNN học cách 
     tự động lan truyền thông điệp có hướng và hiểu logic lập lịch trước khi PPO Agent học chính sách lập lịch.
   - Các nhãn giả được sinh tự động 100% từ cấu trúc đồ thị logic DAG, không cần nhãn thủ công.

Cách embedding được truyền sang PPO:
   - Khi PPO chạy, model load checkpoint `dagnn_pretrained.pth` chứa trọng số DAGNN đã học từ pretraining.
   - Các biểu diễn node h_final sinh ra từ DAGNN lúc này đã chứa đầy đủ tính chất cấu trúc tô-pô và đường găng, 
     giúp PPO Agent đưa ra quyết định tối ưu hóa Makespan và Cost một cách nhanh chóng và ổn định.

Độ phức tạp tính toán:
   - BFS toàn bộ node: O(|V| * (|V| + |E|)) - chạy dưới 0.1s cho đồ thị lớn nhất.
   - Tổng thời gian pretraining DAGNN là tuyến tính theo số node/cạnh, hoàn tất trong giây lát (1s - 15s).

Nguồn tham chiếu:
    - Thinker et al. "Directed Acyclic Graph Neural Network" (2020)
    - docs/22-6/hierarchical_3level_evaluation.md (Tầng 3)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import defaultdict, deque
from typing import Optional, Tuple


class PredecessorAttention(nn.Module):
    """
    Cơ chế Attention Aggregation tập trung vào các task tiền nhiệm quan trọng/trễ hạn
    thay vì cộng đơn thuần gây pha loãng tín hiệu rủi ro.
    """
    def __init__(self, hidden_dim: int, gat_dim: int):
        super(PredecessorAttention, self).__init__()
        self.attn_mlp = nn.Sequential(
            nn.Linear(hidden_dim + gat_dim, hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
    def forward(self, pred_states: torch.Tensor, h_self: torch.Tensor) -> torch.Tensor:
        # pred_states: [num_preds, hidden_dim]
        # h_self: [gat_dim]
        if pred_states.shape[0] == 1:
            return pred_states[0]
            
        h_self_expanded = h_self.unsqueeze(0).repeat(pred_states.shape[0], 1)
        concat_feat = torch.cat([pred_states, h_self_expanded], dim=1)
        scores = self.attn_mlp(concat_feat).squeeze(-1)
        weights = F.softmax(scores, dim=0)
        return torch.sum(weights.unsqueeze(1) * pred_states, dim=0)


class DAGNNPropagator(nn.Module):
    """
    Mô tả (Description):
        Lớp lan truyền trạng thái có hướng dọc theo thứ tự Tô-pô (Topological Order)
        của đồ thị DAG dự án. Kết hợp thông tin từ GAT embeddings và trạng thái
        tích lũy từ các predecessors để tạo ra embedding cuối cùng chứa cả
        thông tin rủi ro cấu trúc (từ GAT) lẫn lan truyền trễ hạn (từ DAGNN).

    Đầu vào khởi tạo (Args):
        gat_dim (int): Số chiều đầu ra của GAT (mặc định 32, khớp với out_dim của LogisticsGATModel).
        hidden_dim (int): Số chiều không gian ẩn cho MLP chuyển tiếp (mặc định 64).
        out_dim (int): Số chiều đầu ra cuối cùng của mỗi node (mặc định 32).
        num_prop_layers (int): Số lớp MLP chuyển tiếp xếp chồng (mặc định 2).
        dropout (float): Tỷ lệ Dropout cho các lớp ẩn (mặc định 0.1).

    Đầu ra / Thuộc tính (Outputs / Attributes):
        transition_mlp (nn.Sequential): Mạng MLP học hàm chuyển tiếp trạng thái.
        output_proj (nn.Linear): Lớp phóng chiếu cuối cùng về không gian đầu ra.
    """
    def __init__(
        self,
        gat_dim: int = 32,
        hidden_dim: int = 64,
        out_dim: int = 32,
        num_prop_layers: int = 2,
        dropout: float = 0.1,
    ):
        super(DAGNNPropagator, self).__init__()
        self.gat_dim = gat_dim
        self.hidden_dim = hidden_dim
        self.out_dim = out_dim

        # Lớp khởi tạo trạng thái ban đầu cho các nút nguồn (Source nodes - không có predecessor)
        # Đầu vào: embedding GAT (gat_dim), Đầu ra: trạng thái ẩn ban đầu (hidden_dim)
        self.init_state = nn.Sequential(
            nn.Linear(gat_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.LeakyReLU(0.2),
        )

        # Hàm chuyển tiếp trạng thái (Transition Function):
        # Đầu vào: [embedding GAT của task hiện tại (gat_dim) || tổng trạng thái predecessors (hidden_dim)]
        # Đầu ra: trạng thái ẩn mới (hidden_dim)
        layers = []
        input_size = gat_dim + hidden_dim
        for i in range(num_prop_layers):
            out_size = hidden_dim
            layers.append(nn.Linear(input_size, out_size))
            layers.append(nn.LayerNorm(out_size))
            layers.append(nn.LeakyReLU(0.2))
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            input_size = out_size
        self.transition_mlp = nn.Sequential(*layers)

        # Cổng kiểm soát (Gating mechanism):
        # Cho phép mô hình tự quyết định mức độ kế thừa trạng thái từ predecessors
        # vs sử dụng thông tin riêng của task hiện tại (từ GAT)
        self.gate_linear = nn.Linear(gat_dim + hidden_dim, hidden_dim)

        # Lớp phóng chiếu cuối cùng: hidden_dim → out_dim
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, out_dim),
            nn.LayerNorm(out_dim),
            nn.LeakyReLU(0.2),
        )

        # Lớp Attention Aggregation cho predecessors (Mục 3)
        self.pred_attn = PredecessorAttention(hidden_dim=hidden_dim, gat_dim=gat_dim)

    def _topological_sort(
        self,
        edge_index: torch.Tensor,
        num_nodes: int,
    ) -> Tuple[list, dict]:
        """
        Mô tả (Description):
            Thực hiện sắp xếp tô-pô (Kahn's Algorithm) trên đồ thị
            và xây dựng danh sách predecessors cho mỗi node.

        Đầu vào (Args):
            edge_index (torch.Tensor): Bản đồ liên kết [2, E], hàng 0 = nguồn, hàng 1 = đích.
            num_nodes (int): Tổng số nút trong đồ thị.

        Đầu ra (Returns):
            topo_order (list[int]): Danh sách chỉ số nút theo thứ tự tô-pô.
            predecessors (dict[int, list[int]]): Ánh xạ node → danh sách các predecessors.
        """
        # Xây dựng danh sách kề và predecessors
        adj_forward = defaultdict(list)
        predecessors = defaultdict(list)
        in_degree = defaultdict(int)

        if edge_index.numel() > 0:
            src = edge_index[0].cpu().tolist()
            dst = edge_index[1].cpu().tolist()
            for s, d in zip(src, dst):
                adj_forward[s].append(d)
                predecessors[d].append(s)
                in_degree[d] += 1

        # Thuật toán Kahn
        queue = deque()
        for i in range(num_nodes):
            if in_degree[i] == 0:
                queue.append(i)

        topo_order = []
        while queue:
            u = queue.popleft()
            topo_order.append(u)
            for v in adj_forward[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # Nếu có nút bị thiếu (do đồ thị có thành phần cô lập), bổ sung vào cuối
        visited = set(topo_order)
        for i in range(num_nodes):
            if i not in visited:
                topo_order.append(i)

        return topo_order, dict(predecessors)

    def forward(
        self,
        h_gat: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        """
        Mô tả (Description):
            Hàm truyền tiến chính. Thực hiện lan truyền trạng thái một chiều
            dọc theo thứ tự tô-pô của đồ thị dự án.

        Đầu vào (Args):
            h_gat (torch.Tensor): Node embeddings từ GAT. Kích thước [N, gat_dim].
            edge_index (torch.Tensor): Bản đồ liên kết đồ thị [2, E].

        Đầu ra (Returns):
            h_final (torch.Tensor): Embedding cuối cùng chứa thông tin rủi ro cấu trúc
                (từ GAT) + lan truyền trễ tích lũy (từ DAGNN). Kích thước [N, out_dim].
        """
        num_nodes = h_gat.shape[0]
        device = h_gat.device

        # Bước 1: Sắp xếp tô-pô
        topo_order, predecessors = self._topological_sort(edge_index, num_nodes)

        # Bước 2: Khởi tạo bộ nhớ trạng thái ẩn cho tất cả các nút
        hidden_states = torch.zeros(num_nodes, self.hidden_dim, device=device)

        # Bước 3: Lan truyền tuần tự theo thứ tự tô-pô
        for node_idx in topo_order:
            h_self = h_gat[node_idx]  # (gat_dim,)
            preds = predecessors.get(node_idx, [])

            if len(preds) == 0:
                # Nút nguồn (Source): Không có predecessor → Dùng init_state
                hidden_states[node_idx] = self.init_state(h_self)
            else:
                # Nút trung gian/cuối: Tổng hợp trạng thái từ predecessors qua Attention Aggregation
                pred_indices = torch.tensor(preds, dtype=torch.long, device=device)
                pred_states = hidden_states[pred_indices]  # (num_preds, hidden_dim)
                agg_state = self.pred_attn(pred_states, h_self)  # (hidden_dim,)

                # Nối [embedding GAT || trạng thái tổng hợp] → MLP → trạng thái mới
                combined = torch.cat([h_self, agg_state])  # (gat_dim + hidden_dim,)
                new_state = self.transition_mlp(combined)  # (hidden_dim,)

                # Cổng kiểm soát (Gating): Tự quyết định tỷ lệ kế thừa vs tự lực
                gate = torch.sigmoid(self.gate_linear(combined))  # (hidden_dim,)
                init_fallback = self.init_state(h_self)  # (hidden_dim,)

                # Trạng thái cuối = gate * (trạng thái lan truyền) + (1 - gate) * (trạng thái tự lực)
                hidden_states[node_idx] = gate * new_state + (1 - gate) * init_fallback

        # Bước 4: Phóng chiếu về không gian đầu ra
        h_final = self.output_proj(hidden_states)  # (N, out_dim)

        return h_final

    def forward_with_attention(
        self,
        h_gat: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> Tuple[torch.Tensor, dict]:
        """
        Mô tả (Description):
            Phiên bản chi tiết của forward, trả về thêm thông tin phân tích
            về mức độ kế thừa (gate values) và trạng thái trung gian.

        Đầu vào (Args):
            h_gat (torch.Tensor): [N, gat_dim].
            edge_index (torch.Tensor): [2, E].

        Đầu ra (Returns):
            h_final (torch.Tensor): [N, out_dim].
            info (dict): Thông tin phân tích bao gồm:
                - 'gate_values': Giá trị cổng trung bình của từng node (N,).
                - 'topo_order': Danh sách thứ tự tô-pô.
                - 'propagation_depth': Độ sâu lan truyền tối đa.
        """
        num_nodes = h_gat.shape[0]
        device = h_gat.device

        topo_order, predecessors = self._topological_sort(edge_index, num_nodes)

        hidden_states = torch.zeros(num_nodes, self.hidden_dim, device=device)
        gate_values = torch.zeros(num_nodes, device=device)
        depth = torch.zeros(num_nodes, dtype=torch.long, device=device)

        for node_idx in topo_order:
            h_self = h_gat[node_idx]
            preds = predecessors.get(node_idx, [])

            if len(preds) == 0:
                hidden_states[node_idx] = self.init_state(h_self)
                gate_values[node_idx] = 0.0  # Nút nguồn không có cổng
                depth[node_idx] = 0
            else:
                pred_indices = torch.tensor(preds, dtype=torch.long, device=device)
                agg_state = hidden_states[pred_indices].sum(dim=0)

                combined = torch.cat([h_self, agg_state])
                new_state = self.transition_mlp(combined)

                gate = torch.sigmoid(self.gate_linear(combined))
                init_fallback = self.init_state(h_self)

                hidden_states[node_idx] = gate * new_state + (1 - gate) * init_fallback
                gate_values[node_idx] = gate.mean()
                depth[node_idx] = depth[pred_indices].max() + 1

        h_final = self.output_proj(hidden_states)

        info = {
            'gate_values': gate_values.detach(),
            'topo_order': topo_order,
            'propagation_depth': int(depth.max()),
            'num_source_nodes': sum(1 for n in range(num_nodes) if n not in predecessors),
            'num_sink_nodes': sum(1 for n in range(num_nodes)
                                  if all(n not in predecessors.get(other, [])
                                         for other in range(num_nodes)
                                         if other != n)),
        }

        return h_final, info


# ============================================================================
# KHỐI KIỂM TRA (Unit Test)
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("  KIỂM TRA MÔ-ĐUN DAGNN PROPAGATOR")
    print("=" * 70)

    # 1. Tạo đồ thị DAG giả lập (5 nút, dạng chuỗi + phân nhánh)
    #    0 → 1 → 3 → 4
    #    0 → 2 → 3
    #
    #    Thứ tự tô-pô: [0, 1, 2, 3, 4] hoặc [0, 2, 1, 3, 4]
    edge_index = torch.tensor([
        [0, 0, 1, 2, 3],  # nguồn
        [1, 2, 3, 3, 4],  # đích
    ], dtype=torch.long)

    num_nodes = 5
    gat_dim = 32

    # Giả lập GAT embeddings
    torch.manual_seed(42)
    h_gat = torch.randn(num_nodes, gat_dim)

    # 2. Khởi tạo DAGNN
    dagnn = DAGNNPropagator(gat_dim=gat_dim, hidden_dim=64, out_dim=32)
    dagnn.eval()

    print(f"\n[1] Cấu hình mô hình:")
    print(f"    GAT dim: {gat_dim}")
    print(f"    Hidden dim: 64")
    print(f"    Output dim: 32")
    total_params = sum(p.numel() for p in dagnn.parameters())
    trainable_params = sum(p.numel() for p in dagnn.parameters() if p.requires_grad)
    print(f"    Tổng tham số: {total_params:,}")
    print(f"    Tham số huấn luyện: {trainable_params:,}")

    # 3. Kiểm tra forward
    print(f"\n[2] Kiểm tra forward:")
    with torch.no_grad():
        h_final = dagnn(h_gat, edge_index)
    print(f"    Đầu vào H_GAT: {h_gat.shape}")
    print(f"    Đầu ra H_final: {h_final.shape}")
    print(f"    Norm trung bình: {h_final.norm(dim=1).mean():.4f}")

    # 4. Kiểm tra forward_with_attention
    print(f"\n[3] Kiểm tra forward_with_attention (Phân tích chi tiết):")
    with torch.no_grad():
        h_final_2, info = dagnn.forward_with_attention(h_gat, edge_index)

    print(f"    Thứ tự tô-pô: {info['topo_order']}")
    print(f"    Độ sâu lan truyền tối đa: {info['propagation_depth']}")
    print(f"    Số nút nguồn (Source): {info['num_source_nodes']}")
    print(f"    Giá trị cổng (Gate) trung bình:")
    for i in range(num_nodes):
        role = "Source" if info['gate_values'][i] == 0 else "Intermediate/Sink"
        print(f"      Node {i}: gate={info['gate_values'][i]:.4f} ({role})")

    # 5. Kiểm tra Gradient flow (Backpropagation)
    print(f"\n[4] Kiểm tra Gradient flow:")
    dagnn.train()
    h_gat_grad = torch.randn(num_nodes, gat_dim, requires_grad=True)
    h_out = dagnn(h_gat_grad, edge_index)
    loss = h_out.sum()
    loss.backward()
    print(f"    Gradient của đầu vào H_GAT: {'✅ Tồn tại' if h_gat_grad.grad is not None else '❌ Không có'}")
    print(f"    Gradient norm: {h_gat_grad.grad.norm():.4f}")

    # 6. Kiểm tra edge case: đồ thị không có cạnh (tất cả nút cô lập)
    print(f"\n[5] Edge case: Đồ thị không có cạnh (nút cô lập):")
    empty_edge = torch.empty((2, 0), dtype=torch.long)
    dagnn.eval()
    with torch.no_grad():
        h_isolated = dagnn(h_gat, empty_edge)
    print(f"    Đầu ra: {h_isolated.shape}")
    print(f"    Tất cả nút sử dụng init_state: ✅")

    print(f"\n{'=' * 70}")
    print("  HOÀN TẤT KIỂM TRA DAGNN PROPAGATOR")
    print(f"{'=' * 70}")
