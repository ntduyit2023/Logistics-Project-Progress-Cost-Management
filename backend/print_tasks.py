import asyncio
from app.db.database import async_session
import sys
sys.path.append('/')
from ai_pipeline.models.moi.pipeline_runner import run_new_pipeline

async def run_test():
    async with async_session() as db:
        from app.models.project import Task
        from sqlalchemy import select
        stmt = select(Task).where(Task.project_code == 'C2011-07').limit(1)
        res = await db.execute(stmt)
        task = res.scalars().first()
        print("Task:", task.task_name)
        print("Baseline start:", task.baseline_start)

asyncio.run(run_test())
