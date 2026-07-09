"""
Project State Manager Module for Dynamic Project State Evolution
===================================================================
GLPO - Graph Logistics Project Optimization

Central coordinator for managing project graph evolution over time.
Supports Action Object parsing, state history stack (Undo/Redo/Replay),
Embedding Re-inference via GAT/DAGNN, Monte Carlo re-simulation,
and detailed Before/After comparative analysis for Dashboard UI.
"""

import copy
import time
import torch
import numpy as np
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Dict, Tuple, Any, Optional

from ai_pipeline.src.state.action_model import ActionType, ActionObject
from ai_pipeline.src.state.action_effect_engine import ActionEffectEngine
from ai_pipeline.src.algorithms.monte_carlo import run_monte_carlo_simulation
from ai_pipeline.src.algorithms.cpm import build_project_graph, calculate_cpm

@dataclass
class ProjectState:
    state_id: int
    timestamp: float
    action_applied: Optional[ActionObject]
    tasks: List[Dict[str, Any]]
    dependencies: List[Tuple[str, str]]
    edge_lags: Dict[Tuple[str, str], float]
    resource_capacities: Dict[str, float]
    cpm_results: Dict[str, Any]
    pyg_data: Any
    attention_scores: Dict[str, float]
    dagnn_embeddings: Optional[np.ndarray]
    delay_pred: Dict[str, float]
    sigma_pred: Dict[str, float]
    monte_carlo_results: Dict[str, Any]
    total_cost: float
    direct_cost: float
    indirect_cost: float
    resource_metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "timestamp": self.timestamp,
            "action_applied": self.action_applied.to_dict() if self.action_applied else None,
            "makespan": float(self.cpm_results.get("makespan", 0.0)),
            "critical_path": list(self.cpm_results.get("critical_path", [])),
            "total_cost": float(self.total_cost),
            "direct_cost": float(self.direct_cost),
            "indirect_cost": float(self.indirect_cost),
            "monte_carlo": {
                "mean_makespan": float(self.monte_carlo_results.get("mean_makespan", 0.0)),
                "on_time_prob": float(self.monte_carlo_results.get("P(on_time)", 0.0)),
                "P90": float(self.monte_carlo_results.get("percentiles", {}).get("P90", 0.0))
            },
            "resource_metrics": dict(self.resource_metrics)
        }

