"""
Mô-đun NSGA-II (Non-dominated Sorting Genetic Algorithm II)
============================================================
Mô-đun này tối ưu hóa đa mục tiêu để lựa chọn chế độ thực thi các công việc.
Tìm tập hợp các phương án đánh đổi tối ưu (Pareto Front) dựa trên 3 mục tiêu:
    1. Tối thiểu hóa thời gian hoàn thành dự án (Makespan - CPM)
    2. Tối thiểu hóa tổng chi phí thực hiện
    3. Tối thiểu hóa rủi ro tích lũy (Chỉ số rủi ro task được gán trọng số theo chỉ số găng)
Mỗi task có 3 chế độ thực thi: Bình thường (0), Tăng ca/Crash (1) và Thuê ngoài/Outsource (2).
Sử dụng thư viện pymoo (hoặc giải thuật fallback tự viết bằng Python nếu thiếu thư viện).
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional

# Import mô-đun CPM nội bộ
try:
    from ai_pipeline.src.algorithms.cpm import build_project_graph, calculate_cpm
except ImportError:
    # Dự phòng import nếu chạy độc lập
    from cpm import build_project_graph, calculate_cpm

# Thử import các lớp của thư viện pymoo phục vụ tối ưu hóa
PYMOO_AVAILABLE = False
try:
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.optimize import minimize
    from pymoo.operators.sampling.rnd import IntegerRandomSampling
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    PYMOO_AVAILABLE = True
except ImportError:
    pass

class ProjectMultiObjectiveProblem:
    """
    Lớp xử lý đánh giá tính toán lõi cho bài toán đánh đổi Thời gian - Chi phí - Rủi ro.
    """
    def __init__(
        self,
        tasks: List[Dict[str, Any]],
        dependencies: List[Tuple[Any, Any]],
        criticality_indices: Dict[Any, float],
        b_max: float = float('inf'),
        k_max: int = 9999
    ):
        self.tasks = tasks
        self.dependencies = dependencies
        self.criticality_indices = criticality_indices
        self.b_max = b_max
        self.k_max = k_max
        
        self.num_tasks = len(tasks)
        self.task_ids = [t['id'] for t in tasks]
        
        # Thiết lập trước ánh xạ các tham số theo chế độ thực thi để tính toán nhanh
        # Chế độ: 0 = Bình thường, 1 = Tăng ca (Crash), 2 = Thuê ngoài (Outsource)
        self.durations_by_mode = []
        self.costs_by_mode = []
        self.risks_by_mode = []
        
        for task in tasks:
            # Thời lượng
            d_m = float(task.get('duration_months', 0.0) or 0.0)
            d_w = float(task.get('duration_weeks', 0.0) or 0.0)
            d_d = float(task.get('duration_days', 0.0) or 0.0)
            d_h = float(task.get('duration_hours', 0.0) or 0.0)
            d_norm = float(task.get('most_probable_duration', task.get('duration', d_m * 720 + d_w * 168 + d_d * 24 + d_h)))
            d_crash = float(task.get('crash_duration', d_norm * 0.7))
            d_out = float(task.get('outsource_duration', d_norm * 0.8))
            
            # Hàm an toàn cho chi phí
            def safe_float(v):
                try:
                    val = float(v)
                    import math
                    return 0.0 if math.isnan(val) else val
                except (ValueError, TypeError):
                    return 0.0

            # Chi phí
            c_norm = safe_float(task.get('total_cost', 0.0))
            if c_norm == 0.0:
                # Tính tổng chi phí từ các cột chi phí thành phần có trong dataset
                cost_keys = [
                    'internal_labor_cost', 'subcontracting_cost', 'overtime_crashing_cost',
                    'material_cost', 'equipment_cost', 'direct_transportation',
                    'energy_fuel_cost', 'testing_and_inspection', 'pm_overhead',
                    'facility_rent', 'utilities', 'communication_cost',
                    'internal_training', 'quality_mgmt_overhead'
                ]
                c_norm = sum(safe_float(task.get(k, 0.0)) for k in cost_keys)
                
            c_crash = float(task.get('crash_cost', c_norm * 1.5))
            c_out = float(task.get('outsource_cost', c_norm * 2.0))
            
            # Rủi ro
            r_norm = float(task.get('risk_index', 0.5))
            r_crash = float(task.get('crash_risk', r_norm * 0.8))
            r_out = float(task.get('outsource_risk', r_norm * 0.5))
            
            self.durations_by_mode.append([d_norm, d_crash, d_out])
            self.costs_by_mode.append([c_norm, c_crash, c_out])
            self.risks_by_mode.append([r_norm, r_crash, r_out])

    def evaluate_solution(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Đánh giá một vector quyết định x kích thước (num_tasks,) với mỗi phần tử thuộc {0, 1, 2}.
        
        Returns:
            objectives: Mảng [makespan, total_cost, total_risk]
            constraints: Mảng [cost_violation, outsource_violation] (giá trị âm hoặc 0 là hợp lệ)
        """
        # 1. Cập nhật thời lượng task dựa trên chế độ thực thi đã chọn
        updated_tasks = []
        for idx, task in enumerate(self.tasks):
            mode = int(x[idx])
            updated_task = task.copy()
            updated_task['duration'] = self.durations_by_mode[idx][mode]
            if 'most_probable_duration' in updated_task:
                updated_task['most_probable_duration'] = self.durations_by_mode[idx][mode]
            updated_tasks.append(updated_task)
            
        # 2. Chạy CPM để tính toán thời gian hoàn thành dự án (Makespan)
        try:
            G = build_project_graph(updated_tasks, self.dependencies)
            _, makespan = calculate_cpm(G)
        except Exception:
            # Dự phòng cộng dồn thời gian nếu đồ thị bị lỗi cấu trúc khi khởi tạo
            makespan = sum(self.durations_by_mode[idx][int(x[idx])] for idx in range(self.num_tasks))
            
        # 3. Tính toán Chi phí và Rủi ro có trọng số
        total_cost = 0.0
        total_risk = 0.0
        num_outsourced = 0
        
        for idx, task_id in enumerate(self.task_ids):
            mode = int(x[idx])
            total_cost += self.costs_by_mode[idx][mode]
            
            crit_idx = self.criticality_indices.get(task_id, 0.0)
            risk_val = self.risks_by_mode[idx][mode]
            total_risk += risk_val * crit_idx
            
            if mode == 2:  # Chế độ thuê ngoài
                num_outsourced += 1
                
        # 4. Thiết lập các ràng buộc (ràng buộc <= 0 là hợp lệ)
        cost_constraint = total_cost - self.b_max
        outsource_constraint = num_outsourced - self.k_max
        
        objectives = np.array([makespan, total_cost, total_risk])
        constraints = np.array([cost_constraint, outsource_constraint])
        
        return objectives, constraints

