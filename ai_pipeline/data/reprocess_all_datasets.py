import os
import glob
import re
import json
import pandas as pd

# Master reprocessing script for all 5 datasets following Master Architecture

def parse_duration(dur_str):
    if not isinstance(dur_str, str):
        return {"months": 0, "weeks": 0, "days": 0, "hours": 0}
    
    months = 0
    weeks = 0
    days = 0
    hours = 0
    
    m_match = re.search(r'(\d+)m', dur_str)
    w_match = re.search(r'(\d+)w', dur_str)
    d_match = re.search(r'(\d+)d', dur_str)
    h_match = re.search(r'(\d+)h', dur_str)
    
    if m_match: months = int(m_match.group(1))
    if w_match: weeks = int(w_match.group(1))
    if d_match: days = int(d_match.group(1))
    if h_match: hours = int(h_match.group(1))
        
    return {"months": months, "weeks": weeks, "days": days, "hours": hours}

def parse_edges(edge_str):
    if pd.isna(edge_str) or str(edge_str).strip() == '':
        return []
    
    edges = []
    parts = re.split(r'[;,]', str(edge_str))
    
    for part in parts:
        part = part.strip()
        if not part: continue
        
        match = re.match(r'^(\d+)([A-Z]{2})?(?:\+(.*))?$', part)
        if match:
            target_id = int(match.group(1))
            dep_type = match.group(2) if match.group(2) else 'FS'
            lag_str = match.group(3) if match.group(3) else ''
            
            lag_obj = parse_duration(lag_str)
            
            edges.append({
                "target_id": target_id,
                "dependency_type": dep_type,
                "lag": lag_obj
            })
    return edges

def classify_resource(rname):
    r_lower = str(rname).lower()
    equipment_keywords = [
        'truck', 'bulldozer', 'loader', 'roller', 'rolles', 'excavator', 'drilling',
        'mixer', 'crane', 'paler', 'milling', 'pile', 'pruning', 'tank', 'striper',
        'vessel', 'template', 'tugs', 'barges', 'machine', 'pulling', 'hardware', 'server', 'lift'
    ]
    material_keywords = ['materials', 'paving material', 'concrete', 'steel']
    
    if any(k in r_lower for k in material_keywords):
        return 'material'
    elif any(k in r_lower for k in equipment_keywords):
        return 'equipment'
    else:
        return 'labor'

def compute_total_hours(dur_obj, hours_per_day, days_per_week):
    hours_per_week = hours_per_day * days_per_week
    hours_per_month = hours_per_week * 4
    return (dur_obj['months'] * hours_per_month) + (dur_obj['weeks'] * hours_per_week) + (dur_obj['days'] * hours_per_day) + dur_obj['hours']

