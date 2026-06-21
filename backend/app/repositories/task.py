"""
GLPO Backend - Task Repository
"""
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import FactTask
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[FactTask, None, None]):
    """
    Repository thao tác với bảng fact_tasks.
    """
    
    async def get_by_project(self, db: AsyncSession, project_id: int) -> List[FactTask]:
        """
        Lấy danh sách tất cả các công việc (Nodes) của một dự án,
        Eager-load luôn toàn bộ các Dimensions đi kèm.

        Args:
            db (AsyncSession): Phiên kết nối DB.
            project_id (int): ID dự án.

        Returns:
            List[FactTask]: Danh sách các Tasks (Nodes).
        """
        stmt = (
            select(self.model)
            .filter(self.model.project_id == project_id)
            .options(
                selectinload(self.model.time_info),
                selectinload(self.model.cost_info),
                selectinload(self.model.risk_info),
                selectinload(self.model.resource_info),
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

# Cung cấp instance Singleton
task_repo = TaskRepository(FactTask)
