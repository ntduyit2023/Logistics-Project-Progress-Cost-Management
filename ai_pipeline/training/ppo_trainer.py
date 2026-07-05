"""
Mô-đun PPO Agent: Huấn luyện Chính sách Lập lịch Dự án
========================================================
Dự án: GLPO - Graph Logistics Project Optimization

Mô tả:
    Triển khai thuật toán PPO (Proximal Policy Optimization) tùy biến
    để huấn luyện Agent lập lịch trên môi trường LogisticsGymEnv.

    Đặc điểm nổi bật:
    1. Invalid Action Masking: Tích hợp sẵn cơ chế masked softmax
       để ngăn Agent chọn hành động vi phạm ràng buộc cứng.
    2. Tương thích với Dict Observation Space (task_features 72
       + task_context 6 + project_state 8 = 86 chiều).
    3. Multi-project Training: Huấn luyện trên nhiều dự án khác nhau
       để Agent học chính sách tổng quát.
    4. Tích hợp UnsupervisedPretrainer: Tự động chạy pre-training
       khi chuyển đổi dự án mới.

Luồng sử dụng:
    trainer = PPOTrainer(config)
    trainer.train()
    trainer.save("ppo_agent.pt")

Nguồn tham chiếu:
    - Schulman et al. (2017): "Proximal Policy Optimization Algorithms"
    - ai_pipeline/envs/logistics_gym_env.py
    - ai_pipeline/training/unsupervised_pretrainer.py
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
import sys
import time
import json
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Thêm đường dẫn project
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ============================================================================
# CẤU HÌNH HUẤN LUYỆN PPO
# ============================================================================
DEFAULT_PPO_CONFIG = {
    # ── Kiến trúc mạng ──
    'obs_dim': 86,              # 72 (task_features) + 6 (task_context) + 8 (project_state)
    'action_dim': 3,            # Normal / Crash / Outsource
    'hidden_dims': [256, 128],  # Kích thước các tầng ẩn

    # ── Tham số PPO ──
    'lr': 3e-4,                 # Tốc độ học (Learning Rate)
    'gamma': 0.99,              # Hệ số chiết khấu (Discount Factor)
    'gae_lambda': 0.95,         # GAE Lambda (Generalized Advantage Estimation)
    'clip_ratio': 0.2,          # PPO Clip Ratio (ε)
    'entropy_coef': 0.01,       # Hệ số entropy (khuyến khích khám phá)
    'value_coef': 0.5,          # Hệ số critic loss
    'max_grad_norm': 0.5,       # Gradient Clipping

    'penalty_weight': 1000.0,   # Hệ số phạt vi phạm ràng buộc (1000.0 kích hoạt dynamic scale)
    'reward_scale': 1000.0,     # Hệ số co giãn phần thưởng (1000.0 kích hoạt dynamic scale)

    # ── Huấn luyện ──
    'total_timesteps': 50_000,  # Tổng số bước huấn luyện
    'n_steps': 256,             # Số bước thu thập trước khi cập nhật
    'n_epochs': 4,              # Số lần cập nhật trên cùng một batch
    'batch_size': 64,           # Kích thước mini-batch

    # ── Multi-project ──
    'project_switch_interval': 5,  # Chuyển đổi dự án mỗi N episodes
    'pretrain_epochs': 30,         # Số epochs pre-training mỗi khi chuyển dự án

    # ── Logging ──
    'log_interval': 10,          # In kết quả mỗi N episodes
    'save_interval': 100,        # Lưu checkpoint mỗi N episodes
    'eval_interval': 50,         # Đánh giá chính sách mỗi N episodes

    # ── Nâng cấp tiền huấn luyện & Đa nhiệm ──
    'freeze_epochs': 20,                # Số epoch/lần cập nhật freeze encoder
    'use_pretrained': True,              # Tự động nạp checkpoints tiền huấn luyện
    'enable_domain_randomization': True, # Bật ngẫu nhiên hóa ràng buộc ở train
    'enable_relative_state': True,       # Dùng đặc trưng tỷ lệ thay vì tuyệt đối
    'random_seed': 42,                  # Random seed cho huấn luyện
    'dr_deadline_range': 0.15,          # Ngẫu nhiên hóa deadline +-15%
    'dr_resource_range': 0.20,          # Ngẫu nhiên hóa tài nguyên +-20%
    'dr_cost_range': 0.10,              # Ngẫu nhiên hóa chi phí +-10%
}


# ============================================================================
# MẠNG NƠRON ACTOR-CRITIC
# ============================================================================
class ActorCritic(nn.Module):
    """
    Mạng nơ-ron Actor-Critic cho PPO Agent.

    Actor: Nhận observation → xuất phân phối xác suất hành động (với masking).
    Critic: Nhận observation → ước lượng giá trị trạng thái V(s).

    Cấu trúc:
        Observation (86) → SharedMLP → [Actor Head (3), Critic Head (1)]
    """

    def __init__(
        self,
        obs_dim: int = 86,
        action_dim: int = 3,
        hidden_dims: List[int] = None,
    ):
        super().__init__()

        self.use_pretrained = False
        self.project_pyg_data = None

        if hidden_dims is None:
            hidden_dims = [256, 128]

        # ── Backbone chung ────────────────────────────────────────
        layers = []
        in_dim = obs_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(in_dim, h_dim),
                nn.LayerNorm(h_dim),
                nn.ReLU(),
            ])
            in_dim = h_dim
        self.backbone = nn.Sequential(*layers)

        # ── Actor Head (Policy) ───────────────────────────────────
        self.actor = nn.Sequential(
            nn.Linear(hidden_dims[-1], hidden_dims[-1] // 2),
            nn.ReLU(),
            nn.Linear(hidden_dims[-1] // 2, action_dim),
        )

        # ── Critic Head (Value) ───────────────────────────────────
        self.critic = nn.Sequential(
            nn.Linear(hidden_dims[-1], hidden_dims[-1] // 2),
            nn.ReLU(),
            nn.Linear(hidden_dims[-1] // 2, 1),
        )

        # Khởi tạo trọng số theo orthogonal initialization
        self._init_weights()

    def setup_pretrained_encoder(self, device):
        """Khởi tạo và nạp trọng số đã tiền huấn luyện cho GAT + DAGNN."""
        if self.use_pretrained:
            from ai_pipeline.models.sequential_glpo_model import SequentialGLPOModel
            self.encoder_model = SequentialGLPOModel(feature_dim=72, gat_out_dim=32, dagnn_out_dim=32).to(device)

            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            gat_path = os.path.join(base_dir, 'checkpoints', 'gat_pretrained.pth')
            dagnn_path = os.path.join(base_dir, 'checkpoints', 'dagnn_pretrained.pth')

            from ai_pipeline.training.unsupervised_pretrainer import load_pretrained, load_pretrained_dagnn

            gat_loaded = False
            if os.path.exists(gat_path):
                gat_loaded = load_pretrained(self.encoder_model, filepath=gat_path, device=device.type)

            dagnn_loaded = False
            if os.path.exists(dagnn_path):
                dagnn_loaded = load_pretrained_dagnn(self.encoder_model, filepath=dagnn_path, device=device.type)

            if not gat_loaded and not dagnn_loaded:
                print("[WARNING] Pretrained GAT/DAGNN checkpoints khong tim thay. Khoi tao ngau nhien.")

    def _init_weights(self):
        """Orthogonal initialization (chuẩn PPO), bỏ qua encoder_model."""
        for name, module in self.named_modules():
            if 'encoder_model' in name:
                continue
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
                nn.init.constant_(module.bias, 0.0)

        # Actor head cuối: gain nhỏ để policy ban đầu gần uniform
        if hasattr(self, 'actor') and len(self.actor) > 2:
            nn.init.orthogonal_(self.actor[-1].weight, gain=0.01)
            nn.init.constant_(self.actor[-1].bias, 0.0)

        # Critic head cuối: gain = 1
        if hasattr(self, 'critic') and len(self.critic) > 2:
            nn.init.orthogonal_(self.critic[-1].weight, gain=1.0)
            nn.init.constant_(self.critic[-1].bias, 0.0)

    def forward(
        self,
        obs: torch.Tensor,
        action_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.distributions.Categorical, torch.Tensor]:
        """
        Forward pass.
        """
        if self.use_pretrained and hasattr(self, 'encoder_model') and self.project_pyg_data is not None:
            # obs: [B, 86]
            project_idx_batch = obs[:, 70].long()
            task_idx_batch = obs[:, 71].long()

            unique_p_indices = torch.unique(project_idx_batch)
            B = obs.size(0)
            device = obs.device
            task_embeddings = torch.zeros((B, 64), dtype=torch.float32, device=device)

            for p_idx in unique_p_indices:
                p_val = p_idx.item()
                if p_val < len(self.project_pyg_data):
                    pyg_data = self.project_pyg_data[p_val].to(device)

                    # Chạy mạng encoder (grad flows if un-frozen)
                    out = self.encoder_model(pyg_data)
                    gat_emb = out['node_embeddings']  # [N, 32]
                    dagnn_emb = out['h_dagnn']        # [N, 32]
                    combined_emb = torch.cat([gat_emb, dagnn_emb], dim=-1)  # [N, 64]

                    p_mask = (project_idx_batch == p_idx)
                    p_task_indices = task_idx_batch[p_mask]
                    task_embeddings[p_mask] = combined_emb[p_task_indices]

            # Lấy 8 đặc trưng cuối của task_features làm phần bù để đủ 72 chiều
            raw_feats_8 = obs[:, 64:72]

            # Xây dựng observation mới [B, 86]
            modified_obs = torch.cat([
                task_embeddings,  # [B, 64]
                raw_feats_8,      # [B, 8]
                obs[:, 72:],      # [B, 14] -> Context (6) + Project State (8)
            ], dim=-1)

            features = self.backbone(modified_obs)
        else:
            features = self.backbone(obs)

        # Actor: tính logits và áp dụng masking
        logits = self.actor(features)

        if action_mask is not None:
            # Đặt logits của hành động bị khóa = -inf
            logits = logits.masked_fill(~action_mask, float('-inf'))

        dist = torch.distributions.Categorical(logits=logits)

        # Critic
        value = self.critic(features)

        return dist, value

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        action_mask: Optional[torch.Tensor] = None,
        action: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Lấy hành động, log_prob, entropy, và value.
        """
        dist, value = self.forward(obs, action_mask)

        if action is None:
            action = dist.sample()

        log_prob = dist.log_prob(action)
        entropy = dist.entropy()

        return action, log_prob, entropy, value.squeeze(-1)