class ProjectStateManager:
    """
    Manages the dynamic evolution of the Project Graph across state steps.
    """
    def __init__(
        self,
        initial_project_graph: Any,
        initial_tasks: List[Dict[str, Any]],
        initial_dependencies: List[Tuple[str, str]],
        initial_resource_capacities: Dict[str, float],
        model: Optional[Any] = None,
        device: str = "cpu",
        deadline: Optional[float] = None
    ):
        self.model = model
        self.device = device
        self.project_graph = initial_project_graph
        self.deadline = deadline
        
        # Build Initial State (State 0)
        state_0 = self._build_state(
            state_id=0,
            action_applied=None,
            tasks=initial_tasks,
            dependencies=initial_dependencies,
            edge_lags={},
            resource_capacities=initial_resource_capacities,
            pyg_data=initial_project_graph.data if hasattr(initial_project_graph, 'data') else None
        )
        
        self.history: List[ProjectState] = [state_0]
        self.current_index: int = 0

    def get_current_state(self) -> ProjectState:
        return self.history[self.current_index]

    def apply_action(self, action_obj: ActionObject) -> ProjectState:
        """
        Applies an ActionObject onto the current project state, evolvng the graph,
        re-inferencing embeddings, re-simulating risk, and advancing the state history.
        """
        curr_state = self.get_current_state()
        
        # 1. Simulate Action Effects on tasks, dependencies, and 72-D PyG features
        effect_res = ActionEffectEngine.simulate(
            tasks=curr_state.tasks,
            dependencies=curr_state.dependencies,
            resource_capacities=curr_state.resource_capacities,
            action_obj=action_obj,
            node_to_idx=getattr(self.project_graph, 'node_to_idx', None),
            pyg_data=curr_state.pyg_data
        )
        
        # 2. Update PyG data tensor if available
        updated_pyg_data = copy.deepcopy(curr_state.pyg_data)
        if effect_res["updated_x_tensor"] is not None and updated_pyg_data is not None:
            updated_pyg_data.x = effect_res["updated_x_tensor"]

        # 3. Build Next State (State N+1)
        next_state_id = self.current_index + 1
        new_state = self._build_state(
            state_id=next_state_id,
            action_applied=action_obj,
            tasks=effect_res["updated_tasks"],
            dependencies=effect_res["updated_dependencies"],
            edge_lags=effect_res["updated_edge_lags"],
            resource_capacities=effect_res["updated_resource_capacities"],
            pyg_data=updated_pyg_data,
            cpm_results=effect_res["cpm_results"]
        )

        # 4. Truncate redo stack if any, append new state, and advance index
        self.history = self.history[:self.current_index + 1]
        self.history.append(new_state)
        self.current_index += 1

        print(f"🚀 [ProjectStateManager] Applied Action '{action_obj.action_type.value}' -> Transitioned to State {next_state_id}")
        print(f"   • Makespan: {curr_state.cpm_results.get('makespan', 0):.1f}h → {new_state.cpm_results.get('makespan', 0):.1f}h")
        print(f"   • Cost: {curr_state.total_cost:.2f} → {new_state.total_cost:.2f}")

        return new_state

    def undo(self) -> Optional[ProjectState]:
        """Reverts to the previous state in history if available."""
        if self.current_index > 0:
            self.current_index -= 1
            print(f"↩️ [ProjectStateManager] Undo -> Restored State {self.current_index}")
            return self.get_current_state()
        print("⚠️ [ProjectStateManager] Reached initial state (State 0). Cannot Undo.")
        return None

    def redo(self) -> Optional[ProjectState]:
        """Advances to the next state in history if available."""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            print(f"↪️ [ProjectStateManager] Redo -> Restored State {self.current_index}")
            return self.get_current_state()
        print("⚠️ [ProjectStateManager] Reached latest state. Cannot Redo.")
        return None

    def get_before_after_comparison(
        self,
        before_index: Optional[int] = 0,
        after_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive comparative report between Before state and After state
        for Dashboard display.
        """
        if before_index is None:
            before_index = 0
        if after_index is None:
            after_index = self.current_index

        before_index = max(0, min(before_index, len(self.history) - 1))
        after_index = max(0, min(after_index, len(self.history) - 1))

        st_before = self.history[before_index]
        st_after = self.history[after_index]

        mk_b = float(st_before.cpm_results.get("makespan", 0.0))
        mk_a = float(st_after.cpm_results.get("makespan", 0.0))
        mk_delta = mk_a - mk_b
        mk_pct = (mk_delta / mk_b * 100.0) if mk_b > 0 else 0.0

        cost_b = float(st_before.total_cost)
        cost_a = float(st_after.total_cost)
        cost_delta = cost_a - cost_b
        cost_pct = (cost_delta / cost_b * 100.0) if cost_b > 0 else 0.0

        prob_b = float(st_before.monte_carlo_results.get("P(on_time)", 0.0))
        prob_a = float(st_after.monte_carlo_results.get("P(on_time)", 0.0))
        prob_delta = prob_a - prob_b

        p90_b = float(st_before.monte_carlo_results.get("percentiles", {}).get("P90", 0.0))
        p90_a = float(st_after.monte_carlo_results.get("percentiles", {}).get("P90", 0.0))

        crit_b = set(st_before.cpm_results.get("critical_path", []))
        crit_a = set(st_after.cpm_results.get("critical_path", []))
        newly_critical = list(crit_a - crit_b)
        no_longer_critical = list(crit_b - crit_a)

        # Top attention score shifts
        att_b = st_before.attention_scores
        att_a = st_after.attention_scores
        att_shifts = []
        for t_id in att_a:
            sc_b = att_b.get(t_id, 0.0)
            sc_a = att_a.get(t_id, 0.0)
            att_shifts.append({
                "task_id": t_id,
                "score_before": sc_b,
                "score_after": sc_a,
                "delta": sc_a - sc_b
            })
        att_shifts.sort(key=lambda x: abs(x["delta"]), reverse=True)

        return {
            "before_state_id": st_before.state_id,
            "after_state_id": st_after.state_id,
            "action_applied": st_after.action_applied.to_dict() if st_after.action_applied else None,
            "metrics_comparison": {
                "makespan": {
                    "before": mk_b,
                    "after": mk_a,
                    "delta": mk_delta,
                    "percent_change": mk_pct
                },
                "total_cost": {
                    "before": cost_b,
                    "after": cost_a,
                    "delta": cost_delta,
                    "percent_change": cost_pct
                },
                "on_time_probability": {
                    "before": prob_b,
                    "after": prob_a,
                    "delta": prob_delta
                },
                "P90_makespan": {
                    "before": p90_b,
                    "after": p90_a,
                    "delta": p90_a - p90_b
                }
            },
            "critical_path_evolution": {
                "before_count": len(crit_b),
                "after_count": len(crit_a),
                "newly_critical_tasks": newly_critical,
                "no_longer_critical_tasks": no_longer_critical
            },
            "resource_utilization_evolution": {
                "before": st_before.resource_metrics,
                "after": st_after.resource_metrics
            },
            "top_attention_shifts": att_shifts[:5]
        }

    def get_replay_history(self) -> List[Dict[str, Any]]:
        """Returns sequence of all states for Replay & History UI."""
        return [st.to_dict() for st in self.history]

    # ── PRIVATE HELPERS ──────────────────────────────────────────────────────
    def _build_state(
        self,
        state_id: int,
        action_applied: Optional[ActionObject],
        tasks: List[Dict[str, Any]],
        dependencies: List[Tuple[str, str]],
        edge_lags: Dict[Tuple[str, str], float],
        resource_capacities: Dict[str, float],
        pyg_data: Any,
        cpm_results: Optional[Dict[str, Any]] = None
    ) -> ProjectState:
        
        # 1. Compute CPM if not provided
        if cpm_results is None:
            G = build_project_graph(tasks, dependencies)
            cpm_task_res, static_makespan = calculate_cpm(G)
            idx_to_node = getattr(self.project_graph, 'idx_to_node', {i: str(t['id']) for i, t in enumerate(tasks)})
            is_crit_list = [t.get('is_critical', False) for t in tasks]
            cpm_results = {
                "makespan": static_makespan,
                "critical_path": [str(t['id']) for t in tasks if t.get('is_critical', False)]
            }

        # 2. Re-inference GAT & DAGNN Embeddings (Forward pass ONLY)
        attention_scores = {}
        h_dagnn_np = None
        delay_pred = {}
        sigma_pred = {}

        if self.model is not None and pyg_data is not None:
            self.model.eval()
            with torch.no_grad():
                data_pyg_dev = pyg_data.to(self.device)
                detailed_out = self.model.forward_detailed(data_pyg_dev)
                
            h_dagnn = detailed_out['h_dagnn'].cpu().numpy()
            gate_values = detailed_out['dagnn_info']['gate_values'].cpu().numpy()
            h_dagnn_np = h_dagnn
            
            idx_to_node = getattr(self.project_graph, 'idx_to_node', {i: str(t['id']) for i, t in enumerate(tasks)})
            attention_scores = {idx_to_node[i]: float(gate_values[i]) for i in range(len(gate_values))}
            delay_pred = {idx_to_node[i]: float(np.mean(h_dagnn[i]) * 5.0) for i in range(len(h_dagnn))}
            sigma_pred = {idx_to_node[i]: float(np.std(h_dagnn[i]) * 2.5) for i in range(len(h_dagnn))}
        else:
            # Fallback mock values
            attention_scores = {str(t['id']): 0.5 for t in tasks}
            delay_pred = {str(t['id']): 0.0 for t in tasks}
            sigma_pred = {str(t['id']): 1.0 for t in tasks}

        # 3. Monte Carlo Simulation
        eff_deadline = self.deadline if self.deadline is not None else cpm_results["makespan"] * 1.3
        mc_res = run_monte_carlo_simulation(
            tasks=tasks,
            dependencies=dependencies,
            delay_pred=delay_pred,
            sigma_pred=sigma_pred,
            attention_score=attention_scores,
            gamma=1.5,
            num_iterations=500,
            deadline=eff_deadline
        )

        # 4. Cost Breakdown (Direct & Indirect)
        cost_keys_direct = [
            'internal_labor_cost', 'subcontracting_cost', 'overtime_crashing_cost',
            'material_cost', 'equipment_cost', 'direct_transportation',
            'energy_fuel_cost', 'testing_and_inspection'
        ]
        cost_keys_indirect = [
            'pm_overhead', 'facility_rent', 'utilities', 'communication_cost',
            'internal_training', 'quality_mgmt_overhead'
        ]
        
        direct_cost = sum(sum(float(t.get(k, 0.0)) for k in cost_keys_direct) for t in tasks)
        indirect_cost = sum(sum(float(t.get(k, 0.0)) for k in cost_keys_indirect) for t in tasks)
        total_cost = direct_cost + indirect_cost

        # 5. Resource Metrics
        res_demands = defaultdict(float)
        for t in tasks:
            if 'resource_demand' in t and isinstance(t['resource_demand'], dict):
                for r_k, r_v in t['resource_demand'].items():
                    res_demands[r_k] += float(r_v)
                    
        res_metrics = {
            "total_demand": dict(res_demands),
            "capacities": dict(resource_capacities),
            "utilization_rate": {
                r_k: (res_demands[r_k] / resource_capacities[r_k]) if resource_capacities.get(r_k, 0) > 0 else 0.0
                for r_k in resource_capacities
            }
        }

        return ProjectState(
            state_id=state_id,
            timestamp=time.time(),
            action_applied=action_applied,
            tasks=tasks,
            dependencies=dependencies,
            edge_lags=edge_lags,
            resource_capacities=resource_capacities,
            cpm_results=cpm_results,
            pyg_data=pyg_data,
            attention_scores=attention_scores,
            dagnn_embeddings=h_dagnn_np,
            delay_pred=delay_pred,
            sigma_pred=sigma_pred,
            monte_carlo_results=mc_res,
            total_cost=total_cost,
            direct_cost=direct_cost,
            indirect_cost=indirect_cost,
            resource_metrics=res_metrics
        )
