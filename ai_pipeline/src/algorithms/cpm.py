"""
Mô-đun CPM (Critical Path Method) - Phân Tích Lập Lịch Tĩnh
============================================================
Mô-đun này triển khai Phương pháp Đường Găng (CPM) cổ điển sử dụng NetworkX.
Nó tính toán Khởi công Sớm (ES), Hoàn thành Sớm (EF), Khởi công Muộn (LS), Hoàn thành Muộn (LF),
Dự trữ Toàn phần (Total Slack), Dự trữ Tự do (Free Slack), và xác định Đường găng (Critical Path) của đồ thị dự án.
"""

import networkx as nx
from typing import Dict, List, Tuple, Any, Optional

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
    for pred, succ in dependencies:
        # Bỏ qua nếu thông tin nút bị rỗng hoặc NaN
        if not pred or not succ or str(pred).lower() == 'nan' or str(succ).lower() == 'nan':
            continue
        if pred not in G.nodes:
            raise ValueError(f"Task đi trước '{pred}' không tồn tại trong danh sách công việc.")
        if succ not in G.nodes:
            raise ValueError(f"Task đi sau '{succ}' không tồn tại trong danh sách công việc.")
        G.add_edge(pred, succ)
        
    # Phát hiện chu trình
    if not nx.is_directed_acyclic_graph(G):
        cycles = list(nx.simple_cycles(G))
        raise ValueError(f"Đồ thị phụ thuộc chứa chu trình! Các chu trình phát hiện: {cycles}")
        
    return G

def calculate_cpm(G: nx.DiGraph) -> Tuple[nx.DiGraph, float]:
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
    
    # --- 1. Duyệt Xuôi (Forward Pass): Tính ES & EF ---
    for node in topo_order:
        preds = list(G_cpm.predecessors(node))
        duration = G_cpm.nodes[node].get('most_probable_duration', G_cpm.nodes[node].get('duration', 0.0))
        
        if not preds:
            G_cpm.nodes[node]['es'] = 0.0
        else:
            G_cpm.nodes[node]['es'] = float(max(G_cpm.nodes[p]['ef'] for p in preds))
            
        G_cpm.nodes[node]['ef'] = G_cpm.nodes[node]['es'] + float(duration)
        
    # Thời gian hoàn thành dự án (Makespan) là giá trị EF lớn nhất của tất cả các nút
    project_duration = max(G_cpm.nodes[n]['ef'] for n in G_cpm.nodes()) if topo_order else 0.0
    
    # --- 2. Duyệt Ngược (Backward Pass): Tính LS & LF ---
    for node in reversed(topo_order):
        succs = list(G_cpm.successors(node))
        duration = G_cpm.nodes[node].get('most_probable_duration', G_cpm.nodes[node].get('duration', 0.0))
        
        if not succs:
            G_cpm.nodes[node]['lf'] = project_duration
        else:
            G_cpm.nodes[node]['lf'] = float(min(G_cpm.nodes[s]['ls'] for s in succs))
            
        G_cpm.nodes[node]['ls'] = G_cpm.nodes[node]['lf'] - float(duration)
        
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

def get_cpm_summary(G: nx.DiGraph) -> List[Dict[str, Any]]:
    """
    Định dạng kết quả tính toán CPM thành cấu trúc bảng phẳng dễ hiển thị.
    """
    summary = []
    topo_order = list(nx.topological_sort(G))
    for node in topo_order:
        data = G.nodes[node]
        summary.append({
            'id': node,
            'name': data.get('name', ''),
            'duration': data.get('most_probable_duration', data.get('duration', 0.0)),
            'es': data.get('es', 0.0),
            'ef': data.get('ef', 0.0),
            'ls': data.get('ls', 0.0),
            'lf': data.get('lf', 0.0),
            'total_slack': data.get('total_slack', 0.0),
            'free_slack': data.get('free_slack', 0.0),
            'is_critical': data.get('is_critical', False)
        })
    return summary
