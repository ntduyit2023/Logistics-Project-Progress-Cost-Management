import sys
import os
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Force UTF-8 stdout/stderr encoding for Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure sys.path includes backend and root
backend_dir = Path(__file__).resolve().parent.parent
root_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from app.db.database import Base, async_session
import app.models
from app.models.project import AppProject, ProjectCalendar, Resource, TaskResource, TaskLogic
from app.models.task import Task
from ai_pipeline.models.moi.cpsat_pareto_solver import CPSATParetoSolver

PROCESSED_DIR = os.path.join(root_dir, "ai_pipeline", "data", "processed", "MFET-3008")

def generate_mfet3008_dataset_files():
    """Generates the official UniSA MFET 3008/5040 dataset files from PPC_casestudy_2010_V1.pdf"""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    print(f"[1/4] Generating official MFET 3008 dataset files (UniSA PPC Case Study) in {PROCESSED_DIR}...")

    # 1. project_info.csv
    df_pinfo = pd.DataFrame([{
        "project_id": "MFET-3008",
        "project_name": "Case Study MFET 3008 - Parcel Transport & Storage System (UniSA PPC)",
        "project_type": "LOGISTICS",
        "penalty_per_day": 2000.0,
        "bonus_per_day": 3000.0,
        "working_hours_per_day": 8.0,
        "working_days_per_week": 5.0,
        "total_baseline_cost": 49510.0,
        "total_final_cost": 70230.0
    }])
    df_pinfo.to_csv(os.path.join(PROCESSED_DIR, "project_info.csv"), index=False)

    # 2. agenda.json
    agenda = {
        "weekly_schedule": {"hours_per_day": 8.0, "days_per_week": 5.0},
        "holidays": []
    }
    with open(os.path.join(PROCESSED_DIR, "agenda.json"), "w", encoding="utf-8") as f:
        json.dump(agenda, f, indent=2)

    # 3. resources.csv (8 Staffing Categories from Table 2 & Table 4 of PDF)
    resources = [
        {"ID": "R1", "resource_name": "Design (Computing)", "resource_type": "Human", "unit_cost": 200.0, "capacity": 1.0},
        {"ID": "R2", "resource_name": "Design (Mechanical)", "resource_type": "Human", "unit_cost": 200.0, "capacity": 1.0},
        {"ID": "R3", "resource_name": "Development (Computing)", "resource_type": "Human", "unit_cost": 150.0, "capacity": 2.0},
        {"ID": "R4", "resource_name": "Development (Mechanical)", "resource_type": "Human", "unit_cost": 150.0, "capacity": 1.0},
        {"ID": "R5", "resource_name": "Assembly (Computing)", "resource_type": "Human", "unit_cost": 100.0, "capacity": 1.0},
        {"ID": "R6", "resource_name": "Assembly (Mechanical)", "resource_type": "Human", "unit_cost": 100.0, "capacity": 1.0},
        {"ID": "R7", "resource_name": "Purchase", "resource_type": "Human", "unit_cost": 80.0, "capacity": 1.0},
        {"ID": "R8", "resource_name": "Documentation", "resource_type": "Human", "unit_cost": 80.0, "capacity": 2.0}
    ]
    pd.DataFrame(resources).to_csv(os.path.join(PROCESSED_DIR, "resources.csv"), index=False)

    # 4. tasks.csv (21 Tasks A through U from Table 1 of PDF)
    # Duration converted from Days to Hours (1 day = 8 hours)
    tasks_data = [
        {"id": "MFET-3008_A", "task_name": "Task A: Architectural decisions", "duration_days": 4.0, "duration_hours": 32.0, "g1_labor": 1600.0, "total_cost": 1600.0},
        {"id": "MFET-3008_B", "task_name": "Task B: Hardware specifications", "duration_days": 6.0, "duration_hours": 48.0, "g1_labor": 3900.0, "total_cost": 3900.0},
        {"id": "MFET-3008_C", "task_name": "Task C: Software specifications", "duration_days": 7.0, "duration_hours": 56.0, "g1_labor": 3150.0, "total_cost": 3150.0},
        {"id": "MFET-3008_D", "task_name": "Task D: Conveyor design", "duration_days": 8.0, "duration_hours": 64.0, "g1_labor": 2800.0, "total_cost": 2800.0},
        {"id": "MFET-3008_E", "task_name": "Task E: Hardware design", "duration_days": 6.0, "duration_hours": 48.0, "g1_labor": 3300.0, "total_cost": 3300.0},
        {"id": "MFET-3008_F", "task_name": "Task F: Software design", "duration_days": 12.0, "duration_hours": 96.0, "g1_labor": 4200.0, "total_cost": 4200.0},
        {"id": "MFET-3008_G", "task_name": "Task G: Operating system documentation", "duration_days": 10.0, "duration_hours": 80.0, "g1_labor": 2300.0, "total_cost": 2300.0},
        {"id": "MFET-3008_H", "task_name": "Task H: Hardware detail drawings", "duration_days": 8.0, "duration_hours": 64.0, "g1_labor": 3040.0, "total_cost": 3040.0},
        {"id": "MFET-3008_I", "task_name": "Task I: Software programming", "duration_days": 16.0, "duration_hours": 128.0, "g1_labor": 4480.0, "total_cost": 4480.0},
        {"id": "MFET-3008_J", "task_name": "Task J: Software verification/testing", "duration_days": 12.0, "duration_hours": 96.0, "g1_labor": 3960.0, "total_cost": 3960.0},
        {"id": "MFET-3008_K", "task_name": "Task K: Conveyor detailed drawings", "duration_days": 7.0, "duration_hours": 56.0, "g1_labor": 2660.0, "total_cost": 2660.0},
        {"id": "MFET-3008_L", "task_name": "Task L: Drawing verification/Minor integration", "duration_days": 9.0, "duration_hours": 72.0, "g1_labor": 3150.0, "total_cost": 3150.0},
        {"id": "MFET-3008_M", "task_name": "Task M: Prototype development", "duration_days": 4.0, "duration_hours": 32.0, "g1_labor": 1200.0, "total_cost": 1200.0},
        {"id": "MFET-3008_N", "task_name": "Task N: Prototype installation", "duration_days": 7.0, "duration_hours": 56.0, "g1_labor": 1400.0, "total_cost": 1400.0},
        {"id": "MFET-3008_O", "task_name": "Task O: Hardware order/delivery", "duration_days": 7.0, "duration_hours": 56.0, "g1_labor": 1610.0, "total_cost": 1610.0},
        {"id": "MFET-3008_P", "task_name": "Task P: System Interface", "duration_days": 5.0, "duration_hours": 40.0, "g1_labor": 1250.0, "total_cost": 1250.0},
        {"id": "MFET-3008_Q", "task_name": "Task Q: Hardware assembly", "duration_days": 4.0, "duration_hours": 32.0, "g1_labor": 800.0, "total_cost": 800.0},
        {"id": "MFET-3008_R", "task_name": "Task R: Hardware/software Integration", "duration_days": 5.0, "duration_hours": 40.0, "g1_labor": 2500.0, "total_cost": 2500.0},
        {"id": "MFET-3008_S", "task_name": "Task S: Hardware/software documentation", "duration_days": 2.0, "duration_hours": 16.0, "g1_labor": 760.0, "total_cost": 760.0},
        {"id": "MFET-3008_T", "task_name": "Task T: System verification", "duration_days": 3.0, "duration_hours": 24.0, "g1_labor": 1050.0, "total_cost": 1050.0},
        {"id": "MFET-3008_U", "task_name": "Task U: Acceptance test", "duration_days": 2.0, "duration_hours": 16.0, "g1_labor": 400.0, "total_cost": 400.0}
    ]
    pd.DataFrame(tasks_data).to_csv(os.path.join(PROCESSED_DIR, "tasks.csv"), index=False)

    # 5. logic.csv (Precedence Relationships from Table 1 of PDF)
    dependencies_data = [
        ("MFET-3008_A", "MFET-3008_B"),
        ("MFET-3008_A", "MFET-3008_C"),
        ("MFET-3008_B", "MFET-3008_D"),
        ("MFET-3008_B", "MFET-3008_E"),
        ("MFET-3008_C", "MFET-3008_F"),
        ("MFET-3008_C", "MFET-3008_G"),
        ("MFET-3008_D", "MFET-3008_K"),
        ("MFET-3008_E", "MFET-3008_H"),
        ("MFET-3008_F", "MFET-3008_H"),
        ("MFET-3008_G", "MFET-3008_I"),
        ("MFET-3008_H", "MFET-3008_L"),
        ("MFET-3008_H", "MFET-3008_M"),
        ("MFET-3008_I", "MFET-3008_J"),
        ("MFET-3008_J", "MFET-3008_N"),
        ("MFET-3008_K", "MFET-3008_L"),
        ("MFET-3008_L", "MFET-3008_O"),
        ("MFET-3008_L", "MFET-3008_P"),
        ("MFET-3008_M", "MFET-3008_N"),
        ("MFET-3008_N", "MFET-3008_R"),
        ("MFET-3008_O", "MFET-3008_Q"),
        ("MFET-3008_P", "MFET-3008_Q"),
        ("MFET-3008_Q", "MFET-3008_R"),
        ("MFET-3008_R", "MFET-3008_S"),
        ("MFET-3008_R", "MFET-3008_T"),
        ("MFET-3008_S", "MFET-3008_U"),
        ("MFET-3008_T", "MFET-3008_U")
    ]
    pd.DataFrame(dependencies_data, columns=["predecessor_id", "successor_id"]).to_csv(
        os.path.join(PROCESSED_DIR, "logic.csv"), index=False
    )

    # 6. task_resources.csv (Labour Resources from Table 1 of PDF)
    tr_mappings = [
        ("MFET-3008_A", "R1"), ("MFET-3008_A", "R2"),
        ("MFET-3008_B", "R1"), ("MFET-3008_B", "R2"), ("MFET-3008_B", "R4"), ("MFET-3008_B", "R6"),
        ("MFET-3008_C", "R1"), ("MFET-3008_C", "R3"), ("MFET-3008_C", "R5"),
        ("MFET-3008_D", "R2"), ("MFET-3008_D", "R4"),
        ("MFET-3008_E", "R1"), ("MFET-3008_E", "R2"), ("MFET-3008_E", "R4"),
        ("MFET-3008_F", "R1"), ("MFET-3008_F", "R3"),
        ("MFET-3008_G", "R3"), ("MFET-3008_G", "R8"),
        ("MFET-3008_H", "R3"), ("MFET-3008_H", "R4"), ("MFET-3008_H", "R8"),
        ("MFET-3008_I", "R1"), ("MFET-3008_I", "R8"),
        ("MFET-3008_J", "R3"), ("MFET-3008_J", "R5"), ("MFET-3008_J", "R8"),
        ("MFET-3008_K", "R3"), ("MFET-3008_K", "R4"), ("MFET-3008_K", "R8"),
        ("MFET-3008_L", "R3"), ("MFET-3008_L", "R5"), ("MFET-3008_L", "R6"),
        ("MFET-3008_M", "R3"), ("MFET-3008_M", "R4"),
        ("MFET-3008_N", "R5"), ("MFET-3008_N", "R6"),
        ("MFET-3008_O", "R4"), ("MFET-3008_O", "R7"),
        ("MFET-3008_P", "R4"), ("MFET-3008_P", "R6"),
        ("MFET-3008_Q", "R5"), ("MFET-3008_Q", "R6"),
        ("MFET-3008_R", "R3"), ("MFET-3008_R", "R4"), ("MFET-3008_R", "R5"), ("MFET-3008_R", "R6"),
        ("MFET-3008_S", "R3"), ("MFET-3008_S", "R4"), ("MFET-3008_S", "R8"),
        ("MFET-3008_T", "R4"), ("MFET-3008_T", "R5"), ("MFET-3008_T", "R6"),
        ("MFET-3008_U", "R5"), ("MFET-3008_U", "R6")
    ]
    tr_data = [{"task_id": tid, "resource_id": rid, "request_quantity": 1.0} for tid, rid in tr_mappings]
    pd.DataFrame(tr_data).to_csv(os.path.join(PROCESSED_DIR, "task_resources.csv"), index=False)

    # 7. task_schedules.csv (Calculated Early Start / Early Finish dates based on 66 days duration)
    base_start = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
    # CPM Early Start offsets in days for tasks A-U
    es_offsets = {
        "MFET-3008_A": 0, "MFET-3008_B": 4, "MFET-3008_C": 4, "MFET-3008_D": 10,
        "MFET-3008_E": 10, "MFET-3008_F": 11, "MFET-3008_G": 11, "MFET-3008_H": 23,
        "MFET-3008_I": 21, "MFET-3008_J": 37, "MFET-3008_K": 18, "MFET-3008_L": 31,
        "MFET-3008_M": 31, "MFET-3008_N": 49, "MFET-3008_O": 40, "MFET-3008_P": 40,
        "MFET-3008_Q": 47, "MFET-3008_R": 56, "MFET-3008_S": 61, "MFET-3008_T": 61,
        "MFET-3008_U": 64
    }
    sched_data = []
    for t in tasks_data:
        tid = t["id"]
        es_d = es_offsets.get(tid, 0)
        st = base_start + timedelta(days=es_d)
        end = st + timedelta(days=int(t["duration_days"]))
        sched_data.append({
            "task_id": tid,
            "baseline_start": st.isoformat(),
            "baseline_end": end.isoformat()
        })
    pd.DataFrame(sched_data).to_csv(os.path.join(PROCESSED_DIR, "task_schedules.csv"), index=False)
    print("   [OK] Generated all MFET 3008 official dataset files successfully!")

