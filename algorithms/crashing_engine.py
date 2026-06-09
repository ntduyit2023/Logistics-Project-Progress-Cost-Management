"""
Module 3: Project Crashing Engine (Ép tiến độ)
================================================
Thuật toán tham lam (Greedy) để rút ngắn thời gian dự án với chi phí
tăng thêm tối thiểu, dựa trên hệ số Cost Slope.

Thuật toán cốt lõi:
    1. Tính Cost Slope cho mỗi task: S = (Crash_Cost - Normal_Cost) / (Normal_Dur - Crash_Dur)
    2. Trong mỗi vòng lặp:
       a. Chạy CPM để xác định đường găng hiện tại
       b. Tìm các task găng có thể crash tiếp (duration > crash_duration)
       c. Nếu có nhiều đường găng → cần crash combo (1 task mỗi đường)
       d. Chọn task/combo có tổng Cost Slope thấp nhất
       e. Giảm duration 1 ngày, cộng thêm chi phí
    3. Lặp cho đến khi đạt target_duration hoặc không thể crash thêm

Đặc biệt cho Case Study PPC 2010:
    - Chi phí overtime: Saturday x1.5, Sunday x3.0 
    - Phải dùng hết Saturday trước khi được dùng Sunday
    - Penalty: $2,000/tuần trễ sau tuần 12
    - Bonus: $3,000/tuần sớm trước tuần 12
    - Overhead: $500/tuần
"""

import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
from copy import deepcopy
from .cpm_engine import calculate_cpm, get_critical_path


def calculate_cost_slope(
    normal_cost: float,
    crash_cost: float,
    normal_duration: int,
    crash_duration: int
) -> float:
    """
    Tính hệ số chi phí cận biên (Cost Slope).

    Cost Slope = (Crash_Cost - Normal_Cost) / (Normal_Duration - Crash_Duration)

    Args:
        normal_cost: Chi phí bình thường
        crash_cost: Chi phí khi ép tối đa
        normal_duration: Thời gian bình thường
        crash_duration: Thời gian tối thiểu khi ép

    Returns:
        Cost Slope ($/ngày rút ngắn). float('inf') nếu không thể crash.
    """
    delta_d = normal_duration - crash_duration
    if delta_d <= 0:
        return float('inf')
    return (crash_cost - normal_cost) / delta_d


def calculate_overtime_cost_for_task(
    G: nx.DiGraph,
    task_id: str,
    resource_costs: Dict[str, float]
) -> float:
    """
    Tính chi phí overtime cho việc crash 1 task thêm 1 ngày (làm thêm ngày T7 hoặc CN).

    Quy tắc từ Case Study (Bảng 5):
        - Saturday: lương x 1.5
        - Sunday: lương x 3.0
        - Phải dùng hết T7 trước khi dùng CN

    Đối với mỗi task, tính chi phí 1 ngày overtime dựa trên
    tổng lương nhân sự làm việc vào task đó.

    Args:
        G: Đồ thị dự án
        task_id: Mã task
        resource_costs: Dict mapping resource_type -> daily_cost

    Returns:
        Chi phí overtime cho 1 ngày rút ngắn
    """
    data = G.nodes[task_id]
    resources = data.get('resources', [])

    # Tổng lương 1 ngày bình thường của tất cả nhân sự làm task này
    daily_labor_cost = sum(resource_costs.get(r, 0) for r in resources)

    # Số ngày đã crash (= normal_duration - current_duration)
    normal_dur = data.get('normal_duration', data['duration'])
    current_dur = data['duration']
    days_already_crashed = normal_dur - current_dur

    # Mỗi tuần có 1 T7 và 1 CN
    # Quy tắc: dùng hết T7 trước, rồi mới dùng CN
    # Giả sử mỗi task khi crash 1 ngày = làm thêm 1 ngày cuối tuần
    # Tuần 1 crash: T7 (x1.5), nếu cần crash thêm: CN (x3.0)
    # Tuần 2 crash tiếp: T7 (x1.5), rồi CN (x3.0), ...

    if days_already_crashed % 2 == 0:
        # Ngày crash tiếp theo là T7 (x1.5)
        overtime_multiplier = 1.5
    else:
        # Ngày crash tiếp theo là CN (x3.0)
        overtime_multiplier = 3.0

    return daily_labor_cost * overtime_multiplier


