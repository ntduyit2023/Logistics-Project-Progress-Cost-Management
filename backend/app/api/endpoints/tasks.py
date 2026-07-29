"""
GLPO Backend - Tasks API Endpoints
Chứa các API xử lý Công việc (Tasks) của một Dự án.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import APIResponse, TaskCreate, TaskUpdate, TaskResponse, TaskResourceCreate, TaskResourceResponse
from app.services import task_service

router = APIRouter()

# ==============================================================================
# TASK CRUD (GET, POST, PUT, DELETE)
# ==============================================================================

@router.get("/{project_id}/tasks", response_model=APIResponse[List[TaskResponse]], summary="Danh sách Tasks của Dự án")
async def get_project_tasks_api(
    project_id: str = Path(..., description="ID số (ví dụ 1) hoặc Mã dự án (ví dụ C2011-07)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách tất cả các công việc (Tasks) thuộc về Dự án.
    """
    data = await task_service.get_project_tasks(db, project_id)
    return APIResponse(success=True, message="Lấy danh sách công việc thành công.", data=data)


@router.get("/{project_id}/tasks/{task_id}", response_model=APIResponse[TaskResponse], summary="Chi tiết một Task")
async def get_task_detail_api(
    project_id: str = Path(..., description="ID số (ví dụ 1) hoặc Mã dự án (ví dụ C2011-07)"),
    task_id: str = Path(..., description="Mã task (ví dụ C2011-07_1)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Xem thông tin chi tiết của 1 Task.
    """
    data = await task_service.get_task_by_id(db, project_id, task_id)
    return APIResponse(success=True, message="Lấy chi tiết công việc thành công.", data=data)


@router.post("/{project_id}/tasks", response_model=APIResponse[TaskResponse], summary="Thêm Task mới")
async def create_task_api(
    project_id: str = Path(..., description="ID số (ví dụ 1) hoặc Mã dự án (ví dụ C2011-07)"),
    task_in: TaskCreate = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[TaskResponse]:
    """
    Tạo mới một công việc (Task) và gắn vào Dự án.
    """
    data = await task_service.create_task(db, project_id, task_in)
    return APIResponse(success=True, message="Tạo công việc thành công.", data=data)


@router.put("/{project_id}/tasks/{task_id}", response_model=APIResponse[TaskResponse], summary="Cập nhật Task")
async def update_task_api(
    project_id: str = Path(..., description="ID số (ví dụ 1) hoặc Mã dự án (ví dụ C2011-07)"),
    task_id: str = Path(..., description="Mã task (ví dụ C2011-07_1)"),
    task_in: TaskUpdate = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[TaskResponse]:
    """
    Cập nhật thông tin của một công việc.
    """
    data = await task_service.update_task(db, project_id, task_id, task_in)
    return APIResponse(success=True, message="Cập nhật công việc thành công.", data=data)


@router.delete("/{project_id}/tasks/{task_id}", response_model=APIResponse, summary="Xóa Task")
async def delete_task_api(
    project_id: str = Path(..., description="Mã/ID dự án (ví dụ C2011-07)"),
    task_id: str = Path(..., description="Mã task cần xóa"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse:
    """
    Xóa một công việc khỏi Dự án.
    """
    await task_service.delete_task(db, project_id, task_id)
    return APIResponse(success=True, message="Đã xóa công việc thành công.")


# ==============================================================================
# TASK RESOURCES ASSIGNMENT
# ==============================================================================

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
    all_res = await task_service.get_task_resources(db, project_id, task_id)
    assigned = next((r for r in all_res if r["resource_id"] == resource_in.resource_id), None)
    return APIResponse(success=True, message="Phân bổ tài nguyên thành công.", data=assigned)


@router.delete("/{project_id}/tasks/{task_id}/resources/{resource_tr_id}", response_model=APIResponse, summary="Xóa phân bổ tài nguyên")
async def delete_task_resource_api(
    project_id: int = Path(...),
    task_id: str = Path(...),
    resource_tr_id: int = Path(..., description="ID bản ghi phân bổ tài nguyên"),
    db: AsyncSession = Depends(get_db)
):
    await task_service.remove_task_resource(db, project_id, task_id, resource_tr_id)
    return APIResponse(success=True, message="Xóa phân bổ tài nguyên thành công.")
