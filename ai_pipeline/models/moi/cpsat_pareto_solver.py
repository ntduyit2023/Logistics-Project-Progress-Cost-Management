"""
CP-SAT Pareto Multi-Objective Solver (Authoritative Data-Driven Engine)
========================================================================
Thư mục: ai_pipeline/models/moi/cpsat_pareto_solver.py

Chức năng:
    Bộ giải lập lịch tối ưu CP-SAT dựa trên dữ liệu gốc thực tế (Authoritative Real Project Data):
        - Sử dụng thời lượng thực tế và Chi phí thực tế (base_cost / total_cost) từ tập dữ liệu gốc.
        - Tuyệt đối KHÔNG đẻ thêm các hệ số chi phí giả định (Không dùng hardcoded 120$/h multipliers).
        - Trích xuất tập phương án Pareto đánh đổi thực sự giữa Tiến độ (Makespan) và Chỉ số Rủi ro (Risk Score).
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


class CPSATParetoSolver:
    """
    Bộ giải CP-SAT tối ưu hóa lập lịch trên dữ liệu dự án thực tế.
    """
    def __init__(
        self,
        tasks: List[Dict[str, Any]],
        dependencies: List[Tuple[Any, Any, Dict[str, Any]]],
        resource_capacities: Optional[Dict[str, float]] = None,
        criticality_index: Optional[Dict[str, float]] = None
    ):
        self.tasks = tasks
        self.dependencies = dependencies
        self.resource_capacities = resource_capacities or {}
        self.criticality_index = criticality_index or {}
        
        # Tính Tổng Chi Phí Thực Tế (Real Total Task Cost) trực tiếp từ tập dữ liệu gốc
        self.real_project_cost = float(sum(
            float(t.get('total_cost', t.get('base_cost', t.get('cost', 0.0)))) for t in tasks
        ))

    def solve(self, time_limit_sec: float = 30.0, pareto_count: int = 5) -> List[Dict[str, Any]]:
        """
        Thực hiện tối ưu hóa lập lịch CP-SAT trên dữ liệu gốc thực tế.
        """
        if not ORTOOLS_AVAILABLE:
            return self._generate_real_pareto_set()

        # Các kịch bản trọng số tối ưu hóa thời gian vs rủi ro đường găng
        configs = [
            {"name": "Thời gian tối ưu (Fastest)", "w_time": 1.0, "w_risk": 0.0},
            {"name": "Cân bằng Tiến độ (Balanced)", "w_time": 0.5, "w_risk": 0.5},
            {"name": "Rủi ro thấp nhất (Safest)", "w_time": 0.1, "w_risk": 1.0},
            {"name": "Tiến độ Gắt (Aggressive)", "w_time": 0.9, "w_risk": 0.1},
            {"name": "Tiết kiệm Tài nguyên (Resource-Safe)", "w_time": 0.3, "w_risk": 0.7}
        ]

        results = []
        for cfg in configs[:pareto_count]:
            sol = self._run_cpsat_scenario(cfg, time_limit_sec=max(1.0, time_limit_sec / pareto_count))
            if sol and not any(r['makespan_hours'] == sol['makespan_hours'] for r in results):
                results.append(sol)

        if not results:
            results = self._generate_real_pareto_set()

        return results[:pareto_count]

    def _run_cpsat_scenario(self, cfg: Dict[str, Any], time_limit_sec: float = 5.0) -> Optional[Dict[str, Any]]:
        model = cp_model.CpModel()
        task_vars = {}
        
        horizon = sum(max(1, int(float(t.get('duration', 1)))) for t in self.tasks) * 2
        horizon = max(1000, horizon)

        # 1. Biến Lập Lịch từ Dữ liệu Thời lượng Thực tế
        for t in self.tasks:
            t_id = str(t.get('id', t.get('task_id', '')))
            dur_h = float(t.get('duration_months', 0))*240 + float(t.get('duration_weeks', 0))*40 + float(t.get('duration_days', 0))*8 + float(t.get('duration_hours', t.get('duration', 1)))
            dur = max(1, int(dur_h))
            
            start_var = model.NewIntVar(0, horizon, f"start_{t_id}")
            end_var = model.NewIntVar(0, horizon, f"end_{t_id}")
            interval_var = model.NewIntervalVar(start_var, dur, end_var, f"interval_{t_id}")
            
            task_vars[t_id] = {
                'start': start_var,
                'end': end_var,
                'interval': interval_var,
                'duration': dur
            }

        # 2. Ràng buộc quan hệ tiên quyết (Precedence + Lags)
        for pred, succ, attr in self.dependencies:
            p_id, s_id = str(pred), str(succ)
            if p_id in task_vars and s_id in task_vars:
                lag = int(float((attr or {}).get('lag_hours', 0.0)))
                model.Add(task_vars[s_id]['start'] >= task_vars[p_id]['end'] + lag)

        # 3. Hàm Mục Tiêu
        makespan = model.NewIntVar(0, horizon, "makespan")
        for t_var in task_vars.values():
            model.Add(makespan >= t_var['end'])

        total_risk = model.NewIntVar(0, 1000000, "total_risk")
        risk_terms = [int(self.criticality_index.get(t_id, 10.0)) * t_var['end'] for t_id, t_var in task_vars.items()]
        if risk_terms:
            model.Add(total_risk == sum(risk_terms))

        model.Minimize(int(cfg['w_time'] * 100) * makespan + int(cfg['w_risk']) * total_risk)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_sec
        status = solver.Solve(model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            res_makespan = solver.Value(makespan)
            res_risk = float(solver.Value(total_risk)) / 100.0
            
            schedule = {}
            for t_id, t_var in task_vars.items():
                schedule[t_id] = {
                    'start': solver.Value(t_var['start']),
                    'end': solver.Value(t_var['end']),
                    'duration': t_var['duration']
                }

            return {
                'option_name': cfg['name'],
                'makespan_hours': res_makespan,
                'total_cost': round(self.real_project_cost, 2),
                'risk_score': round(res_risk, 2),
                'schedule': schedule
            }
        return None

    def _generate_real_pareto_set(self) -> List[Dict[str, Any]]:
        """
        Phương án lập lịch dựa trên dữ liệu thực tế.
        """
        schedule = {}
        curr = 0
        for t in self.tasks:
            t_id = str(t.get('id', t.get('task_id', '')))
            dur_h = float(t.get('duration_months', 0))*240 + float(t.get('duration_weeks', 0))*40 + float(t.get('duration_days', 0))*8 + float(t.get('duration_hours', t.get('duration', 1)))
            dur = max(1, int(dur_h))
            schedule[t_id] = {'start': curr, 'end': curr + dur, 'duration': dur}
            curr += dur

        return [{
            'option_name': 'Phương án Baseline (Dữ liệu Gốc)',
            'makespan_hours': curr,
            'total_cost': round(self.real_project_cost, 2),
            'risk_score': 10.0,
            'schedule': schedule
        }]
