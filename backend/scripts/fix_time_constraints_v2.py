import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.db.database import async_session
from app.models.constraint import ProjectConstraintTime

async def fix():
    schedule = {
        "monday": ["08:00-12:00", "13:00-17:00"],
        "tuesday": ["08:00-12:00", "13:00-17:00"],
        "wednesday": ["08:00-12:00", "13:00-17:00"],
        "thursday": ["08:00-12:00", "13:00-17:00"],
        "friday": ["08:00-12:00", "13:00-17:00"],
        "saturday": [],
        "sunday": []
    }
    
    async with async_session() as db:
        stmt = update(ProjectConstraintTime).values(weekly_schedule=schedule)
        await db.execute(stmt)
        await db.commit()
        print("Updated all time constraints to default schedule!")

if __name__ == "__main__":
    asyncio.run(fix())
