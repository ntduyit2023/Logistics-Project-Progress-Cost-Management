import asyncio
from app.db.database import async_session
import sys
sys.path.append('/')
from ai_pipeline.models.moi.pipeline_runner import run_new_pipeline
import os
import json

async def run_test():
    async with async_session() as db:
        print("Running AI Pipeline for C2011-07...")
        try:
            results = run_new_pipeline(
                project_id='C2011-07', 
                mc_iterations=10, 
                pareto_count=10, 
                overtime_multiplier=1.5, 
                penalty_per_day=500.0, 
                bonus_per_day=200.0, 
                target_deadline='2011-05-30T17:00:00'
            )
            print("Pipeline run successfully! No 500 error!")
            
            pareto_options = results.get('pareto_options', [])
            if pareto_options:
                opt_0 = pareto_options[0]
                tasks_sched = opt_0.get('tasks_schedule', {})
                if isinstance(tasks_sched, dict):
                    task_items = tasks_sched.values()
                else:
                    task_items = tasks_sched
                    
                for t in task_items:
                    if t.get('task_id') == 'C2011-07_1' or t.get('id') == 'C2011-07_1':
                        print("\n--- Task 1 Details ---")
                        print(f"Base Effort Hours: {t.get('base_effort_hours')}")
                        print(f"Duration Hours: {t.get('duration_hours')}")
                        print(f"OT Resource Breakdown: {json.dumps(t.get('ot_resource_breakdown', []), indent=2)}")
                        break
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(run_test())
