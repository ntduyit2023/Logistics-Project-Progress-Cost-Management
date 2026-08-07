import asyncio
import sys
from pathlib import Path

# Thêm đường dẫn tuyệt đối vào sys.path để có thể import app
root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir))

from app.db.database import engine, Base
# Import toàn bộ models để Base đăng ký
from app.models.project import AppProject, ProjectCalendar, Resource, TaskLogic, TaskResource
from app.models.task import Task
from app.models.user import User

async def reset_db():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("DB reset complete!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_db())
