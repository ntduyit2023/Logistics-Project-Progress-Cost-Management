import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
from ai_pipeline.models.moi.utils.calendar_engine import (
    WorkingCalendarEngine
)

def compute_ai_critical_path(
    tasks: List[Dict[str, Any]],
    dependencies: List[Tuple[Any, Any, Dict[str, Any]]],
    ai_task_preds: Dict[str, Dict[str, float]],
    calendar_engine: Optional[WorkingCalendarEngine] = None
) -> Tuple[Dict[str, float], List[str]]:
    """
    Tính toán Forward / Backward CPM pass dự báo để xác định Đường Găng AI.

    Hàm này tạo một đồ thị có hướng (Directed Graph) từ danh sách công việc và quan hệ phụ thuộc.
    Thời lượng công việc được tính toán dựa trên (1) Lịch Agenda thực tế và (2) Kết quả dự báo
    thời gian trễ (delay) từ AI model (HGT).

    Từ đó, hàm thực hiện 2 lượt quét:
        - Forward Pass: Tính mốc sớm nhất có thể khởi công (ES - Early Start) và hoàn thành (EF - Early Finish).
        - Backward Pass: Tính mốc trễ nhất được phép khởi công (LS - Late Start) và hoàn thành (LF - Late Finish).
    Độ trễ cho phép (Slack) = LS - ES. Nếu Slack <= 0, công việc nằm trên Đường Găng (Critical Path).

    Args:
        tasks (List[Dict[str, Any]]): Danh sách công việc gốc.
        dependencies (List[Tuple[Any, Any, Dict[str, Any]]]): Quan hệ logic nối tiếp.
        ai_task_preds (Dict[str, Dict[str, float]]): Kết quả dự báo AI (duration_factor, expected_delay).
        calendar_engine (Optional[WorkingCalendarEngine]): Động cơ lịch làm việc để tính số giờ gốc.

    Returns:
        Tuple[Dict[str, float], List[str]]: 
            - Từ điển mapping task_id -> slack time (giờ).
            - Danh sách các ID công việc nằm trên Đường Găng (slack <= 1.0h).
    """
    # =========================================================================
    # BƯỚC 1: XÂY DỰNG ĐỒ THỊ VÀ TÍNH THỜI LƯỢNG MỚI (AI DỰ BÁO)
    # =========================================================================
    if calendar_engine is None:
        calendar_engine = WorkingCalendarEngine()

    G = nx.DiGraph()
    task_map = {}
    
    for t in tasks:
        t_id = str(t.get('id', t.get('task_id', '')))
        task_map[t_id] = t
        base_dur = calendar_engine.calculate_task_total_hours(t)
        
        preds = ai_task_preds.get(t_id, {})
        dur_factor = preds.get('duration_factor', 1.0)
        delay_h = preds.get('expected_delay', 0.0)
        
        ai_dur = max(1.0, base_dur * dur_factor + delay_h)
        G.add_node(t_id, duration=ai_dur, base_dur=base_dur)

    for pred, succ, attr in dependencies:
        p_id, s_id = str(pred), str(succ)
        if p_id in G and s_id in G:
            lag = float((attr or {}).get('lag_hours', 0.0))
            G.add_edge(p_id, s_id, lag=lag)

    try:
        topo_order = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        # Nếu có chu trình (vòng lặp) làm hỏng DAG, fallback duyệt tuần tự
        topo_order = [str(t.get('id', t.get('task_id', ''))) for t in tasks]

    # =========================================================================
    # BƯỚC 2: FORWARD PASS (TÍNH ES, EF)
    # =========================================================================

    es = {node: 0.0 for node in G.nodes()}
    ef = {node: G.nodes[node]['duration'] for node in G.nodes()}

    for node in topo_order:
        start_time = es[node]
        ef[node] = start_time + G.nodes[node]['duration']
        for succ in G.successors(node):
            lag = G.edges[node, succ].get('lag', 0.0)
            es[succ] = max(es[succ], ef[node] + lag)

    max_makespan = max(ef.values()) if ef else 0.0

    # =========================================================================
    # BƯỚC 3: BACKWARD PASS (TÍNH LS, LF)
    # =========================================================================

    lf = {node: max_makespan for node in G.nodes()}
    ls = {node: max_makespan - G.nodes[node]['duration'] for node in G.nodes()}

    for node in reversed(topo_order):
        for pred in G.predecessors(node):
            lag = G.edges[pred, node].get('lag', 0.0)
            lf[pred] = min(lf[pred], ls[node] - lag)
            ls[pred] = lf[pred] - G.nodes[pred]['duration']

    # =========================================================================
    # BƯỚC 4: TÍNH ĐỘ TRỄ CHO PHÉP (SLACK) VÀ TRÍCH XUẤT ĐƯỜNG GĂNG
    # =========================================================================
    slack = {node: ls[node] - es[node] for node in G.nodes()}
    critical_tasks = [node for node, s in slack.items() if s <= 1.0]

    return slack, critical_tasks