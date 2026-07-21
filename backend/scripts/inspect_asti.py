import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://glpo_admin:glpo_password@db:5432/glpo_db')
    async with engine.connect() as conn:
        res_p = await conn.execute(text("SELECT id, project_name, type, num_tasks, num_edges, base_cost, total_cost FROM projects WHERE project_name LIKE '%Asti%'"))
        print("PROJECT RECORD IN PG:")
        proj_row = res_p.fetchone()
        print(proj_row)
        
        if proj_row:
            p_id = proj_row[0]
            res_t = await conn.execute(text(f"SELECT id, task_name, duration_days, duration_hours, internal_labor_cost, equipment_fuel_cost, base_cost, total_cost FROM tasks WHERE project_id = {p_id} LIMIT 10"))
            print("\nFIRST 10 TASKS IN PG:")
            for r in res_t.fetchall():
                print(r)
                
            res_sum = await conn.execute(text(f"SELECT SUM(base_cost), SUM(total_cost), SUM(internal_labor_cost), SUM(equipment_fuel_cost) FROM tasks WHERE project_id = {p_id}"))
            print("\nSUM OF TASK COSTS IN PG:")
            print(res_sum.fetchone())
            
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(check())