def calculate_38_costs(project_type, labor_cost, equipment_cost, material_cost, overtime_cost, fixed_cost):
    costs = {k: 0.0 for k in [
        'labor', 'material', 'equipment', 'energy', 'testing_inspection',
        'project_management', 'facility', 'utilities', 'communication', 'training', 'quality_management',
        'overtime', 'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay', 'expediting',
        'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance', 'contingency_reserve', 'management_reserve',
        'transportation', 'ordering', 'packaging', 'reverse_logistics', 'customs', 'supplier_coordination',
        'opportunity_cost', 'capital_cost', 'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
    ]}
    
    costs['labor'] = labor_cost
    costs['equipment'] = equipment_cost
    costs['material'] = material_cost + fixed_cost
    costs['overtime'] = overtime_cost
    
    if project_type == 'CON':
        energy_pct = 0.30 if equipment_cost > 0 else 0.02
        testing_pct = 0.03
    elif project_type == 'ITLG':
        energy_pct = 0.20 if equipment_cost > 0 else 0.015
        testing_pct = 0.05
    else: # PRO
        energy_pct = 0.05 if equipment_cost > 0 else 0.005
        testing_pct = 0.02
        
    costs['energy'] = equipment_cost * energy_pct if equipment_cost > 0 else (labor_cost + costs['material']) * energy_pct
    costs['testing_inspection'] = (costs['labor'] + costs['material'] + costs['equipment'] + costs['energy']) * testing_pct
    
    direct_cost = costs['labor'] + costs['material'] + costs['equipment'] + costs['energy'] + costs['testing_inspection']
    
    if project_type == 'CON':
        profile = {
            'project_management': 0.03, 'facility': 0.02, 'utilities': 0.01, 'communication': 0.01, 'training': 0.005, 'quality_management': 0.015,
            'delay_penalty': 0.02, 'inventory_holding': 0.02, 'waiting_cost': 0.01, 'idle_resource': 0.01, 'revenue_delay': 0.015, 'expediting': 0.01,
            'insurance': 0.025, 'rework': 0.02, 'warranty': 0.015, 'litigation': 0.01, 'regulatory_compliance': 0.015, 'contingency_reserve': 0.025, 'management_reserve': 0.02,
            'transportation': 0.025, 'ordering': 0.01, 'packaging': 0.005, 'reverse_logistics': 0.015, 'customs': 0.01, 'supplier_coordination': 0.02,
            'capital_cost': 0.02, 'financing_cost': 0.02, 'opportunity_cost': 0.01, 'npv_loss': 0.015, 'esg_cost': 0.015, 'carbon_tax': 0.01, 'reputation_cost': 0.01
        }
    elif project_type == 'ITLG':
        profile = {
            'project_management': 0.04, 'facility': 0.025, 'utilities': 0.015, 'communication': 0.04, 'training': 0.02, 'quality_management': 0.03,
            'delay_penalty': 0.025, 'inventory_holding': 0.01, 'waiting_cost': 0.01, 'idle_resource': 0.015, 'revenue_delay': 0.03, 'expediting': 0.015,
            'insurance': 0.02, 'rework': 0.03, 'warranty': 0.02, 'litigation': 0.015, 'regulatory_compliance': 0.02, 'contingency_reserve': 0.03, 'management_reserve': 0.025,
            'transportation': 0.015, 'ordering': 0.01, 'packaging': 0.005, 'reverse_logistics': 0.01, 'customs': 0.01, 'supplier_coordination': 0.025,
            'capital_cost': 0.02, 'financing_cost': 0.015, 'opportunity_cost': 0.025, 'npv_loss': 0.02, 'esg_cost': 0.015, 'carbon_tax': 0.01, 'reputation_cost': 0.03
        }
    else: # PRO
        profile = {
            'project_management': 0.04, 'facility': 0.015, 'utilities': 0.01, 'communication': 0.04, 'training': 0.03, 'quality_management': 0.025,
            'delay_penalty': 0.015, 'inventory_holding': 0.005, 'waiting_cost': 0.01, 'idle_resource': 0.02, 'revenue_delay': 0.02, 'expediting': 0.025,
            'insurance': 0.015, 'rework': 0.015, 'warranty': 0.015, 'litigation': 0.02, 'regulatory_compliance': 0.025, 'contingency_reserve': 0.025, 'management_reserve': 0.02,
            'transportation': 0.01, 'ordering': 0.01, 'packaging': 0.005, 'reverse_logistics': 0.005, 'customs': 0.005, 'supplier_coordination': 0.02,
            'capital_cost': 0.015, 'financing_cost': 0.015, 'opportunity_cost': 0.035, 'npv_loss': 0.02, 'esg_cost': 0.005, 'carbon_tax': 0.00, 'reputation_cost': 0.03
        }
        
    for sub, pct in profile.items():
        costs[sub] = direct_cost * pct
        
    task_base = sum(costs.values())
    task_total = task_base # Total Cost = Base Cost!
    
    return costs, task_base, task_total

