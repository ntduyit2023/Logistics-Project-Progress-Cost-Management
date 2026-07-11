import subprocess
import json
import os
import asyncio
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import AppProject
from app.db.database import async_session

import pandas as pd
from sqlalchemy import text

async def _export_project_data(project_id: str, db_session: AsyncSession, base_dir: str):
    processed_dir = os.path.join(base_dir, "ai_pipeline", "data", "processed", str(project_id))
    os.makedirs(processed_dir, exist_ok=True)
    
    tasks_query = text(f"SELECT * FROM tasks WHERE project_id = {project_id}")
    tasks_res = await db_session.execute(tasks_query)
    df_tasks = pd.DataFrame(tasks_res.mappings().all())
    if df_tasks.empty:
        df_tasks = pd.DataFrame(columns=['id', 'task_name'])
    df_tasks.to_csv(os.path.join(processed_dir, 'tasks.csv'), index=False)
    
    logic_query = text(f"SELECT predecessor_id as predecessor_task_id, successor_id as successor_task_id, dependency_type, lag_days FROM project_constraint_logic WHERE project_id = {project_id}")
    logic_res = await db_session.execute(logic_query)
    df_logic = pd.DataFrame(logic_res.mappings().all())
    if df_logic.empty:
        df_logic = pd.DataFrame(columns=['predecessor_task_id', 'successor_task_id', 'dependency_type', 'lag_days'])
    df_logic.to_csv(os.path.join(processed_dir, 'predecessors.csv'), index=False)
    
    res_query = text(f"SELECT id as \"ID\", resource_name, resource_type, cost_per_unit as unit_cost, max_availability as capacity FROM project_constraint_resource WHERE project_id = {project_id}")
    res_res = await db_session.execute(res_query)
    df_res = pd.DataFrame(res_res.mappings().all())
    if df_res.empty:
        df_res = pd.DataFrame(columns=['ID', 'resource_name', 'resource_type', 'unit_cost', 'capacity'])
    df_res.to_csv(os.path.join(processed_dir, 'resources.csv'), index=False)
    
    tr_query = text(f"SELECT tr.task_id, tr.resource_id, tr.request_quantity FROM task_resources tr JOIN tasks t ON tr.task_id = t.id WHERE t.project_id = {project_id}")
    tr_res = await db_session.execute(tr_query)
    df_tr = pd.DataFrame(tr_res.mappings().all())
    if df_tr.empty:
        df_tr = pd.DataFrame(columns=['task_id', 'resource_id', 'request_quantity'])
    df_tr.to_csv(os.path.join(processed_dir, 'task_resources.csv'), index=False)

async def _run_ai_pipeline(project_id: str, project_type: str, db_session: AsyncSession):
    """
    Hàm chạy ngầm quá trình giả lập AI (Optimal Simulation)
    Gọi script ai_pipeline/src/pipeline_runners/run_main.py
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    ai_script_path = os.path.join(base_dir, "ai_pipeline", "src", "pipeline_runners", "run_main.py")
    output_file = os.path.join(base_dir, "ai_pipeline", "data", "processed", str(project_id), f"output_{project_id}_main.json")
    
    await _export_project_data(project_id, db_session, base_dir)
    
    try:
        # Chạy subprocess không block event loop
        ai_cmd = [
            "python", ai_script_path,
            "--project_id", str(project_id),
            "--output_json", output_file
        ]
        process = await asyncio.create_subprocess_exec(
            *ai_cmd,
            cwd=base_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                simulation_results = json.load(f)
                
            project = await db_session.get(AppProject, int(project_id))
            if project:
                current_metadata = project.metadata_json or {}
                new_metadata = dict(current_metadata)
                new_metadata['simulation_results'] = simulation_results
                
                project.metadata_json = new_metadata
                project.status = "Planning"
                await db_session.commit()
                print(f"✅ AI Simulation completed for Project {project_id}.")
        else:
            print(f"⚠️ AI Simulation finished but output file not found: {output_file}")
            print(f"STDERR: {stderr.decode('utf-8')}")
            await _restore_project_status(project_id, db_session, "Planning")

    except Exception as e:
        print(f"❌ Unexpected Error in AI Simulation: {e}")
        await _restore_project_status(project_id, db_session, "Error")

async def _restore_project_status(project_id: str, db_session: AsyncSession, status: str):
    project = await db_session.get(AppProject, int(project_id))
    if project:
        project.status = status
        await db_session.commit()

async def run_simulation_background(project_id: str, project_type: str):
    """
    Entrypoint để FastAPI gọi BackgroundTasks
    """
    async with async_session() as db:
        await _run_ai_pipeline(project_id, project_type, db)

