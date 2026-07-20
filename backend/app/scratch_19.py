import asyncio
import json
from sqlalchemy import text
from app.db.database import async_session
from app.models.project import AppProject

async def main():
    async with async_session() as s:
        p = await s.get(AppProject, 19)
        print("=== PROJECT 19 ===")
        if p:
            print("Status:", p.status)
            meta = p.metadata_json or {}
            sim_res = meta.get("simulation_results", {})
            print("Simulation Keys:", list(sim_res.keys()))
            
        res = await s.execute(text("SELECT * FROM tasks WHERE project_id = 19 AND task_name ILIKE '%ladder%'"))
        tasks = [dict(r) for r in res.mappings().all()]
        print("\n=== TASKS (WBS 26 / Installing ladder) ===")
        for t in tasks:
            print(t)
            t_id = t['id']
            tr_res = await s.execute(text(f"SELECT tr.*, r.resource_name, r.cost_per_unit FROM task_resources tr JOIN project_constraint_resource r ON tr.resource_id = r.id WHERE tr.task_id = '{t_id}'"))
            trs = [dict(r) for r in tr_res.mappings().all()]
            print(f"  Task Resources for {t_id}:", trs)

if __name__ == '__main__':
    asyncio.run(main())
