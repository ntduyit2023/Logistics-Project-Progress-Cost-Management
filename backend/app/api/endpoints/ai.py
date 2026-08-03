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
    
from pydantic import BaseModel

class ApplyParetoRequest(BaseModel):
    option_index: int
    option_name: Optional[str] = None
    makespan_hours: Optional[float] = None
    total_cost: Optional[float] = None
    tasks_schedule: Optional[dict] = None

from fastapi import APIRouter, Depends, HTTPException, Path, Body

@router.post("/{project_id}/apply-pareto", response_model=APIResponse[dict])
async def apply_pareto_option_api(
    project_id: str = Path(..., description="Mã/ID dự án"),
    payload: ApplyParetoRequest = Body(...),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[dict]:
    """
    Áp dụng Lịch trình Phương án Pareto Tối ưu được chọn vào CSDL Dự án.
    """
    try:
        from app.services.project_service import get_project_by_identifier
        from datetime import datetime, timedelta
        
        project = await get_project_by_identifier(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Không tìm thấy dự án")

        # Lấy danh sách tasks hiện tại của dự án
        stmt = select(Task).where(Task.project_id == project.id)
        res = await db.execute(stmt)
        db_tasks = list(res.scalars().all())
        
        # Map tasks by all ID variations (task_id, int id, suffix numbers)
        task_map = {}
        for t in db_tasks:
            str_id = str(t.id)
            str_tid = str(t.task_id) if t.task_id else ""
            
            task_map[str_id] = t
            if str_tid:
                task_map[str_tid] = t
                parts = str_tid.replace('T-', '').split('_')
                if len(parts) > 0:
                    task_map[parts[-1]] = t

        updated_count = 0
        tasks_sched = payload.tasks_schedule or {}
        
        # Base datetime from earliest task baseline_start or default
        task_starts = [t.baseline_start for t in db_tasks if t.baseline_start]
        base_start_dt = min(task_starts) if task_starts else datetime(2010, 1, 1, 8, 0, 0)
        
        # 1. Cơ chế Bảo vệ Dữ liệu Gốc trên bảng Project
        proj_meta = dict(project.metadata_json or {})
        orig_baselines = proj_meta.get("original_task_baselines", {})
        if not orig_baselines:
            orig_baselines = {}
            for t in db_tasks:
                t_key = str(t.task_id or t.id)
                orig_baselines[t_key] = {
                    "duration_hours": float(t.duration_hours or 0.0),
                    "baseline_start": t.baseline_start.isoformat() if t.baseline_start else None
                }
            proj_meta["original_task_baselines"] = orig_baselines

        modified_task_ids = []
        task_details_map = {}

        print(f"[APPLY_PARETO] tasks_sched keys ({len(tasks_sched)}): {list(tasks_sched.keys())[:10]}")
        print(f"[APPLY_PARETO] task_map keys ({len(task_map)}): {list(task_map.keys())[:15]}")

        for t_key, s_data in tasks_sched.items():
            if isinstance(s_data, dict):
                tid_in_data = str(s_data.get("task_id", ""))
                matched_task = (
                    task_map.get(str(t_key)) or 
                    task_map.get(tid_in_data) or 
                    task_map.get(str(t_key).replace('T-', '').split('_')[-1]) or
                    task_map.get(tid_in_data.replace('T-', '').split('_')[-1])
                )
                if matched_task:
                    t_canon_id = str(matched_task.task_id or matched_task.id)
                    old_dur = orig_baselines.get(t_canon_id, {}).get("duration_hours", float(matched_task.duration_hours))

                    new_dur = float(s_data["duration_hours"]) if ("duration_hours" in s_data and s_data["duration_hours"] is not None) else float(matched_task.duration_hours)
                    matched_task.duration_hours = new_dur

                    if "start_hours" in s_data and s_data["start_hours"] is not None:
                        offset_hrs = float(s_data["start_hours"])
                        matched_task.baseline_start = base_start_dt + timedelta(hours=offset_hrs)

                    ot_cost = float(s_data.get("overtime_cost", s_data.get("overtime", 0.0)) or 0.0)
                    ot_hours_per_day = float(s_data.get("overtime_hours_per_day", s_data.get("overtime_hours", 0.0)) or 0.0)
                    
                    matched_task.overtime = ot_cost

                    is_crashed = (new_dur < old_dur - 0.01) or (ot_cost > 0) or (ot_hours_per_day > 0) or (s_data.get("crashing_strategy", "Normal") != "Normal") or (s_data.get("extra_workers", 0) > 0) or s_data.get("is_ai_optimized", False)
                    
                    # Debug first 5 tasks
                    if updated_count < 5:
                        print(f"[APPLY_PARETO] Task {t_key} -> matched={t_canon_id} | old_dur={old_dur} new_dur={new_dur} | ot_cost={ot_cost} ot_h/d={ot_hours_per_day} | is_crashed={is_crashed}")
                        print(f"  s_data keys: {list(s_data.keys())}")
                    
                    if is_crashed:
                        modified_task_ids.append(str(matched_task.task_id))
                        modified_task_ids.append(str(matched_task.id))
                        task_details_map[t_canon_id] = {
                            "old_duration": old_dur,
                            "new_duration": new_dur,
                            "base_effort_hours": s_data.get("base_effort_hours", old_dur),
                            "assigned_workers": s_data.get("assigned_workers", 1),
                            "extra_workers": s_data.get("extra_workers", 0),
                            "crashing_strategy": s_data.get("crashing_strategy", "Normal"),
                            "overtime_hours_per_day": ot_hours_per_day,
                            "overtime_cost": ot_cost,
                            "labor_ot_premium": s_data.get("labor_ot_premium", 0),
                            "equipment_ot_extra": s_data.get("equipment_ot_extra", 0),
                            "energy_ot_extra": s_data.get("energy_ot_extra", 0),
                            "added_resources_cost": s_data.get("added_resources_cost", 0),
                            "baseline_start": s_data.get("baseline_start"),
                            "baseline_end": s_data.get("baseline_end"),
                            "is_crashed": True
                        }
                    updated_count += 1
                else:
                    print(f"[APPLY_PARETO] NO MATCH for t_key={t_key}, tid_in_data={tid_in_data}")

        print(f"[APPLY_PARETO] RESULT: updated_count={updated_count}, modified_task_ids={modified_task_ids[:10]}")

        proj_meta["applied_option"] = payload.option_name or f"Phương án {payload.option_index + 1}"
        proj_meta["applied_task_ids"] = list(set(modified_task_ids))
        proj_meta["applied_task_details"] = task_details_map
        project.metadata_json = proj_meta
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "metadata_json")

        await db.commit()
        
        return APIResponse(
            success=True,
            message=f"Đã áp dụng thành công {payload.option_name or f'Phương án {payload.option_index + 1}'} vào CSDL dự án!",
            data={
                "project_id": project.id,
                "updated_tasks": updated_count,
                "modified_crashed_tasks": len(set(modified_task_ids)),
                "option_index": payload.option_index
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/restore-baseline", response_model=APIResponse[dict])
async def restore_baseline_api(
    project_id: str = Path(..., description="Mã/ID dự án"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[dict]:
    """
    Khôi phục dữ liệu ban đầu (Baseline) của Dự án từ bản sao lưu bảo vệ.
    """
    try:
        from app.services.project_service import get_project_by_identifier
        from datetime import datetime
        project = await get_project_by_identifier(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Không tìm thấy dự án")

        stmt = select(Task).where(Task.project_id == project.id)
        res = await db.execute(stmt)
        db_tasks = list(res.scalars().all())
        
        proj_meta = dict(project.metadata_json or {})
        orig_baselines = proj_meta.get("original_task_baselines", {})

        restored_count = 0
        for t in db_tasks:
            t_key = str(t.task_id or t.id)
            orig = orig_baselines.get(t_key)
            if orig:
                if "duration_hours" in orig and orig["duration_hours"] is not None:
                    t.duration_hours = float(orig["duration_hours"])
                if "baseline_start" in orig:
                    st_val = orig["baseline_start"]
                    t.baseline_start = datetime.fromisoformat(st_val) if st_val else None
                t.overtime = 0.0
                restored_count += 1

        proj_meta.pop("applied_option", None)
        proj_meta.pop("applied_task_ids", None)
        proj_meta.pop("applied_task_details", None)
        project.metadata_json = proj_meta

        await db.commit()
        
        return APIResponse(
            success=True,
            message=f"Đã khôi phục thành công dữ liệu ban đầu (Baseline) cho {restored_count} công việc của dự án!",
            data={"project_id": project.id, "restored_tasks": restored_count}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
