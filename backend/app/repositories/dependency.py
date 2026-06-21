"""
GLPO Backend - Dependency (Edge) Repository
"""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import BridgeTaskDependency
from app.repositories.base import BaseRepository


class DependencyRepository(BaseRepository[BridgeTaskDependency, None, None]):
    """
    Repository thao tác với bảng bridge_task_dependencies (Các cạnh của đồ thị).
    """

    async def get_by_project(self, db: AsyncSession, project_id: int) -> List[BridgeTaskDependency]:
        """
        Lấy danh sách tất cả các liên kết (Edges) của một dự án.

        Args:
            db (AsyncSession): Phiên kết nối DB.
            project_id (int): ID dự án.

        Returns:
            List[BridgeTaskDependency]: Danh sách các liên kết (Edges).
        """
        stmt = select(self.model).filter(self.model.project_id == project_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

# Cung cấp instance Singleton
dependency_repo = DependencyRepository(BridgeTaskDependency)
