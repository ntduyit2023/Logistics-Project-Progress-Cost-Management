import os
import pandas as pd
import re
from datetime import datetime

def analyze_nlp_keywords(task_name):
    task_lower = task_name.lower()
    
    # 1. Thuê ngoài (G1_Subcontract)
    if any(k in task_lower for k in ['eandis', 'trafiroad', 'uwlaadpunt', 'installation', 'drilling', 'connecting']):
        return 'G1_Subcontract'
        
    # 2. Vận tải / Logistics (G6)
    if any(k in task_lower for k in ['delivery', 'placing']):
        return 'G6_Transport'
        
    # 3. Vật tư phần mềm (G1_Material)
    if any(k in task_lower for k in ['developing website', 'developing payment']):
        return 'G1_Material'
        
    # 4. Kiểm định / QA_QC (G1_QA_QC)
    if any(k in task_lower for k in ['testing', 'research', 'analysis', 'feasibility', 'study', 'determine']):
        return 'G1_QA_QC'
        
    # 5. Pháp lý / Giấy phép (G4_Permit)
    if any(k in task_lower for k in ['approval', 'contract', 'sign', 'funding', 'city', 'negotiate']):
        return 'G4_Permit'
        
    # 6. Truyền thông (G2_Truyen_thong)
    if any(k in task_lower for k in ['marketing', 'campaign', 'publicity', 'launch', 'promotion']):
        return 'G2_Marketing'
        
    # 7. Tiện ích / Họp hành (G2_Utility)
    if any(k in task_lower for k in ['meeting', 'discuss']):
        return 'G2_Utility'
        
    # Default is G1_Material if it has fixed costs but doesn't match above
    return 'G1_Material'

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

