"""
Mô-đun Lập Lịch CP-SAT (Constraint Programming - SAT Solver)
=============================================================
Mô-đun này triển khai bộ giải bài toán lập lịch ràng buộc tài nguyên (RCPSP)
sử dụng thư viện Google OR-Tools CP-SAT.
Nó tìm thời điểm bắt đầu và kết thúc tối ưu cho từng task sao cho:
    - Tôn trọng ràng buộc thứ tự tiên quyết (DAG).
    - Không vượt quá giới hạn tài nguyên khả dụng tại mỗi thời điểm (Cumulative constraints).
    - Tối thiểu hóa tổng thời gian hoàn thành dự án (Makespan).
Tự động kích hoạt giải thuật Heuristic dự phòng (Serial SGS) nếu thiếu thư viện ortools.
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional

try:
    from ai_pipeline.src.utils.agenda_calculator import calculate_duration_hours
except ImportError:
    from src.utils.agenda_calculator import calculate_duration_hours

# Thử import thư viện Google OR-Tools
ORTOOLS_AVAILABLE = False
try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    pass

def run_cpsat_scheduling(
    tasks: List[Dict[str, Any]],
    dependencies: List[Tuple[Any, Any]],
    resource_capacities: Dict[str, int],
    calendar_data: Optional[Dict[str, Any]] = None,
    horizon_multiplier: float = 3.0,
    time_limit_sec: float = 60.0,
    hours_per_day: float = 8.0,
    days_per_week: float = 5.0
) -> Dict[str, Any]:
    """
    Chạy bộ lập lịch CP-SAT để tìm Baseline Schedule tối ưu cho bài toán RCPSP.

    Args:
        tasks: Danh sách các task. Mỗi task là một dict chứa:
            - 'id': ID duy nhất của task
            - 'duration': Thời lượng thực hiện (số nguyên ngày)
            - 'resource_demand': Dict nhu cầu tài nguyên, ví dụ: {'nhan_su': 2, 'may_moc': 1}
        dependencies: Danh sách các quan hệ tiên quyết (pred_id, succ_id)
        resource_capacities: Dict giới hạn tối đa của từng loại tài nguyên, ví dụ: {'nhan_su': 5, 'may_moc': 2}
        calendar_data: Thông tin lịch làm việc để hiệu chỉnh ngày lễ/cuối tuần (tùy chọn)
        horizon_multiplier: Hệ số nhân để ước lượng thời gian chân trời (horizon) tối đa của dự án

    Returns:
        Dict kết quả lập lịch:
            - 'status': Trạng thái của bộ giải ("OPTIMAL", "FEASIBLE", "INFEASIBLE", "TIMEOUT", hoặc "FALLBACK_HEURISTIC")
            - 'makespan': Tổng thời lượng dự án tối ưu
            - 'schedule': Dict ánh xạ task_id sang {'start': int, 'end': int, 'duration': int}
            - 'resource_profiles': Biểu đồ phân bổ tài nguyên theo thời gian
    """
    # Lọc bỏ các cạnh rỗng / NaN ngay từ đầu
    valid_deps = []
    for edge in dependencies:
        pred, succ = edge[0], edge[1]
        if not pred or not succ or str(pred).lower() == 'nan' or str(succ).lower() == 'nan':
            continue
        valid_deps.append((pred, succ))
    dependencies = valid_deps

    # 1. Phát hiện chu trình trước khi giải
    G = nx.DiGraph()
    for task in tasks:
        G.add_node(task['id'], **task)
    for pred, succ in dependencies:
        G.add_edge(pred, succ)
        
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("Đồ thị dự án chứa chu trình; không thể lập lịch.")
        
    # Tính thời gian chân trời tối đa (Horizon) làm biên trên cho bộ giải
    sum_durations = sum(max(1, int(t.get('most_probable_duration', t.get('duration', 0)))) for t in tasks)
    horizon = int(sum_durations * horizon_multiplier)
    
    if ORTOOLS_AVAILABLE:
        # --- TRIỂN KHAI BẰNG GOOGLE OR-TOOLS CP-SAT ---
        model = cp_model.CpModel()
        
        # Biến quyết định
        task_intervals = {}
        task_starts = {}
        task_ends = {}
        
        for task in tasks:
            task_id = task['id']
            d_m = float(task.get('duration_months', 0.0) or 0.0)
            d_w = float(task.get('duration_weeks', 0.0) or 0.0)
            d_d = float(task.get('duration_days', 0.0) or 0.0)
            d_h = float(task.get('duration_hours', 0.0) or 0.0)
            cal_type = str(task.get('calendar_type', 'Agenda'))
            dur_calc = calculate_duration_hours(d_m, d_w, d_d, d_h, hours_per_day, days_per_week, cal_type)
            duration = max(1, int(task.get('most_probable_duration', task.get('duration', dur_calc))))
            
            # Khai báo các biến Start, End, Interval trong CP-SAT
            start_var = model.NewIntVar(0, horizon, f"start_{task_id}")
            end_var = model.NewIntVar(0, horizon, f"end_{task_id}")
            interval_var = model.NewIntervalVar(start_var, duration, end_var, f"interval_{task_id}")
            
            task_starts[task_id] = start_var
            task_ends[task_id] = end_var
            task_intervals[task_id] = interval_var
            
        # Ràng buộc 1: Quan hệ tiên quyết (Precedence Constraints)
        for pred, succ in dependencies:
            model.Add(task_starts[succ] >= task_ends[pred])
            
        # Ràng buộc 2: Giới hạn tài nguyên tích lũy (Cumulative Resource Constraints)
        for res_type, capacity in resource_capacities.items():
            intervals = []
            demands = []
            
            for task in tasks:
                task_id = task['id']
                # Đọc nhu cầu tài nguyên của task
                demands_dict = task.get('resource_demand', {})
                # Nếu demands_dict là chuỗi định dạng (ví dụ: 'Handlanger[2.00 #20]'), cần tiền xử lý
                # Ở đây chúng ta tạm thời lấy số nguyên đơn giản từ dict
                demand_val = 0
                if isinstance(demands_dict, dict):
                    demand_val = int(demands_dict.get(res_type, 0))
                
                if demand_var := demand_val:
                    intervals.append(task_intervals[task_id])
                    demands.append(demand_val)
                    
            if intervals:
                # AddCumulative đảm bảo tại mọi thời điểm t, tổng demand <= capacity
                model.AddCumulative(intervals, demands, capacity)
                
        # Mục tiêu: Tối thiểu hóa Makespan (Thời điểm kết thúc của các công việc cuối cùng)
        makespan = model.NewIntVar(0, horizon, "makespan")
        # Makespan phải >= End time của tất cả các tasks
        model.AddMaxEquality(makespan, list(task_ends.values()))
        model.Minimize(makespan)
        
        # Cấu hình solver
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(time_limit_sec)  # Giới hạn thời gian giải
        
        status = solver.Solve(model)
        
        # Xử lý kết quả đầu ra
        status_name = "UNKNOWN"
        schedule = {}
        project_makespan = 0
        
        if status == cp_model.OPTIMAL:
            status_name = "OPTIMAL"
        elif status == cp_model.FEASIBLE:
            status_name = "FEASIBLE"
        elif status == cp_model.INFEASIBLE:
            status_name = "INFEASIBLE"
            
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            project_makespan = int(solver.ObjectiveValue())
            for task in tasks:
                task_id = task['id']
                start_val = int(solver.Value(task_starts[task_id]))
                end_val = int(solver.Value(task_ends[task_id]))
                schedule[task_id] = {
                    'start': start_val,
                    'end': end_val,
                    'duration': end_val - start_val
                }
                
            # Tính toán biểu đồ tài nguyên sử dụng theo thời gian
            resource_profiles = calculate_resource_profiles(schedule, tasks, resource_capacities, project_makespan)
            
            return {
                'status': status_name,
                'makespan': project_makespan,
                'schedule': schedule,
                'resource_profiles': resource_profiles
            }
        else:
            return {
                'status': status_name,
                'makespan': 0,
                'schedule': {},
                'resource_profiles': {}
            }
            
    else:
        # --- GIẢI THUẬT DỰ PHÒNG HEURISTIC (Serial Schedule Generation Scheme) ---
        print("[WARNING] Google OR-Tools chưa được cài đặt. Đang sử dụng thuật toán Heuristic Serial-SGS dự phòng...")
        
        topo_order = list(nx.topological_sort(G))
        schedule = {}
        
        # Mảng lưu vết lượng tài nguyên đã sử dụng tại mỗi thời điểm t
        # Kích thước mảng tạm thời lấy bằng horizon
        max_time = horizon
        res_usage = {res: np.zeros(max_time, dtype=int) for res in resource_capacities}
        
        for task_id in topo_order:
            task_data = G.nodes[task_id]
            duration = max(1, int(task_data.get('most_probable_duration', task_data.get('duration', 0))))
            
            # Đọc nhu cầu tài nguyên
            demands = task_data.get('resource_demand', {})
            
            # 1. Tìm thời điểm bắt đầu sớm nhất có thể dựa trên quan hệ tiên quyết
            preds = list(G.predecessors(task_id))
            es_limit = 0
            if preds:
                es_limit = max(schedule[p]['end'] for p in preds)
                
            # 2. Tìm thời điểm bắt đầu t >= es_limit sao cho đủ tài nguyên trong suốt khoảng [t, t + duration]
            scheduled_start = es_limit
            for t in range(es_limit, max_time - duration):
                feasible = True
                for res, cap in resource_capacities.items():
                    demand_val = 0
                    if isinstance(demands, dict):
                        demand_val = int(demands.get(res, 0))
                    
                    if demand_val > 0:
                        # Kiểm tra xem tài nguyên sử dụng vượt quá giới hạn hay không
                        future_usage = res_usage[res][t : t + duration] + demand_val
                        if np.any(future_usage > cap):
                            feasible = False
                            break
                if feasible:
                    scheduled_start = t
                    break
                    
            # Đăng ký lịch cho task
            scheduled_end = scheduled_start + duration
            schedule[task_id] = {
                'start': scheduled_start,
                'end': scheduled_end,
                'duration': duration
            }
            
            # Cập nhật lượng tài nguyên sử dụng vào mảng lưu vết
            for res, cap in resource_capacities.items():
                demand_val = 0
                if isinstance(demands, dict):
                    demand_val = int(demands.get(res, 0))
                if demand_val > 0:
                    res_usage[res][scheduled_start:scheduled_end] += demand_val
                    
        project_makespan = max(schedule[t]['end'] for t in schedule) if schedule else 0
        resource_profiles = calculate_resource_profiles(schedule, tasks, resource_capacities, project_makespan)
        
        return {
            'status': "FALLBACK_HEURISTIC",
            'makespan': project_makespan,
            'schedule': schedule,
            'resource_profiles': resource_profiles
        }

def calculate_resource_profiles(
    schedule: Dict[Any, Dict[str, int]],
    tasks: List[Dict[str, Any]],
    resource_capacities: Dict[str, int],
    makespan: int
) -> Dict[str, List[int]]:
    """
    Tính toán biểu đồ sử dụng tài nguyên theo từng đơn vị thời gian từ 0 đến makespan.
    """
    profiles = {res: [0] * (makespan + 1) for res in resource_capacities}
    
    for task in tasks:
        task_id = task['id']
        if task_id not in schedule:
            continue
            
        start = schedule[task_id]['start']
        end = schedule[task_id]['end']
        demands = task.get('resource_demand', {})
        
        for res in resource_capacities:
            demand_val = 0
            if isinstance(demands, dict):
                demand_val = int(demands.get(res, 0))
                
            if demand_val > 0:
                for t in range(start, end):
                    if t <= makespan:
                        profiles[res][t] += demand_val
                        
    return profiles
