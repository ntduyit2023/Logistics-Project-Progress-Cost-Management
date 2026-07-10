import sys
from pathlib import Path as FilePath
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models import AppProject, Task, TaskResource
from app.schemas.common import APIResponse

# Add ai_pipeline dir to sys.path for cost_model
backend_dir = FilePath(__file__).resolve().parent.parent.parent.parent
ai_pipeline_data_dir = backend_dir.parent / "ai_pipeline" / "data"
sys.path.append(str(ai_pipeline_data_dir))
import cost_model

router = APIRouter()

@router.post("/{project_id}/simulate", response_model=APIResponse[dict])
async def run_ai_simulation(
    project_id: int = Path(..., description="ID của dự án cần chạy mô phỏng AI"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[dict]:
    """
    Chạy mô phỏng AI (Cost Model) cho một dự án cụ thể.

    Hàm này lấy toàn bộ Tasks và Resources của dự án từ DB, 
    chuyển chúng thành Pandas DataFrame và gọi mô hình học máy (cost_model) 
    để dự đoán chi phí. Kết quả sau đó được cập nhật lại vào Database.

    Args:
        project_id (int): ID dự án cần mô phỏng.
        db (AsyncSession): Phiên làm việc cơ sở dữ liệu (Dependency Injection).

    Returns:
        APIResponse[dict]: Phản hồi chứa kết quả dự đoán tổng chi phí và số lượng task cập nhật.

    Raises:
        HTTPException(404): Nếu không tìm thấy Project.
        HTTPException(400): Nếu Project không có Task nào.
    """
    # 1. Lấy Project
    result = await db.execute(select(AppProject).where(AppProject.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Lấy Tasks và TaskResources
    tasks_query = await db.execute(
        select(Task).where(Task.project_id == project_id).options(selectinload(Task.resources))
    )
    tasks = tasks_query.scalars().all()
    
    if not tasks:
        raise HTTPException(status_code=400, detail="No tasks found for this project")

    # Convert to DataFrames cho cost_model
    tasks_data = []
    res_data = []
    
    for t in tasks:
        tasks_data.append({
            "task_id": t.id,
            "project_id": t.project_id,
            "task_name": t.task_name,
            "duration_months": t.duration_months,
            "duration_weeks": t.duration_weeks,
            "duration_days": t.duration_days,
            "duration_hours": t.duration_hours,
            "overtime_hours": t.overtime_hours,
            "lag_time": t.lag_time,
            "complexity": t.complexity,
            "weather_contingency": t.weather_contingency,
            "rework_risk": t.rework_risk,
        })
        
        for r in t.resources:
            res_data.append({
                "task_id": t.id,
                "resource_id": r.resource_id,
                "request_quantity": r.request_quantity
            })
            
    df_tasks = pd.DataFrame(tasks_data)
    df_res = pd.DataFrame(res_data)
    
    # 3. Tính toán qua AI Model
    df_targets = cost_model.calculate_costs_for_dataframe(df_tasks, df_res, project.type or "CON")
    
    # 4. Cập nhật lại vào DB
    targets_dict = df_targets.set_index("task_id").to_dict(orient="index")
    
    total_project_base_cost = 0.0
    total_project_final_cost = 0.0
    
    for t in tasks:
        if t.id in targets_dict:
            td = targets_dict[t.id]
            t.base_cost = td.get("base_cost", 0.0)
            t.total_cost = td.get("total_cost", 0.0)
            t.risk_factor = td.get("risk_factor", 1.0)
            
            total_project_base_cost += t.base_cost
            total_project_final_cost += t.total_cost

    project.base_cost = total_project_base_cost
    project.total_cost = total_project_final_cost
    
    await db.commit()
    
    return APIResponse(
        success=True,
        message="AI Simulation completed successfully",
        data={
            "project_id": project.id,
            "base_cost": float(project.base_cost),
            "total_cost": float(project.total_cost),
            "updated_tasks": len(tasks)
        }
    )
