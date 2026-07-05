"""
Mô-đun SequentialGLPOModel: Mô hình Lai ghép Tuần tự (End-to-End Wrapper)
==========================================================================
Dự án: GLPO - Graph Logistics Project Optimization

Mô tả:
    Wrapper tích hợp toàn bộ luồng xử lý tuần tự của 3 tầng trong kiến trúc GLPO:

    [Dữ liệu thô 72 Features + Đồ thị DAG]
        │
        ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ TẦNG 1 & 2: HierarchicalAttentionEncoder                    │
    │   72 features → 13 giá trị đại diện S'_g (có Masking)       │
    └──────────────────────────────────────────────────────────────┘
        │ S'_g (N, 13) + group_masks (N, 13)
        ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ TẦNG 3a: LogisticsGATModel (Graph Attention Network)         │
    │   Lan truyền rủi ro cấu trúc qua Message Passing             │
    └──────────────────────────────────────────────────────────────┘
        │ H_GAT (N, gat_out_dim)
        ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ TẦNG 3b: DAGNNPropagator (Directed Acyclic GNN)              │
    │   Lan truyền độ trễ tích lũy theo thứ tự Tô-pô               │
    └──────────────────────────────────────────────────────────────┘
        │ H_final (N, dagnn_out_dim)
        ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ TẦNG 3c: Decoder → S'_g tăng cường                           │
    │   Phóng chiếu H_final trở lại không gian 13 nhóm             │
    └──────────────────────────────────────────────────────────────┘
        │ S'_g_enhanced (N, 13)
        ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ TẦNG 3d: TGCLayer3 (Tổng Chi phí Quy đổi)                   │
    │   Tính TGC = Σ β·S'_g + Σ γ·S'_g·S'_h                       │
    └──────────────────────────────────────────────────────────────┘
        │ TGC (N,) — dùng làm Reward cho PPO Agent
        ▼

Nguồn tham chiếu:
    - ai_pipeline/models/hierarchical_encoder.py
    - ai_pipeline/models/gat_model.py
    - ai_pipeline/models/dagnn_propagator.py
    - ai_pipeline/models/tgc_layer3.py
    - docs/22-6/hierarchical_3level_evaluation.md
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, global_mean_pool
from typing import Dict, Optional, Tuple

# Import các module nội bộ
import sys
import os
try:
    from ai_pipeline.models.hierarchical_encoder import HierarchicalAttentionEncoder
    from ai_pipeline.models.dagnn_propagator import DAGNNPropagator
    from ai_pipeline.models.tgc_layer3 import TGCLayer3, NUM_GROUPS
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hierarchical_encoder import HierarchicalAttentionEncoder
    from dagnn_propagator import DAGNNPropagator
    from tgc_layer3 import TGCLayer3, NUM_GROUPS


class SequentialGLPOModel(nn.Module):
    """
    Mô tả (Description):
        Mô hình lai ghép tuần tự tích hợp hoàn chỉnh cho dự án GLPO.
        Nối tiếp 4 khối xử lý: Encoder → GAT → DAGNN → TGC.
        Hỗ trợ huấn luyện End-to-End (gradient chảy xuyên suốt từ TGC ngược về Encoder).

    Đầu vào khởi tạo (Args):
        feature_dim (int): Số chiều vector đặc trưng thô (mặc định 72).
        num_groups (int): Số nhóm đặc trưng (mặc định 13 = Hub + G1-G12).
        gat_hidden_dim (int): Số chiều ẩn của GAT (mặc định 64).
        gat_out_dim (int): Số chiều đầu ra của GAT (mặc định 32).
        gat_heads (int): Số Attention Heads của GAT (mặc định 4).
        dagnn_hidden_dim (int): Số chiều ẩn của DAGNN (mặc định 64).
        dagnn_out_dim (int): Số chiều đầu ra của DAGNN (mặc định 32).
        learnable_beta (bool): Cho phép AI học trọng số β trong TGC (mặc định True).
        learnable_gamma (bool): Cho phép AI học ma trận γ trong TGC (mặc định False).
        dropout (float): Tỷ lệ Dropout chung (mặc định 0.2).

    Đầu ra / Thuộc tính (Outputs / Attributes):
        encoder: HierarchicalAttentionEncoder (Tầng 1 & 2).
        gat_layers: Các lớp GAT (Tầng 3a).
        dagnn: DAGNNPropagator (Tầng 3b).
        decoder: Lớp phóng chiếu ngược về 13 nhóm (Tầng 3c).
        tgc: TGCLayer3 (Tầng 3d).
    """
    def __init__(
        self,
        feature_dim: int = 72,
        num_groups: int = NUM_GROUPS,
        gat_hidden_dim: int = 64,
        gat_out_dim: int = 32,
        gat_heads: int = 4,
        dagnn_hidden_dim: int = 64,
        dagnn_out_dim: int = 32,
        learnable_beta: bool = True,
        learnable_gamma: bool = False,
        dropout: float = 0.2,
    ):
        super(SequentialGLPOModel, self).__init__()

        # Lưu hyperparameters
        self.feature_dim = feature_dim
        self.num_groups = num_groups
        self.gat_out_dim = gat_out_dim
        self.dagnn_out_dim = dagnn_out_dim
        self.dropout = dropout

        # =========================================================
        # TẦNG 1 & 2: Hierarchical Attention Encoder
        # =========================================================
        self.encoder = HierarchicalAttentionEncoder(
            feature_dim=feature_dim,
            num_groups=num_groups - 1,  # Encoder dùng num_groups=12, tự tạo 13 nhóm nội bộ
        )

        # =========================================================
        # TẦNG 3a: Graph Attention Network (GAT)
        # =========================================================
        # Phóng chiếu S'_g (13 chiều) lên không gian ẩn của GAT
        self.node_proj = nn.Linear(num_groups, gat_hidden_dim)

        # Các lớp GAT: Message Passing trên đồ thị
        self.gat1 = GATConv(
            gat_hidden_dim, gat_hidden_dim,
            heads=gat_heads, concat=True, dropout=dropout,
        )
        self.gat2 = GATConv(
            gat_hidden_dim * gat_heads, gat_out_dim,
            heads=1, concat=False, dropout=dropout,
        )

        # Global Pooling: Tạo vector đại diện cho toàn bộ đồ thị (dùng cho PPO State)
        self.global_proj = nn.Linear(gat_out_dim, gat_out_dim)

        # =========================================================
        # TẦNG 3b: DAGNN Propagator (Lan truyền Tô-pô)
        # =========================================================
        self.dagnn = DAGNNPropagator(
            gat_dim=gat_out_dim,
            hidden_dim=dagnn_hidden_dim,
            out_dim=dagnn_out_dim,
        )

        # =========================================================
        # TẦNG 3c: Decoder — Phóng chiếu ngược về không gian 13 nhóm
        # =========================================================
        # Kết hợp thông tin từ DAGNN embedding VÀ S'_g gốc (Residual Connection)
        # Đầu vào: [dagnn_out || S'_g gốc] → 13 giá trị nhóm tăng cường
        self.decoder = nn.Sequential(
            nn.Linear(dagnn_out_dim + num_groups, num_groups * 2),
            nn.LayerNorm(num_groups * 2),
            nn.LeakyReLU(0.2),
            nn.Dropout(dropout),
            nn.Linear(num_groups * 2, num_groups),
        )

        # =========================================================
        # TẦNG 3d: TGC Layer 3 (Tổng Chi phí Quy đổi)
        # =========================================================
        self.tgc = TGCLayer3(
            num_groups=num_groups,
            learnable_beta=learnable_beta,
            learnable_gamma=learnable_gamma,
        )

    def forward(
        self,
        data,
    ) -> Dict[str, torch.Tensor]:
        """
        Mô tả (Description):
            Hàm truyền tiến toàn bộ pipeline tuần tự.
            Chạy xuyên suốt từ Tầng 1 đến Tầng 3 và trả về TGC cùng các kết quả trung gian.

        Đầu vào (Args):
            data (torch_geometric.data.Data): Đối tượng đồ thị PyG chứa:
                - data.x: Tensor [N, 72] — Vector đặc trưng thô của mỗi task.
                - data.edge_index: Tensor [2, E] — Bản đồ liên kết logic (DAG).
                - data.u: Tensor [1, 3] — Ràng buộc toàn cục (giờ/ngày, ngày/tuần, ngày nghỉ).

        Đầu ra (Returns):
            Dict chứa:
                - 'tgc': Tensor [N] — Tổng Chi phí Quy đổi của từng task.
                - 'S_prime_g': Tensor [N, 13] — Giá trị đại diện nhóm từ Encoder (Tầng 1-2).
                - 'S_prime_g_enhanced': Tensor [N, 13] — Giá trị đại diện tăng cường (Tầng 3).
                - 'group_masks': Tensor [N, 13] — Mặt nạ nhóm.
                - 'node_embeddings': Tensor [N, gat_out_dim] — Node Embeddings từ GAT.
                - 'graph_embedding': Tensor [1, gat_out_dim] — Graph Embedding (cho PPO State).
                - 'h_dagnn': Tensor [N, dagnn_out_dim] — Embeddings từ DAGNN.
        """
        x, edge_index = data.x, data.edge_index

        # ── TẦNG 1 & 2: Encoder ──────────────────────────────────
        S_prime_g, group_masks = self.encoder(x)
        # S_prime_g: (N, 13), group_masks: (N, 13)

        # ── TẦNG 3a: GAT ─────────────────────────────────────────
        # Phóng chiếu S'_g lên không gian ẩn
        h = F.leaky_relu(self.node_proj(S_prime_g))  # (N, gat_hidden_dim)

        # Message Passing qua đồ thị
        h = self.gat1(h, edge_index)
        h = F.elu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)

        h = self.gat2(h, edge_index)
        node_embeddings = h  # (N, gat_out_dim)

        # Global Pooling (cho PPO State)
        batch = data.batch if hasattr(data, 'batch') and data.batch is not None \
            else torch.zeros(x.shape[0], dtype=torch.long, device=x.device)
        graph_embedding = global_mean_pool(node_embeddings, batch)
        graph_embedding = self.global_proj(graph_embedding)  # (1, gat_out_dim)

        # ── TẦNG 3b: DAGNN ───────────────────────────────────────
        h_dagnn = self.dagnn(node_embeddings, edge_index)  # (N, dagnn_out_dim)

        # ── TẦNG 3c: Decoder (Phóng chiếu ngược về 13 nhóm) ─────
        # Residual Connection: kết hợp H_DAGNN với S'_g gốc
        decoder_input = torch.cat([h_dagnn, S_prime_g], dim=1)  # (N, dagnn_out_dim + 13)
        S_prime_g_enhanced = self.decoder(decoder_input)  # (N, 13)

        # Áp dụng mask: nhóm đã chết không được hồi sinh
        S_prime_g_enhanced = S_prime_g_enhanced * group_masks

        # Residual Addition: S'_g tăng cường = S'_g gốc + Δ (điều chỉnh từ đồ thị)
        S_prime_g_enhanced = S_prime_g + S_prime_g_enhanced

        # ── TẦNG 3d: TGC ─────────────────────────────────────────
        tgc = self.tgc(S_prime_g_enhanced, group_masks)  # (N,)

        return {
            'tgc': tgc,
            'S_prime_g': S_prime_g,
            'S_prime_g_enhanced': S_prime_g_enhanced,
            'group_masks': group_masks,
            'node_embeddings': node_embeddings,
            'graph_embedding': graph_embedding,
            'h_dagnn': h_dagnn,
        }

    def forward_detailed(
        self,
        data,
    ) -> Dict[str, object]:
        """
        Mô tả (Description):
            Phiên bản phân tích chi tiết của forward().
            Trả về thêm thông tin về top synergies, gate values, và propagation depth.

        Đầu vào (Args):
            data: Đối tượng đồ thị PyG (giống forward()).

        Đầu ra (Returns):
            Dict mở rộng, bao gồm tất cả kết quả của forward() CỘNG THÊM:
                - 'tgc_details': Dict từ TGCLayer3.forward_detailed().
                - 'dagnn_info': Dict từ DAGNNPropagator.forward_with_attention().
        """
        x, edge_index = data.x, data.edge_index

        # Tầng 1 & 2
        S_prime_g, group_masks = self.encoder(x)

        # Tầng 3a: GAT
        h = F.leaky_relu(self.node_proj(S_prime_g))
        h = self.gat1(h, edge_index)
        h = F.elu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = self.gat2(h, edge_index)
        node_embeddings = h

        batch = data.batch if hasattr(data, 'batch') and data.batch is not None \
            else torch.zeros(x.shape[0], dtype=torch.long, device=x.device)
        graph_embedding = global_mean_pool(node_embeddings, batch)
        graph_embedding = self.global_proj(graph_embedding)

        # Tầng 3b: DAGNN (phiên bản chi tiết)
        h_dagnn, dagnn_info = self.dagnn.forward_with_attention(node_embeddings, edge_index)

        # Tầng 3c: Decoder
        decoder_input = torch.cat([h_dagnn, S_prime_g], dim=1)
        S_prime_g_enhanced = self.decoder(decoder_input)
        S_prime_g_enhanced = S_prime_g_enhanced * group_masks
        S_prime_g_enhanced = S_prime_g + S_prime_g_enhanced

        # Tầng 3d: TGC (phiên bản chi tiết)
        tgc_details = self.tgc.forward_detailed(S_prime_g_enhanced, group_masks)

        return {
            'tgc': tgc_details['tgc'],
            'S_prime_g': S_prime_g,
            'S_prime_g_enhanced': S_prime_g_enhanced,
            'group_masks': group_masks,
            'node_embeddings': node_embeddings,
            'graph_embedding': graph_embedding,
            'h_dagnn': h_dagnn,
            'tgc_details': tgc_details,
            'dagnn_info': dagnn_info,
        }

    def get_ppo_state(self, data) -> torch.Tensor:
        """
        Mô tả (Description):
            Hàm tiện ích để trích xuất State Vector cho PPO Agent.
            Kết hợp Graph Embedding (toàn cục) với thông tin ràng buộc.

        Đầu vào (Args):
            data: Đối tượng đồ thị PyG.

        Đầu ra (Returns):
            ppo_state (torch.Tensor): Vector trạng thái cho PPO [1, gat_out_dim + 3].
                Gồm: [graph_embedding || global_constraints(u)].
        """
        result = self.forward(data)
        graph_emb = result['graph_embedding']  # (1, gat_out_dim)
        u = data.u if hasattr(data, 'u') and data.u is not None \
            else torch.zeros(1, 3, device=graph_emb.device)

        # Nối graph embedding với các ràng buộc toàn cục
        ppo_state = torch.cat([graph_emb, u], dim=1)  # (1, gat_out_dim + 3)
        return ppo_state


# ============================================================================
# KHỐI KIỂM TRA (Unit Test)
# ============================================================================
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    from torch_geometric.data import Data

    print("=" * 70)
    print("  KIỂM TRA MÔ HÌNH SEQUENTIALGLPOMODEL")
    print("=" * 70)

    # 1. Tạo đồ thị giả lập (10 tasks, dạng DAG)
    num_nodes = 10
    feature_dim = 72

    torch.manual_seed(42)
    x = torch.rand(num_nodes, feature_dim)
    # Ép một số nhóm về 0 để kiểm tra Masking
    x[:, 15:21] = 0.0   # G2 = 0
    x[:, 21:25] = 0.0   # G4 = 0

    # Đồ thị DAG: 0→1, 0→2, 1→3, 2→3, 3→4, 4→5, 4→6, 5→7, 6→7, 7→8, 8→9
    edge_index = torch.tensor([
        [0, 0, 1, 2, 3, 4, 4, 5, 6, 7, 8],
        [1, 2, 3, 3, 4, 5, 6, 7, 7, 8, 9],
    ], dtype=torch.long)

    u = torch.tensor([[8.0, 5.0, 10.0]], dtype=torch.float)
    data = Data(x=x, edge_index=edge_index, u=u)

    # 2. Khởi tạo mô hình
    model = SequentialGLPOModel(
        feature_dim=feature_dim,
        gat_hidden_dim=64,
        gat_out_dim=32,
        gat_heads=4,
        dagnn_hidden_dim=64,
        dagnn_out_dim=32,
        learnable_beta=True,
        learnable_gamma=False,
    )

    print(f"\n[1] Cấu hình mô hình:")
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"    Tổng tham số: {total_params:,}")
    print(f"    Tham số huấn luyện: {trainable_params:,}")
    print(f"    Số lượng module con: {len(list(model.children()))}")

    # 3. Forward pass
    print(f"\n[2] Kiểm tra Forward Pass:")
    model.eval()
    with torch.no_grad():
        result = model(data)

    print(f"    data.x:              {data.x.shape}")
    print(f"    data.edge_index:     {data.edge_index.shape}")
    print(f"    S_prime_g:           {result['S_prime_g'].shape}")
    print(f"    S_prime_g_enhanced:  {result['S_prime_g_enhanced'].shape}")
    print(f"    group_masks:         {result['group_masks'].shape}")
    print(f"    node_embeddings:     {result['node_embeddings'].shape}")
    print(f"    graph_embedding:     {result['graph_embedding'].shape}")
    print(f"    h_dagnn:             {result['h_dagnn'].shape}")
    print(f"    tgc:                 {result['tgc'].shape}")
    print(f"    TGC values:          {result['tgc'][:5].tolist()}")

    # 4. Kiểm tra Masking
    print(f"\n[3] Kiểm tra Adaptive Masking:")
    masks = result['group_masks'][0]
    for g_id in range(13):
        from tgc_layer3 import GROUP_NAMES
        status = "🟢 Sống" if masks[g_id] > 0 else "⚫ Chết"
        print(f"    {GROUP_NAMES.get(g_id, f'G{g_id}')}: {status}")

    # 5. Kiểm tra Detailed Forward
    print(f"\n[4] Kiểm tra Forward Detailed:")
    with torch.no_grad():
        detailed = model.forward_detailed(data)

    tgc_info = detailed['tgc_details']
    dagnn_info = detailed['dagnn_info']

    print(f"    TGC Phần tuyến tính (tb): {tgc_info['linear_term'].mean():.4f}")
    print(f"    TGC Phần phi tuyến (tb):  {tgc_info['cross_term'].mean():.4f}")
    print(f"    DAGNN Độ sâu lan truyền:  {dagnn_info['propagation_depth']}")
    print(f"    DAGNN Số nút nguồn:       {dagnn_info['num_source_nodes']}")
    print(f"    Top synergies:")
    for syn in tgc_info['top_synergies'][:3]:
        print(f"      #{syn['rank']}: {syn['group_g']} × {syn['group_h']}"
              f" = {syn['cross_value']:.4f} ({syn['effect']})")

    # 6. Kiểm tra PPO State
    print(f"\n[5] Kiểm tra PPO State Vector:")
    with torch.no_grad():
        ppo_state = model.get_ppo_state(data)
    print(f"    PPO State shape: {ppo_state.shape}  (graph_emb + global_constraints)")

    # 7. Kiểm tra Gradient Flow (End-to-End Backpropagation)
    print(f"\n[6] Kiểm tra End-to-End Gradient Flow:")
    model.train()
    result_train = model(data)
    loss = result_train['tgc'].mean()
    loss.backward()

    gradient_ok = True
    for name, param in model.named_parameters():
        if param.requires_grad and param.grad is None:
            print(f"    ❌ Không có gradient cho: {name}")
            gradient_ok = False

    if gradient_ok:
        print(f"    ✅ Gradient chảy xuyên suốt từ TGC → DAGNN → GAT → Encoder")

    # Đếm gradient norm theo module
    module_grad_norms = {}
    for name, param in model.named_parameters():
        if param.requires_grad and param.grad is not None:
            module_name = name.split('.')[0]
            if module_name not in module_grad_norms:
                module_grad_norms[module_name] = 0.0
            module_grad_norms[module_name] += param.grad.norm().item()

    print(f"    Gradient norm theo module:")
    for mod, norm in sorted(module_grad_norms.items()):
        print(f"      {mod}: {norm:.4f}")

    print(f"\n{'=' * 70}")
    print("  HOÀN TẤT KIỂM TRA SEQUENTIALGLPOMODEL")
    print(f"{'=' * 70}")
