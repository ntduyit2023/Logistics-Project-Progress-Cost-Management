import os
import sys
import pandas as pd
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pathlib import Path

# Add backend dir to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.db.database import async_session
from app.models import (
    AppProject, Task, ProjectConstraintLogic, 
    ProjectConstraintResource, TaskResource, ProjectConstraintTime
)

# Detect if running in Docker or natively
if Path("/ai_pipeline/data/processed").exists():
    DATA_DIR = Path("/ai_pipeline/data/processed")
else:
    DATA_DIR = backend_dir.parent / "ai_pipeline" / "data" / "processed"

async def clear_existing_data(db: AsyncSession):
    print("Xóa dữ liệu cũ...")
    # Vì đã cấu hình ON DELETE CASCADE trên DB, ta chỉ cần xóa các project cũ (hoặc toàn bộ)
    await db.execute(delete(AppProject))
    await db.commit()

async def process_project(db: AsyncSession, project_folder: Path):
    project_name = project_folder.name
    if project_name.startswith("~") or not project_folder.is_dir():
        return
    
    # Bỏ qua các thư mục đánh số thuần (15, 16, 17, 18, 19) vì chúng là bản sao
    # của các thư mục có tên thật (C2011-07, C2012-04, ...) đã chứa project_info.csv
    if project_name.isdigit():
        print(f"  [SKIP] Bỏ qua thư mục số '{project_name}' (dùng thư mục có tên dự án thật).")
        return
        
    print(f"\n=> Đang import dự án: {project_name}")
    
    # 1. Tạo Project từ project_info.csv
    info_file = project_folder / "project_info.csv"
    project_type = "CON"
    base_cost = 0.0
    total_cost = 0.0
    
    if info_file.exists():
        df_info = pd.read_csv(info_file)
        if not df_info.empty:
            info = df_info.iloc[0]
            project_name = info.get("project_name", project_name)
            project_type = info.get("project_type", "CON")
            base_cost = info.get("total_baseline_cost", 0.0)
            total_cost = info.get("total_final_cost", 0.0)
            
    project = AppProject(
        project_name=project_name, 
        type=project_type,
        base_cost=base_cost,
        total_cost=total_cost,
        status="Planning"
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    project_id = project.id
    
    # 2. Tạo Tasks (Wide Table)
    tasks_file = project_folder / "tasks.csv"
    res_file = project_folder / "task_resources.csv"
    
    if tasks_file.exists():
        df_tasks = pd.read_csv(tasks_file)
        
        # Handle NaN -> None
        df_tasks = df_tasks.where(pd.notnull(df_tasks), None)
        
        tasks_to_insert = []
        valid_task_columns = {c.name for c in Task.__table__.columns}
        
        for row_dict in df_tasks.to_dict(orient="records"):
            task_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            task_dict["project_id"] = project_id
            
            csv_id = str(task_dict.get("id", task_dict.get("task_id", "")))
            if "_" in csv_id:
                original_task_id = csv_id.split("_", 1)[1]
            else:
                original_task_id = csv_id
            task_dict["id"] = f"{project_id}_{original_task_id}"
            
            # Baseline start handling
            if "baseline_start" in task_dict:
                val = task_dict["baseline_start"]
                if pd.isna(val) or not val:
                    task_dict["baseline_start"] = None
                else:
                    try:
                        task_dict["baseline_start"] = pd.to_datetime(val).to_pydatetime()
                    except Exception:
                        task_dict["baseline_start"] = None
            csv_to_task_map = {
                "g1_labor": "internal_labor_cost",
                "g1_ot": "overtime_cost",
                "g1_fuel": "equipment_fuel_cost",
                "g1_qa_qc": "qa_qc_cost",
                "g1_material": "material_cost",
                "g1_subcontract": "outsourcing_cost",
                "g2_training": "training_cost",
                "g2_space": "facility_rent",
                "g2_comm": "communication_cost",
                "g2_utility": "utilities_cost",
                "g4_insurance": "insurance_cost",
                "g4_license": "licensing_cost",
                "g4_warranty": "warranty_cost",
                "g5_complexity": "complexity",
                "g5_weather": "weather_contingency",
                "g5_contingency": "general_contingency",
                "g5_rework": "rework_risk",
                "g6_storage": "holding_cost",
                "g6_int_transport": "international_freight",
                "g6_handling": "handling_cost",
                "g6_recovery": "reverse_logistics",
                "g6_error": "defect_cost",
                "g7_dur_months": "duration_months",
                "g7_dur_weeks": "duration_weeks",
                "g7_dur_days": "duration_days",
                "g7_dur_hours": "duration_hours",
                "g7_ot_hours": "overtime_hours"
            }
            
            for csv_col, task_col in csv_to_task_map.items():
                if csv_col in task_dict and pd.notna(task_dict[csv_col]):
                    task_dict[task_col] = float(task_dict[csv_col]) if "cost" in task_col or "hours" in task_col or "days" in task_col else task_dict[csv_col]
                    
            filtered_task_dict = {k: v for k, v in task_dict.items() if k in valid_task_columns}
            
            # Map cost targets
            filtered_task_dict["base_cost"] = task_dict.get("base_cost", 0.0)
            
            # Auto sum total cost if missing
            if not task_dict.get("total_cost"):
                total = sum([
                    float(task_dict.get(c) or 0.0) for c in [
                        "internal_labor_cost", "overtime_cost", "equipment_fuel_cost", "qa_qc_cost", "material_cost", "outsourcing_cost",
                        "training_cost", "facility_rent", "communication_cost", "utilities_cost",
                        "insurance_cost", "licensing_cost", "warranty_cost",
                        "holding_cost", "international_freight", "handling_cost", "reverse_logistics", "defect_cost"
                    ]
                ])
                filtered_task_dict["total_cost"] = total
            else:
                filtered_task_dict["total_cost"] = task_dict.get("total_cost", 0.0)
                
            filtered_task_dict["risk_factor"] = task_dict.get("risk_factor", 1.0)
            
            tasks_to_insert.append(Task(**filtered_task_dict))
            
        db.add_all(tasks_to_insert)
        await db.commit()
        print(f"  - Import {len(tasks_to_insert)} Tasks thành công.")

    # 3. Tạo Resources
    res_file = project_folder / "resources.csv"
    res_mapping = {} # Name -> ID
    if res_file.exists():
        df_res = pd.read_csv(res_file)
        df_res = df_res.where(pd.notnull(df_res), None)
        
        for row_dict in df_res.to_dict(orient="records"):
            row = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            # CSV: 'ID', 'Name'/'resource_name', 'Type'/'resource_type', 'Availability'/'capacity', 'Cost/Use'/'cost_per_use', 'Cost/Unit'/'unit_cost'
            res = ProjectConstraintResource(
                project_id=project_id,
                resource_name=row.get("resource_name", row.get("Name", "")),
                resource_type=row.get("resource_type", row.get("Type", "Renewable")),
                max_availability=row.get("capacity", row.get("Availability", 1.0)) or 1.0,
                cost_per_use=row.get("cost_per_use", row.get("Cost/Use", 0)) or 0.0,
                cost_per_unit=row.get("unit_cost", row.get("Cost/Unit", 0)) or 0.0
            )
            db.add(res)
            await db.commit() # Cần commit để lấy ID
            await db.refresh(res)
            
            original_res_id = str(row.get("ID", row.get("id", "")))
            res_mapping[original_res_id] = res.id
            
        print(f"  - Import {len(df_res)} Resources thành công.")

    # 4. Tạo Task Resources (G7)
    task_res_file = project_folder / "task_resources.csv"
    if task_res_file.exists():
        df_tr = pd.read_csv(task_res_file)
        df_tr = df_tr.where(pd.notnull(df_tr), None)
        
        tr_to_insert = []
        for row_dict in df_tr.to_dict(orient="records"):
            row = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            csv_task_id = str(row['task_id'])
            if "_" in csv_task_id:
                original_task_id = csv_task_id.split("_", 1)[1]
            else:
                original_task_id = csv_task_id
                
            task_id = f"{project_id}_{original_task_id}"
            
            original_res_id = str(row.get("resource_id", ""))
            if original_res_id in res_mapping:
                actual_res_id = res_mapping[original_res_id]
                tr = TaskResource(
                    task_id=task_id,
                    resource_id=actual_res_id,
                    request_quantity=row.get("quantity", row.get("request_quantity", 1.0))
                )
                tr_to_insert.append(tr)
                
        if tr_to_insert:
            db.add_all(tr_to_insert)
            await db.commit()
            print(f"  - Import {len(tr_to_insert)} Task-Resources thành công.")

    # 5. Tạo Logic Constraints (Edges)
    pred_file = project_folder / "predecessors.csv"
    if pred_file.exists():
        df_pred = pd.read_csv(pred_file)
        df_pred = df_pred.where(pd.notnull(df_pred), None)
        
        from sqlalchemy import select
        result = await db.execute(select(Task.id).where(Task.project_id == project_id))
        valid_task_ids = {row[0] for row in result.all()}
        
        edges_to_insert = []
        for row_dict in df_pred.to_dict(orient="records"):
            row = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            predecessor_id = str(row.get("predecessor_task_id", row.get("source_id")))
            successor_id = str(row.get("successor_task_id", row.get("target_id")))
            
            if predecessor_id in ("None", "nan") or successor_id in ("None", "nan"):
                continue
                
            if "_" in predecessor_id:
                pred_orig = predecessor_id.split("_", 1)[1]
            else:
                pred_orig = predecessor_id
                
            if "_" in successor_id:
                succ_orig = successor_id.split("_", 1)[1]
            else:
                succ_orig = successor_id
                
            pred_full_id = f"{project_id}_{pred_orig}"
            succ_full_id = f"{project_id}_{succ_orig}"
            
            if pred_full_id not in valid_task_ids or succ_full_id not in valid_task_ids:
                print(f"    [!] Warning: Skipping edge {pred_full_id} -> {succ_full_id} (Node not found)")
                continue
                
            edge = ProjectConstraintLogic(
                project_id=project_id,
                predecessor_id=pred_full_id,
                successor_id=succ_full_id,
                dependency_type=row.get("dependency_type", "FS"),
                lag_months=row.get("lag_months", 0),
                lag_weeks=row.get("lag_weeks", 0),
                lag_days=row.get("lag_days", 0),
                lag_hours=row.get("lag_hours", 0)
            )
            edges_to_insert.append(edge)
            
        db.add_all(edges_to_insert)
        await db.commit()
        print(f"  - Import {len(edges_to_insert)} Edges thành công.")

    # 6. Tạo Time Constraints
    # Đọc agenda_working_days, agenda_working_hours, agenda_holidays
    weekly_schedule = {}
    holidays_list = []
    
    days_file = project_folder / "agenda_working_days.csv"
    if days_file.exists():
        df_days = pd.read_csv(days_file)
        for _, row in df_days.iterrows():
            day = str(row["Day"]).lower()
            working = str(row.get("Working", "Yes")).lower() == "yes"
            weekly_schedule[day] = [] if working else None
            
    hours_file = project_folder / "agenda_working_hours.csv"
    if hours_file.exists():
        df_hours = pd.read_csv(hours_file)
        for _, row in df_hours.iterrows():
            time_range = row.get("Time Range")
            working = str(row.get("Working", "Yes")).lower() == "yes"
            # Giả định nếu Working = No, thì loại bỏ khoảng thời gian này
            # Thực tế schedule thường lưu các ca làm việc (Shift)
            # Tạm thời gán mẫu
            pass 
            
    # Gán mẫu schedule nếu rỗng
    if not weekly_schedule:
        weekly_schedule = {
            "monday": ["08:00-17:00"],
            "tuesday": ["08:00-17:00"],
            "wednesday": ["08:00-17:00"],
            "thursday": ["08:00-17:00"],
            "friday": ["08:00-17:00"],
            "saturday": [],
            "sunday": []
        }
        
    time_constraint = ProjectConstraintTime(
        project_id=project_id,
        weekly_schedule=weekly_schedule,
        holidays_list=holidays_list,
        overtime_multiplier=1.5
    )
    db.add(time_constraint)
    await db.commit()
    print(f"  - Import Time Constraints thành công.")


async def main():
    async with async_session() as db:
        await clear_existing_data(db) # Xóa trắng CSDL trước khi nạp
        
        for folder in DATA_DIR.iterdir():
            if folder.is_dir():
                await process_project(db, folder)
                
    print("\n[+] HOÀN THÀNH LOAD DATA VÀO DATABASE!")

if __name__ == "__main__":
    asyncio.run(main())
