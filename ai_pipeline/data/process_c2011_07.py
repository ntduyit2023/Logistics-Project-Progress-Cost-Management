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
    # Split by ';' or ','
    parts = re.split(r'[;,]', str(edge_str))
    
    for part in parts:
        part = part.strip()
        if not part: continue
        
        # Regex to capture ID, Type, Lag
        # Format: <ID><Type>+<Lag> e.g. 1FS+1w 1d, 3SS, 4FF+2h
        # Also handles cases like '1' (implicit FS)
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
    
    if any(k in name_lower for k in ['meeting', 'brainstorming', 'get-together', 'presentation', 'board']):
        return 'G2_Communication_Space'
    elif any(k in name_lower for k in ['analyze', 'review', 'testing', 'inspect', 'survey']):
        return 'G1_QA_QC'
    elif any(k in name_lower for k in ['purchase', 'buy', 'supplier', 'hardware']):
        return 'G1_Material_Subcontract'
    elif any(k in name_lower for k in ['train', 'guide', 'instruction', 'coach']):
        return 'G2_Training'
    elif any(k in name_lower for k in ['license', 'contract', 'formal document']):
        return 'G4_Contractual'
    else:
        return 'G1_Internal_Default'

def compute_total_hours(dur_obj):
    return (dur_obj['months'] * 160) + (dur_obj['weeks'] * 40) + (dur_obj['days'] * 8) + dur_obj['hours']

