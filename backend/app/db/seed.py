"""
GLPO Database Seeder & Importer Script
======================================
Thư mục: backend/app/db/seed.py

Chức năng:
    Nạp tự động toàn bộ dữ liệu 5 Dự án Tiêu chuẩn (C2011-07, C2012-04, C2012-08, C2018-09, C2019-16)
    từ thư mục /ai_pipeline/data/processed/ vào Database PostgreSQL mới.
"""

import os
import sys
import json
import asyncio
import pandas as pd
from pathlib import Path
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from app.models import (
    AppProject, ProjectCalendar, Resource, Task, TaskLogic, TaskResource
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://glpo_admin:glpo_password@db:5432/glpo_db"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

COST_COLS = [
    'labor', 'material', 'equipment', 'energy', 'testing_inspection', 'project_management',
    'facility', 'utilities', 'communication', 'training', 'quality_management', 'overtime',
    'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay',
    'expediting', 'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance',
    'contingency_reserve', 'management_reserve', 'transportation', 'ordering', 'packaging',
    'reverse_logistics', 'customs', 'supplier_coordination', 'opportunity_cost', 'capital_cost',
    'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
]


async def seed_project_data(session: AsyncSession, project_dir: Path):
    project_code = project_dir.name
    print(f"\n[SEEDER] Đang nạp dữ liệu dự án: {project_code}...")

    # 1. Đọc project_info.csv
    info_file = project_dir / "project_info.csv"
    project_name = f"Dự án {project_code}"
    project_type = "CON"
    penalty_per_day = 0.0
    bonus_per_day = 0.0

    if info_file.exists():
        df_info = pd.read_csv(info_file)
        if not df_info.empty:
            row = df_info.iloc[0]
            project_name = str(row.get('project_name', project_name))
            project_type = str(row.get('project_type', project_type)).upper()
            penalty_per_day = float(row.get('penalty_per_day', 0.0) or 0.0)
            bonus_per_day = float(row.get('bonus_per_day', 0.0) or 0.0)

    # Lấy hoặc tạo mới AppProject (khóa chính id = project_code)
    stmt_p = select(AppProject).where(AppProject.id == project_code)
    res_p = await session.execute(stmt_p)
    project = res_p.scalars().first()

    if not project:
        project = AppProject(
            id=project_code,
            project_name=project_name,
            project_type=project_type,
            status="Planning",
            penalty_per_day=penalty_per_day,
            bonus_per_day=bonus_per_day
        )
        session.add(project)
        await session.flush()
    else:
        project.project_name = project_name
        project.project_type = project_type
        project.penalty_per_day = penalty_per_day
        project.bonus_per_day = bonus_per_day

    # Xóa dữ liệu cũ của dự án để nạp mới (Clean Reload)
    await session.execute(delete(TaskResource).where(TaskResource.project_id == project.id))
    await session.execute(delete(TaskLogic).where(TaskLogic.project_id == project.id))
    await session.execute(delete(Task).where(Task.project_id == project.id))
    await session.execute(delete(Resource).where(Resource.project_id == project.id))
    await session.execute(delete(ProjectCalendar).where(ProjectCalendar.project_id == project.id))

    # 2. Đọc agenda.json (ProjectCalendar)
    agenda_file = project_dir / "agenda.json"
    if agenda_file.exists():
        with open(agenda_file, "r", encoding="utf-8") as f:
            agenda_data = json.load(f)
            weekly_schedule = agenda_data.get('weekly_schedule', {})
            holidays_list = agenda_data.get('holidays_list', [])
            
            calendar_obj = ProjectCalendar(
                project_id=project.id,
                weekly_schedule=weekly_schedule,
                holidays_list=holidays_list
            )
            session.add(calendar_obj)

    # 3. Đọc resources.csv
    resources_file = project_dir / "resources.csv"
    if resources_file.exists():
        df_res = pd.read_csv(resources_file)
        for _, row in df_res.iterrows():
            res_obj = Resource(
                project_id=project.id,
                resource_id=str(row.get('ID', row.get('resource_id', ''))),
                name=str(row.get('name', '')),
                type=str(row.get('type', 'Human')),
                max_availability=float(row.get('max_availability', 1.0) or 1.0),
                unit_cost=float(row.get('unit_cost', 0.0) or 0.0),
                energy=float(row.get('energy', 0.0) or 0.0),
                overtime_multi=float(row.get('overtime_multi', 1.5) or 1.5),
                max_overtime_per_day=float(row.get('max_overtime_per_day', 4.0) or 4.0),
                addres_efficiency=float(row.get('addres_efficiency', 0.7) or 0.7)
            )
            session.add(res_obj)
        await session.flush()

    # 4. Đọc tasks.csv
    tasks_file = project_dir / "tasks.csv"
    total_project_base_cost = 0.0
    task_count = 0

    if tasks_file.exists():
        df_tasks = pd.read_csv(tasks_file)
        task_count = len(df_tasks)
        for _, row in df_tasks.iterrows():
            t_id = str(row.get('task_id', ''))
            t_name = str(row.get('task_name', t_id))
            b_start = row.get('baseline_start', None)
            b_start_dt = None
            if pd.notna(b_start):
                dt_obj = pd.to_datetime(b_start)
                if hasattr(dt_obj, 'to_pydatetime'):
                    b_start_dt = dt_obj.to_pydatetime()
                else:
                    b_start_dt = dt_obj
            dur_h = float(row.get('duration_hours', 0.0) or 0.0)

            cost_kwargs = {}
            task_total_c = 0.0
            for col in COST_COLS:
                val = 0.0
                if col in row and pd.notna(row[col]):
                    val = round(float(row[col] or 0.0), 2)
                cost_kwargs[col] = val
                task_total_c += val

            total_project_base_cost += task_total_c

            task_obj = Task(
                project_id=project.id,
                task_id=t_id,
                task_name=t_name,
                baseline_start=b_start_dt,
                duration_hours=dur_h,
                **cost_kwargs
            )
            session.add(task_obj)
        await session.flush()

    # 5. Đọc logic.csv
    logic_file = project_dir / "logic.csv"
    edge_count = 0
    if logic_file.exists():
        df_logic = pd.read_csv(logic_file)
        edge_count = len(df_logic)
        for _, row in df_logic.iterrows():
            logic_obj = TaskLogic(
                project_id=project.id,
                predecessor_id=str(row.get('predecessor_id', '')),
                successor_id=str(row.get('successor_id', '')),
                dependency_type=str(row.get('dependency_type', 'FS')),
                lag_hours=float(row.get('lag_hours', 0.0) or 0.0)
            )
            session.add(logic_obj)

    # 6. Đọc task_resources.csv
    task_res_file = project_dir / "task_resources.csv"
    if task_res_file.exists():
        df_tr = pd.read_csv(task_res_file)
        for _, row in df_tr.iterrows():
            tr_obj = TaskResource(
                project_id=project.id,
                task_id=str(row.get('task_id', '')),
                resource_id=str(row.get('resource_id', '')),
                request_quantity=float(row.get('request_quantity', 1.0) or 1.0)
            )
            session.add(tr_obj)

    # 7. Cập nhật thông tin tổng hợp lên Project
    project.num_tasks = task_count
    project.num_edges = edge_count
    project.base_cost = round(total_project_base_cost, 2)
    project.total_cost = round(total_project_base_cost, 2)

    await session.commit()
    print(f"   ✓ Đã import thành công: {task_count} Tasks, {edge_count} Logic Edges | Chi phí gốc: ${total_project_base_cost:,.2f}")


async def main():
    processed_dir = Path("/ai_pipeline/data/processed")
    if not processed_dir.exists():
        # Fallback local path
        processed_dir = Path("/app/ai_pipeline/data/processed")
        if not processed_dir.exists():
            processed_dir = root_dir.parent / "ai_pipeline" / "data" / "processed"

    print("================================================================================")
    print("[START] KHỞI TẠO VÀ NẠP DỮ LIỆU CƠ SỞ DỮ LIỆU MỚI (DATABASE SEEDER)")
    print("================================================================================")

    async with AsyncSessionLocal() as session:
        project_dirs = [d for d in processed_dir.iterdir() if d.is_dir()]
        for p_dir in project_dirs:
            try:
                await seed_project_data(session, p_dir)
            except Exception as e:
                import traceback
                print(f"[ERROR] Lỗi khi nạp dữ liệu {p_dir.name}: {e}")
                traceback.print_exc()

    print("\n================================================================================")
    print("[DONE] NẠP DỮ LIỆU THÀNH CÔNG CHO TOÀN BỘ CÁC DỰ ÁN!")
    print("================================================================================")


if __name__ == "__main__":
    asyncio.run(main())
