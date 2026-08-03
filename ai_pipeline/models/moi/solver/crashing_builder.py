import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
from ai_pipeline.models.moi.domain_normalizers import (
    calculate_task_total_hours,
    WorkingCalendarEngine
)

def calculate_task_inter_costs(
    task: Dict[str, Any],
    base_dur_h: float,
    overtime_multiplier: float,
    task_labor_rates: Dict[str, float]
) -> Dict[str, float]:
    """
    Động cơ tính toán chi phí nội hàm (Dynamic Inter-Cost Engine) cho nhân công, thiết bị, năng lượng.
    """
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
            
    # 1. Base components từ các cột chi phí tiêu chuẩn
    base_labor = float(task.get('labor', task.get('direct_labor_cost', 0.0)) or 0.0)
    base_equipment = float(task.get('equipment', task.get('direct_equipment_cost', 0.0)) or 0.0)
    base_energy = float(task.get('energy', task.get('direct_energy_cost', 0.0)) or 0.0)

    # 2. Hourly rates
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