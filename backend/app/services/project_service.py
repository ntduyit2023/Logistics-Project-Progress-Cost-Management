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

async def search_projects(
    db: AsyncSession,
    q: Optional[str],
    project_type: Optional[str],
    status: Optional[str],
    page: int,
    page_size: int
) -> PaginatedResponse[ProjectSummary]:
    """
    Tìm kiếm và phân trang danh sách các dự án có hỗ trợ lọc theo loại hình và trạng thái.
    """
    paginated = await project_repo.search_projects(db, q, project_type, status, page, page_size)
    
    # Map to ProjectSummary
    summaries = []
    for p in paginated.items:
        # Quick counts
        tasks = await task_repo.get_by_project(db, p.id)
        edges = await dependency_repo.get_by_project(db, p.id)
        # Calculate network density
        num_tasks = len(tasks)
        num_edges = len(edges)
        network_density = (num_edges / (num_tasks * (num_tasks - 1))) if num_tasks > 1 else 0.0
        
        summaries.append(ProjectSummary(
            id=p.id,
            project_code=p.project_code,
            project_name=p.project_name,
            project_type=p.project_type,
            status=p.status,
            target_deadline=p.target_deadline,
            penalty_per_day=p.penalty_per_day,
            bonus_per_day=p.bonus_per_day,
            base_cost=p.base_cost,
            total_cost=p.total_cost,
            num_tasks=num_tasks,
            num_edges=num_edges,
            network_density=network_density,
            metadata_json=p.metadata_json,
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


from app.models import AppProject
from sqlalchemy import select

async def get_project_by_identifier(db: AsyncSession, identifier: Any) -> AppProject:
    """
    Tìm kiếm Dự án theo Mã/ID (ví dụ 'C2011-07').
    """
    id_str = str(identifier).strip()
    stmt = select(AppProject).where(AppProject.id.ilike(id_str))
    result = await db.execute(stmt)
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với Mã '{identifier}'."
        )
    return project


async def get_project_summary(db: AsyncSession, project_id: Any) -> ProjectSummary:
    """
    Lấy thông tin tóm tắt của một Dự án theo ID hoặc Mã C2011-07.
    """
    project = await get_project_by_identifier(db, project_id)
    tasks = await task_repo.get_by_project(db, project.id)
    dependencies = await dependency_repo.get_by_project(db, project.id)
    
    return ProjectSummary(
        id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        project_type=project.project_type,
        status=project.status,
        target_deadline=project.target_deadline,
        penalty_per_day=project.penalty_per_day,
        bonus_per_day=project.bonus_per_day,
        base_cost=project.base_cost,
        total_cost=project.total_cost,
        num_tasks=len(tasks),
        num_edges=len(dependencies),
        network_density=0.0,
        metadata_json=project.metadata_json,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


async def get_project_detail(db: AsyncSession, project_id: int) -> ProjectDetail:
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dự án với ID {project_id}"
        )
        
    tasks = await task_repo.get_by_project(db, project_id)
    dependencies = await dependency_repo.get_by_project(db, project_id)
    
    from sqlalchemy import select
    from app.models import Resource, ProjectCalendar
    res_stmt = select(Resource).where(Resource.project_id == project_id)
    res_result = await db.execute(res_stmt)
    resources = res_result.scalars().all()
    
    time_stmt = select(ProjectCalendar).where(ProjectCalendar.project_id == project_id)
    time_result = await db.execute(time_stmt)
    time_constraint = time_result.scalars().first()
    
    return ProjectDetail(
        id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        project_type=project.project_type,
        status=project.status,
        target_deadline=project.target_deadline,
        penalty_per_day=project.penalty_per_day,
        bonus_per_day=project.bonus_per_day,
        base_cost=project.base_cost,
        total_cost=project.total_cost,
        num_tasks=len(tasks),
        num_edges=len(dependencies),
        network_density=0.0,
        metadata_json=project.metadata_json,
        created_at=project.created_at,
        updated_at=project.updated_at,
        tasks=tasks,
        constraint_logic=dependencies,
        constraint_resources=list(resources),
        constraint_time=time_constraint
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

async def create_project(db: AsyncSession, project_in: ProjectCreate) -> ProjectSummary:
    """
    Khởi tạo một dự án mới.
    """
    new_p = await project_repo.create(db, obj_in=project_in)
    return await get_project_summary(db, new_p.id)


# ==============================================================================
# MUTATIONS (UPDATES & DELETES)
# ==============================================================================

async def update_project(db: AsyncSession, project_id: int, project_in: ProjectUpdate) -> ProjectSummary:
    """
    Cập nhật thông tin dự án.
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")
    updated_p = await project_repo.update(db, db_obj=project, obj_in=project_in)
    return await get_project_summary(db, updated_p.id)


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
