import os
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from typing import List

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
moi_dir = os.path.abspath(os.path.join(script_dir, ".."))
project_root = os.path.abspath(os.path.join(moi_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.moi.hetero_graph_builder import HeteroGraphBuilder
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GATConv, to_hetero

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
# MODELS
# =============================================================================

class MLPTaskPredictor(nn.Module):
    def __init__(self, in_channels=41, hidden_dim=128):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(in_channels, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        self.dfac_head = nn.Linear(hidden_dim, 1)
        self.delay_head = nn.Linear(hidden_dim, 2)
        
    def forward(self, x_dict, edge_index_dict=None):
        # MLP ignores edges and other node types
        x = x_dict['task']
        h = self.mlp(x)
        
        dfac = self.dfac_head(h).squeeze(-1)
        delay_out = self.delay_head(h)
        expected_delay = delay_out[:, 0]
        sigma = F.softplus(delay_out[:, 1]) + 0.1
        
        return {
            'duration_factor': dfac,
            'expected_delay': expected_delay,
            'uncertainty_sigma': sigma
        }


class BaseGAT(nn.Module):
    def __init__(self, hidden_dim=128, num_heads=4):
        super().__init__()
        self.conv1 = GATConv((-1, -1), hidden_dim, heads=num_heads, concat=False, add_self_loops=False)
        self.conv2 = GATConv((-1, -1), hidden_dim, heads=num_heads, concat=False, add_self_loops=False)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        return x

class GATTaskPredictor(nn.Module):
    def __init__(self, metadata, hidden_dim=128, num_heads=4):
        super().__init__()
        # 1. Project input features to hidden_dim
        self.proj_dict = nn.ModuleDict({
            'task': nn.Linear(41, hidden_dim),
            'resource': nn.Linear(6, hidden_dim),
            'shift': nn.Linear(5, hidden_dim)
        })
        
        # 2. Base GAT converted to Hetero
        base_gat = BaseGAT(hidden_dim, num_heads)
        self.hetero_gat = to_hetero(base_gat, metadata, aggr='mean')
        
        # 3. Heads
        self.dfac_head = nn.Linear(hidden_dim, 1)
        self.delay_head = nn.Linear(hidden_dim, 2)
        
    def forward(self, x_dict, edge_index_dict):
        h_dict = {k: self.proj_dict[k](x) for k, x in x_dict.items()}
        h_dict = self.hetero_gat(h_dict, edge_index_dict)
        
        h_task = h_dict['task']
        dfac = self.dfac_head(h_task).squeeze(-1)
        delay_out = self.delay_head(h_task)
        expected_delay = delay_out[:, 0]
        sigma = F.softplus(delay_out[:, 1]) + 0.1
        
        return {
            'duration_factor': dfac,
            'expected_delay': expected_delay,
            'uncertainty_sigma': sigma
        }

# =============================================================================
# TRAINING FUNCTION
# =============================================================================

def train_baseline(model_type, data_list, max_epochs=200, lr=0.01, patience=30):
    k_folds = len(data_list)
    print(f"\n================================================================================")
    print(f"[{model_type}] LEAVE-ONE-PROJECT-OUT CV (LOOCV)")
    print(f"================================================================================")
    
    nll_loss_fn = nn.GaussianNLLLoss(eps=1e-6)
    fold_r2_scores = []
    
    for fold in range(k_folds):
        print(f"\n  [Fold {fold+1}/{k_folds}] Val Project: {fold}")
        
        num_train_nodes, num_val_nodes = 0, 0
        all_dfac_train = []
        
        for i, data in enumerate(data_list):
            num_tasks = data['task'].x.size(0)
            if i == fold:
                data['task'].train_mask = torch.zeros(num_tasks, dtype=torch.bool)
                data['task'].val_mask = torch.ones(num_tasks, dtype=torch.bool)
                num_val_nodes += num_tasks
            else:
                data['task'].train_mask = torch.ones(num_tasks, dtype=torch.bool)
                data['task'].val_mask = torch.zeros(num_tasks, dtype=torch.bool)
                num_train_nodes += num_tasks
                all_dfac_train.append(data['task'].y[:, 0])

        target_mean = torch.cat(all_dfac_train).mean().item()
        target_std  = torch.cat(all_dfac_train).std().item() + 1e-6

        if model_type == 'MLP':
            model = MLPTaskPredictor()
        else:
            model = GATTaskPredictor(data_list[0].metadata())
            
        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-3)
        loader = DataLoader(data_list, batch_size=1, shuffle=True)
        
        best_val_loss = float('inf')
        best_val_r2 = float('-inf')
        patience_counter = 0

        for epoch in range(1, max_epochs + 1):
            model.train()
            for data in loader:
                train_mask = data['task'].train_mask
                if not train_mask.any(): continue
                optimizer.zero_grad()
                out = model(data.x_dict, data.edge_index_dict)
                
                y_true = data['task'].y[train_mask]
                t_dfac_norm = (y_true[:, 0] - target_mean) / target_std
                
                loss_mse = F.mse_loss(out['duration_factor'][train_mask], t_dfac_norm)
                loss_nll = nll_loss_fn(out['expected_delay'][train_mask], y_true[:, 1], torch.square(out['uncertainty_sigma'][train_mask]))
                loss = loss_mse + 0.01 * loss_nll
                loss.backward()
                optimizer.step()

            # Validation
            model.eval()
            val_loss = 0.0
            n_val = 0
            all_true_dfac_val = []
            all_pred_dfac_val = []

            with torch.no_grad():
                for data in loader:
                    val_mask = data['task'].val_mask
                    if not val_mask.any(): continue
                    out = model(data.x_dict, data.edge_index_dict)
                    
                    y_val = data['task'].y[val_mask]
                    t_dfac = y_val[:, 0]
                    t_dfac_norm = (t_dfac - target_mean) / target_std
                    
                    v_mse = F.mse_loss(out['duration_factor'][val_mask], t_dfac_norm)
                    v_nll = nll_loss_fn(out['expected_delay'][val_mask], y_val[:, 1], torch.square(out['uncertainty_sigma'][val_mask]))
                    val_loss += (v_mse + 0.01 * v_nll).item()
                    
                    p_dfac_raw = out['duration_factor'][val_mask] * target_std + target_mean
                    all_true_dfac_val.append(t_dfac)
                    all_pred_dfac_val.append(p_dfac_raw)
                    n_val += 1

            if n_val == 0: continue
            avg_val_loss = val_loss / n_val
            
            true_val_cat = torch.cat(all_true_dfac_val)
            pred_val_cat = torch.cat(all_pred_dfac_val)
            avg_val_r2 = calculate_r2(true_val_cat, pred_val_cat).item() if len(true_val_cat) > 0 else 0.0

            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                best_val_r2 = avg_val_r2
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"    [Early Stop] Fold {fold+1} @ Epoch {epoch}. Best Val R2: {best_val_r2:.4f}")
                    break

        fold_r2_scores.append(best_val_r2)
        print(f"  [Fold {fold+1}] Hoan thanh. Best Val R2: {best_val_r2:.4f}")

    r2_mean = np.mean(fold_r2_scores)
    r2_std = np.std(fold_r2_scores)
    print(f"--- TONG KET {k_folds}-FOLD LEAVE-ONE-PROJECT-OUT CV ({model_type}) ---")
    print(f"Mean Test R2:  {r2_mean:.4f} ± {r2_std:.4f}")
    return r2_mean, r2_std

if __name__ == "__main__":
    set_seed(42)
    processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
    projects = ['C2011-07', 'C2012-04', 'C2012-08', 'C2018-09', 'C2019-16']
    p_dirs = [os.path.join(processed_dir, p) for p in projects]

    data_list = []
    for p_dir in p_dirs:
        builder = HeteroGraphBuilder(p_dir)
        data = builder.build()
        if 'y' in data['task']:
            data_list.append(data)
            
    print(f"Da nap {len(data_list)} do thi. Chay cac baselines...")
    
    train_baseline('MLP', data_list)
    train_baseline('GAT', data_list)
