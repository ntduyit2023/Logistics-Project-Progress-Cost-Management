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
from app.models import Task, TaskResource, ProjectConstraintResource

async def _recalculate_task_costs(db: AsyncSession, project: Any, task_id: str):
    task = await task_repo.get_by_id(db, task_id)
    if not task: return

    # Query Project Time Constraint (Agenda)
    stmt_time = select(ProjectConstraintTime).where(ProjectConstraintTime.project_id == project.id)
    res_time = await db.execute(stmt_time)
    time_constraint = res_time.scalars().first()

    hours_per_day = 8.0
    days_per_week = 5.0
    ot_multiplier = 1.4

    if time_constraint:
        if time_constraint.overtime_multiplier:
            ot_multiplier = float(time_constraint.overtime_multiplier)
        if time_constraint.weekly_schedule:
            sched = time_constraint.weekly_schedule
            if isinstance(sched, dict):
                hours_per_day = float(sched.get('hours_per_day', 8.0) or 8.0)
                days_per_week = float(sched.get('days_per_week', 5.0) or 5.0)

    # Calculate task duration in working hours based on Agenda
    d_m = float(task.duration_months or 0.0)
    d_w = float(task.duration_weeks or 0.0)
    d_d = float(task.duration_days or 0.0)
    d_h = float(task.duration_hours or 0.0)

    cal_type = str(task.calendar_type or 'Standard').lower()
    if '24/7' in cal_type or 'continuous' in cal_type:
        total_h = d_m * 30.0 * 24.0 + d_w * 7.0 * 24.0 + d_d * 24.0 + d_h
    else:
        if d_d > 0 and d_h == 0:
            total_h = d_m * 4.0 * days_per_week * hours_per_day + d_w * days_per_week * hours_per_day + d_d * hours_per_day
        elif d_h > 0 and d_d == 0 and d_w == 0 and d_m == 0:
            total_h = d_h
        else:
            total_h = d_m * 4.0 * days_per_week * hours_per_day + d_w * days_per_week * hours_per_day + (d_d * hours_per_day if d_d > 0 else hours_per_day)

    task.duration_hours = max(1.0, total_h)

    stmt = select(TaskResource, ProjectConstraintResource).join(
        ProjectConstraintResource, TaskResource.resource_id == ProjectConstraintResource.id
    ).where(TaskResource.task_id == task_id)
    result = await db.execute(stmt)
    resources = result.all()

    g1_labor = 0.0
    g1_ot = 0.0
    g1_fuel_res = 0.0
    g1_mat_res = 0.0
    g1_sub_res = 0.0
    task_work_hours = float(task.duration_hours or hours_per_day)

    for tr, pcr in resources:
        qty = float(tr.request_quantity or 0.0)
        h_rate = float(pcr.cost_per_unit or 0.0)
        ot_rate = h_rate * ot_multiplier  # 1.4 multiplier
        
        r_type = str(pcr.resource_type or 'Human').lower()
        r_name = str(pcr.resource_name or '').lower()

        if 'equip' in r_type or 'fuel' in r_type or 'machine' in r_name or 'crane' in r_name or 'truck' in r_name:
            g1_fuel_res += qty * task_work_hours * h_rate
        elif 'mat' in r_type or 'consumable' in r_type or 'supply' in r_name:
            g1_mat_res += qty * h_rate
        elif 'subcontract' in r_type or 'outsourc' in r_type or 'vendor' in r_type:
            g1_sub_res += qty * h_rate
        else:
            # Human / Labor / Personnel / Multi-resource Team
            g1_labor += qty * task_work_hours * h_rate
            g1_ot += qty * float(getattr(task, "overtime_hours", 0.0) or 0.0) * ot_rate

    # If resources assigned, set task costs from accumulated resources
    if len(resources) > 0:
        task.internal_labor_cost = g1_labor
        task.overtime_cost = g1_ot
        if g1_fuel_res > 0: task.equipment_fuel_cost = g1_fuel_res
        if g1_mat_res > 0: task.material_cost = g1_mat_res
        if g1_sub_res > 0: task.outsourcing_cost = g1_sub_res
    else:
        g1_labor = float(task.internal_labor_cost or 0.0)
        g1_ot = float(task.overtime_cost or 0.0)

    project_type = project.type

    g1_fuel = float(task.equipment_fuel_cost or 0.0)
    g1_qa_qc = float(task.qa_qc_cost or 0.0)
    g1_material = float(task.material_cost or 0.0)
    g1_subcontract = float(task.outsourcing_cost or 0.0)

    g2_training = float(task.training_cost or 0.0)
    g2_space = float(task.facility_rent or 0.0)
    g2_comm = float(task.communication_cost or 0.0)
    g2_utility = float(task.utilities_cost or 0.0)

    g4_insurance = float(task.insurance_cost or 0.0)
    g4_license = float(task.licensing_cost or 0.0)
    g4_warranty = float(task.warranty_cost or 0.0)

    g6_storage = float(task.holding_cost or 0.0)
    g6_int_transport = float(task.international_freight or 0.0)
    g6_handling = float(task.handling_cost or 0.0)
    g6_recovery = float(task.reverse_logistics or 0.0)
    g6_error = float(task.defect_cost or 0.0)

    if project_type == "ITLG":
        g1 = g1_labor + g1_ot + g1_subcontract + g1_qa_qc + g1_material
        g2 = g2_training + g2_space + g2_utility + g2_comm
        g4 = g4_insurance + g4_license + g4_warranty
        g6 = g6_int_transport + g6_storage + g6_recovery + g6_error
        base_cost = g1 + g2 + g4 + g6
    elif project_type == "PRO":
        g1 = g1_subcontract + g1_labor
        g2 = g2_training + g2_space + g2_comm
        base_cost = g1 + g2
    else:
        g1 = g1_material + g1_qa_qc + g1_subcontract + g1_labor + g1_fuel
        g2 = g2_space + g2_utility
        g4 = g4_license + g4_warranty + g4_insurance
        g6 = g6_storage + g6_handling + g6_recovery + g6_error + g6_int_transport
        base_cost = g1 + g2 + g4 + g6

    g5_complexity = getattr(task, "complexity", 0.0) or 0.0
    g5_weather = getattr(task, "weather_contingency", 0.0) or 0.0
    g5_rework = getattr(task, "rework_risk", 0.0) or 0.0
    g5_contingency = getattr(task, "general_contingency", 0.0) or 0.0

    risk_factor = 1.0 + float(g5_complexity) + float(g5_weather) + float(g5_rework) + float(g5_contingency)
    total_cost = float(base_cost) * risk_factor

    await task_repo.update(db, db_obj=task, obj_in={
        "duration_hours": task.duration_hours,
        "internal_labor_cost": g1_labor,
        "overtime_cost": g1_ot,
        "base_cost": base_cost,
        "risk_factor": risk_factor,
        "total_cost": total_cost
    })

