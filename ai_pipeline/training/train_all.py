"""
Script Huấn luyện Toàn bộ Dự án (Multi-Project Training & Anti-Overfitting)
========================================================================
Dự án: GLPO - Graph Logistics Project Optimization

Chức năng:
  1. Quét toàn bộ các dự án trong `data/processed/` (C2011-07, C2012-04, C2012-08, C2018-09, C2019-16, v.v.).
  2. Pha 1: Pretrain GAT + DAGNN Encoder trên toàn bộ các đồ thị dự án.
  3. Pha 2: Huấn luyện PPO Agent luân chuyển đa dự án (Multi-project switching)
     với Domain Randomization và Entropy Regularization để chống overfitting.
"""

import os
import sys
import json
import time
import torch
import numpy as np
from torch_geometric.data import Batch

# Reconfigure stdout for Windows console UTF-8 support
sys.stdout.reconfigure(encoding='utf-8')

# Adjust paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.data_loader import GlPoDataset
from ai_pipeline.models.sequential_glpo_model import SequentialGLPOModel
from ai_pipeline.training.unsupervised_pretrainer import UnsupervisedPretrainer
from ai_pipeline.training.ppo_trainer import PPOTrainer


def run_multi_project_training(
    gae_epochs: int = 300,
    cpm_epochs: int = 500,
    total_ppo_steps: int = 30000
):
    processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
    checkpoints_dir = os.path.join(project_root, 'ai_pipeline', 'checkpoints')
    logs_dir = os.path.join(project_root, 'ai_pipeline', 'logs')
    os.makedirs(checkpoints_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    print("=" * 80)
    print("HUAN LUYEN DA DU AN TOAN DIEN (MULTI-PROJECT TRAINING WITH ANTI-OVERFITTING)")
    print("=" * 80)

    # 1. Load Dataset
    dataset = GlPoDataset(processed_dir)
    print(f"Tim thay {len(dataset)} du an thuc te:")
    for idx, pg in enumerate(dataset.graphs):
        print(f"   [{idx + 1}] Project {pg.project_id}: {pg.data.num_nodes} Nodes, {pg.data.num_edges} Edges")

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Thiet bi tinh toan: {device.upper()}")

    # ------------------------------------------------------------------
    # PHA 1: OFFLINE PRETRAINING GAT + DAGNN TRÊN TOÀN BỘ DỰ ÁN
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("1. PRETRAINING GNN ENCODERS TREN TAT CA DU AN")
    print("-" * 70)

    model = SequentialGLPOModel(
        project_type="logistics_standard",
        gat_out_dim=32,
        dagnn_out_dim=32
    ).to(device)

    pretrainer = UnsupervisedPretrainer(model, device=device)

    # Gộp tất cả 6 đồ thị dự án thành 1 Batch Siêu Đồ Thị (Joint Multi-Graph Batching)
    # Giúp loại bỏ hoàn toàn hiện tượng Catastrophic Forgetting (Quên lãng thảm khốc)
    print(f"\n⚡ Dang gop {len(dataset)} do thi du an thanh 1 Joint Multi-Graph Batch cho GPU...")
    data_list = [pg.data for pg in dataset.graphs]
    batch_data = Batch.from_data_list(data_list).to(device)

    print(f"   • Tong so Nodes: {batch_data.num_nodes} | Tong so Edges: {batch_data.num_edges}")
    print(f"   • Dang chay Pretraining dong thoi tren TAT CA du an (GAE={gae_epochs}, CPM={cpm_epochs} epochs)...")
    
    pretrainer.pretrain_all(
        batch_data,
        gae_epochs=gae_epochs,
        cpm_epochs=cpm_epochs,
        verbose=True
    )

    print("\n[SUCCESS] Hoan tat Joint Multi-Graph Pretraining tren tat ca du an!")
    print(f"Checkpoints da luu tai: {checkpoints_dir}")

    # ------------------------------------------------------------------
    # PHA 2: HUẤN LUYỆN PPO AGENT ĐA DỰ ÁN + CHỐNG OVERFITTING
    # ------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("2. HUAN LUYEN PPO AGENT LUAN CHUYE N DU AN + DOMAIN RANDOMIZATION")
    print("-" * 70)

    ppo_config = {
        # Kiến trúc
        'obs_dim': 50,
        'action_dim': 3,
        'hidden_dims': [256, 128],

        # Hyperparameters chống Overfitting
        'lr': 3e-4,
        'gamma': 0.99,
        'gae_lambda': 0.95,
        'clip_ratio': 0.2,
        'entropy_coef': 0.03,        # Tăng entropy để tăng tính khám phá
        'value_coef': 0.5,
        'max_grad_norm': 0.5,
        'penalty_weight': 1000.0,
        'reward_scale': 1000.0,

        # Cấu hình bước huấn luyện
        'total_timesteps': total_ppo_steps,
        'n_steps': 512,
        'n_epochs': 4,
        'batch_size': 64,

        # Anti-Overfitting: Multi-project switching & Domain randomization
        'use_pretrained': True,
        'enable_domain_randomization': True,
        'enable_relative_state': True,
        'project_switch_interval': 2, # Đổi dự án mỗi 2 episodes
        'pretrain_epochs': 20,

        # Logging
        'log_interval': 5,
        'save_interval': 50,
        'eval_interval': 25,
    }

    trainer = PPOTrainer(
        config=ppo_config,
        processed_dir=processed_dir,
        save_dir=checkpoints_dir,
    )

    training_log = trainer.train()

    print("\n" + "=" * 80)
    print("[SUCCESS] HOAN THANH TIEN HUAN LUYEN & HUAN LUYEN PPO TREN TOAN BO DU AN!")
    print("=" * 80)


if __name__ == "__main__":
    run_multi_project_training()
