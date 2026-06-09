"""
Module 2: Resource Smoothing (San bằng Tài nguyên)
====================================================
Tính toán Resource Profile (nhu cầu nhân sự theo ngày) và thực hiện
thuật toán Heuristic để san bằng tài nguyên khi bị quá tải.

Thuật toán:
    1. Tính Daily Resource Profile từ lịch ES hiện tại
    2. Phát hiện ngày quá tải (demand > capacity)
    3. Với mỗi ngày quá tải, tìm task phi găng (Slack > 0)
       đang chạy trong ngày đó
    4. Dịch chuyển task có Slack lớn nhất sang 1 ngày
    5. Lặp lại cho đến khi hết quá tải hoặc hết slack khả dụng

Lưu ý quan trọng:
    - Chỉ dịch chuyển task trong phạm vi Slack cho phép
    - KHÔNG thay đổi thời gian tổng dự án (Project Duration)
    - Đây là Resource SMOOTHING (san bằng trong hạn), 
      KHÔNG phải Resource LEVELING (có thể kéo dài dự án)
"""

import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
from copy import deepcopy


def get_daily_resource_profile(
    G: nx.DiGraph,
    resource_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tính toán nhu cầu nhân sự theo từng ngày (Daily Resource Profile).

    Có thể tính tổng hợp tất cả resource hoặc tách theo từng loại resource.

    Args:
        G: Đồ thị đã được tính CPM
        resource_type: Nếu chỉ định, chỉ tính cho loại resource cụ thể.
                       Nếu None, tính theo từng loại resource riêng biệt.

    Returns:
        Dict chứa:
            - 'total_profile': List[int] - tổng resource theo ngày
            - 'per_resource': Dict[str, List[int]] - resource theo từng loại
            - 'task_schedule': Dict[str, tuple] - (es, ef) mỗi task
    """
    project_duration = max(G.nodes[n]['ef'] for n in G.nodes())

    # Profile tổng hợp
    total_profile = [0] * project_duration
    # Profile theo từng loại resource
    per_resource_profile = {}
    # Lịch trình các task
    task_schedule = {}

    for node, data in G.nodes(data=True):
        es = data['es']
        ef = data['ef']
        task_schedule[node] = (es, ef)

        resources = data.get('resources', [])
        if not resources:
            continue

        for res in resources:
            if resource_type and res != resource_type:
                continue

            if res not in per_resource_profile:
                per_resource_profile[res] = [0] * project_duration

            for t in range(es, ef):
                per_resource_profile[res][t] += 1
                total_profile[t] += 1

    return {
        'total_profile': total_profile,
        'per_resource': per_resource_profile,
        'task_schedule': task_schedule,
        'project_duration': project_duration
    }


def detect_overloaded_days(
    profile: List[int],
    capacity: int
) -> List[Tuple[int, int]]:
    """
    Phát hiện các ngày bị quá tải tài nguyên.

    Args:
        profile: Resource profile (demand mỗi ngày)
        capacity: Năng lực tối đa cho phép

    Returns:
        List of (day, overload_amount) cho các ngày vượt quá capacity
    """
    overloaded = []
    for day, demand in enumerate(profile):
        if demand > capacity:
            overloaded.append((day, demand - capacity))
    return overloaded


def resource_smoothing(
    G: nx.DiGraph,
    resource_capacities: Dict[str, int]
) -> Tuple[nx.DiGraph, Dict[str, Any]]:
    """
    Thực hiện san bằng tài nguyên bằng thuật toán Heuristic.

    Dịch chuyển các task phi găng (có Total Slack > 0) để giảm quá tải,
    mà KHÔNG kéo dài tổng thời gian dự án.

    Args:
        G: Đồ thị DAG đã được tính CPM
        resource_capacities: Dict mapping resource_type -> max_capacity
                             Ví dụ: {'Design(Comp)': 1, 'Dev(Mech)': 1, ...}

    Returns:
        Tuple gồm:
            - G: Đồ thị đã được điều chỉnh lịch trình
            - report: Dict chứa thông tin về các thay đổi đã thực hiện
    """
    G = deepcopy(G)
    project_duration = max(G.nodes[n]['ef'] for n in G.nodes())

    adjustments = []
    iteration = 0
    max_iterations = 1000  # Tránh vòng lặp vô hạn

    while iteration < max_iterations:
        iteration += 1
        found_overload = False

        # Kiểm tra từng loại resource
        for res_type, capacity in resource_capacities.items():
            # Tính profile cho resource type này
            res_profile = [0] * project_duration

            for node, data in G.nodes(data=True):
                resources = data.get('resources', [])
                es = data['es']
                ef = data['ef']
                for res in resources:
                    if res == res_type:
                        for t in range(es, ef):
                            res_profile[t] += 1

            # Tìm ngày quá tải đầu tiên
            for t in range(project_duration):
                if res_profile[t] <= capacity:
                    continue

                found_overload = True

                # Tìm các task phi găng đang chạy vào ngày t
                candidates = [
                    n for n in G.nodes()
                    if G.nodes[n]['es'] <= t < G.nodes[n]['ef']
                    and G.nodes[n].get('total_slack', 0) > 0
                    and res_type in G.nodes[n].get('resources', [])
                ]

                if not candidates:
                    continue

                # Chọn task có Total Slack lớn nhất
                best_task = max(
                    candidates,
                    key=lambda x: G.nodes[x]['total_slack']
                )

                # Dịch chuyển ES lên 1 ngày
                old_es = G.nodes[best_task]['es']
                G.nodes[best_task]['es'] += 1
                G.nodes[best_task]['ef'] += 1
                G.nodes[best_task]['total_slack'] -= 1

                adjustments.append({
                    'iteration': iteration,
                    'task': best_task,
                    'resource': res_type,
                    'day': t,
                    'old_es': old_es,
                    'new_es': old_es + 1,
                    'remaining_slack': G.nodes[best_task]['total_slack']
                })

                break  # Tính lại profile sau mỗi thay đổi

            if found_overload:
                break

        if not found_overload:
            break

    # Tạo báo cáo
    report = {
        'total_adjustments': len(adjustments),
        'iterations': iteration,
        'adjustments': adjustments,
        'remaining_overloads': {}
    }

    # Kiểm tra xem còn quá tải không
    for res_type, capacity in resource_capacities.items():
        res_profile = [0] * project_duration
        for node, data in G.nodes(data=True):
            if res_type in data.get('resources', []):
                for t in range(data['es'], data['ef']):
                    res_profile[t] += 1
        overloads = detect_overloaded_days(res_profile, capacity)
        if overloads:
            report['remaining_overloads'][res_type] = overloads

    return G, report


def print_resource_profile(
    profile_data: Dict[str, Any],
    resource_capacities: Optional[Dict[str, int]] = None
):
    """
    In Resource Profile ra console dạng bảng.
    """
    per_resource = profile_data['per_resource']
    project_dur = profile_data['project_duration']

    print("\n" + "=" * 80)
    print("RESOURCE PROFILE (Nhu cầu nhân sự theo ngày)")
    print("=" * 80)

    for res_type, profile in sorted(per_resource.items()):
        cap = resource_capacities.get(res_type, '∞') if resource_capacities else '∞'
        peak = max(profile) if profile else 0
        overloaded = sum(1 for v in profile if resource_capacities and v > resource_capacities.get(res_type, float('inf')))

        print(f"\n--- {res_type} (Capacity: {cap}, Peak: {peak}, Overloaded days: {overloaded}) ---")

        # Hiển thị dạng bar chart đơn giản
        for day in range(project_dur):
            demand = profile[day]
            bar = '█' * demand
            cap_val = resource_capacities.get(res_type, float('inf')) if resource_capacities else float('inf')
            marker = ' ⚠️ OVERLOAD!' if demand > cap_val else ''
            print(f"  Day {day:>3}: {bar} ({demand}){marker}")

    print("=" * 80)