async def _recalculate_project_costs(db: AsyncSession, project_id: int):
    stmt = select(Task.base_cost, Task.total_cost).where(Task.project_id == project_id)
    result = await db.execute(stmt)
    tasks_costs = result.all()
    project_base_cost = sum([float(tc[0] or 0.0) for tc in tasks_costs])
    project_total_cost = sum([float(tc[1] or 0.0) for tc in tasks_costs])
    
    project = await project_repo.get_by_id(db, project_id)
    if project:
        await project_repo.update(db, db_obj=project, obj_in={"base_cost": project_base_cost, "total_cost": project_total_cost})



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

    # Recalculate
    await _recalculate_task_costs(db, project, new_task.id)
    await _recalculate_project_costs(db, project_id)
    
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
    updated_task = await task_repo.update(db, db_obj=task, obj_in=task_in)
    
    project = await project_repo.get_by_id(db, project_id)
    if project:
        await _recalculate_task_costs(db, project, task_id)
        await _recalculate_project_costs(db, project_id)
        
    return updated_task


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
        obj = existing
    else:
        new_assignment = TaskResource(
            task_id=task_id,
            **resource_in.model_dump()
        )
        db.add(new_assignment)
        await db.commit()
        await db.refresh(new_assignment)
        obj = new_assignment

    project = await project_repo.get_by_id(db, project_id)
    if project:
        await _recalculate_task_costs(db, project, task_id)
        await _recalculate_project_costs(db, project_id)

    return obj

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

    project = await project_repo.get_by_id(db, project_id)
    if project:
        await _recalculate_task_costs(db, project, task_id)
        await _recalculate_project_costs(db, project_id)

