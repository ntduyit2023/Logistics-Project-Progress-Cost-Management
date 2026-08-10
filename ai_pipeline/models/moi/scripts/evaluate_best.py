import os
import sys
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

script_dir = os.path.dirname(os.path.abspath(__file__))
moi_dir = os.path.abspath(os.path.join(script_dir, ".."))
project_root = os.path.abspath(os.path.join(moi_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.moi.hgt_model import HGTTaskPredictor
from ai_pipeline.models.moi.hetero_graph_builder import HeteroGraphBuilder
from torch_geometric.loader import DataLoader

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

def augment_features(x_dict, noise_std=0.0):
    augmented = {}
    for node_type, x in x_dict.items():
        if node_type == 'task':
            noise = torch.randn_like(x) * noise_std
            augmented[node_type] = x + noise
        else:
            augmented[node_type] = x
    return augmented

def augment_edges(edge_index_dict, drop_rate=0.0):
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

def mixup_embeddings(embeddings, targets_dfac, targets_delay, alpha=0.0):
    n = embeddings.size(0)
    if n < 2 or alpha <= 0:
        return embeddings, targets_dfac, targets_delay, 1.0
    lam = float(np.random.beta(alpha, alpha))
    perm = torch.randperm(n, device=embeddings.device)
    mixed_emb   = lam * embeddings        + (1 - lam) * embeddings[perm]
    mixed_dfac  = lam * targets_dfac      + (1 - lam) * targets_dfac[perm]
    mixed_delay = lam * targets_delay     + (1 - lam) * targets_delay[perm]
    return mixed_emb, mixed_dfac, mixed_delay, lam

def main():
    # 1. Best parameters from HPO
    lr = 0.002338
    noise_std = 0.01748
    edge_drop_rate = 0.2115
    mixup_alpha = 0.00458
    weight_decay = 0.000983
    
    max_epochs = 100
    patience = 20

    # 2. Load data
    processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
    projects = ['C2011-07', 'C2012-04', 'C2012-08', 'C2018-09', 'C2019-16']
    project_dirs = [os.path.join(processed_dir, p) for p in projects]
    
    data_list = []
    for p_dir in project_dirs:
        builder = HeteroGraphBuilder(p_dir)
        data = builder.build()
        if 'y' in data['task']:
            data_list.append(data)
            
    k_folds = len(data_list)
    pretrained_path = os.path.join(project_root, "checkpoints", "hgt_best_weights.pt")
    nll_loss_fn = nn.GaussianNLLLoss(eps=1e-6)
    
    results = {
        "projects": projects,
        "fold_metrics": [],
        "predictions": {},
        "epoch_history": {}
    }

    print("BAT DAU DANH GIA CHUYEN SAU (EVALUATION)...")
    for fold in range(k_folds):
        print(f"-> Dang chay Fold {fold+1}: Test tren Du an {projects[fold]}")
        set_seed(42 + fold)
        
        all_dfac_train = []
        num_test_tasks = 0
        for i, data in enumerate(data_list):
            num_tasks = data['task'].x.size(0)
            if i == fold:
                num_test_tasks = num_tasks
                indices = torch.randperm(num_tasks)
                num_context = max(1, int(0.20 * num_tasks))
                context_indices = indices[:num_context]
                val_indices = indices[num_context:]
                
                data['task'].train_mask = torch.zeros(num_tasks, dtype=torch.bool)
                data['task'].val_mask = torch.zeros(num_tasks, dtype=torch.bool)
                data['task'].train_mask[context_indices] = True
                data['task'].val_mask[val_indices] = True
                all_dfac_train.append(data['task'].y[context_indices, 0])
            else:
                data['task'].train_mask = torch.ones(num_tasks, dtype=torch.bool)
                data['task'].val_mask = torch.zeros(num_tasks, dtype=torch.bool)
                all_dfac_train.append(data['task'].y[:, 0])

        target_mean = torch.cat(all_dfac_train).mean().item()
        target_std  = torch.cat(all_dfac_train).std().item() + 1e-6

        # Initialize and load weights
        model = HGTTaskPredictor(
            in_channels_dict={'task': 41, 'resource': 6, 'shift': 5},
            hidden_dim=128, num_heads=4, num_layers=2
        )
        if os.path.exists(pretrained_path):
            state_dict = torch.load(pretrained_path, map_location='cpu', weights_only=True)
            model.load_state_dict(state_dict, strict=False)
            
        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max_epochs, eta_min=1e-5)
        loader = DataLoader(data_list, batch_size=1, shuffle=True)
        
        best_val_loss = float('inf')
        best_val_r2 = float('-inf')
        best_preds = []
        best_trues = []
        patience_counter = 0
        
        fold_history = {"train_loss": [], "val_loss": [], "val_r2": []}
        
        for epoch in range(1, max_epochs + 1):
            model.train()
            train_loss_epoch = 0.0
            n_batches = 0
            for data in loader:
                train_mask = data['task'].train_mask
                if not train_mask.any(): continue
                optimizer.zero_grad()
                aug_x = augment_features(data.x_dict, noise_std=noise_std)
                aug_edges = augment_edges(data.edge_index_dict, drop_rate=edge_drop_rate)
                out = model(aug_x, aug_edges)
                
                train_embed = out['task_embeddings'][train_mask]
                y_true = data['task'].y[train_mask]
                mixed_embed, mixed_dfac, mixed_delay, lam = mixup_embeddings(
                    train_embed, y_true[:, 0], y_true[:, 1], alpha=mixup_alpha
                )
                
                pred_dfac_raw = model.dfac_head(mixed_embed).squeeze(-1)
                delay_out = model.delay_head(mixed_embed)
                pred_delay = delay_out[:, 0]
                pred_sigma = F.softplus(delay_out[:, 1]) + 0.1
                
                mixed_dfac_norm = (mixed_dfac - target_mean) / target_std
                loss = F.mse_loss(pred_dfac_raw, mixed_dfac_norm) + 0.01 * nll_loss_fn(pred_delay, mixed_delay, torch.square(pred_sigma))
                loss.backward()
                optimizer.step()
                
                train_loss_epoch += loss.item()
                n_batches += 1
                
            scheduler.step()
            avg_train_loss = train_loss_epoch / max(1, n_batches)
            
            # Validation
            model.eval()
            val_loss = 0.0
            all_true = []
            all_pred = []
            with torch.no_grad():
                for data in loader:
                    val_mask = data['task'].val_mask
                    if not val_mask.any(): continue
                    out = model(data.x_dict, data.edge_index_dict)
                    y_val = data['task'].y[val_mask]
                    p_dfac = out['duration_factor'][val_mask]
                    
                    t_dfac_norm = (y_val[:, 0] - target_mean) / target_std
                    v_mse = F.mse_loss(p_dfac, t_dfac_norm)
                    v_nll = nll_loss_fn(out['expected_delay'][val_mask], y_val[:, 1], torch.square(out['uncertainty_sigma'][val_mask]))
                    val_loss += (v_mse + 0.01 * v_nll).item()
                    
                    p_dfac_raw = p_dfac * target_std + target_mean
                    all_true.append(y_val[:, 0])
                    all_pred.append(p_dfac_raw)
                    
            if len(all_true) > 0:
                avg_val_loss = val_loss / len(all_true)
                t_tensor = torch.cat(all_true)
                p_tensor = torch.cat(all_pred)
                avg_val_r2 = calculate_r2(t_tensor, p_tensor).item()
                
                fold_history["train_loss"].append(avg_train_loss)
                fold_history["val_loss"].append(avg_val_loss)
                fold_history["val_r2"].append(avg_val_r2)
                
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    best_val_r2 = avg_val_r2
                    best_preds = p_tensor.cpu().numpy().tolist()
                    best_trues = t_tensor.cpu().numpy().tolist()
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        break
                        
        print(f"   => Xong! Du an {projects[fold]} (Quy mo {num_test_tasks} tasks) - R2: {best_val_r2:.4f}")
        
        results["fold_metrics"].append({
            "project": projects[fold],
            "total_tasks": num_test_tasks,
            "r2": best_val_r2,
            "best_loss": best_val_loss
        })
        results["predictions"][projects[fold]] = {
            "y_true": best_trues,
            "y_pred": best_preds
        }
        results["epoch_history"][projects[fold]] = fold_history

    out_dir = os.path.join(project_root, "ai_pipeline", "data", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "final_evaluation.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"\n=> Da xuat bao cao JSON thanh cong tai: {out_file}")

if __name__ == "__main__":
    main()
