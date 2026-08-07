"""
ai_pipeline.models — Các mô hình AI/ML của dự án GLPO
=====================================================

Bao gồm:
    - HierarchicalAttentionEncoder: Tầng 1 & 2 — Encoder phân cấp (72 features → 13 nhóm)
    - LogisticsGATModel: Tầng 3a — Graph Attention Network cho cấu trúc đồ thị dự án
    - DAGNNPropagator: Tầng 3b — Lan truyền độ trễ theo thứ tự Tô-pô (DAG)
    - TGCLayer3: Tầng 3d — Tính Tổng Chi phí Quy đổi (TGC) — hàm Reward PPO
    - SequentialGLPOModel: Wrapper tích hợp toàn bộ pipeline (End-to-End)
    - compute_tgc_numpy: Phiên bản NumPy của TGC (dùng trong PPO Environment)
    - compute_reward: Hàm tính Reward PPO (TGC + Phạt ràng buộc)
"""

from .hierarchical_encoder import HierarchicalAttentionEncoder
from .gat_model import LogisticsGATModel
from .dagnn_propagator import DAGNNPropagator
from .tgc_layer3 import TGCLayer3, compute_tgc_numpy, compute_reward
from .sequential_glpo_model import SequentialGLPOModel

__all__ = [
    'HierarchicalAttentionEncoder',
    'LogisticsGATModel',
    'DAGNNPropagator',
    'TGCLayer3',
    'SequentialGLPOModel',
    'compute_tgc_numpy',
    'compute_reward',
]
