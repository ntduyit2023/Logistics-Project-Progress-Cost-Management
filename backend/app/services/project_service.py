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

from app.schemas import (
    ProjectGraphResponse, PaginatedResponse, ProjectSummary, ProjectDetail,
    ProjectCreate, ProjectUpdate
)

# ==============================================================================
# QUERIES
# ==============================================================================

async def search_projects(db: AsyncSession, q: Optional[str], page: int, page_size: int) -> PaginatedResponse[ProjectSummary]:
    """
    Tìm kiếm và phân trang danh sách các dự án.

    Args:
        db (AsyncSession): Phiên kết nối DB.
        q (Optional[str]): Từ khóa tìm kiếm tên dự án.
        page (int): Trang hiện tại.
        page_size (int): Số lượng trên một trang.

    Returns:
        PaginatedResponse[ProjectSummary]: Kết quả phân trang Dự án.
    """
    paginated = await project_repo.search_projects(db, q, page, page_size)
    
    # Map to ProjectSummary
    summaries = []
    for p in paginated.items:
        # Quick counts
        tasks = await task_repo.get_by_project(db, p.id)
        edges = await dependency_repo.get_by_project(db, p.id)
        summaries.append(ProjectSummary(
            id=p.id,
            project_name=p.project_name,
            metadata_json=p.metadata_json,
            num_tasks=len(tasks),
            num_edges=len(edges),
            network_density=0.0,
            status=p.status,
            created_at=p.created_at,
            updated_at=p.updated_at
        ))
        
    return PaginatedResponse(
        total=paginated.total,
        page=paginated.page,
        page_size=paginated.page_size,
        total_pages=paginated.total_pages,
        items=summaries
    )


async def get_project_summary(db: AsyncSession, project_id: int) -> ProjectSummary:
    """
    Lấy thông tin tóm tắt cơ bản của một dự án (không tải toàn bộ nodes, edges).
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với ID {project_id}"
        )
        
    tasks = await task_repo.get_by_project(db, project_id)
    dependencies = await dependency_repo.get_by_project(db, project_id)
    
    return ProjectSummary(
        id=project.id,
        project_name=project.project_name,
        metadata_json=project.metadata_json,
        num_tasks=len(tasks),
        num_edges=len(dependencies),
        network_density=0.0,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


async def get_project_detail(db: AsyncSession, project_id: int) -> ProjectDetail:
    """
    Lấy thông tin chi tiết một dự án.

    Args:
        db (AsyncSession): Phiên DB.
        project_id (int): ID dự án.

    Returns:
        ProjectDetail: Chi tiết dự án cùng các công việc.

    Raises:
        HTTPException: Nếu dự án không tồn tại.
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
        metadata_json=project.metadata_json,
        num_tasks=len(tasks),
        num_edges=len(dependencies),
        network_density=0.0,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        tasks=tasks,
        constraint_logic=dependencies,
        constraint_resources=[],
        constraint_time=None
    )


async def get_project_graph(db: AsyncSession, project_id: int) -> ProjectGraphResponse:
    """
    Lấy toàn bộ dữ liệu Đồ thị mạng lưới của một Dự án.

    Args:
        db (AsyncSession): Phiên kết nối DB.
        project_id (int): ID dự án.

    Returns:
        ProjectGraphResponse: Mảng Nodes và Edges.

    Raises:
        HTTPException: Nếu không có dữ liệu Graph.
    """
    tasks = await task_repo.get_by_project(db, project_id)
    edges = await dependency_repo.get_by_project(db, project_id)
    
    if not tasks and not edges:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dữ liệu Graph cho dự án có ID {project_id}."
        )
        
    return ProjectGraphResponse(
        project_id=project_id,
        nodes=tasks,
        edges=edges
    )


# ==============================================================================
# MUTATIONS (CREATES)
# ==============================================================================

async def create_project(db: AsyncSession, project_in: ProjectCreate) -> Any:
    """
    Khởi tạo một dự án mới.

    Args:
        db (AsyncSession): Phiên DB.
        project_in (ProjectCreate): Dữ liệu khởi tạo.

    Returns:
        Any: Đối tượng Dự án vừa tạo.
    """
    return await project_repo.create(db, obj_in=project_in)


# ==============================================================================
# MUTATIONS (UPDATES & DELETES)
# ==============================================================================

async def update_project(db: AsyncSession, project_id: int, project_in: ProjectUpdate) -> Any:
    """
    Cập nhật thông tin dự án.

    Args:
        db (AsyncSession): Phiên DB.
        project_id (int): ID dự án.
        project_in (ProjectUpdate): Dữ liệu cập nhật.

    Returns:
        Any: Dự án sau cập nhật.

    Raises:
        HTTPException: Nếu không tìm thấy.
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")
    return await project_repo.update(db, db_obj=project, obj_in=project_in)


async def delete_project(db: AsyncSession, project_id: int) -> Any:
    """
    Xóa toàn bộ dự án.

    Args:
        db (AsyncSession): Phiên DB.
        project_id (int): ID dự án.

    Returns:
        Any: Dự án vừa bị xóa.

    Raises:
        HTTPException: Nếu không tìm thấy.
    """
    project = await project_repo.delete(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")
    return project
