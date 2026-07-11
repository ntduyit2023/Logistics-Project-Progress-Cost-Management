"""
Mô-đun CPM (Critical Path Method) - Phân Tích Lập Lịch Tĩnh
============================================================
Mô-đun này triển khai Phương pháp Đường Găng (CPM) cổ điển sử dụng NetworkX.
Nó tính toán Khởi công Sớm (ES), Hoàn thành Sớm (EF), Khởi công Muộn (LS), Hoàn thành Muộn (LF),
Dự trữ Toàn phần (Total Slack), Dự trữ Tự do (Free Slack), và xác định Đường găng (Critical Path) của đồ thị dự án.
"""

import networkx as nx
from typing import Dict, List, Tuple, Any, Optional

try:
    from ai_pipeline.src.utils.agenda_calculator import calculate_duration_hours
except ImportError:
    from src.utils.agenda_calculator import calculate_duration_hours

def build_project_graph(
    tasks: List[Dict[str, Any]],
    dependencies: List[Tuple[Any, Any]]
) -> nx.DiGraph:
    """
    Xây dựng Đồ thị Có hướng Không chu trình (DAG) từ danh sách công việc và quan hệ phụ thuộc.

    Args:
        tasks: Danh sách các dictionary, mỗi dict chứa ít nhất:
            - 'id': Mã định danh duy nhất của task (int hoặc str)
            - 'duration': Thời lượng tiêu chuẩn của task (float hoặc int)
            - 'name': Tên task (tùy chọn)
        dependencies: Danh sách các tuple đại diện cho quan hệ có hướng (predecessor_id, successor_id)

    Returns:
        nx.DiGraph: Đồ thị phụ thuộc của dự án với các thuộc tính task kèm theo.
    """
    G = nx.DiGraph()
    
    # Thêm các nút với các thuộc tính kèm theo
    for task in tasks:
        task_id = task['id']
        G.add_node(task_id, **task)
        
    # Thêm các cạnh phụ thuộc
    for edge in dependencies:
        if len(edge) == 3:
            pred, succ, attrs = edge
        else:
            pred, succ = edge[0], edge[1]
            attrs = {}
            
        # Bỏ qua nếu thông tin nút bị rỗng hoặc NaN
        if not pred or not succ or str(pred).lower() == 'nan' or str(succ).lower() == 'nan':
            continue
        if pred not in G.nodes or succ not in G.nodes:
            continue # Bỏ qua các quan hệ có nút không tồn tại thay vì ném lỗi
        G.add_edge(pred, succ, **attrs)
        
    # Phát hiện và tự động gỡ chu trình (Break cycles)
    while not nx.is_directed_acyclic_graph(G):
        try:
            cycle = nx.find_cycle(G, orientation="original")
            # cycle là list các cạnh, ví dụ [('A', 'B'), ('B', 'C'), ('C', 'A')]
            # Chúng ta sẽ xóa cạnh cuối cùng để gỡ chu trình
            edge_to_remove = cycle[-1]
            G.remove_edge(edge_to_remove[0], edge_to_remove[1])
        except nx.NetworkXNoCycle:
            break
            
    return G