def find_all_critical_paths(G: nx.DiGraph) -> List[List[str]]:
    """
    Tìm TẤT CẢ các đường găng trong đồ thị (có thể có nhiều đường găng).

    Returns:
        List of critical paths, mỗi path là list các task IDs
    """
    critical_tasks = [n for n in G.nodes() if G.nodes[n].get('is_critical', False)]

    if not critical_tasks:
        return []

    # Tạo subgraph chỉ chứa critical tasks
    critical_subgraph = G.subgraph(critical_tasks).copy()

    # Tìm start nodes và end nodes trong subgraph
    start_nodes = [n for n in critical_subgraph.nodes()
                   if critical_subgraph.in_degree(n) == 0]
    end_nodes = [n for n in critical_subgraph.nodes()
                 if critical_subgraph.out_degree(n) == 0]

    # Tìm tất cả đường đi từ start đến end
    all_paths = []
    for start in start_nodes:
        for end in end_nodes:
            for path in nx.all_simple_paths(critical_subgraph, start, end):
                all_paths.append(path)

    return all_paths


def project_crashing(
    G: nx.DiGraph,
    target_duration: int,
    resource_costs: Optional[Dict[str, float]] = None,
    use_overtime_model: bool = False
) -> Tuple[nx.DiGraph, List[Dict[str, Any]]]:
    """
    Thực hiện ép tiến độ dự án bằng thuật toán tham lam (Greedy Crashing).

    Args:
        G: Đồ thị DAG đã được tính CPM. Mỗi node cần có:
            - 'duration': thời gian hiện tại
            - 'normal_duration': thời gian ban đầu
            - 'crash_duration': thời gian tối thiểu khi ép
            - 'normal_cost': chi phí bình thường
            - 'crash_cost': chi phí khi ép (hoặc sử dụng overtime model)
        target_duration: Thời gian mục tiêu cần đạt
        resource_costs: Chi phí hàng ngày cho mỗi loại resource (cho overtime model)
        use_overtime_model: True để sử dụng mô hình overtime (T7/CN) thay vì cost_slope cố định

    Returns:
        Tuple gồm:
            - G: Đồ thị sau khi crash
            - crash_log: Danh sách các bước crash đã thực hiện
    """
    G = deepcopy(G)

    # Đảm bảo mỗi task có normal_duration
    for node in G.nodes():
        data = G.nodes[node]
        if 'normal_duration' not in data:
            data['normal_duration'] = data['duration']
        if 'crash_duration' not in data:
            data['crash_duration'] = data['duration']  # Không thể crash

    # Tính Cost Slope cố định cho mỗi task (nếu không dùng overtime model)
    if not use_overtime_model:
        for node in G.nodes():
            data = G.nodes[node]
            data['cost_slope'] = calculate_cost_slope(
                data.get('normal_cost', 0),
                data.get('crash_cost', 0),
                data.get('normal_duration', data['duration']),
                data.get('crash_duration', data['duration'])
            )

    # Chạy CPM lần đầu
    G, current_duration = calculate_cpm(G)
    crash_log = []
    total_crash_cost = 0

    step = 0
    while current_duration > target_duration:
        step += 1

        # Tìm tất cả đường găng hiện tại
        critical_paths = find_all_critical_paths(G)

        if not critical_paths:
            break

        # Tìm các task găng có thể crash tiếp
        crashable_critical = set()
        for path in critical_paths:
            for task in path:
                data = G.nodes[task]
                if data['duration'] > data['crash_duration']:
                    crashable_critical.add(task)

        if not crashable_critical:
            # Không thể crash thêm
            crash_log.append({
                'step': step,
                'action': 'STOP',
                'reason': 'Tất cả task găng đã đạt crash_duration tối thiểu',
                'current_duration': current_duration
            })
            break

        # ===== XỬ LÝ TRƯỜNG HỢP NHIỀU ĐƯỜNG GĂNG =====
        if len(critical_paths) == 1:
            # Chỉ có 1 đường găng → chọn task có cost_slope thấp nhất
            candidates = list(crashable_critical)

            if use_overtime_model and resource_costs:
                best_task = min(
                    candidates,
                    key=lambda t: calculate_overtime_cost_for_task(G, t, resource_costs)
                )
                crash_cost = calculate_overtime_cost_for_task(G, best_task, resource_costs)
            else:
                best_task = min(candidates, key=lambda t: G.nodes[t]['cost_slope'])
                crash_cost = G.nodes[best_task]['cost_slope']

            # Crash task 1 ngày
            G.nodes[best_task]['duration'] -= 1
            total_crash_cost += crash_cost

            crash_log.append({
                'step': step,
                'action': 'CRASH',
                'task': best_task,
                'cost': crash_cost,
                'new_duration': G.nodes[best_task]['duration'],
                'total_crash_cost': total_crash_cost
            })
        else:
            # Nhiều đường găng → cần tìm combo tối ưu
            # Kiểm tra xem có task nào nằm trên TẤT CẢ đường găng không
            common_tasks = crashable_critical.copy()
            for path in critical_paths:
                common_tasks &= set(path)

            # Lọc chỉ giữ task có thể crash
            common_crashable = [t for t in common_tasks
                                if G.nodes[t]['duration'] > G.nodes[t]['crash_duration']]

            if common_crashable:
                # Có task chung → chỉ cần crash 1 task
                if use_overtime_model and resource_costs:
                    best_task = min(
                        common_crashable,
                        key=lambda t: calculate_overtime_cost_for_task(G, t, resource_costs)
                    )
                    crash_cost = calculate_overtime_cost_for_task(G, best_task, resource_costs)
                else:
                    best_task = min(common_crashable, key=lambda t: G.nodes[t]['cost_slope'])
                    crash_cost = G.nodes[best_task]['cost_slope']

                G.nodes[best_task]['duration'] -= 1
                total_crash_cost += crash_cost

                crash_log.append({
                    'step': step,
                    'action': 'CRASH (common critical)',
                    'task': best_task,
                    'cost': crash_cost,
                    'new_duration': G.nodes[best_task]['duration'],
                    'total_crash_cost': total_crash_cost,
                    'note': f'Task nằm trên {len(critical_paths)} đường găng'
                })
            else:
                # Phải crash combo: 1 task từ mỗi đường găng
                # Dùng heuristic: tìm combo có tổng cost_slope thấp nhất
                # (simplified: chọn task rẻ nhất từ mỗi đường)
                combo = []
                combo_cost = 0

                for path in critical_paths:
                    path_crashable = [t for t in path
                                      if t in crashable_critical
                                      and t not in [c['task'] for c in combo if 'task' in c]]
                    if path_crashable:
                        if use_overtime_model and resource_costs:
                            best = min(path_crashable,
                                       key=lambda t: calculate_overtime_cost_for_task(G, t, resource_costs))
                            cost = calculate_overtime_cost_for_task(G, best, resource_costs)
                        else:
                            best = min(path_crashable, key=lambda t: G.nodes[t]['cost_slope'])
                            cost = G.nodes[best]['cost_slope']

                        combo.append({'task': best, 'cost': cost})
                        combo_cost += cost

                # Thực hiện crash combo
                for item in combo:
                    G.nodes[item['task']]['duration'] -= 1

                total_crash_cost += combo_cost

                crash_log.append({
                    'step': step,
                    'action': 'CRASH COMBO',
                    'tasks': [c['task'] for c in combo],
                    'costs': [c['cost'] for c in combo],
                    'total_step_cost': combo_cost,
                    'total_crash_cost': total_crash_cost
                })

        # Re-calculate CPM sau mỗi bước crash
        G, current_duration = calculate_cpm(G)

        # Thêm info về duration hiện tại
        if crash_log:
            crash_log[-1]['project_duration_after'] = current_duration

    return G, crash_log


