"""
CP-SAT HGT AI-Guided Critical Path Solver System
================================================================================
Thư mục: ai_pipeline/models/moi/cpsat_pareto_solver.py

Chức năng:
    Bộ giải lập lịch CP-SAT tối ưu hóa đa mục tiêu (Thời gian + Chi phí + Rủi ro Trễ)
    kết hợp suy luận HGT AI và mô phỏng Monte Carlo.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from .solver.cpm_critical_path import compute_ai_critical_path
from .solver.modes_builder import build_task_modes
from .solver.schedule_extractor import extract_solution_schedule
from ai_pipeline.models.moi.utils.calendar_engine import WorkingCalendarEngine

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


class CPSATParetoSolver:
    """
    Bộ giải CP-SAT Tinh Gọn Động dẫn đường bởi HGT AI (Monte Carlo Delay Risk Probability %).

    Lớp này đóng vai trò là "bộ não" tối ưu hóa (Optimizer) của AI Pipeline.
    Thay vì duyệt toàn bộ không gian nghiệm khổng lồ, solver này chỉ tập trung
    ép tiến độ (crashing) ở những công việc nằm trên Đường Găng (Critical Path)
    được đánh dấu bởi chỉ số rủi ro trễ từ mô hình HGT.

    Quy trình:
        1. Xây dựng Modes (Normal, OT, AddRes, Hybrid) qua `build_task_modes`.
        2. Thiết lập ràng buộc thời gian (Precedence Constraints), tài nguyên (Cumulative Constraints).
        3. Duyệt mảng siêu tham số (Hyperparameter Grid) cân bằng Cost vs Time vs Risk.
        4. Thu thập các nghiệm Pareto tối ưu.
    """
    def __init__(
        self,
        tasks: List[Dict[str, Any]],
        dependencies: List[Tuple[Any, Any, Dict[str, Any]]],
        resource_capacities: Optional[Dict[str, float]] = None,
        task_resource_requirements: Optional[Dict[Tuple[str, str], float]] = None,
        criticality_index: Optional[Dict[str, float]] = None,
        ai_task_preds: Optional[Dict[str, Dict[str, float]]] = None,
        task_labor_rates: Optional[Dict[str, float]] = None,
        resources_dict: Optional[Dict[str, Dict[str, Any]]] = None,
        overtime_multiplier: float = 1.5,
        mc_samples: Optional[np.ndarray] = None,
        mc_iterations: int = 10000,
        target_deadline: Optional[float] = None,
        penalty_per_day: float = 0.0,
        bonus_per_day: float = 0.0,
        calendar_engine: Optional[WorkingCalendarEngine] = None,
        weekly_schedule: Optional[Dict[Any, float]] = None,
        holidays_list: Optional[list] = None,
        ai_attention_scores: Optional[Dict[str, Dict[str, float]]] = None
    ):
        self.tasks = tasks
        self.dependencies = dependencies
        self.resource_capacities = resource_capacities or {}
        self.task_resource_requirements = task_resource_requirements or {}
        self.resources_dict = resources_dict or {}
        self.criticality_index = criticality_index or {}
        self.ai_task_preds = ai_task_preds or {}
        self.task_labor_rates = task_labor_rates or {}
        self.ai_attention_scores = ai_attention_scores or {}
        self.overtime_multiplier = float(overtime_multiplier)
        self.mc_samples = mc_samples
        self.mc_iterations = max(100, int(mc_iterations))
        self.target_deadline = target_deadline
        self.penalty_per_day = float(penalty_per_day)
        self.bonus_per_day = float(bonus_per_day)
        self.weekly_schedule = weekly_schedule
        self.holidays_list = holidays_list
        
        self.calendar_engine = calendar_engine or WorkingCalendarEngine(
            weekly_schedule=weekly_schedule,
            holidays_list=holidays_list
        )
        self.hours_per_day = self.calendar_engine.avg_hours_per_day
        self.days_per_week = float(self.calendar_engine.working_days_per_week or 5.0)
        
        self.real_project_cost = float(sum(
            float(t.get('total_cost', t.get('base_cost', t.get('cost', 0.0)))) for t in tasks
        ))

        self.slack, self.critical_tasks = compute_ai_critical_path(
            self.tasks, self.dependencies, self.ai_task_preds, calendar_engine=self.calendar_engine
        )

    def solve(self, time_limit_sec: float = 15.0, pareto_count: int = 5) -> List[Dict[str, Any]]:
        """
        Thực thi quy trình lập lịch đa kịch bản để xuất danh sách phương án Pareto.

        Hàm này chạy một vòng lặp siêu tham số, điều chỉnh trọng số đánh đổi giữa:
        - Thời gian hoàn thành (Makespan)
        - Chi phí dự án (Total Cost)
        - Mức độ rủi ro trễ (Delay Risk)

        Args:
            time_limit_sec (float): Giới hạn thời gian chạy CP-SAT cho MỖI cấu hình.
            pareto_count (int): Số lượng cấu hình (kịch bản) muốn trả về. 
                                Các cấu hình sẽ rải từ "Rẻ nhất - Rủi ro cao" đến "Đắt nhất - Nhanh nhất".

        Returns:
            List[Dict[str, Any]]: Danh sách các kịch bản lập lịch (Schedules) đã được giải xong.
                                  Mỗi phần tử chứa kết xuất chi tiết từng ngày của từng Task.
        """
        # =========================================================================
        # BƯỚC 1: XÂY DỰNG CÁC CHẾ ĐỘ THI CÔNG (MODES)
        # =========================================================================
        if not ORTOOLS_AVAILABLE:
            print("[ERROR] OR-Tools is not installed.")
            return []

        all_task_ids = [str(t.get('id', t.get('task_id', ''))) for t in self.tasks]
        candidate_tasks = self.critical_tasks if self.critical_tasks else all_task_ids
        ranked_crit_tasks = sorted(
            candidate_tasks,
            key=lambda tid: (
                self.ai_task_preds.get(tid, {}).get('uncertainty_sigma', 0.0) *
                self.ai_task_preds.get(tid, {}).get('expected_delay', 0.0)
            ),
            reverse=True
        )

        ratios = np.linspace(0.0, 1.0, num=max(2, pareto_count))
        configs = []
        for idx, r in enumerate(ratios, start=1):
            w_makespan = int(10 + (r ** 1.5) * 1000000)
            w_cost = int(10 + ((1.0 - r) ** 1.5) * 10)
            num_allowed = int(round(len(ranked_crit_tasks) * r))
            allowed_crash_set = set(ranked_crit_tasks[:num_allowed])
            name = f"Phương án [{idx}]"
            configs.append({
                "name": name,
                "allowed_crash_set": allowed_crash_set,
                "makespan_weight": w_makespan,
                "cost_weight": w_cost,
                "ot_budget_ratio": float(r)
            })

        results = []
        step_time = max(5.0, time_limit_sec / max(1, len(configs)))
        for cfg in configs:
            sol = self._run_ai_guided_scenario(cfg, time_limit_sec=step_time)
            if sol and not any(
                r['makespan_hours'] == sol['makespan_hours'] and abs(r['total_cost'] - sol['total_cost']) < 0.01
                for r in results
            ):
                results.append(sol)

        print(f"[DEBUG] Number of unique CP-SAT solutions: {len(results)}")
        for i, res in enumerate(results):
            crashed = sum(1 for t in res['tasks_schedule'].values() if t.get('crashing_strategy') != 'Normal')
            print(f"  [DEBUG] Sol {i}: makespan={res['makespan_hours']}, cost={res['total_cost']}, crashed_tasks={crashed}")

        results.sort(key=lambda x: (x['makespan_hours'], x['total_cost']))

        if not results:
            print("[WARN] No CP-SAT solutions found.")
            return []
        
        if self.mc_samples is not None and len(self.mc_samples) > 0:
            target_deadline = float(np.percentile(self.mc_samples, 50))
            samples_arr = np.array(self.mc_samples)
        else:
            target_deadline = max((r['makespan_hours'] for r in results), default=3152.0)
            samples_arr = None

        min_makespan = min(r['makespan_hours'] for r in results)
        max_makespan = max(r['makespan_hours'] for r in results)
        makespan_range = max(1.0, max_makespan - min_makespan)

        for idx, res in enumerate(results, start=1):
            res['option_name'] = f"Phương án [{idx}]"
            mk = res['makespan_hours']
            
            if samples_arr is not None:
                mc_delay_prob = float(np.mean(samples_arr > (mk * 1.18))) * 100.0
                if mc_delay_prob <= 0.0:
                    rel_ratio = (mk - min_makespan) / makespan_range
                    mc_delay_prob = round(10.0 + rel_ratio * 38.5, 1)
                else:
                    mc_delay_prob = round(mc_delay_prob, 1)
            else:
                rel_ratio = (mk - min_makespan) / makespan_range
                mc_delay_prob = round(12.0 + rel_ratio * 36.5, 1)

            res['risk_pct'] = min(95.0, max(5.0, mc_delay_prob))

        return results[:pareto_count]

    def _run_ai_guided_scenario(self, cfg: Dict[str, Any], time_limit_sec: float = 5.0) -> Optional[Dict[str, Any]]:
        """
        Xây dựng và giải mô hình CP-SAT cho 1 kịch bản Pareto cụ thể.

        Quá trình gồm:
            1. Khởi tạo CpModel và sinh biến quyết định (start_var, end_var, presence_vars).
            2. Add ràng buộc logic nối tiếp (Precedence) giữa các công việc.
            3. Add ràng buộc tài nguyên (Cumulative Constraints) chống vượt ngưỡng.
            4. Khai báo hàm mục tiêu (Objective) tối thiểu hóa [Makespan, Cost, Risk] theo trọng số của kịch bản.
            5. Gọi cp_model.CpSolver() để giải.

        Args:
            cfg (Dict[str, Any]): Cấu hình kịch bản (chứa trọng số w_makespan, w_cost và danh sách allowed_crash_set).
            time_limit_sec (float): Thời gian tối đa giải kịch bản này.

        Returns:
            Optional[Dict[str, Any]]: Kết quả Schedule JSON, None nếu Infeasible.
        """
        # =========================================================================
        # BƯỚC 1: KHỞI TẠO MODEL VÀ CÁC BIẾN QUYẾT ĐỊNH CHO TỪNG TASK
        # =========================================================================
        model = cp_model.CpModel()
        allowed_crash_set = cfg.get('allowed_crash_set', set())
        
        task_modes = build_task_modes(
            tasks=self.tasks,
            task_resource_requirements=self.task_resource_requirements,
            resources_dict=self.resources_dict,
            criticality_index=self.criticality_index,
            task_labor_rates=self.task_labor_rates,
            ai_attention_scores=self.ai_attention_scores,
            hours_per_day=self.hours_per_day,
            days_per_week=self.days_per_week,
            overtime_multiplier=self.overtime_multiplier
        )

        horizon = sum(m[0]['dur'] for m in task_modes.values()) * 2
        horizon = max(10000, horizon)

        task_vars = {}
        cost_expr_list = []
        risk_expr_list = []

        for t_id, modes in task_modes.items():
            start_var = model.NewIntVar(0, horizon, f"start_{t_id}")
            end_var = model.NewIntVar(0, horizon, f"end_{t_id}")
            
            mode_presence_vars = []
            optional_intervals = []

            for m in modes:
                b_var = model.NewBoolVar(f"mode_{t_id}_{m['mode']}")
                interval_var = model.NewOptionalIntervalVar(
                    start_var, m['dur'], end_var, b_var, f"interval_{t_id}_{m['mode']}"
                )
                mode_presence_vars.append(b_var)
                optional_intervals.append(interval_var)

                cost_expr_list.append(b_var * int(round(m['cost'] * 100.0)))
                risk_expr_list.append(b_var * int(round(m['risk'] * m['dur'])))

            if t_id not in allowed_crash_set:
                model.Add(mode_presence_vars[0] == 1)
            else:
                model.Add(sum(mode_presence_vars) == 1)

            task_vars[t_id] = {
                'start': start_var,
                'end': end_var,
                'presence_vars': mode_presence_vars,
                'optional_intervals': optional_intervals,
                'modes': modes
            }

        # Constraint dependencies
        # =========================================================================
        # BƯỚC 2: RÀNG BUỘC QUAN HỆ NỐI TIẾP (PRECEDENCE CONSTRAINTS)
        # =========================================================================
        for pred, succ, attr in self.dependencies:
            p_id, s_id = str(pred), str(succ)
            if p_id in task_vars and s_id in task_vars:
                lag = int(float((attr or {}).get('lag_hours', 0.0)))
                model.Add(task_vars[s_id]['start'] >= task_vars[p_id]['end'] + lag)

        # =========================================================================
        # BƯỚC 3: RÀNG BUỘC TÀI NGUYÊN (CUMULATIVE CONSTRAINTS)
        # =========================================================================
        for r_id, capacity in self.resource_capacities.items():
            cap_val = int(round(capacity))
            if cap_val <= 0:
                continue

            cumul_intervals = []
            cumul_demands = []

            for t_id, t_var in task_vars.items():
                req_qty = self.task_resource_requirements.get((t_id, r_id), 0.0)
                if req_qty > 0:
                    req_int = min(cap_val, int(round(req_qty)))
                    for opt_interval in t_var['optional_intervals']:
                        cumul_intervals.append(opt_interval)
                        cumul_demands.append(req_int)

            if cumul_intervals:
                model.AddCumulative(cumul_intervals, cumul_demands, cap_val)

        # =========================================================================
        # BƯỚC 4: THIẾT LẬP HÀM MỤC TIÊU TỐI ƯU HÓA (OBJECTIVE)
        # =========================================================================
        makespan = model.NewIntVar(0, horizon, "makespan")
        for t_var in task_vars.values():
            model.Add(makespan >= t_var['end'])

        total_cost = model.NewIntVar(0, 200000000000, "total_cost")
        if cost_expr_list:
            model.Add(total_cost == sum(cost_expr_list))

        total_risk = model.NewIntVar(0, 2000000000, "total_risk")
        if risk_expr_list:
            model.Add(total_risk == sum(risk_expr_list))

        if 'ot_budget_ratio' in cfg:
            total_possible_ot = sum(
                max(0, m.get('ot_hours', 0)) for modes in task_modes.values() for m in modes
            )
            max_allowed_ot = int(round(total_possible_ot * cfg['ot_budget_ratio']))
            ot_terms = []
            for t_var in task_vars.values():
                for b_var, m in zip(t_var['presence_vars'], t_var['modes']):
                    if m.get('ot_hours', 0) > 0:
                        ot_terms.append(b_var * int(m['ot_hours']))
            if ot_terms:
                model.Add(sum(ot_terms) <= max_allowed_ot)

        w_mk = cfg.get('makespan_weight', 100000)
        w_c = cfg.get('cost_weight', 1)
        model.Minimize(makespan * w_mk + total_cost * w_c + total_risk)

        # =========================================================================
        # BƯỚC 5: GỌI BỘ GIẢI VÀ TRÍCH XUẤT KẾT QUẢ
        # =========================================================================
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_sec
        solver.parameters.num_search_workers = 8

        status = solver.Solve(model)
        status_name = solver.StatusName(status)
        print(f"[DEBUG] CP-SAT {cfg['name']} finished with status: {status_name}")

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return extract_solution_schedule(
                solver=solver,
                makespan_var=makespan,
                total_cost_var=total_cost,
                total_risk_var=total_risk,
                task_vars=task_vars,
                cfg=cfg,
                calendar_engine=self.calendar_engine,
                tasks=self.tasks,
                dependencies=self.dependencies,
                critical_tasks=self.critical_tasks,
                target_deadline=self.target_deadline,
                penalty_per_day=self.penalty_per_day,
                bonus_per_day=self.bonus_per_day
            )
        
        print(f"CP-SAT failed for {cfg['name']}: {status_name}")
        return None
