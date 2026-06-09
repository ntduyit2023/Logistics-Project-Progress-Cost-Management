"""
Module 1: CPM Engine (Critical Path Method)
============================================
Xây dựng đồ thị DAG từ dữ liệu dự án, thực hiện Forward Pass / Backward Pass,
tính Total Slack, Free Slack và xác định Đường găng (Critical Path).

Thuật toán:
    1. Dựng DAG (Directed Acyclic Graph) bằng NetworkX
    2. Forward Pass: Tính ES (Early Start), EF (Early Finish)
       - ES[start] = 0
       - ES[i] = max(EF[j]) với j ∈ Predecessors(i)
       - EF[i] = ES[i] + Duration[i]
    3. Backward Pass: Tính LS (Late Start), LF (Late Finish)
       - LF[end] = max(EF[v]) với v ∈ V (= Project Duration)
       - LF[i] = min(LS[j]) với j ∈ Successors(i)
       - LS[i] = LF[i] - Duration[i]
    4. Total Slack = LS[i] - ES[i]
    5. Free Slack = min(ES[j]) - EF[i] với j ∈ Successors(i)
    6. Critical Path: Tất cả task có Total Slack == 0
"""

import networkx as nx
from typing import Dict, List, Tuple, Any, Optional


def build_project_graph(
    tasks: List[Dict[str, Any]],
    dependencies: List[Tuple[str, str]]
) -> nx.DiGraph:
    """
    Xây dựng đồ thị DAG từ danh sách công việc và quan hệ phụ thuộc.

    Args:
        tasks: Danh sách dict, mỗi dict chứa ít nhất:
            - 'id': Mã công việc (str), ví dụ 'A', 'B', ...
            - 'duration': Thời gian thực hiện (int)
            - Các trường tùy chọn: 'name', 'resources', 'normal_cost',
              'crash_duration', 'crash_cost', ...
        dependencies: Danh sách tuple (predecessor_id, successor_id)

    Returns:
        nx.DiGraph: Đồ thị có hướng không chu trình (DAG)

    Raises:
        ValueError: Nếu đồ thị chứa chu trình (cycle)
    """
    G = nx.DiGraph()

    # Thêm các node (công việc) vào đồ thị
    for task in tasks:
        task_id = task['id']
        G.add_node(task_id, **task)

    # Thêm các cạnh (quan hệ phụ thuộc)
    for pred, succ in dependencies:
        if pred not in G.nodes:
            raise ValueError(f"Predecessor '{pred}' không tồn tại trong danh sách công việc.")
        if succ not in G.nodes:
            raise ValueError(f"Successor '{succ}' không tồn tại trong danh sách công việc.")
        G.add_edge(pred, succ)

    # Kiểm tra chu trình (Cycle Detection)
    if not nx.is_directed_acyclic_graph(G):
        cycles = list(nx.simple_cycles(G))
        raise ValueError(
            f"Đồ thị chứa chu trình! Không thể tính CPM. "
            f"Các chu trình phát hiện: {cycles}"
        )

    return G


