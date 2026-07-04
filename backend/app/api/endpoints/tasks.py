"""
GLPO Backend - Tasks API Endpoints
Chứa các API xử lý Công việc (Tasks) của một Dự án.
"""
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import APIResponse, TaskCreate, TaskUpdate, TaskResponse
from app.services import task_service

router = APIRouter()

@router.post("/{project_id}/tasks", response_model=APIResponse[TaskResponse], summary="Thêm Task mới")
async def create_task_api(
    project_id: int = Path(..., description="ID dự án"),
    task_in: TaskCreate = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[TaskResponse]:
    """
    Tạo mới một công việc (Task) và gắn vào Dự án.

    Args:
        project_id (int): ID dự án.
        task_in (TaskCreate): Dữ liệu khởi tạo Task (Wide Table schema).
        db (AsyncSession): Phiên DB (Dependency Injection).

    Returns:
        APIResponse[TaskResponse]: Phản hồi chứa dữ liệu Task vừa được tạo.

    Raises:
        HTTPException: Nếu dự án không tồn tại hoặc lỗi khởi tạo.
    """
    data = await task_service.create_task(db, project_id, task_in)
    return APIResponse(success=True, message="Tạo công việc thành công.", data=data)


@router.put("/{project_id}/tasks/{task_id}", response_model=APIResponse[TaskResponse], summary="Cập nhật Task")
async def update_task_api(
    project_id: int = Path(..., description="ID dự án"),
    task_id: str = Path(..., description="ID của task"),
    task_in: TaskUpdate = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[TaskResponse]:
    """
    Cập nhật thông tin của một công việc.

    Args:
        project_id (int): ID dự án.
        task_id (str): ID công việc cần cập nhật.
        task_in (TaskUpdate): Dữ liệu cập nhật.
        db (AsyncSession): Phiên DB (Dependency Injection).

    Returns:
        APIResponse[TaskResponse]: Phản hồi chứa dữ liệu Task sau cập nhật.

    Raises:
        HTTPException: Nếu Task không tồn tại.
    """
    data = await task_service.update_task(db, project_id, task_id, task_in)
    return APIResponse(success=True, message="Cập nhật công việc thành công.", data=data)


@router.delete("/{project_id}/tasks/{task_id}", response_model=APIResponse, summary="Xóa Task")
async def delete_task_api(
    project_id: int = Path(..., description="ID dự án"),
    task_id: str = Path(..., description="ID của task"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse:
    """
    Xóa một công việc khỏi Dự án.

    Args:
        project_id (int): ID dự án.
        task_id (str): ID công việc cần xóa.
        db (AsyncSession): Phiên DB (Dependency Injection).

    Returns:
        APIResponse: Thông báo thành công.

    Raises:
        HTTPException: Nếu Task không tồn tại.
    """
    await task_service.delete_task(db, project_id, task_id)
    return APIResponse(success=True, message="Đã xóa công việc thành công.")
