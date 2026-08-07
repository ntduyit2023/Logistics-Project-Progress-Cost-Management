"""
GLPO Backend - Dataset Import & Export Sync Service
===================================================
Thư mục: backend/app/services/dataset_sync.py

Mô tả:
  Cung cấp dịch vụ xuất (Export) dữ liệu Dự án từ PostgreSQL thành bộ 6 tệp chuẩn AI Pipeline 
  (/ai_pipeline/data/processed/{project_code}/) bao gồm:
    1. project_info.csv
    2. tasks.csv (38 cột chi phí + duration_hours + baseline_start + total_cost + task_name)
    3. resources.csv
    4. logic.csv
    5. task_resources.csv
    6. agenda.json (lịch làm việc)

  Đồng thời hỗ trợ nhập (Import) đồng bộ trực tiếp từ thư mục chuẩn vào PostgreSQL Database.
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    AppProject, ProjectCalendar, Resource, Task, TaskLogic, TaskResource
)
from app.services.project_service import get_project_by_identifier
from app.db.seed import seed_project_data

# Thư mục gốc chứa dữ liệu sản xuất / tạm thời AI Pipeline (data/production)
root_app = Path(__file__).resolve().parent.parent.parent
if Path("/ai_pipeline/data/production").exists():
    BASE_PRODUCTION_DIR = Path("/ai_pipeline/data/production")
elif (root_app.parent / "ai_pipeline" / "data" / "production").exists():
    BASE_PRODUCTION_DIR = root_app.parent / "ai_pipeline" / "data" / "production"
else:
    BASE_PRODUCTION_DIR = root_app / "ai_pipeline" / "data" / "production"

BASE_PROCESSED_DIR = BASE_PRODUCTION_DIR

COST_COLS = [
    'labor', 'material', 'equipment', 'energy', 'testing_inspection', 'project_management',
    'facility', 'utilities', 'communication', 'training', 'quality_management', 'overtime',
    'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay',
    'expediting', 'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance',
    'contingency_reserve', 'management_reserve', 'transportation', 'ordering', 'packaging',
    'reverse_logistics', 'customs', 'supplier_coordination', 'opportunity_cost', 'capital_cost',
    'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
]


async def export_project_dataset(db: AsyncSession, project_id_or_code: str, target_dir: Optional[Path] = None) -> Path:
    """
    Xuất toàn bộ dữ liệu dự án từ Database PostgreSQL ra cấu trúc thư mục huấn luyện AI.
    """
    project = await get_project_by_identifier(db, project_id_or_code)
    project_code = project.id

    if target_dir is None:
        target_dir = BASE_PROCESSED_DIR / project_code

    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Xuất project_info.csv
    info_data = [{
        "project_id": project.id,
        "project_name": project.project_name,
        "project_type": project.project_type or "CON",
        "penalty_per_day": float(project.penalty_per_day or 0.0),
        "bonus_per_day": float(project.bonus_per_day or 0.0)
    }]
    pd.DataFrame(info_data).to_csv(target_dir / "project_info.csv", index=False)

    # 2. Xuất tasks.csv
    stmt_t = select(Task).where(Task.project_id == project.id).order_by(Task.id.asc())
    res_t = await db.execute(stmt_t)
    tasks = list(res_t.scalars().all())

    tasks_rows = []
    for t in tasks:
        b_start_str = t.baseline_start.isoformat() if t.baseline_start else ""
        row = {
            "task_id": t.task_id,
            "baseline_start": b_start_str,
            "duration_hours": float(t.duration_hours or 0.0)
        }
        for col in COST_COLS:
            row[col] = float(getattr(t, col, 0.0) or 0.0)
        row["task_name"] = t.task_name
        row["total_cost"] = float(t.total_cost or 0.0)
        tasks_rows.append(row)

    pd.DataFrame(tasks_rows).to_csv(target_dir / "tasks.csv", index=False)

    # 3. Xuất resources.csv
    stmt_r = select(Resource).where(Resource.project_id == project.id).order_by(Resource.id.asc())
    res_r = await db.execute(stmt_r)
    resources = list(res_r.scalars().all())

    res_rows = []
    for idx, r in enumerate(resources, 1):
        res_rows.append({
            "ID": r.resource_id or idx,
            "name": r.name or r.resource_id,
            "type": r.type,
            "max_availability": float(r.max_availability or 1.0),
            "unit_cost": float(r.unit_cost or 0.0),
            "energy": float(r.energy or 0.0),
            "overtime_multi": float(r.overtime_multi or 1.5),
            "max_overtime_per_day": float(r.max_overtime_per_day or 4.0)
        })
    pd.DataFrame(res_rows).to_csv(target_dir / "resources.csv", index=False)

    # 4. Xuất logic.csv
    stmt_l = select(TaskLogic).where(TaskLogic.project_id == project.id).order_by(TaskLogic.id.asc())
    res_l = await db.execute(stmt_l)
    logics = list(res_l.scalars().all())

    logic_rows = []
    for l in logics:
        logic_rows.append({
            "predecessor_id": l.predecessor_id,
            "successor_id": l.successor_id,
            "dependency_type": l.dependency_type or "FS",
            "lag_hours": float(l.lag_hours or 0.0)
        })
    pd.DataFrame(logic_rows).to_csv(target_dir / "logic.csv", index=False)

    # 5. Xuất task_resources.csv
    stmt_tr = select(TaskResource).where(TaskResource.project_id == project.id).order_by(TaskResource.id.asc())
    res_tr = await db.execute(stmt_tr)
    tr_list = list(res_tr.scalars().all())

    tr_rows = []
    for tr in tr_list:
        tr_rows.append({
            "task_id": tr.task_id,
            "resource_id": tr.resource_id,
            "request_quantity": float(tr.request_quantity or 1.0)
        })
    pd.DataFrame(tr_rows).to_csv(target_dir / "task_resources.csv", index=False)

    # 6. Xuất agenda.json
    stmt_cal = select(ProjectCalendar).where(ProjectCalendar.project_id == project.id)
    res_cal = await db.execute(stmt_cal)
    calendar = res_cal.scalars().first()

    agenda_dict = {
        "project_id": project.id,
        "weekly_schedule": calendar.weekly_schedule if calendar and calendar.weekly_schedule else {},
        "holidays": calendar.holidays_list if calendar and calendar.holidays_list else [],
        "overtime_allowed": True
    }
    with open(target_dir / "agenda.json", "w", encoding="utf-8") as f:
        json.dump(agenda_dict, f, indent=2, ensure_ascii=False)

    print(f"[DATASET SYNC] Đã xuất thành công bộ dữ liệu chuẩn AI tại: {target_dir}")
    return target_dir


async def import_project_dataset(db: AsyncSession, project_dir: Path) -> AppProject:
    """
    Nạp dữ liệu từ thư mục chuẩn AI (/ai_pipeline/data/processed/{project_code}) vào PostgreSQL CSDL.
    """
    if not project_dir.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục dự án: {project_dir}")

    await seed_project_data(db, project_dir)
    return await get_project_by_identifier(db, project_dir.name)