def process_project():
    excel_path = r'E:\University\Year 3 - 3\DA3\ai_pipeline\data\raw\DSLIB\Excel\C2018-09 CarSharing platform.xlsx'
    out_dir = r'E:\University\Year 3 - 3\DA3\ai_pipeline\data\processed\C2018-09'
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load Data
    df_sched = pd.read_excel(excel_path, sheet_name='Baseline Schedule')
    df_res = pd.read_excel(excel_path, sheet_name='Resources')
    df_agenda = pd.read_excel(excel_path, sheet_name='Agenda')
    df_risk = pd.read_excel(excel_path, sheet_name='Risk Analysis')
    
    # 2. Parse Agenda
    hours_per_day = len(df_agenda[df_agenda['Unnamed: 1'] == 'Yes'])
    if hours_per_day == 0: hours_per_day = 8
    
    # 3. Parse Resources (IT/Business roles -> Labor)
    res_rates = {}
    for i, row in df_res.iterrows():
        if i == 0 or pd.isna(row['Unnamed: 1']): continue
        name = str(row['Unnamed: 1']).strip()
        cost = float(row['Unnamed: 5']) if pd.notna(row['Unnamed: 5']) else 0.0
        res_rates[name] = cost

    # 4. Parse Risk
    risk_map = {}
    for i, row in df_risk.iterrows():
        if i == 0 or pd.isna(row['General']): continue
        task_id = str(row['General']).strip()
        opt = float(row['Unnamed: 22']) if pd.notna(row['Unnamed: 22']) else 100.0
        mos = float(row['Unnamed: 23']) if pd.notna(row['Unnamed: 23']) else 100.0
        pes = float(row['Unnamed: 24']) if pd.notna(row['Unnamed: 24']) else 100.0
        risk_map[task_id] = {'optimistic': opt, 'most_probable': mos, 'pessimistic': pes}
        
    # 5. Extract Leaf Tasks (WBS Filter)
    leaf_tasks = []
    for i in range(1, len(df_sched)):
        row = df_sched.iloc[i]
        if pd.isna(row['Unnamed: 2']): continue
        wbs = str(row['Unnamed: 2'])
        is_summary = False
        if i + 1 < len(df_sched):
            next_wbs = str(df_sched.iloc[i+1]['Unnamed: 2'])
            if pd.notna(next_wbs) and next_wbs.startswith(wbs + '.'):
                is_summary = True
        if not is_summary:
            leaf_tasks.append(row)
            
    # 6. Process Tasks
    output_tasks = []
    schedules = []
    resources_rows = []
    
    for row in leaf_tasks:
        task_id = str(row['General']).strip()
        task_name = str(row['Unnamed: 1'])
        
        # Duration
        dur_str = str(row['Unnamed: 7']) if pd.notna(row['Unnamed: 7']) else '0h'
        duration_obj = parse_duration(dur_str)
        total_hours = (duration_obj['months'] * 20 * hours_per_day) + \
                      (duration_obj['weeks'] * 5 * hours_per_day) + \
                      (duration_obj['days'] * hours_per_day) + \
                      duration_obj['hours']
                      
        # Resources
        assigned = str(row['Resource Demand']) if pd.notna(row['Resource Demand']) else ""
        labor_cost = 0.0
        for res_str in assigned.split(','):
            res_str = res_str.strip()
            if not res_str: continue
            
            qty = 1.0
            name = res_str
            if '[' in res_str:
                parts = res_str.split('[')
                name = parts[0].strip()
                qty_str = parts[1].replace(']', '').replace('%', '').strip()
                try:
                    qty = float(qty_str) / 100.0
                except:
                    qty = 1.0
                    
            if name in res_rates:
                hr_rate = res_rates[name]
                labor_cost += (qty * hr_rate * total_hours)
                resources_rows.append({
                    "task_id": task_id,
                    "resource_name": name,
                    "quantity": qty,
                    "hourly_rate": hr_rate,
                    "ot_rate": hr_rate * 1.5
                })
                
        # NLP Classification
        classification = analyze_nlp_keywords(task_name)
        
        # Costs
        fixed_cost = float(row['Baseline Costs']) if not pd.isna(row['Baseline Costs']) else 0.0
        var_cost = float(row['Unnamed: 12']) if not pd.isna(row['Unnamed: 12']) else 0.0
        
        # Init G1 to G6
        g1 = {"chi_phi_nhan_cong_noi_bo": labor_cost, "chi_phi_thue_ngoai": 0.0, "chi_phi_vat_lieu": 0.0, "chi_phi_nhien_lieu": 0.0, "chi_phi_qa_qc": 0.0}
        g2 = {"chi_phi_dao_tao": 0.0, "chi_phi_mat_bang": 0.0, "chi_phi_truyen_thong": 0.0, "chi_phi_tien_ich": 0.0}
        g4 = {"chi_phi_bao_hiem": 0.0, "chi_phi_giay_phep": 0.0, "chi_phi_bao_hanh": 0.0}
        g6 = {"chi_phi_luu_kho": 0.0, "chi_phi_van_tai_qt": 0.0, "chi_phi_boc_xep": 0.0, "chi_phi_thu_hoi": 0.0, "chi_phi_loi": 0.0}
        
        # Assign fixed/var costs based on NLP
        if classification == 'G1_Subcontract': g1['chi_phi_thue_ngoai'] += fixed_cost
        elif classification == 'G6_Transport': g6['chi_phi_van_tai_qt'] += fixed_cost
        elif classification == 'G1_QA_QC': g1['chi_phi_qa_qc'] += fixed_cost
        elif classification == 'G4_Permit': g4['chi_phi_giay_phep'] += fixed_cost
        elif classification == 'G2_Marketing': g2['chi_phi_truyen_thong'] += fixed_cost
        elif classification == 'G2_Utility': g2['chi_phi_tien_ich'] += fixed_cost
        else: g1['chi_phi_vat_lieu'] += fixed_cost # Default
        
        # Risk (G5) using Most Probable Logic
        task_risk = risk_map.get(task_id, {'optimistic': 100.0, 'most_probable': 100.0, 'pessimistic': 100.0})
        complexity = max(0, task_risk['pessimistic'] - task_risk['most_probable']) / 100.0
        contingency = max(0, task_risk['most_probable'] - task_risk['optimistic']) / 100.0
        
        g5 = {
            "do_phuc_tap": complexity,
            "du_tru_thoi_tiet": 0.0,
            "du_phong_bat_ngo": contingency,
            "rui_ro_lam_lai": 0.0
        }
        
        # Dependencies
        preds = str(row['Relations']) if pd.notna(row['Relations']) else ""
        succs = str(row['Unnamed: 4']) if pd.notna(row['Unnamed: 4']) else ""
        
        output_tasks.append({
            "task_id": task_id,
            "task_name": task_name,
            "g1_labor": g1["chi_phi_nhan_cong_noi_bo"],
            "g1_material": g1["chi_phi_vat_lieu"],
            "g1_subcontract": g1["chi_phi_thue_ngoai"],
            "g1_fuel": g1["chi_phi_nhien_lieu"],
            "g1_qa_qc": g1["chi_phi_qa_qc"],
            "g2_training": g2["chi_phi_dao_tao"],
            "g2_space": g2["chi_phi_mat_bang"],
            "g2_communication": g2["chi_phi_truyen_thong"],
            "g2_utility": g2["chi_phi_tien_ich"],
            "g4_insurance": g4["chi_phi_bao_hiem"],
            "g4_license": g4["chi_phi_giay_phep"],
            "g4_warranty": g4["chi_phi_bao_hanh"],
            "g5_complexity": g5["do_phuc_tap"],
            "g5_weather": g5["du_tru_thoi_tiet"],
            "g5_contingency": g5["du_phong_bat_ngo"],
            "g5_rework": g5["rui_ro_lam_lai"],
            "g6_storage": g6["chi_phi_luu_kho"],
            "g6_int_transport": g6["chi_phi_van_tai_qt"],
            "g6_handling": g6["chi_phi_boc_xep"],
            "g6_recovery": g6["chi_phi_thu_hoi"],
            "g7_dur_months": duration_obj["months"],
            "g7_dur_weeks": duration_obj["weeks"],
            "g7_dur_days": duration_obj["days"],
            "g7_dur_hours": total_hours,
            "g7_ot_hours": 0.0
        })
        
        schedules.append({
            "task_id": task_id,
            "baseline_start": str(row['Baseline']),
            "baseline_end": str(row['Unnamed: 6']),
            "predecessors": preds,
            "successors": succs
        })
        
    df_tasks = pd.DataFrame(output_tasks)
    df_tasks.to_csv(os.path.join(out_dir, 'tasks.csv'), index=False, encoding='utf-8')
    
    df_schedules = pd.DataFrame(schedules)
    df_schedules.to_csv(os.path.join(out_dir, 'task_schedules.csv'), index=False, encoding='utf-8')
    
    df_resources = pd.DataFrame(resources_rows)
    if not df_resources.empty:
        df_resources.to_csv(os.path.join(out_dir, 'task_resources.csv'), index=False, encoding='utf-8')
    
    print(f"Successfully processed {len(leaf_tasks)} tasks for C2018-09.")
    print(f"Saved CSVs to {out_dir}")

if __name__ == "__main__":
    process_project()
