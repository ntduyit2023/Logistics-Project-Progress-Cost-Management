import sys
from typing import Optional
from pathlib import Path as FilePath
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models import AppProject, Task, TaskResource
from app.schemas.common import APIResponse

# Add project root directory to sys.path so that 'ai_pipeline' is discoverable as a package
backend_dir = FilePath(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(backend_dir.parent))
from ai_pipeline.data import cost_model
from ai_pipeline.models.moi.pipeline_runner import run_new_pipeline

router = APIRouter()

def _convert_numpy(obj):
    import numpy as np
    if isinstance(obj, dict):
        return {k: _convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy(v) for v in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return _convert_numpy(obj.tolist())
    return obj


@router.post("/{project_id}/glpo-optimize", response_model=APIResponse[dict])
async def run_glpo_optimization(
    project_code: str = Path(..., alias="project_id", description="Mã dự án (ví dụ C2011-07)"),
    mc_iterations: int = 10000,
    pareto_count: int = 5,
    overtime_multiplier: float = 1.5,
    target_deadline: Optional[str] = None,
    penalty_per_day: float = 0.0,
    bonus_per_day: float = 0.0,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[dict]:
    """
    Chạy Quy trình AI Pipeline 4 Bước Tự Động:
      1. Xuất CSDL dự án ra thư mục chuẩn
      2. Xử lý qua AI + OR + MC-CPM Pipeline
      3. Ghi nhận kết quả & tập phương án Pareto vào Database PostgreSQL
      4. Xóa dọn dẹp thư mục chuẩn tạm thời cho sạch hệ thống
    """
    try:
        from app.services.ai_pipeline_service import run_ai_pipeline_workflow
        results = await run_ai_pipeline_workflow(
            db=db,
            project_id_or_code=project_code,
            mc_iterations=mc_iterations,
            pareto_count=pareto_count,
            overtime_multiplier=overtime_multiplier,
            target_deadline=target_deadline,
            penalty_per_day=penalty_per_day,
            bonus_per_day=bonus_per_day
        )
        return APIResponse(
            success=True,
            message="GLPO AI + OR + MC-CPM Pipeline completed successfully and saved to Database.",
            data=results
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {str(e)}")


@router.get("/pipeline/runs/{project_id}", response_model=APIResponse[list])
async def get_ai_pipeline_runs_api(
    project_id: str = Path(..., description="Mã/ID dự án (ví dụ C2011-07)"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[list]:
    """
    Lấy danh sách các phiên mô phỏng AI Pipeline của dự án.
    """
    from app.models.ai import AIPipelineRun
    from app.services.project_service import get_project_by_identifier
    project = await get_project_by_identifier(db, project_id)
    
    stmt = select(AIPipelineRun).where(AIPipelineRun.project_id == project.id).order_by(AIPipelineRun.id.desc())
    result = await db.execute(stmt)
    runs = list(result.scalars().all())
    
    data = []
    for r in runs:
        data.append({
            "id": r.id,
            "project_id": r.project_id,
            "status": r.status,
            "pareto_count": r.pareto_count,
            "created_at": r.created_at
        })
    return APIResponse(success=True, message="Lấy danh sách AI Pipeline runs thành công.", data=data)


@router.post("/{project_id}/simulate", response_model=APIResponse[dict])
async def run_ai_simulation(
    project_id: str = Path(..., description="Mã/ID dự án cần chạy mô phỏng AI"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[dict]:
    """
    Chạy mô phỏng AI (Cost Model) cho một dự án cụ thể.
    """
    from app.services.project_service import get_project_by_identifier
    project = await get_project_by_identifier(db, project_id)

    # 2. Lấy Tasks
    tasks_query = await db.execute(
        select(Task).where(Task.project_id == project.id)
    )
    tasks = list(tasks_query.scalars().all())
    
    if not tasks:
        raise HTTPException(status_code=400, detail="Dự án chưa có công việc nào.")

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
