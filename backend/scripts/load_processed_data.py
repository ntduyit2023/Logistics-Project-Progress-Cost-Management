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

DATA_DIR = Path("/ai_pipeline/data/processed")

async def clear_existing_data(db: AsyncSession):
    print("Xóa dữ liệu cũ...")
    # Vì đã cấu hình ON DELETE CASCADE trên DB, ta chỉ cần xóa các project cũ (hoặc toàn bộ)
    await db.execute(delete(AppProject))
    await db.commit()

async def process_project(db: AsyncSession, project_folder: Path):
    project_name = project_folder.name
    if project_name.startswith("~") or not project_folder.is_dir():
        return
        
    print(f"\n=> Đang import dự án: {project_name}")
    
    # 1. Tạo Project
    project = AppProject(project_name=project_name, status="Planning")
    db.add(project)
    await db.commit()
    await db.refresh(project)
    project_id = project.id
    
    # 2. Tạo Tasks (Wide Table)
    tasks_file = project_folder / "tasks.csv"
    if tasks_file.exists():
        df_tasks = pd.read_csv(tasks_file)
        # Handle NaN -> None
        df_tasks = df_tasks.where(pd.notnull(df_tasks), None)
        
        tasks_to_insert = []
        valid_task_columns = {c.name for c in Task.__table__.columns}
        
        for _, row in df_tasks.iterrows():
            task_dict = row.to_dict()
            task_dict["project_id"] = project_id
            
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
                
            filtered_task_dict = {k: v for k, v in task_dict.items() if k in valid_task_columns}
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
        
        for _, row in df_res.iterrows():
            # CSV: 'ID', 'Name', 'Type', 'Availability', 'Cost/Use', 'Cost/Unit'
            res = ProjectConstraintResource(
                project_id=project_id,
                resource_name=row["Name"],
                resource_type=row.get("Type", "Renewable"),
                max_availability=row.get("Availability", 1.0) or 1.0,
                cost_per_use=row.get("Cost/Use", 0) or 0.0,
                cost_per_unit=row.get("Cost/Unit", 0) or 0.0
            )
            db.add(res)
            await db.commit() # Cần commit để lấy ID
            await db.refresh(res)
            res_mapping[res.resource_name] = res.id
            
        print(f"  - Import {len(df_res)} Resources thành công.")

    # 4. Tạo Task Resources (G7)
    task_res_file = project_folder / "task_resources.csv"
    if task_res_file.exists():
        df_tr = pd.read_csv(task_res_file)
        df_tr = df_tr.where(pd.notnull(df_tr), None)
        
        tr_to_insert = []
        for _, row in df_tr.iterrows():
            res_name = str(row["resource_id"])
            if res_name in res_mapping:
                actual_res_id = res_mapping[res_name]
                tr = TaskResource(
                    task_id=row["task_id"],
                    resource_id=actual_res_id,
                    request_quantity=row.get("request_quantity", 1.0)
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
        
        edges_to_insert = []
        for _, row in df_pred.iterrows():
            if pd.isna(row["predecessor_task_id"]) or pd.isna(row["successor_task_id"]):
                continue
                
            edge = ProjectConstraintLogic(
                project_id=project_id,
                predecessor_id=row["predecessor_task_id"],
                successor_id=row["successor_task_id"],
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
