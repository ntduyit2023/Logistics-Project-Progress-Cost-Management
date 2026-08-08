import pandas as pd
from typing import Dict, Any, List

def extract_solution_schedule(
    solver: Any,
    makespan_var: Any,
    total_cost_var: Any,
    total_risk_var: Any,
    task_vars: Dict[str, Any],
    cfg: Dict[str, Any],
    calendar_engine: Any,
    tasks: List[Dict[str, Any]],
    dependencies: List[tuple],
    critical_tasks: set,
    target_deadline: Any,
    penalty_per_day: float,
    bonus_per_day: float
) -> Dict[str, Any]:
    """
    Trích xuất kết quả lịch thi công chi tiết từ lời giải CP-SAT.
    
    Hàm này duyệt qua các biến quyết định (decision variables) của OR-Tools (mốc bắt đầu, mốc kết thúc, 
    biến boolean chọn Mode thi công) để phiên dịch lại thành ngày tháng thực tế (Datetime). 
    Sử dụng Topological Pass dựa trên `pred_map` để đảm bảo mốc thời gian tuân thủ logic nối tiếp.

    Args:
        solver (Any): Đối tượng CP-SAT solver đã gọi .Solve() thành công.
        makespan_var (Any): Biến quyết định biểu diễn tổng thời gian hoàn thành dự án.
        total_cost_var (Any): Biến quyết định biểu diễn tổng chi phí dự án.
        total_risk_var (Any): Biến quyết định biểu diễn tổng rủi ro trễ của dự án.
        task_vars (Dict[str, Any]): Từ điển chứa các biến quyết định của từng công việc.
        cfg (Dict[str, Any]): Cấu hình kịch bản (weights, giới hạn).
        calendar_engine (WorkingCalendarEngine): Động cơ tính lịch làm việc.
        tasks (List[Dict[str, Any]]): Dữ liệu công việc ban đầu.
        dependencies (List[tuple]): Danh sách các quan hệ logic (pred, succ, lag).
        critical_tasks (set): Tập hợp các công việc nằm trên Đường Gang (Critical Path).
        target_deadline (Any): Hạn chót dự án mục tiêu do người dùng chỉ định.
        penalty_per_day (float): Chi phí phạt mỗi ngày trễ hạn.
        bonus_per_day (float): Tiền thưởng mỗi ngày hoàn thành sớm.

    Returns:
        Dict[str, Any]: Một JSON / Dictionary hoàn chỉnh chứa lịch trình thực thi từng công việc 
                        và các chỉ số cấp dự án (Tổng chi phí, Tổng số giờ OT, Phạt/Thưởng...).
    """
    # =========================================================================
    # BƯỚC 1: ĐỌC KẾT QUẢ TỔNG QUAN TỪ BỘ GIẢI
    # =========================================================================
    res_makespan = solver.Value(makespan_var)
    res_cost = float(solver.Value(total_cost_var)) / 100.0
    res_risk = float(solver.Value(total_risk_var)) / 100.0
    
    schedule = {}
    affected_tasks = []
    total_ot_hours_project = 0
    tasks_overtime_count = 0
    
    hours_per_day = calendar_engine.avg_hours_per_day
    hours_per_week = calendar_engine.hours_per_week
    hours_per_month = calendar_engine.hours_per_month

    # Mốc bắt đầu dự án ban đầu
    b_start_series = [t.get('baseline_start', '2010-01-01T08:00:00') for t in tasks]
    b_dt = pd.to_datetime(b_start_series, errors='coerce').dropna()
    min_proj_dt = b_dt.min() if len(b_dt) > 0 else pd.to_datetime('2010-01-01T08:00:00')
    try:
        min_proj_dt = min_proj_dt.tz_localize(None)
    except Exception:
        min_proj_dt = min_proj_dt.tz_convert(None)
    
    # =========================================================================
    # BƯỚC 2: XÂY DỰNG BẢN ĐỒ TIỀN NHIỆM (PREDECESSOR MAP)
    # Dùng cho việc đẩy lùi lịch dựa trên ngày hoàn thành thực tế của task trước
    # =========================================================================
    pred_map = {t_id: [] for t_id in task_vars.keys()}
    for pred, succ, attr in dependencies:
        p_id, s_id = str(pred), str(succ)
        if s_id in pred_map and p_id in task_vars:
            pred_map[s_id].append(p_id)
            
    # =========================================================================
    # BƯỚC 3: DUYỆT TỪNG CÔNG VIỆC THEO TRẬT TỰ THỜI GIAN (TOPOLOGICAL PASS)
    # =========================================================================
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
        
        is_crit = t_id in critical_tasks
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
            base_start_dt = calendar_engine.add_working_hours(min_proj_dt, st_val, is_start_time=True)
            preds = pred_map.get(t_id, [])
            if preds:
                max_pred_finish = max((real_finish_dts.get(p_id, base_start_dt) for p_id in preds), default=base_start_dt)
                if max_pred_finish > base_start_dt:
                    base_start_dt = calendar_engine.add_working_hours(max_pred_finish, 0.0, is_start_time=True)
            real_start_dts[t_id] = base_start_dt
            
            # Resolve true finish time using custom OT shifts
            ot_hours_per_day = float(m_info.get('ot_hours_per_day', 0.0))
            finish_dt = calendar_engine.add_working_hours(base_start_dt, dur_h, is_start_time=False, ot_hours=ot_hours_per_day)
            real_finish_dts[t_id] = finish_dt
            
            start_str = base_start_dt.strftime('%Y-%m-%dT%H:%M:%S')
            finish_str = finish_dt.strftime('%Y-%m-%dT%H:%M:%S')
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

    # =========================================================================
    # BƯỚC 4: TÍNH TOÁN CÁC CHỈ SỐ TỔNG KẾT DỰ ÁN & TIỀN PHẠT/THƯỞNG
    # =========================================================================
    makespan_days = round(res_makespan / hours_per_day, 2)

    actual_finish_dt = calendar_engine.add_working_hours(min_proj_dt, res_makespan)

    penalty_cost = 0.0
    bonus_amount = 0.0
    
    target_dt = None
    if target_deadline is not None and str(target_deadline).strip():
        try:
            target_dt = pd.to_datetime(target_deadline)
            try:
                target_dt = target_dt.tz_localize(None)
            except Exception:
                target_dt = target_dt.tz_convert(None)
                
            if target_dt < min_proj_dt:
                target_dt = target_dt.replace(year=min_proj_dt.year)
        except Exception:
            target_dt = None
            
    if target_dt is None:
        target_dt = calendar_engine.add_working_hours(min_proj_dt, res_makespan)

    delta_days = (actual_finish_dt - target_dt).total_seconds() / 86400.0
    if delta_days > 0 and penalty_per_day > 0:
        penalty_cost = round(delta_days * penalty_per_day, 2)
    elif delta_days < 0 and bonus_per_day > 0:
        bonus_amount = round(abs(delta_days) * bonus_per_day, 2)

    final_cost = round(res_cost + penalty_cost - bonus_amount, 2)

    return {
        'option_name': cfg['name'],
        'makespan_hours': res_makespan,
        'makespan_days': makespan_days,
        'finish_datetime': actual_finish_dt.strftime('%Y-%m-%dT%H:%M:%S'),
        'base_project_cost': round(res_cost, 2),
        'penalty_cost': penalty_cost,
        'bonus_amount': bonus_amount,
        'total_cost': final_cost,
        'project_total_cost': final_cost,
        'raw_risk_score': round(res_risk, 2),
        'risk_pct': 0.0, # Will be set by Pareto Solver
        'affected_tasks': affected_tasks,
        'tasks_overtime_count': tasks_overtime_count,
        'total_ot_hours_project': total_ot_hours_project,
        'tasks_schedule': schedule
    }
