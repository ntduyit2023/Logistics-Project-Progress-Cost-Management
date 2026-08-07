import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
from ai_pipeline.models.moi.utils.calendar_engine import (
    WorkingCalendarEngine
)

def calculate_task_inter_costs(
    task: Dict[str, Any],
    base_dur_h: float,
    task_labor_rates: Dict[str, float]
) -> Dict[str, float]:
    """
    Động cơ tính toán chi phí nội hàm (Dynamic Inter-Cost Engine) cho nhân công, thiết bị, năng lượng.

    Hàm này bóc tách tổng chi phí của một công việc (dựa trên 38 cột chi phí tiêu chuẩn)
    thành các cấu phần (Base Components) và tính toán đơn giá theo giờ (Hourly Rates).
    Kết quả từ hàm này được dùng làm cơ sở cho `modes_builder.py` để ước lượng chi phí
    khi thay đổi thời lượng thi công (Crashing / Overtime).

    Args:
        task (Dict[str, Any]): Dữ liệu công việc từ tasks.csv.
        base_dur_h (float): Thời lượng thi công gốc tính bằng giờ.
        task_labor_rates (Dict[str, float]): Từ điển đơn giá nhân công của các công việc (nếu có).

    Returns:
        Dict[str, float]: Dictionary chứa các chỉ số đơn giá đã được chuẩn hóa.
    """
    # =========================================================================
    # BƯỚC 1: XÁC ĐỊNH TỔNG CHI PHÍ GỐC (BASE COST) CỦA CÔNG VIỆC
    # =========================================================================
    t_id = str(task.get('id', task.get('task_id', '')))
    # Tính tổng chi phí thực tế từ 38 cột chi phí tiêu chuẩn trong tasks.csv
    cost_cols = [
        'labor', 'material', 'equipment', 'energy', 'testing_inspection', 'project_management',
        'facility', 'utilities', 'communication', 'training', 'quality_management', 'overtime',
        'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay',
        'expediting', 'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance',
        'contingency_reserve', 'management_reserve', 'transportation', 'ordering', 'packaging',
        'reverse_logistics', 'customs', 'supplier_coordination', 'opportunity_cost', 'capital_cost',
        'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
    ]
    
    if 'total_cost' in task and float(task.get('total_cost', 0.0) or 0.0) > 0:
        base_cost = float(task['total_cost'])
    elif 'base_cost' in task and float(task.get('base_cost', 0.0) or 0.0) > 0:
        base_cost = float(task['base_cost'])
    else:
        base_cost = sum(float(task.get(c, 0.0) or 0.0) for c in cost_cols)
        if base_cost <= 0:
            base_cost = 100.0
            
    # =========================================================================
    # BƯỚC 2: BÓC TÁCH CHI PHÍ CỐ ĐỊNH TỪNG LOẠI
    # =========================================================================
    base_labor = float(task.get('labor', task.get('direct_labor_cost', 0.0)) or 0.0)
    base_equipment = float(task.get('equipment', task.get('direct_equipment_cost', 0.0)) or 0.0)
    base_energy = float(task.get('energy', task.get('direct_energy_cost', 0.0)) or 0.0)

    # =========================================================================
    # BƯỚC 3: TÍNH ĐƠN GIÁ (RATE) THEO GIỜ LÀM VIỆC
    # =========================================================================
    labor_rate_per_h = float(task_labor_rates.get(t_id, 0.0))
    if labor_rate_per_h <= 0:
        labor_rate_per_h = base_labor / max(1.0, base_dur_h)

    energy_rate_per_h = base_energy / max(1.0, base_dur_h)
    equipment_rate_per_h = base_equipment / max(1.0, base_dur_h)

    return {
        't_id': t_id,
        'base_cost': base_cost,
        'base_labor': base_labor,
        'base_equipment': base_equipment,
        'base_energy': base_energy,
        'labor_rate_per_h': labor_rate_per_h,
        'energy_rate_per_h': energy_rate_per_h,
        'equipment_rate_per_h': equipment_rate_per_h
    }