"""
GLPO Backend - Task Repository
"""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task
from app.repositories.base import BaseRepository
from app.schemas import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    """
    Repository thao tác với bảng tasks (Wide Table).
    """
    
    async def get_by_project(self, db: AsyncSession, project_id: int) -> List[Task]:
        """
        Lấy danh sách tất cả các công việc (Nodes) của một dự án.
        Vì dùng kiến trúc Wide Table, toàn bộ Features đã nằm sẵn trong bảng Tasks, 
        không cần phải JOIN hay selectinload các Dimensions nữa.
        """
        stmt = select(self.model).filter(self.model.project_id == project_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

# Cung cấp instance Singleton
task_repo = TaskRepository(Task)