def calculate_cpm(G: nx.DiGraph) -> Tuple[nx.DiGraph, int]:
    """
    Thực hiện thuật toán CPM đầy đủ trên đồ thị DAG.

    Bao gồm:
        - Forward Pass (tính ES, EF)
        - Backward Pass (tính LS, LF)
        - Tính Total Slack, Free Slack
        - Xác định Critical Path

    Args:
        G: Đồ thị DAG đã được xây dựng bởi build_project_graph()

    Returns:
        Tuple gồm:
            - G: Đồ thị đã được cập nhật các thuộc tính CPM
            - project_duration: Tổng thời gian hoàn thành dự án
    """
    # =========================================================
    # BƯỚC 1: FORWARD PASS - Tính ES (Early Start) và EF (Early Finish)
    # =========================================================
    # Duyệt theo thứ tự Topological Sort (đảm bảo predecessors luôn được xử lý trước)
    topo_order = list(nx.topological_sort(G))

    for node in topo_order:
        predecessors = list(G.predecessors(node))

        if not predecessors:
            # Công việc gốc (không có predecessor): ES = 0
            G.nodes[node]['es'] = 0
        else:
            # ES = max(EF của tất cả predecessors)
            G.nodes[node]['es'] = max(G.nodes[p]['ef'] for p in predecessors)

        # EF = ES + Duration
        G.nodes[node]['ef'] = G.nodes[node]['es'] + G.nodes[node]['duration']

    # =========================================================
    # BƯỚC 2: Xác định thời gian hoàn thành dự án
    # =========================================================
    project_duration = max(G.nodes[n]['ef'] for n in G.nodes())

    # =========================================================
    # BƯỚC 3: BACKWARD PASS - Tính LF (Late Finish) và LS (Late Start)
    # =========================================================
    # Duyệt ngược lại thứ tự Topological Sort
    for node in reversed(topo_order):
        successors = list(G.successors(node))

        if not successors:
            # Công việc cuối (không có successor): LF = Project Duration
            G.nodes[node]['lf'] = project_duration
        else:
            # LF = min(LS của tất cả successors)
            G.nodes[node]['lf'] = min(G.nodes[s]['ls'] for s in successors)

        # LS = LF - Duration
        G.nodes[node]['ls'] = G.nodes[node]['lf'] - G.nodes[node]['duration']

    # =========================================================
    # BƯỚC 4: Tính Total Slack, Free Slack và xác định Critical Path
    # =========================================================
    for node in G.nodes():
        data = G.nodes[node]

        # Total Slack = LS - ES (hoặc LF - EF)
        data['total_slack'] = data['ls'] - data['es']

        # Free Slack = min(ES[successors]) - EF[node]
        successors = list(G.successors(node))
        if successors:
            data['free_slack'] = min(G.nodes[s]['es'] for s in successors) - data['ef']
        else:
            # Công việc cuối cùng: Free Slack = LF - EF = Total Slack
            data['free_slack'] = data['lf'] - data['ef']

        # Đánh dấu Critical Task
        data['is_critical'] = (data['total_slack'] == 0)

    return G, project_duration


def get_critical_path(G: nx.DiGraph) -> List[str]:
    """
    Trích xuất danh sách công việc trên đường găng (theo thứ tự topological).

    Args:
        G: Đồ thị đã được tính CPM

    Returns:
        Danh sách mã công việc thuộc đường găng, theo thứ tự thực hiện
    """
    topo_order = list(nx.topological_sort(G))
    return [n for n in topo_order if G.nodes[n].get('is_critical', False)]


def get_cpm_results_table(G: nx.DiGraph) -> List[Dict[str, Any]]:
    """
    Xuất kết quả CPM dưới dạng bảng (list of dicts) để dễ hiển thị.

    Args:
        G: Đồ thị đã được tính CPM

    Returns:
        Danh sách dict chứa thông tin CPM của từng task
    """
    topo_order = list(nx.topological_sort(G))
    results = []

    for node in topo_order:
        data = G.nodes[node]
        results.append({
            'Task': node,
            'Name': data.get('name', ''),
            'Duration': data['duration'],
            'ES': data['es'],
            'EF': data['ef'],
            'LS': data['ls'],
            'LF': data['lf'],
            'Total Slack': data['total_slack'],
            'Free Slack': data['free_slack'],
            'Critical': '✓' if data['is_critical'] else ''
        })

    return results


def print_cpm_results(G: nx.DiGraph, project_duration: int):
    """
    In kết quả CPM ra console dạng bảng đẹp.
    """
    results = get_cpm_results_table(G)
    critical_path = get_critical_path(G)

    # Header
    print("\n" + "=" * 90)
    print("KẾT QUẢ PHÂN TÍCH CPM (Critical Path Method)")
    print("=" * 90)

    # Bảng kết quả
    header = f"{'Task':<6} {'Name':<35} {'Dur':>4} {'ES':>4} {'EF':>4} {'LS':>4} {'LF':>4} {'TS':>4} {'FS':>4} {'CP':>4}"
    print(header)
    print("-" * 90)

    for row in results:
        line = (
            f"{row['Task']:<6} "
            f"{row['Name']:<35} "
            f"{row['Duration']:>4} "
            f"{row['ES']:>4} "
            f"{row['EF']:>4} "
            f"{row['LS']:>4} "
            f"{row['LF']:>4} "
            f"{row['Total Slack']:>4} "
            f"{row['Free Slack']:>4} "
            f"{'  ✓' if row['Critical'] else '':>4}"
        )
        print(line)

    print("-" * 90)
    print(f"Thời gian hoàn thành dự án: {project_duration} ngày")
    print(f"Đường găng: {' → '.join(critical_path)}")
    print("=" * 90)
