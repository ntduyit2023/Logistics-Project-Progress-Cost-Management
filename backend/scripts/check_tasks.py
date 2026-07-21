import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://glpo_admin:glpo_password@db:5432/glpo_db')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, task_name, complexity, weather_contingency, general_contingency, rework_risk, risk_factor FROM tasks WHERE id LIKE 'C2018-09%' LIMIT 5"))
        rows = res.fetchall()
        print("RISK DATA IN PG FOR C2018-09:")
        for r in rows:
            print(r)
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(check())