async def seed_mfet3008_database():
    """Seeds the official MFET 3008 case study project using SQLAlchemy ORM Session"""
    print(f"\n[2/4] Seeding MFET-3008 (UniSA PPC Case Study) via SQLAlchemy ORM Session...")

    async with async_session() as db:
        # Check if project already exists
        existing_proj = (await db.execute(select(AppProject).where(AppProject.id == "MFET-3008"))).scalars().first()
        if existing_proj:
            print("   [UPDATE] Cleaning previous project data for fresh seed...")
            await db.delete(existing_proj)
            await db.commit()

        # 1. AppProject
        project = AppProject(
            id="MFET-3008",
            project_name="Case Study MFET 3008 - Parcel Transport & Storage System (UniSA PPC)",
            project_type="LOGISTICS",
            status="Planning",
            penalty_per_day=2000.0,
            bonus_per_day=3000.0,
            num_tasks=21,
            num_edges=26,
            base_cost=49510.0,
            total_cost=70230.0,
            metadata_json={}
        )
        db.add(project)
        await db.flush()

        # 2. ProjectCalendar
        calendar = ProjectCalendar(
            project_id="MFET-3008",
            weekly_schedule={"hours_per_day": 8.0, "days_per_week": 5.0},
            holidays_list=[]
        )
        db.add(calendar)

        # 3. Resources
        df_res = pd.read_csv(os.path.join(PROCESSED_DIR, "resources.csv"))
        res_orm_map = {}
        for _, r in df_res.iterrows():
            res_obj = Resource(
                project_id="MFET-3008",
                resource_id=r["ID"],
                name=r["resource_name"],
                type=r["resource_type"],
                unit_cost=float(r["unit_cost"]),
                max_availability=float(r["capacity"]),
                energy=0.0,
                overtime_multi=1.5,
                max_overtime_per_day=4.0,
                addres_efficiency=0.7
            )
            db.add(res_obj)
            await db.flush()
            res_orm_map[r["ID"]] = res_obj.id

        print(f"   [OK] Inserted {len(res_orm_map)} Staffing Resources (Table 2/4)")

        # 4. Tasks
        df_tasks = pd.read_csv(os.path.join(PROCESSED_DIR, "tasks.csv"))
        df_sched = pd.read_csv(os.path.join(PROCESSED_DIR, "task_schedules.csv"))
        sched_map = dict(zip(df_sched["task_id"], zip(df_sched["baseline_start"], df_sched["baseline_end"])))

        for _, t in df_tasks.iterrows():
            tid = t["id"]
            st_str, end_str = sched_map.get(tid, (None, None))
            st_dt = datetime.fromisoformat(st_str) if st_str else datetime.now(timezone.utc)
            end_dt = datetime.fromisoformat(end_str) if end_str else st_dt + timedelta(hours=float(t["duration_hours"]))

            task_obj = Task(
                project_id="MFET-3008",
                task_id=tid,
                task_name=t["task_name"],
                duration_hours=float(t["duration_hours"]),
                baseline_start=st_dt,
                baseline_end=end_dt,
                labor=float(t["g1_labor"]),
                material=0.0,
                equipment=0.0,
                energy=0.0,
                testing_inspection=0.0,
                project_management=0.0,
                facility=0.0,
                utilities=0.0,
                communication=0.0,
                training=0.0,
                quality_management=0.0,
                overtime=0.0,
                delay_penalty=0.0,
                inventory_holding=0.0,
                waiting_cost=0.0,
                idle_resource=0.0,
                revenue_delay=0.0,
                expediting=0.0,
                insurance=0.0,
                rework=0.0,
                warranty=0.0,
                litigation=0.0,
                regulatory_compliance=0.0,
                contingency_reserve=0.0,
                management_reserve=0.0,
                transportation=0.0,
                ordering=0.0,
                packaging=0.0
            )
            db.add(task_obj)

        print(f"   [OK] Inserted {len(df_tasks)} Tasks (Task A through Task U)")

        # 5. TaskLogic Dependencies
        df_logic = pd.read_csv(os.path.join(PROCESSED_DIR, "logic.csv"))
        for _, l in df_logic.iterrows():
            logic_obj = TaskLogic(
                project_id="MFET-3008",
                predecessor_id=l["predecessor_id"],
                successor_id=l["successor_id"],
                dependency_type="FS",
                lag_hours=0.0
            )
            db.add(logic_obj)

        print(f"   [OK] Inserted {len(df_logic)} Task Precedence Dependencies")

        # 6. TaskResource Assignments
        df_tr = pd.read_csv(os.path.join(PROCESSED_DIR, "task_resources.csv"))
        for _, tr in df_tr.iterrows():
            tr_obj = TaskResource(
                project_id="MFET-3008",
                task_id=tr["task_id"],
                resource_id=str(tr["resource_id"]),
                request_quantity=float(tr["request_quantity"])
            )
            db.add(tr_obj)

        await db.commit()
        print("   [OK] Committed all UniSA MFET 3008 ORM records to Database!")

