"""
GLPO Backend - Project Repository
"""
from typing import Optional, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AppProject
from app.repositories.base import BaseRepository
from app.schemas.schemas import PaginatedResponse


class ProjectRepository(BaseRepository[AppProject, None, None]):
    """
    Repository thao tác với bảng app_projects.
    """

    async def search_projects(self, db: AsyncSession, q: Optional[str], page: int, page_size: int) -> PaginatedResponse[Any]:
        """
        Tìm kiếm và phân trang danh sách các dự án.

        Args:
            db (AsyncSession): Phiên kết nối DB.
            q (Optional[str]): Chuỗi tìm kiếm tên dự án.
            page (int): Trang hiện tại.
            page_size (int): Số bản ghi trên 1 trang.

        Returns:
            PaginatedResponse[AppProject]: Dữ liệu phân trang các Dự án.
        """
        query = select(self.model)
        
        if q:
            # Sử dụng Full-Text Search (FTS) với to_tsquery để map với search_vector
            # Chuyển đổi khoảng trắng thành toán tử AND (&) cho tsquery
            formatted_query = ' & '.join(q.split())
            query = query.filter(
                self.model.search_vector.op('@@')(func.to_tsquery('simple', formatted_query))
            )
            
        # Sắp xếp mới nhất lên đầu
        query = query.order_by(self.model.created_at.desc())
        
        return await self.paginate(db, query, page, page_size)


# Cung cấp instance Singleton
project_repo = ProjectRepository(AppProject)
