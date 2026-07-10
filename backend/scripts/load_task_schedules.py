import asyncio
import sys
import os
import pandas as pd
from pathlib import Path

# Add backend dir to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import async_session
from app.models import AppProject, Task

# Detect if running in Docker or natively
if Path("/ai_pipeline/data/processed").exists():
    DATA_DIR = Path("/ai_pipeline/data/processed")
else:
    DATA_DIR = backend_dir.parent / "ai_pipeline" / "data" / "processed"

async def run():
    print("Starting load task_schedules.csv...")
    async with async_session() as db:
        stmt = select(AppProject)
        result = await db.execute(stmt)
        projects = {p.project_name: p.id for p in result.scalars().all()}
        
        updated_count = 0
        
        for project_folder in DATA_DIR.iterdir():
            if not project_folder.is_dir() or project_folder.name.startswith("~"):
                continue
                
            project_name = project_folder.name
            info_file = project_folder / "project_info.csv"
            if info_file.exists():
                df_info = pd.read_csv(info_file)
                if not df_info.empty:
                    info = df_info.iloc[0]
                    project_name = info.get("project_name", project_name)
                    
            project_id = projects.get(project_name)
            if not project_id:
                print(f"Project '{project_name}' not found in DB.")
                continue
                
            schedule_file = project_folder / "task_schedules.csv"
            if schedule_file.exists():
                df_schedule = pd.read_csv(schedule_file)
                df_schedule = df_schedule.where(pd.notnull(df_schedule), None)
                
                # Pre-fetch tasks for this project to speed up updates
                stmt_tasks = select(Task).where(Task.project_id == project_id)
                res_tasks = await db.execute(stmt_tasks)
                tasks_dict = {t.id: t for t in res_tasks.scalars().all()}
                
                project_updated = 0
                for _, row in df_schedule.iterrows():
                    tid_raw = str(row.get("task_id", ""))
                    if not tid_raw: continue
                    
                    db_task_id = f"{project_id}_{tid_raw}"
                    if db_task_id in tasks_dict:
                        t = tasks_dict[db_task_id]
                        # Only loading baseline_start, specifically ignoring baseline_end
                        start_val = row.get("baseline_start")
                        if start_val and pd.notna(start_val):
                            try:
                                t.baseline_start = pd.to_datetime(start_val).to_pydatetime()
                                db.add(t)
                                project_updated += 1
                                updated_count += 1
                            except Exception as e:
                                print(f"Error parsing date {start_val}: {e}")
                                
                print(f"Updated {project_updated} tasks in project '{project_name}'.")
                
        await db.commit()
    print(f"Done loading task schedules. Total tasks updated: {updated_count}")

if __name__ == "__main__":
    asyncio.run(run())