async def run_cpsat_pareto_solver_mfet3008():
    """Runs the CP-SAT Pareto solver on MFET-3008 and saves 5 Pareto options in metadata_json"""
    print("\n[3/4] Running CP-SAT Pareto Solver for MFET-3008...")
    async with async_session() as db:
        result = await db.execute(
            select(AppProject).options(joinedload(AppProject.calendar)).where(AppProject.id == "MFET-3008")
        )
        project = result.scalars().first()
        if not project:
            print("   [ERROR] Project MFET-3008 not found!")
            return

        db_tasks = (await db.execute(select(Task).where(Task.project_id == "MFET-3008"))).scalars().all()
        db_res = (await db.execute(select(Resource).where(Resource.project_id == "MFET-3008"))).scalars().all()
        db_tr = (await db.execute(select(TaskResource).where(TaskResource.project_id == "MFET-3008"))).scalars().all()
        db_dep = (await db.execute(select(TaskLogic).where(TaskLogic.project_id == "MFET-3008"))).scalars().all()

        tasks = []
        for t in db_tasks:
            tasks.append({
                'id': t.task_id, 'task_id': t.task_id, 'task_name': t.task_name,
                'duration_hours': float(t.duration_hours),
                'baseline_start': t.baseline_start.strftime('%Y-%m-%dT%H:%M:%SZ') if t.baseline_start else None,
                'baseline_end': t.baseline_end.strftime('%Y-%m-%dT%H:%M:%SZ') if t.baseline_end else None,
                'base_cost': float(t.total_cost or 0.0), 'labor': float(t.labor or 0.0),
                'equipment': float(t.equipment or 0.0), 'energy': float(t.energy or 0.0),
                'total_cost': float(t.total_cost or 0.0)
            })

        resources_dict = {}
        capacities = {}
        for r in db_res:
            r_dict = {
                'ID': r.resource_id, 'name': r.name, 'type': r.type,
                'unit_cost': float(r.unit_cost), 'max_availability': float(r.max_availability),
                'energy': float(r.energy or 0.0), 'overtime_multi': float(r.overtime_multi or 1.5),
                'max_overtime_per_day': float(r.max_overtime_per_day or 4.0)
            }
            resources_dict[r.resource_id] = r_dict
            resources_dict[r.name] = r_dict
            capacities[r.resource_id] = float(r.max_availability)
            capacities[r.name] = float(r.max_availability)

        task_resource_reqs = {}
        task_labor_rates = {}
        for tr in db_tr:
            r_info = resources_dict.get(tr.resource_id, {})
            qty = float(tr.request_quantity)
            u_cost = float(r_info.get('unit_cost', 0.0))
            task_resource_reqs[(tr.task_id, tr.resource_id)] = qty
            task_labor_rates[tr.task_id] = task_labor_rates.get(tr.task_id, 0.0) + (qty * u_cost)

        dependencies = [(d.predecessor_id, d.successor_id, {'lag': float(d.lag_hours), 'type': d.dependency_type}) for d in db_dep]

        calendar = project.calendar
        weekly_schedule = calendar.weekly_schedule if calendar else None
        holidays_list = calendar.holidays_list if calendar else None

        solver = CPSATParetoSolver(
            tasks=tasks, dependencies=dependencies, resource_capacities=capacities,
            task_resource_requirements=task_resource_reqs, task_labor_rates=task_labor_rates,
            resources_dict=resources_dict, weekly_schedule=weekly_schedule, holidays_list=holidays_list
        )

        solutions = solver.solve(time_limit_sec=15.0, pareto_count=5)
        
        meta = project.metadata_json or {}
        meta["pareto_options_data"] = {
            "project_id": "MFET-3008",
            "pareto_options": solutions
        }
        project.metadata_json = meta

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "metadata_json")
        await db.commit()
        print(f"   [OK] Solved & saved {len(solutions)} Pareto options for MFET-3008!")

