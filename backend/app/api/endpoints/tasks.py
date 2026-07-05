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


# --- TASK RESOURCES ---

from app.schemas.task import TaskResourceCreate, TaskResourceResponse
from typing import List

@router.get("/{project_id}/tasks/{task_id}/resources", response_model=APIResponse[List[TaskResourceResponse]], summary="Lấy danh sách tài nguyên của Task")
async def get_task_resources_api(
    project_id: int = Path(...),
    task_id: str = Path(...),
    db: AsyncSession = Depends(get_db)
):
    data = await task_service.get_task_resources(db, project_id, task_id)
    return APIResponse(success=True, message="Lấy danh sách tài nguyên thành công.", data=data)

@router.post("/{project_id}/tasks/{task_id}/resources", response_model=APIResponse[TaskResourceResponse], summary="Phân bổ tài nguyên cho Task")
async def assign_task_resource_api(
    project_id: int = Path(...),
    task_id: str = Path(...),
    resource_in: TaskResourceCreate = ...,
    db: AsyncSession = Depends(get_db)
):
    data = await task_service.assign_resource(db, project_id, task_id, resource_in)
    
    # We need to return it in the schema format, so fetch again to get name/type joined
    all_res = await task_service.get_task_resources(db, project_id, task_id)
    assigned = next((r for r in all_res if r["resource_id"] == resource_in.resource_id), None)
    
    return APIResponse(success=True, message="Phân bổ tài nguyên thành công.", data=assigned)

@router.delete("/{project_id}/tasks/{task_id}/resources/{resource_id}", response_model=APIResponse, summary="Xóa phân bổ tài nguyên")
async def delete_task_resource_api(
    project_id: int = Path(...),
    task_id: str = Path(...),
    resource_id: int = Path(...),
    db: AsyncSession = Depends(get_db)
):
    await task_service.remove_task_resource(db, project_id, task_id, resource_id)
    return APIResponse(success=True, message="Xóa phân bổ tài nguyên thành công.")