def calculate_crashing_summary(
    crash_log: List[Dict],
    original_duration: int,
    overhead_per_week: float = 500,
    penalty_per_week: float = 2000,
    bonus_per_week: float = 3000,
    baseline_weeks: int = 12
) -> Dict[str, Any]:
    """
    Tạo bảng tổng hợp Time-Cost Tradeoff cho quá trình crashing.

    Args:
        crash_log: Log các bước crash từ project_crashing()
        original_duration: Thời gian ban đầu (ngày)
        overhead_per_week: Chi phí gián tiếp mỗi tuần
        penalty_per_week: Phạt cho mỗi tuần trễ so với baseline
        bonus_per_week: Thưởng cho mỗi tuần sớm so với baseline
        baseline_weeks: Mốc tuần để tính penalty/bonus

    Returns:
        Dict chứa bảng Time-Cost Analysis
    """
    import math

    summary = []
    cumulative_crash_cost = 0

    # Bản gốc (chưa crash)
    original_weeks = math.ceil(original_duration / 5)  # 5 ngày/tuần
    overhead_original = original_weeks * overhead_per_week

    if original_weeks > baseline_weeks:
        penalty_original = (original_weeks - baseline_weeks) * penalty_per_week
        bonus_original = 0
    else:
        penalty_original = 0
        bonus_original = (baseline_weeks - original_weeks) * bonus_per_week

    summary.append({
        'step': 0,
        'duration_days': original_duration,
        'duration_weeks': original_weeks,
        'crash_cost_step': 0,
        'crash_cost_cumulative': 0,
        'overhead': overhead_original,
        'penalty': penalty_original,
        'bonus': bonus_original,
        'total_cost': overhead_original + penalty_original - bonus_original
    })

    for log_entry in crash_log:
        if log_entry.get('action') == 'STOP':
            continue

        dur_after = log_entry.get('project_duration_after', original_duration)
        weeks_after = math.ceil(dur_after / 5)
        step_cost = log_entry.get('cost', log_entry.get('total_step_cost', 0))
        cumulative_crash_cost += step_cost

        overhead = weeks_after * overhead_per_week

        if weeks_after > baseline_weeks:
            penalty = (weeks_after - baseline_weeks) * penalty_per_week
            bonus = 0
        else:
            penalty = 0
            bonus = (baseline_weeks - weeks_after) * bonus_per_week

        total = cumulative_crash_cost + overhead + penalty - bonus

        summary.append({
            'step': log_entry['step'],
            'duration_days': dur_after,
            'duration_weeks': weeks_after,
            'task_crashed': log_entry.get('task', log_entry.get('tasks', '')),
            'crash_cost_step': step_cost,
            'crash_cost_cumulative': cumulative_crash_cost,
            'overhead': overhead,
            'penalty': penalty,
            'bonus': bonus,
            'total_cost': total
        })

    return {
        'time_cost_table': summary,
        'optimal': min(summary, key=lambda x: x['total_cost']) if summary else None
    }


def print_crash_log(crash_log: List[Dict], original_duration: int):
    """
    In log quá trình crash ra console.
    """
    print("\n" + "=" * 90)
    print("QUÁ TRÌNH ÉP TIẾN ĐỘ (PROJECT CRASHING)")
    print("=" * 90)

    print(f"Thời gian dự án ban đầu: {original_duration} ngày\n")

    header = f"{'Step':>5} {'Action':<25} {'Task':>8} {'Cost':>10} {'Cum.Cost':>12} {'Duration':>10}"
    print(header)
    print("-" * 90)

    for entry in crash_log:
        if entry.get('action') == 'STOP':
            print(f"\n⚠️  DỪNG: {entry.get('reason', 'N/A')}")
            continue

        task = entry.get('task', ','.join(entry.get('tasks', [])))
        cost = entry.get('cost', entry.get('total_step_cost', 0))
        cum_cost = entry.get('total_crash_cost', 0)
        dur = entry.get('project_duration_after', '?')

        print(
            f"{entry['step']:>5} "
            f"{entry['action']:<25} "
            f"{task:>8} "
            f"${cost:>9,.0f} "
            f"${cum_cost:>11,.0f} "
            f"{dur:>8} ngày"
        )

    print("=" * 90)
