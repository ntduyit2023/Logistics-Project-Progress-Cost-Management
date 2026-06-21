"""
GLPO Backend - Project Service Logic
Chứa các logic nghiệp vụ liên quan đến Dự án, bao gồm việc tính toán, tổng hợp Graph.
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional, Any
from app.repositories.project import project_repo
from app.repositories.task import task_repo
from app.repositories.dependency import dependency_repo
from app.schemas.schemas import ProjectGraphResponse, PaginatedResponse, ProjectSummary, ProjectDetail
from app.models.models import AppProject


async def search_projects(db: AsyncSession, q: Optional[str], page: int, page_size: int) -> PaginatedResponse[Any]:
    """
    Tìm kiếm và phân trang dự án. Dùng để làm danh sách ngoài trang chủ.

    Args:
        db (AsyncSession): Phiên DB.
        q (str): Từ khóa tìm kiếm.
        page (int): Trang hiện tại.
        page_size (int): Số lượng trên một trang.

    Returns:
        PaginatedResponse[AppProject]: Kết quả phân trang.
    """
    return await project_repo.search_projects(db, q, page, page_size)


async def get_project_detail(db: AsyncSession, project_id: int) -> ProjectDetail:
    """
    Lấy thông tin chi tiết một dự án bao gồm toàn bộ Nodes (tasks) và Edges (dependencies).
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với ID {project_id}"
        )
        
    tasks = await task_repo.get_by_project(db, project_id)
    dependencies = await dependency_repo.get_by_project(db, project_id)
    
    return ProjectDetail(
        id=project.id,
        project_name=project.project_name,
        num_tasks=project.num_tasks,
        num_edges=project.num_edges,
        network_density=project.network_density,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        working_hours=project.working_hours,
        working_days=project.working_days,
        tasks=tasks,
        dependencies=dependencies
    )


async def get_project_graph(db: AsyncSession, project_id: int) -> ProjectGraphResponse:
    """
    Lấy toàn bộ dữ liệu Đồ thị mạng lưới (Nodes & Edges) của một Dự án.

    Args:
        db (AsyncSession): Phiên kết nối DB.
        project_id (int): ID dự án.

    Returns:
        ProjectGraphResponse: Object chứa mảng Nodes (Tasks) và Edges (Dependencies).

    Raises:
        HTTPException (404): Nếu dự án không có bất kỳ Task hay Edge nào.
    """
    # 1. Fetch tất cả Nodes (kèm Dimensions)
    tasks = await task_repo.get_by_project(db, project_id)
    
    # 2. Fetch tất cả Edges
    edges = await dependency_repo.get_by_project(db, project_id)
    
    if not tasks and not edges:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dữ liệu Graph (Nodes/Edges) cho dự án có ID {project_id}."
        )
        
    return ProjectGraphResponse(
        project_id=project_id,
        nodes=tasks,
        edges=edges
    )
