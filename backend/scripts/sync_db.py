import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.db.database import engine, Base
# Import all models to ensure they are registered with Base
from app.models.models import *

async def init_db():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    print("Creating all tables based on models.py...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database synchronized!")

if __name__ == "__main__":
    asyncio.run(init_db())
