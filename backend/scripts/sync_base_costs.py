import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import async_session
from app.models import Task, AppProject
from app.services.task_service import _recalculate_task_costs, _recalculate_project_costs
from app.repositories.project import project_repo

async def run():
    print("Starting sync base costs...")
    async with async_session() as db:
        stmt = select(AppProject)
        result = await db.execute(stmt)
        projects = result.scalars().all()
        
        for project in projects:
            print(f"Processing Project {project.id}: {project.project_name}")
            
            stmt_tasks = select(Task).where(Task.project_id == project.id)
            result_tasks = await db.execute(stmt_tasks)
            tasks = result_tasks.scalars().all()
            
            for task in tasks:
                await _recalculate_task_costs(db, project, task.id)
                
            await _recalculate_project_costs(db, project.id)
            print(f"Finished Project {project.id}")
            
        await db.commit()
    print("Done sync base costs.")

if __name__ == "__main__":
    asyncio.run(run())
