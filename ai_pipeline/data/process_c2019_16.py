import os
import pandas as pd
import re
from datetime import datetime

def analyze_nlp_keywords(task_name):
    task_lower = task_name.lower()
    
    if any(k in task_lower for k in ['generators', 'lighting', 'toilets', 'fencing']):
        return 'facility'
    elif any(k in task_lower for k in ['transport']):
        return 'transportation'
    elif any(k in task_lower for k in ['remove', 'cleaning']):
        return 'labor'
    elif any(k in task_lower for k in ['put', 'installing', 'replacing', 'supply', 'concrete', 'wooden', 'pumps', 'hinges', 'pivot', 'stairs', 'repairing', 'ladder', 'platforms']):
        return 'material'
    else:
        return 'material'

def parse_duration(dur_str):
    if pd.isna(dur_str):
        return {'months': 0, 'weeks': 0, 'days': 0, 'hours': 0}
    dur_str = str(dur_str).strip().lower()
    
    months = weeks = days = hours = 0
    
    m_match = re.search(r'([\d.]+)\s*m', dur_str)
    w_match = re.search(r'([\d.]+)\s*w', dur_str)
    d_match = re.search(r'([\d.]+)\s*d', dur_str)
    h_match = re.search(r'([\d.]+)\s*h', dur_str)
    
    if m_match and 'min' not in dur_str: months = float(m_match.group(1))
    if w_match: weeks = float(w_match.group(1))
    if d_match: days = float(d_match.group(1))
    if h_match: hours = float(h_match.group(1))
    
    return {'months': months, 'weeks': weeks, 'days': days, 'hours': hours}

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

