"""
GLPO Backend - Task Service Logic
Chứa các logic nghiệp vụ liên quan đến Công việc (Tasks) và Phân bổ Tài nguyên.
"""
from typing import Any, List, Dict, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models import Task, TaskResource, Resource, AppProject
from app.schemas import TaskCreate, TaskUpdate, TaskResourceCreate


from app.services.project_service import get_project_by_identifier

async def get_project_tasks(db: AsyncSession, project_id_or_code: Any) -> List[Dict[str, Any]]:
    """
    Lấy danh sách tất cả các Tasks của một dự án (chấp nhận ID số hoặc mã C2011-07).
    """
    project = await get_project_by_identifier(db, project_id_or_code)
    stmt = select(Task).where(Task.project_id == project.id).order_by(Task.id.asc())
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())
    
    from app.schemas.task import TaskResponse
    res = []
    for t in tasks:
        td = TaskResponse.model_validate(t).model_dump()
        td["project_code"] = project.project_code
        res.append(td)
    return res


async def get_task_by_id(db: AsyncSession, project_id_or_code: Any, task_id_str: str) -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết của 1 Task theo task_id.
    """
    project = await get_project_by_identifier(db, project_id_or_code)
    stmt = select(Task).where(Task.project_id == project.id, Task.task_id == task_id_str)
    result = await db.execute(stmt)
    task_obj = result.scalars().first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task không tồn tại.")
        
    from app.schemas.task import TaskResponse
    td = TaskResponse.model_validate(task_obj).model_dump()
    td["project_code"] = project.project_code
    return td


async def create_task(db: AsyncSession, project_id_or_code: Any, task_in: TaskCreate) -> Dict[str, Any]:
    """
    Tạo mới một công việc (Task) và gắn vào Dự án.
    """
    project = await get_project_by_identifier(db, project_id_or_code)

    task_dict = task_in.model_dump(exclude_unset=True)
    task_dict["project_id"] = project.id
    if "task_id" not in task_dict or not task_dict.get("task_id"):
        import uuid
        task_dict["task_id"] = f"{project.project_code}_NEW_{uuid.uuid4().hex[:6]}"

    task_dict.pop("total_cost", None)
    new_task = Task(**task_dict)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    from app.schemas.task import TaskResponse
    td = TaskResponse.model_validate(new_task).model_dump()
    return td


async def update_task(db: AsyncSession, project_id_or_code: Any, task_id_str: str, task_in: TaskUpdate) -> Dict[str, Any]:
    """
    Cập nhật thông tin của một công việc.
    """
    project = await get_project_by_identifier(db, project_id_or_code)
    stmt = select(Task).where(Task.project_id == project.id, Task.task_id == task_id_str)
    result = await db.execute(stmt)
    task_obj = result.scalars().first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task không tồn tại.")

    update_data = task_in.model_dump(exclude_unset=True)
    update_data.pop("total_cost", None)
    for k, v in update_data.items():
        setattr(task_obj, k, v)

    await db.commit()
    await db.refresh(task_obj)
    from app.schemas.task import TaskResponse
    return TaskResponse.model_validate(task_obj).model_dump()


async def delete_task(db: AsyncSession, project_id_or_code: Any, task_id_str: str) -> Dict[str, str]:
    """
    Xóa một công việc khỏi Dự án.
    """
    project = await get_project_by_identifier(db, project_id_or_code)
    stmt = delete(Task).where(Task.project_id == project.id, Task.task_id == task_id_str)
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task không tồn tại.")
    return {"message": "Đã xóa công việc thành công."}


async def get_task_resources(db: AsyncSession, project_id_or_code: Any, task_id_str: str) -> List[Dict[str, Any]]:
    """
    Lấy danh sách phân bổ tài nguyên cho một Task.
    """
    project = await get_project_by_identifier(db, project_id_or_code)
    stmt = select(TaskResource, Resource).join(
        Resource, (TaskResource.resource_id == Resource.resource_id) & (TaskResource.project_id == Resource.project_id)
    ).where(TaskResource.project_id == project.id, TaskResource.task_id == task_id_str)
    
    result = await db.execute(stmt)
    items = []
    for tr, r in result.all():
        items.append({
            "id": tr.id,
            "project_id": tr.project_id,
            "task_id": tr.task_id,
            "resource_id": tr.resource_id,
            "resource_name": r.name,
            "resource_type": r.type,
            "request_quantity": tr.request_quantity,
            "unit_cost": r.unit_cost
        })
    return items


async def assign_resource(db: AsyncSession, project_id_or_code: Any, task_id_str: str, resource_in: TaskResourceCreate) -> TaskResource:
    """
    Phân bổ tài nguyên cho Task.
    """
    project = await get_project_by_identifier(db, project_id_or_code)
    new_tr = TaskResource(
        project_id=project.id,
        task_id=task_id_str,
        resource_id=resource_in.resource_id,
        request_quantity=resource_in.request_quantity
    )
    db.add(new_tr)
    await db.commit()
    await db.refresh(new_tr)
    return new_tr


async def remove_task_resource(db: AsyncSession, project_id_or_code: Any, task_id_str: str, resource_tr_id: int) -> Dict[str, str]:
    """
    Xóa phân bổ tài nguyên.
    """
    project = await get_project_by_identifier(db, project_id_or_code)
    stmt = delete(TaskResource).where(
        TaskResource.project_id == project.id,
        TaskResource.task_id == task_id_str,
        TaskResource.id == resource_tr_id
    )
    await db.execute(stmt)
    await db.commit()
    return {"message": "Xóa phân bổ tài nguyên thành công."}
