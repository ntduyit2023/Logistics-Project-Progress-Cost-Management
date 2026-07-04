"""
GLPO Backend - Constraint Service Logic
Chứa các logic nghiệp vụ liên quan đến Ràng buộc (Constraints) như Thời gian, Tài nguyên, Logic.
"""
from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.repositories.project import project_repo
from app.repositories.constraints import resource_repo
from app.schemas import (
    ConstraintTimeBase, ConstraintTimeResponse,
    ConstraintResourceBase, ConstraintResourceResponse,
    ConstraintLogicBase, ConstraintLogicResponse
)
from app.models import ProjectConstraintTime, ProjectConstraintResource, ProjectConstraintLogic


# ==============================================================================
# TIME CONSTRAINTS
# ==============================================================================

async def create_constraint_time(db: AsyncSession, project_id: int, time_in: ConstraintTimeBase) -> ProjectConstraintTime:
    """
    Tạo lịch làm việc (Time Constraint) cho dự án.
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")
        
    time_dict = time_in.model_dump()
    time_dict["project_id"] = project_id
    
    new_time = ProjectConstraintTime(**time_dict)
    db.add(new_time)
    await db.commit()
    await db.refresh(new_time)
    return new_time


async def update_constraint_time(db: AsyncSession, project_id: int, time_in: ConstraintTimeBase) -> ConstraintTimeResponse:
    """
    Cập nhật lịch làm việc (Time Constraint).
    """
    stmt = select(ProjectConstraintTime).where(ProjectConstraintTime.project_id == project_id)
    result = await db.execute(stmt)
    time_cfg = result.scalars().first()
    
    if not time_cfg:
        raise HTTPException(status_code=404, detail="Lịch làm việc không tồn tại.")
        
    for k, v in time_in.model_dump().items():
        setattr(time_cfg, k, v)
        
    await db.commit()
    await db.refresh(time_cfg)
    return ConstraintTimeResponse.model_validate(time_cfg)


async def delete_constraint_time(db: AsyncSession, project_id: int) -> Dict[str, str]:
    """
    Xóa cấu hình thời gian.
    """
    stmt = delete(ProjectConstraintTime).where(ProjectConstraintTime.project_id == project_id)
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy ràng buộc thời gian.")
    return {"message": "Đã xóa lịch làm việc thành công."}


# ==============================================================================
# RESOURCE CONSTRAINTS
# ==============================================================================

async def create_constraint_resource(db: AsyncSession, project_id: int, resource_in: ConstraintResourceBase) -> ProjectConstraintResource:
    """
    Định nghĩa một loại tài nguyên mới.
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")
        
    res_dict = resource_in.model_dump()
    res_dict["project_id"] = project_id
    
    new_res = ProjectConstraintResource(**res_dict)
    db.add(new_res)
    await db.commit()
    await db.refresh(new_res)
    return new_res


async def update_constraint_resource(db: AsyncSession, project_id: int, resource_id: int, resource_in: ConstraintResourceBase) -> ConstraintResourceResponse:
    """
    Cập nhật một tài nguyên.
    """
    stmt = select(ProjectConstraintResource).where(
        ProjectConstraintResource.project_id == project_id,
        ProjectConstraintResource.id == resource_id
    )
    result = await db.execute(stmt)
    resource = result.scalars().first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        
    for k, v in resource_in.model_dump().items():
        setattr(resource, k, v)
        
    await db.commit()
    await db.refresh(resource)
    return ConstraintResourceResponse.model_validate(resource)


async def delete_constraint_resource(db: AsyncSession, project_id: int, resource_id: int) -> Any:
    """
    Xóa tài nguyên dự án.
    """
    resource = await resource_repo.get_by_id(db, resource_id)
    if not resource or resource.project_id != project_id:
        raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại trong dự án này.")
    return await resource_repo.delete(db, id=resource_id)


# ==============================================================================
# LOGIC CONSTRAINTS
# ==============================================================================

async def create_constraint_logic(db: AsyncSession, project_id: int, logic_in: ConstraintLogicBase) -> ProjectConstraintLogic:
    """
    Định nghĩa liên kết logic giữa 2 Tasks.
    """
    logic_dict = logic_in.model_dump()
    logic_dict["project_id"] = project_id
    
    new_logic = ProjectConstraintLogic(**logic_dict)
    db.add(new_logic)
    
    try:
        await db.commit()
        await db.refresh(new_logic)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi khởi tạo liên kết: {str(e)}")
        
    return new_logic


async def update_constraint_logic(db: AsyncSession, project_id: int, logic_in: ConstraintLogicBase) -> ConstraintLogicResponse:
    """
    Cập nhật liên kết ràng buộc logic.
    """
    stmt = select(ProjectConstraintLogic).where(
        ProjectConstraintLogic.project_id == project_id,
        ProjectConstraintLogic.predecessor_id == logic_in.predecessor_id,
        ProjectConstraintLogic.successor_id == logic_in.successor_id
    )
    result = await db.execute(stmt)
    logic = result.scalars().first()
    
    if not logic:
        raise HTTPException(status_code=404, detail="Ràng buộc logic không tồn tại.")
        
    for k, v in logic_in.model_dump().items():
        setattr(logic, k, v)
        
    await db.commit()
    await db.refresh(logic)
    return ConstraintLogicResponse.model_validate(logic)


async def delete_constraint_logic(db: AsyncSession, project_id: int, predecessor_id: str, successor_id: str) -> Dict[str, str]:
    """
    Xóa liên kết logic (Edge).
    """
    stmt = delete(ProjectConstraintLogic).where(
        ProjectConstraintLogic.project_id == project_id,
        ProjectConstraintLogic.predecessor_id == predecessor_id,
        ProjectConstraintLogic.successor_id == successor_id
    )
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy liên kết logic này.")
    return {"message": "Đã xóa liên kết thành công."}