def process_project():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, 'raw', 'DSLIB', 'Excel', 'C2019-16 Lock Ganzepoot Excel.xlsx')
    out_dir = os.path.join(script_dir, 'processed', 'C2019-16')
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load Data
    df_sched = pd.read_excel(excel_path, sheet_name='Baseline Schedule', skiprows=1)
    df_res = pd.read_excel(excel_path, sheet_name='Resources', skiprows=1)
    df_agenda = pd.read_excel(excel_path, sheet_name='Agenda')
    df_risk = pd.read_excel(excel_path, sheet_name='Risk Analysis', skiprows=1)
    
    # 2. Parse Agenda
    hours_per_day = len(df_agenda[df_agenda['Unnamed: 1'] == 'Yes']) if 'Unnamed: 1' in df_agenda.columns else 8
    days_per_week = len(df_agenda[df_agenda['Unnamed: 4'] == 'Yes']) if 'Unnamed: 4' in df_agenda.columns else 5
    if hours_per_day == 0: hours_per_day = 8
    if days_per_week == 0: days_per_week = 5
    
    # Export Agenda CSVs
    agenda_hours_rows = []
    for i, row in df_agenda.iterrows():
        tr = str(row.iloc[0]).strip()
        is_w = str(row.iloc[1]).strip()
        if tr and tr != 'nan' and 'PMConverter' not in tr:
            agenda_hours_rows.append({"Time Range": tr, "Working": is_w})
    pd.DataFrame(agenda_hours_rows).to_csv(os.path.join(out_dir, 'agenda_working_hours.csv'), index=False)
    
    agenda_days_rows = []
    for i, row in df_agenda.iterrows():
        day_name = str(row.iloc[3]).strip() if df_agenda.shape[1] > 3 else ""
        is_w = str(row.iloc[4]).strip() if df_agenda.shape[1] > 4 else ""
        if day_name and day_name != 'nan':
            agenda_days_rows.append({"Day": day_name, "Working": is_w})
    pd.DataFrame(agenda_days_rows).to_csv(os.path.join(out_dir, 'agenda_working_days.csv'), index=False)
    
    agenda_hol_rows = []
    if df_agenda.shape[1] > 6:
        for i, row in df_agenda.iterrows():
            hol = row.iloc[6]
            if not pd.isna(hol) and str(hol).strip() != 'nan':
                agenda_hol_rows.append({"Holiday": str(hol).strip()})
    pd.DataFrame(agenda_hol_rows).to_csv(os.path.join(out_dir, 'agenda_holidays.csv'), index=False)
    
    # 3. Parse Resources
    res_rates = {}
    resources_list = []
    for i, row in df_res.iterrows():
        if pd.isna(row['Name']): continue
        res_id = str(row['ID']).strip() if 'ID' in row else str(i)
        name = str(row['Name']).strip()
        res_type = str(row['Type']).strip() if 'Type' in row else 'Human'
        cost = float(row['Cost/Unit']) if pd.notna(row['Cost/Unit']) else 0.0
        max_avail = row['Max Availability'] if 'Max Availability' in row and pd.notna(row['Max Availability']) else 10.0
        res_rates[name] = cost
        
        resources_list.append({
            "ID": res_id,
            "Name": name,
            "Type": res_type,
            "Max Availability": max_avail,
            "Cost/Unit": cost
        })
    pd.DataFrame(resources_list).to_csv(os.path.join(out_dir, 'resources.csv'), index=False)
        
    # Default Employee rate if not found
    employee_rate = res_rates.get('Employees', 40.0)

    # 4. Parse Risk
    risk_map = {}
    for i, row in df_risk.iterrows():
        if pd.isna(row['ID']): continue
        task_id = str(row['ID']).strip()
        opt = float(row['Optimistic (%)']) if pd.notna(row['Optimistic (%)']) else 100.0
        mos = float(row['Most probable (%)']) if pd.notna(row['Most probable (%)']) else 100.0
        pes = float(row['Pessimistic (%)']) if pd.notna(row['Pessimistic (%)']) else 100.0
        risk_map[task_id] = {'optimistic': opt, 'most_probable': mos, 'pessimistic': pes}
        
    # 5. Extract Leaf Tasks (WBS Filter)
    leaf_tasks = []
    for i in range(len(df_sched)):
        row = df_sched.iloc[i]
        if pd.isna(row['WBS']): continue
        wbs = str(row['WBS'])
        if wbs.endswith('.0'): wbs = wbs[:-2]
        is_summary = False
        if i + 1 < len(df_sched):
            next_wbs = str(df_sched.iloc[i+1]['WBS'])
            if next_wbs.endswith('.0'): next_wbs = next_wbs[:-2]
            if pd.notna(next_wbs) and next_wbs.startswith(wbs + '.'):
                is_summary = True
        if not is_summary:
            leaf_tasks.append(row)
            
    # 6. Process Tasks
    output_tasks = []
    schedules = []
    resources_rows = []
    edges_rows = []
    
    for row in leaf_tasks:
        task_id = str(row['ID']).strip()
        task_name = str(row['Name'])
        
        # Duration
        dur_str = str(row['Duration']) if pd.notna(row['Duration']) else '0h'
        duration_obj = parse_duration(dur_str)
        total_hours = (duration_obj['months'] * 20 * hours_per_day) + \
                      (duration_obj['weeks'] * 5 * hours_per_day) + \
                      (duration_obj['days'] * hours_per_day) + \
                      duration_obj['hours']
                      
        # Resources using Regex for "Employees[3.00 #3]"
        assigned = str(row['Resource Demand']) if pd.notna(row['Resource Demand']) else ""
        labor_cost = 0.0
        qty = 0.0
        
        if 'Employees' in assigned:
            match = re.search(r'\[([\d.]+)', assigned)
            if match:
                qty = float(match.group(1))
            else:
                qty = 1.0
            
            labor_cost = (qty * employee_rate * total_hours)
            resources_rows.append({
                "task_id": f"C2019-16_{task_id}",
                "role": "Employees",
                "quantity": qty,
                "hourly_rate": employee_rate,
                "type": "Human"
            })
                
        # NLP Classification
        classification = analyze_nlp_keywords(task_name)
        
        # Costs
        fixed_cost = float(row['Fixed Cost']) if not pd.isna(row['Fixed Cost']) else 0.0
        var_cost = float(row['Variable Cost']) if not pd.isna(row['Variable Cost']) else 0.0
        
        # 38 cost sub-groups mapping
        costs = {k: 0.0 for k in [
            'labor', 'material', 'equipment', 'energy', 'testing_inspection',
            'project_management', 'facility', 'utilities', 'communication', 'training', 'quality_management',
            'overtime', 'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay', 'expediting',
            'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance', 'contingency_reserve', 'management_reserve',
            'transportation', 'ordering', 'packaging', 'reverse_logistics', 'customs', 'supplier_coordination',
            'opportunity_cost', 'capital_cost', 'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
        ]}
        
        costs['labor'] = labor_cost
        
        if classification == 'facility':
            costs['facility'] += fixed_cost
        elif classification == 'transportation':
            costs['transportation'] += fixed_cost
        elif classification == 'labor':
            costs['labor'] += fixed_cost
        elif classification == 'material':
            costs['material'] += fixed_cost
        else:
            costs['material'] += fixed_cost
            costs['utilities'] += var_cost
        
        # Risk (G5) using Most Probable Logic
        task_risk = risk_map.get(task_id, {'optimistic': 100.0, 'most_probable': 100.0, 'pessimistic': 100.0})
        complexity = max(0, task_risk['pessimistic'] - task_risk['most_probable']) / 100.0
        contingency = max(0, task_risk['most_probable'] - task_risk['optimistic']) / 100.0
        
        # Dependencies
        preds = str(row['Predecessors']) if pd.notna(row['Predecessors']) else ""
        succs = str(row['Successors']) if pd.notna(row['Successors']) else ""
        
        baseline_start = str(row['Baseline Start']) if 'Baseline Start' in row and pd.notna(row['Baseline Start']) else ""
        
        # Base and Total costs
        task_base = sum(costs.values())
        r_factor = 1.0 + complexity + contingency
        task_total = task_base * r_factor
        
        output_row = {
            "task_id": f"C2019-16_{task_id}",
            "task_name": task_name,
            "baseline_start": baseline_start,
            "duration_months": duration_obj["months"],
            "duration_weeks": duration_obj["weeks"],
            "duration_days": duration_obj["days"],
            "duration_hours": duration_obj["hours"],
            "overtime_hours": 0.0,
            "complexity": complexity,
            "weather_contingency": 0.0,
            "general_contingency": contingency,
            "rework_risk": 0.0,
            "risk_factor": r_factor,
            "base_cost": task_base,
            "total_cost": task_total
        }
        output_row.update(costs)
        output_tasks.append(output_row)
        
        parsed_preds = parse_edges(preds)
        for p in parsed_preds:
            edges_rows.append({
                "source_id": f"C2019-16_{p['target_id']}",
                "target_id": f"C2019-16_{task_id}",
                "dependency_type": p["dependency_type"],
                "lag_months": p["lag"]["months"],
                "lag_weeks": p["lag"]["weeks"],
                "lag_days": p["lag"]["days"],
                "lag_hours": p["lag"]["hours"]
            })
        
        schedules.append({
            "task_id": f"C2019-16_{task_id}",
            "baseline_start": baseline_start,
            "baseline_end": "",
            "predecessors": [f"C2019-16_{p['target_id']}" for p in parsed_preds],
            "successors": []
        })
        
    df_tasks = pd.DataFrame(output_tasks)
    df_tasks.to_csv(os.path.join(out_dir, 'tasks.csv'), index=False, encoding='utf-8')
    
    df_edges = pd.DataFrame(edges_rows)
    df_edges.to_csv(os.path.join(out_dir, 'predecessors.csv'), index=False, encoding='utf-8')
    
    df_schedules = pd.DataFrame(schedules)
    df_schedules.to_csv(os.path.join(out_dir, 'task_schedules.csv'), index=False, encoding='utf-8')
    
    df_resources = pd.DataFrame(resources_rows)
    if not df_resources.empty:
        df_resources.to_csv(os.path.join(out_dir, 'task_resources.csv'), index=False, encoding='utf-8')
    
    print(f"Successfully processed {len(leaf_tasks)} tasks for C2019-16.")
    print(f"Saved CSVs to {out_dir}")

if __name__ == "__main__":
    process_project()
