import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
from ai_pipeline.models.moi.domain_normalizers import (
    calculate_task_total_hours,
    WorkingCalendarEngine
)

def compute_ai_critical_path(
    tasks: List[Dict[str, Any]],
    dependencies: List[Tuple[Any, Any, Dict[str, Any]]],
    ai_task_preds: Dict[str, Dict[str, float]],
    calendar_engine: Optional[WorkingCalendarEngine] = None
) -> Tuple[Dict[str, float], List[str]]:
    """
    Tính toán Forward / Backward CPM pass dựa trên Lịch Agenda (WorkingCalendarEngine) và thời lượng HGT AI dự báo để xác định Đường Găng AI.
    """
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
        topo_order = [str(t.get('id', t.get('task_id', ''))) for t in tasks]

    es = {node: 0.0 for node in G.nodes()}
    ef = {node: G.nodes[node]['duration'] for node in G.nodes()}

    for node in topo_order:
        start_time = es[node]
        ef[node] = start_time + G.nodes[node]['duration']
        for succ in G.successors(node):
            lag = G.edges[node, succ].get('lag', 0.0)
            es[succ] = max(es[succ], ef[node] + lag)

    max_makespan = max(ef.values()) if ef else 0.0

    lf = {node: max_makespan for node in G.nodes()}
    ls = {node: max_makespan - G.nodes[node]['duration'] for node in G.nodes()}

    for node in reversed(topo_order):
        for pred in G.predecessors(node):
            lag = G.edges[pred, node].get('lag', 0.0)
            lf[pred] = min(lf[pred], ls[node] - lag)
            ls[pred] = lf[pred] - G.nodes[pred]['duration']

    slack = {node: max(0.0, ls[node] - es[node]) for node in G.nodes()}
    critical_tasks = [node for node, s_val in slack.items() if s_val <= 1e-3]

    return slack, critical_tasks