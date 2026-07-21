import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://glpo_admin:glpo_password@db:5432/glpo_db')
    async with engine.connect() as conn:
        res_p = await conn.execute(text("SELECT id, project_name, base_cost, total_cost FROM projects WHERE project_name LIKE '%Ganzepoot%'"))
        p = res_p.fetchone()
        print("PROJECT GANZAPOOT:", p)
        
        p_id = p[0]
        res_t = await conn.execute(text(f"SELECT id, task_name, duration_days, internal_labor_cost, material_cost, base_cost, total_cost FROM tasks WHERE project_id = {p_id} LIMIT 5"))
        print("\nFIRST 5 TASKS IN GANZAPOOT:")
        for r in res_t.fetchall():
            print(r)
            
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(check())
