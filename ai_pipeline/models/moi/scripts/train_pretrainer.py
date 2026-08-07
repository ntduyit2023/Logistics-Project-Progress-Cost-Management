"""
Multi-Domain & Multi-Project HGT Pretrainer Training Script (Deterministic & Reproducible)
============================================================================================
Thư mục: ai_pipeline/models/moi/train_pretrainer.py

Chức năng:
    Huấn luyện HGT Pretrainer trên toàn bộ 5 tập dữ liệu đa loại hình dự án (CON, ITLG, PRO):
        - C2011-07 (Patient Transport System - PRO)
        - C2012-04 (Asti-Cuneo Highway - CON)
        - C2012-08 (Sea Electricity - CON)
        - C2018-09 (CarSharing Platform - ITLG)
        - C2019-16 (Lock Ganzepoot - CON)
    Cấu hình seed cố định (set_seed(42)) đảm bảo kết quả tái lập 100% nhất quán giữa các lần chạy.
    Xuất bộ trọng số tối ưu nhất ra file: checkpoints/hgt_best_weights.pt
"""

import os
import sys
import random
import torch
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Path resolution
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.moi.hetero_graph_builder import HeteroGraphBuilder
from ai_pipeline.models.moi.hgt_model import HGTTaskPredictor
from ai_pipeline.models.moi.pretrainer import HGTPretrainer


def set_seed(seed: int = 42):
    """Cố định Random Seed để đảm bảo tính tái lập 100% (Reproducibility) giữa các lần chạy."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_multi_domain_projects(
    target_projects: list = None,
    max_epochs: int = 300,
    patience: int = 40,
    seed: int = 42
):
    set_seed(seed)
    
    if target_projects is None:
        target_projects = ['C2011-07', 'C2012-04', 'C2012-08', 'C2018-09', 'C2019-16']

    print("================================================================================")
    print(f"[START] KET HOP DA LOAI HINH (MULTI-DOMAIN) PRETRAINING (SEED={seed}) TREN {len(target_projects)} DU AN:")
    for p in target_projects:
        print(f"   * {p}")
    print("================================================================================")

    # 1. Dựng Đồ thị HeteroData cho từng dự án
    hetero_data_list = []
    valid_projects = []

    for p_id in target_projects:
        project_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed', p_id)
        if not os.path.exists(project_dir):
            print(f"[WARNING] Khong tim thay thu muc du an: {project_dir}, bo qua.")
            continue
        
        print(f"\n[BUILD] Dang dung do thi HeteroData (Z-Score Normalization) cho du an {p_id}...")
        builder = HeteroGraphBuilder(project_dir)
        hetero_data = builder.build()
        total_edges = sum(hetero_data[edge_type].edge_index.size(1) for edge_type in hetero_data.edge_types)
        print(f"   -> Nodes: Task={hetero_data['task'].x.size(0)} | Resource={hetero_data['resource'].x.size(0)} | "
              f"Shift={hetero_data['shift'].x.size(0)} | "
              f"Edges={total_edges}")
        hetero_data_list.append(hetero_data)
        valid_projects.append(p_id)

    if not hetero_data_list:
        raise RuntimeError("Khong nap duoc do thi du an nao!")

    # 2. Khởi tạo Mô hình HGT Predictor với Hybrid Readout Pooling (3 Node Types)
    sample_data = hetero_data_list[0]
    model = HGTTaskPredictor({
        'task': sample_data['task'].x.size(1),
        'resource': sample_data['resource'].x.size(1),
        'shift': sample_data['shift'].x.size(1)
    }, hidden_dim=128)
    checkpoint_dir = os.path.join(project_root, "checkpoints")
    pretrainer = HGTPretrainer(model, checkpoint_dir=checkpoint_dir)

    # 3. Tiến hành Huấn luyện Tự Giám Sát Multi-Domain với Early Stopping & Validation Monitoring
    print(f"\n[TRAIN] Kich hoat Masked Autoencoder Pretrainer (300 Epochs Max, Early Stop Patience={patience})...")
    pretrainer.train_multi_projects(
        hetero_data_list=hetero_data_list,
        project_ids=valid_projects,
        max_epochs=max_epochs,
        patience=patience,
        mask_rate=0.25,
        val_ratio=0.20,
        lr=0.001
    )

    print("\n================================================================================")
    print("[SUCCESS] DA DAT DUOC BO THAM SO TOI UU NHAT HOAN HAO CHO CAC DANG DU AN!")
    print(f"Checkpoint location: {pretrainer.checkpoint_path}")
    print("================================================================================")


if __name__ == "__main__":
    train_multi_domain_projects(
        target_projects=['C2011-07', 'C2012-04', 'C2012-08', 'C2018-09', 'C2019-16'],
        max_epochs=300,
        patience=40,
        seed=42
    )
