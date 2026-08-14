import asyncio
import os
import sys
import json
import pandas as pd
from pathlib import Path
from zoneinfo import ZoneInfo

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
    
    from app.db.database import Base
    import app.models

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        await conn.run_sync(Base.metadata.create_all)
        print("[SUCCESS] Da drop vac recreate toan bo public schema trong Docker DB theo schema SQLAlchemy model moi!")

    print("\n========================================================================")
    print("2. IMPORT CHUAN DATASET G1-G7: LABOR, MATERIAL, FUEL/EQUIPMENT & RISK FACTORS")
    print("========================================================================")
    
    target_projects = ["C2011-07", "C2012-04", "C2012-08", "C2018-09", "C2019-16"]
    print(f"Thu muc dataset: {PROCESSED_DIR}")
    print(f"Danh sach 5 du an se nap: {target_projects}")
    
    async with engine.connect() as conn:
        for proj_folder in target_projects:
            proj_path = os.path.join(PROCESSED_DIR, proj_folder)
            
            pinfo_csv = os.path.join(proj_path, 'project_info.csv')
            tasks_csv = os.path.join(proj_path, 'tasks.csv')
            edges_csv = os.path.join(proj_path, 'logic.csv')
            if not os.path.exists(edges_csv):
                edges_csv = os.path.join(proj_path, 'predecessors.csv')
                
            res_csv = os.path.join(proj_path, 'resources.csv')
            tr_csv = os.path.join(proj_path, 'task_resources.csv')
            sched_csv = os.path.join(proj_path, 'task_schedules.csv')
            
            agenda_json_file = os.path.join(proj_path, 'agenda.json')
            
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
                text("INSERT INTO projects (id, project_name, project_type, penalty_per_day, bonus_per_day, num_tasks, num_edges, base_cost, total_cost, status, metadata_json, created_at, updated_at) VALUES (:pid, :p_name, :p_type, 0.0, 0.0, :n_tasks, :n_edges, :b_cost, :t_cost, 'Planning', '{}', NOW(), NOW()) RETURNING id"),
                {"pid": proj_folder, "p_name": p_name, "p_type": p_type, "n_tasks": n_tasks, "n_edges": n_edges, "b_cost": base_cost_pinfo, "t_cost": total_cost_pinfo}
            )
            p_id = res_proj.fetchone()[0]
            print(f"\n---> [LOAD PROJECT #{p_id}] '{p_name}' (Folder: {proj_folder}, Type: {p_type})")

            # Build Agenda JSON & Insert Time Constraints
            sched_data = {
                "hours_per_day": h_per_day,
                "days_per_week": d_per_week
            }
            holidays_list = []
            if os.path.exists(agenda_json_file):
                try:
                    with open(agenda_json_file, 'r', encoding='utf-8') as f:
                        ag_json = json.load(f)
                        sched_data = ag_json.get('weekly_schedule', sched_data)
                        holidays_list = ag_json.get('holidays', [])
                except Exception as e:
                    print(f"  [WARN] Khong doc duoc agenda.json: {e}")

            await conn.execute(
                text("INSERT INTO project_calendars (project_id, weekly_schedule, holidays_list, created_at, updated_at) VALUES (:p_id, :sched, :holidays, NOW(), NOW())"),
                {"p_id": p_id, "sched": json.dumps(sched_data), "holidays": json.dumps(holidays_list)}
            )

            # Helper to parse local time
            def parse_local_time(val):
                if pd.isna(val): return None
                try:
                    dt = pd.to_datetime(val)
                    if dt.tzinfo is None:
                        dt = dt.tz_localize(ZoneInfo('Asia/Ho_Chi_Minh'))
                    return dt.to_pydatetime()
                except Exception:
                    return None
                    
            # Parse baseline_start and baseline_end from task_schedules.csv
            schedule_map = {}
            if not df_sched.empty:
                t_col_sched = 'task_id' if 'task_id' in df_sched.columns else df_sched.columns[0]
                start_col = 'baseline_start' if 'baseline_start' in df_sched.columns else df_sched.columns[1]
                end_col = 'baseline_end'
                for _, s_row in df_sched.iterrows():
                    t_id_str = str(s_row[t_col_sched])
                    st_val = s_row.get(start_col)
                    end_val = s_row.get(end_col) if end_col in df_sched.columns else None
                    
                    st_dt = parse_local_time(st_val)
                    end_dt = parse_local_time(end_val)
                            
                    schedule_map[t_id_str] = (st_dt, end_dt)

            # Insert resources from resources.csv
            res_id_db_map = {}
            res_name_db_map = {}
            res_cost_map = {}

            if not df_res.empty:
                r_id_col = 'ID' if 'ID' in df_res.columns else ('id' if 'id' in df_res.columns else df_res.columns[0])
                r_name_col = 'resource_name' if 'resource_name' in df_res.columns else ('name' if 'name' in df_res.columns else df_res.columns[1])
                r_type_col = 'resource_type' if 'resource_type' in df_res.columns else 'type'
                r_cost_col = 'unit_cost' if 'unit_cost' in df_res.columns else ('Cost/Unit' if 'Cost/Unit' in df_res.columns else 'cost')
                r_cap_col = 'capacity' if 'capacity' in df_res.columns else 'max_availability'
                
                for _, r_row in df_res.iterrows():
                    orig_r_id = str(r_row[r_id_col]).strip()
                    r_name = str(r_row.get(r_name_col, 'Resource')).strip()
                    r_type_raw = str(r_row.get(r_type_col, 'Human')).strip()
                    r_name_lower = r_name.lower()
                    if any(k in r_name_lower for k in ['truck', 'loader', 'roller', 'excavator', 'crane', 'drill', 'mixer', 'paver', 'milling', 'driver', 'pruning', 'machine', 'bulldozer', 'paler', 'vehicle', 'tank']):
                        r_type = 'Equipment'
                    elif any(k in r_name_lower for k in ['material', 'paving', 'concrete', 'steel', 'asphalt']):
                        r_type = 'Material'
                    else:
                        r_type = r_type_raw if r_type_raw and r_type_raw.lower() != 'renewable' else 'Human'

                    r_cost = float(r_row.get(r_cost_col, 100.0) or 100.0)
                    r_cap = float(r_row.get(r_cap_col, 10.0) or 10.0)
                    
                    res_r = await conn.execute(
                        text("INSERT INTO resources (project_id, resource_id, name, type, unit_cost, max_availability, energy, overtime_multi, max_overtime_per_day, addres_efficiency, created_at, updated_at) VALUES (:p_id, :r_id, :r_name, :r_type, :r_cost, :r_cap, 0.0, 1.5, 4.0, 1.0, NOW(), NOW()) RETURNING id"),
                        {"p_id": p_id, "r_id": orig_r_id, "r_name": r_name, "r_type": r_type, "r_cost": r_cost, "r_cap": r_cap}
                    )
                    db_r_id = res_r.fetchone()[0]
                    res_id_db_map[orig_r_id] = db_r_id
                    res_name_db_map[r_name.lower()] = db_r_id
                    res_cost_map[db_r_id] = r_cost
                print(f"     [OK] Chen {len(res_id_db_map)} resources tu resources.csv thanh cong!")

            # Insert tasks & preserve accurate G1-G7 costs from tasks.csv
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

                # 38 cost sub-groups
                labor = float(row.get('labor', row.get('g1_labor', row.get('internal_labor_cost', 0.0))) or 0.0)
                material = float(row.get('material', row.get('g1_material', row.get('material_cost', 0.0))) or 0.0)
                equipment = float(row.get('equipment', row.get('g1_fuel', row.get('equipment_fuel_cost', 0.0))) or 0.0)
                energy = float(row.get('energy', 0.0) or 0.0)
                testing_inspection = float(row.get('testing_inspection', row.get('g1_qa_qc', row.get('qa_qc_cost', 0.0))) or 0.0)

                project_management = float(row.get('project_management', 0.0) or 0.0)
                facility = float(row.get('facility', row.get('g2_space', row.get('facility_rent', 0.0))) or 0.0)
                utilities = float(row.get('utilities', row.get('g2_utility', row.get('utilities_cost', 0.0))) or 0.0)
                communication = float(row.get('communication', row.get('g2_communication', row.get('communication_cost', 0.0))) or 0.0)
                training = float(row.get('training', row.get('g2_training', row.get('training_cost', 0.0))) or 0.0)
                quality_management = float(row.get('quality_management', 0.0) or 0.0)

                overtime = float(row.get('overtime', row.get('overtime_cost', 0.0)) or 0.0)
                delay_penalty = float(row.get('delay_penalty', 0.0) or 0.0)
                inventory_holding = float(row.get('inventory_holding', row.get('g6_storage', row.get('holding_cost', 0.0))) or 0.0)
                waiting_cost = float(row.get('waiting_cost', 0.0) or 0.0)
                idle_resource = float(row.get('idle_resource', 0.0) or 0.0)
                revenue_delay = float(row.get('revenue_delay', 0.0) or 0.0)
                expediting = float(row.get('expediting', 0.0) or 0.0)

                insurance = float(row.get('insurance', row.get('g4_insurance', row.get('insurance_cost', 0.0))) or 0.0)
                rework = float(row.get('rework', row.get('g5_rework', row.get('rework_risk', 0.0))) or 0.0)
                warranty = float(row.get('warranty', row.get('g4_warranty', row.get('warranty_cost', 0.0))) or 0.0)
                litigation = float(row.get('litigation', 0.0) or 0.0)
                regulatory_compliance = float(row.get('regulatory_compliance', row.get('g4_license', row.get('licensing_cost', 0.0))) or 0.0)
                contingency_reserve = float(row.get('contingency_reserve', row.get('g5_contingency', row.get('general_contingency', 0.0))) or 0.0)
                management_reserve = float(row.get('management_reserve', 0.0) or 0.0)

                transportation = float(row.get('transportation', row.get('g6_int_transport', row.get('international_freight', 0.0))) or 0.0)
                ordering = float(row.get('ordering', 0.0) or 0.0)
                packaging = float(row.get('packaging', 0.0) or 0.0)
                reverse_logistics = float(row.get('reverse_logistics', row.get('g6_recovery', row.get('reverse_logistics', 0.0))) or 0.0)
                customs = float(row.get('customs', 0.0) or 0.0)
                supplier_coordination = float(row.get('supplier_coordination', row.get('g1_subcontract', row.get('outsourcing_cost', 0.0))) or 0.0)

                opportunity_cost = float(row.get('opportunity_cost', 0.0) or 0.0)
                capital_cost = float(row.get('capital_cost', 0.0) or 0.0)
                financing_cost = float(row.get('financing_cost', 0.0) or 0.0)
                npv_loss = float(row.get('npv_loss', 0.0) or 0.0)
                esg_cost = float(row.get('esg_cost', 0.0) or 0.0)
                carbon_tax = float(row.get('carbon_tax', 0.0) or 0.0)
                reputation_cost = float(row.get('reputation_cost', 0.0) or 0.0)

                b_start = None
                b_end = None
                sched_data = schedule_map.get(raw_id) or schedule_map.get(db_t_id)
                if sched_data:
                    b_start, b_end = sched_data
                    
                if not b_start:
                    b_start = parse_local_time(row.get('baseline_start'))
                        
                if not b_end:
                    b_end = parse_local_time(row.get('baseline_end'))

                # Base cost is sum of all 38 cost sub-groups
                task_base = float(row.get('base_cost', 0.0) or 0.0)
                if task_base <= 1e-6:
                    task_base = (
                        labor + material + equipment + energy + testing_inspection +
                        project_management + facility + utilities + communication + training + quality_management +
                        overtime + delay_penalty + inventory_holding + waiting_cost + idle_resource + revenue_delay + expediting +
                        insurance + rework + warranty + litigation + regulatory_compliance + contingency_reserve + management_reserve +
                        transportation + ordering + packaging + reverse_logistics + customs + supplier_coordination +
                        opportunity_cost + capital_cost + financing_cost + npv_loss + esg_cost + carbon_tax + reputation_cost
                    )

                task_total = float(row.get('total_cost', 0.0) or 0.0)
                if task_total <= 1e-6:
                    task_total = task_base * r_factor

                calc_project_base += task_base
                calc_project_total += task_total

                await conn.execute(
                    text(
                        "INSERT INTO tasks (project_id, task_id, task_name, duration_hours, baseline_start, baseline_end, "
                        "labor, material, equipment, energy, testing_inspection, project_management, facility, utilities, communication, training, quality_management, "
                        "overtime, delay_penalty, inventory_holding, waiting_cost, idle_resource, revenue_delay, expediting, insurance, rework, warranty, litigation, "
                        "regulatory_compliance, contingency_reserve, management_reserve, transportation, ordering, packaging, reverse_logistics, customs, supplier_coordination, "
                        "opportunity_cost, capital_cost, financing_cost, npv_loss, esg_cost, carbon_tax, reputation_cost, "
                        "created_at, updated_at) "
                        "VALUES (:project_id, :task_id, :task_name, :duration_hours, :baseline_start, :baseline_end, "
                        ":labor, :material, :equipment, :energy, :testing_inspection, :project_management, :facility, :utilities, :communication, :training, :quality_management, "
                        ":overtime, :delay_penalty, :inventory_holding, :waiting_cost, :idle_resource, :revenue_delay, :expediting, :insurance, :rework, :warranty, :litigation, "
                        ":regulatory_compliance, :contingency_reserve, :management_reserve, :transportation, :ordering, :packaging, :reverse_logistics, :customs, :supplier_coordination, "
                        ":opportunity_cost, :capital_cost, :financing_cost, :npv_loss, :esg_cost, :carbon_tax, :reputation_cost, "
                        "NOW(), NOW())"
                    ),
                    {
                        "project_id": p_id, "task_id": db_t_id, "task_name": t_name,
                        "duration_hours": dur_h, "baseline_start": b_start, "baseline_end": b_end,
                        "labor": labor, "material": material, "equipment": equipment, "energy": energy, "testing_inspection": testing_inspection,
                        "project_management": project_management, "facility": facility, "utilities": utilities, "communication": communication, "training": training, "quality_management": quality_management,
                        "overtime": overtime, "delay_penalty": delay_penalty, "inventory_holding": inventory_holding, "waiting_cost": waiting_cost, "idle_resource": idle_resource, "revenue_delay": revenue_delay, "expediting": expediting,
                        "insurance": insurance, "rework": rework, "warranty": warranty, "litigation": litigation, "regulatory_compliance": regulatory_compliance, "contingency_reserve": contingency_reserve, "management_reserve": management_reserve,
                        "transportation": transportation, "ordering": ordering, "packaging": packaging, "reverse_logistics": reverse_logistics, "customs": customs, "supplier_coordination": supplier_coordination,
                        "opportunity_cost": opportunity_cost, "capital_cost": capital_cost, "financing_cost": financing_cost, "npv_loss": npv_loss, "esg_cost": esg_cost, "carbon_tax": carbon_tax, "reputation_cost": reputation_cost
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

            # Insert task_resources
            if not df_tr.empty:
                tr_inserted = 0
                t_col = 'task_id' if 'task_id' in df_tr.columns else df_tr.columns[0]
                r_col = 'role' if 'role' in df_tr.columns else ('resource_id' if 'resource_id' in df_tr.columns else df_tr.columns[1])
                q_col = 'quantity' if 'quantity' in df_tr.columns else df_tr.columns[-1]
                
                for _, tr_row in df_tr.iterrows():
                    orig_t = str(tr_row[t_col]).strip()
                    orig_r = str(tr_row[r_col]).strip()
                    qty = float(tr_row[q_col] or 1.0)
                    
                    db_t = task_id_db_map.get(orig_t) or task_id_db_map.get(f"{proj_folder}_{orig_t}")
                    db_r = res_id_db_map.get(orig_r) or res_name_db_map.get(orig_r.lower())
                    
                    if db_t:
                        await conn.execute(
                            text("INSERT INTO task_resources (project_id, task_id, resource_id, request_quantity, created_at) VALUES (:p_id, :task_id, :resource_id, :request_quantity, NOW())"),
                            {"p_id": p_id, "task_id": db_t, "resource_id": str(orig_r), "request_quantity": qty}
                        )
                        tr_inserted += 1
                print(f"     [OK] Chen {tr_inserted} phan bo task_resources thanh cong!")

            # Insert logic edges
            if not df_edges.empty:
                edges_inserted = 0
                p_col = 'source_id' if 'source_id' in df_edges.columns else ('predecessor_task_id' if 'predecessor_task_id' in df_edges.columns else ('predecessor_id' if 'predecessor_id' in df_edges.columns else df_edges.columns[0]))
                s_col = 'target_id' if 'target_id' in df_edges.columns else ('successor_task_id' if 'successor_task_id' in df_edges.columns else ('successor_id' if 'successor_id' in df_edges.columns else df_edges.columns[1]))
                dep_col = 'dependency_type' if 'dependency_type' in df_edges.columns else 'type'
                
                for _, e_row in df_edges.iterrows():
                    orig_p = str(e_row[p_col]).strip()
                    orig_s = str(e_row[s_col]).strip()
                    dep = str(e_row.get(dep_col, 'FS') or 'FS')
                    lag_m = float(e_row.get('lag_months', 0.0) or 0.0)
                    lag_w = float(e_row.get('lag_weeks', 0.0) or 0.0)
                    lag_d = float(e_row.get('lag_days', 0.0) or 0.0)
                    lag_h = float(e_row.get('lag_hours', 0.0) or 0.0)
                    
                    db_p = task_id_db_map.get(orig_p) or task_id_db_map.get(f"{proj_folder}_{orig_p}")
                    db_s = task_id_db_map.get(orig_s) or task_id_db_map.get(f"{proj_folder}_{orig_s}")
                    
                    if db_p and db_s:
                        await conn.execute(
                            text("INSERT INTO task_logic (project_id, predecessor_id, successor_id, dependency_type, lag_hours, created_at) VALUES (:p_id, :pred, :succ, :dep, :lag_h, NOW())"),
                            {"p_id": p_id, "pred": db_p, "succ": db_s, "dep": dep, "lag_h": lag_h}
                        )
                        edges_inserted += 1
                print(f"     [OK] Chen {edges_inserted} lien ket canh logic (predecessors) thanh cong!")

        await conn.commit()
    
    await engine.dispose()
    print("\n========================================================================")
    print("[SUCCESS] RE-INITIALIZED ALL TABLES IN DOCKER POSTGRESQL WITH EXACT G1-G7 COSTS FROM DATASET!")
    print("========================================================================")

if __name__ == "__main__":
    asyncio.run(reload_docker_database_rigorous())
