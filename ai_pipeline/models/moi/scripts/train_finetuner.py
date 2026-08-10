import os
import sys
import shutil
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from sklearn.linear_model import Ridge
from typing import List

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
moi_dir = os.path.abspath(os.path.join(script_dir, ".."))
project_root = os.path.abspath(os.path.join(moi_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.moi.hgt_model import HGTTaskPredictor
from ai_pipeline.models.moi.hetero_graph_builder import HeteroGraphBuilder
from torch_geometric.loader import DataLoader


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_r2(y_true, y_pred):
    ss_res = torch.sum((y_true - y_pred) ** 2)
    ss_tot = torch.sum((y_true - torch.mean(y_true)) ** 2)
    if ss_tot == 0:
        return torch.tensor(0.0, device=y_true.device)
    return 1 - (ss_res / ss_tot)

def set_seed(seed=42):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)


# =============================================================================
# KỸ THUẬT 2: GRAPH DATA AUGMENTATION (Gaussian Noise + Edge Dropout)
# =============================================================================

def augment_features(x_dict, noise_std=0.02):
    augmented = {}
    for node_type, x in x_dict.items():
        if node_type == 'task':
            noise = torch.randn_like(x) * noise_std
            augmented[node_type] = x + noise
        else:
            augmented[node_type] = x
    return augmented


def augment_edges(edge_index_dict, drop_rate=0.20):
    augmented = {}
    for edge_type, edge_index in edge_index_dict.items():
        if edge_index.size(1) == 0:
            augmented[edge_type] = edge_index
            continue
        num_edges = edge_index.size(1)
        keep_mask = torch.rand(num_edges) > drop_rate
        if keep_mask.sum() == 0:
            keep_mask[torch.randint(num_edges, (1,))] = True
        augmented[edge_type] = edge_index[:, keep_mask]
    return augmented


# =============================================================================
# KỸ THUẬT MỚI 1: MANIFOLD MIXUP TRÊN EMBEDDING SPACE
# =============================================================================

def mixup_embeddings(embeddings, targets_dfac, targets_delay, alpha=0.2):
    n = embeddings.size(0)
    if n < 2 or alpha <= 0:
        return embeddings, targets_dfac, targets_delay, 1.0

    lam = float(np.random.beta(alpha, alpha))
    perm = torch.randperm(n, device=embeddings.device)

    mixed_emb   = lam * embeddings        + (1 - lam) * embeddings[perm]
    mixed_dfac  = lam * targets_dfac      + (1 - lam) * targets_dfac[perm]
    mixed_delay = lam * targets_delay     + (1 - lam) * targets_delay[perm]

    return mixed_emb, mixed_dfac, mixed_delay, lam


# =============================================================================
# HÀM TẠO MÔ HÌNH MỚI
# =============================================================================

def build_model(moi_dir, checkpoint_dir):
    model = HGTTaskPredictor(
        in_channels_dict={'task': 41, 'resource': 6, 'shift': 5},
        hidden_dim=128,
        num_heads=4,
        num_layers=2
    )
    return model


# =============================================================================
# HÀM TRAINING CHÍNH
# =============================================================================

def train_finetuner(
    project_dirs: List[str],
    checkpoint_dir: str = "checkpoints",
    max_epochs: int = 300,
    lr: float = 0.01,
    patience: int = 30,
    noise_std: float = 0.02,
    edge_drop_rate: float = 0.20,
    mixup_alpha: float = 0.2,
    use_cosine_lr: bool = True,
):
    print("================================================================================")
    print(f"[HGT] LEAVE-ONE-PROJECT-OUT CV (LOOCV)")
    print(f"Tong so du an: {len(project_dirs)}")
    print("================================================================================")

    set_seed(42)

    data_list = []
    total_tasks = 0
    for p_dir in project_dirs:
        if not os.path.exists(p_dir):
            print(f"  [WARN] Khong tim thay thu muc: {p_dir}")
            continue
        builder = HeteroGraphBuilder(p_dir)
        data = builder.build()
        if 'y' in data['task']:
            num_tasks = data['task'].x.size(0)
            total_tasks += num_tasks
            data_list.append(data)

    if not data_list:
        print("[ERROR] Khong co do thi nao hop le de huan luyen.")
        return

    k_folds = len(data_list)
    print(f"Da nap {k_folds} do thi. Tong so tasks: {total_tasks}")

    os.makedirs(os.path.join(moi_dir, checkpoint_dir), exist_ok=True)
    nll_loss_fn = nn.GaussianNLLLoss(eps=1e-6)
    
    fold_r2_scores = []
    fold_mse_scores = []

    for fold in range(k_folds):
        print(f"\n{'='*60}")
        print(f"  [Fold {fold+1}/{k_folds}] Val Project: {os.path.basename(project_dirs[fold])}")
        print(f"{'='*60}")

        num_train_nodes, num_val_nodes = 0, 0
        all_dfac_train = []
        
        for i, data in enumerate(data_list):
            num_tasks = data['task'].x.size(0)
            if i == fold:
                indices = torch.randperm(num_tasks)
                num_context = max(1, int(0.20 * num_tasks))
                context_indices = indices[:num_context]
                val_indices = indices[num_context:]
                
                data['task'].train_mask = torch.zeros(num_tasks, dtype=torch.bool)
                data['task'].val_mask = torch.zeros(num_tasks, dtype=torch.bool)
                data['task'].train_mask[context_indices] = True
                data['task'].val_mask[val_indices] = True
                
                num_train_nodes += num_context
                num_val_nodes += (num_tasks - num_context)
                all_dfac_train.append(data['task'].y[context_indices, 0])
            else:
                data['task'].train_mask = torch.ones(num_tasks, dtype=torch.bool)
                data['task'].val_mask = torch.zeros(num_tasks, dtype=torch.bool)
                num_train_nodes += num_tasks
                all_dfac_train.append(data['task'].y[:, 0])

        target_mean = torch.cat(all_dfac_train).mean().item()
        target_std  = torch.cat(all_dfac_train).std().item() + 1e-6

        print(f"    Train: {num_train_nodes} tasks | Val: {num_val_nodes} tasks")
        print(f"    Target Normalization (Train): Mean={target_mean:.4f}, Std={target_std:.4f}")

        model = build_model(moi_dir, checkpoint_dir)
        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-3)

        scheduler = None
        if use_cosine_lr:
            scheduler = optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=max_epochs, eta_min=1e-5
            )

        loader = DataLoader(data_list, batch_size=1, shuffle=True)
        best_val_loss   = float('inf')
        best_val_r2     = float('-inf')
        best_val_mse    = float('inf')
        patience_counter = 0

        for epoch in range(1, max_epochs + 1):
            model.train()
            total_loss = 0.0
            n_batches = 0
            
            all_true_dfac_train = []
            all_pred_dfac_train = []

            for data in loader:
                train_mask = data['task'].train_mask
                if not train_mask.any():
                    continue

                optimizer.zero_grad()

                aug_x     = augment_features(data.x_dict, noise_std=noise_std)
                aug_edges = augment_edges(data.edge_index_dict, drop_rate=edge_drop_rate)
                out = model(aug_x, aug_edges)

                train_embed = out['task_embeddings'][train_mask]
                y_true      = data['task'].y[train_mask]
                true_dfac   = y_true[:, 0]
                true_delay  = y_true[:, 1]

                mixed_embed, mixed_dfac, mixed_delay, lam = mixup_embeddings(
                    train_embed, true_dfac, true_delay, alpha=mixup_alpha
                )

                pred_dfac_raw = model.dfac_head(mixed_embed).squeeze(-1)
                delay_out     = model.delay_head(mixed_embed)
                pred_delay    = delay_out[:, 0]
                pred_sigma    = F.softplus(delay_out[:, 1]) + 0.1

                mixed_dfac_norm = (mixed_dfac - target_mean) / target_std
                loss_mse = F.mse_loss(pred_dfac_raw, mixed_dfac_norm)
                loss_nll = nll_loss_fn(pred_delay, mixed_delay, torch.square(pred_sigma))
                loss = loss_mse + 0.01 * loss_nll
                loss.backward()
                optimizer.step()

                with torch.no_grad():
                    orig_pred = model.dfac_head(out['task_embeddings'][train_mask]).squeeze(-1)
                    orig_pred_raw = orig_pred * target_std + target_mean
                    all_true_dfac_train.append(true_dfac)
                    all_pred_dfac_train.append(orig_pred_raw)

                total_loss += loss.item()
                n_batches  += 1

            if n_batches == 0:
                continue

            if scheduler is not None:
                scheduler.step()

            avg_loss = total_loss / n_batches
            avg_r2 = calculate_r2(torch.cat(all_true_dfac_train), torch.cat(all_pred_dfac_train)).item() if len(all_true_dfac_train) > 0 else 0.0

            model.eval()
            val_loss = 0.0
            n_val = 0
            
            all_true_dfac_val = []
            all_pred_dfac_val = []

            with torch.no_grad():
                for data in loader:
                    val_mask = data['task'].val_mask
                    if not val_mask.any():
                        continue

                    out    = model(data.x_dict, data.edge_index_dict)
                    y_val  = data['task'].y[val_mask]
                    t_dfac  = y_val[:, 0]
                    t_delay = y_val[:, 1]

                    p_dfac  = out['duration_factor'][val_mask]
                    p_delay = out['expected_delay'][val_mask]
                    p_sigma = out['uncertainty_sigma'][val_mask]

                    t_dfac_norm = (t_dfac - target_mean) / target_std
                    v_mse = F.mse_loss(p_dfac, t_dfac_norm)
                    v_nll = nll_loss_fn(p_delay, t_delay, torch.square(p_sigma))
                    val_loss += (v_mse + 0.01 * v_nll).item()

                    p_dfac_raw = p_dfac * target_std + target_mean
                    all_true_dfac_val.append(t_dfac)
                    all_pred_dfac_val.append(p_dfac_raw)
                    n_val  += 1

            if n_val == 0:
                continue

            avg_val_loss = val_loss / n_val
            true_val_cat = torch.cat(all_true_dfac_val)
            pred_val_cat = torch.cat(all_pred_dfac_val)
            avg_val_r2 = calculate_r2(true_val_cat, pred_val_cat).item() if len(true_val_cat) > 0 else 0.0
            avg_val_mse = F.mse_loss(pred_val_cat, true_val_cat).item()

            if epoch % 20 == 0 or epoch == 1:
                curr_lr = scheduler.get_last_lr()[0] if scheduler else lr
                print(f"    Epoch {epoch:03d} | LR: {curr_lr:.5f} | "
                      f"Train Loss: {avg_loss:.4f} (R2: {avg_r2:.4f}) | "
                      f"Val Loss: {avg_val_loss:.4f} (R2: {avg_val_r2:.4f})")

            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                best_val_r2 = avg_val_r2
                best_val_mse = avg_val_mse
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"    [Early Stop] Fold {fold+1} dung tai Epoch {epoch}. "
                          f"Best Val R2: {best_val_r2:.4f}")
                    break

        fold_r2_scores.append(best_val_r2)
        fold_mse_scores.append(best_val_mse)
        print(f"  [Fold {fold+1}] Hoan thanh. Best Val R2: {best_val_r2:.4f}")

    print("\n================================================================================")
    print(f"--- TONG KET {k_folds}-FOLD LEAVE-ONE-PROJECT-OUT CV (HGT) ---")
    r2_mean = np.mean(fold_r2_scores)
    r2_std = np.std(fold_r2_scores)
    mse_mean = np.mean(fold_mse_scores)
    mse_std = np.std(fold_mse_scores)
    print(f"Mean Test R2:  {r2_mean:.4f} ± {r2_std:.4f}")
    print(f"Mean Test MSE: {mse_mean:.4f} ± {mse_std:.4f}")
    for i, r2 in enumerate(fold_r2_scores):
        print(f"  Project {i+1} R2: {r2:.4f}")
    print("================================================================================")

if __name__ == "__main__":
    processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
    projects = ['C2011-07', 'C2012-04', 'C2012-08', 'C2018-09', 'C2019-16']
    p_dirs = [os.path.join(processed_dir, p) for p in projects]

    train_finetuner(
        p_dirs,
        max_epochs=300,
        patience=30,
        noise_std=0.02,
        edge_drop_rate=0.20,
        mixup_alpha=0.2,
        use_cosine_lr=True,
    )