# ============================================================================
# BỘ NHỚ ROLLOUT BUFFER
# ============================================================================
class RolloutBuffer:
    """
    Bộ nhớ lưu trữ dữ liệu trải nghiệm (Rollout Buffer) cho PPO.

    Lưu trữ:
        - observations, actions, rewards, dones
        - log_probs, values
        - action_masks
        - advantages (GAE), returns

    Sau khi thu thập đủ n_steps, tính GAE rồi trả về mini-batches.
    """

    def __init__(self, n_steps: int, obs_dim: int, action_dim: int):
        self.n_steps = n_steps
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.reset()

    def reset(self):
        self.observations = []
        self.actions = []
        self.rewards = []
        self.dones = []
        self.log_probs = []
        self.values = []
        self.action_masks = []
        self.ptr = 0

    def add(
        self,
        obs: np.ndarray,
        action: int,
        reward: float,
        done: bool,
        log_prob: float,
        value: float,
        action_mask: np.ndarray,
    ):
        self.observations.append(obs)
        self.actions.append(action)
        self.rewards.append(reward)
        self.dones.append(done)
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.action_masks.append(action_mask)
        self.ptr += 1

    def is_full(self) -> bool:
        return self.ptr >= self.n_steps

    def compute_gae(
        self,
        last_value: float,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
    ):
        """Tính Generalized Advantage Estimation (GAE)."""
        rewards = np.array(self.rewards, dtype=np.float32)
        values = np.array(self.values, dtype=np.float32)
        dones = np.array(self.dones, dtype=np.float32)

        T = len(rewards)
        advantages = np.zeros(T, dtype=np.float32)
        last_gae = 0.0

        for t in reversed(range(T)):
            if t == T - 1:
                next_value = last_value
                next_non_terminal = 1.0 - dones[t]
            else:
                next_value = values[t + 1]
                next_non_terminal = 1.0 - dones[t]

            delta = rewards[t] + gamma * next_value * next_non_terminal - values[t]
            advantages[t] = last_gae = delta + gamma * gae_lambda * next_non_terminal * last_gae

        returns = advantages + values

        self.advantages = advantages
        self.returns = returns

    def get_batches(self, batch_size: int):
        """Sinh ra các mini-batch ngẫu nhiên từ buffer."""
        T = self.ptr
        indices = np.arange(T)
        np.random.shuffle(indices)

        obs_array = np.array(self.observations, dtype=np.float32)
        act_array = np.array(self.actions, dtype=np.int64)
        logp_array = np.array(self.log_probs, dtype=np.float32)
        mask_array = np.array(self.action_masks, dtype=bool)

        for start in range(0, T, batch_size):
            end = min(start + batch_size, T)
            batch_idx = indices[start:end]

            yield {
                'obs': torch.tensor(obs_array[batch_idx]),
                'actions': torch.tensor(act_array[batch_idx]),
                'log_probs': torch.tensor(logp_array[batch_idx]),
                'advantages': torch.tensor(self.advantages[batch_idx]),
                'returns': torch.tensor(self.returns[batch_idx]),
                'action_masks': torch.tensor(mask_array[batch_idx]),
            }


