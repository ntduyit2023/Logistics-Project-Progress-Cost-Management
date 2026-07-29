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


async def get_project_tasks(db: AsyncSession, project_id: int) -> List[Task]:
    """
    Lấy danh sách tất cả các Tasks của một dự án.
    """
    stmt = select(Task).where(Task.project_id == project_id).order_by(Task.id.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_task_by_id(db: AsyncSession, project_id: int, task_id_str: str) -> Task:
    """
    Lấy thông tin chi tiết của 1 Task theo task_id.
    """
    stmt = select(Task).where(Task.project_id == project_id, Task.task_id == task_id_str)
    result = await db.execute(stmt)
    task_obj = result.scalars().first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task không tồn tại.")
    return task_obj


async def create_task(db: AsyncSession, project_id: int, task_in: TaskCreate) -> Task:
    """
    Tạo mới một công việc (Task) và gắn vào Dự án.
    """
    stmt = select(AppProject).where(AppProject.id == project_id)
    result = await db.execute(stmt)
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại.")

    task_dict = task_in.model_dump(exclude_unset=True)
    task_dict["project_id"] = project_id
    if "task_id" not in task_dict or not task_dict["task_id"]:
        task_dict["task_id"] = f"{project.project_code}_{task_dict.get('task_name', '1')}"

    # Tách 38 cột chi phí chuẩn vào cost_features JSONB
    cost_cols = [
        'labor', 'material', 'equipment', 'energy', 'testing_inspection', 'project_management',
        'facility', 'utilities', 'communication', 'training', 'quality_management', 'overtime',
        'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay',
        'expediting', 'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance',
        'contingency_reserve', 'management_reserve', 'transportation', 'ordering', 'packaging',
        'reverse_logistics', 'customs', 'supplier_coordination', 'opportunity_cost', 'capital_cost',
        'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
    ]
    
    cost_features = task_dict.get("cost_features", {}) or {}
    total_cost = 0.0
    for col in cost_cols:
        if col in task_dict:
            val = float(task_dict.pop(col, 0.0) or 0.0)
            cost_features[col] = val
            total_cost += val

    task_dict["cost_features"] = cost_features
    if total_cost > 0:
        task_dict["total_cost"] = total_cost

    new_task = Task(**task_dict)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task


async def update_task(db: AsyncSession, project_id: int, task_id_str: str, task_in: TaskUpdate) -> Task:
    """
    Cập nhật thông tin của một công việc.
    """
    stmt = select(Task).where(Task.project_id == project_id, Task.task_id == task_id_str)
    result = await db.execute(stmt)
    task_obj = result.scalars().first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task không tồn tại.")

    update_dict = task_in.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(task_obj, k, v)

    await db.commit()
    await db.refresh(task_obj)
    return task_obj


async def delete_task(db: AsyncSession, project_id: int, task_id_str: str) -> Dict[str, str]:
    """
    Xóa một công việc khỏi Dự án.
    """
    stmt = delete(Task).where(Task.project_id == project_id, Task.task_id == task_id_str)
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task không tồn tại.")
    return {"message": "Đã xóa công việc thành công."}


async def get_task_resources(db: AsyncSession, project_id: int, task_id_str: str) -> List[Dict[str, Any]]:
    """
    Lấy danh sách phân bổ tài nguyên cho một Task.
    """
    stmt = select(TaskResource, Resource).join(
        Resource, (TaskResource.resource_id == Resource.resource_id) & (TaskResource.project_id == Resource.project_id)
    ).where(TaskResource.project_id == project_id, TaskResource.task_id == task_id_str)
    
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


async def assign_resource(db: AsyncSession, project_id: int, task_id_str: str, resource_in: TaskResourceCreate) -> TaskResource:
    """
    Phân bổ tài nguyên cho Task.
    """
    new_tr = TaskResource(
        project_id=project_id,
        task_id=task_id_str,
        resource_id=resource_in.resource_id,
        request_quantity=resource_in.request_quantity
    )
    db.add(new_tr)
    await db.commit()
    await db.refresh(new_tr)
    return new_tr


async def remove_task_resource(db: AsyncSession, project_id: int, task_id_str: str, resource_tr_id: int) -> Dict[str, str]:
    """
    Xóa phân bổ tài nguyên.
    """
    stmt = delete(TaskResource).where(
        TaskResource.project_id == project_id,
        TaskResource.task_id == task_id_str,
        TaskResource.id == resource_tr_id
    )
    await db.execute(stmt)
    await db.commit()
    return {"message": "Xóa phân bổ tài nguyên thành công."}