async def main():
    print("========================================================================")
    print("SEEDING OFFICIAL UniSA MFET-3008/5040 CASE STUDY FOR FRONTEND VISUALIZATION")
    print("========================================================================")
    generate_mfet3008_dataset_files()
    await seed_mfet3008_database()
    await run_cpsat_pareto_solver_mfet3008()

    print("\n[4/4] SUCCESS! Case study 'MFET-3008' (UniSA PPC) is now fully loaded.")
    print("------------------------------------------------------------------------")
    print("INSTRUCTIONS FOR USER SCREENSHOTS:")
    print("1. Ensure Backend is running (port 8000) and Frontend is running (port 5173).")
    print("2. Open your web browser to: http://localhost:5173")
    print("3. Navigate to Project 'Case Study MFET 3008 - Parcel Transport & Storage System (UniSA PPC)' (ID: MFET-3008).")
    print("4. FOR HÌNH 3.1 (React-Flow Network Graph):")
    print("   - Click on 'Airflow Graph' or 'DAG Network' tab.")
    print("   - You will see the 21-node DAG network (Tasks A-U) auto-rendered with Dagre layout & Critical Path highlighted (66 days duration).")
    print("   - Take a high-resolution screenshot and save to: docs/baocao2/image/hinh3_1_reactflow_network.png")
    print("5. FOR HÌNH 3.9 (EVM Dashboard & Gantt Chart):")
    print("   - Click on 'Workspace' / 'Dashboard' tab.")
    print("   - You will see the EVM Metrics (Baseline $49,510, 66 days normal, 96 days constrained, $70,230 with contractors), Pareto Frontier Options, and Interactive Gantt Chart.")
    print("   - Take a high-resolution screenshot and save to: docs/baocao2/image/hinh3_9_evm_gantt_dashboard.png")
    print("========================================================================")

if __name__ == "__main__":
    asyncio.run(main())
