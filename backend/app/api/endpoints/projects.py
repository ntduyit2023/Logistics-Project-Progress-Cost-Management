"""
GLPO Backend - Projects API Endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.schemas import ProjectGraphResponse, APIResponse, PaginatedResponse, ProjectSummary, ProjectDetail
from app.services import project_service

router = APIRouter()


@router.get("", response_model=APIResponse[PaginatedResponse[ProjectSummary]], summary="Danh sách Dự án")
async def get_projects_api(
    q: Optional[str] = Query(None, description="Từ khóa tìm kiếm theo tên"),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Kích thước trang"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[PaginatedResponse[ProjectSummary]]:
    """
    Lấy danh sách tóm tắt các dự án. Hỗ trợ tìm kiếm theo tên và phân trang.
    """
    data = await project_service.search_projects(db, q, page, page_size)
    return APIResponse(
        success=True,
        message="Lấy danh sách dự án thành công.",
        data=data
    )


@router.get("/{project_id}", response_model=APIResponse[ProjectDetail], summary="Chi tiết Dự án")
async def get_project_api(
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ProjectDetail]:
    """
    Lấy thông tin chi tiết của một dự án, bao gồm lịch làm việc, toàn bộ công việc (Tasks) và liên kết (Dependencies).
    """
    data = await project_service.get_project_detail(db, project_id)
    return APIResponse(
        success=True,
        message="Lấy chi tiết dự án thành công.",
        data=data
    )


@router.get("/{project_id}/graph", response_model=APIResponse[ProjectGraphResponse], summary="Lấy dữ liệu Đồ thị Dự án")
async def get_project_graph_api(project_id: int, db: AsyncSession = Depends(get_db)) -> APIResponse[ProjectGraphResponse]:
    """
    API lấy toàn bộ dữ liệu Đồ thị mạng lưới (Nodes & Edges) của một Dự án phục vụ việc vẽ biểu đồ trên Frontend.

    Args:
        project_id (int): ID của dự án cần lấy Graph.
        db (AsyncSession): Database session (Dependency Injection).

    Returns:
        APIResponse[ProjectGraphResponse]: Dữ liệu đồ thị bao gồm Nodes và Edges.
    """
    data = await project_service.get_project_graph(db, project_id)
    return APIResponse(
        success=True,
        message="Lấy dữ liệu đồ thị thành công.",
        data=data
    )
