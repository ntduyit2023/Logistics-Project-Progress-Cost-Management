"""
Monte Carlo CPM Simulation Engine
=================================
Thư mục: ai_pipeline/models/moi/monte_carlo_cpm.py

Chức năng:
    Mô phỏng xác suất tiến độ Beta-PERT kết hợp đường găng CPM.
    Hỗ trợ:
        - Tùy chỉnh linh hoạt số vòng mô phỏng (1,000 / 5,000 / 10,000 runs).
        - Đóng góp từ trọng số dự báo của AI (Duration Factor & Expected Delay & Sigma).
        - Tính toán chỉ số găng Criticality Index (CI%) cho từng task.
        - Phân tích rủi ro thời gian P50, P80, P95.
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional


def sample_beta_pert(a: float, m: float, b: float) -> float:
    """
    Lấy mẫu giá trị từ phân phối xác suất Beta-PERT.
    
    Phân phối Beta-PERT là xương sống của quản trị rủi ro dự án, 
    giúp mô phỏng thời lượng thi công dựa trên 3 điểm ước lượng:
    Lạc quan (Optimistic), Khả dĩ nhất (Most Likely), và Bi quan (Pessimistic).

    Args:
        a (float): Cận dưới - Thời gian lạc quan nhất (Optimistic).
        m (float): Đỉnh phân phối - Thời gian khả dĩ nhất (Most Likely).
        b (float): Cận trên - Thời gian bi quan nhất (Pessimistic).

    Returns:
        float: Giá trị thời lượng được lấy mẫu ngẫu nhiên.
    """
    if a >= b:
        return a
    alpha = 1 + 4 * (m - a) / (b - a)
    beta = 1 + 4 * (b - m) / (b - a)
    sample = np.random.beta(alpha, beta)
    return a + (b - a) * sample


from ai_pipeline.models.moi.utils.calendar_engine import WorkingCalendarEngine, calculate_task_total_hours


class MonteCarloCPMEngine:
    """
    Bộ mô phỏng Monte Carlo kết hợp CPM (Critical Path Method) cho dự án.

    Nhiệm vụ của module này là chạy giả lập (Simulation) hàng nghìn kịch bản (vòng lặp) 
    tiến độ thi công. Trong mỗi vòng lặp, thời lượng của từng công việc sẽ bị "làm nhiễu"
    dựa trên dự báo của AI (Sigma/Delay) thông qua phân phối Beta-PERT.
    
    Sau Hàng nghìn lần tính toán CPM Forward-Pass, hệ thống sẽ thống kê:
        - Criticality Index (CI%): Tỷ lệ % số lần một công việc trở thành Nút thắt (Nằm trên Đường găng).
        - Phân phối độ trễ toàn dự án (P50, P80, P90, P95).
    """
    def __init__(
        self,
        tasks: List[Dict[str, Any]],
        dependencies: List[Tuple[Any, Any, Dict[str, Any]]],
        calendar_engine: Optional[WorkingCalendarEngine] = None,
        weekly_schedule: Optional[Dict[Any, float]] = None,
        holidays_list: Optional[list] = None
    ):
        self.tasks = tasks
        self.dependencies = dependencies
        
        self.calendar_engine = calendar_engine or WorkingCalendarEngine(
            weekly_schedule=weekly_schedule,
            holidays_list=holidays_list
        )
        self.hours_per_day = self.calendar_engine.avg_hours_per_day
        self.days_per_week = float(self.calendar_engine.working_days_per_week or 5.0)
        
        # Dựng đồ thị DAG
        self.graph = nx.DiGraph()
        for t in tasks:
            t_id = str(t.get('id', t.get('task_id', '')))
            self.graph.add_node(t_id, **t)
        for pred, succ, attr in dependencies:
            p_id, s_id = str(pred), str(succ)
            if p_id in self.graph and s_id in self.graph:
                self.graph.add_edge(p_id, s_id, **(attr or {}))

    def run_simulation(
        self,
        num_iterations: int = 10000,
        ai_preds: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Khởi chạy tiến trình mô phỏng Monte Carlo đa vòng lặp.

        Args:
            num_iterations (int): Số lượng vòng lặp giả lập (khuyến nghị >= 1000).
            ai_preds (Optional[Dict]): Dự báo nhiễu từ AI (expected_delay, uncertainty_sigma).

        Returns:
            Dict[str, Any]: Object chứa mảng mẫu makespan `samples`, Criticality Index `ci`, 
                            và các ngưỡng rủi ro xác suất P50, P80, P95.
        """
        # =========================================================================
        # BƯỚC 1: KHỞI TẠO BỘ BIẾN ĐẾM
        # =========================================================================
        num_iterations = max(100, int(num_iterations))
        task_ids = list(self.graph.nodes())
        
        # Ma trận lưu kết quả mô phỏng
        makespan_samples = np.zeros(num_iterations)
        critical_counts = {t_id: 0 for t_id in task_ids}
        
        topo_order = list(nx.topological_sort(self.graph))
        
        # =========================================================================
        # BƯỚC 2: VÒNG LẶP MONTE CARLO CHÍNH (SIMULATION LOOP)
        # =========================================================================
        for i in range(num_iterations):
            # 1. Lấy mẫu thời lượng cho từng task
            sampled_durations = {}
            for t_id in task_ids:
                node_data = self.graph.nodes[t_id]
                base_dur = self.calendar_engine.calculate_task_total_hours(node_data)
                
                # Áp dụng dự báo AI nếu có
                if ai_preds and t_id in ai_preds:
                    pred = ai_preds[t_id]
                    factor = pred.get('duration_factor', 1.0)
                    delay = pred.get('expected_delay', 0.0)
                    sigma = pred.get('uncertainty_sigma', 0.1)
                else:
                    factor, delay, sigma = 1.0, 0.0, 0.1
                    
                m = base_dur * factor + delay
                a = max(0.5, m * (1.0 - 2.0 * sigma))
                b = m * (1.0 + 3.0 * sigma)
                
                sampled_durations[t_id] = sample_beta_pert(a, m, b)
                
            # 2. Tính Forward Pass (Early Start/Finish)
            # =========================================================================
            # BƯỚC 2.1: TÍNH TOÁN CPM FORWARD PASS CHO 1 VÒNG LẶP
            # =========================================================================
            es = {node: 0.0 for node in topo_order}
            ef = {t_id: 0.0 for t_id in task_ids}
            
            for t_id in topo_order:
                preds = list(self.graph.predecessors(t_id))
                if not preds:
                    es[t_id] = 0.0
                else:
                    max_pred = 0.0
                    for p in preds:
                        edge_data = self.graph.get_edge_data(p, t_id) or {}
                        lag = float(edge_data.get('lag_hours', 0.0))
                        dep_type = str(edge_data.get('dependency_type', 'FS')).upper()
                        
                        if dep_type == 'SS':
                            v_es = es[p] + lag
                        elif dep_type == 'FF':
                            v_es = ef[p] + lag - sampled_durations[t_id]
                        elif dep_type == 'SF':
                            v_es = es[p] + lag - sampled_durations[t_id]
                        else:
                            v_es = ef[p] + lag
                            
                        max_pred = max(max_pred, v_es)
                    es[t_id] = max_pred
                ef[t_id] = es[t_id] + sampled_durations[t_id]
                
            project_makespan = max(ef.values()) if ef else 0.0
            makespan_samples[i] = project_makespan
            
            # 3. Tính Backward Pass tìm đường găng
            ls = {t_id: project_makespan for t_id in task_ids}
            lf = {t_id: project_makespan for t_id in task_ids}
            
            for t_id in reversed(topo_order):
                succs = list(self.graph.successors(t_id))
                if succs:
                    min_succ = float('inf')
                    for s in succs:
                        edge_data = self.graph.get_edge_data(t_id, s) or {}
                        lag = float(edge_data.get('lag_hours', 0.0))
                        dep_type = str(edge_data.get('dependency_type', 'FS')).upper()
                        
                        if dep_type == 'SS':
                            u_lf = ls[s] - lag + sampled_durations[t_id]
                        elif dep_type == 'FF':
                            u_lf = lf[s] - lag
                        elif dep_type == 'SF':
                            u_lf = lf[s] - lag + sampled_durations[t_id]
                        else:
                            u_lf = ls[s] - lag
                            
                        min_succ = min(min_succ, u_lf)
                    lf[t_id] = min_succ
                ls[t_id] = lf[t_id] - sampled_durations[t_id]
                
                # Slack = LS - ES
                slack = ls[t_id] - es[t_id]
                if abs(slack) < 1e-4:
                    critical_counts[t_id] += 1
                    
        # 4. Tổng hợp chỉ số thống kê
        criticality_index = {t_id: round(count / num_iterations * 100.0, 2) for t_id, count in critical_counts.items()}
        
        return {
            'num_iterations': num_iterations,
            'makespan_mean': float(np.mean(makespan_samples)),
            'makespan_std': float(np.std(makespan_samples)),
            'p50': float(np.percentile(makespan_samples, 50)),
            'p80': float(np.percentile(makespan_samples, 80)),
            'p95': float(np.percentile(makespan_samples, 95)),
            'criticality_index': criticality_index
        }
