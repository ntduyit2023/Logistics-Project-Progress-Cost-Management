import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://glpo_admin:glpo_password@db:5432/glpo_db')
    async with engine.connect() as conn:
        res_r = await conn.execute(text("SELECT id, resource_name, resource_type, cost_per_unit FROM project_constraint_resource WHERE project_id = 154"))
        print("RESOURCES IN PG FOR PROJECT 154:")
        for r in res_r.fetchall():
            print(r)
            
        res_t = await conn.execute(text("SELECT id, task_name, internal_labor_cost, equipment_fuel_cost, material_cost, base_cost, total_cost FROM tasks WHERE id LIKE '%46%' LIMIT 5"))
        print("\nTASK EMBANKMENTS IN PG:")
        for r in res_t.fetchall():
            print(r)
            
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(check())
