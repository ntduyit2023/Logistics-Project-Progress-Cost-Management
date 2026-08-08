from app.models.task import Task
from app.db.session import SessionLocal
from sqlalchemy import select
import asyncio

async def run():
    async with SessionLocal() as db:
        res = await db.execute(select(Task).where(Task.task_name == 'Cleaning site'))
        t = res.scalars().first()
        if t:
            print("Task 29 baseline_start:", t.baseline_start)
        else:
            print("Not found")

asyncio.run(run())
