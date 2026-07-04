"""
GLPO Backend - Project Repository
"""
from typing import Optional, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppProject
from app.repositories.base import BaseRepository
from app.schemas import PaginatedResponse, ProjectCreate, ProjectUpdate


class ProjectRepository(BaseRepository[AppProject, ProjectCreate, ProjectUpdate]):
    """
    Repository thao tác với bảng app_projects.
    """

    async def search_projects(self, db: AsyncSession, q: Optional[str], page: int, page_size: int) -> PaginatedResponse[Any]:
        """
        Tìm kiếm và phân trang danh sách các dự án.
        """
        query = select(self.model)
        
        if q:
            formatted_query = ' & '.join(q.split())
            query = query.filter(
                self.model.search_vector.op('@@')(func.to_tsquery('simple', formatted_query))
            )
            
        # Sắp xếp mới nhất lên đầu
        query = query.order_by(self.model.created_at.desc())
        
        return await self.paginate(db, query, page, page_size)


# Cung cấp instance Singleton
project_repo = ProjectRepository(AppProject)
