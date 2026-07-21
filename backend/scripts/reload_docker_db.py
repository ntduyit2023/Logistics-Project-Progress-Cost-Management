import asyncio
import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://glpo_admin:glpo_password@db:5432/glpo_db"
)

PROCESSED_DIR = os.getenv("PROCESSED_DIR", "/app/data/processed")
if not os.path.exists(PROCESSED_DIR):
    PROCESSED_DIR = r"E:\University\Year 3 - 3\DA3\ai_pipeline\data\processed"
if not os.path.exists(PROCESSED_DIR):
    PROCESSED_DIR = os.path.abspath(os.path.join(backend_dir, "..", "ai_pipeline", "data", "processed"))

def _safe_read_csv(filepath):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 5:
        try:
            return pd.read_csv(filepath)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

async def reload_docker_database_rigorous():
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    print("========================================================================")
    print("1. DROP VAC TRUNCATE TOAN BO BANG TRONG DOCKER POSTGRESQL (CLEAN RESET)")
    print("========================================================================")
    
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """))
        existing_tables = [row[0] for row in res.fetchall()]
        print(f"Danh sach tat ca cac bang trong Docker DB ({len(existing_tables)} bang): {existing_tables}")
        
        if existing_tables:
            tables_str = ", ".join(f'"{t}"' for t in existing_tables)
            await conn.execute(text(f"TRUNCATE TABLE {tables_str} CASCADE;"))
            await conn.commit()
            print("[SUCCESS] Da truncate xoa sach toan bo du lieu trong tat ca cac bang Docker DB!")

    print("\n========================================================================")
    print("2. IMPORT CHUAN DATASET: RESOURCES.CSV = HUMAN LABOR (HOURLY RATE), OTHER = MATERIAL (FLAT)")
    print("========================================================================")
    
    target_projects = ["C2011-07", "C2012-04", "C2012-08", "C2018-09", "C2019-16"]
    print(f"Thu muc dataset: {PROCESSED_DIR}")
    print(f"Danh sach 5 du an se nap: {target_projects}")
    
    async with engine.connect() as conn:
        for proj_folder in target_projects:
            proj_path = os.path.join(PROCESSED_DIR, proj_folder)
            
            pinfo_csv = os.path.join(proj_path, 'project_info.csv')
            tasks_csv = os.path.join(proj_path, 'tasks.csv')
            edges_csv = os.path.join(proj_path, 'predecessors.csv')
            res_csv = os.path.join(proj_path, 'resources.csv')
            tr_csv = os.path.join(proj_path, 'task_resources.csv')
            sched_csv = os.path.join(proj_path, 'task_schedules.csv')
            
            hours_csv = os.path.join(proj_path, 'agenda_working_hours.csv')
            days_csv = os.path.join(proj_path, 'agenda_working_days.csv')
            holidays_csv = os.path.join(proj_path, 'agenda_holidays.csv')
            
            if not os.path.exists(tasks_csv):
                print(f"[SKIP] Bo qua {proj_folder}: Khong tim thay tasks.csv")
                continue

            # Safely Load DataFrames
            df_pinfo = _safe_read_csv(pinfo_csv)
            df_tasks = pd.read_csv(tasks_csv)
            df_edges = _safe_read_csv(edges_csv)
            df_res = _safe_read_csv(res_csv)
            df_tr = _safe_read_csv(tr_csv)
            df_sched = _safe_read_csv(sched_csv)
            
            df_hours = _safe_read_csv(hours_csv)
            df_days = _safe_read_csv(days_csv)
            df_holidays = _safe_read_csv(holidays_csv)

            # Extract project_info & Agenda
            if not df_pinfo.empty:
                p_row = df_pinfo.iloc[0]
                p_name = str(p_row.get('project_name', f"Project {proj_folder}"))
                p_type = str(p_row.get('project_type', 'ITLG'))
                h_per_day = float(p_row.get('working_hours_per_day', 8.0) or 8.0)
                d_per_week = float(p_row.get('working_days_per_week', 5.0) or 5.0)
                base_cost_pinfo = float(p_row.get('total_baseline_cost', 0.0) or 0.0)
                total_cost_pinfo = float(p_row.get('total_final_cost', 0.0) or 0.0)
            else:
                p_name = f"Project {proj_folder}"
                p_type = "ITLG"
                h_per_day = 8.0
                d_per_week = 5.0
                base_cost_pinfo = 0.0
                total_cost_pinfo = 0.0

            n_tasks = len(df_tasks)
            n_edges = len(df_edges)

            # Insert project record
            res_proj = await conn.execute(
                text("INSERT INTO projects (project_name, type, num_tasks, num_edges, base_cost, total_cost, status) VALUES (:p_name, :p_type, :n_tasks, :n_edges, :b_cost, :t_cost, 'Planning') RETURNING id"),
                {"p_name": p_name, "p_type": p_type, "n_tasks": n_tasks, "n_edges": n_edges, "b_cost": base_cost_pinfo, "t_cost": total_cost_pinfo}
            )
            p_id = res_proj.fetchone()[0]
            print(f"\n---> [LOAD PROJECT #{p_id}] '{p_name}' (Folder: {proj_folder}, Type: {p_type})")

            # Build Agenda JSON & Insert Time Constraints with 1.4 Overtime Multiplier
            working_hours_list = df_hours[df_hours['Working'].astype(str).str.lower() == 'yes']['Time Range'].tolist() if not df_hours.empty and 'Working' in df_hours.columns else []
            working_days_list = df_days[df_days['Working'].astype(str).str.lower() == 'yes']['Day'].tolist() if not df_days.empty and 'Working' in df_days.columns else []
            holidays_list = df_holidays.iloc[:, 0].tolist() if not df_holidays.empty else []

            sched_data = {
                "hours_per_day": h_per_day,
                "days_per_week": d_per_week,
                "working_hours": working_hours_list,
                "working_days": working_days_list
            }
            await conn.execute(
                text("INSERT INTO project_constraint_time (project_id, weekly_schedule, holidays_list, overtime_multiplier) VALUES (:p_id, :sched, :holidays, :ot_mult)"),
                {"p_id": p_id, "sched": json.dumps(sched_data), "holidays": json.dumps(holidays_list), "ot_mult": 1.4}
            )

            # Parse baseline_start from task_schedules.csv
            schedule_map = {}
            if not df_sched.empty:
                t_col_sched = 'task_id' if 'task_id' in df_sched.columns else df_sched.columns[0]
                start_col = 'baseline_start' if 'baseline_start' in df_sched.columns else df_sched.columns[1]
                for _, s_row in df_sched.iterrows():
                    t_id_str = str(s_row[t_col_sched])
                    st_val = s_row.get(start_col)
                    if pd.notna(st_val):
                        try:
                            schedule_map[t_id_str] = pd.to_datetime(st_val).to_pydatetime()
                        except Exception:
                            schedule_map[t_id_str] = None

            # Insert resources from resources.csv -> ALL ARE OFFICIAL HUMAN / LABOR RESOURCES
            res_id_db_map = {}
            res_name_db_map = {}
            res_cost_map = {}
            official_human_resources = set()

            if not df_res.empty:
                r_id_col = 'ID' if 'ID' in df_res.columns else ('id' if 'id' in df_res.columns else df_res.columns[0])
                r_name_col = 'resource_name' if 'resource_name' in df_res.columns else ('name' if 'name' in df_res.columns else df_res.columns[1])
                r_type_col = 'resource_type' if 'resource_type' in df_res.columns else 'type'
                r_cost_col = 'unit_cost' if 'unit_cost' in df_res.columns else ('Cost/Unit' if 'Cost/Unit' in df_res.columns else 'cost')
                r_cap_col = 'capacity' if 'capacity' in df_res.columns else 'max_availability'
                
                for _, r_row in df_res.iterrows():
                    orig_r_id = str(r_row[r_id_col]).strip()
                    r_name = str(r_row.get(r_name_col, 'Resource')).strip()
                    r_type = str(r_row.get(r_type_col, 'Human')).strip()
                    r_cost = float(r_row.get(r_cost_col, 100.0) or 100.0)
                    r_cap = float(r_row.get(r_cap_col, 10.0) or 10.0)
                    
                    res_r = await conn.execute(
                        text("INSERT INTO project_constraint_resource (project_id, resource_name, resource_type, cost_per_unit, max_availability) VALUES (:p_id, :r_name, :r_type, :r_cost, :r_cap) RETURNING id"),
                        {"p_id": p_id, "r_name": r_name, "r_type": r_type, "r_cost": r_cost, "r_cap": r_cap}
                    )
                    db_r_id = res_r.fetchone()[0]
                    res_id_db_map[orig_r_id] = db_r_id
                    res_name_db_map[r_name.lower()] = db_r_id
                    res_cost_map[db_r_id] = r_cost
                    official_human_resources.add(db_r_id)
                print(f"     [OK] Chen {len(res_id_db_map)} official human resources tu resources.csv thanh cong!")

            # Map task resource assignments:
            # - IF in resources.csv -> Human Labor (Hourly Rate * task_work_hours)
            # - IF NOT in resources.csv -> Material Cost (Flat unit cost)
            task_labor_burn_map = {}
            task_material_flat_map = {}

            if not df_tr.empty and res_id_db_map:
                t_col = 'task_id' if 'task_id' in df_tr.columns else df_tr.columns[0]
                r_col = 'resource_id' if 'resource_id' in df_tr.columns else ('resource_name' if 'resource_name' in df_tr.columns else df_tr.columns[1])
                q_col = 'request_quantity' if 'request_quantity' in df_tr.columns else ('quantity' if 'quantity' in df_tr.columns else df_tr.columns[-1])
                
                for _, tr_row in df_tr.iterrows():
                    orig_t = str(tr_row[t_col]).strip()
                    orig_r = str(tr_row[r_col]).strip()
                    qty = float(tr_row[q_col] or 1.0)
                    
                    db_r = res_id_db_map.get(orig_r) or res_name_db_map.get(orig_r.lower())
                    
                    if db_r and db_r in official_human_resources:
                        # Resource is listed in resources.csv -> Human Labor Hourly Rate
                        u_cost = res_cost_map.get(db_r, 40.0)
                        task_labor_burn_map[orig_t] = task_labor_burn_map.get(orig_t, 0.0) + (qty * u_cost)
                    else:
                        # Resource is NOT in resources.csv -> Material Flat Cost
                        u_cost = res_cost_map.get(db_r, 0.0) if db_r else float(tr_row.get('unit_cost', 0.0) or 0.0)
                        task_material_flat_map[orig_t] = task_material_flat_map.get(orig_t, 0.0) + (qty * u_cost)

            # Insert tasks & calculate exact costs
            task_id_db_map = {}
            calc_project_base = 0.0
            calc_project_total = 0.0
            
            for _, row in df_tasks.iterrows():
                raw_id = str(row.get('id', row.get('task_id', row.get('ID', '')))).strip()
                if raw_id.startswith(proj_folder):
                    db_t_id = raw_id
                else:
                    db_t_id = f"{proj_folder}_{raw_id}"
                    
                t_name = str(row.get('task_name', row.get('name', 'Task')))
                
                # Extract all 4 time components
                dur_m = float(row.get('g7_dur_months', row.get('duration_months', 0.0)) or 0.0)
                dur_w = float(row.get('g7_dur_weeks', row.get('duration_weeks', 0.0)) or 0.0)
                dur_d = float(row.get('g7_dur_days', row.get('duration_days', row.get('duration', 0.0))) or 0.0)
                dur_h = float(row.get('g7_dur_hours', row.get('duration_hours', 0.0)) or 0.0)
                ot_h = float(row.get('g7_ot_hours', row.get('overtime_hours', 0.0)) or 0.0)

                # Extract G5 Risk Factors
                g5_comp = float(row.get('g5_complexity', row.get('complexity', 0.0)) or 0.0)
                g5_weat = float(row.get('g5_weather', row.get('weather_contingency', 0.0)) or 0.0)
                g5_cont = float(row.get('g5_contingency', row.get('general_contingency', 0.0)) or 0.0)
                g5_rewo = float(row.get('g5_rework', row.get('rework_risk', 0.0)) or 0.0)

                r_factor = 1.0 + g5_comp + g5_weat + g5_cont + g5_rewo

                # Calculate total task working hours using project Agenda
                task_work_hours = (dur_m * 4.0 * d_per_week * h_per_day) + \
                                  (dur_w * d_per_week * h_per_day) + \
                                  (dur_d * h_per_day) + \
                                  dur_h
                                  
                if task_work_hours <= 1e-6:
                    task_work_hours = h_per_day
                    dur_d = 1.0

                # Extract Costs (G1, G2, G4, G6)
                labor_c = float(row.get('g1_labor', row.get('internal_labor_cost', 0.0)) or 0.0)
                ot_c = float(row.get('overtime_cost', 0.0) or 0.0)
                equip_c = float(row.get('g1_fuel', row.get('equipment_fuel_cost', 0.0)) or 0.0)
                qa_c = float(row.get('g1_qa_qc', row.get('qa_qc_cost', 0.0)) or 0.0)
                mat_c = float(row.get('g1_material', row.get('material_cost', 0.0)) or 0.0)
                out_c = float(row.get('g1_subcontract', row.get('outsourcing_cost', 0.0)) or 0.0)

                train_c = float(row.get('g2_training', row.get('training_cost', 0.0)) or 0.0)
                space_c = float(row.get('g2_space', row.get('facility_rent', 0.0)) or 0.0)
                comm_c = float(row.get('g2_communication', row.get('communication_cost', 0.0)) or 0.0)
                util_c = float(row.get('g2_utility', row.get('utilities_cost', 0.0)) or 0.0)

                insur_c = float(row.get('g4_insurance', row.get('insurance_cost', 0.0)) or 0.0)
                lic_c = float(row.get('g4_license', row.get('licensing_cost', 0.0)) or 0.0)
                warr_c = float(row.get('g4_warranty', row.get('warranty_cost', 0.0)) or 0.0)

                hold_c = float(row.get('g6_storage', row.get('holding_cost', 0.0)) or 0.0)
                freight_c = float(row.get('g6_int_transport', row.get('international_freight', 0.0)) or 0.0)
                handl_c = float(row.get('g6_handling', row.get('handling_cost', 0.0)) or 0.0)
                recov_c = float(row.get('g6_recovery', row.get('reverse_logistics', 0.0)) or 0.0)

                b_start = schedule_map.get(raw_id) or schedule_map.get(db_t_id)

                # Set Material cost if item was not in resources.csv
                if raw_id in task_material_flat_map:
                    mat_c += task_material_flat_map[raw_id]

                # Set Labor cost from official resources.csv * task_work_hours
                if raw_id in task_labor_burn_map:
                    labor_c = task_labor_burn_map[raw_id] * task_work_hours

                # Calculate overtime cost with 1.4x multiplier
                if ot_h > 0 and ot_c <= 1e-6:
                    hourly_rate = (labor_c / task_work_hours) if task_work_hours > 0 else 50.0
                    ot_c = ot_h * hourly_rate * 1.4

                task_base = float(row.get('base_cost', 0.0) or 0.0)
                if task_base <= 1e-6:
                    task_base = labor_c + equip_c + mat_c + out_c + train_c + space_c + comm_c + util_c + insur_c + lic_c + warr_c + hold_c + freight_c + handl_c + recov_c

                task_total = float(row.get('total_cost', 0.0) or 0.0)
                if task_total <= 1e-6:
                    task_total = task_base * r_factor + ot_c + qa_c
                
                calc_project_base += task_base
                calc_project_total += task_total

                await conn.execute(
                    text(
                        "INSERT INTO tasks (id, project_id, task_name, duration_months, duration_weeks, duration_days, duration_hours, overtime_hours, baseline_start, internal_labor_cost, overtime_cost, equipment_fuel_cost, qa_qc_cost, material_cost, outsourcing_cost, training_cost, facility_rent, communication_cost, utilities_cost, insurance_cost, licensing_cost, warranty_cost, complexity, weather_contingency, general_contingency, rework_risk, holding_cost, international_freight, handling_cost, reverse_logistics, risk_factor, base_cost, total_cost, status) "
                        "VALUES (:id, :project_id, :task_name, :duration_months, :duration_weeks, :duration_days, :duration_hours, :overtime_hours, :baseline_start, :internal_labor_cost, :overtime_cost, :equipment_fuel_cost, :qa_qc_cost, :material_cost, :outsourcing_cost, :training_cost, :facility_rent, :communication_cost, :utilities_cost, :insurance_cost, :licensing_cost, :warranty_cost, :complexity, :weather_contingency, :general_contingency, :rework_risk, :holding_cost, :international_freight, :handling_cost, :reverse_logistics, :risk_factor, :base_cost, :total_cost, :status)"
                    ),
                    {
                        "id": db_t_id, "project_id": p_id, "task_name": t_name,
                        "duration_months": dur_m, "duration_weeks": dur_w, "duration_days": dur_d,
                        "duration_hours": dur_h, "overtime_hours": ot_h, "baseline_start": b_start,
                        "internal_labor_cost": labor_c, "overtime_cost": ot_c, "equipment_fuel_cost": equip_c,
                        "qa_qc_cost": qa_c, "material_cost": mat_c, "outsourcing_cost": out_c,
                        "training_cost": train_c, "facility_rent": space_c, "communication_cost": comm_c, "utilities_cost": util_c,
                        "insurance_cost": insur_c, "licensing_cost": lic_c, "warranty_cost": warr_c,
                        "complexity": g5_comp, "weather_contingency": g5_weat, "general_contingency": g5_cont, "rework_risk": g5_rewo,
                        "holding_cost": hold_c, "international_freight": freight_c, "handling_cost": handl_c, "reverse_logistics": recov_c,
                        "risk_factor": r_factor, "base_cost": task_base, "total_cost": task_total, "status": "Pending"
                    }
                )
                task_id_db_map[raw_id] = db_t_id
                task_id_db_map[db_t_id] = db_t_id

            # Update project total costs in DB
            final_p_base = base_cost_pinfo if base_cost_pinfo > 0 else calc_project_base
            final_p_total = total_cost_pinfo if total_cost_pinfo > 0 else calc_project_total

            await conn.execute(
                text("UPDATE projects SET base_cost = :b_cost, total_cost = :t_cost WHERE id = :p_id"),
                {"b_cost": final_p_base, "t_cost": final_p_total, "p_id": p_id}
            )

            print(f"     [OK] Chen {len(df_tasks)} tasks thanh cong (Project Base Cost: ${final_p_base:,.2f}, Total Cost: ${final_p_total:,.2f})!")

            # Insert task_resources ONLY for official human resources listed in resources.csv
            if not df_tr.empty:
                tr_inserted = 0
                t_col = 'task_id' if 'task_id' in df_tr.columns else df_tr.columns[0]
                r_col = 'resource_id' if 'resource_id' in df_tr.columns else ('resource_name' if 'resource_name' in df_tr.columns else df_tr.columns[1])
                q_col = 'request_quantity' if 'request_quantity' in df_tr.columns else ('quantity' if 'quantity' in df_tr.columns else df_tr.columns[-1])
                
                for _, tr_row in df_tr.iterrows():
                    orig_t = str(tr_row[t_col]).strip()
                    orig_r = str(tr_row[r_col]).strip()
                    qty = float(tr_row[q_col] or 1.0)
                    
                    db_t = task_id_db_map.get(orig_t) or task_id_db_map.get(f"{proj_folder}_{orig_t}")
                    db_r = res_id_db_map.get(orig_r) or res_name_db_map.get(orig_r.lower())
                    
                    if db_t and db_r and db_r in official_human_resources:
                        await conn.execute(
                            text("INSERT INTO task_resources (task_id, resource_id, request_quantity) VALUES (:task_id, :resource_id, :request_quantity)"),
                            {"task_id": db_t, "resource_id": db_r, "request_quantity": qty}
                        )
                        tr_inserted += 1
                print(f"     [OK] Chen {tr_inserted} phan bo task_resources (official human resources) thanh cong!")

            # Insert logic edges
            if not df_edges.empty:
                edges_inserted = 0
                p_col = 'predecessor_task_id' if 'predecessor_task_id' in df_edges.columns else ('predecessor_id' if 'predecessor_id' in df_edges.columns else df_edges.columns[0])
                s_col = 'successor_task_id' if 'successor_task_id' in df_edges.columns else ('successor_id' if 'successor_id' in df_edges.columns else df_edges.columns[1])
                dep_col = 'dependency_type' if 'dependency_type' in df_edges.columns else 'type'
                lag_col = 'lag_days' if 'lag_days' in df_edges.columns else 'lag'
                
                for _, e_row in df_edges.iterrows():
                    orig_p = str(e_row[p_col]).strip()
                    orig_s = str(e_row[s_col]).strip()
                    dep = str(e_row.get(dep_col, 'FS') or 'FS')
                    lag = float(e_row.get(lag_col, 0.0) or 0.0)
                    
                    db_p = task_id_db_map.get(orig_p) or task_id_db_map.get(f"{proj_folder}_{orig_p}")
                    db_s = task_id_db_map.get(orig_s) or task_id_db_map.get(f"{proj_folder}_{orig_s}")
                    
                    if db_p and db_s:
                        await conn.execute(
                            text("INSERT INTO project_constraint_logic (project_id, predecessor_id, successor_id, dependency_type, lag_days) VALUES (:p_id, :pred, :succ, :dep, :lag)"),
                            {"p_id": p_id, "pred": db_p, "succ": db_s, "dep": dep, "lag": lag}
                        )
                        edges_inserted += 1
                print(f"     [OK] Chen {edges_inserted} lien ket canh logic (predecessors) thanh cong!")

        await conn.commit()
    
    await engine.dispose()
    print("\n========================================================================")
    print("[SUCCESS] RE-INITIALIZED ALL TABLES IN DOCKER POSTGRESQL ACCORDING TO OFFICIAL RESOURCES.CSV POOL!")
    print("========================================================================")

if __name__ == "__main__":
    asyncio.run(reload_docker_database_rigorous())
