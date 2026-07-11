"""
Mô-đun LogisticsGymEnv: Môi trường Gymnasium cho PPO Agent
============================================================
Dự án: GLPO - Graph Logistics Project Optimization

Mô tả:
    Triển khai môi trường mô phỏng lập lịch dự án động tuân thủ chuẩn Gymnasium.
    PPO Agent sẽ tương tác với môi trường này để học chính sách lập lịch tối ưu.

    Mỗi Episode:
        1. Nạp một đồ thị dự án (PyG Data) từ GlPoDataset.
        2. Agent lần lượt chọn chế độ chạy (Normal / Crash / Outsource) cho từng task
           theo thứ tự tô-pô (Topological Order).
        3. Sau mỗi quyết định, môi trường tính toán CPM động, cập nhật tài nguyên,
           và trả về Reward = -TGC (từ compute_reward).
        4. Episode kết thúc khi tất cả task đã được gán chế độ chạy.

    Invalid Action Masking:
        Tích hợp sẵn cơ chế trả về mặt nạ hành động hợp lệ (action_masks()) để
        ngăn PPO Agent chọn các hành động vi phạm ràng buộc cứng (tài nguyên quá tải,
        task chưa đủ điều kiện tiên quyết, v.v.).

Luồng dữ liệu:
    GlPoDataset → LogisticsGymEnv.reset() → Observation
                  LogisticsGymEnv.step(action) → (obs, reward, terminated, truncated, info)
                  LogisticsGymEnv.action_masks() → np.ndarray (mask hành động hợp lệ)

Nguồn tham chiếu:
    - ai_pipeline/models/tgc_layer3.py (compute_reward, compute_tgc_numpy)
    - ai_pipeline/models/data_loader.py (GlPoDataset)
    - ai_pipeline/src/algorithms/cpm.py (CPM động)
    - docs/22-6/hierarchical_3level_evaluation.md
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from collections import defaultdict, deque
from typing import Optional, Dict, List, Tuple, Any
import copy


# ============================================================================
# HẰNG SỐ TOÀN CỤC
# ============================================================================

# Các chế độ chạy task (Action Space)
MODE_NORMAL = 0       # Chạy bình thường
MODE_CRASH = 1        # Tăng ca / Đẩy nhanh (Crash)
MODE_OUTSOURCE = 2    # Thuê ngoài (Outsource)
NUM_MODES = 3

# Hệ số thay đổi khi Crash / Outsource
CRASH_DURATION_FACTOR = 0.7     # Thời lượng giảm còn 70%
CRASH_COST_FACTOR = 1.5         # Chi phí tăng 150%

OUTSOURCE_DURATION_FACTOR = 0.5  # Thời lượng giảm còn 50%
OUTSOURCE_COST_FACTOR = 2.0      # Chi phí tăng 200%

# Số nhóm đặc trưng
NUM_GROUPS = 8

# Mapping chỉ số nhóm trong vector 34 chiều
GROUP_INDICES = {
    0:  list(range(0, 5)),      # Hub Time (0-4)
    1:  list(range(5, 11)),     # G1: Direct Costs (5-10)
    2:  list(range(11, 15)),    # G2: Indirect Costs (11-14)
    3:  list(range(15, 18)),    # G3: Contractual (15-17)
    4:  list(range(18, 22)),    # G4: Risk (18-21)
    5:  list(range(22, 27)),    # G5: Logistics (22-26)
    6:  list(range(27, 29)),    # G6: Time (27-28)
    7:  list(range(29, 34)),    # G7: AI Topology (29-33)
}


class LogisticsGymEnv(gym.Env):
    """
    Mô tả (Description):
        Môi trường Gymnasium mô phỏng quy trình lập lịch dự án logistics.
        PPO Agent ra quyết định tuần tự cho từng task theo thứ tự tô-pô.

    Đầu vào khởi tạo (Args):
        project_data (dict): Dữ liệu dự án đã được tiền xử lý, bao gồm:
            - 'features': np.ndarray [N, 72] — Vector đặc trưng thô.
            - 'edge_index': np.ndarray [2, E] — Bản đồ liên kết.
            - 'durations': np.ndarray [N] — Thời lượng cơ bản (giờ).
            - 'resource_demands': dict[int, dict[str, float]] — Nhu cầu tài nguyên.
            - 'resource_capacities': dict[str, float] — Giới hạn tài nguyên.
            - 'global_constraints': dict — Ràng buộc toàn cục (deadline, budget...).
        max_steps (int): Số bước tối đa trước khi truncate (mặc định = số task).

    Observation Space:
        Dict chứa:
            - 'task_features': Box [72] — Đặc trưng của task hiện tại.
            - 'task_context': Box [6] — Thông tin bối cảnh:
                [topo_position_ratio, num_predecessors, num_successors,
                 total_float, is_critical, resource_load_ratio]
            - 'project_state': Box [8] — Trạng thái toàn cục:
                [progress_ratio, cumulative_tgc_norm, makespan_norm,
                 budget_usage_ratio, resource_utilization,
                 num_completed, num_remaining, deadline_slack_ratio]

    Action Space:
        Discrete(3): {0: Normal, 1: Crash, 2: Outsource}
    """

    metadata = {"render_modes": ["human", "ansi"], "render_fps": 1}

    def __init__(
        self,
        project_data: Dict[str, Any],
        max_steps: Optional[int] = None,
        render_mode: Optional[str] = None,
        penalty_weight: float = 1000.0,
        reward_scale: float = 1000.0,
        domain_randomization: bool = True,
    ):
        super(LogisticsGymEnv, self).__init__()
        self.domain_randomization = domain_randomization

        # ── Lưu trữ dữ liệu dự án gốc (không thay đổi) ──────────
        self._original_features = np.array(project_data['features'], dtype=np.float32)
        self._edge_index = np.array(project_data['edge_index'], dtype=np.int64)
        self._edge_attr = np.array(project_data.get('edge_attr', [])) if project_data.get('edge_attr') is not None else None
        self._base_durations = np.array(project_data['durations'], dtype=np.float32)
        self._resource_demands = project_data.get('resource_demands', {})
        self._resource_capacities = project_data.get('resource_capacities', {})
        self._global_constraints = copy.deepcopy(project_data.get('global_constraints', {}))

        # RMS phục vụ chuẩn hóa đặc trưng quan sát đầu vào (giới hạn tối thiểu 1.0 để tránh chia cho số siêu nhỏ)
        self._rms = np.sqrt(np.mean(self._original_features**2, axis=0, keepdims=True))
        self._rms = np.maximum(self._rms, 1.0)

        # Chuẩn hóa các ràng buộc dự án dựa trên tỷ lệ chuẩn hóa RMS để khớp với đầu vào
        cost_rms = self._rms[0, 5:11].mean()
        if 'total_budget' in self._global_constraints:
            self._global_constraints['total_budget'] /= cost_rms
            
        if 'carbon_cap' in self._global_constraints and self._global_constraints['carbon_cap'] != float('inf'):
            pass # V34 schema doesn't have an explicit carbon footprint feature, skip scaling

        # Đặt các tham số PPO trên thang đo chuẩn hóa mới
        self.reward_scale = 1.0       # Đồ thị đã chuẩn hóa nên không cần chia thêm
        self.penalty_weight = 100.0   # Mức phạt 100.0 điểm trên thang điểm [-10, 0] là rất lớn và đủ răn đe

        self.num_tasks = self._original_features.shape[0]
        self.max_steps = max_steps or self.num_tasks
        self.render_mode = render_mode

        # ── Xây dựng cấu trúc đồ thị ─────────────────────────────
        self._build_graph_structure()

        self.feature_dim = self._original_features.shape[1]
        self.project_type = project_data.get('project_type', 'logistics_standard')

        # ── Định nghĩa Observation Space ──────────────────────────
        self.observation_space = spaces.Dict({
            'task_features': spaces.Box(
                low=-np.inf, high=np.inf, shape=(self.feature_dim,), dtype=np.float32,
            ),
            'task_context': spaces.Box(
                low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32,
            ),
            'project_state': spaces.Box(
                low=-np.inf, high=np.inf, shape=(8,), dtype=np.float32,
            ),
        })

        # ── Định nghĩa Action Space ──────────────────────────────
        self.action_space = spaces.Discrete(NUM_MODES)

        # ── Khởi tạo trạng thái (sẽ được reset) ──────────────────
        self._state = None

    def _build_graph_structure(self):
        """Xây dựng danh sách kề, predecessors, thứ tự tô-pô từ edge_index."""
        self._adj_forward = defaultdict(list)
        self._adj_backward = defaultdict(list)
        self._in_degree = defaultdict(int)
        self._out_degree = defaultdict(int)

        if self._edge_index.size > 0:
            for i in range(self._edge_index.shape[1]):
                src = int(self._edge_index[0, i])
                dst = int(self._edge_index[1, i])
                self._adj_forward[src].append((dst, i))
                self._adj_backward[dst].append((src, i))
                self._out_degree[src] += 1
                self._in_degree[dst] += 1

        # Tính thứ tự tô-pô (Kahn's Algorithm)
        self._topo_order = self._compute_topo_order()

    def _compute_topo_order(self) -> List[int]:
        """Sắp xếp tô-pô bằng thuật toán Kahn."""
        in_deg = dict(self._in_degree)
        queue = deque()
        for i in range(self.num_tasks):
            if in_deg.get(i, 0) == 0:
                queue.append(i)

        order = []
        while queue:
            u = queue.popleft()
            order.append(u)
            for v, _ in self._adj_forward[u]:
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    queue.append(v)

        # Bổ sung nút cô lập
        visited = set(order)
        for i in range(self.num_tasks):
            if i not in visited:
                order.append(i)

        return order

    def _run_cpm_dynamic(self, durations: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Chạy CPM động trên thời lượng hiện tại.

        Returns:
            Dict chứa: 'ES', 'EF', 'LS', 'LF', 'total_float', 'is_critical', 'makespan'.
        """
        N = self.num_tasks
        ES = np.zeros(N, dtype=np.float32)
        EF = np.zeros(N, dtype=np.float32)

        # Forward Pass
        for u in self._topo_order:
            EF[u] = ES[u] + durations[u]
            for v, edge_idx in self._adj_forward[u]:
                # Xử lý Link Type và Lag
                if self._edge_attr is not None:
                    attr = self._edge_attr[edge_idx]
                    is_fs, is_ss, is_ff, is_sf = attr[0], attr[1], attr[2], attr[3]
                    # lag in hours (chỉ số 7)
                    lag_h = attr[7]
                else:
                    is_fs, is_ss, is_ff, is_sf, lag_h = 1.0, 0.0, 0.0, 0.0, 0.0

                if is_ss > 0.5:
                    ES[v] = max(ES[v], ES[u] + lag_h)
                elif is_ff > 0.5:
                    # FF -> EF[v] >= EF[u] + lag -> ES[v] >= EF[u] + lag - durations[v]
                    ES[v] = max(ES[v], EF[u] + lag_h - durations[v])
                elif is_sf > 0.5:
                    # SF -> EF[v] >= ES[u] + lag -> ES[v] >= ES[u] + lag - durations[v]
                    ES[v] = max(ES[v], ES[u] + lag_h - durations[v])
                else: # Mặc định là FS
                    ES[v] = max(ES[v], EF[u] + lag_h)

        # Backward Pass
        makespan = float(np.max(EF)) if N > 0 else 0.0
        LF = np.full(N, makespan, dtype=np.float32)
        LS = np.zeros(N, dtype=np.float32)

        for u in reversed(self._topo_order):
            LS[u] = LF[u] - durations[u]
            for p, edge_idx in self._adj_backward[u]:
                if self._edge_attr is not None:
                    attr = self._edge_attr[edge_idx]
                    is_fs, is_ss, is_ff, is_sf = attr[0], attr[1], attr[2], attr[3]
                    lag_h = attr[7]
                else:
                    is_fs, is_ss, is_ff, is_sf, lag_h = 1.0, 0.0, 0.0, 0.0, 0.0

                if is_ss > 0.5:
                    # SS -> ES[u] >= ES[p] + lag -> ES[p] <= ES[u] - lag -> LS[p] <= LS[u] - lag -> LF[p] <= LS[u] - lag + durations[p]
                    LF[p] = min(LF[p], LS[u] - lag_h + durations[p])
                elif is_ff > 0.5:
                    # FF -> EF[u] >= EF[p] + lag -> LF[p] <= LF[u] - lag
                    LF[p] = min(LF[p], LF[u] - lag_h)
                elif is_sf > 0.5:
                    # SF -> EF[u] >= ES[p] + lag -> LS[p] <= LF[u] - lag -> LF[p] <= LF[u] - lag + durations[p]
                    LF[p] = min(LF[p], LF[u] - lag_h + durations[p])
                else: # FS
                    # FS -> ES[u] >= EF[p] + lag -> LF[p] <= LS[u] - lag
                    LF[p] = min(LF[p], LS[u] - lag_h)

        total_float = LS - ES
        is_critical = (np.abs(total_float) < 1e-6).astype(np.float32)

        return {
            'ES': ES, 'EF': EF, 'LS': LS, 'LF': LF,
            'total_float': total_float,
            'is_critical': is_critical,
            'makespan': makespan,
        }

    def _compute_S_prime_g(self, features_34: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Tính S'_g (phiên bản NumPy thuần) bằng trung bình có trọng số theo nhóm.
        Đây là phiên bản Backup (không cần Neural Network).
        """
        # Chuẩn hóa đặc trưng bằng RMS để khớp với mạng nơ-ron
        features_34_norm = features_34 / self._rms[0]

        S_g = np.zeros(NUM_GROUPS, dtype=np.float32)
        group_masks = np.zeros(NUM_GROUPS, dtype=np.float32)

        for g_id, indices in GROUP_INDICES.items():
            if len(indices) == 0:
                continue
            vals = features_34_norm[indices]
            if np.any(np.abs(vals) > 0):
                group_masks[g_id] = 1.0
                S_g[g_id] = np.mean(vals)

        # Áp dụng masking
        S_prime_g = S_g * group_masks
        return S_prime_g, group_masks

    def _get_resource_usage_at_time(self, time_point: float) -> Dict[str, float]:
        """Tính tổng tài nguyên đang sử dụng tại một thời điểm."""
        usage = defaultdict(float)
        state = self._state

        for task_idx in range(self.num_tasks):
            if state['completed'][task_idx]:
                es = state['cpm_results']['ES'][task_idx]
                ef = state['cpm_results']['EF'][task_idx]
                if es <= time_point < ef:
                    # Nếu thuê ngoài, không tiêu thụ tài nguyên nội bộ
                    if state['modes'][task_idx] == MODE_OUTSOURCE:
                        continue
                    demands = self._resource_demands.get(task_idx, {})
                    for res_id, qty in demands.items():
                        usage[res_id] += qty

        return dict(usage)

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict] = None,
    ) -> Tuple[Dict[str, np.ndarray], Dict]:
        """
        Khởi tạo lại môi trường cho một episode mới.

        Returns:
            observation: Dict chứa observation ban đầu.
            info: Dict chứa thông tin bổ sung.
        """
        super().reset(seed=seed)

        # Khôi phục trạng thái gốc (nếu đã bị thay đổi bởi domain randomization bên ngoài)
        if hasattr(self, '_original_resource_capacities'):
            self._resource_capacities = copy.deepcopy(self._original_resource_capacities)
        else:
            self._original_resource_capacities = copy.deepcopy(self._resource_capacities)

        self.crash_cost_factor = CRASH_COST_FACTOR
        self.outsource_cost_factor = OUTSOURCE_COST_FACTOR

        # Quyết định chạy domain randomization cho episode này
        active_dr = self.domain_randomization
        if options is not None and 'domain_randomization' in options:
            active_dr = options['domain_randomization']

        # Sao chép ràng buộc vĩ mô cho episode
        self.episode_constraints = copy.deepcopy(self._global_constraints)

        # Khởi tạo trạng thái nội bộ
        self._state = {
            # Dữ liệu có thể thay đổi
            'features': self._original_features.copy(),
            'durations': self._base_durations.copy(),

            # Trạng thái lập lịch
            'modes': np.full(self.num_tasks, -1, dtype=np.int32),  # -1 = chưa gán
            'completed': np.zeros(self.num_tasks, dtype=bool),

            # Con trỏ topo
            'current_topo_idx': 0,

            # Theo dõi tích lũy
            'cumulative_tgc': 0.0,
            'cumulative_env_impact': 0.0,
            'cumulative_ev': 0.0,
            'cumulative_pv': 0.0,
            'step_count': 0,

            # Kết quả CPM (sẽ được tính ngay)
            'cpm_results': None,

            # Lịch sử hành động
            'action_history': [],
            'reward_history': [],
        }

        # Chạy CPM ban đầu với thời lượng gốc
        self._state['cpm_results'] = self._run_cpm_dynamic(self._state['durations'])

        if active_dr:
            # Ngẫu nhiên hóa deadline quanh baseline makespan của dự án (1.0x - 1.4x)
            baseline_makespan = self._state['cpm_results']['makespan']
            if seed is not None:
                np.random.seed(seed)
            self.episode_constraints['deadline'] = baseline_makespan * np.random.uniform(1.0, 1.4)
            
            # Ngẫu nhiên hóa budget (nếu có cấu hình > 0.0)
            base_budget = self._global_constraints.get('total_budget', 0.0)
            if base_budget > 0.0:
                self.episode_constraints['total_budget'] = base_budget * np.random.uniform(0.8, 1.2)

        obs = self._get_observation()
        info = self._get_info()

        return obs, info

    def step(
        self,
        action: int,
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict]:
        """
        Thực hiện một bước hành động: gán chế độ chạy cho task hiện tại.

        Args:
            action (int): Chế độ chạy {0: Normal, 1: Crash, 2: Outsource}.

        Returns:
            observation, reward, terminated, truncated, info
        """
        state = self._state
        topo_idx = state['current_topo_idx']
        task_idx = self._topo_order[topo_idx]

        # ── 1. Áp dụng hành động ─────────────────────────────────
        state['modes'][task_idx] = action
        old_duration = self._base_durations[task_idx]

        if action == MODE_NORMAL:
            new_duration = old_duration
            cost_multiplier = 1.0
        elif action == MODE_CRASH:
            new_duration = old_duration * CRASH_DURATION_FACTOR
            cost_multiplier = getattr(self, 'crash_cost_factor', CRASH_COST_FACTOR)
        elif action == MODE_OUTSOURCE:
            new_duration = old_duration * OUTSOURCE_DURATION_FACTOR
            cost_multiplier = getattr(self, 'outsource_cost_factor', OUTSOURCE_COST_FACTOR)
        else:
            new_duration = old_duration
            cost_multiplier = 1.0

        # Cập nhật thời lượng thực tế
        state['durations'][task_idx] = new_duration

        # Cập nhật vector đặc trưng 72-chiều (phản ánh quyết định)
        features = state['features'][task_idx]

        # Cập nhật chi phí trực tiếp G1 (index 5-10): nhân với hệ số chi phí
        for fi in range(5, 11):
            features[fi] *= cost_multiplier

        # Cập nhật chi phí thuê ngoài G1 (index 10) nếu Outsource
        if action == MODE_OUTSOURCE:
            base_cost = features[5:11].sum()
            features[10] += max(old_duration * 50.0, base_cost * 2.0)  # Hình phạt nặng nếu ép Outsource

        # Cập nhật Hub duration (index 0-3)
        duration_ratio = new_duration / max(old_duration, 1e-6)
        for fi in range(0, 4):
            features[fi] *= duration_ratio

        state['features'][task_idx] = features

        # Đánh dấu task hoàn thành
        state['completed'][task_idx] = True

        # ── 2. Chạy CPM động ─────────────────────────────────────
        state['cpm_results'] = self._run_cpm_dynamic(state['durations'])

        # Cập nhật G8 (Network Topology) cho tất cả task
        cpm = state['cpm_results']
        for i in range(self.num_tasks):
            state['features'][i, 31] = cpm['is_critical'][i]
            state['features'][i, 32] = cpm['total_float'][i]

        # ── 3. Tính Reward ────────────────────────────────────────
        S_prime_g, group_masks = self._compute_S_prime_g(state['features'][task_idx])

        schedule_info = {
            'finish_time': cpm['makespan'],
            'active_resource_usage': self._get_resource_usage_at_time(
                cpm['ES'][task_idx]
            ),
        }

        project_constraints = {
            **self.episode_constraints,
            'resource_capacities': self._resource_capacities,
            'cumulative_tgc': state['cumulative_tgc'],
            'cumulative_env_impact': state['cumulative_env_impact'],
            'cumulative_ev': state['cumulative_ev'],
            'cumulative_pv': state['cumulative_pv'],
        }

        # Import hàm compute_reward (lazy import để tránh circular dependency)
        try:
            from ai_pipeline.models.tgc_layer3 import compute_reward
        except ImportError:
            import sys, os
            models_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), '..', 'models'
            )
            if models_dir not in sys.path:
                sys.path.insert(0, os.path.abspath(models_dir))
            from ai_pipeline.models.tgc_layer3 import compute_reward

        reward_info = compute_reward(
            S_prime_g=S_prime_g,
            group_masks=group_masks,
            raw_features=state['features'][task_idx],
            schedule_info=schedule_info,
            project_constraints=project_constraints,
            penalty_weight=self.penalty_weight,
        )

        reward = float(reward_info['reward']) / self.reward_scale

        # Update environmental impact if available
        # In 34D schema, index for environmental impact is absent, so we just add 0
        state['cumulative_env_impact'] += 0.0

        # ── 4. Tiến tới task tiếp theo ────────────────────────────
        state['current_topo_idx'] += 1
        state['step_count'] += 1
        state['action_history'].append((task_idx, action))
        state['reward_history'].append(reward)

        # ── 5. Kiểm tra kết thúc ─────────────────────────────────
        terminated = state['current_topo_idx'] >= len(self._topo_order)
        truncated = state['step_count'] >= self.max_steps

        # Bonus/Penalty cuối episode
        if terminated:
            # Bonus nếu hoàn thành trước deadline
            deadline = self.episode_constraints.get('deadline', float('inf'))
            if cpm['makespan'] <= deadline:
                slack = (deadline - cpm['makespan']) / max(deadline, 1.0)
                reward += 100.0 * slack  # Thưởng tỷ lệ với thời gian dự phòng

        obs = self._get_observation() if not terminated else self._get_terminal_obs()
        info = self._get_info()
        info['reward_breakdown'] = reward_info

        return obs, reward, terminated, truncated, info

    def action_masks(self) -> np.ndarray:
        """
        Trả về mặt nạ hành động hợp lệ (Invalid Action Masking).

        Returns:
            mask (np.ndarray): Array boolean [NUM_MODES].
                mask[i] = True nếu hành động i hợp lệ, False nếu bị khóa.

        Logic khóa hành động:
            - MODE_NORMAL (0): Luôn hợp lệ.
            - MODE_CRASH (1): Khóa nếu:
                ① Task không có dữ liệu chi phí overtime (overtime_crashing_cost = 0).
                ② Crash sẽ gây quá tải tài nguyên không thể khắc phục.
            - MODE_OUTSOURCE (2): Khóa nếu:
                ① Task không có dữ liệu chi phí subcontracting (subcontracting_cost = 0).
                ② Outsource sẽ vượt ngân sách dự án.
        """
        state = self._state
        if state is None or state['current_topo_idx'] >= len(self._topo_order):
            return np.ones(NUM_MODES, dtype=bool)

        task_idx = self._topo_order[state['current_topo_idx']]
        features = state['features'][task_idx]

        mask = np.ones(NUM_MODES, dtype=bool)  # Mặc định: tất cả hợp lệ

        # ── Kiểm tra MODE_CRASH (1) ──────────────────────────────
        overtime_cost = float(features[9])  # overtime_crashing_cost (index 9)
        if overtime_cost <= 0:
            # Không có dữ liệu chi phí crash → Không cho phép crash
            mask[MODE_CRASH] = False

        # Kiểm tra tài nguyên: Crash không giảm nhu cầu tài nguyên
        # nhưng thời lượng ngắn hơn có thể gây xung đột tài nguyên tạm thời
        crash_duration = self._base_durations[task_idx] * CRASH_DURATION_FACTOR
        if crash_duration < 1e-6:
            mask[MODE_CRASH] = False

        # ── Kiểm tra MODE_OUTSOURCE (2) ──────────────────────────
        subcontracting_cost = float(features[8])  # subcontracting_cost (index 8)
        outsourcing_cost_val = float(features[10]) # outsourcing_cost (index 10)
        
        # Outsource luôn có chi phí cao → chỉ cho phép nếu có cơ sở dữ liệu về thuê ngoài
        if subcontracting_cost <= 0 and outsourcing_cost_val <= 0:
            mask[MODE_OUTSOURCE] = False

        # Kiểm tra ngân sách: Outsource sẽ tăng chi phí 2x
        total_budget = self.episode_constraints.get('total_budget', float('inf'))
        estimated_outsource_tgc = state['cumulative_tgc'] + max(subcontracting_cost, outsourcing_cost_val) * OUTSOURCE_COST_FACTOR
        if estimated_outsource_tgc > total_budget * 1.5:
            mask[MODE_OUTSOURCE] = False

        return mask

    def _get_observation(self) -> Dict[str, np.ndarray]:
        """Xây dựng observation cho task hiện tại (Abstract State Space)."""
        state = self._state

        if state['current_topo_idx'] >= len(self._topo_order):
            return self._get_terminal_obs()

        task_idx = self._topo_order[state['current_topo_idx']]
        cpm = state['cpm_results']

        # 1. Task Features (34 chiều) - đã được chuẩn hóa qua RMS
        task_features = (state['features'][task_idx] / self._rms[0]).copy()

        # 2. Task Context (6 chiều) - Quy chuẩn hóa hoàn toàn (Abstract State)
        topo_position = state['current_topo_idx'] / max(len(self._topo_order) - 1, 1)
        num_preds = len(self._adj_backward.get(task_idx, []))
        num_succs = len(self._adj_forward.get(task_idx, []))
        
        num_preds_ratio = num_preds / max(self.num_tasks, 1)
        num_succs_ratio = num_succs / max(self.num_tasks, 1)
        
        makespan = cpm['makespan']
        total_float = float(cpm['total_float'][task_idx])
        total_float_ratio = total_float / max(makespan, 1e-6)
        
        is_critical = float(cpm['is_critical'][task_idx])

        # Tỷ lệ tải tài nguyên
        demands = self._resource_demands.get(task_idx, {})
        if demands and self._resource_capacities:
            load_ratios = []
            for res_id, qty in demands.items():
                cap = self._resource_capacities.get(res_id, float('inf'))
                load_ratios.append(qty / max(cap, 1e-6))
            resource_load = np.mean(load_ratios) if load_ratios else 0.0
        else:
            resource_load = 0.0

        task_context = np.array([
            topo_position, num_preds_ratio, num_succs_ratio,
            total_float_ratio, is_critical, resource_load,
        ], dtype=np.float32)

        # 3. Project State (8 chiều) - Quy chuẩn hóa hoàn toàn (Abstract State)
        num_completed = int(np.sum(state['completed']))
        num_remaining = self.num_tasks - num_completed
        progress = num_completed / max(self.num_tasks, 1)
        deadline = self.episode_constraints.get('deadline', makespan * 2)
        budget = self.episode_constraints.get('total_budget', state['cumulative_tgc'] * 2 + 1)

        # Tính tỷ lệ sử dụng tài nguyên trung bình
        if self._resource_capacities:
            current_usage = self._get_resource_usage_at_time(
                cpm['ES'][task_idx] if task_idx < len(cpm['ES']) else 0.0
            )
            util_ratios = []
            for res_id, cap in self._resource_capacities.items():
                usage = current_usage.get(res_id, 0.0)
                util_ratios.append(usage / max(cap, 1e-6))
            resource_util = np.mean(util_ratios) if util_ratios else 0.0
        else:
            resource_util = 0.0

        deadline_slack = (deadline - makespan) / max(deadline, 1e-6)
        completed_ratio = float(num_completed) / max(self.num_tasks, 1)
        remaining_ratio = float(num_remaining) / max(self.num_tasks, 1)

        # Relative State Encoding
        if getattr(self, 'enable_relative_state', False):
            uncompleted_mask = ~state['completed']
            remaining_duration = float(np.sum(state['durations'][uncompleted_mask]))
            total_duration = float(np.sum(self._base_durations))
            remaining_duration_ratio = remaining_duration / max(total_duration, 1e-6)
            
            project_state = np.array([
                progress,
                state['cumulative_tgc'] / max(budget, 1e-6),
                makespan / max(deadline, 1e-6),
                remaining_duration_ratio,  # Replaces duplicate cumulative_tgc ratio
                resource_util,
                completed_ratio,
                remaining_ratio,
                deadline_slack,
            ], dtype=np.float32)
        else:
            project_state = np.array([
                progress,
                state['cumulative_tgc'] / max(budget, 1e-6),
                makespan / max(deadline, 1e-6),
                state['cumulative_tgc'] / max(budget, 1e-6),
                resource_util,
                completed_ratio,
                remaining_ratio,
                deadline_slack,
            ], dtype=np.float32)

        return {
            'task_features': task_features,
            'task_context': task_context,
            'project_state': project_state,
        }

    def _get_terminal_obs(self) -> Dict[str, np.ndarray]:
        """Observation khi episode kết thúc (padding zeros)."""
        return {
            'task_features': np.zeros(self.feature_dim, dtype=np.float32),
            'task_context': np.zeros(6, dtype=np.float32),
            'project_state': np.zeros(8, dtype=np.float32),
        }

    def _get_info(self) -> Dict[str, Any]:
        """Thông tin bổ sung cho mỗi step."""
        state = self._state
        cpm = state['cpm_results']

        return {
            'step': state['step_count'],
            'current_topo_idx': state['current_topo_idx'],
            'num_completed': int(np.sum(state['completed'])),
            'num_remaining': self.num_tasks - int(np.sum(state['completed'])),
            'cumulative_tgc': state['cumulative_tgc'],
            'makespan': cpm['makespan'],
            'num_critical_tasks': int(np.sum(cpm['is_critical'])),
            'modes_assigned': state['modes'].tolist(),
        }

    def render(self):
        """Hiển thị trạng thái hiện tại (chế độ ANSI)."""
        if self.render_mode != "ansi":
            return

        state = self._state
        cpm = state['cpm_results']

        lines = []
        lines.append("=" * 60)
        lines.append(f"  LOGISTICS GYM ENV — Step {state['step_count']}/{self.max_steps}")
        lines.append("=" * 60)
        lines.append(f"  Tiến độ: {int(np.sum(state['completed']))}/{self.num_tasks} tasks")
        lines.append(f"  TGC tích lũy: {state['cumulative_tgc']:.2f}")
        lines.append(f"  Makespan: {cpm['makespan']:.1f}h")
        lines.append(f"  Đường găng: {int(np.sum(cpm['is_critical']))} tasks")

        if state['current_topo_idx'] < len(self._topo_order):
            task_idx = self._topo_order[state['current_topo_idx']]
            mask = self.action_masks()
            lines.append(f"\n  Task tiếp theo: #{task_idx}")
            lines.append(f"  Action mask: Normal={mask[0]}, Crash={mask[1]}, Outsource={mask[2]}")

        lines.append("=" * 60)
        output = "\n".join(lines)
        print(output)
        return output


# ============================================================================
# HÀM TIỆN ÍCH: Tạo project_data từ GlPoProjectGraph
# ============================================================================
def create_env_from_project_graph(project_graph, global_constraints=None, penalty_weight=1000.0, reward_scale=1000.0, domain_randomization=True, resource_demands=None, resource_capacities=None, hours_per_day=8.0, days_per_week=5.0):
    """
    Tạo LogisticsGymEnv từ đối tượng GlPoProjectGraph.
    """
    data = project_graph.data
    features = data.x.cpu().numpy()
    edge_index = data.edge_index.cpu().numpy()

    # Tính thời lượng từ vector 34-chiều (Hub: index 0-3)
    N = features.shape[0]
    durations = np.zeros(N)
    for i in range(N):
        d_m = float(features[i, 0])  # duration_months
        d_w = float(features[i, 1])  # duration_weeks
        d_d = float(features[i, 2])  # duration_days
        d_h = float(features[i, 3])  # duration_hours
        is_24_7 = float(features[i, 4])  # calendar_type 24/7
        
        # Nếu data.u có tensor thì ưu tiên dùng, nếu không thì dùng tham số truyền vào
        if hasattr(data, 'u') and data.u is not None and data.u.size(0) > 0 and data.u.size(1) >= 2:
            u_tensor = data.u.cpu().numpy()[0]
            env_hours_per_day = float(u_tensor[0])
            env_days_per_week = float(u_tensor[1])
        else:
            env_hours_per_day = hours_per_day
            env_days_per_week = days_per_week

        if is_24_7 > 0.5:
            total_h = d_m * 30 * 24 + d_w * 7 * 24 + d_d * 24 + d_h
        else:
            total_h = (d_m * 4 * env_days_per_week * env_hours_per_day
                       + d_w * env_days_per_week * env_hours_per_day
                       + d_d * env_hours_per_day + d_h)
        durations[i] = total_h

    if resource_demands is None:
        resource_demands = {}
    if resource_capacities is None:
        resource_capacities = {}

    # Ràng buộc mặc định nếu không cung cấp
    if global_constraints is None:
        # Chạy CPM để tìm makespan baseline
        from collections import deque
        adj_fwd = defaultdict(list)
        if edge_index.size > 0:
            for j in range(edge_index.shape[1]):
                adj_fwd[int(edge_index[0, j])].append(int(edge_index[1, j]))

        ES = np.zeros(N)
        in_deg = defaultdict(int)
        for j in range(edge_index.shape[1]):
            in_deg[int(edge_index[1, j])] += 1

        topo = []
        q = deque([i for i in range(N) if in_deg[i] == 0])
        while q:
            u = q.popleft()
            topo.append(u)
            for v in adj_fwd[u]:
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    q.append(v)

        EF = np.zeros(N)
        for u in topo:
            EF[u] = ES[u] + durations[u]
            for v in adj_fwd[u]:
                ES[v] = max(ES[v], EF[u])

        baseline_makespan = float(np.max(EF)) if N > 0 else 100.0

        global_constraints = {
            'deadline': baseline_makespan * 1.2,  # Deadline = 120% makespan
            'total_budget': float(np.sum(features[:, 7:15])) * 2.0,  # Budget = 2x tổng chi phí
            'carbon_cap': float('inf'),
            'min_quality': 0.0,
        }

    edge_attr = data.edge_attr.cpu().numpy() if hasattr(data, 'edge_attr') and data.edge_attr is not None else None

    project_data = {
        'features': features,
        'edge_index': edge_index,
        'edge_attr': edge_attr,
        'durations': durations,
        'resource_demands': resource_demands,
        'resource_capacities': {},
        'global_constraints': global_constraints,
    }

    return LogisticsGymEnv(project_data, penalty_weight=penalty_weight, reward_scale=reward_scale, domain_randomization=domain_randomization)


# ============================================================================
# KHỐI KIỂM TRA (Unit Test)
# ============================================================================
if __name__ == "__main__":
    import sys
    import os
    sys.stdout.reconfigure(encoding='utf-8')
    # Thêm đường dẫn project gốc
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("=" * 70)
    print("  KIỂM TRA MÔI TRƯỜNG LOGISTICS GYM ENV")
    print("=" * 70)

    # 1. Tạo đồ thị dự án giả lập (8 tasks, DAG)
    num_tasks = 8
    np.random.seed(42)

    features = np.random.rand(num_tasks, 72).astype(np.float32) * 10.0
    # Đảm bảo có chi phí cho Crash và Outsource
    features[:, 9] = np.random.rand(num_tasks) * 5.0   # overtime_crashing_cost
    features[:, 8] = np.random.rand(num_tasks) * 3.0   # subcontracting_cost
    features[:, 7] = np.random.rand(num_tasks) * 10.0  # internal_labor_cost

    # Thiết lập thời lượng hợp lý
    features[:, 1] = 0.0  # duration_months
    features[:, 2] = 0.0  # duration_weeks
    features[:, 3] = np.array([2, 3, 1, 4, 2, 3, 1, 5])  # duration_days
    features[:, 4] = 0.0  # duration_hours
    features[:, 5] = 1.0  # calendar_type Agenda
    features[:, 6] = 0.0  # calendar_type 24/7

    # DAG: 0→1, 0→2, 1→3, 2→3, 3→4, 4→5, 4→6, 5→7, 6→7
    edge_index = np.array([
        [0, 0, 1, 2, 3, 4, 4, 5, 6],
        [1, 2, 3, 3, 4, 5, 6, 7, 7],
    ], dtype=np.int64)

    durations = np.array([16, 24, 8, 32, 16, 24, 8, 40], dtype=np.float32)  # hours

    project_data = {
        'features': features,
        'edge_index': edge_index,
        'durations': durations,
        'resource_demands': {
            0: {'Crew_A': 3.0},
            1: {'Crew_A': 2.0, 'Crew_B': 1.0},
            3: {'Crew_A': 4.0},
            5: {'Crew_B': 2.0},
        },
        'resource_capacities': {
            'Crew_A': 5.0,
            'Crew_B': 3.0,
        },
        'global_constraints': {
            'deadline': 200.0,
            'total_budget': 500.0,
            'carbon_cap': 100.0,
            'min_quality': 0.0,
        },
    }

    # 2. Khởi tạo môi trường
    env = LogisticsGymEnv(project_data, render_mode="ansi")

    print(f"\n[1] Cấu hình môi trường:")
    print(f"    Số tasks: {env.num_tasks}")
    print(f"    Observation Space: {env.observation_space}")
    print(f"    Action Space: {env.action_space}")

    # 3. Reset
    obs, info = env.reset(seed=42)
    print(f"\n[2] Reset thành công:")
    print(f"    task_features shape: {obs['task_features'].shape}")
    print(f"    task_context shape:  {obs['task_context'].shape}")
    print(f"    project_state shape: {obs['project_state'].shape}")
    print(f"    Makespan ban đầu:    {info['makespan']:.1f}h")
    print(f"    Đường găng:          {info['num_critical_tasks']} tasks")

    # 4. Chạy Episode: Random Agent với Action Masking
    print(f"\n[3] Chạy Episode (Random Agent + Action Masking):")
    total_reward = 0.0
    step = 0
    terminated = False
    truncated = False

    while not terminated and not truncated:
        # Lấy mask hành động hợp lệ
        mask = env.action_masks()
        valid_actions = np.where(mask)[0]

        # Chọn ngẫu nhiên trong các hành động hợp lệ
        action = np.random.choice(valid_actions)
        mode_name = ['Normal', 'Crash', 'Outsource'][action]

        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        step += 1

        task_idx = env._state['action_history'][-1][0]
        print(f"    Step {step}: Task #{task_idx} → {mode_name}"
              f" | Reward: {reward:.2f} | TGC tích lũy: {info['cumulative_tgc']:.2f}"
              f" | Mask: {mask}")

    print(f"\n[4] Kết quả Episode:")
    print(f"    Tổng Reward: {total_reward:.2f}")
    print(f"    TGC tích lũy: {info['cumulative_tgc']:.2f}")
    print(f"    Makespan cuối: {info['makespan']:.1f}h")
    print(f"    Đường găng cuối: {info['num_critical_tasks']} tasks")
    print(f"    Các chế độ đã gán: {info['modes_assigned']}")

    # 5. Kiểm tra Gymnasium API compatibility
    print(f"\n[5] Kiểm tra Gymnasium API compatibility:")
    try:
        from gymnasium.utils.env_checker import check_env
        env2 = LogisticsGymEnv(project_data)
        check_env(env2, skip_render_check=True)
        print(f"    ✅ Gymnasium check_env PASSED")
    except Exception as e:
        print(f"    ⚠️ Gymnasium check_env: {e}")

    # 6. Kiểm tra Reset/Step lặp lại
    print(f"\n[6] Kiểm tra Reset lặp lại (3 episodes):")
    for ep in range(3):
        obs, info = env.reset(seed=ep)
        ep_reward = 0.0
        done = False
        while not done:
            mask = env.action_masks()
            action = np.random.choice(np.where(mask)[0])
            obs, r, term, trunc, info = env.step(action)
            ep_reward += r
            done = term or trunc
        print(f"    Episode {ep+1}: Reward={ep_reward:.2f}, "
              f"Makespan={info['makespan']:.1f}h, "
              f"TGC={info['cumulative_tgc']:.2f}")

    print(f"\n{'=' * 70}")
    print("  HOÀN TẤT KIỂM TRA LOGISTICS GYM ENV")
    print(f"{'=' * 70}")
