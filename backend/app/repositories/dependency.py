"""
GLPO Backend - Dependency (Edge) Repository
"""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TaskLogic
from app.repositories.base import BaseRepository
from app.schemas import ConstraintLogicBase


class DependencyRepository(BaseRepository[TaskLogic, ConstraintLogicBase, ConstraintLogicBase]):
    """
    Repository thao tác với bảng task_logic (Các cạnh của đồ thị).
    """

    async def get_by_project(self, db: AsyncSession, project_id: int) -> List[TaskLogic]:
        """
        Lấy danh sách tất cả các liên kết (Edges) của một dự án.
        """
        stmt = select(self.model).filter(self.model.project_id == project_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

# Cung cấp instance Singleton
dependency_repo = DependencyRepository(TaskLogic)
