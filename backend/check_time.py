import asyncio
from app.db.database import async_session
import sys
sys.path.append('/')
from ai_pipeline.models.moi.pipeline_runner import run_new_pipeline

async def run_test():
    async with async_session() as db:
        results = run_new_pipeline(project_id='C2011-07', mc_iterations=10, pareto_count=1, overtime_multiplier=1.5, penalty_per_day=500.0, bonus_per_day=200.0)
        tasks_sched = results['pareto_options'][0]['tasks_schedule']
        for t_id, t in tasks_sched.items():
            if t_id == 'C2011-07_1':
                print(f"Task 1: {t}")
                break
asyncio.run(run_test())
