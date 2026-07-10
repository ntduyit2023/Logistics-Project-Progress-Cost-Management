import pandas as pd

def calculate_task_base_cost(row, project_type, df_resources):
    """
    Calculate the Base Cost for a single task row based on the Project Type.
    """
    base_cost = 0.0
    task_id = row['task_id']
    
    # 1. Dynamically calculate g1_labor and g1_ot from resources
    g1_labor = 0.0
    g1_ot = 0.0
    if df_resources is not None and not df_resources.empty:
        # Filter resources for this task
        # Convert both to string to avoid type mismatch
        res_matches = df_resources[df_resources['task_id'].astype(str) == str(task_id)]
        for _, res in res_matches.iterrows():
            qty = res.get('quantity', 0.0)
            h_rate = res.get('hourly_rate', 0.0)
            ot_rate = res.get('ot_rate', h_rate * 1.5) # Default OT rate
            
            # Add to labor and OT
            g1_labor += qty * row.get('g7_dur_hours', 0.0) * h_rate
            g1_ot += qty * row.get('g7_ot_hours', 0.0) * ot_rate
            
    # Common Groups mapping
    g1_fuel = row.get("g1_fuel", 0.0)
    g1_qa_qc = row.get("g1_qa_qc", 0.0)
    g1_material = row.get("g1_material", 0.0)
    g1_subcontract = row.get("g1_subcontract", 0.0)
    
    g2_training = row.get("g2_training", 0.0)
    g2_space = row.get("g2_space", 0.0)
    g2_comm = row.get("g2_comm", 0.0)
    g2_utility = row.get("g2_utility", 0.0)
    
    g4_insurance = row.get("g4_insurance", 0.0)
    g4_license = row.get("g4_license", 0.0)
    g4_warranty = row.get("g4_warranty", 0.0)
    
    g6_storage = row.get("g6_storage", 0.0)
    g6_int_transport = row.get("g6_int_transport", 0.0)
    g6_handling = row.get("g6_handling", 0.0)
    g6_recovery = row.get("g6_recovery", 0.0)
    g6_error = row.get("g6_error", 0.0)

    if project_type == "ITLG":
        g1 = g1_labor + g1_ot + g1_subcontract + g1_qa_qc + g1_material
        g2 = g2_training + g2_space + g2_utility + g2_comm
        g4 = g4_insurance + g4_license + g4_warranty
        g6 = g6_int_transport + g6_storage + g6_recovery + g6_error
        base_cost = g1 + g2 + g4 + g6
        
    elif project_type == "CON":
        g1 = g1_material + g1_qa_qc + g1_subcontract + g1_labor + g1_fuel
        g2 = g2_space + g2_utility
        g4 = g4_license + g4_warranty + g4_insurance
        g6 = g6_storage + g6_handling + g6_recovery + g6_error
        base_cost = g1 + g2 + g4 + g6
        
    elif project_type == "IND":
        g1 = g1_material + g1_subcontract + g1_labor + g1_fuel
        g2 = g2_space + g2_utility
        g4 = g4_license + g4_warranty
        g6 = g6_int_transport + g6_handling + g6_storage
        base_cost = g1 + g2 + g4 + g6
        
    elif project_type == "PRO":
        g1 = g1_subcontract + g1_labor
        g2 = g2_training + g2_space + g2_comm
        base_cost = g1 + g2
        
    elif project_type == "TRL":
        g1 = g1_subcontract + g1_fuel + g1_labor
        g4 = g4_license + g4_insurance
        g6 = g6_int_transport + g6_handling + g6_storage
        base_cost = g1 + g4 + g6
        
    elif project_type == "IT":
        # Fallback for IT if similar to PRO or ITLG
        g1 = g1_labor + g1_ot + g1_subcontract + g1_qa_qc + g1_material
        g2 = g2_training + g2_space + g2_utility + g2_comm
        g4 = g4_insurance + g4_license + g4_warranty
        g6 = g6_int_transport + g6_storage + g6_recovery + g6_error
        base_cost = g1 + g2 + g4 + g6
        
    return base_cost

def calculate_task_total_cost(row, project_type, df_resources):
    base_cost = calculate_task_base_cost(row, project_type, df_resources)
    
    g5_complexity = row.get("g5_complexity", 0.0)
    g5_weather = row.get("g5_weather", 0.0)
    g5_rework = row.get("g5_rework", 0.0)
    g5_contingency = row.get("g5_contingency", 0.0)
    
    risk_factor = 1.0 + g5_complexity + g5_weather + g5_rework + g5_contingency
    
    return base_cost * risk_factor

def calculate_project_totals(df_tasks, df_resources, project_type):
    total_base = 0.0
    total_final = 0.0
    for idx, row in df_tasks.iterrows():
        b_cost = calculate_task_base_cost(row, project_type, df_resources)
        f_cost = calculate_task_total_cost(row, project_type, df_resources)
        total_base += b_cost
        total_final += f_cost
        
    return total_base, total_final

if __name__ == "__main__":
    import os
    
    # Test with C2012-08 (CON)
    base_dir = r"E:\University\Year 3 - 3\DA3\ai_pipeline\data\processed\C2012-08"
    df = pd.read_csv(os.path.join(base_dir, "tasks.csv"))
    df_res = pd.read_csv(os.path.join(base_dir, "task_resources.csv"))
    
    base, final = calculate_project_totals(df, df_res, "CON")
    print(f"C2012-08 (CON) - Base Cost: {base}, Final Cost (with Risk): {final}")
    
    # Test with C2018-09 (ITLG)
    base_dir2 = r"E:\University\Year 3 - 3\DA3\ai_pipeline\data\processed\C2018-09"
    df2 = pd.read_csv(os.path.join(base_dir2, "tasks.csv"))
    df_res2 = pd.read_csv(os.path.join(base_dir2, "task_resources.csv"))
    
    base2, final2 = calculate_project_totals(df2, df_res2, "ITLG")
    print(f"C2018-09 (ITLG) - Base Cost: {base2}, Final Cost (with Risk): {final2}")
