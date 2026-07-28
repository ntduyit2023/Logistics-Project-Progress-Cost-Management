"""
Masked Autoencoder Pretrainer (Phase 0 Self-Supervised Reconstruction)
========================================================================
Thư mục: ai_pipeline/models/moi/pretrainer.py

Chức năng:
    Thực hiện Huấn luyện Tự Giám Sát (Self-Supervised Pretraining) cho mô hình HGT
    bằng cơ chế Masked Feature Reconstruction với Smooth L1 Loss chuẩn hóa.
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from typing import List, Dict, Any, Tuple
from ai_pipeline.models.moi.hgt_model import HGTTaskPredictor


def compute_r2_score(y_true: torch.Tensor, y_pred: torch.Tensor) -> float:
    """
    Tính hệ số giải thích biến thiên R2 Score tiêu chuẩn trên mảng 1D.
    """
    y_true_np = y_true.detach().cpu().numpy().flatten()
    y_pred_np = y_pred.detach().cpu().numpy().flatten()
    
    ss_res = np.sum((y_true_np - y_pred_np) ** 2)
    ss_tot = np.sum((y_true_np - np.mean(y_true_np)) ** 2) + 1e-8
    r2 = 1.0 - (ss_res / ss_tot)
    return float(r2)


class HGTPretrainer:
    """
    Trình quản lý Pretraining tự động cho HGT dùng Smooth L1 Reconstruction Loss.
    """
    def __init__(self, model: HGTTaskPredictor, checkpoint_dir: str = "checkpoints"):
        self.model = model
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_path = os.path.join(checkpoint_dir, "hgt_best_weights.pt")
        os.makedirs(checkpoint_dir, exist_ok=True)

    def train_multi_projects(
        self,
        hetero_data_list: List[Any],
        project_ids: List[str] = None,
        max_epochs: int = 300,
        patience: int = 40,
        mask_rate: float = 0.25,
        val_ratio: float = 0.20,
        lr: float = 0.001
    ) -> Dict[str, Any]:
        """
        Huấn luyện Pretraining tự giám sát với Train/Val Mask Split và Smooth L1 Loss.
        """
        if not hetero_data_list:
            print("[Pretrainer] Danh sach do thi rong!")
            return {}

        proj_str = ", ".join(project_ids) if project_ids else f"{len(hetero_data_list)} du an"
        print("================================================================================")
        print(f"[Pretrainer] SMOOTH L1 RECONSTRUCTION PRETRAINING: {proj_str}")
        print(f"   * Max Epochs: {max_epochs} | Patience: {patience} | Mask Rate: {mask_rate*100:.0f}%")
        print("================================================================================")

        optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10)
        
        best_val_loss = float('inf')
        best_metrics = {}
        no_improve_count = 0

        for epoch in range(1, max_epochs + 1):
            self.model.train()
            optimizer.zero_grad()
            
            epoch_train_loss = 0.0
            epoch_val_loss = 0.0
            val_y_true_list, val_y_pred_list = [], []

            for hetero_data in hetero_data_list:
                x_dict = hetero_data.x_dict
                edge_index_dict = hetero_data.edge_index_dict
                task_x = x_dict['task'].clone()
                num_nodes = task_x.size(0)

                if num_nodes > 0:
                    perm = torch.randperm(num_nodes)
                    num_masked = max(2, int(num_nodes * mask_rate))
                    masked_indices = perm[:num_masked]
                    
                    num_val = max(1, int(num_masked * val_ratio))
                    val_indices = masked_indices[:num_val]
                    train_indices = masked_indices[num_val:]

                    masked_task_x = task_x.clone()
                    masked_task_x[masked_indices] = 0.0
                    masked_x_dict = {k: (masked_task_x if k == 'task' else v) for k, v in x_dict.items()}
                else:
                    masked_x_dict = x_dict
                    train_indices = torch.tensor([], dtype=torch.long)
                    val_indices = torch.tensor([], dtype=torch.long)

                out = self.model(masked_x_dict, edge_index_dict)
                reconstructed_x = out['reconstructed_x']

                # 1. Train Smooth L1 Loss
                if len(train_indices) > 0:
                    train_loss = F.smooth_l1_loss(reconstructed_x[train_indices], task_x[train_indices])
                    epoch_train_loss += train_loss
                
                # 2. Validation Loss (Out-of-sample prediction)
                if len(val_indices) > 0:
                    with torch.no_grad():
                        val_loss = F.smooth_l1_loss(reconstructed_x[val_indices], task_x[val_indices])
                        epoch_val_loss += val_loss
                        val_y_true_list.append(task_x[val_indices])
                        val_y_pred_list.append(reconstructed_x[val_indices])

            # Lan truyền ngược gradient từ Train Loss & Gradient Clipping
            avg_train_loss = epoch_train_loss / len(hetero_data_list)
            avg_val_loss = (epoch_val_loss / len(hetero_data_list)) if epoch_val_loss > 0 else avg_train_loss
            
            if isinstance(avg_train_loss, torch.Tensor) and avg_train_loss.requires_grad:
                avg_train_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()

            # Thống kê Metric Validation (MAE, RMSE, R2, Overfit Ratio)
            train_loss_val = avg_train_loss.item() if isinstance(avg_train_loss, torch.Tensor) else float(avg_train_loss)
            val_loss_val = avg_val_loss.item() if isinstance(avg_val_loss, torch.Tensor) else float(avg_val_loss)
            
            scheduler.step(val_loss_val)

            if val_y_true_list:
                cat_true = torch.cat(val_y_true_list)
                cat_pred = torch.cat(val_y_pred_list)
                val_mae = float(torch.mean(torch.abs(cat_pred - cat_true)).item())
                val_rmse = float(torch.sqrt(torch.mean((cat_pred - cat_true) ** 2)).item())
                val_r2 = compute_r2_score(cat_true, cat_pred)
            else:
                val_mae, val_rmse, val_r2 = 0.0, 0.0, 0.0

            overfit_ratio = val_loss_val / max(1e-6, train_loss_val)

            # Đánh giá Early Stopping theo Val Loss
            if val_loss_val < best_val_loss - 1e-4:
                best_val_loss = val_loss_val
                best_metrics = {
                    'epoch': epoch,
                    'train_loss': train_loss_val,
                    'val_loss': val_loss_val,
                    'val_mae': val_mae,
                    'val_rmse': val_rmse,
                    'val_r2': val_r2,
                    'overfit_ratio': overfit_ratio
                }
                no_improve_count = 0
                torch.save(self.model.state_dict(), self.checkpoint_path)
                improved_str = " (Saved Best Weights)"
            else:
                no_improve_count += 1
                improved_str = ""

            # In thông số đánh giá chi tiết
            if epoch % 10 == 0 or epoch == 1 or improved_str:
                overfit_warning = " [CANH BAO OVERFIT!]" if overfit_ratio > 1.5 else ""
                print(f"   * Epoch {epoch:03d}/{max_epochs:03d} | Train Loss: {train_loss_val:.6f} | "
                      f"Val Loss: {val_loss_val:.6f} | Val MAE: {val_mae:.4f} | Val R2: {val_r2:.4f} | "
                      f"Ratio: {overfit_ratio:.2f}{improved_str}{overfit_warning}")

            if no_improve_count >= patience:
                print(f"\n[EARLY STOPPING] Model dat nguong toi uu o Epoch {best_metrics['epoch']} "
                      f"(Val Loss khong giam sau {patience} epochs consecutive).")
                break

        print("\n================================================================================")
        print("[PRETRAINER EVALUATION REPORT] SUMMARY METRICS:")
        print(f"   - Optimal Epoch: {best_metrics.get('epoch')}")
        print(f"   - Train Loss (Smooth L1): {best_metrics.get('train_loss', 0.0):.6f}")
        print(f"   - Val Loss (Out-of-Sample): {best_metrics.get('val_loss', 0.0):.6f}")
        print(f"   - Val MAE (Mean Absolute Error): {best_metrics.get('val_mae', 0.0):.4f}")
        print(f"   - Val RMSE (Root Mean Squared Error): {best_metrics.get('val_rmse', 0.0):.4f}")
        print(f"   - Val R2 Score: {best_metrics.get('val_r2', 0.0):.4f}")
        print(f"   - Overfitting Ratio (Val/Train): {best_metrics.get('overfit_ratio', 1.0):.2f} (Ideal <= 1.2)")
        print("================================================================================")

        self.model.eval()
        return best_metrics

    def train_or_load(self, hetero_data, epochs: int = 50, mask_rate: float = 0.25, force_retrain: bool = False):
        if os.path.exists(self.checkpoint_path) and not force_retrain:
            print(f"[Pretrainer] Tai trong so Pretrained tu: {self.checkpoint_path}")
            try:
                try:
                    state_dict = torch.load(self.checkpoint_path, map_location='cpu', weights_only=True)
                except TypeError:
                    state_dict = torch.load(self.checkpoint_path, map_location='cpu')
                self.model.load_state_dict(state_dict)
                self.model.eval()
                return True
            except Exception as e:
                print(f"[Pretrainer] File checkpoint bi loi, khoi dong lai Pretraining: {e}")

        return self.train_multi_projects([hetero_data], max_epochs=epochs, mask_rate=mask_rate)
