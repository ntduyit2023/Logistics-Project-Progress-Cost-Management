from typing import Dict, List, Any, Optional
from ai_pipeline.models.moi.domain_normalizers import calculate_task_total_hours
from ai_pipeline.models.moi.solver.crashing_builder import calculate_task_inter_costs

def build_task_modes(
    tasks: List[Dict[str, Any]],
    task_resource_requirements: Dict[tuple, float],
    resources_dict: Dict[str, Dict[str, Any]],
    criticality_index: Dict[str, float],
    task_labor_rates: Dict[str, float],
    ai_attention_scores: Dict[str, Dict[str, float]],
    hours_per_day: float,
    days_per_week: float,
    overtime_multiplier: float
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Xây dựng các kịch bản thực thi (Execution Modes) khả thi cho từng công việc (Task).
    
    Hàm này tạo ra không gian tìm kiếm đa chiều (Search Space) cho bộ giải CP-SAT,
    đánh giá và định lượng các phương án "ép tiến độ" (Crashing) khác nhau dựa trên
    Rủi ro AI (HGT), Lịch làm việc thực tế, và Đặc tính Tài nguyên (Human/Machine).

    Bao gồm 4 Mode chính:
        0. Normal (Chế độ Tiêu chuẩn): Không ép tiến độ, giữ nguyên cấu hình ban đầu.
        1. Overtime (Tăng ca): Tăng thời gian làm việc trong ngày (bị giới hạn bởi max_ot_day).
        2. AddRes (Thêm nhân lực/máy móc): Tăng cường số lượng tài nguyên để giảm thời lượng thi công.
        3. Hybrid (Tăng ca + Thêm nhân lực): Kết hợp cả 2 phương án ép tối đa.

    Args:
        tasks (List[Dict[str, Any]]): Danh sách các công việc gốc từ database/CSV.
        task_resource_requirements (Dict[tuple, float]): Bảng phân bổ số lượng tài nguyên ban đầu (t_id, r_id) -> qty.
        resources_dict (Dict[str, Dict[str, Any]]): Danh mục từ điển tài nguyên chi tiết.
        criticality_index (Dict[str, float]): Mức độ khẩn cấp/rủi ro trễ của từng công việc được phân tích bởi AI.
        task_labor_rates (Dict[str, float]): Tổng đơn giá nhân công tiêu chuẩn theo giờ cho từng công việc.
        ai_attention_scores (Dict[str, Dict[str, float]]): Điểm chú ý HGT chỉ ra tài nguyên nào là nút thắt (bottleneck).
        hours_per_day (float): Số giờ làm việc tiêu chuẩn 1 ngày.
        days_per_week (float): Số ngày làm việc tiêu chuẩn 1 tuần.
        overtime_multiplier (float): Hệ số lương ngoài giờ cơ sở (vd: 1.5).

    Returns:
        Dict[str, List[Dict[str, Any]]]: Từ điển ánh xạ ID công việc tới danh sách các Mode cấu hình thực thi.
    """
    # =========================================================================
    # QUÁ TRÌNH KHỞI TẠO VÀ XÉT DUYỆT TỪNG CÔNG VIỆC
    # =========================================================================
    task_modes = {}
    
    for t in tasks:
        t_id = str(t.get('id', t.get('task_id', '')))
        base_effort_h = calculate_task_total_hours(t, hours_per_day, days_per_week)
        ci_score = float(criticality_index.get(t_id, 10.0))

        cost_meta = calculate_task_inter_costs(t, base_effort_h, task_labor_rates)
        base_cost = cost_meta['base_cost']

        # =========================================================================
        # BƯỚC 1: PHÂN LOẠI TÀI NGUYÊN (HUMAN vs MACHINE)
        # =========================================================================
        human_resources = []   # [(r_info_dict, qty), ...]
        machine_resources = [] # [(r_info_dict, qty), ...]

        for (tid, rid), qty in task_resource_requirements.items():
            if str(tid) == t_id and qty > 0:
                r_info = resources_dict.get(str(rid), {})
                r_type = str(r_info.get('type', 'Machine')).lower()
                if r_type == 'human':
                    human_resources.append((r_info, float(qty)))
                else:
                    machine_resources.append((r_info, float(qty)))

        all_resources = human_resources + machine_resources

        # ========== TÍNH OT BOTTLENECK ==========
        if all_resources:
            task_max_ot_per_day = min(
                float(r_info.get('max_overtime_per_day', 4.0 if str(r_info.get('type','')).lower() == 'human' else 16.0))
                for r_info, _ in all_resources
            )
        else:
            task_max_ot_per_day = 0.0

        # ========== TÍNH ĐƠN GIÁ THEO LOẠI ==========
        human_labor_rate_total = sum(qty * float(r.get('unit_cost', 25.0)) for r, qty in human_resources)
        human_ot_multi = min(
            (float(r.get('overtime_multi', overtime_multiplier)) for r, _ in human_resources),
            default=overtime_multiplier
        )

        machine_equip_rate_total = sum(qty * float(r.get('unit_cost', 10.0)) for r, qty in machine_resources)
        machine_energy_rate_total = sum(qty * float(r.get('energy', 0.0)) for r, qty in machine_resources)

        # ========== BASE DURATION (tính từ Effort) ==========
        base_workers = max(1, sum(int(qty) for _, qty in human_resources)) if human_resources else 1
        dur_0 = max(1, int(round(base_effort_h)))
        cost_0 = base_cost
        risk_0 = ci_score * 1.0

        # ========== BASE COST COMPONENTS ==========
        base_labor = float(t.get('labor', cost_meta.get('base_labor', 0.0)) or 0.0)
        base_equipment = float(t.get('equipment') or 0.0)
        base_energy = float(t.get('energy', cost_meta.get('base_energy', 0.0)) or 0.0)

        # =========================================================================
        # BƯỚC 2: TẠO MODE 0 - TIÊU CHUẨN (NORMAL)
        # =========================================================================
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
            'labor_ot_cost': 0.0,
            'equipment_ot_cost': 0.0,
            'energy_ot_cost': 0.0,
            'added_res_cost': 0.0,
            'crashing_strategy': 'Normal'
        }]

        # =========================================================================
        # BƯỚC 3: TẠO MODE 1 - TĂNG CA (OVERTIME)
        # =========================================================================
        allow_ot = task_max_ot_per_day > 0

        if allow_ot:
            dur_days = base_effort_h / hours_per_day
            ot_hours_total = round(dur_days * task_max_ot_per_day, 1)

            new_h_per_day = hours_per_day + task_max_ot_per_day
            dur_1 = max(1, int(round(base_effort_h * hours_per_day / new_h_per_day)))

            ot_breakdown = []
            ot_premium_human = 0.0
            equipment_ot_extra = 0.0
            energy_ot_extra = 0.0

            if human_resources:
                for r_info, qty in human_resources:
                    labor_rate = float(r_info.get('unit_cost', 25.0))
                    multi = float(r_info.get('overtime_multi', overtime_multiplier))
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
                ot_premium_human = round(ot_hours_total * labor_rate_per_h * (overtime_multiplier - 1.0), 2)

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

        # =========================================================================
        # BƯỚC 4: TẠO MODE 2 - THÊM TÀI NGUYÊN (ADD-RES AI-DRIVEN)
        # =========================================================================
        if human_resources:
            extra_workers_needed = max(1, int(round(base_workers * 1.0)))
            
            available_pool = []
            for r_info, qty in human_resources:
                r_id = str(r_info.get('ID', ''))
                max_avail = float(r_info.get('max_availability', 10.0))
                room = max(0, int(max_avail - qty))
                score = ai_attention_scores.get(t_id, {}).get(r_id, 0.0)
                if room > 0:
                    available_pool.append({
                        'id': r_id,
                        'name': str(r_info.get('name', r_id)),
                        'unit_cost': float(r_info.get('unit_cost', 25.0)),
                        'room': room,
                        'score': score
                    })
            
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
                    'total_extra_cost': 0.0
                })
                workers_to_add -= take
            
            actual_extra_workers = extra_workers_needed - workers_to_add
            if actual_extra_workers > 0:
                effective_workers = base_workers
                for d in added_detail:
                    r_info = resources_dict.get(d['resource_id'], {})
                    eff = float(r_info.get('addres_efficiency', 0.7))
                    effective_workers += d['added_qty'] * eff
                    
                dur_2_actual = max(1, int(round(base_effort_h * base_workers / effective_workers)))
                
                added_res_cost = 0.0
                for d in added_detail:
                    d['total_extra_cost'] = d['added_qty'] * d['unit_cost'] * dur_2_actual
                    added_res_cost += d['total_extra_cost']
                    
                net_cost_increase = added_res_cost * 1.1
                
                labor_rate_h = base_labor / max(1.0, dur_0)
                equip_rate_h = base_equipment / max(1.0, dur_0)
                energy_rate_h = base_energy / max(1.0, dur_0)
                
                new_base_labor = round(labor_rate_h * dur_2_actual, 2)
                new_base_equip = round(equip_rate_h * dur_2_actual, 2)
                new_base_energy = round(energy_rate_h * dur_2_actual, 2)
                new_base_cost = round(new_base_labor + new_base_equip + new_base_energy, 2)
                
                cost_2 = round(new_base_cost + net_cost_increase, 2)
                risk_2 = ci_score * 0.85
                
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

                # =========================================================================
                # BƯỚC 5: TẠO MODE 3 - KẾT HỢP (HYBRID OT + ADD-RES)
                # =========================================================================
                if allow_ot and human_resources:
                    dur_days_after_add = dur_2_actual / hours_per_day
                    total_ot_hours_hybrid = round(dur_days_after_add * task_max_ot_per_day, 1)
                    
                    new_h_per_day = hours_per_day + task_max_ot_per_day
                    dur_3 = max(1, int(round(dur_2_actual * hours_per_day / new_h_per_day)))
                    
                    ot_premium_base = 0.0
                    equipment_ot_extra_3 = 0.0
                    energy_ot_extra_3 = 0.0
                    ot_breakdown_3 = []
                    
                    if human_resources:
                        for r_info, qty in human_resources:
                            labor_rate = float(r_info.get('unit_cost', 25.0))
                            multi = float(r_info.get('overtime_multi', overtime_multiplier))
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
                        ot_premium_base = round(total_ot_hours_hybrid * labor_rate_per_h * (overtime_multiplier - 1.0), 2)
                        
                    ot_premium_added = 0.0
                    for d in added_detail:
                        r_info = resources_dict.get(d['resource_id'], {})
                        multi = float(r_info.get('overtime_multi', overtime_multiplier))
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
    
    return task_modes