# ============================================================================
# HÀM TIỆN ÍCH: Flatten Dict Observation
# ============================================================================
def flatten_obs(
    obs_dict: Dict[str, np.ndarray],
    project_idx: int = 0,
    task_idx: int = 0,
    use_pretrained: bool = False,
    enable_relative_state: bool = False,
) -> np.ndarray:
    """Nối task_features (72) + task_context (6) + project_state (8) = 86."""
    task_features = obs_dict['task_features'].copy()
    task_context = obs_dict['task_context'].copy()
    project_state = obs_dict['project_state'].copy()

    if enable_relative_state:
        # Giới hạn tỷ lệ trong khoảng hợp lý
        task_context = np.clip(task_context, -10.0, 10.0)
        project_state = np.clip(project_state, -10.0, 10.0)

    if use_pretrained:
        # Lưu project_idx và task_idx tại index 70 và 71 của task_features
        task_features[70] = float(project_idx)
        task_features[71] = float(task_idx)

    return np.concatenate([
        task_features,
        task_context,
        project_state,
    ], dtype=np.float32)


# ============================================================================
# HÀM TIỆN ÍCH: Chuẩn hóa observation
# ============================================================================
class RunningMeanStd:
    """Running mean/std cho chuẩn hóa observation (z-score)."""

    def __init__(self, shape: Tuple[int, ...] = (), epsilon: float = 1e-8):
        self.mean = np.zeros(shape, dtype=np.float64)
        self.var = np.ones(shape, dtype=np.float64)
        self.count = epsilon

    def update(self, x: np.ndarray):
        batch_mean = np.mean(x, axis=0)
        batch_var = np.var(x, axis=0)
        batch_count = x.shape[0] if x.ndim > 1 else 1

        delta = batch_mean - self.mean
        total_count = self.count + batch_count

        self.mean += delta * batch_count / total_count
        m_a = self.var * self.count
        m_b = batch_var * batch_count
        M2 = m_a + m_b + np.square(delta) * self.count * batch_count / total_count
        self.var = M2 / total_count
        self.count = total_count

    def normalize(self, x: np.ndarray) -> np.ndarray:
        return (x - self.mean.astype(np.float32)) / (
            np.sqrt(self.var.astype(np.float32)) + 1e-8
        )