def calculate_cpm(G: nx.DiGraph, hours_per_day: float = 8.0, days_per_week: float = 5.0) -> Tuple[nx.DiGraph, float]:
    """
    Thực hiện các bước tính toán duyệt xuôi (Forward Pass) và duyệt ngược (Backward Pass) trên đồ thị dự án G.

    Sửa đổi trực tiếp đồ thị G bằng cách thêm các thuộc tính CPM cho mỗi nút:
        - 'es': Khởi công Sớm (Early Start)
        - 'ef': Hoàn thành Sớm (Early Finish)
        - 'ls': Khởi công Muộn (Late Start)
        - 'lf': Hoàn thành Muộn (Late Finish)
        - 'total_slack': Dự trữ Toàn phần (LS - ES)
        - 'free_slack': Dự trữ Tự do (min(ES của các task kế nhiệm) - EF)
        - 'is_critical': Giá trị Boolean xác định task có thuộc đường găng hay không

    Args:
        G: Đồ thị dự án DiGraph được xây dựng từ hàm build_project_graph()

    Returns:
        Tuple gồm (G, project_duration)
    """
    # Sao chép đồ thị để tránh các tác động phụ ngoài ý muốn
    G_cpm = G.copy()
    topo_order = list(nx.topological_sort(G_cpm))
    
    def safe_float(v):
        try:
            val = float(v)
            import math
            return 0.0 if math.isnan(val) else val
        except (ValueError, TypeError):
            return 0.0

    # --- 1. Duyệt Xuôi (Forward Pass): Tính ES & EF ---
    for node in topo_order:
        preds = list(G_cpm.predecessors(node))
        d_m = safe_float(G_cpm.nodes[node].get('duration_months', 0.0))
        d_w = safe_float(G_cpm.nodes[node].get('duration_weeks', 0.0))
        d_d = safe_float(G_cpm.nodes[node].get('duration_days', 0.0))
        d_h = safe_float(G_cpm.nodes[node].get('duration_hours', 0.0))
        cal_type = str(G_cpm.nodes[node].get('calendar_type', 'Agenda'))
        dur_calc = calculate_duration_hours(d_m, d_w, d_d, d_h, hours_per_day, days_per_week, cal_type)
        duration = safe_float(G_cpm.nodes[node].get('most_probable_duration', G_cpm.nodes[node].get('duration', dur_calc)))
        
        if not preds:
            G_cpm.nodes[node]['es'] = 0.0
        else:
            max_es = 0.0
            for p in preds:
                edge_data = G_cpm.edges[p, node]
                dep_type = str(edge_data.get('dependency_type', 'FS')).upper()
                lag_h = float(edge_data.get('lag_hours', 0.0))
                
                p_ef = safe_float(G_cpm.nodes[p].get('ef', 0.0))
                p_es = safe_float(G_cpm.nodes[p].get('es', 0.0))
                
                if dep_type == 'SS':
                    v_es = p_es + lag_h
                elif dep_type == 'FF':
                    v_es = p_ef + lag_h - duration
                elif dep_type == 'SF':
                    v_es = p_es + lag_h - duration
                else: # FS
                    v_es = p_ef + lag_h
                    
                if v_es > max_es:
                    max_es = v_es
            G_cpm.nodes[node]['es'] = safe_float(max_es)
            
        G_cpm.nodes[node]['ef'] = G_cpm.nodes[node]['es'] + duration
        
    # Thời gian hoàn thành dự án (Makespan) là giá trị EF lớn nhất của tất cả các nút
    project_duration = max(G_cpm.nodes[n]['ef'] for n in G_cpm.nodes()) if topo_order else 0.0
    
    # --- 2. Duyệt Ngược (Backward Pass): Tính LS & LF ---
    for node in reversed(topo_order):
        succs = list(G_cpm.successors(node))
        d_m = safe_float(G_cpm.nodes[node].get('duration_months', 0.0))
        d_w = safe_float(G_cpm.nodes[node].get('duration_weeks', 0.0))
        d_d = safe_float(G_cpm.nodes[node].get('duration_days', 0.0))
        d_h = safe_float(G_cpm.nodes[node].get('duration_hours', 0.0))
        cal_type = str(G_cpm.nodes[node].get('calendar_type', 'Agenda'))
        dur_calc = calculate_duration_hours(d_m, d_w, d_d, d_h, hours_per_day, days_per_week, cal_type)
        duration = safe_float(G_cpm.nodes[node].get('most_probable_duration', G_cpm.nodes[node].get('duration', dur_calc)))
        
        if not succs:
            G_cpm.nodes[node]['lf'] = project_duration
        else:
            min_lf = float('inf')
            for s in succs:
                edge_data = G_cpm.edges[node, s]
                dep_type = str(edge_data.get('dependency_type', 'FS')).upper()
                lag_h = float(edge_data.get('lag_hours', 0.0))
                
                s_ls = safe_float(G_cpm.nodes[s].get('ls', project_duration))
                s_lf = safe_float(G_cpm.nodes[s].get('lf', project_duration))
                
                # Retrieve successor's computed duration
                s_d_m = safe_float(G_cpm.nodes[s].get('duration_months', 0.0))
                s_d_w = safe_float(G_cpm.nodes[s].get('duration_weeks', 0.0))
                s_d_d = safe_float(G_cpm.nodes[s].get('duration_days', 0.0))
                s_d_h = safe_float(G_cpm.nodes[s].get('duration_hours', 0.0))
                s_cal_type = str(G_cpm.nodes[s].get('calendar_type', 'Agenda'))
                s_dur_calc = calculate_duration_hours(s_d_m, s_d_w, s_d_d, s_d_h, hours_per_day, days_per_week, s_cal_type)
                s_duration = safe_float(G_cpm.nodes[s].get('most_probable_duration', G_cpm.nodes[s].get('duration', s_dur_calc)))

                if dep_type == 'SS':
                    # SS: ES[s] >= ES[node] + lag -> ES[node] <= ES[s] - lag -> LS[node] <= LS[s] - lag -> LF[node] <= LS[s] - lag + duration
                    u_lf = s_ls - lag_h + duration
                elif dep_type == 'FF':
                    # FF: EF[s] >= EF[node] + lag -> LF[node] <= LF[s] - lag
                    u_lf = s_lf - lag_h
                elif dep_type == 'SF':
                    # SF: EF[s] >= ES[node] + lag -> ES[node] <= EF[s] - lag -> LF[node] <= LF[s] - lag + duration
                    u_lf = s_lf - lag_h + duration
                else: # FS
                    # FS: ES[s] >= EF[node] + lag -> EF[node] <= ES[s] - lag -> LF[node] <= LS[s] - lag
                    u_lf = s_ls - lag_h
                    
                if u_lf < min_lf:
                    min_lf = u_lf
            G_cpm.nodes[node]['lf'] = safe_float(min_lf)
            
        G_cpm.nodes[node]['ls'] = G_cpm.nodes[node]['lf'] - duration
        
    # --- 3. Tính toán Dự trữ (Slack) và Đường Găng (Criticality) ---
    for node in G_cpm.nodes():
        node_data = G_cpm.nodes[node]
        node_data['total_slack'] = round(node_data['ls'] - node_data['es'], 6)
        
        succs = list(G_cpm.successors(node))
        if succs:
            node_data['free_slack'] = round(min(G_cpm.nodes[s]['es'] for s in succs) - node_data['ef'], 6)
        else:
            node_data['free_slack'] = round(node_data['lf'] - node_data['ef'], 6)
            
        # Công việc thuộc đường găng nếu dự trữ toàn phần bằng 0
        node_data['is_critical'] = (abs(node_data['total_slack']) < 1e-6)
        
    return G_cpm, project_duration

