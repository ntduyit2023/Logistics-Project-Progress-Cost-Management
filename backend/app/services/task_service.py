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
