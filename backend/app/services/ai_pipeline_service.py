"""
GLPO AI Pipeline Orchestrator Service
======================================
Thư mục: backend/app/services/ai_pipeline_service.py

Mô tả:
  Thực thi quy trình 4 bước huấn luyện / chạy mô phỏng AI Pipeline hoàn chỉnh:
    Bước 1: Xuất CSDL dự án ra thư mục chuẩn (/ai_pipeline/data/processed/{project_code}/)
    Bước 2: Đưa thư mục chuẩn đó vào xử lý qua AI Pipeline (HGT GNN + Monte Carlo CPM + CP-SAT Pareto Solver)
    Bước 3: Xuất kết quả & tập phương án Pareto Frontier lưu trực tiếp vào CSDL PostgreSQL
    Bước 4: Xóa thư mục chuẩn tạm để giữ sạch hệ thống.
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIPipelineRun, ParetoSolution
from app.services.dataset_sync import export_project_dataset
from app.services.project_service import get_project_by_identifier
from ai_pipeline.models.moi.pipeline_runner import run_new_pipeline


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


async def run_ai_pipeline_workflow(
    db: AsyncSession,
    project_id_or_code: str,
    mc_iterations: int = 10000,
    pareto_count: int = 5,
    target_deadline: Optional[str] = None,
    penalty_per_day: float = 0.0,
    bonus_per_day: float = 0.0
) -> Dict[str, Any]:
    """
    Thực thi toàn bộ Quy trình 4 bước của AI Pipeline.
    """
    project = await get_project_by_identifier(db, project_id_or_code)
    project_code = project.id

    # Tạo bản ghi theo dõi AI Pipeline Run trong PostgreSQL
    run_obj = AIPipelineRun(
        project_id=project.id,
        status="Running",
        penalty_per_day=penalty_per_day,
        bonus_per_day=bonus_per_day,
        mc_iterations=mc_iterations,
        pareto_count=pareto_count,
        created_at=datetime.utcnow()
    )
    db.add(run_obj)
    await db.commit()
    await db.refresh(run_obj)

    project_dir = None
    try:
        # BƯỚC 1: Xuất CSDL dự án ra thư mục chuẩn
        print(f"\n================================================================================")
        print(f"[AI WORKFLOW Step 1/4] Xuất CSDL dự án {project_code} ra thư mục chuẩn...")
        print(f"================================================================================")
        project_dir = await export_project_dataset(db, project_code)

        # BƯỚC 2: Đưa thư mục chuẩn đó vào xử lý qua AI Pipeline
        print(f"\n[AI WORKFLOW Step 2/4] Đưa thư mục chuẩn vào xử lý qua AI + OR + MC-CPM Pipeline...")
        raw_results = run_new_pipeline(
            project_id=project_code,
            mc_iterations=mc_iterations,
            pareto_count=pareto_count,
            target_deadline=target_deadline,
            penalty_per_day=penalty_per_day,
            bonus_per_day=bonus_per_day,
            output_json=False
        )
        safe_results = _convert_numpy(raw_results)

        # BƯỚC 3: Xuất kết quả & lưu vào Database PostgreSQL
        print(f"\n[AI WORKFLOW Step 3/4] Ghi nhận kết quả tối ưu & Pareto Frontier vào CSDL PostgreSQL...")
        run_obj.status = "Completed"
        run_obj.finished_at = datetime.utcnow()
        run_obj.ai_predictions = safe_results.get("ai_predictions", {})
        run_obj.mc_results = safe_results.get("mc_results", {})

        pareto_list = safe_results.get("pareto_options") or safe_results.get("pareto_solutions", [])
        for idx, sol in enumerate(pareto_list, 1):
            ps = ParetoSolution(
                run_id=run_obj.id,
                option_name=sol.get("option_name", f"Option {idx}"),
                option_index=idx,
                makespan_hours=float(sol.get("makespan_hours", 0.0)),
                finish_datetime=str(sol.get("finish_datetime", "")),
                base_project_cost=float(sol.get("base_project_cost", 0.0)),
                penalty_cost=float(sol.get("penalty_cost", 0.0)),
                bonus_amount=float(sol.get("bonus_amount", 0.0)),
                total_cost=float(sol.get("total_cost", 0.0)),
                risk_pct=float(sol.get("risk_pct", 0.0)),
                tasks_schedule=sol.get("tasks", sol.get("tasks_schedule", {}))
            )
            db.add(ps)

        await db.commit()
        await db.refresh(run_obj)
        print(f"   ✓ Đã lưu thành công {len(pareto_list)} phương án Pareto Frontier vào Database (Run ID: {run_obj.id})!")

        return {
            "run_id": run_obj.id,
            "project_id": project_code,
            "status": "Completed",
            "pareto_solutions": pareto_list,
            "pareto_options": pareto_list,
            "mc_summary": safe_results.get("mc_results", {}).get("summary", {})
        }

    except Exception as e:
        run_obj.status = "Failed"
        run_obj.error_message = str(e)
        run_obj.finished_at = datetime.utcnow()
        await db.commit()
        raise e

    finally:
        # BƯỚC 4: Xóa thư mục chuẩn để làm sạch hệ thống
        if project_dir and Path(project_dir).exists():
            print(f"\n[AI WORKFLOW Step 4/4] Dọn dẹp & Xóa thư mục chuẩn tạm ({project_dir}) cho sạch hệ thống...")
            shutil.rmtree(project_dir, ignore_errors=True)
            print(f"   ✓ Đã dọn dẹp sạch sẽ toàn bộ thư mục chuẩn tạm!")
