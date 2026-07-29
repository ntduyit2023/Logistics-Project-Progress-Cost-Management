import pandas as pd
from pathlib import Path

base_dir = Path('ai_pipeline/data/processed')

for p_dir in sorted(base_dir.glob('C*')):
    t_file = p_dir / 'tasks.csv'
    tr_file = p_dir / 'task_resources.csv'
    r_file = p_dir / 'resources.csv'
    
    if not (t_file.exists() and tr_file.exists() and r_file.exists()):
        continue

    print(f"\n==========================================")
    print(f"PROCESSING & NORMALIZING DATASET: {p_dir.name}")
    print(f"==========================================")
    
    df_t = pd.read_csv(t_file)
    df_tr = pd.read_csv(tr_file)
    df_r = pd.read_csv(r_file)

    # Xây dựng map lookup từ resources.csv
    # key: ID hoặc name -> resource info dict
    res_map = {}
    for _, r in df_r.iterrows():
        r_id = str(r.get('ID', r.get('resource_id', ''))).strip()
        r_name = str(r.get('name', '')).strip()
        r_type = str(r.get('type', 'Human')).strip()
        u_cost = float(r.get('unit_cost', 0.0) or 0.0)
        e_cost = float(r.get('energy', 0.0) or 0.0)
        
        info = {'type': r_type, 'unit_cost': u_cost, 'energy': e_cost}
        if r_id:
            res_map[r_id] = info
        if r_name:
            res_map[r_name] = info

    # Nhóm task_resources theo task_id
    tr_by_task = {}
    for _, tr in df_tr.iterrows():
        tid = str(tr.get('task_id', '')).strip()
        rid = str(tr.get('resource_id', '')).strip()
        qty = float(tr.get('request_quantity', 1.0) or 1.0)
        
        if tid not in tr_by_task:
            tr_by_task[tid] = []
        tr_by_task[tid].append({'resource_id': rid, 'quantity': qty})

    # Duyệt qua các task và tính toán/chuẩn hóa labor, equipment, energy
    fixed_count = 0
    zero_energy_fixed = 0

    for idx, row in df_t.iterrows():
        tid = str(row.get('task_id', '')).strip()
        dur_h = float(row.get('duration_hours', 0.0) or 0.0)
        
        calc_labor = 0.0
        calc_equipment = 0.0
        calc_energy = 0.0

        if tid in tr_by_task:
            # Task CÓ gán tài nguyên -> tính chuẩn từ resource assignment
            for item in tr_by_task[tid]:
                rid = item['resource_id']
                qty = item['quantity']
                r_info = res_map.get(rid)
                if not r_info:
                    # thử tìm case-insensitive
                    for k, v in res_map.items():
                        if k.lower() == rid.lower():
                            r_info = v
                            break
                if r_info:
                    r_type = r_info['type']
                    u_cost = r_info['unit_cost']
                    e_cost = r_info['energy']
                    
                    cost = qty * dur_h * u_cost
                    energy = qty * dur_h * e_cost
                    
                    if r_type.lower() in ['human', 'labor', 'personnel']:
                        calc_labor += cost
                    else:
                        calc_equipment += cost
                    calc_energy += energy
        else:
            # Task KHÔNG CÓ tài nguyên -> labor = 0, equipment = 0, energy = 0
            calc_labor = 0.0
            calc_equipment = 0.0
            calc_energy = 0.0

        old_labor = float(row.get('labor', 0.0) or 0.0)
        old_equip = float(row.get('equipment', 0.0) or 0.0)
        old_energy = float(row.get('energy', 0.0) or 0.0)

        # Cập nhật lại vào DataFrame nếu khác biệt
        if abs(old_labor - calc_labor) > 1e-3 or abs(old_equip - calc_equipment) > 1e-3 or abs(old_energy - calc_energy) > 1e-3:
            if tid not in tr_by_task and old_energy > 0:
                zero_energy_fixed += 1
            fixed_count += 1
            df_t.at[idx, 'labor'] = round(calc_labor, 2)
            df_t.at[idx, 'equipment'] = round(calc_equipment, 2)
            df_t.at[idx, 'energy'] = round(calc_energy, 2)
            
            # Cập nhật lại total_cost
            cost_cols = [
                'labor', 'material', 'equipment', 'energy', 'testing_inspection', 'project_management',
                'facility', 'utilities', 'communication', 'training', 'quality_management', 'overtime',
                'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay',
                'expediting', 'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance',
                'contingency_reserve', 'management_reserve', 'transportation', 'ordering', 'packaging',
                'reverse_logistics', 'customs', 'supplier_coordination', 'opportunity_cost', 'capital_cost',
                'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
            ]
            t_cost = 0.0
            for col in cost_cols:
                val = float(df_t.at[idx, col] if col in df_t.columns and pd.notna(df_t.at[idx, col]) else 0.0)
                t_cost += val
            df_t.at[idx, 'total_cost'] = round(t_cost, 2)

    df_t.to_csv(t_file, index=False)
    print(f"   [OK] Adjusted & normalized {fixed_count} tasks (Fixed {zero_energy_fixed} tasks with no resources to energy=0.0)!")
