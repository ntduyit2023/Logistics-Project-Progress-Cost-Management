"""
GLPO Backend - Constraint Service Logic
Chứa các logic nghiệp vụ liên quan đến Ràng buộc (ProjectCalendar, Resource, TaskLogic).
"""
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.repositories.project import project_repo
from app.schemas import (
    ConstraintTimeBase, ConstraintTimeResponse,
    ConstraintResourceBase, ConstraintResourceResponse,
    ConstraintLogicBase, ConstraintLogicResponse
)
from app.models import ProjectCalendar, Resource, TaskLogic, AppProject


# ==============================================================================
# TIME CONSTRAINTS (PROJECT CALENDARS)
# ==============================================================================

async def get_constraint_time(db: AsyncSession, project_id: int) -> Optional[ProjectCalendar]:
    """
    Lấy cấu hình Lịch làm việc (ProjectCalendar) của dự án.
    """
    stmt = select(ProjectCalendar).where(ProjectCalendar.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_constraint_time(db: AsyncSession, project_id: int, time_in: ConstraintTimeBase) -> ProjectCalendar:
    """
    Tạo lịch làm việc (ProjectCalendar) cho dự án.
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")
        
    time_dict = time_in.model_dump()
    time_dict["project_id"] = project_id
    
    new_time = ProjectCalendar(**time_dict)
    db.add(new_time)
    await db.commit()
    await db.refresh(new_time)
    return new_time


async def update_constraint_time(db: AsyncSession, project_id: int, time_in: ConstraintTimeBase) -> ConstraintTimeResponse:
    """
    Cập nhật lịch làm việc (ProjectCalendar).
    """
    stmt = select(ProjectCalendar).where(ProjectCalendar.project_id == project_id)
    result = await db.execute(stmt)
    time_cfg = result.scalars().first()
    
    if not time_cfg:
        time_dict = time_in.model_dump()
        time_dict["project_id"] = project_id
        time_cfg = ProjectCalendar(**time_dict)
        db.add(time_cfg)
    else:
        for k, v in time_in.model_dump().items():
            setattr(time_cfg, k, v)
        
    await db.commit()
    await db.refresh(time_cfg)
    return ConstraintTimeResponse.model_validate(time_cfg)


async def delete_constraint_time(db: AsyncSession, project_id: int) -> Dict[str, str]:
    """
    Xóa cấu hình thời gian.
    """
    stmt = delete(ProjectCalendar).where(ProjectCalendar.project_id == project_id)
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy ràng buộc thời gian.")
    return {"message": "Đã xóa lịch làm việc thành công."}


# ==============================================================================
# RESOURCE CONSTRAINTS (RESOURCES)
# ==============================================================================

async def get_constraint_resources(db: AsyncSession, project_id: int) -> List[Resource]:
    """
    Lấy danh sách tất cả các tài nguyên của dự án.
    """
    stmt = select(Resource).where(Resource.project_id == project_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_constraint_resource(db: AsyncSession, project_id: int, resource_in: ConstraintResourceBase) -> Resource:
    """
    Định nghĩa một loại tài nguyên mới.
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")
        
    res_dict = resource_in.model_dump()
    res_dict["project_id"] = project_id
    
    new_res = Resource(**res_dict)
    db.add(new_res)
    await db.commit()
    await db.refresh(new_res)
    return new_res


async def update_constraint_resource(db: AsyncSession, project_id: int, resource_id: int, resource_in: ConstraintResourceBase) -> ConstraintResourceResponse:
    """
    Cập nhật một tài nguyên.
    """
    stmt = select(Resource).where(
        Resource.project_id == project_id,
        Resource.id == resource_id
    )
    result = await db.execute(stmt)
    res_obj = result.scalars().first()
    
    if not res_obj:
        raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
        
    for k, v in resource_in.model_dump().items():
        setattr(res_obj, k, v)
        
    await db.commit()
    await db.refresh(res_obj)
    return ConstraintResourceResponse.model_validate(res_obj)


async def delete_constraint_resource(db: AsyncSession, project_id: int, resource_id: int) -> Dict[str, str]:
    """
    Xóa một tài nguyên.
    """
    stmt = delete(Resource).where(
        Resource.project_id == project_id,
        Resource.id == resource_id
    )
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Tài nguyên không tồn tại.")
    return {"message": "Xóa tài nguyên thành công."}


# ==============================================================================
# LOGIC CONSTRAINTS (TASK LOGIC EDGES)
# ==============================================================================

async def get_constraint_logics(db: AsyncSession, project_id: int) -> List[TaskLogic]:
    """
    Lấy tất cả các mối quan hệ phụ thuộc logic giữa các Tasks.
    """
    stmt = select(TaskLogic).where(TaskLogic.project_id == project_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_constraint_logic(db: AsyncSession, project_id: int, logic_in: ConstraintLogicBase) -> TaskLogic:
    """
    Tạo mối quan hệ phụ thuộc giữa 2 Tasks.
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")
        
    logic_dict = logic_in.model_dump()
    logic_dict["project_id"] = project_id
    
    new_logic = TaskLogic(**logic_dict)
    db.add(new_logic)
    await db.commit()
    await db.refresh(new_logic)
    return new_logic


async def update_constraint_logic(db: AsyncSession, project_id: int, logic_in: ConstraintLogicBase) -> TaskLogic:
    """
    Cập nhật mối quan hệ phụ thuộc giữa 2 Tasks.
    """
    stmt = select(TaskLogic).where(
        TaskLogic.project_id == project_id,
        TaskLogic.predecessor_id == logic_in.predecessor_id,
        TaskLogic.successor_id == logic_in.successor_id
    )
    result = await db.execute(stmt)
    logic_obj = result.scalars().first()
    
    if not logic_obj:
        return await create_constraint_logic(db, project_id, logic_in)
        
    for k, v in logic_in.model_dump().items():
        setattr(logic_obj, k, v)
        
    await db.commit()
    await db.refresh(logic_obj)
    return logic_obj


async def delete_constraint_logic(db: AsyncSession, project_id: int, predecessor_id: str, successor_id: str) -> Dict[str, str]:
    """
    Xóa phụ thuộc logic giữa predecessor_id và successor_id.
    """
    stmt = delete(TaskLogic).where(
        TaskLogic.project_id == project_id,
        TaskLogic.predecessor_id == predecessor_id,
        TaskLogic.successor_id == successor_id
    )
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Phụ thuộc logic không tồn tại.")
    return {"message": "Xóa phụ thuộc thành công."}
