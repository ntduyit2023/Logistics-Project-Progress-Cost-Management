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

    async def search_projects(
        self,
        db: AsyncSession,
        q: Optional[str],
        project_type: Optional[str],
        status: Optional[str],
        page: int,
        page_size: int
    ) -> PaginatedResponse[Any]:
        """
        Tìm kiếm Full-Text Search và Lọc theo loại hình (project_type) & trạng thái (status).
        """
        query = select(self.model)
        
        if q and q.strip():
            clean_q = q.strip()
            search_pattern = f"%{clean_q}%"
            
            # PostgreSQL Native Full-Text Search Vector
            ts_vector = func.to_tsvector('simple', func.coalesce(self.model.project_name, '') + ' ' + func.coalesce(self.model.id, ''))
            ts_query = func.plainto_tsquery('simple', clean_q)
            
            query = query.filter(
                (ts_vector.op('@@')(ts_query)) |
                (self.model.project_name.ilike(search_pattern)) | 
                (self.model.id.ilike(search_pattern))
            )
            
        if project_type and project_type.strip():
            query = query.filter(self.model.project_type.ilike(project_type.strip()))
            
        if status and status.strip():
            query = query.filter(self.model.status.ilike(status.strip()))
            
        # Sắp xếp mới nhất lên đầu
        query = query.order_by(self.model.created_at.desc())
        
        return await self.paginate(db, query, page, page_size)


# Cung cấp instance Singleton
project_repo = ProjectRepository(AppProject)