def main():
    file_path = r'E:\University\Year 3 - 3\DA3\ai_pipeline\data\raw\DSLIB\Excel\C2011-07 Patient Transport System.xlsx'
    
    # Read Sheets
    df_schedule = pd.read_excel(file_path, sheet_name='Baseline Schedule')
    df_resources = pd.read_excel(file_path, sheet_name='Resources')
    df_risk = pd.read_excel(file_path, sheet_name='Risk Analysis')
    
    # 1. Process Resources Map
    res_map = {}
    for i in range(1, len(df_resources)):
        row = df_resources.iloc[i]
        res_name = str(row['Unnamed: 1']).strip()
        cost_unit = row['Unnamed: 5']
        if pd.isna(cost_unit): cost_unit = 0
        res_map[res_name] = float(cost_unit)
        
    # 2. Process Risk Map
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
            
    # 3. Process Baseline Schedule
    # Collect all WBS to identify summary tasks
    all_wbs = [str(x).strip() for x in df_schedule['Unnamed: 2'].dropna() if str(x).strip() != 'WBS']
    
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
        
        # Skip if ID is missing
        if pd.isna(row['General']):
            continue
            
        try:
            task_id = int(row['General'])
        except:
            continue
            
        task_name = str(row['Unnamed: 1']).strip()
        wbs = str(row['Unnamed: 2']).strip()
        
        # Skip summary tasks (header rows)
        if is_summary_task(wbs):
            continue
        
        # G7: Duration
        dur_str = row['Unnamed: 7']
        duration_obj = parse_duration(dur_str)
        total_hours = compute_total_hours(duration_obj)
        
        # G7: Lag & Edges
        preds = parse_edges(row['Relations'])
        succs = parse_edges(row['Unnamed: 4'])
        
        # G3: Resources & G1 Internal Labor
        res_demand_str = str(row['Resource Demand'])
        internal_labor_cost = 0
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
                    qty = 1.0 # default
                    if qty_str:
                        q_match = re.search(r'([\d\.]+)', qty_str)
                        if q_match:
                            qty = float(q_match.group(1))
                    
                    rate = res_map.get(rname, 0.0)
                    resources_list.append({"role": rname, "quantity": qty, "hourly_rate": rate})
                    internal_labor_cost += (qty * total_hours * rate)
                    
        # Extract Fixed and Variable Cost
        fixed_cost = float(row['Baseline Costs']) if not pd.isna(row['Baseline Costs']) else 0.0
        var_cost = float(row['Unnamed: 12']) if not pd.isna(row['Unnamed: 12']) else 0.0
        
        # NLP Classification
        classification = analyze_nlp_keywords(task_name)
        
        # Initialize 7 Groups
        g1 = {
            "chi_phi_nhan_cong_noi_bo": internal_labor_cost,
            "chi_phi_lam_them_gio": 0.0,
            "chi_phi_nhien_lieu": 0.0,
            "chi_phi_qa_qc": 0.0,
            "chi_phi_vat_lieu": 0.0,
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
        
        if classification == 'G2_Communication_Space':
            g2['chi_phi_truyen_thong'] += var_cost * 0.5
            g2['chi_phi_mat_bang'] += var_cost * 0.5
        elif classification == 'G1_QA_QC':
            g1['chi_phi_qa_qc'] += fixed_cost
        elif classification == 'G1_Material_Subcontract':
            g1['chi_phi_thue_ngoai'] += fixed_cost * 0.8
            g1['chi_phi_vat_lieu'] += fixed_cost * 0.2
        elif classification == 'G2_Training':
            g2['dao_tao_nhan_cong'] += fixed_cost
        elif classification == 'G4_Contractual':
            g4['chi_phi_giay_phep'] += fixed_cost * 0.5
            g4['chi_phi_bao_hiem'] += fixed_cost * 0.5
        else:
            g1['chi_phi_vat_lieu'] += fixed_cost
            g2['chi_phi_tien_ich'] += var_cost
            
        task_risk = risk_map.get(task_id, {'optimistic': 100, 'most_probable': 100, 'pessimistic': 100})
        complexity = max(0, task_risk['pessimistic'] - 100) / 100.0
        complexity = min(0.5, complexity)
        
        contingency = max(0, task_risk['most_probable'] - 100) / 100.0
        if contingency == 0: contingency = 0.05
        
        rework = 0.15 if classification == 'G1_QA_QC' else (0.10 if 'set-up' in task_name.lower() or 'code' in task_name.lower() else 0.0)
        
        g5 = {
            "do_phuc_tap": complexity,
            "du_tru_thoi_tiet": 0.0,
            "du_phong_bat_ngo": contingency,
            "rui_ro_lam_lai": rework
        }
        
        g6 = {
            "chi_phi_luu_kho": 0.0,
            "chi_phi_van_tai_qt": 0.0,
            "chi_phi_boc_xep": 0.0,
            "chi_phi_thu_hoi": 0.0,
            "chi_phi_loi": 0.0
        }
        
        g7 = {
            "thoi_gian_thuc_hien": duration_obj,
            "thoi_gian_lam_them": 0.0,
            "predecessors": preds,
            "successors": succs
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
        
    out_dir = r'E:\University\Year 3 - 3\DA3\ai_pipeline\data\processed\C2011-07'
    os.makedirs(out_dir, exist_ok=True)
    
    # CSV Outputs for PyG / DGL compatibility
    tasks_rows = []
    edges_rows = []
    resources_rows = []
    
    for t in output_tasks:
        # Task Row
        row = {
            "task_id": t["task_id"],
            "task_name": t["task_name"],
            # G1
            "g1_labor": t["g1_direct_cost"]["chi_phi_nhan_cong_noi_bo"],
            "g1_ot": t["g1_direct_cost"]["chi_phi_lam_them_gio"],
            "g1_fuel": t["g1_direct_cost"]["chi_phi_nhien_lieu"],
            "g1_qa_qc": t["g1_direct_cost"]["chi_phi_qa_qc"],
            "g1_material": t["g1_direct_cost"]["chi_phi_vat_lieu"],
            "g1_subcontract": t["g1_direct_cost"]["chi_phi_thue_ngoai"],
            # G2
            "g2_training": t["g2_indirect_cost"]["dao_tao_nhan_cong"],
            "g2_space": t["g2_indirect_cost"]["chi_phi_mat_bang"],
            "g2_comm": t["g2_indirect_cost"]["chi_phi_truyen_thong"],
            "g2_utility": t["g2_indirect_cost"]["chi_phi_tien_ich"],
            # G4
            "g4_insurance": t["g4_contractual_cost"]["chi_phi_bao_hiem"],
            "g4_license": t["g4_contractual_cost"]["chi_phi_giay_phep"],
            "g4_warranty": t["g4_contractual_cost"]["chi_phi_bao_hanh"],
            # G5
            "g5_complexity": t["g5_risk_multipliers"]["do_phuc_tap"],
            "g5_weather": t["g5_risk_multipliers"]["du_tru_thoi_tiet"],
            "g5_contingency": t["g5_risk_multipliers"]["du_phong_bat_ngo"],
            "g5_rework": t["g5_risk_multipliers"]["rui_ro_lam_lai"],
            # G6
            "g6_storage": t["g6_logistics_cost"]["chi_phi_luu_kho"],
            "g6_int_transport": t["g6_logistics_cost"]["chi_phi_van_tai_qt"],
            "g6_handling": t["g6_logistics_cost"]["chi_phi_boc_xep"],
            "g6_recovery": t["g6_logistics_cost"]["chi_phi_thu_hoi"],
            "g6_error": t["g6_logistics_cost"]["chi_phi_loi"],
            # G7 Node
            "g7_dur_months": t["g7_temporal"]["thoi_gian_thuc_hien"]["months"],
            "g7_dur_weeks": t["g7_temporal"]["thoi_gian_thuc_hien"]["weeks"],
            "g7_dur_days": t["g7_temporal"]["thoi_gian_thuc_hien"]["days"],
            "g7_dur_hours": t["g7_temporal"]["thoi_gian_thuc_hien"]["hours"],
            "g7_ot_hours": t["g7_temporal"]["thoi_gian_lam_them"]
        }
        tasks_rows.append(row)
        
        # Edges (Predecessors)
        for p in t["g7_temporal"]["predecessors"]:
            edges_rows.append({
                "source_id": p["target_id"], # Predecessor points TO this task
                "target_id": t["task_id"],
                "dependency_type": p["dependency_type"],
                "lag_months": p["lag"]["months"],
                "lag_weeks": p["lag"]["weeks"],
                "lag_days": p["lag"]["days"],
                "lag_hours": p["lag"]["hours"]
            })
            
        # Resources
        for r in t["g3_hr_parameters"]["resources"]:
            resources_rows.append({
                "task_id": t["task_id"],
                "role": r["role"],
                "quantity": r["quantity"],
                "hourly_rate": r["hourly_rate"]
            })
            
    pd.DataFrame(tasks_rows).to_csv(os.path.join(out_dir, 'tasks.csv'), index=False, encoding='utf-8')
    pd.DataFrame(edges_rows).to_csv(os.path.join(out_dir, 'predecessors.csv'), index=False, encoding='utf-8')
    pd.DataFrame(resources_rows).to_csv(os.path.join(out_dir, 'task_resources.csv'), index=False, encoding='utf-8')
        
    print(f"Successfully processed {len(output_tasks)} tasks.")
    print(f"Saved CSVs to {out_dir}")

if __name__ == '__main__':
    main()
