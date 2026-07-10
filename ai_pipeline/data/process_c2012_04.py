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
        return 'G2_Setup_Utility'
    elif any(k in name_lower for k in ['clearing', 'demolition', 'levelling', 'ground movement', 'embankments', 'removal']):
        return 'G6_Handling_Earthworks'
    elif any(k in name_lower for k in ['concrete', 'formworks', 'pile', 'paving', 'barriers', 'culverts', 'manhole']):
        return 'G1_Material_Subcontract'
    elif any(k in name_lower for k in ['permit', 'license', 'minor works']):
        return 'G4_Contractual'
    elif any(k in name_lower for k in ['testing', 'survey', 'inspection']):
        return 'G1_QA_QC'
    else:
        return 'G1_Internal_Default'

def compute_total_hours(dur_obj, hours_per_day, days_per_week):
    hours_per_week = hours_per_day * days_per_week
    hours_per_month = hours_per_week * 4
    return (dur_obj['months'] * hours_per_month) + (dur_obj['weeks'] * hours_per_week) + (dur_obj['days'] * hours_per_day) + dur_obj['hours']

def main():
    file_path = r'E:\University\Year 3 - 3\DA3\ai_pipeline\data\raw\DSLIB\Excel\C2012-04 Asti-Cuneo Highway.xlsx'
    
    df_schedule = pd.read_excel(file_path, sheet_name='Baseline Schedule')
    df_resources = pd.read_excel(file_path, sheet_name='Resources')
    df_risk = pd.read_excel(file_path, sheet_name='Risk Analysis')
    df_agenda = pd.read_excel(file_path, sheet_name='Agenda')
    
    # 0. Process Agenda
    hours_per_day = len(df_agenda[df_agenda['Unnamed: 1'] == 'Yes'])
    days_per_week = len(df_agenda[df_agenda['Unnamed: 4'] == 'Yes'])
    if hours_per_day == 0: hours_per_day = 8
    if days_per_week == 0: days_per_week = 5
    
    # 1. Process Resources
    res_map = {}
    for i in range(1, len(df_resources)):
        row = df_resources.iloc[i]
        res_name = str(row['Unnamed: 1']).strip()
        res_type = str(row['Unnamed: 2']).strip() 
        cost_unit = row['Unnamed: 5']
        if pd.isna(cost_unit): cost_unit = 0
        res_map[res_name] = {'cost': float(cost_unit), 'type': res_type}
        
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
        succs = parse_edges(row['Unnamed: 4'])
        
        res_demand_str = str(row['Resource Demand'])
        internal_labor_cost = 0
        fuel_rental_cost = 0
        material_cost = 0
        resources_list = []
        
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
                    
                    if r_type == 'Consumable':
                        cost = qty * rate 
                    else:
                        cost = qty * total_hours * rate
                        
                    resources_list.append({"role": rname, "quantity": qty, "hourly_rate": rate, "type": r_type})
                    
                    rname_lower = rname.lower()
                    if 'labourer' in rname_lower or 'worker' in rname_lower or 'coordinator' in rname_lower:
                        internal_labor_cost += cost
                    elif r_type == 'Consumable' or 'material' in rname_lower:
                        material_cost += cost
                    else:
                        fuel_rental_cost += cost
                    
        fixed_cost = float(row['Baseline Costs']) if not pd.isna(row['Baseline Costs']) else 0.0
        var_cost = float(row['Unnamed: 12']) if not pd.isna(row['Unnamed: 12']) else 0.0
        
        classification = analyze_nlp_keywords(task_name)
        
        g1 = {
            "chi_phi_nhan_cong_noi_bo": internal_labor_cost,
            "chi_phi_lam_them_gio": 0.0,
            "chi_phi_nhien_lieu": fuel_rental_cost,
            "chi_phi_qa_qc": 0.0,
            "chi_phi_vat_lieu": material_cost,
            "chi_phi_thue_ngoai": 0.0
        }
        
        g2 = {
            "dao_tao_nhan_cong": 0.0,
            "chi_phi_mat_bang": 0.0,
            "chi_phi_truyen_thong": 0.0,
            "chi_phi_tien_ich": 0.0
        }
        
        g3 = {
            "chi_phi_thay_the": 0.0,
            "chi_phi_lam_them_gio_mot_nhan_cong": 0.0,
            "resources": resources_list
        }
        
        g4 = {
            "chi_phi_bao_hiem": 0.0,
            "chi_phi_giay_phep": 0.0,
            "chi_phi_bao_hanh": 0.0
        }
        
        g6 = {
            "chi_phi_luu_kho": 0.0,
            "chi_phi_van_tai_qt": 0.0,
            "chi_phi_boc_xep": 0.0,
            "chi_phi_thu_hoi": 0.0,
            "chi_phi_loi": 0.0
        }
        
        if classification == 'G2_Setup_Utility':
            g2['chi_phi_mat_bang'] += fixed_cost * 0.8 + var_cost * 0.5
            g2['chi_phi_tien_ich'] += fixed_cost * 0.2 + var_cost * 0.5
        elif classification == 'G6_Handling_Earthworks':
            g6['chi_phi_boc_xep'] += fixed_cost * 0.7 + var_cost
            g1['chi_phi_nhien_lieu'] += fixed_cost * 0.3
        elif classification == 'G1_Material_Subcontract':
            g1['chi_phi_vat_lieu'] += fixed_cost * 0.6 + var_cost * 0.5
            g1['chi_phi_thue_ngoai'] += fixed_cost * 0.4 + var_cost * 0.5
        elif classification == 'G4_Contractual':
            g4['chi_phi_giay_phep'] += fixed_cost * 0.7
            g4['chi_phi_bao_hiem'] += fixed_cost * 0.3
        elif classification == 'G1_QA_QC':
            g1['chi_phi_qa_qc'] += fixed_cost + var_cost
        else:
            g1['chi_phi_vat_lieu'] += fixed_cost
            g2['chi_phi_tien_ich'] += var_cost
            
        task_risk = risk_map.get(task_id, {'optimistic': 100, 'most_probable': 100, 'pessimistic': 100})
        variance = max(0, task_risk['pessimistic'] - 100) / 100.0
        variance = min(0.5, variance)
        
        weather_risk = variance * 0.75
        complexity = variance * 0.25
        
        contingency = max(0, task_risk['most_probable'] - 100) / 100.0
        if contingency == 0: contingency = 0.05
        
        rework = 0.10 if classification == 'G1_QA_QC' else 0.0
        
        g5 = {
            "do_phuc_tap": complexity,
            "du_tru_thoi_tiet": weather_risk,
            "du_phong_bat_ngo": contingency,
            "rui_ro_lam_lai": rework
        }
        
        g7 = {
            "thoi_gian_thuc_hien": duration_obj,
            "thoi_gian_lam_them": 0.0,
            "predecessors": preds,
            "successors": succs,
            "baseline_start": str(row['Baseline'])
        }
        
        output_tasks.append({
            "task_id": task_id,
            "task_name": task_name,
            "g1_direct_cost": g1,
            "g2_indirect_cost": g2,
            "g3_hr_parameters": g3,
            "g4_contractual_cost": g4,
            "g5_risk_multipliers": g5,
            "g6_logistics_cost": g6,
            "g7_temporal": g7
        })
        
    out_dir = r'E:\University\Year 3 - 3\DA3\ai_pipeline\data\processed\C2012-04'
    os.makedirs(out_dir, exist_ok=True)
    
    tasks_rows = []
    edges_rows = []
    resources_rows = []
    schedules_rows = []
    
    for t in output_tasks:
        row = {
            "task_id": t["task_id"],
            "task_name": t["task_name"],
            "g1_labor": t["g1_direct_cost"]["chi_phi_nhan_cong_noi_bo"],
            "g1_ot": t["g1_direct_cost"]["chi_phi_lam_them_gio"],
            "g1_fuel": t["g1_direct_cost"]["chi_phi_nhien_lieu"],
            "g1_qa_qc": t["g1_direct_cost"]["chi_phi_qa_qc"],
            "g1_material": t["g1_direct_cost"]["chi_phi_vat_lieu"],
            "g1_subcontract": t["g1_direct_cost"]["chi_phi_thue_ngoai"],
            "g2_training": t["g2_indirect_cost"]["dao_tao_nhan_cong"],
            "g2_space": t["g2_indirect_cost"]["chi_phi_mat_bang"],
            "g2_comm": t["g2_indirect_cost"]["chi_phi_truyen_thong"],
            "g2_utility": t["g2_indirect_cost"]["chi_phi_tien_ich"],
            "g4_insurance": t["g4_contractual_cost"]["chi_phi_bao_hiem"],
            "g4_license": t["g4_contractual_cost"]["chi_phi_giay_phep"],
            "g4_warranty": t["g4_contractual_cost"]["chi_phi_bao_hanh"],
            "g5_complexity": t["g5_risk_multipliers"]["do_phuc_tap"],
            "g5_weather": t["g5_risk_multipliers"]["du_tru_thoi_tiet"],
            "g5_contingency": t["g5_risk_multipliers"]["du_phong_bat_ngo"],
            "g5_rework": t["g5_risk_multipliers"]["rui_ro_lam_lai"],
            "g6_storage": t["g6_logistics_cost"]["chi_phi_luu_kho"],
            "g6_int_transport": t["g6_logistics_cost"]["chi_phi_van_tai_qt"],
            "g6_handling": t["g6_logistics_cost"]["chi_phi_boc_xep"],
            "g6_recovery": t["g6_logistics_cost"]["chi_phi_thu_hoi"],
            "g6_error": t["g6_logistics_cost"]["chi_phi_loi"],
            "g7_dur_months": t["g7_temporal"]["thoi_gian_thuc_hien"]["months"],
            "g7_dur_weeks": t["g7_temporal"]["thoi_gian_thuc_hien"]["weeks"],
            "g7_dur_days": t["g7_temporal"]["thoi_gian_thuc_hien"]["days"],
            "g7_dur_hours": t["g7_temporal"]["thoi_gian_thuc_hien"]["hours"],
            "g7_ot_hours": t["g7_temporal"]["thoi_gian_lam_them"]
        }
        tasks_rows.append(row)
        
        for p in t["g7_temporal"]["predecessors"]:
            edges_rows.append({
                "source_id": p["target_id"],
                "target_id": t["task_id"],
                "dependency_type": p["dependency_type"],
                "lag_months": p["lag"]["months"],
                "lag_weeks": p["lag"]["weeks"],
                "lag_days": p["lag"]["days"],
                "lag_hours": p["lag"]["hours"]
            })
            
        for r in t["g3_hr_parameters"]["resources"]:
            resources_rows.append({
                "task_id": t["task_id"],
                "role": r["role"],
                "quantity": r["quantity"],
                "hourly_rate": r["hourly_rate"],
                "type": r["type"]
            })
            
        schedules_rows.append({
            "task_id": t["task_id"],
            "baseline_start": t["g7_temporal"]["baseline_start"],
            "baseline_end": str(row['Baseline End']) if 'Baseline End' in row and pd.notna(row['Baseline End']) else "",
            "predecessors": [p["target_id"] for p in t["g7_temporal"]["predecessors"]],
            "successors": []
        })
            
    pd.DataFrame(tasks_rows).to_csv(os.path.join(out_dir, 'tasks.csv'), index=False, encoding='utf-8')
    pd.DataFrame(edges_rows).to_csv(os.path.join(out_dir, 'predecessors.csv'), index=False, encoding='utf-8')
    pd.DataFrame(resources_rows).to_csv(os.path.join(out_dir, 'task_resources.csv'), index=False, encoding='utf-8')
    pd.DataFrame(schedules_rows).to_csv(os.path.join(out_dir, 'task_schedules.csv'), index=False, encoding='utf-8')
        
    print(f"Successfully processed {len(output_tasks)} tasks.")
    print(f"Saved CSVs to {out_dir}")

if __name__ == '__main__':
    main()
