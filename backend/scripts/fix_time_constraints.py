import asyncio
import sys
import os
import pandas as pd
from pathlib import Path

# Add backend dir to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.database import async_session
from app.models.project import AppProject as Project
from app.models.constraint import ProjectConstraintTime

DATA_DIR = backend_dir.parent / "ai_pipeline" / "data" / "processed"

async def update_time_constraints():
    async with async_session() as db:
        result = await db.execute(select(Project.id, Project.metadata_json))
        projects = result.all()
        
        for project_id, metadata in projects:
            corpus_name = metadata.get("corpus_name") if metadata else None
            if not corpus_name:
                continue
                
            project_folder = DATA_DIR / corpus_name
            if not project_folder.exists():
                continue
                
            # Parse working days
            weekly_schedule = {}
            days_file = project_folder / "agenda_working_days.csv"
            if days_file.exists():
                df_days = pd.read_csv(days_file)
                for _, row in df_days.iterrows():
                    day = str(row["Day"]).lower()
                    working = str(row.get("Working", "Yes")).lower() == "yes"
                    weekly_schedule[day] = [] if working else None

            # Parse working hours
            hours_file = project_folder / "agenda_working_hours.csv"
            working_ranges = []
            if hours_file.exists():
                df_hours = pd.read_csv(hours_file)
                
                # Combine contiguous Yes blocks
                current_start = None
                current_end = None
                
                for _, row in df_hours.iterrows():
                    time_range = str(row.get("Time Range"))
                    working = str(row.get("Working", "Yes")).lower() == "yes"
                    
                    if working:
                        start_str, end_str = [t.strip() for t in time_range.split("-")]
                        # Format "8:00" to "08:00"
                        if len(start_str) == 4: start_str = "0" + start_str
                        if len(end_str) == 4: end_str = "0" + end_str
                        
                        if current_start is None:
                            current_start = start_str
                            current_end = end_str
                        elif current_end == start_str:
                            current_end = end_str
                        else:
                            working_ranges.append(f"{current_start}-{current_end}")
                            current_start = start_str
                            current_end = end_str
                    else:
                        if current_start is not None:
                            working_ranges.append(f"{current_start}-{current_end}")
                            current_start = None
                            current_end = None
                            
                if current_start is not None:
                    working_ranges.append(f"{current_start}-{current_end}")
            
            if not working_ranges:
                working_ranges = ["08:00-12:00", "13:00-17:00"]
                
            # Apply working ranges to working days
            for day in weekly_schedule:
                if weekly_schedule[day] is not None:
                    weekly_schedule[day] = list(working_ranges)
                    
            if not weekly_schedule:
                weekly_schedule = {
                    "monday": working_ranges,
                    "tuesday": working_ranges,
                    "wednesday": working_ranges,
                    "thursday": working_ranges,
                    "friday": working_ranges,
                    "saturday": None,
                    "sunday": None
                }
                
            print(f"Updating project {project_id} with schedule: {weekly_schedule}")
            # Update DB
            stmt = update(ProjectConstraintTime).where(
                ProjectConstraintTime.project_id == project_id
            ).values(weekly_schedule=weekly_schedule)
            await db.execute(stmt)
            
        await db.commit()
        print("Done updating time constraints!")

if __name__ == "__main__":
    asyncio.run(update_time_constraints())
