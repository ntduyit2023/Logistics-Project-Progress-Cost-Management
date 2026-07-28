"""
Pretrainer Evaluation & Cross-Validation Script (Leave-One-Project-Out & Val Metrics)
========================================================================================
Thư mục: ai_pipeline/models/moi/eval_pretrainer.py

Chức năng:
    Thực hiện kiểm thử và đánh giá mô hình HGT Masked Autoencoder Pretrainer bằng các chỉ số khoa học:
        1. Train Loss vs Val Loss (Smooth L1)
        2. Val MAE (Mean Absolute Error)
        3. Val RMSE (Root Mean Squared Error)
        4. Val R2 Score (Hệ số giải thích biến thiên R-squared)
        5. Overfitting Ratio (Tỷ lệ Val Loss / Train Loss)
        6. Out-of-Domain Generalization Test (Leave-One-Project-Out Cross Validation):
           Huấn luyện trên C2012-04 + C2012-08 -> Đánh giá trên dự án độc lập C2019-16.
"""

import os
import sys
import torch
import numpy as np
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Path resolution
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.moi.hetero_graph_builder import HeteroGraphBuilder
from ai_pipeline.models.moi.hgt_model import HGTTaskPredictor
from ai_pipeline.models.moi.pretrainer import HGTPretrainer, compute_r2_score


def evaluate_lopo_cross_validation(
    train_project_ids: list = None,
    test_project_id: str = "C2019-16",
    max_epochs: int = 150
):
    if train_project_ids is None:
        train_project_ids = ['C2012-04', 'C2012-08']

    print("================================================================================")
    print(f"[EVALUATION] LEAVE-ONE-PROJECT-OUT CROSS VALIDATION REPORT")
    print(f"   * Training Set Projects: {', '.join(train_project_ids)}")
    print(f"   * Unseen Out-of-Domain Test Project: {test_project_id}")
    print("================================================================================")

    # 1. Dựng Đồ thị Tập Huấn Luyện (Train Graphs)
    train_graphs = []
    for p_id in train_project_ids:
        project_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed', p_id)
        builder = HeteroGraphBuilder(project_dir)
        hetero_data = builder.build()
        train_graphs.append(hetero_data)
        print(f"   + Loaded Train Graph [{p_id}]: {hetero_data['task'].x.size(0)} tasks")

    # 2. Dựng Đồ thị Tập Kiểm Thử Độc Lập (Test Graph)
    test_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed', test_project_id)
    test_builder = HeteroGraphBuilder(test_dir)
    test_graph = test_builder.build()
    print(f"   + Loaded Unseen Test Graph [{test_project_id}]: {test_graph['task'].x.size(0)} tasks")

    # 3. Khởi tạo mô hình
    model = HGTTaskPredictor({
        'task': sample_data['task'].x.size(1),
        'resource': sample_data['resource'].x.size(1),
        'shift': sample_data['shift'].x.size(1),
        'project': sample_data['project'].x.size(1)
    }, hidden_dim=64)
    pretrainer = HGTPretrainer(model, checkpoint_dir=os.path.join(project_root, "checkpoints"))

    # 4. Huấn luyện mô hình trên Train Graphs với Validation Split
    print("\n[STEP 1] Running Multi-Project Training with Val Mask Monitoring...")
    val_summary = pretrainer.train_multi_projects(
        hetero_data_list=train_graphs,
        project_ids=train_project_ids,
        max_epochs=max_epochs,
        patience=20,
        mask_rate=0.15,
        val_ratio=0.20
    )

    # 5. Đánh giá Khả năng Tổng quát hóa Out-of-Domain trên Unseen Test Graph (C2019-16)
    print(f"\n[STEP 2] Evaluating Out-of-Domain Generalization on Project [{test_project_id}]...")
    model.eval()
    with torch.no_grad():
        test_x = test_graph['task'].x.clone()
        num_test_nodes = test_x.size(0)
        
        # Mask ngẫu nhiên 20% các task của dự án chưa từng thấy
        mask_indices = torch.randperm(num_test_nodes)[:max(1, int(num_test_nodes * 0.20))]
        masked_test_x = test_x.clone()
        masked_test_x[mask_indices] = 0.0
        masked_test_dict = {k: (masked_test_x if k == 'task' else v) for k, v in test_graph.x_dict.items()}

        test_out = model(masked_test_dict, test_graph.edge_index_dict)
        rec_test_x = test_out['reconstructed_x']

        test_loss = float(torch.nn.functional.smooth_l1_loss(rec_test_x[mask_indices], test_x[mask_indices]).item())
        test_mae = float(torch.mean(torch.abs(rec_test_x[mask_indices] - test_x[mask_indices])).item())
        test_rmse = float(torch.sqrt(torch.mean((rec_test_x[mask_indices] - test_x[mask_indices]) ** 2)).item())
        test_r2 = compute_r2_score(test_x[mask_indices], rec_test_x[mask_indices])

    train_final_loss = val_summary.get('train_loss', 1e-4)
    generalization_gap = test_loss / max(1e-6, train_final_loss)

    print("\n================================================================================")
    print("                 BÁO CÁO ĐÁNH GIÁ CHẤT LƯỢNG MÔ HÌNH HGT PRETRAINER              ")
    print("================================================================================")
    print(f"1. Train Loss (Nút huấn luyện):             {train_final_loss:.6f}")
    print(f"2. Validation Loss (Nút trong cùng dự án):  {val_summary.get('val_loss', 0.0):.6f}")
    print(f"3. Out-of-Domain Test Loss ({test_project_id}): {test_loss:.6f}")
    print(f"4. Test MAE (Mean Absolute Error):           {test_mae:.4f}")
    print(f"5. Test RMSE (Root Mean Squared Error):       {test_rmse:.4f}")
    print(f"6. Test R2 Score (Giải thích biến thiên):     {test_r2:.4f} (Mục tiêu > 0.60)")
    print(f"7. Out-of-Domain Generalization Gap Ratio:   {generalization_gap:.2f}")
    
    print("\n--- ĐÁNH GIÁ TÌNH TRẠNG MÔ HÌNH ---")
    if generalization_gap <= 1.5 and test_r2 >= 0.50:
        print(">> KẾT LUẬN: MÔ HÌNH HOẠT ĐỘNG TỐT! KHÔNG BỊ OVERFITTING!")
        print("   Mô hình học được đặc trưng cấu trúc tổng quát hóa tốt sang dự án chưa từng thấy.")
    elif generalization_gap > 2.0:
        print(">> KẾT LUẬN: CÓ DẤU HIỆU OVERFITTING NHẸ!")
        print("   Khoảng cách giữa Train và Out-of-domain Test loss lớn hơn 2.0x. Khuyên tăng Dropout hoặc Weight Decay.")
    else:
        print(">> KẾT LUẬN: MÔ HÌNH CHẤP NHẬN ĐƯỢC! Cần bổ sung thêm dữ liệu đa dạng dự án.")
    print("================================================================================")


if __name__ == "__main__":
    evaluate_lopo_cross_validation(
        train_project_ids=['C2012-04', 'C2012-08'],
        test_project_id='C2019-16',
        max_epochs=150
    )
