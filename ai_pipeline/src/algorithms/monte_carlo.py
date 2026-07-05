"""
Mô-đun Mô Phỏng Monte Carlo - Phân Tích Xác Suất Tiến Độ (Cấp độ 2)
===================================================================
Mô-đun này thực hiện mô phỏng xác suất trên đồ thị dự án để đánh giá rủi ro
tiến độ dưới sự tác động của các yếu tố bất định. Mô-đun tích hợp đầu ra từ các mô hình AI:
    - Thời lượng kỳ vọng và độ bất định của từng task từ mô hình DAGNN.
    - Điểm chú ý nhạy cảm cấp độ nút từ mô hình GAT (đóng vai trò là hệ số nhân rủi ro động).
Mô phỏng tính toán xác suất hoàn thành dự án đúng hạn và chỉ số găng (xác suất nằm trên đường găng)
cho từng công việc cụ thể.
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional

def sample_pert_beta(a: float, m: float, b: float) -> float:
    """
    Lấy mẫu một giá trị đơn lẻ từ phân phối Beta-PERT.

    Args:
        a: Thời lượng lạc quan (tối thiểu)
        m: Thời lượng khả thi nhất (yếu vị/mode)
        b: Thời lượng bi quan (tối đa)
    """
    if a >= b:
        return a
    
    # Tính toán các tham số hình dạng alpha và beta cho phân phối Beta
    alpha = 1 + 4 * (m - a) / (b - a)
    beta = 1 + 4 * (b - m) / (b - a)
    
    # Lấy mẫu từ phân phối beta tiêu chuẩn và co giãn về khoảng [a, b]
    sample = np.random.beta(alpha, beta)
    return a + (b - a) * sample

def run_monte_carlo_simulation(
    tasks: List[Dict[str, Any]],
    dependencies: List[Tuple[Any, Any]],
    delay_pred: Optional[Dict[Any, float]] = None,
    sigma_pred: Optional[Dict[Any, float]] = None,
    attention_score: Optional[Dict[Any, float]] = None,
    gamma: float = 1.0,
    num_iterations: int = 10000,
    deadline: Optional[float] = None
) -> Dict[str, Any]:
    """
    Chạy mô phỏng Monte Carlo Cấp độ 2 trên đồ thị dự án.

    Args:
        tasks: Danh sách các dict của task (bắt buộc chứa 'id' và 'duration')
        dependencies: Danh sách các cạnh phụ thuộc (pred_id, succ_id)
        delay_pred: Thời gian trễ kỳ vọng dự báo từ DAGNN (mặc định: 0.0)
        sigma_pred: Độ bất định của task dự báo từ DAGNN (mặc định: 0.1 * duration)
        attention_score: Điểm chú ý của nút từ GAT (mặc định: 0.0)
        gamma: Hệ số nhạy cảm rủi ro đối với điểm chú ý của GAT
        num_iterations: Số lượng lượt mô phỏng lấy mẫu
        deadline: Hạn chót dự án để tính xác suất đúng hạn (mặc định: mốc P90 của baseline)

    Returns:
        Dict chứa kết quả mô phỏng:
            - 'P(on_time)': Xác suất hoàn thành trước hạn chót (deadline)
            - 'makespans': Mảng lưu Makespan của tất cả các lượt mô phỏng
            - 'mean_makespan': Thời gian hoàn thành trung bình
            - 'std_makespan': Độ lệch chuẩn của thời gian hoàn thành
            - 'percentiles': Dict chứa các mốc phân vị thời gian hoàn thành P50, P75, P85, P90, P95
            - 'criticality_indices': Dict ánh xạ task ID sang chỉ số găng thực tế [0.0, 1.0]
            - 'task_pert_params': Dict lưu cấu hình tham số (a_i, m_i, b_i) đã sử dụng cho từng task
    """
    # 1. Dựng đồ thị cơ sở và trích xuất thứ tự sắp xếp tô-pô
    G = nx.DiGraph()
    for task in tasks:
        G.add_node(task['id'], **task)
    for pred, succ in dependencies:
        if not pred or not succ or str(pred).lower() == 'nan' or str(succ).lower() == 'nan':
            continue
        G.add_edge(pred, succ)
        
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("Đồ thị dự án chứa chu trình; không thể chạy mô phỏng Monte Carlo.")
        
    topo_order = list(nx.topological_sort(G))
    N = len(topo_order)
    
    # 2. Ánh xạ node ID sang chỉ số mảng (index) để tối ưu hóa tốc độ tính toán vector
    node_to_idx = {node: idx for idx, node in enumerate(topo_order)}
    idx_to_node = {idx: node for idx, node in enumerate(topo_order)}
    
    # Tính toán trước danh sách chỉ số các nút đi trước (predecessors) và đi sau (successors)
    preds_indices = [
        [node_to_idx[p] for p in G.predecessors(node)]
        for node in topo_order
    ]
    succs_indices = [
        [node_to_idx[s] for s in G.successors(node)]
        for node in topo_order
    ]
    
    # 3. Tính toán trước các tham số phân phối PERT-Beta cho từng task
    # Khởi tạo các vector a_i, m_i, b_i kích thước N
    a_vec = np.zeros(N)
    m_vec = np.zeros(N)
    b_vec = np.zeros(N)
    task_pert_params = {}
    
    for idx, node in enumerate(topo_order):
        task_data = G.nodes[node]
        planned_duration = float(task_data.get('most_probable_duration', task_data.get('duration', 0.0)))
        
        # Đọc thời lượng lạc quan và bi quan thực tế từ dữ liệu
        o_val = float(task_data.get('optimistic_duration', task_data.get('optimistic_time', planned_duration)))
        p_val = float(task_data.get('pessimistic_duration', task_data.get('pessimistic_time', planned_duration)))
        default_sigma = (p_val - o_val) / 6.0 if p_val > o_val else 0.1 * planned_duration
        
        # Lấy dự báo của DAGNN và GAT với các giá trị fallback dự phòng
        delay_val = delay_pred.get(node, 0.0) if delay_pred else 0.0
        d_val = planned_duration + delay_val
        sigma_val = sigma_pred.get(node, default_sigma) if sigma_pred else default_sigma
        attn_val = attention_score.get(node, 0.0) if attention_score else 0.0
        
        # Công thức PERT-Beta Cấp độ 2: Attention của GAT kéo dài biên bi quan
        a_i = max(0.0, d_val - 2.0 * sigma_val)
        m_i = d_val
        b_i = d_val + 2.0 * sigma_val * (1.0 + gamma * attn_val)
        
        # Ràng buộc kiểm tra nếu đầu ra bị bất thường
        if a_i >= b_i:
            b_i = a_i + 1e-5
            if m_i < a_i or m_i > b_i:
                m_i = (a_i + b_i) / 2.0
                
        a_vec[idx] = a_i
        m_vec[idx] = m_i
        b_vec[idx] = b_i
        task_pert_params[node] = (a_i, m_i, b_i)

    # 4. Khởi tạo mảng lưu dữ liệu mô phỏng
    makespans = np.zeros(num_iterations)
    critical_counts = np.zeros(N, dtype=int)
    
    # 5. Vòng lặp mô phỏng cốt lõi
    for k in range(num_iterations):
        # Lấy mẫu ngẫu nhiên thời lượng cho toàn bộ các task
        sampled_durations = np.zeros(N)
        for i in range(N):
            sampled_durations[i] = sample_pert_beta(a_vec[i], m_vec[i], b_vec[i])
            
        # Thuật toán duyệt xuôi CPM Forward Pass nhanh
        ef = np.zeros(N)
        es = np.zeros(N)
        for i in range(N):
            preds = preds_indices[i]
            if not preds:
                es[i] = 0.0
            else:
                es[i] = max(ef[p] for p in preds)
            ef[i] = es[i] + sampled_durations[i]
            
        makespan = max(ef) if N > 0 else 0.0
        makespans[k] = makespan
        
        # Thuật toán duyệt ngược CPM Backward Pass nhanh
        lf = np.zeros(N)
        ls = np.zeros(N)
        for i in reversed(range(N)):
            succs = succs_indices[i]
            if not succs:
                lf[i] = makespan
            else:
                lf[i] = min(ls[s] for s in succs)
            ls[i] = lf[i] - sampled_durations[i]
            
        # Xác định các task găng trong lượt mô phỏng này (Total Slack ~ 0)
        total_slack = lf - ef
        critical_mask = total_slack < 1e-5
        critical_counts += critical_mask.astype(int)
        
    # 6. Tổng hợp các chỉ số đầu ra
    mean_makespan = float(np.mean(makespans))
    std_makespan = float(np.std(makespans))
    
    percentiles = {
        'P50': float(np.percentile(makespans, 50)),
        'P75': float(np.percentile(makespans, 75)),
        'P85': float(np.percentile(makespans, 85)),
        'P90': float(np.percentile(makespans, 90)),
        'P95': float(np.percentile(makespans, 95))
    }
    
    # Tính xác suất hoàn thành dự án trước hạn
    if deadline is None:
        # Nếu không chỉ định deadline, mặc định lấy mốc P90
        deadline = percentiles['P90']
    p_on_time = float(np.sum(makespans <= deadline) / num_iterations)
    
    # Tính toán chỉ số găng (Criticality Index) của từng task
    criticality_indices = {
        idx_to_node[i]: float(critical_counts[i] / num_iterations)
        for i in range(N)
    }
    
    # Sắp xếp mảng để tạo dữ liệu vẽ biểu đồ phân phối tích lũy CDF
    sorted_makespans = np.sort(makespans)
    cdf_x = sorted_makespans.tolist()
    cdf_y = np.linspace(0.0, 1.0, num_iterations).tolist()
    
    return {
        'P(on_time)': p_on_time,
        'deadline': deadline,
        'mean_makespan': mean_makespan,
        'std_makespan': std_makespan,
        'percentiles': percentiles,
        'criticality_indices': criticality_indices,
        'task_pert_params': task_pert_params,
        'cdf_data': {
            'x': cdf_x[::max(1, num_iterations // 500)],  # Thu nhỏ số điểm dữ liệu gửi lên UI
            'y': cdf_y[::max(1, num_iterations // 500)]
        }
    }