# ============================================================================
# PPO TRAINER
# ============================================================================
class PPOTrainer:
    """
    Bộ huấn luyện PPO cho LogisticsGymEnv.

    Đầu vào (Args):
        config (dict): Cấu hình huấn luyện (xem DEFAULT_PPO_CONFIG).
        processed_dir (str): Đường dẫn tới thư mục chứa dữ liệu dự án.
        save_dir (str): Đường dẫn lưu checkpoint và log.

    Phương thức chính:
        train(): Chạy toàn bộ quy trình huấn luyện PPO.
        evaluate(n_episodes): Đánh giá chính sách hiện tại.
        save(path): Lưu mô hình.
        load(path): Nạp mô hình.
    """

    def __init__(
        self,
        config: Optional[Dict] = None,
        processed_dir: Optional[str] = None,
        save_dir: Optional[str] = None,
    ):
        self.config = {**DEFAULT_PPO_CONFIG, **(config or {})}

        # Đường dẫn dữ liệu
        if processed_dir is None:
            processed_dir = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'processed'
            )
        self.processed_dir = os.path.abspath(processed_dir)

        if save_dir is None:
            save_dir = os.path.join(
                os.path.dirname(__file__), '..', 'checkpoints'
            )
        self.save_dir = os.path.abspath(save_dir)
        os.makedirs(self.save_dir, exist_ok=True)

        # Set random seeds
        seed = self.config.get('random_seed', 42)
        import random
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

        # ── Khởi tạo các thành phần ──
        self.device = torch.device('cpu')

        # Actor-Critic
        self.agent = ActorCritic(
            obs_dim=self.config['obs_dim'],
            action_dim=self.config['action_dim'],
            hidden_dims=self.config['hidden_dims'],
        ).to(self.device)

        # Optimizer
        self.optimizer = torch.optim.Adam(
            self.agent.parameters(),
            lr=self.config['lr'],
            eps=1e-5,
        )

        # Rollout Buffer
        self.buffer = RolloutBuffer(
            n_steps=self.config['n_steps'],
            obs_dim=self.config['obs_dim'],
            action_dim=self.config['action_dim'],
        )

        # Observation Normalizer
        self.obs_normalizer = RunningMeanStd(shape=(self.config['obs_dim'],))

        # ── Nạp danh sách dự án ──
        self._load_projects()

        # Cấu hình đặc trưng tỷ lệ cho môi trường
        for env in self.envs:
            env.enable_relative_state = self.config.get('enable_relative_state', False)

        # Setup pretrained encoder
        self.agent.use_pretrained = self.config.get('use_pretrained', False)
        if hasattr(self, 'dataset') and hasattr(self.dataset, 'graphs'):
            self.agent.project_pyg_data = [pg.data for pg in self.dataset.graphs]
        if self.agent.use_pretrained:
            self.agent.setup_pretrained_encoder(self.device)
            # Recreate optimizer to include encoder parameters
            self.optimizer = torch.optim.Adam(
                self.agent.parameters(),
                lr=self.config['lr'],
                eps=1e-5,
            )

        self.update_count = 0
        self.encoder_frozen = False

        # ── Logging ──
        self.training_log = {
            'episode_rewards': [],
            'episode_lengths': [],
            'episode_tgc': [],
            'episode_makespans': [],
            'episode_resource_utils': [],  # Thêm thông tin sử dụng tài nguyên
            'policy_losses': [],
            'value_losses': [],
            'entropy_losses': [],
            'approx_kl': [],
            'learning_rates': [],
        }
        self.global_step = 0
        self.episode_count = 0
        self.best_eval_reward = float('-inf')

    def _load_projects(self):
        """Nạp tất cả dự án từ thư mục processed."""
        from ai_pipeline.models.data_loader import GlPoDataset
        from ai_pipeline.envs.logistics_gym_env import create_env_from_project_graph

        print(f"📂 Nạp dự án từ: {self.processed_dir}")
        self.dataset = GlPoDataset(self.processed_dir)
        print(f"   Tìm thấy {len(self.dataset)} dự án.")

        # Tạo danh sách environments
        self.envs = []
        self.project_ids = []
        for pg in self.dataset.graphs:
            env = create_env_from_project_graph(
                pg,
                penalty_weight=self.config.get('penalty_weight', 1000.0),
                reward_scale=self.config.get('reward_scale', 10000.0)
            )
            self.envs.append(env)
            self.project_ids.append(pg.project_id)
            print(f"   ✅ {pg.project_id}: {pg.data.num_nodes} tasks, "
                  f"{pg.data.num_edges} edges")

        self.current_env_idx = 0

    def _get_current_env(self):
        """Lấy môi trường hiện tại."""
        return self.envs[self.current_env_idx]

    def _switch_project(self):
        """Chuyển sang dự án tiếp theo (round-robin)."""
        self.current_env_idx = (self.current_env_idx + 1) % len(self.envs)
        pid = self.project_ids[self.current_env_idx]
        return pid

    def train(self):
        """
        Chạy toàn bộ quy trình huấn luyện PPO.

        Luồng:
            1. Thu thập trải nghiệm (Rollout) trên môi trường.
            2. Tính GAE (Generalized Advantage Estimation).
            3. Cập nhật PPO (Clipped Surrogate Objective).
            4. Log kết quả và lưu checkpoint.
        """
        cfg = self.config
        total_timesteps = cfg['total_timesteps']

        print("\n" + "=" * 70)
        print("  BẮT ĐẦU HUẤN LUYỆN PPO AGENT")
        print("=" * 70)
        print(f"  Tổng timesteps: {total_timesteps:,}")
        print(f"  Số dự án: {len(self.envs)}")
        print(f"  n_steps: {cfg['n_steps']}")
        print(f"  batch_size: {cfg['batch_size']}")
        print(f"  clip_ratio: {cfg['clip_ratio']}")
        print(f"  lr: {cfg['lr']}")
        print(f"  freeze_epochs: {cfg.get('freeze_epochs', 20)}")
        print(f"  use_pretrained: {cfg.get('use_pretrained', False)}")
        print(f"  enable_domain_randomization: {cfg.get('enable_domain_randomization', False)}")
        print(f"  enable_relative_state: {cfg.get('enable_relative_state', False)}")
        print("=" * 70)

        t_start = time.time()

        use_pretrained = cfg.get('use_pretrained', False)
        enable_relative_state = cfg.get('enable_relative_state', False)
        enable_domain_randomization = cfg.get('enable_domain_randomization', False)

        # Reset môi trường ban đầu
        env = self._get_current_env()
        obs_dict, info = env.reset(options={'domain_randomization': False})

        # Áp dụng domain randomization đầu tiên
        if enable_domain_randomization:
            deadline_range = cfg.get('dr_deadline_range', 0.15)
            resource_range = cfg.get('dr_resource_range', 0.20)
            cost_range = cfg.get('dr_cost_range', 0.10)

            base_deadline = env._global_constraints.get('deadline', env._state['cpm_results']['makespan'] * 1.2)
            env.episode_constraints['deadline'] = base_deadline * np.random.uniform(1.0 - deadline_range, 1.0 + deadline_range)

            if env._resource_capacities:
                env._resource_capacities = {
                    k: v * np.random.uniform(1.0 - resource_range, 1.0 + resource_range)
                    for k, v in env._original_resource_capacities.items()
                }
            env.crash_cost_factor = env.crash_cost_factor * np.random.uniform(1.0 - cost_range, 1.0 + cost_range)
            env.outsource_cost_factor = env.outsource_cost_factor * np.random.uniform(1.0 - cost_range, 1.0 + cost_range)

        # Trích xuất project_idx và task_idx ban đầu
        pidx = self.current_env_idx
        topo_idx = env._state['current_topo_idx']
        tidx = env._topo_order[topo_idx] if topo_idx < len(env._topo_order) else 0

        obs_flat = flatten_obs(
            obs_dict,
            project_idx=pidx,
            task_idx=tidx,
            use_pretrained=use_pretrained,
            enable_relative_state=enable_relative_state
        )

        ep_reward = 0.0
        ep_length = 0
        ep_resource_utils = []

        while self.global_step < total_timesteps:
            # ── Thu thập Rollout ──────────────────────────────────
            self.buffer.reset()

            for _ in range(cfg['n_steps']):
                self.global_step += 1

                # Chuẩn hóa observation
                obs_norm = self.obs_normalizer.normalize(obs_flat)
                if use_pretrained:
                    # Ghi đè chỉ số không chuẩn hóa
                    obs_norm[70] = float(pidx)
                    obs_norm[71] = float(tidx)

                obs_tensor = torch.tensor(obs_norm, dtype=torch.float32).unsqueeze(0)

                # Lấy action mask
                mask = env.action_masks()
                mask_tensor = torch.tensor(mask, dtype=torch.bool).unsqueeze(0)

                # Chọn hành động
                with torch.no_grad():
                    action, log_prob, _, value = self.agent.get_action_and_value(
                        obs_tensor, mask_tensor
                    )

                action_int = action.item()
                log_prob_val = log_prob.item()
                value_val = value.item()

                # Thực thi hành động trên môi trường
                next_obs_dict, reward, terminated, truncated, info = env.step(action_int)
                done = terminated or truncated

                # Lưu vào buffer
                self.buffer.add(
                    obs=obs_norm,
                    action=action_int,
                    reward=reward,
                    done=done,
                    log_prob=log_prob_val,
                    value=value_val,
                    action_mask=mask,
                )

                # Cập nhật running statistics cho normalizer
                self.obs_normalizer.update(obs_flat.reshape(1, -1))

                ep_reward += reward
                ep_length += 1
                
                # Lưu thông tin tài nguyên tại bước hiện tại
                if 'project_state' in obs_dict and len(obs_dict['project_state']) > 4:
                    ep_resource_utils.append(float(obs_dict['project_state'][4]))
                else:
                    ep_resource_utils.append(0.0)

                if done:
                    # Ghi nhận kết quả episode
                    self.training_log['episode_rewards'].append(ep_reward)
                    self.training_log['episode_lengths'].append(ep_length)
                    self.training_log['episode_tgc'].append(info.get('cumulative_tgc', 0.0))
                    self.training_log['episode_makespans'].append(info.get('makespan', 0.0))

                    avg_res = np.mean(ep_resource_utils) if ep_resource_utils else 0.0
                    self.training_log['episode_resource_utils'].append(avg_res)
                    self.episode_count += 1
                    ep_resource_utils = []

                    # Logging
                    if self.episode_count % cfg['log_interval'] == 0:
                        self._print_progress(t_start)
                        self._save_ppo_metrics(t_start)

                    # Chuyển đổi dự án
                    if self.episode_count % cfg['project_switch_interval'] == 0:
                        pid = self._switch_project()
                        env = self._get_current_env()

                    # Evaluation
                    if self.episode_count % cfg['eval_interval'] == 0:
                        self._evaluate_and_save()

                    # Reset episode
                    obs_dict, info = env.reset(options={'domain_randomization': False})

                    if enable_domain_randomization:
                        deadline_range = cfg.get('dr_deadline_range', 0.15)
                        resource_range = cfg.get('dr_resource_range', 0.20)
                        cost_range = cfg.get('dr_cost_range', 0.10)

                        base_deadline = env._global_constraints.get('deadline', env._state['cpm_results']['makespan'] * 1.2)
                        env.episode_constraints['deadline'] = base_deadline * np.random.uniform(1.0 - deadline_range, 1.0 + deadline_range)

                        if env._resource_capacities:
                            env._resource_capacities = {
                                k: v * np.random.uniform(1.0 - resource_range, 1.0 + resource_range)
                                for k, v in env._original_resource_capacities.items()
                            }
                        env.crash_cost_factor = env.crash_cost_factor * np.random.uniform(1.0 - cost_range, 1.0 + cost_range)
                        env.outsource_cost_factor = env.outsource_cost_factor * np.random.uniform(1.0 - cost_range, 1.0 + cost_range)

                    pidx = self.current_env_idx
                    topo_idx = env._state['current_topo_idx']
                    tidx = env._topo_order[topo_idx] if topo_idx < len(env._topo_order) else 0

                    obs_flat = flatten_obs(
                        obs_dict,
                        project_idx=pidx,
                        task_idx=tidx,
                        use_pretrained=use_pretrained,
                        enable_relative_state=enable_relative_state
                    )
                    ep_reward = 0.0
                    ep_length = 0
                else:
                    obs_dict = next_obs_dict
                    topo_idx = env._state['current_topo_idx']
                    tidx = env._topo_order[topo_idx] if topo_idx < len(env._topo_order) else 0
                    obs_flat = flatten_obs(
                        obs_dict,
                        project_idx=pidx,
                        task_idx=tidx,
                        use_pretrained=use_pretrained,
                        enable_relative_state=enable_relative_state
                    )

                if self.global_step >= total_timesteps:
                    break

            # ── Tính GAE ──────────────────────────────────────────
            if not done:
                obs_norm = self.obs_normalizer.normalize(obs_flat)
                if use_pretrained:
                    obs_norm[70] = float(pidx)
                    obs_norm[71] = float(tidx)
                obs_tensor = torch.tensor(obs_norm, dtype=torch.float32).unsqueeze(0)
                with torch.no_grad():
                    _, _, _, last_value = self.agent.get_action_and_value(obs_tensor)
                last_val = last_value.item()
            else:
                last_val = 0.0

            self.buffer.compute_gae(last_val, cfg['gamma'], cfg['gae_lambda'])

            # ── Cập nhật PPO ──────────────────────────────────────
            self._update_ppo()

        # Kết thúc
        total_time = time.time() - t_start
        print("\n" + "=" * 70)
        print(f"  ✅ HUẤN LUYỆN HOÀN TẤT")
        print(f"  Tổng thời gian: {total_time:.1f}s")
        print(f"  Episodes: {self.episode_count}")
        print(f"  Timesteps: {self.global_step:,}")
        print("=" * 70)

        # Lưu mô hình cuối cùng
        self.save(os.path.join(self.save_dir, 'ppo_final.pt'))

        return self.training_log

    def _set_encoder_frozen(self, frozen: bool):
        """Đóng băng hoặc mở đóng băng các tham số GAT & DAGNN."""
        if not hasattr(self.agent, 'encoder_model'):
            return

        for param in self.agent.encoder_model.parameters():
            param.requires_grad = not frozen

        self.encoder_frozen = frozen

    def _update_ppo(self):
        """Cập nhật tham số mạng PPO bằng Clipped Surrogate Objective."""
        cfg = self.config

        # ── Kiểm tra Huấn luyện 2 Giai đoạn (Progressive Fine-tuning) ──
        freeze_epochs = cfg.get('freeze_epochs', 20)
        use_pretrained = cfg.get('use_pretrained', False)

        if use_pretrained and hasattr(self.agent, 'encoder_model'):
            if self.update_count < freeze_epochs:
                if not getattr(self, 'encoder_frozen', False):
                    self._set_encoder_frozen(True)
                    print(f"🔒 [PPO Trainer] Giai đoạn 1: Freeze Encoder ({self.update_count}/{freeze_epochs})")
            else:
                if getattr(self, 'encoder_frozen', True):
                    self._set_encoder_frozen(False)
                    print(f"🔓 [PPO Trainer] Giai đoạn 2: Unfreeze Encoder ({self.update_count})")

        # Chuẩn hóa advantages
        advantages_all = self.buffer.advantages
        adv_mean = advantages_all.mean()
        adv_std = advantages_all.std() + 1e-8

        total_pg_loss = 0.0
        total_v_loss = 0.0
        total_ent_loss = 0.0
        total_approx_kl = 0.0
        n_updates = 0

        for epoch in range(cfg['n_epochs']):
            for batch in self.buffer.get_batches(cfg['batch_size']):
                obs_b = batch['obs'].to(self.device)
                act_b = batch['actions'].to(self.device)
                old_logp_b = batch['log_probs'].to(self.device)
                adv_b = batch['advantages'].to(self.device)
                ret_b = batch['returns'].to(self.device)
                mask_b = batch['action_masks'].to(self.device)

                # Chuẩn hóa advantages trong batch
                adv_b = (adv_b - adv_b.mean()) / (adv_b.std() + 1e-8)

                # Forward
                _, new_logp, entropy, new_value = self.agent.get_action_and_value(
                    obs_b, mask_b, act_b
                )

                # ── Policy Loss (Clipped Surrogate) ───────────────
                log_ratio = new_logp - old_logp_b
                ratio = torch.exp(log_ratio)

                pg_loss1 = -adv_b * ratio
                pg_loss2 = -adv_b * torch.clamp(
                    ratio, 1.0 - cfg['clip_ratio'], 1.0 + cfg['clip_ratio']
                )
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()

                # ── Value Loss ────────────────────────────────────
                v_loss = F.mse_loss(new_value, ret_b)

                # ── Entropy Loss ──────────────────────────────────
                ent_loss = entropy.mean()

                # ── Total Loss ────────────────────────────────────
                loss = (
                    pg_loss
                    + cfg['value_coef'] * v_loss
                    - cfg['entropy_coef'] * ent_loss
                )

                # ── Backward & Step ───────────────────────────────
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(
                    self.agent.parameters(), cfg['max_grad_norm']
                )
                self.optimizer.step()

                # Tracking
                with torch.no_grad():
                    approx_kl = ((ratio - 1) - log_ratio).mean().item()

                total_pg_loss += pg_loss.item()
                total_v_loss += v_loss.item()
                total_ent_loss += ent_loss.item()
                total_approx_kl += approx_kl
                n_updates += 1

        # Ghi log
        if n_updates > 0:
            self.training_log['policy_losses'].append(total_pg_loss / n_updates)
            self.training_log['value_losses'].append(total_v_loss / n_updates)
            self.training_log['entropy_losses'].append(total_ent_loss / n_updates)
            self.training_log['approx_kl'].append(total_approx_kl / n_updates)
            self.training_log['learning_rates'].append(
                self.optimizer.param_groups[0]['lr']
            )

        self.update_count += 1

    def _print_progress(self, t_start: float):
        """In tiến độ huấn luyện."""
        log = self.training_log
        n = min(20, len(log['episode_rewards']))
        if n == 0:
            return

        recent_rewards = log['episode_rewards'][-n:]
        recent_tgc = log['episode_tgc'][-n:]
        recent_len = log['episode_lengths'][-n:]
        recent_makespan = log['episode_makespans'][-n:]

        elapsed = time.time() - t_start
        fps = self.global_step / max(elapsed, 1.0)

        pid = self.project_ids[self.current_env_idx]

        stage = 1 if getattr(self, 'encoder_frozen', False) else 2
        print(f"  📊 Ep {self.episode_count:5d} | "
              f"Step {self.global_step:>7,d} | "
              f"Reward: {np.mean(recent_rewards):>8.1f} ± {np.std(recent_rewards):>6.1f} | "
              f"TGC: {np.mean(recent_tgc):>8.1f} | "
              f"Makespan: {np.mean(recent_makespan):>7.1f}h | "
              f"Stage: {stage} | "
              f"Project: {pid} | "
              f"FPS: {fps:.0f}")

        if log['policy_losses']:
            print(f"       PG Loss: {log['policy_losses'][-1]:.4f} | "
                  f"V Loss: {log['value_losses'][-1]:.4f} | "
                  f"Entropy: {log['entropy_losses'][-1]:.4f} | "
                  f"KL: {log['approx_kl'][-1]:.4f}")

    def _save_ppo_metrics(self, t_start: float):
        """Ghi nhật ký huấn luyện PPO chi tiết."""
        cfg = self.config
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(base_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        metrics_file = os.path.join(logs_dir, 'ppo_training_metrics.json')

        metrics_history = []
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics_history = json.load(f)
            except Exception:
                metrics_history = []

        recent_n = min(cfg['log_interval'], len(self.training_log['episode_rewards']))
        recent_rewards = self.training_log['episode_rewards'][-recent_n:]
        recent_makespans = self.training_log['episode_makespans'][-recent_n:]
        recent_tgcs = self.training_log['episode_tgc'][-recent_n:]
        recent_res_utils = self.training_log.get('episode_resource_utils', [])[-recent_n:]

        entry = {
            'episode': self.episode_count,
            'global_step': self.global_step,
            'actor_loss': self.training_log['policy_losses'][-1] if self.training_log['policy_losses'] else 0.0,
            'critic_loss': self.training_log['value_losses'][-1] if self.training_log['value_losses'] else 0.0,
            'entropy': self.training_log['entropy_losses'][-1] if self.training_log['entropy_losses'] else 0.0,
            'average_reward': float(np.mean(recent_rewards)) if recent_rewards else 0.0,
            'average_makespan': float(np.mean(recent_makespans)) if recent_makespans else 0.0,
            'average_cost': float(np.mean(recent_tgcs)) if recent_tgcs else 0.0,
            'average_resource_utilization': float(np.mean(recent_res_utils)) if recent_res_utils else 0.0,
            'encoder_stage': 1 if getattr(self, 'encoder_frozen', False) else 2,
            'training_time': time.time() - t_start,
        }
        metrics_history.append(entry)

        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_history, f, indent=2, ensure_ascii=False)

    def _evaluate_and_save(self):
        """Đánh giá chính sách hiện tại trên tất cả dự án."""
        eval_results = self.evaluate(n_episodes=1)

        mean_reward = np.mean(eval_results['total_rewards'])
        print(f"\n  🎯 ĐÁNH GIÁ (Ep {self.episode_count}): "
              f"Reward TB = {mean_reward:.2f}")
        for i, pid in enumerate(eval_results['project_ids']):
            print(f"     {pid}: Reward={eval_results['total_rewards'][i]:.2f}, "
                  f"TGC={eval_results['total_tgc'][i]:.2f}, "
                  f"Makespan={eval_results['makespans'][i]:.1f}h")

        # Lưu best model
        if mean_reward > self.best_eval_reward:
            self.best_eval_reward = mean_reward
            self.save(os.path.join(self.save_dir, 'ppo_best.pt'))
            print(f"     💾 Lưu mô hình tốt nhất (Reward={mean_reward:.2f})")
        print()

    def evaluate(self, n_episodes: int = 1) -> Dict:
        """
        Đánh giá chính sách hiện tại.
        """
        self.agent.eval()
        results = {
            'project_ids': [],
            'total_rewards': [],
            'total_tgc': [],
            'makespans': [],
            'mode_distributions': [],
        }

        use_pretrained = self.config.get('use_pretrained', False)
        enable_relative_state = self.config.get('enable_relative_state', False)

        for env_idx, env in enumerate(self.envs):
            pid = self.project_ids[env_idx]

            for ep in range(n_episodes):
                obs_dict, info = env.reset(options={'domain_randomization': False})
                
                topo_idx = env._state['current_topo_idx']
                tidx = env._topo_order[topo_idx] if topo_idx < len(env._topo_order) else 0
                
                obs_flat = flatten_obs(
                    obs_dict,
                    project_idx=env_idx,
                    task_idx=tidx,
                    use_pretrained=use_pretrained,
                    enable_relative_state=enable_relative_state
                )
                total_reward = 0.0
                mode_counts = [0, 0, 0]
                done = False

                while not done:
                    obs_norm = self.obs_normalizer.normalize(obs_flat)
                    if use_pretrained:
                        obs_norm[70] = float(env_idx)
                        obs_norm[71] = float(tidx)

                    obs_tensor = torch.tensor(
                        obs_norm, dtype=torch.float32
                    ).unsqueeze(0)
                    mask = env.action_masks()
                    mask_tensor = torch.tensor(
                        mask, dtype=torch.bool
                    ).unsqueeze(0)

                    with torch.no_grad():
                        dist, _ = self.agent(obs_tensor, mask_tensor)
                        action = dist.probs.argmax(dim=-1).item()

                    obs_dict, reward, terminated, truncated, info = env.step(action)
                    total_reward += reward
                    mode_counts[action] += 1
                    done = terminated or truncated

                    if not done:
                        topo_idx = env._state['current_topo_idx']
                        tidx = env._topo_order[topo_idx] if topo_idx < len(env._topo_order) else 0
                        obs_flat = flatten_obs(
                            obs_dict,
                            project_idx=env_idx,
                            task_idx=tidx,
                            use_pretrained=use_pretrained,
                            enable_relative_state=enable_relative_state
                        )

                results['project_ids'].append(pid)
                results['total_rewards'].append(total_reward)
                results['total_tgc'].append(info.get('cumulative_tgc', 0.0))
                results['makespans'].append(info.get('makespan', 0.0))
                results['mode_distributions'].append(mode_counts)

        self.agent.train()
        return results

    def save(self, path: str):
        """Lưu checkpoint."""
        checkpoint = {
            'agent_state_dict': self.agent.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'global_step': self.global_step,
            'episode_count': self.episode_count,
            'best_eval_reward': self.best_eval_reward,
            'obs_normalizer': {
                'mean': self.obs_normalizer.mean,
                'var': self.obs_normalizer.var,
                'count': self.obs_normalizer.count,
            },
            # Bổ sung thông tin nâng cấp tiền huấn luyện
            'encoder_frozen': getattr(self, 'encoder_frozen', False),
            'encoder_unfrozen': not getattr(self, 'encoder_frozen', False),
            'training_stage': 1 if getattr(self, 'encoder_frozen', False) else 2,
            'learning_rate': self.optimizer.param_groups[0]['lr'],
            'episode': self.episode_count,
            'reward': np.mean(self.training_log['episode_rewards'][-10:]) if self.training_log['episode_rewards'] else 0.0,
            'best_reward': self.best_eval_reward,
            'update_count': getattr(self, 'update_count', 0),
        }
        torch.save(checkpoint, path)

    def load(self, path: str):
        """Nạp checkpoint."""
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.agent.load_state_dict(checkpoint['agent_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.global_step = checkpoint['global_step']
        self.episode_count = checkpoint['episode_count']
        self.best_eval_reward = checkpoint.get('best_eval_reward', float('-inf'))

        if 'obs_normalizer' in checkpoint:
            norm_data = checkpoint['obs_normalizer']
            self.obs_normalizer.mean = norm_data['mean']
            self.obs_normalizer.var = norm_data['var']
            self.obs_normalizer.count = norm_data['count']

        # Khôi phục trạng thái encoder frozen/unfrozen
        self.update_count = checkpoint.get('update_count', 0)
        self.encoder_frozen = checkpoint.get('encoder_frozen', False)
        self._set_encoder_frozen(self.encoder_frozen)

        print(f"✅ Nạp checkpoint từ {path}")
        print(f"   Step: {self.global_step}, Episode: {self.episode_count}, Stage: {1 if self.encoder_frozen else 2}")


# ============================================================================
# MAIN: Chạy huấn luyện PPO
# ============================================================================
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("  GIAI ĐOẠN 4: HUẤN LUYỆN PPO AGENT")
    print("=" * 70)

    # Cấu hình đã tinh chỉnh cho dataset 5 dự án nhỏ
    config = {
        # ── Kiến trúc ──
        'obs_dim': 86,
        'action_dim': 3,
        'hidden_dims': [256, 128],

        # ── PPO ──
        'lr': 3e-4,
        'gamma': 0.99,
        'gae_lambda': 0.95,
        'clip_ratio': 0.2,
        'entropy_coef': 0.02,       # Entropy cao hơn để khám phá nhiều hơn
        'value_coef': 0.5,
        'max_grad_norm': 0.5,
        'penalty_weight': 1000.0,   # Trị số 1000.0 kích hoạt dynamic scale
        'reward_scale': 1000.0,     # Trị số 1000.0 kích hoạt dynamic scale

        # ── Huấn luyện ──
        'total_timesteps': 50_000,
        'n_steps': 512,             # Rollout dài hơn cho dự án lớn
        'n_epochs': 4,
        'batch_size': 64,

        # ── Multi-project ──
        'project_switch_interval': 3,   # Chuyển dự án mỗi 3 episodes
        'pretrain_epochs': 30,

        # ── Logging ──
        'log_interval': 5,
        'save_interval': 50,
        'eval_interval': 25,
    }

    processed_dir = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'processed'
    )
    save_dir = os.path.join(
        os.path.dirname(__file__), '..', 'checkpoints'
    )

    trainer = PPOTrainer(
        config=config,
        processed_dir=processed_dir,
        save_dir=save_dir,
    )

    # Chạy huấn luyện
    training_log = trainer.train()

    # Đánh giá cuối cùng
    print("\n" + "=" * 70)
    print("  ĐÁNH GIÁ CUỐI CÙNG")
    print("=" * 70)

    eval_results = trainer.evaluate(n_episodes=3)

    for i, pid in enumerate(eval_results['project_ids']):
        modes = eval_results['mode_distributions'][i]
        total = sum(modes)
        pct = [f"{m/max(total,1)*100:.0f}%" for m in modes]
        print(f"  {pid}: Reward={eval_results['total_rewards'][i]:>8.2f} | "
              f"TGC={eval_results['total_tgc'][i]:>8.2f} | "
              f"Makespan={eval_results['makespans'][i]:>7.1f}h | "
              f"Modes: N={pct[0]} C={pct[1]} O={pct[2]}")

    print(f"\n  Reward trung bình: {np.mean(eval_results['total_rewards']):.2f}")
    print("=" * 70)

    # Lưu training log
    log_path = os.path.join(save_dir, 'training_log.json')
    serializable_log = {}
    for k, v in training_log.items():
        serializable_log[k] = [float(x) for x in v]
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_log, f, indent=2, ensure_ascii=False)
    print(f"\n  📄 Training log đã lưu tại: {log_path}")
