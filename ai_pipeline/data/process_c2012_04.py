import pandas as pd
import json
import re
import os

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

def analyze_nlp_keywords(task_name):
    name_lower = str(task_name).lower()
    
    if any(k in name_lower for k in ['fixed yard', 'containers', 'fence', 'pegging', 'network service']):
        return 'facility'
    elif any(k in name_lower for k in ['clearing', 'demolition', 'levelling', 'ground movement', 'embankments', 'removal']):
        return 'labor'
    elif any(k in name_lower for k in ['concrete', 'formworks', 'pile', 'paving', 'barriers', 'culverts', 'manhole']):
        return 'material'
    elif any(k in name_lower for k in ['permit', 'license', 'minor works']):
        return 'regulatory_compliance'
    elif any(k in name_lower for k in ['testing', 'survey', 'inspection']):
        return 'testing_inspection'
    else:
        return 'material'

def compute_total_hours(dur_obj, hours_per_day, days_per_week):
    hours_per_week = hours_per_day * days_per_week
    hours_per_month = hours_per_week * 4
    return (dur_obj['months'] * hours_per_month) + (dur_obj['weeks'] * hours_per_week) + (dur_obj['days'] * hours_per_day) + dur_obj['hours']

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'raw', 'DSLIB', 'Excel', 'C2012-04 Asti-Cuneo Highway.xlsx')
    out_dir = os.path.join(script_dir, 'processed', 'C2012-04')
    os.makedirs(out_dir, exist_ok=True)
    
    df_schedule = pd.read_excel(file_path, sheet_name='Baseline Schedule')
    df_resources = pd.read_excel(file_path, sheet_name='Resources')
    df_risk = pd.read_excel(file_path, sheet_name='Risk Analysis')
    df_agenda = pd.read_excel(file_path, sheet_name='Agenda')
    
    # 0. Process Agenda
    hours_per_day = len(df_agenda[df_agenda['Unnamed: 1'] == 'Yes'])
    days_per_week = len(df_agenda[df_agenda['Unnamed: 4'] == 'Yes'])
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
    
    # 1. Process Resources
    res_map = {}
    clean_resources_list = []
    for i in range(1, len(df_resources)):
        row = df_resources.iloc[i]
        res_id = str(row.iloc[0]).strip()
        res_name = str(row['Unnamed: 1']).strip()
        res_type = str(row['Unnamed: 2']).strip() 
        cost_unit = row['Unnamed: 5']
        max_avail = row['Unnamed: 3'] if pd.notna(row['Unnamed: 3']) else 10.0
        if pd.isna(cost_unit): cost_unit = 0
        res_map[res_name] = {'cost': float(cost_unit), 'type': res_type}
        
        # Exclude Materials and Paving Material from resources.csv
        if res_name not in ['Materials', 'Paving Material']:
            clean_resources_list.append({
                "ID": res_id,
                "Name": res_name,
                "Type": res_type,
                "Max Availability": max_avail,
                "Cost/Unit": float(cost_unit)
            })
    pd.DataFrame(clean_resources_list).to_csv(os.path.join(out_dir, 'resources.csv'), index=False)
        
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
        if not wbs_val or wbs_val == 'nan': return False
        prefix = wbs_val + '.'
        for other in all_wbs:
            if other.startswith(prefix):
                return True
        return False

    output_tasks = []
    edges_rows = []
    resources_rows = []
    schedules_rows = []
    
    for i in range(1, len(df_schedule)):
        row = df_schedule.iloc[i]
        
        if pd.isna(row['General']):
            continue
            
        try:
            task_id = int(row['General'])
        except:
            continue
            
        task_name = str(row['Unnamed: 1']).strip()
        wbs = str(row['Unnamed: 2']).strip()
        
        if is_summary_task(wbs):
            continue
        
        dur_str = row['Unnamed: 7']
        duration_obj = parse_duration(dur_str)
        total_hours = compute_total_hours(duration_obj, hours_per_day, days_per_week)
        
        preds = parse_edges(row['Relations'])
        
        res_demand_str = str(row['Resource Demand'])
        internal_labor_cost = 0
        equipment_cost = 0
        allocated_material_cost = 0
        
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
                        if q_match:
                            qty = float(q_match.group(1))
                    
                    res_info = res_map.get(rname, {'cost': 0.0, 'type': 'Renewable'})
                    rate = res_info['cost']
                    r_type = res_info['type']
                    
                    if rname in ['Materials', 'Paving Material']:
                        # Special handling: calculate cost but do NOT add to task_resources.csv
                        cost = qty * rate
                        allocated_material_cost += cost
                    else:
                        cost = qty * total_hours * rate
                        resources_rows.append({
                            "task_id": f"C2012-04_{task_id}",
                            "role": rname,
                            "quantity": qty,
                            "hourly_rate": rate,
                            "type": r_type
                        })
                        rname_lower = rname.lower()
                        if 'labourer' in rname_lower or 'worker' in rname_lower or 'coordinator' in rname_lower:
                            internal_labor_cost += cost
                        else:
                            equipment_cost += cost
                    
        fixed_cost = float(row['Baseline Costs']) if not pd.isna(row['Baseline Costs']) else 0.0
        var_cost = float(row['Unnamed: 12']) if not pd.isna(row['Unnamed: 12']) else 0.0
        
        classification = analyze_nlp_keywords(task_name)
        
        # 38 cost sub-groups mapping
        costs = {k: 0.0 for k in [
            'labor', 'material', 'equipment', 'energy', 'testing_inspection',
            'project_management', 'facility', 'utilities', 'communication', 'training', 'quality_management',
            'overtime', 'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay', 'expediting',
            'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance', 'contingency_reserve', 'management_reserve',
            'transportation', 'ordering', 'packaging', 'reverse_logistics', 'customs', 'supplier_coordination',
            'opportunity_cost', 'capital_cost', 'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
        ]}
        
        costs['labor'] = internal_labor_cost
        costs['equipment'] = equipment_cost
        costs['material'] = allocated_material_cost
        
        if classification == 'facility':
            costs['facility'] += fixed_cost * 0.8
            costs['utilities'] += fixed_cost * 0.2
        elif classification == 'labor':
            costs['labor'] += fixed_cost
        elif classification == 'material':
            costs['material'] += fixed_cost
        elif classification == 'regulatory_compliance':
            costs['regulatory_compliance'] += fixed_cost
        elif classification == 'testing_inspection':
            costs['testing_inspection'] += fixed_cost
        else:
            costs['material'] += fixed_cost
            costs['utilities'] += var_cost
            
        task_risk = risk_map.get(task_id, {'optimistic': 100, 'most_probable': 100, 'pessimistic': 100})
        variance = max(0, task_risk['pessimistic'] - 100) / 100.0
        variance = min(0.5, variance)
        
        weather_risk = variance * 0.75
        complexity = variance * 0.25
        contingency = max(0, task_risk['most_probable'] - 100) / 100.0
        if contingency == 0: contingency = 0.05
        rework = 0.10 if classification == 'testing_inspection' else 0.0
        
        baseline_start = str(row['Baseline']) if 'Baseline' in row and pd.notna(row['Baseline']) else ""
        
        # Base and Total costs
        task_base = sum(costs.values())
        r_factor = 1.0 + complexity + weather_risk + contingency + rework
        task_total = task_base * r_factor
        
        output_row = {
            "task_id": f"C2012-04_{task_id}",
            "task_name": task_name,
            "baseline_start": baseline_start,
            "g7_dur_months": duration_obj["months"],
            "g7_dur_weeks": duration_obj["weeks"],
            "g7_dur_days": duration_obj["days"],
            "g7_dur_hours": duration_obj["hours"],
            "g7_ot_hours": 0.0,
            "complexity": complexity,
            "weather_contingency": weather_risk,
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
                "source_id": f"C2012-04_{p['target_id']}",
                "target_id": f"C2012-04_{task_id}",
                "dependency_type": p["dependency_type"],
                "lag_months": p["lag"]["months"],
                "lag_weeks": p["lag"]["weeks"],
                "lag_days": p["lag"]["days"],
                "lag_hours": p["lag"]["hours"]
            })
            
        schedules_rows.append({
            "task_id": f"C2012-04_{task_id}",
            "baseline_start": baseline_start,
            "baseline_end": str(row['Baseline End']) if 'Baseline End' in row and pd.notna(row['Baseline End']) else "",
            "predecessors": [f"C2012-04_{p['target_id']}" for p in preds],
            "successors": []
        })
            
    pd.DataFrame(output_tasks).to_csv(os.path.join(out_dir, 'tasks.csv'), index=False, encoding='utf-8')
    pd.DataFrame(edges_rows).to_csv(os.path.join(out_dir, 'predecessors.csv'), index=False, encoding='utf-8')
    pd.DataFrame(resources_rows).to_csv(os.path.join(out_dir, 'task_resources.csv'), index=False, encoding='utf-8')
    pd.DataFrame(schedules_rows).to_csv(os.path.join(out_dir, 'task_schedules.csv'), index=False, encoding='utf-8')
    
    print(f"Successfully processed {len(output_tasks)} tasks for C2012-04.")

if __name__ == '__main__':
    main()
