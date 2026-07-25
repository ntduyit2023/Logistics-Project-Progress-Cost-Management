import pandas as pd

COST_SUBGROUPS = [
    'labor', 'material', 'equipment', 'energy', 'testing_inspection',
    'project_management', 'facility', 'utilities', 'communication', 'training', 'quality_management',
    'overtime', 'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay', 'expediting',
    'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance', 'contingency_reserve', 'management_reserve',
    'transportation', 'ordering', 'packaging', 'reverse_logistics', 'customs', 'supplier_coordination',
    'opportunity_cost', 'capital_cost', 'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
]

def calculate_task_base_cost(row, project_type=None, df_resources=None):
    """
    Calculate Base Cost as the sum of all 38 cost sub-groups in the task row.
    """
    if 'base_cost' in row and pd.notna(row['base_cost']) and row['base_cost'] > 0:
        return float(row['base_cost'])
        
    base_cost = 0.0
    for col in COST_SUBGROUPS:
        if col in row and pd.notna(row[col]):
            base_cost += float(row[col])
            
    return base_cost

def calculate_task_total_cost(row, project_type=None, df_resources=None):
    """
    In the Master Architecture, Total Cost equals Base Cost.
    Schedule risks are handled in Monte Carlo Simulation for duration delays.
    """
    return calculate_task_base_cost(row, project_type, df_resources)

def calculate_project_totals(df_tasks, df_resources=None, project_type=None):
    """
    Calculate total baseline cost and total final cost for the project.
    Both total_base and total_final equal the sum of task base costs.
    """
    total_base = 0.0
    for idx, row in df_tasks.iterrows():
        b_cost = calculate_task_base_cost(row, project_type, df_resources)
        total_base += b_cost
        
    total_final = total_base  # Total Cost = Base Cost
    return total_base, total_final
