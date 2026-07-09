"""
Action Effect Engine Module for Dynamic Project State Evolution
================================================================
GLPO - Graph Logistics Project Optimization

Simulates realistic multi-attribute consequences of actions (Crash, Outsource,
Fast Tracking, Resource Leveling) on project tasks, resource pools, graph topology,
and 72-dimensional dynamic feature tensors without retraining AI models.
"""

import copy
import numpy as np
import torch
from collections import defaultdict, deque
from typing import List, Dict, Tuple, Any, Optional

from ai_pipeline.src.state.action_model import ActionType, ActionObject
from ai_pipeline.src.algorithms.cpm import build_project_graph, calculate_cpm

class ActionEffectEngine:
    """
    ActionEffectEngine simulates the realistic domain consequences of applying an action.
    It updates dynamic task parameters, recalculates CPM metrics, adjusts graph edges,
    and updates the 72-dimensional feature tensor for PyG inference.
    """
    
    @staticmethod
    def simulate(
        tasks: List[Dict[str, Any]],
        dependencies: List[Tuple[str, str]],
        resource_capacities: Dict[str, float],
        action_obj: ActionObject,
        node_to_idx: Optional[Dict[str, int]] = None,
        pyg_data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes multi-attribute consequence simulation for an action.
        
        Returns a dictionary containing:
        - updated_tasks: List of updated task dicts
        - updated_dependencies: List of updated (pred, succ) tuples
        - updated_edge_lags: Dict mapping (pred, succ) to lead/lag values (hours)
        - updated_resource_capacities: Dict of updated resource capacities
        - cpm_results: Dict with ES, EF, LS, LF, Float, is_critical, makespan
        - affected_tasks: List of task IDs directly or indirectly changed
        - updated_x_tensor: Updated torch.Tensor [N, 72] for PyG data.x
        """
        updated_tasks = [copy.deepcopy(t) for t in tasks]
        updated_dependencies = list(dependencies)
        updated_edge_lags = {}
        updated_capacities = copy.deepcopy(resource_capacities)
        
        task_map = {str(t['id']): t for t in updated_tasks}
        affected_ids = set(action_obj.affected_tasks)
        
        act_type = action_obj.action_type
        
        # ── 1. APPLY ACTION TYPE CONSEQUENCES ─────────────────────────────────
        if act_type == ActionType.CRASH:
            crash_factor = max(1.1, action_obj.crash_level)
            for t_id in action_obj.affected_tasks:
                if t_id in task_map:
                    t = task_map[t_id]
                    # Duration reduction
                    d_orig = float(t.get('most_probable_duration', t.get('duration', 0.0)))
                    d_new = max(1.0, d_orig / crash_factor)
                    t['most_probable_duration'] = d_new
                    t['duration'] = d_new
                    t['duration_hours'] = d_new
                    
                    # Direct Cost Increase (Overtime, equipment, labor)
                    t['overtime_crashing_cost'] = float(t.get('overtime_crashing_cost', 0)) + float(t.get('internal_labor_cost', 0)) * 0.5
                    t['equipment_cost'] = float(t.get('equipment_cost', 0)) * 1.25
                    t['internal_labor_cost'] = float(t.get('internal_labor_cost', 0)) * 1.25
                    
                    # Indirect Cost Savings (PM overhead reduction)
                    saved_h = max(0.0, d_orig - d_new)
                    t['pm_overhead'] = max(0.0, float(t.get('pm_overhead', 0)) - saved_h * 5.0)
                    
                    # Resource Demand Increase (Crew size)
                    if 'resource_demand' in t and isinstance(t['resource_demand'], dict):
                        for r_k in t['resource_demand']:
                            t['resource_demand'][r_k] = int(round(t['resource_demand'][r_k] * 1.5))
                            
                    # Risk Increase (Overtime fatigue, rework, safety)
                    t['rework_probability'] = min(1.0, float(t.get('rework_probability', 0)) + 0.15)
                    t['occupational_safety_risk'] = min(1.0, float(t.get('occupational_safety_risk', 0)) + 0.20)
                    t['equipment_utilization'] = min(1.0, float(t.get('equipment_utilization', 0)) + 0.25)

        elif act_type == ActionType.OUTSOURCE:
            out_factor = max(1.1, action_obj.outsource_level)
            for t_id in action_obj.affected_tasks:
                if t_id in task_map:
                    t = task_map[t_id]
                    d_orig = float(t.get('most_probable_duration', t.get('duration', 0.0)))
                    d_new = max(1.0, d_orig / out_factor)
                    t['most_probable_duration'] = d_new
                    t['duration'] = d_new
                    t['duration_hours'] = d_new
                    
                    # Cost Redistribution (Internal down, Subcontracting up)
                    t['internal_labor_cost'] = float(t.get('internal_labor_cost', 0)) * 0.4
                    t['subcontracting_cost'] = float(t.get('subcontracting_cost', 0)) + float(t.get('internal_labor_cost', 0)) * 1.5 + d_new * 10.0
                    t['communication_cost'] = float(t.get('communication_cost', 0)) + 50.0
                    t['quality_mgmt_overhead'] = float(t.get('quality_mgmt_overhead', 0)) + 40.0
                    
                    # Internal Resource relief
                    if 'resource_demand' in t and isinstance(t['resource_demand'], dict):
                        for r_k in t['resource_demand']:
                            t['resource_demand'][r_k] = max(1, int(round(t['resource_demand'][r_k] * 0.4)))
                            
                    # Risk Shift (External dependency & technology risk up)
                    t['external_dependency_level'] = min(1.0, float(t.get('external_dependency_level', 0)) + 0.30)
                    t['rework_probability'] = min(1.0, float(t.get('rework_probability', 0)) + 0.10)

        elif act_type == ActionType.FAST_TRACKING:
            overlap = max(0.05, min(0.8, action_obj.overlap_ratio))
            for t_id in action_obj.affected_tasks:
                if t_id in task_map:
                    t = task_map[t_id]
                    # Fast tracking introduces overlap lead time with predecessors
                    for pred, succ in dependencies:
                        if succ == t_id and pred in task_map:
                            pred_d = float(task_map[pred].get('most_probable_duration', task_map[pred].get('duration', 0.0)))
                            lead_time = pred_d * overlap
                            updated_edge_lags[(pred, succ)] = -lead_time  # Negative lag = Lead/Overlap
                            
                    # Concurrent execution increases complexity & rework risk
                    t['technical_complexity'] = min(1.0, float(t.get('technical_complexity', 0)) + 0.20)
                    t['rework_probability'] = min(1.0, float(t.get('rework_probability', 0)) + 0.25)
                    t['cross_functional_coordination'] = min(1.0, float(t.get('cross_functional_coordination', 0)) + 0.30)

        elif act_type == ActionType.RESOURCE_LEVELING:
            for t_id in action_obj.affected_tasks:
                if t_id in task_map:
                    t = task_map[t_id]
                    d_orig = float(t.get('most_probable_duration', t.get('duration', 0.0)))
                    # Slight duration extension to balance peak resources
                    d_new = d_orig * 1.10
                    t['most_probable_duration'] = d_new
                    t['duration'] = d_new
                    t['duration_hours'] = d_new
                    
                    # Balanced resource utilization
                    t['equipment_utilization'] = 0.80
                    t['labor_productivity'] = min(1.0, float(t.get('labor_productivity', 0)) + 0.15)
                    t['hr_stability_risk'] = max(0.0, float(t.get('hr_stability_risk', 0)) - 0.20)
                    
                    if 'resource_demand' in t and isinstance(t['resource_demand'], dict):
                        for r_k in t['resource_demand']:
                            t['resource_demand'][r_k] = max(1, int(round(t['resource_demand'][r_k] * 0.8)))

        # ── 2. RECOMPUTE GRAPH TOPOLOGY & CPM METRICS ─────────────────────────
        G = build_project_graph(updated_tasks, updated_dependencies)
        cpm_task_results, static_makespan = calculate_cpm(G)
        
        # Build node mapping if not supplied
        if node_to_idx is None:
            node_to_idx = {str(t['id']): i for i, t in enumerate(updated_tasks)}
        idx_to_node = {i: n for n, i in node_to_idx.items()}
        num_nodes = len(node_to_idx)
        
        # Calculate ES, EF, LS, LF, Float, Criticality for PyG features
        durations = np.zeros(num_nodes)
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        adj_forward = defaultdict(list)
        adj_backward = defaultdict(list)
        
        for pred, succ in updated_dependencies:
            if pred in node_to_idx and succ in node_to_idx:
                u = node_to_idx[pred]
                v = node_to_idx[succ]
                out_degree[u] += 1
                in_degree[v] += 1
                adj_forward[u].append(v)
                adj_backward[v].append(u)
                
        for t_id, idx in node_to_idx.items():
            if t_id in task_map:
                durations[idx] = float(task_map[t_id].get('most_probable_duration', task_map[t_id].get('duration', 0.0)))
                
        in_deg_temp = in_degree.copy()
        topo_order = []
        queue = deque([i for i in range(num_nodes) if in_deg_temp[i] == 0])
        while queue:
            u = queue.popleft()
            topo_order.append(u)
            for v in adj_forward[u]:
                in_deg_temp[v] -= 1
                if in_deg_temp[v] == 0:
                    queue.append(v)
                    
        ES = np.zeros(num_nodes)
        EF = np.zeros(num_nodes)
        for u in topo_order:
            EF[u] = ES[u] + durations[u]
            for v in adj_forward[u]:
                lag = updated_edge_lags.get((idx_to_node[u], idx_to_node[v]), 0.0)
                ES[v] = max(ES[v], EF[u] + lag)
                
        LS = np.zeros(num_nodes)
        LF = np.zeros(num_nodes)
        project_dur = max(EF) if len(EF) > 0 else 0
        LF.fill(project_dur)
        for u in reversed(topo_order):
            LS[u] = LF[u] - durations[u]
            for p in adj_backward[u]:
                lag = updated_edge_lags.get((idx_to_node[p], idx_to_node[u]), 0.0)
                LF[p] = min(LF[p], LS[u] - lag)
                
        total_float = LS - ES
        is_critical = (np.abs(total_float) <= 1e-4).astype(float)
        
        path_length = np.zeros(num_nodes)
        for u in topo_order:
            for v in adj_forward[u]:
                path_length[v] = max(path_length[v], path_length[u] + 1)
                
        cpm_results = {
            "makespan": float(project_dur),
            "ES": {idx_to_node[i]: float(ES[i]) for i in range(num_nodes)},
            "EF": {idx_to_node[i]: float(EF[i]) for i in range(num_nodes)},
            "LS": {idx_to_node[i]: float(LS[i]) for i in range(num_nodes)},
            "LF": {idx_to_node[i]: float(LF[i]) for i in range(num_nodes)},
            "total_float": {idx_to_node[i]: float(total_float[i]) for i in range(num_nodes)},
            "is_critical": {idx_to_node[i]: bool(is_critical[i]) for i in range(num_nodes)},
            "critical_path": [idx_to_node[i] for i in range(num_nodes) if is_critical[i] == 1.0]
        }

        # ── 3. UPDATE 72-DIM FEATURE TENSOR (PyG data.x) ──────────────────────
        updated_x = None
        if pyg_data is not None and hasattr(pyg_data, 'x'):
            x_mat = pyg_data.x.clone()
            for t_id, idx in node_to_idx.items():
                if t_id in task_map:
                    t = task_map[t_id]
                    
                    # Update dynamic features
                    x_mat[idx, 1] = float(t.get('duration_months', 0))
                    x_mat[idx, 2] = float(t.get('duration_weeks', 0))
                    x_mat[idx, 3] = float(t.get('duration_days', 0))
                    x_mat[idx, 4] = float(t.get('most_probable_duration', t.get('duration', 0)))
                    
                    # Direct Costs (G1: 7-14)
                    x_mat[idx, 7] = float(t.get('internal_labor_cost', 0))
                    x_mat[idx, 8] = float(t.get('subcontracting_cost', 0))
                    x_mat[idx, 9] = float(t.get('overtime_crashing_cost', 0))
                    x_mat[idx, 11] = float(t.get('equipment_cost', 0))
                    
                    # Indirect Costs (G2: 15-20)
                    x_mat[idx, 15] = float(t.get('pm_overhead', 0))
                    x_mat[idx, 18] = float(t.get('communication_cost', 0))
                    x_mat[idx, 20] = float(t.get('quality_mgmt_overhead', 0))
                    
                    # Resources (G7: 37-41)
                    tot_req = 0.0
                    if 'resource_demand' in t and isinstance(t['resource_demand'], dict):
                        tot_req = float(sum(t['resource_demand'].values()))
                    x_mat[idx, 37] = tot_req
                    x_mat[idx, 40] = float(t.get('equipment_utilization', 0))
                    
                    # Risks (G9: 42-48)
                    x_mat[idx, 42] = float(t.get('technical_complexity', 0))
                    x_mat[idx, 43] = float(t.get('rework_probability', 0))
                    x_mat[idx, 44] = float(t.get('external_dependency_level', 0))
                    
                    # Org & ESG (G11/12: 52-54)
                    x_mat[idx, 52] = float(t.get('hr_stability_risk', 0))
                    x_mat[idx, 54] = float(t.get('occupational_safety_risk', 0))
                    
                    # G8: Recomputed Topological Features (63-67)
                    x_mat[idx, 63] = float(in_degree[idx])
                    x_mat[idx, 64] = float(out_degree[idx])
                    x_mat[idx, 65] = float(is_critical[idx])
                    x_mat[idx, 66] = float(total_float[idx])
                    x_mat[idx, 67] = float(path_length[idx])
            updated_x = x_mat

        # Add downstream affected tasks to affected_ids
        for t_id in list(affected_ids):
            if t_id in node_to_idx:
                u = node_to_idx[t_id]
                for v in adj_forward[u]:
                    affected_ids.add(idx_to_node[v])

        return {
            "updated_tasks": updated_tasks,
            "updated_dependencies": updated_dependencies,
            "updated_edge_lags": updated_edge_lags,
            "updated_resource_capacities": updated_capacities,
            "cpm_results": cpm_results,
            "affected_tasks": list(affected_ids),
            "updated_x_tensor": updated_x
        }