def process_single_dataset(proj_id, excel_filename, proj_type, weather_cont):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'raw', 'DSLIB', 'Excel', excel_filename)
    out_dir = os.path.join(script_dir, 'processed', proj_id)
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"--> Processing {proj_id} ({proj_type}) from {excel_filename}...")
    
    df_schedule = pd.read_excel(file_path, sheet_name='Baseline Schedule')
    df_resources = pd.read_excel(file_path, sheet_name='Resources')
    df_risk = pd.read_excel(file_path, sheet_name='Risk Analysis')
    df_agenda = pd.read_excel(file_path, sheet_name='Agenda')
    
    hours_per_day = len(df_agenda[df_agenda['Unnamed: 1'] == 'Yes'])
    days_per_week = len(df_agenda[df_agenda['Unnamed: 4'] == 'Yes'])
    if hours_per_day == 0: hours_per_day = 8
    if days_per_week == 0: days_per_week = 5
    
    # Process Resources Map
    res_map = {}
    for i in range(1, len(df_resources)):
        row = df_resources.iloc[i]
        res_name = str(row['Unnamed: 1']).strip()
        cost_unit = row['Unnamed: 5']
        res_type = str(row.iloc[2]).strip() if df_resources.shape[1] > 2 and pd.notna(row.iloc[2]) else 'Renewable'
        if pd.isna(cost_unit): cost_unit = 0
        res_map[res_name] = {'cost': float(cost_unit), 'type': res_type}
        
    # Process Risk Map
    risk_map = {}
    for i in range(1, len(df_risk)):
        row = df_risk.iloc[i]
        try:
            tid = int(row['General'])
            opt = float(row['Unnamed: 22']) if not pd.isna(row['Unnamed: 22']) else 100
            mp = float(row['Unnamed: 23']) if not pd.isna(row['Unnamed: 23']) else 100
            pes = float(row['Unnamed: 24']) if not pd.isna(row['Unnamed: 24']) else 100
            risk_map[tid] = {'optimistic': opt, 'most_probable': mp, 'pessimistic': pes}
        except:
            continue

    all_wbs = [str(x).strip()[:-2] if str(x).strip().endswith('.0') else str(x).strip() for x in df_schedule['Unnamed: 2'].dropna() if str(x).strip() != 'WBS']
    
    def is_summary_task(wbs_val):
        wbs_val = str(wbs_val).strip()
        if wbs_val.endswith('.0'): wbs_val = wbs_val[:-2]
        if wbs_val.endswith('.0'): wbs_val = wbs_val[:-2]
        if not wbs_val or wbs_val == 'nan': return False
        prefix = wbs_val + '.'
        for other in all_wbs:
            if other.startswith(prefix):
                return True
        return False

    output_tasks = []
    edges_rows = []
    resources_rows = []
    schedules = []
    
    for i in range(1, len(df_schedule)):
        row = df_schedule.iloc[i]
        if pd.isna(row['General']): continue
        try: task_id = int(row['General'])
        except: continue
            
        task_name = str(row['Unnamed: 1']).strip()
        wbs = str(row['Unnamed: 2']).strip()
        if is_summary_task(wbs): continue
        
        dur_str = row['Unnamed: 7']
        duration_obj = parse_duration(dur_str)
        total_hours = compute_total_hours(duration_obj, hours_per_day, days_per_week)
        preds = parse_edges(row['Relations'])
        
        res_demand_str = str(row['Resource Demand'])
        labor_cost = 0.0
        equipment_cost = 0.0
        material_cost = 0.0
        
        if res_demand_str and str(res_demand_str) != 'nan':
            res_parts = res_demand_str.split(';')
            for rp in res_parts:
                rp = rp.strip()
                if not rp: continue
                match = re.match(r'([^\[]+)(?:\[(.*?)\])?', rp)
                if match:
                    rname = match.group(1).strip()
                    qty_str = match.group(2)
                    qty = 1.0
                    if qty_str:
                        q_match = re.search(r'([\d\.]+)', qty_str)
                        if q_match: qty = float(q_match.group(1))
                    
                    r_info = res_map.get(rname, {'cost': 0.0, 'type': 'Renewable'})
                    rate = r_info['cost']
                    cat = classify_resource(rname)
                    
                    if cat == 'material':
                        material_cost += (qty * rate)
                    else:
                        cost = qty * total_hours * rate
                        resources_rows.append({
                            "task_id": f"{proj_id}_{task_id}",
                            "role": rname,
                            "quantity": qty,
                            "hourly_rate": rate,
                            "type": r_info['type']
                        })
                        if cat == 'equipment':
                            equipment_cost += cost
                        else:
                            labor_cost += cost
                            
        fixed_cost = float(row['Baseline Costs']) if not pd.isna(row['Baseline Costs']) else 0.0
        var_cost = float(row['Unnamed: 12']) if 'Unnamed: 12' in row and not pd.isna(row['Unnamed: 12']) else 0.0
        
        costs, task_base, task_total = calculate_38_costs(proj_type, labor_cost, equipment_cost, material_cost, 0.0, fixed_cost + var_cost)
        
        task_risk = risk_map.get(task_id, {'optimistic': 100, 'most_probable': 100, 'pessimistic': 100})
        complexity = max(0, task_risk['pessimistic'] - 100) / 100.0
        complexity = min(0.5, complexity)
        contingency = max(0, task_risk['most_probable'] - 100) / 100.0
        if contingency == 0: contingency = 0.05
        rework = 0.15 if 'test' in task_name.lower() or 'inspect' in task_name.lower() else (0.10 if 'setup' in task_name.lower() or 'code' in task_name.lower() else 0.0)
        
        baseline_start = str(row['Baseline']) if 'Baseline' in row and pd.notna(row['Baseline']) else ""
        r_factor = 1.0 + complexity + weather_cont + contingency + rework
        
        output_row = {
            "task_id": f"{proj_id}_{task_id}",
            "task_name": task_name,
            "baseline_start": baseline_start,
            "duration_months": duration_obj["months"],
            "duration_weeks": duration_obj["weeks"],
            "duration_days": duration_obj["days"],
            "duration_hours": duration_obj["hours"],
            "overtime_hours": 0.0,
            "complexity": complexity,
            "weather_contingency": weather_cont,
            "general_contingency": contingency,
            "rework_risk": rework,
            "risk_factor": r_factor,
            "base_cost": task_base,
            "total_cost": task_total
        }
        output_row.update(costs)
        output_tasks.append(output_row)
        
        for p in preds:
            edges_rows.append({
                "source_id": f"{proj_id}_{p['target_id']}",
                "target_id": f"{proj_id}_{task_id}",
                "dependency_type": p["dependency_type"],
                "lag_months": p["lag"]["months"],
                "lag_weeks": p["lag"]["weeks"],
                "lag_days": p["lag"]["days"],
                "lag_hours": p["lag"]["hours"]
            })
            
        schedules.append({
            "task_id": f"{proj_id}_{task_id}",
            "baseline_start": baseline_start,
            "baseline_end": "",
            "predecessors": [f"{proj_id}_{p['target_id']}" for p in preds],
            "successors": []
        })
        
    pd.DataFrame(output_tasks).to_csv(os.path.join(out_dir, 'tasks.csv'), index=False, encoding='utf-8')
    pd.DataFrame(edges_rows).to_csv(os.path.join(out_dir, 'predecessors.csv'), index=False, encoding='utf-8')
    pd.DataFrame(resources_rows).to_csv(os.path.join(out_dir, 'task_resources.csv'), index=False, encoding='utf-8')
    pd.DataFrame(schedules).to_csv(os.path.join(out_dir, 'task_schedules.csv'), index=False, encoding='utf-8')
    
    print(f"-> Finished {proj_id}: {len(output_tasks)} tasks processed.")

def main():
    datasets = [
        ('C2011-07', 'C2011-07 Patient Transport System.xlsx', 'PRO', 0.0),
        ('C2012-04', 'C2012-04 Asti-Cuneo Highway.xlsx', 'CON', 0.20),
        ('C2012-08', 'C2012-08 Sea Electricity.xlsx', 'CON', 0.25),
        ('C2018-09', 'C2018-09 CarSharing platform.xlsx', 'ITLG', 0.0),
        ('C2019-16', 'C2019-16 Lock Ganzepoot Excel.xlsx', 'CON', 0.20)
    ]
    for proj_id, excel_file, ptype, w_cont in datasets:
        process_single_dataset(proj_id, excel_file, ptype, w_cont)

if __name__ == '__main__':
    main()
