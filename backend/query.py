from app.services.pipeline_runner import run_ai_pipeline_sync
import asyncio
from app.db.database import async_session
import json

async def run():
    async with async_session() as db:
        res = await run_ai_pipeline_sync(db, 'C2012-04')
        if hasattr(res, 'pareto_options'):
            print(json.dumps(res.pareto_options[-1]['tasks_schedule'].get('C2012-04_48', {}), indent=2))
        else:
            print("No pareto options")

asyncio.run(run())

asyncio.run(run())
