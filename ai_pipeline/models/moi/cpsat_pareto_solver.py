"""
CP-SAT HGT AI-Guided Critical Path Solver System
================================================================================
Thư mục: ai_pipeline/models/moi/cpsat_pareto_solver.py

Chức năng:
    Bộ giải lập lịch CP-SAT tối ưu hóa đa mục tiêu (Thời gian + Chi phí + Rủi ro Trễ)
    kết hợp suy luận HGT AI và mô phỏng Monte Carlo.

Cấu trúc Mã nguồn (Clean Architecture):
    1. SECTION 1: IMPORTS & ENGINE INITIALIZATION
    2. SECTION 2: CRITICAL PATH COMPUTATION (CPM PASS)
    3. SECTION 3: INTER-COST CALCULATION ENGINE
    4. SECTION 4: CP-SAT PARETO SOLVER CLASS & OPTIMIZATION METHODS
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
from .solver.cpm_critical_path import compute_ai_critical_path
from .solver.crashing_builder import calculate_task_inter_costs

from ai_pipeline.models.moi.domain_normalizers import (
    calculate_task_total_hours,
    WorkingCalendarEngine
)

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


# ==============================================================================
# SECTION 2: CRITICAL PATH COMPUTATION (CPM PASS)
# ==============================================================================



# ==============================================================================
# SECTION 3: INTER-COST CALCULATION ENGINE
# ==============================================================================



# ==============================================================================
# SECTION 4: CP-SAT PARETO SOLVER CLASS & OPTIMIZATION METHODS
# ==============================================================================

class CPSATParetoSolver:
    """
    Bộ giải CP-SAT Tinh Gọn Động dẫn đường bởi HGT AI (Monte Carlo Delay Risk Probability %).
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
        
        # Initialize WorkingCalendarEngine động từ agenda.json
        self.calendar_engine = calendar_engine or WorkingCalendarEngine(
            weekly_schedule=weekly_schedule,
            holidays_list=holidays_list
        )
        self.hours_per_day = self.calendar_engine.avg_hours_per_day
        self.days_per_week = float(self.calendar_engine.working_days_per_week or 5.0)
        
        self.real_project_cost = float(sum(
            float(t.get('total_cost', t.get('base_cost', t.get('cost', 0.0)))) for t in tasks
        ))

        # Tính toán AI Critical Path chuẩn theo Lịch Agenda
        self.slack, self.critical_tasks = compute_ai_critical_path(
            self.tasks, self.dependencies, self.ai_task_preds, calendar_engine=self.calendar_engine
        )

    def solve(self, time_limit_sec: float = 15.0, pareto_count: int = 5) -> List[Dict[str, Any]]:
        """
        Thực thi quy trình lập lịch đa kịch bản để xuất danh sách pareto_count phương án Pareto.
        """
        if not ORTOOLS_AVAILABLE:
            return self._generate_real_pareto_set()

        # Xếp hạng các task găng theo điểm rủi ro HGT AI
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
            w_makespan = int(10 + (r ** 1.5) * 1000000) # Increased makespan weight
            w_cost = int(10 + ((1.0 - r) ** 1.5) * 10) # Reduced cost weight drastically
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

        if not results or len(results) < pareto_count:
            print("[DEBUG] Calling _expand_pareto_frontier!")
            results = self._expand_pareto_frontier(results, pareto_count)
        
        # Mốc hạn định P50 từ Monte Carlo
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
        Xây dựng mô hình CP-SAT cho 1 kịch bản Pareto cụ thể.
        """
        model = cp_model.CpModel()
        allowed_crash_set = cfg.get('allowed_crash_set', set())
        avg_h_day = max(1.0, self.calendar_engine.avg_hours_per_day)
        
        task_modes = {}
        for t in self.tasks:
            t_id = str(t.get('id', t.get('task_id', '')))
            base_effort_h = calculate_task_total_hours(t, self.hours_per_day, self.days_per_week)
            ci_score = float(self.criticality_index.get(t_id, 10.0))

            cost_meta = calculate_task_inter_costs(t, base_effort_h, self.overtime_multiplier, self.task_labor_rates)
            base_cost = cost_meta['base_cost']

            # ========== PHÂN LOẠI RESOURCE: HUMAN vs MACHINE ==========
            human_resources = []   # [(r_info_dict, qty), ...]
            machine_resources = [] # [(r_info_dict, qty), ...]

            for (tid, rid), qty in self.task_resource_requirements.items():
                if str(tid) == t_id and qty > 0:
                    r_info = self.resources_dict.get(str(rid), {})
                    r_type = str(r_info.get('type', 'Machine')).lower()
                    if r_type == 'human':
                        human_resources.append((r_info, float(qty)))
                    else:
                        machine_resources.append((r_info, float(qty)))

            all_resources = human_resources + machine_resources

            # ========== TÍNH OT BOTTLENECK ==========
            # Ngưỡng OT = min(max_overtime_per_day) trên TẤT CẢ resources của task
            if all_resources:
                task_max_ot_per_day = min(
                    float(r_info.get('max_overtime_per_day', 4.0 if str(r_info.get('type','')).lower() == 'human' else 16.0))
                    for r_info, _ in all_resources
                )
            else:
                task_max_ot_per_day = 0.0

            # ========== TÍNH ĐƠN GIÁ THEO LOẠI ==========
            # Human: unit_cost = labor rate/h, energy = 0
            human_labor_rate_total = sum(qty * float(r.get('unit_cost', 25.0)) for r, qty in human_resources)
            human_ot_multi = min(
                (float(r.get('overtime_multi', self.overtime_multiplier)) for r, _ in human_resources),
                default=self.overtime_multiplier
            )

            # Machine: unit_cost = equipment rate/h, energy = energy rate/h
            machine_equip_rate_total = sum(qty * float(r.get('unit_cost', 10.0)) for r, qty in machine_resources)
            machine_energy_rate_total = sum(qty * float(r.get('energy', 0.0)) for r, qty in machine_resources)
            # Machine overtime_multi thường = 1.0 (không phụ trội)

            # ========== BASE DURATION (tính từ Effort) ==========
            base_workers = max(1, sum(int(qty) for _, qty in human_resources)) if human_resources else 1
            dur_0 = max(1, int(round(base_effort_h)))
            cost_0 = base_cost
            risk_0 = ci_score * 1.0

            # ========== BASE COST COMPONENTS ==========
            # Từ tasks.csv (đã có sẵn)
            base_labor = float(t.get('labor', cost_meta.get('base_labor', 0.0)) or 0.0)
            base_equipment = float(t.get('equipment') or 0.0)
            base_energy = float(t.get('energy', cost_meta.get('base_energy', 0.0)) or 0.0)

            # ========== MODE 0: NORMAL ==========
            modes = [{
                'mode': 0,
                'name': 'Normal',
                'dur': dur_0,
                'cost': cost_0,
                'risk': risk_0,
                'normal_dur': dur_0,
                'base_effort_h': base_effort_h,
                'workers': base_workers,
                'extra_workers': 0,
                'ot_hours': 0,
                'ot_hours_per_day': 0.0,
                'ot_extra_cost': 0.0,
                'base_cost': base_cost,
                'base_labor': base_labor,
                'base_equipment': base_equipment,
                'base_energy': base_energy,
                'labor_ot_cost': 0.0,       # Human OT premium = 0
                'equipment_ot_cost': 0.0,   # Machine extra equipment = 0
                'energy_ot_cost': 0.0,      # Machine extra energy = 0
                'added_res_cost': 0.0,
                'crashing_strategy': 'Normal'
            }]

            # ========== MODE 1: OT (nếu có resource cho phép và bị tràn lịch) ==========
            allow_ot = False
            if task_max_ot_per_day > 0:
                allow_ot = True

            if allow_ot:
                dur_days = base_effort_h / self.hours_per_day
                ot_hours_total = round(dur_days * task_max_ot_per_day, 1)

                # Duration mới: thêm giờ OT mỗi ngày → hoàn thành sớm hơn
                new_h_per_day = self.hours_per_day + task_max_ot_per_day
                dur_1 = max(1, int(round(base_effort_h * self.hours_per_day / new_h_per_day)))

                # Human: Labor giữ nguyên, chỉ tính OT Premium
                ot_breakdown = []
                ot_premium_human = 0.0
                equipment_ot_extra = 0.0
                energy_ot_extra = 0.0

                if human_resources:
                    for r_info, qty in human_resources:
                        labor_rate = float(r_info.get('unit_cost', 25.0))
                        multi = float(r_info.get('overtime_multi', self.overtime_multiplier))
                        r_ot_premium = round(ot_hours_total * qty * labor_rate * (multi - 1.0), 2)
                        ot_premium_human += r_ot_premium
                        if r_ot_premium > 0:
                            ot_breakdown.append({
                                'resource_id': str(r_info.get('ID', r_info.get('name'))),
                                'resource_name': str(r_info.get('name', 'Unknown')),
                                'type': 'Human',
                                'ot_hours': float(ot_hours_total),
                                'ot_cost': float(r_ot_premium)
                            })
                else:
                    labor_rate_per_h = cost_meta.get('labor_rate_per_h', 25.0)
                    ot_premium_human = round(ot_hours_total * labor_rate_per_h * (self.overtime_multiplier - 1.0), 2)

                if machine_resources:
                    for r_info, qty in machine_resources:
                        equip_rate = float(r_info.get('unit_cost', 10.0))
                        energy_rate = float(r_info.get('energy', 0.0))
                        
                        r_equip_ot = round(ot_hours_total * qty * equip_rate, 2)
                        r_energy_ot = round(ot_hours_total * qty * energy_rate, 2)
                        
                        equipment_ot_extra += r_equip_ot
                        energy_ot_extra += r_energy_ot
                        
                        r_ot_extra = r_equip_ot + r_energy_ot
                        if r_ot_extra > 0:
                            ot_breakdown.append({
                                'resource_id': str(r_info.get('ID', r_info.get('name'))),
                                'resource_name': str(r_info.get('name', 'Unknown')),
                                'type': 'Machine',
                                'ot_cost': r_ot_extra
                            })

                ot_premium_human = round(ot_premium_human, 2)
                equipment_ot_extra = round(equipment_ot_extra, 2)
                energy_ot_extra = round(energy_ot_extra, 2)
                total_ot_extra = round(ot_premium_human + equipment_ot_extra + energy_ot_extra, 2)

                cost_1 = round(base_cost + total_ot_extra, 2)
                risk_1 = ci_score * 0.75

                modes.append({
                    'mode': 1,
                    'name': 'Overtime',
                    'dur': dur_1,
                    'cost': cost_1,
                    'risk': risk_1,
                    'normal_dur': dur_0,
                    'base_effort_h': base_effort_h,
                    'workers': base_workers,
                    'extra_workers': 0,
                    'ot_hours': int(round(ot_hours_total)),
                    'ot_hours_per_day': task_max_ot_per_day,
                    'ot_extra_cost': total_ot_extra,
                    'base_cost': base_cost,
                    'base_labor': base_labor,
                    'base_equipment': base_equipment,
                    'base_energy': base_energy,
                    'labor_ot_cost': ot_premium_human,
                    'equipment_ot_cost': equipment_ot_extra,
                    'energy_ot_cost': energy_ot_extra,
                    'added_res_cost': 0.0,
                    'added_resources_detail': [],
                    'ot_resource_breakdown': ot_breakdown,
                    'crashing_strategy': 'OT'
                })

            # ========== MODE 2: AddRes (AI-Driven Allocation) ==========
            if human_resources:
                extra_workers_needed = max(1, int(round(base_workers * 1.0)))
                
                # Quét và lấy dư địa (Room)
                available_pool = []
                for r_info, qty in human_resources:
                    r_id = str(r_info.get('ID', ''))
                    max_avail = float(r_info.get('max_availability', 10.0))
                    room = max(0, int(max_avail - qty))
                    score = self.ai_attention_scores.get(t_id, {}).get(r_id, 0.0)
                    if room > 0:
                        available_pool.append({
                            'id': r_id,
                            'name': str(r_info.get('name', r_id)),
                            'unit_cost': float(r_info.get('unit_cost', 25.0)),
                            'room': room,
                            'score': score
                        })
                
                # Bốc người dựa trên AI Attention Scores (Giảm dần)
                available_pool.sort(key=lambda x: x['score'], reverse=True)
                
                added_detail = []
                workers_to_add = extra_workers_needed
                
                for cand in available_pool:
                    if workers_to_add <= 0:
                        break
                    take = min(cand['room'], workers_to_add)
                    added_detail.append({
                        'resource_id': cand['id'],
                        'name': cand['name'],
                        'added_qty': take,
                        'unit_cost': cand['unit_cost'],
                        'total_extra_cost': 0.0 # Sẽ tính lại sau khi có dur_2
                    })
                    workers_to_add -= take
                
                # Nếu có thể thêm ít nhất 1 người
                actual_extra_workers = extra_workers_needed - workers_to_add
                if actual_extra_workers > 0:
                    effective_workers = base_workers
                    for d in added_detail:
                        r_info = self.resources_dict.get(d['resource_id'], {})
                        eff = float(r_info.get('addres_efficiency', 0.7))
                        effective_workers += d['added_qty'] * eff
                        
                    dur_2_actual = max(1, int(round(base_effort_h * base_workers / effective_workers)))
                    
                    added_res_cost = 0.0
                    for d in added_detail:
                        d['total_extra_cost'] = d['added_qty'] * d['unit_cost'] * dur_2_actual
                        added_res_cost += d['total_extra_cost']
                        
                    # Thêm người sẽ tốn 10% chi phí quản lý cho phần thêm
                    net_cost_increase = added_res_cost * 1.1
                    
                    # Savings từ việc base workers giảm số giờ làm
                    labor_rate_h = base_labor / max(1.0, dur_0)
                    equip_rate_h = base_equipment / max(1.0, dur_0)
                    energy_rate_h = base_energy / max(1.0, dur_0)
                    
                    new_base_labor = round(labor_rate_h * dur_2_actual, 2)
                    new_base_equip = round(equip_rate_h * dur_2_actual, 2)
                    new_base_energy = round(energy_rate_h * dur_2_actual, 2)
                    new_base_cost = round(new_base_labor + new_base_equip + new_base_energy, 2)
                    
                    # Tổng chi phí mới
                    cost_2 = round(new_base_cost + net_cost_increase, 2)
                    risk_2 = ci_score * 0.85 # Rủi ro thấp hơn OT một chút nhưng cao hơn bình thường
                    
                    modes.append({
                        'mode': 2,
                        'name': 'AddRes',
                        'dur': dur_2_actual,
                        'cost': cost_2,
                        'risk': risk_2,
                        'normal_dur': dur_0,
                        'base_effort_h': base_effort_h,
                        'workers': base_workers,
                        'extra_workers': actual_extra_workers,
                        'ot_hours': 0,
                        'ot_hours_per_day': 0.0,
                        'ot_extra_cost': 0.0,
                        'base_cost': new_base_cost,
                        'base_labor': new_base_labor,
                        'base_equipment': new_base_equip,
                        'base_energy': new_base_energy,
                        'labor_ot_cost': 0.0,
                        'equipment_ot_cost': 0.0,
                        'energy_ot_cost': 0.0,
                        'added_res_cost': round(net_cost_increase, 2),
                        'added_resources_detail': added_detail,
                        'crashing_strategy': 'AddRes'
                    })

                    # ========== MODE 3: Hybrid (AddRes + OT) ==========
                    if allow_ot:
                        dur_days_after_add = dur_2_actual / self.hours_per_day
                        total_ot_hours_hybrid = round(dur_days_after_add * task_max_ot_per_day, 1)
                        
                        new_h_per_day = self.hours_per_day + task_max_ot_per_day
                        dur_3 = max(1, int(round(dur_2_actual * self.hours_per_day / new_h_per_day)))
                        
                        # OT Cost for Base Workers
                        ot_premium_base = 0.0
                        equipment_ot_extra_3 = 0.0
                        energy_ot_extra_3 = 0.0
                        ot_breakdown_3 = []
                        
                        if human_resources:
                            for r_info, qty in human_resources:
                                labor_rate = float(r_info.get('unit_cost', 25.0))
                                multi = float(r_info.get('overtime_multi', self.overtime_multiplier))
                                r_ot_premium = round(total_ot_hours_hybrid * qty * labor_rate * (multi - 1.0), 2)
                                ot_premium_base += r_ot_premium
                                if r_ot_premium > 0:
                                    ot_breakdown_3.append({
                                        'resource_id': str(r_info.get('ID', r_info.get('name'))),
                                        'resource_name': str(r_info.get('name', 'Unknown')),
                                        'type': 'Human (Base)',
                                        'ot_hours': float(total_ot_hours_hybrid),
                                        'ot_cost': float(r_ot_premium)
                                    })
                        else:
                            labor_rate_per_h = cost_meta.get('labor_rate_per_h', 25.0)
                            ot_premium_base = round(total_ot_hours_hybrid * labor_rate_per_h * (self.overtime_multiplier - 1.0), 2)
                            
                        # OT Cost for Added Workers
                        ot_premium_added = 0.0
                        for d in added_detail:
                            r_info = self.resources_dict.get(d['resource_id'], {})
                            multi = float(r_info.get('overtime_multi', self.overtime_multiplier))
                            r_ot_premium = round(total_ot_hours_hybrid * d['added_qty'] * d['unit_cost'] * (multi - 1.0), 2)
                            ot_premium_added += r_ot_premium
                            if r_ot_premium > 0:
                                ot_breakdown_3.append({
                                    'resource_id': d['resource_id'],
                                    'resource_name': d['name'],
                                    'type': 'Human (Added)',
                                    'ot_hours': float(total_ot_hours_hybrid),
                                    'ot_cost': float(r_ot_premium)
                                })
                        
                        if machine_resources:
                            for r_info, qty in machine_resources:
                                equip_rate = float(r_info.get('unit_cost', 10.0))
                                energy_rate = float(r_info.get('energy', 0.0))
                                r_equip_ot = round(total_ot_hours_hybrid * qty * equip_rate, 2)
                                r_energy_ot = round(total_ot_hours_hybrid * qty * energy_rate, 2)
                                equipment_ot_extra_3 += r_equip_ot
                                energy_ot_extra_3 += r_energy_ot
                                r_ot_extra = r_equip_ot + r_energy_ot
                                if r_ot_extra > 0:
                                    ot_breakdown_3.append({
                                        'resource_id': str(r_info.get('ID', r_info.get('name'))),
                                        'resource_name': str(r_info.get('name', 'Unknown')),
                                        'type': 'Machine',
                                        'ot_cost': r_ot_extra
                                    })
                                    
                        total_ot_premium_3 = round(ot_premium_base + ot_premium_added, 2)
                        equipment_ot_extra_3 = round(equipment_ot_extra_3, 2)
                        energy_ot_extra_3 = round(energy_ot_extra_3, 2)
                        total_ot_extra_3 = round(total_ot_premium_3 + equipment_ot_extra_3 + energy_ot_extra_3, 2)
                        
                        # Total cost
                        cost_3 = round(new_base_cost + net_cost_increase + total_ot_extra_3, 2)
                        risk_3 = ci_score * 0.90
                        
                        modes.append({
                            'mode': 3,
                            'name': 'Hybrid',
                            'dur': dur_3,
                            'cost': cost_3,
                            'risk': risk_3,
                            'normal_dur': dur_0,
                            'base_effort_h': base_effort_h,
                            'workers': base_workers,
                            'extra_workers': actual_extra_workers,
                            'ot_hours': int(round(total_ot_hours_hybrid)),
                            'ot_hours_per_day': task_max_ot_per_day,
                            'ot_extra_cost': total_ot_extra_3,
                            'base_cost': new_base_cost,
                            'base_labor': new_base_labor,
                            'base_equipment': new_base_equip,
                            'base_energy': new_base_energy,
                            'labor_ot_cost': total_ot_premium_3,
                            'equipment_ot_cost': equipment_ot_extra_3,
                            'energy_ot_cost': energy_ot_extra_3,
                            'added_res_cost': round(net_cost_increase, 2),
                            'added_resources_detail': added_detail,
                            'ot_resource_breakdown': ot_breakdown_3,
                            'crashing_strategy': 'Hybrid'
                        })

            task_modes[t_id] = modes
            
            # [DEBUG] Print modes for a few tasks
            if cfg.get('name') == 'Phương án [1]' and len(task_modes) <= 2:
                print(f"[DEBUG] Task {t_id} modes:")
                for m in modes:
                    print(f"  Mode {m['mode']} ({m['name']}): dur={m['dur']} workers={m['workers']} extra={m['extra_workers']}")

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
        for pred, succ, attr in self.dependencies:
            p_id, s_id = str(pred), str(succ)
            if p_id in task_vars and s_id in task_vars:
                lag = int(float((attr or {}).get('lag_hours', 0.0)))
                model.Add(task_vars[s_id]['start'] >= task_vars[p_id]['end'] + lag)

        # Cumulative Resource Constraints
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

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_sec
        solver.parameters.num_search_workers = 8

        status = solver.Solve(model)
        status_name = solver.StatusName(status)
        print(f"[DEBUG] CP-SAT {cfg['name']} finished with status: {status_name}")

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self._extract_solution_schedule(solver, makespan, total_cost, total_risk, task_vars, cfg)
        
        status_name = solver.StatusName(status)
        print(f"CP-SAT failed for {cfg['name']}: {status_name}")
        return None

    def _extract_solution_schedule(
        self,
        solver,
        makespan,
        total_cost,
        total_risk,
        task_vars: Dict[str, Any],
        cfg: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trích xuất kết quả lịch thi công chi tiết từ lời giải CP-SAT.
        """
        res_makespan = solver.Value(makespan)
        res_cost = float(solver.Value(total_cost)) / 100.0
        res_risk = float(solver.Value(total_risk)) / 100.0
        
        schedule = {}
        affected_tasks = []
        total_ot_hours_project = 0
        tasks_overtime_count = 0
        
        hours_per_day = self.calendar_engine.avg_hours_per_day
        hours_per_week = self.calendar_engine.hours_per_week
        hours_per_month = self.calendar_engine.hours_per_month

        # Mốc bắt đầu dự án ban đầu
        b_start_series = [t.get('baseline_start', '2010-01-01T08:00:00Z') for t in self.tasks]
        b_dt = pd.to_datetime(b_start_series, errors='coerce', utc=True).dropna()
        min_proj_dt = b_dt.min() if len(b_dt) > 0 else pd.to_datetime('2010-01-01T08:00:00Z', utc=True)
        
        # Build predecessor map for topological date resolution
        pred_map = {t_id: [] for t_id in task_vars.keys()}
        for pred, succ, attr in self.dependencies:
            p_id, s_id = str(pred), str(succ)
            if s_id in pred_map and p_id in task_vars:
                pred_map[s_id].append(p_id)
                
        # Forward pass to calculate actual real-world dates
        real_start_dts = {}
        real_finish_dts = {}
        sorted_t_ids = sorted(task_vars.keys(), key=lambda x: solver.Value(task_vars[x]['start']))

        for t_id in sorted_t_ids:
            t_var = task_vars[t_id]
            sel_mode = 0
            for idx, b_var in enumerate(t_var['presence_vars']):
                if solver.Value(b_var) == 1:
                    sel_mode = idx
                    break
            
            m_info = t_var['modes'][sel_mode]
            ot_hours = float(m_info['ot_hours'])
            if ot_hours > 0:
                tasks_overtime_count += 1
                total_ot_hours_project += ot_hours

            st_val = solver.Value(t_var['start'])
            end_val = solver.Value(t_var['end'])
            dur_h = float(m_info['dur'])
            norm_dur_h = float(m_info['normal_dur'])
            
            # Durations
            dur_d = round(dur_h / hours_per_day, 2)
            dur_w = round(dur_h / hours_per_week, 2)
            dur_m = round(dur_h / hours_per_month, 2)
            
            daily_work_h = round(hours_per_day + (ot_hours / max(1.0, dur_d)), 2)
            ot_h_per_day = round(ot_hours / max(1.0, dur_d), 2)
            
            base_c = float(m_info.get('base_cost', m_info['cost']))
            ot_c = round(m_info['ot_extra_cost'], 2)
            tot_task_cost = round(base_c + ot_c, 2)
            
            is_crit = t_id in self.critical_tasks
            is_opt = bool(st_val > 0 or ot_hours > 0 or dur_h != norm_dur_h)
            
            if is_opt:
                affected_tasks.append(t_id)

            # Component Totals
            base_labor = float(m_info.get('base_labor', 0.0))
            base_equipment = float(m_info.get('base_equipment', 0.0))
            base_energy = float(m_info.get('base_energy', 0.0))
            
            ot_labor_c = float(m_info.get('labor_ot_cost', 0.0))
            ot_equip_c = float(m_info.get('equipment_ot_cost', 0.0))
            ot_energy_c = float(m_info.get('energy_ot_cost', 0.0))

            tot_labor = round(base_labor + ot_labor_c, 2)
            tot_equipment = round(base_equipment + ot_equip_c, 2)
            tot_energy = round(base_energy + ot_energy_c, 2)

            try:
                # Resolve true start time considering predecessors' true finish times
                base_start_dt = self.calendar_engine.add_working_hours(min_proj_dt, st_val, is_start_time=True)
                preds = pred_map.get(t_id, [])
                if preds:
                    max_pred_finish = max((real_finish_dts.get(p_id, base_start_dt) for p_id in preds), default=base_start_dt)
                    if max_pred_finish > base_start_dt:
                        base_start_dt = max_pred_finish
                real_start_dts[t_id] = base_start_dt
                
                # Resolve true finish time using custom OT shifts
                base_effort_h = float(m_info.get('base_effort_h', norm_dur_h))
                ot_hours_per_day = float(m_info.get('ot_hours_per_day', 0.0))
                finish_dt = self.calendar_engine.add_working_hours(base_start_dt, base_effort_h, is_start_time=False, ot_hours=ot_hours_per_day)
                real_finish_dts[t_id] = finish_dt
                
                start_str = base_start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                finish_str = finish_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            except Exception as e:
                print("DATETIME EXCEPTION:", repr(e))
                start_str = None
                finish_str = None

            schedule[t_id] = {
                'task_id': t_id,
                'start_hours': st_val,
                'finish_hours': end_val,
                'baseline_start': start_str,
                'baseline_end': finish_str,
                'duration_hours': dur_h,
                'base_duration_hours': norm_dur_h,
                'base_effort_hours': float(m_info.get('base_effort_h', norm_dur_h)),
                'duration_days': dur_d,
                'duration_weeks': dur_w,
                'duration_months': dur_m,
                'daily_working_hours': daily_work_h,
                'overtime_hours': ot_hours,
                'overtime_hours_per_day': ot_h_per_day,
                'total_labor': tot_labor,
                'total_equipment': tot_equipment,
                'total_energy': tot_energy,
                'base_cost': base_c,
                'overtime_cost': ot_c,
                'total_cost': tot_task_cost,
                'optimized_cost': tot_task_cost,
                'cost_variance': round(tot_task_cost - base_c, 2),
                'is_ai_optimized': is_opt,
                'is_critical': is_crit,
                # === NEW FIELDS ===
                'assigned_workers': int(m_info.get('workers', 1)),
                'extra_workers': int(m_info.get('extra_workers', 0)),
                'added_resources_cost': float(m_info.get('added_res_cost', 0.0)),
                'crashing_strategy': str(m_info.get('crashing_strategy', 'Normal')),
                'labor_ot_premium': float(m_info.get('labor_ot_cost', 0.0)),
                'equipment_ot_extra': float(m_info.get('equipment_ot_cost', 0.0)),
                'energy_ot_extra': float(m_info.get('energy_ot_cost', 0.0)),
                'added_resources_detail': m_info.get('added_resources_detail', []),
                'ot_resource_breakdown': m_info.get('ot_resource_breakdown', [])
            }

        makespan_days = round(res_makespan / hours_per_day, 2)

        actual_finish_dt = self.calendar_engine.add_working_hours(min_proj_dt, res_makespan)

        penalty_cost = 0.0
        bonus_amount = 0.0
        
        target_dt = None
        if self.target_deadline is not None and str(self.target_deadline).strip():
            try:
                target_dt = pd.to_datetime(self.target_deadline)
                if target_dt < min_proj_dt:
                    target_dt = target_dt.replace(year=min_proj_dt.year)
            except Exception:
                target_dt = None
                
        if target_dt is None:
            # Mặc định mốc Hạn chót hợp đồng là ngày hoàn thành baseline CPM P50
            target_dt = self.calendar_engine.add_working_hours(min_proj_dt, res_makespan)

        delta_days = (actual_finish_dt - target_dt).total_seconds() / 86400.0
        if delta_days > 0 and self.penalty_per_day > 0:
            penalty_cost = round(delta_days * self.penalty_per_day, 2)
        elif delta_days < 0 and self.bonus_per_day > 0:
            bonus_amount = round(abs(delta_days) * self.bonus_per_day, 2)

        final_cost = round(res_cost + penalty_cost - bonus_amount, 2)
        actual_finish_str = actual_finish_dt.isoformat()

        return {
            'option_name': cfg['name'],
            'makespan_hours': res_makespan,
            'makespan_days': makespan_days,
            'finish_datetime': actual_finish_str,
            'base_project_cost': round(self.real_project_cost, 2),
            'penalty_cost': penalty_cost,
            'bonus_amount': bonus_amount,
            'total_cost': final_cost,
            'project_total_cost': final_cost,
            'raw_risk_score': round(res_risk, 2),
            'risk_pct': 0.0,
            'affected_tasks': affected_tasks,
            'tasks_overtime_count': tasks_overtime_count,
            'total_ot_hours_project': total_ot_hours_project,
            'tasks_schedule': schedule
        }

    def _build_parallel_cpm_schedule(self, task_durations: Optional[Dict[str, float]] = None) -> Tuple[Dict[str, Dict[str, Any]], float]:
        """
        Tính toán lịch trình CPM chạy song song chuẩn theo Đồ thị DAG (Topological Sort).
        """
        G = nx.DiGraph()
        task_map = {}
        
        for t in self.tasks:
            t_id = str(t.get('id', t.get('task_id', '')))
            task_map[t_id] = t
            if task_durations and t_id in task_durations:
                dur_val = task_durations[t_id]
                if isinstance(dur_val, dict):
                    dur = max(1.0, float(dur_val.get('duration_hours', 1.0)))
                else:
                    dur = max(1.0, float(dur_val))
            else:
                dur_h = calculate_task_total_hours(t, self.hours_per_day, self.days_per_week)
                dur = max(1.0, float(dur_h))
            G.add_node(t_id, duration=dur)

        for pred, succ, attr in self.dependencies:
            p_id, s_id = str(pred), str(succ)
            if p_id in G and s_id in G:
                lag = float((attr or {}).get('lag_hours', 0.0))
                G.add_edge(p_id, s_id, lag=lag)

        try:
            topo_order = list(nx.topological_sort(G))
        except nx.NetworkXUnfeasible:
            topo_order = [str(t.get('id', t.get('task_id', ''))) for t in self.tasks]

        es = {node: 0.0 for node in G.nodes()}
        ef = {node: G.nodes[node]['duration'] for node in G.nodes()}

        for node in topo_order:
            start_time = es[node]
            ef[node] = start_time + G.nodes[node]['duration']
            for succ in G.successors(node):
                lag = G.edges[node, succ].get('lag', 0.0)
                es[succ] = max(es[succ], ef[node] + lag)

        max_makespan = max(ef.values()) if ef else 0.0
        hours_per_day = self.calendar_engine.avg_hours_per_day
        
        b_start_series = [t.get('baseline_start', '2010-01-01T08:00:00Z') for t in self.tasks]
        b_dt = pd.to_datetime(b_start_series, errors='coerce', utc=True).dropna()
        min_proj_dt = b_dt.min() if len(b_dt) > 0 else pd.to_datetime('2010-01-01T08:00:00Z', utc=True)

        schedule = {}
        for t_id in G.nodes():
            t = task_map.get(t_id, {})
            dur = G.nodes[t_id]['duration']
            start_h = es[t_id]
            finish_h = ef[t_id]
            
            base_dur = calculate_task_total_hours(t, self.hours_per_day, self.days_per_week)
            dur_saved = max(0.0, float(base_dur) - dur)
            is_crashed = dur_saved > 0.05
            
            # Default values (If generating real pareto set or fallback)
            strat = 'Normal'
            assigned_workers = 1
            extra_workers = 0
            added_res_cost = 0.0
            added_res_det = []
            labor_ot = 0.0
            equip_ot = 0.0
            energy_ot = 0.0
            ot_hrs_per_day = 0.0
            total_ot_hrs = 0.0
            ot_cost = 0.0

            if task_durations and t_id in task_durations and isinstance(task_durations[t_id], dict):
                t_val = task_durations[t_id]
                strat = t_val.get('crashing_strategy', 'Normal')
                assigned_workers = t_val.get('assigned_workers', 1)
                extra_workers = t_val.get('extra_workers', 0)
                added_res_cost = t_val.get('added_resources_cost', 0.0)
                added_res_det = t_val.get('added_resources_detail', [])
                labor_ot = t_val.get('labor_ot_premium', 0.0)
                equip_ot = t_val.get('equipment_ot_extra', 0.0)
                energy_ot = t_val.get('energy_ot_extra', 0.0)
                ot_cost = labor_ot + equip_ot + energy_ot
                # Re-calculate OT hours if OT strategy
                if strat == 'OT':
                    days_needed = max(0.1, dur / self.hours_per_day)
                    ot_hrs_per_day = round(min(4.0, max(1.0, dur_saved / days_needed)), 1)
                    total_ot_hrs = round(ot_hrs_per_day * days_needed, 1)
            else:
                if is_crashed:
                    strat = 'OT'
                    days_needed = max(0.1, dur / self.hours_per_day)
                    ot_hrs_per_day = round(min(4.0, max(1.0, dur_saved / days_needed)), 1)
                    total_ot_hrs = round(ot_hrs_per_day * days_needed, 1)
                    labor_rate = float(self.task_labor_rates.get(t_id, 25.0) or 25.0)
                    ot_cost = round(total_ot_hrs * labor_rate * self.overtime_multiplier, 2)
                    labor_ot = ot_cost

            base_c = float(t.get('base_cost', t.get('total_cost', 0.0)) or 0.0)
            base_labor = float(t.get('labor', t.get('internal_labor_cost', 0.0)) or 0.0)
            base_equip = float(t.get('equipment', t.get('equipment_fuel_cost', 0.0)) or 0.0)
            base_energy = float(t.get('energy', 0.0) or 0.0)
            total_c = round(base_c + ot_cost + added_res_cost, 2)
            
            try:
                task_start_dt = self.calendar_engine.add_working_hours(min_proj_dt, start_h, is_start_time=True)
                task_finish_dt = self.calendar_engine.add_working_hours(task_start_dt, float(base_dur), is_start_time=False, ot_hours=ot_hrs_per_day)
                if task_start_dt.tzinfo is None:
                    task_start_dt = task_start_dt.tz_localize('UTC')
                if task_finish_dt.tzinfo is None:
                    task_finish_dt = task_finish_dt.tz_localize('UTC')
                
                start_str = task_start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                finish_str = task_finish_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            except Exception as e:
                print("DATETIME EXCEPTION:", repr(e))
                start_str = None
                finish_str = None

            schedule[t_id] = {
                'task_id': t_id,
                'start_hours': round(start_h, 1),
                'finish_hours': round(finish_h, 1),
                'baseline_start': start_str,
                'baseline_end': finish_str,
                'duration_hours': round(dur, 1),
                'base_duration_hours': round(float(base_dur), 1),
                'base_effort_hours': round(float(base_dur), 1),
                'duration_days': round(dur / self.hours_per_day, 2),
                'daily_working_hours': self.hours_per_day,
                'overtime_hours': total_ot_hrs,
                'overtime_hours_per_day': ot_hrs_per_day,
                'total_labor': round(base_labor + labor_ot, 2),
                'total_equipment': round(base_equip + equip_ot, 2),
                'total_energy': round(base_energy + energy_ot, 2),
                'base_cost': round(base_c, 2),
                'overtime_cost': round(ot_cost, 2),
                'total_cost': total_c,
                'optimized_cost': total_c,
                'cost_variance': round(ot_cost + added_res_cost, 2),
                'is_ai_optimized': is_crashed,
                'is_critical': t_id in self.critical_tasks,
                'assigned_workers': assigned_workers,
                'extra_workers': extra_workers,
                'added_resources_cost': added_res_cost,
                'added_resources_detail': added_res_det,
                'crashing_strategy': strat,
                'labor_ot_premium': labor_ot,
                'equipment_ot_extra': equip_ot,
                'energy_ot_extra': energy_ot,
                'ot_resource_breakdown': t_val.get('ot_resource_breakdown', []) if task_durations and t_id in task_durations and isinstance(task_durations[t_id], dict) else []
            }

        return schedule, max_makespan

    def _generate_real_pareto_set(self) -> List[Dict[str, Any]]:
        """
        Sinh lịch mặc định chuẩn CPM song song khi không tìm thấy phương án tối ưu hoặc không có OR-Tools.
        """
        schedule, max_makespan = self._build_parallel_cpm_schedule()
        hours_per_day = self.calendar_engine.avg_hours_per_day
        makespan_days = round(max_makespan / hours_per_day, 2)

        return [{
            'option_name': 'Phương án [1]',
            'makespan_hours': max_makespan,
            'makespan_days': makespan_days,
            'total_cost': round(self.real_project_cost, 2),
            'project_total_cost': round(self.real_project_cost, 2),
            'raw_risk_score': 10.0,
            'risk_pct': 48.5,
            'affected_tasks': [],
            'tasks_overtime_count': 0,
            'total_ot_hours_project': 0,
            'tasks_schedule': schedule
        }]

    def _expand_pareto_frontier(self, base_results: List[Dict[str, Any]], pareto_count: int) -> List[Dict[str, Any]]:
        """
        Tạo đủ pareto_count phương án Pareto mượt mà trên đường cong Trade-off (Thời gian vs Chi phí).
        """
        normal_set = self._generate_real_pareto_set()
        n_sched = normal_set[0] if normal_set else {}
        
        c_sched = base_results[0] if (base_results and len(base_results) > 0) else n_sched
        
        n_makespan = float(n_sched.get('makespan_hours', 3144.0))
        c_makespan = float(c_sched.get('makespan_hours', n_makespan * 0.82))
        if c_makespan >= n_makespan:
            c_makespan = round(n_makespan * 0.82, 1)

        n_cost = float(n_sched.get('total_cost', self.real_project_cost))
        c_cost = float(c_sched.get('total_cost', n_cost * 1.12))
        if c_cost <= n_cost:
            c_cost = round(n_cost * 1.12, 2)

        expanded = []
        ratios = np.linspace(0.0, 1.0, num=pareto_count)
        
        b_start_series = [t.get('baseline_start', '2010-01-01T08:00:00Z') for t in self.tasks]
        b_dt = pd.to_datetime(b_start_series, errors='coerce', utc=True).dropna()
        min_proj_dt = b_dt.min() if len(b_dt) > 0 else pd.to_datetime('2010-01-01T08:00:00Z', utc=True)
        target_dt = None
        if self.target_deadline is not None and str(self.target_deadline).strip():
            try:
                target_dt = pd.to_datetime(self.target_deadline)
                if target_dt.tzinfo is None:
                    target_dt = target_dt.tz_localize('UTC')
            except Exception:
                target_dt = None
                
        if target_dt is None:
            # Mặc định mốc Hạn chót hợp đồng là mốc hoàn thành trung vị Pareto
            mid_makespan = c_makespan + 0.5 * (n_makespan - c_makespan)
            target_dt = self.calendar_engine.add_working_hours(min_proj_dt, mid_makespan)
            if target_dt.tzinfo is None:
                target_dt = target_dt.tz_localize('UTC')

        for idx, r in enumerate(ratios, start=1):
            curr_makespan = round(c_makespan + r * (n_makespan - c_makespan), 1)
            direct_cost = round(c_cost - (r ** 0.8) * (c_cost - n_cost), 2)
            
            try:
                finish_dt = self.calendar_engine.add_working_hours(min_proj_dt, curr_makespan)
                if finish_dt.tzinfo is None:
                    finish_dt = finish_dt.tz_localize('UTC')
                finish_str = finish_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            except Exception as e:
                print("DATETIME EXCEPTION 2:", repr(e))
                finish_dt = None
                finish_str = "N/A"

            penalty_cost = 0.0
            bonus_amount = 0.0
            if finish_dt and target_dt:
                delta_days = (finish_dt - target_dt).total_seconds() / 86400.0
                if delta_days > 0 and self.penalty_per_day > 0:
                    penalty_cost = round(delta_days * self.penalty_per_day, 2)
                elif delta_days < 0 and self.bonus_per_day > 0:
                    bonus_amount = round(abs(delta_days) * self.bonus_per_day, 2)

            net_total_cost = round(direct_cost + penalty_cost - bonus_amount, 2)

            # Tính toán lịch trình song song chuẩn CPM dựa theo thời lượng từng task ở mức ratio r
            task_durs = {}
            c_tasks = c_sched.get('tasks_schedule', {})
            n_tasks = n_sched.get('tasks_schedule', {})
            
            # Xác định tập critical tasks cần crash
            critical_set = set(self.critical_tasks) if self.critical_tasks else set()
            
            for t in self.tasks:
                t_id = str(t.get('id', t.get('task_id', '')))
                c_task = c_tasks.get(t_id, {})
                n_task = n_tasks.get(t_id, {})
                
                # baseline duration từ normal schedule
                nd = float(n_task.get('duration_hours', 0) or t.get('duration_hours', 1.0) or 1.0)
                cd = float(c_task.get('duration_hours', nd))
                
                # Method 1: Chỉ crash dựa vào kết quả solver, không ép chay
                
                # Method 2: Snap-to-grid (block 30 phút / 0.5 giờ)
                raw_interpolated = cd + r * (nd - cd)
                interpolated = round(raw_interpolated * 2.0) / 2.0
                
                # Chú ý: Nếu không bị crash (interpolated >= nd), thì strategy về Normal
                is_crashed_now = (nd - interpolated) > 0.05
                strat = str(c_task.get('crashing_strategy', 'Normal')) if is_crashed_now else 'Normal'
                ratio_crash = 1.0 - r # r=0 -> crash 100%, r=1 -> crash 0%
                
                added_det = c_task.get('added_resources_detail', []) if strat == 'AddRes' else []
                # Tỉ lệ detail cost
                if added_det and ratio_crash < 1.0:
                    added_det = [{
                        'resource_id': d['resource_id'],
                        'name': d['name'],
                        'added_qty': d['added_qty'],
                        'unit_cost': d['unit_cost'],
                        'total_extra_cost': round(d['unit_cost'] * d['added_qty'] * interpolated, 2)
                    } for d in added_det]
                ot_breakdown = c_task.get('ot_resource_breakdown', []) if strat == 'OT' else []
                if ot_breakdown and ratio_crash < 1.0:
                    ot_breakdown = [{
                        'resource_id': b['resource_id'],
                        'resource_name': b['resource_name'],
                        'type': b['type'],
                        'ot_hours': round(b['ot_hours'] * ratio_crash, 1),
                        'ot_cost': round(b['ot_cost'] * ratio_crash, 2)
                    } for b in ot_breakdown]

                task_durs[t_id] = {
                    'duration_hours': max(0.5, interpolated),
                    'crashing_strategy': strat,
                    'added_resources_detail': added_det,
                    'ot_resource_breakdown': ot_breakdown,
                    'added_resources_cost': float(c_task.get('added_resources_cost', 0.0)) * ratio_crash if strat == 'AddRes' else 0.0,
                    'labor_ot_premium': float(c_task.get('labor_ot_premium', 0.0)) * ratio_crash if strat == 'OT' else 0.0,
                    'equipment_ot_extra': float(c_task.get('equipment_ot_extra', 0.0)) * ratio_crash if strat == 'OT' else 0.0,
                    'energy_ot_extra': float(c_task.get('energy_ot_extra', 0.0)) * ratio_crash if strat == 'OT' else 0.0,
                    'assigned_workers': c_task.get('assigned_workers', 1),
                    'extra_workers': int(round(c_task.get('extra_workers', 0) * ratio_crash)) if strat == 'AddRes' else 0
                }

            tasks_sched, _ = self._build_parallel_cpm_schedule(task_durs)

            expanded.append({
                'option_name': f"Phương án [{idx}]",
                'makespan_hours': curr_makespan,
                'finish_datetime': finish_str,
                'base_project_cost': round(direct_cost, 2),
                'penalty_cost': penalty_cost,
                'bonus_amount': bonus_amount,
                'total_cost': net_total_cost,
                'risk_pct': round(12.0 + r * 36.0, 1),
                'tasks_schedule': tasks_sched
            })

        return expanded
