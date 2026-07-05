"""
GLPO Backend - Task Service Logic
Chứa các logic nghiệp vụ liên quan đến Công việc (Tasks).
"""
from typing import Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.task import task_repo
from app.repositories.project import project_repo
from app.schemas import TaskCreate, TaskUpdate
from app.models import Task


async def create_task(db: AsyncSession, project_id: int, task_in: TaskCreate) -> Task:
    """
    Tạo mới một Task (Wide Table) và gắn vào Project.

    Args:
        db (AsyncSession): Phiên DB.
        project_id (int): ID dự án.
        task_in (TaskCreate): Dữ liệu tạo Task.

    Returns:
        Task: Công việc vừa tạo.

    Raises:
        HTTPException: Nếu Dự án không tồn tại.
    """
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")
        
    task_dict = task_in.model_dump()
    task_dict["project_id"] = project_id
    
    new_task = Task(**task_dict)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task


async def update_task(db: AsyncSession, project_id: int, task_id: str, task_in: TaskUpdate) -> Any:
    """
    Cập nhật một công việc.

    Args:
        db (AsyncSession): Phiên DB.
        project_id (int): ID dự án.
        task_id (str): ID công việc.
        task_in (TaskUpdate): Dữ liệu cập nhật.

    Returns:
        Any: Task sau cập nhật.

    Raises:
        HTTPException: Nếu không tìm thấy.
    """
    task = await task_repo.get_by_id(db, task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Công việc không tồn tại trong dự án này.")
    return await task_repo.update(db, db_obj=task, obj_in=task_in)


async def delete_task(db: AsyncSession, project_id: int, task_id: str):
    """
    Xóa một công việc (Cascade sẽ lo các bảng liên quan).

    Args:
        db (AsyncSession): Database session.
        project_id (int): ID dự án.
        task_id (str): ID công việc.

    Raises:
        HTTPException: Nếu task không tồn tại.
    """
    stmt = select(Task).where(Task.project_id == project_id, Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task không tồn tại.")
        
    await db.delete(task)
    await db.commit()


# --- TASK RESOURCE MANAGEMENT ---

from app.models import TaskResource, ProjectConstraintResource

async def assign_resource(db: AsyncSession, project_id: int, task_id: str, resource_in: Any) -> TaskResource:
    # Verify task exists and belongs to project
    stmt_task = select(Task).where(Task.project_id == project_id, Task.id == task_id)
    result_task = await db.execute(stmt_task)
    if not result_task.scalars().first():
        raise HTTPException(status_code=404, detail="Task không tồn tại trong dự án này.")
        
    # Verify resource exists and belongs to project
    stmt_res = select(ProjectConstraintResource).where(
        ProjectConstraintResource.project_id == project_id, 
        ProjectConstraintResource.id == resource_in.resource_id
    )
    result_res = await db.execute(stmt_res)
    if not result_res.scalars().first():
        raise HTTPException(status_code=404, detail="Resource không tồn tại trong dự án này.")

    # Upsert logic (if already assigned, update quantity)
    stmt_check = select(TaskResource).where(TaskResource.task_id == task_id, TaskResource.resource_id == resource_in.resource_id)
    result_check = await db.execute(stmt_check)
    existing = result_check.scalars().first()
    
    if existing:
        for k, v in resource_in.model_dump(exclude_unset=True).items():
            setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        new_assignment = TaskResource(
            task_id=task_id,
            **resource_in.model_dump()
        )
        db.add(new_assignment)
        await db.commit()
        await db.refresh(new_assignment)
        return new_assignment

async def get_task_resources(db: AsyncSession, project_id: int, task_id: str) -> list[Any]:
    stmt = select(
        TaskResource, 
        ProjectConstraintResource.resource_name, 
        ProjectConstraintResource.resource_type
    ).join(
        ProjectConstraintResource, 
        TaskResource.resource_id == ProjectConstraintResource.id
    ).where(
        TaskResource.task_id == task_id
    )
    result = await db.execute(stmt)
    
    # Map to schema shape
    resp = []
    for tr, r_name, r_type in result.all():
        data = {
            "task_id": tr.task_id,
            "resource_id": tr.resource_id,
            "request_quantity": tr.request_quantity,
            "allocated_quantity": tr.allocated_quantity,
            "labor_productivity": tr.labor_productivity,
            "equipment_utilization": tr.equipment_utilization,
            "resource_substitutability": tr.resource_substitutability,
            "resource_name": r_name,
            "resource_type": r_type
        }
        resp.append(data)
    return resp

async def remove_task_resource(db: AsyncSession, project_id: int, task_id: str, resource_id: int):
    stmt = select(TaskResource).where(TaskResource.task_id == task_id, TaskResource.resource_id == resource_id)
    result = await db.execute(stmt)
    tr = result.scalars().first()
    if not tr:
        raise HTTPException(status_code=404, detail="Assignment không tồn tại.")
    await db.delete(tr)
    await db.commit()

