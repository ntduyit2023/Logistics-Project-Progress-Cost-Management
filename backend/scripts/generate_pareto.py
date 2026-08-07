import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Setup paths so we can import backend and ai_pipeline modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.db.database import async_session
from app.models.project import AppProject, Resource, TaskResource, TaskLogic
from app.models.task import Task
from ai_pipeline.models.moi.cpsat_pareto_solver import CPSATParetoSolver

async def generate_pareto(project_id: str):
    async with async_session() as db:
        result = await db.execute(
            select(AppProject)
            .options(joinedload(AppProject.calendar))
            .where(AppProject.id == project_id)
        )
        project = result.scalars().first()
        if not project:
            print(f"Project {project_id} not found.")
            return

        result_tasks = await db.execute(select(Task).where(Task.project_id == project_id))
        db_tasks = result_tasks.scalars().all()

        result_res = await db.execute(select(Resource).where(Resource.project_id == project_id))
        db_res = result_res.scalars().all()

        result_tr = await db.execute(select(TaskResource).where(TaskResource.project_id == project_id))
        db_tr = result_tr.scalars().all()

        result_dep = await db.execute(select(TaskLogic).where(TaskLogic.project_id == project_id))
        db_dep = result_dep.scalars().all()

        # Build structures
        tasks = []
        for t in db_tasks:
            tasks.append({
                'id': t.task_id,
                'task_id': t.task_id,
                'task_name': t.task_name,
                'duration_hours': float(t.duration_hours),
                'baseline_start': t.baseline_start.strftime('%Y-%m-%dT%H:%M:%SZ') if t.baseline_start else None,
                'baseline_end': t.baseline_end.strftime('%Y-%m-%dT%H:%M:%SZ') if t.baseline_end else None,
                'base_cost': float(t.total_cost),
                'labor': float(t.labor),
                'equipment': float(t.equipment),
                'energy': float(t.energy),
                'total_cost': float(t.total_cost)
            })

        resources_dict = {}
        capacities = {}
        for r in db_res:
            r_dict = {
                'ID': r.resource_id,
                'name': r.name,
                'type': r.type,
                'unit_cost': float(r.unit_cost),
                'max_availability': float(r.max_availability),
                'energy': float(r.energy),
                'overtime_multi': float(r.overtime_multi),
                'max_overtime_per_day': float(r.max_overtime_per_day)
            }
            resources_dict[r.resource_id] = r_dict
            resources_dict[r.name] = r_dict
            capacities[r.resource_id] = float(r.max_availability)
            capacities[r.name] = float(r.max_availability)

        task_resource_reqs = {}
        task_labor_rates = {}
        for tr in db_tr:
            r_info = resources_dict.get(tr.resource_id, {})
            qty = float(tr.request_quantity)
            u_cost = float(r_info.get('unit_cost', 0.0))
            task_resource_reqs[(tr.task_id, tr.resource_id)] = qty
            task_labor_rates[tr.task_id] = task_labor_rates.get(tr.task_id, 0.0) + (qty * u_cost)

        dependencies = []
        for d in db_dep:
            dependencies.append((d.predecessor_id, d.successor_id, {'lag': float(d.lag_hours), 'type': d.dependency_type}))

        calendar = project.calendar
        weekly_schedule = calendar.weekly_schedule if calendar else None
        holidays_list = calendar.holidays_list if calendar else None

        solver = CPSATParetoSolver(
            tasks=tasks,
            dependencies=dependencies,
            resource_capacities=capacities,
            task_resource_requirements=task_resource_reqs,
            task_labor_rates=task_labor_rates,
            resources_dict=resources_dict,
            weekly_schedule=weekly_schedule,
            holidays_list=holidays_list
        )

        print("Running AI Solver (CP-SAT)...")
        solutions = solver.solve(time_limit_sec=15.0, pareto_count=5)
        
        # Save to DB
        meta = project.metadata_json or {}
        
        # Option wrapper
        output_data = {
            "project_id": project_id,
            "pareto_options": solutions
        }
        
        meta["pareto_options_data"] = output_data
        project.metadata_json = meta
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "metadata_json")
        await db.commit()
        print(f"Successfully saved {len(solutions)} Pareto options for {project_id}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_pareto.py <project_id>")
        sys.exit(1)
    
    # Check if inside an event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop and loop.is_running():
        pass
    else:
        asyncio.run(generate_pareto(sys.argv[1]))
