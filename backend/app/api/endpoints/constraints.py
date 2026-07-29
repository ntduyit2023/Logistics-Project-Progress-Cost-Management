"""
GLPO Backend - Constraints API Endpoints
Chứa các API xử lý Ràng buộc (Logic, Resource, Time) của một Dự án.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import (
    APIResponse, ConstraintTimeBase, ConstraintTimeResponse,
    ConstraintResourceBase, ConstraintResourceResponse, ConstraintLogicBase, ConstraintLogicResponse
)
from app.services import constraint_service

router = APIRouter()

# ==============================================================================
# TIME CONSTRAINTS (AGENDA / CALENDAR)
# ==============================================================================

@router.get("/{project_id}/constraints/time", response_model=APIResponse[Optional[ConstraintTimeResponse]], summary="Lấy Lịch làm việc")
async def get_time_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
):
    data = await constraint_service.get_constraint_time(db, project_id)
    return APIResponse(success=True, message="Lấy Lịch làm việc thành công.", data=data)


@router.post("/{project_id}/constraints/time", response_model=APIResponse[ConstraintTimeResponse], summary="Định nghĩa Lịch làm việc")
async def create_time_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    time_in: ConstraintTimeBase = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ConstraintTimeResponse]:
    data = await constraint_service.create_constraint_time(db, project_id, time_in)
    return APIResponse(success=True, message="Cập nhật Lịch làm việc thành công.", data=data)


@router.put("/{project_id}/constraints/time", response_model=APIResponse[ConstraintTimeResponse], summary="Cập nhật Lịch làm việc")
async def update_time_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    time_in: ConstraintTimeBase = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ConstraintTimeResponse]:
    data = await constraint_service.update_constraint_time(db, project_id, time_in)
    return APIResponse(success=True, message="Cập nhật Lịch làm việc thành công.", data=data)


@router.delete("/{project_id}/constraints/time", response_model=APIResponse, summary="Xóa Lịch làm việc")
async def delete_time_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse:
    await constraint_service.delete_constraint_time(db, project_id)
    return APIResponse(success=True, message="Đã xóa lịch làm việc thành công.")


# ==============================================================================
# RESOURCE CONSTRAINTS (RESOURCES)
# ==============================================================================

@router.get("/{project_id}/constraints/resources", response_model=APIResponse[List[ConstraintResourceResponse]], summary="Danh sách Tài nguyên")
async def get_resource_constraints_api(
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
):
    data = await constraint_service.get_constraint_resources(db, project_id)
    return APIResponse(success=True, message="Lấy danh sách tài nguyên thành công.", data=data)


@router.post("/{project_id}/constraints/resources", response_model=APIResponse[ConstraintResourceResponse], summary="Thêm Tài nguyên mới")
async def create_resource_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    resource_in: ConstraintResourceBase = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ConstraintResourceResponse]:
    data = await constraint_service.create_constraint_resource(db, project_id, resource_in)
    return APIResponse(success=True, message="Thêm tài nguyên thành công.", data=data)


@router.put("/{project_id}/constraints/resources/{resource_id}", response_model=APIResponse[ConstraintResourceResponse], summary="Cập nhật Tài nguyên")
async def update_resource_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    resource_id: int = Path(..., description="ID tài nguyên"),
    resource_in: ConstraintResourceBase = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ConstraintResourceResponse]:
    data = await constraint_service.update_constraint_resource(db, project_id, resource_id, resource_in)
    return APIResponse(success=True, message="Cập nhật tài nguyên thành công.", data=data)


@router.delete("/{project_id}/constraints/resources/{resource_id}", response_model=APIResponse, summary="Xóa Tài nguyên")
async def delete_resource_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    resource_id: int = Path(..., description="ID tài nguyên"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse:
    await constraint_service.delete_constraint_resource(db, project_id, resource_id)
    return APIResponse(success=True, message="Đã xóa tài nguyên thành công.")


# ==============================================================================
# LOGIC CONSTRAINTS (EDGES)
# ==============================================================================

@router.get("/{project_id}/constraints/logic", response_model=APIResponse[List[ConstraintLogicResponse]], summary="Danh sách Phụ thuộc (Edges)")
async def get_logic_constraints_api(
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
):
    data = await constraint_service.get_constraint_logics(db, project_id)
    return APIResponse(success=True, message="Lấy danh sách phụ thuộc logic thành công.", data=data)


@router.post("/{project_id}/constraints/logic", response_model=APIResponse[ConstraintLogicResponse], summary="Thêm Liên kết (Edge)")
async def create_logic_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    logic_in: ConstraintLogicBase = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ConstraintLogicResponse]:
    data = await constraint_service.create_constraint_logic(db, project_id, logic_in)
    return APIResponse(success=True, message="Thêm liên kết (FS, SS...) thành công.", data=data)


@router.put("/{project_id}/constraints/logic", response_model=APIResponse[ConstraintLogicResponse], summary="Cập nhật Liên kết (Edge)")
async def update_logic_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    logic_in: ConstraintLogicBase = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ConstraintLogicResponse]:
    data = await constraint_service.update_constraint_logic(db, project_id, logic_in)
    return APIResponse(success=True, message="Cập nhật liên kết thành công.", data=data)


@router.delete("/{project_id}/constraints/logic/{predecessor_id}/{successor_id}", response_model=APIResponse, summary="Xóa Liên kết (Edge)")
async def delete_logic_constraint_api(
    project_id: int = Path(..., description="ID dự án"),
    predecessor_id: str = Path(..., description="ID Task đứng trước"),
    successor_id: str = Path(..., description="ID Task đứng sau"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse:
    await constraint_service.delete_constraint_logic(db, project_id, predecessor_id, successor_id)
    return APIResponse(success=True, message="Đã xóa liên kết logic thành công.")