def get_critical_path(G: nx.DiGraph) -> List[Any]:
    """
    Trích xuất danh sách ID các nút nằm trên đường găng, đã được sắp xếp theo thứ tự tô-pô.
    """
    topo_order = list(nx.topological_sort(G))
    return [node for node in topo_order if G.nodes[node].get('is_critical', False)]

def get_cpm_summary(G: nx.DiGraph, hours_per_day: float = 8.0, days_per_week: float = 5.0) -> List[Dict[str, Any]]:
    """
    Định dạng kết quả tính toán CPM thành cấu trúc bảng phẳng dễ hiển thị.
    """
    summary = []
    topo_order = list(nx.topological_sort(G))
    for node in topo_order:
        data = G.nodes[node]
        cal_type = str(data.get('calendar_type', 'Agenda'))
        dur_fallback = calculate_duration_hours(
            float(data.get('duration_months', 0.0) or 0.0),
            float(data.get('duration_weeks', 0.0) or 0.0),
            float(data.get('duration_days', 0.0) or 0.0),
            float(data.get('duration_hours', 0.0) or 0.0),
            hours_per_day, days_per_week, cal_type
        )
        summary.append({
            'id': node,
            'name': data.get('name', ''),
            'duration': data.get('most_probable_duration', data.get('duration', dur_fallback)),
            'es': data.get('es', 0.0),
            'ef': data.get('ef', 0.0),
            'ls': data.get('ls', 0.0),
            'lf': data.get('lf', 0.0),
            'total_slack': data.get('total_slack', 0.0),
            'free_slack': data.get('free_slack', 0.0),
            'is_critical': data.get('is_critical', False)
        })
    return summary