# Định nghĩa lớp bao bọc Pymoo nếu thư viện có sẵn
if PYMOO_AVAILABLE:
    class PymooProjectProblem(ElementwiseProblem):
        def __init__(self, core_problem: ProjectMultiObjectiveProblem):
            self.core = core_problem
            super().__init__(
                n_var=self.core.num_tasks,
                n_obj=3,
                n_ieq_constr=2,
                xl=np.zeros(self.core.num_tasks, dtype=int),
                xu=np.ones(self.core.num_tasks, dtype=int) * 2
            )
            
        def _evaluate(self, x, out, *args, **kwargs):
            objs, constrs = self.core.evaluate_solution(x)
            out["F"] = objs
            out["G"] = constrs
else:
    class PymooProjectProblem:
        """Lớp giữ chỗ dự phòng khi thiếu thư viện pymoo"""
        def __init__(self, *args, **kwargs):
            pass

def run_nsga2_optimization(
    tasks: List[Dict[str, Any]],
    dependencies: List[Tuple[Any, Any]],
    criticality_indices: Dict[Any, float],
    b_max: float = float('inf'),
    k_max: int = 9999,
    pop_size: int = 100,
    n_generations: int = 100,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Chạy thuật toán NSGA-II để tìm tập phương án tối ưu Pareto.

    Args:
        tasks: Danh sách các dict chứa thuộc tính task
        dependencies: Danh sách các quan hệ tiên quyết dạng tuple
        criticality_indices: Chỉ số găng của từng task lấy từ mô phỏng Monte Carlo
        b_max: Giới hạn ngân sách nghiêm ngặt của dự án
        k_max: Số lượng task thuê ngoài tối đa cho phép
        pop_size: Kích thước quần thể gen
        n_generations: Số lượng thế hệ lặp của giải thuật
        seed: Seed ngẫu nhiên để tái lập kết quả

    Returns:
        Danh sách các phương án tối ưu thuộc biên Pareto:
            [
                {
                    'makespan': float,
                    'cost': float,
                    'risk': float,
                    'modes': List[int] (danh sách chế độ chọn cho mỗi task)
                },
                ...
            ]
    """
    core_problem = ProjectMultiObjectiveProblem(
        tasks=tasks,
        dependencies=dependencies,
        criticality_indices=criticality_indices,
        b_max=b_max,
        k_max=k_max
    )
    
    if PYMOO_AVAILABLE:
        # Thực thi NSGA-II bằng thư viện Pymoo
        problem = PymooProjectProblem(core_problem)
        
        algorithm = NSGA2(
            pop_size=pop_size,
            sampling=IntegerRandomSampling(),
            crossover=SBX(prob=0.9, eta=15, vtype=int),
            mutation=PM(prob=0.1, eta=20, vtype=int),
            eliminate_duplicates=True
        )
        
        res = minimize(
            problem,
            algorithm,
            ('n_gen', n_generations),
            seed=seed,
            verbose=False
        )
        
        # Định dạng và giải nén kết quả tối ưu Pareto
        pareto_options = []
        if res.X is not None:
            # Xử lý trường hợp trả về 1 hoặc nhiều giải pháp trên biên Pareto
            solutions_x = res.X if len(res.X.shape) > 1 else np.array([res.X])
            solutions_f = res.F if len(res.F.shape) > 1 else np.array([res.F])
            
            for idx, x in enumerate(solutions_x):
                f = solutions_f[idx]
                pareto_options.append({
                    'makespan': float(f[0]),
                    'cost': float(f[1]),
                    'risk': float(f[2]),
                    'modes': x.tolist()
                })
        return pareto_options
    else:
        # Fallback Python thuần: Lấy mẫu ngẫu nhiên có lọc thống trị Pareto
        print("[WARNING] Thư viện pymoo chưa được cài đặt. Đang chạy thuật toán fallback bằng Python thuần...")
        
        # Thiết lập seed
        np.random.seed(seed)
        sampled_solutions = []
        
        # Lấy mẫu ngẫu nhiên tập quần thể
        for _ in range(pop_size * 5):
            # Tạo ngẫu nhiên vector chế độ: kích thước N, các giá trị trong khoảng {0, 1, 2}
            x = np.random.randint(0, 3, size=core_problem.num_tasks)
            objs, constrs = core_problem.evaluate_solution(x)
            
            # Kiểm tra tính hợp lệ ràng buộc
            if np.all(constrs <= 0):
                sampled_solutions.append((objs, x))
                
        if not sampled_solutions:
            # Nếu không tìm thấy giải pháp hợp lệ nào, trả về kịch bản mặc định (chế độ 0 cho tất cả)
            x_norm = np.zeros(core_problem.num_tasks, dtype=int)
            objs, _ = core_problem.evaluate_solution(x_norm)
            return [{'makespan': float(objs[0]), 'cost': float(objs[1]), 'risk': float(objs[2]), 'modes': x_norm.tolist()}]
            
        # Lọc không thống trị để trích xuất biên Pareto
        pareto_options = []
        for i, (objs_i, x_i) in enumerate(sampled_solutions):
            is_dominated = False
            for j, (objs_j, x_j) in enumerate(sampled_solutions):
                if i == j:
                    continue
                # Giải pháp j thống trị giải pháp i nếu:
                # - j tốt hơn hoặc bằng i trên mọi mục tiêu, VÀ
                # - j tốt hơn hẳn i trên ít nhất một mục tiêu
                better_in_all = np.all(objs_j <= objs_i)
                better_in_at_least_one = np.any(objs_j < objs_i)
                if better_in_all and better_in_at_least_one:
                    is_dominated = True
                    break
            
            if not is_dominated:
                # Kiểm tra trùng lặp mục tiêu
                if not any(np.allclose(objs_i, opt['objectives']) for opt in pareto_options):
                    pareto_options.append({
                        'makespan': float(objs_i[0]),
                        'cost': float(objs_i[1]),
                        'risk': float(objs_i[2]),
                        'modes': x_i.tolist(),
                        'objectives': objs_i # Lưu tạm để kiểm tra trùng lặp
                    })
                    
        # Loại bỏ các khóa bổ trợ tạm thời
        for opt in pareto_options:
            opt.pop('objectives', None)
            
        return sorted(pareto_options, key=lambda x: x['makespan'])
