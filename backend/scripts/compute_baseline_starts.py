import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import async_session
from app.models import Task, AppProject, ProjectConstraintLogic
from collections import defaultdict, deque

async def run():
    print("Starting CPM forward pass to calculate baseline_start...")
    async with async_session() as db:
        stmt = select(AppProject)
        result = await db.execute(stmt)
        projects = result.scalars().all()
        
        for project in projects:
            print(f"Processing Project {project.id}: {project.project_name}")
            
            stmt_tasks = select(Task).where(Task.project_id == project.id)
            result_tasks = await db.execute(stmt_tasks)
            tasks = {t.id: t for t in result_tasks.scalars().all()}
            
            stmt_logic = select(ProjectConstraintLogic).where(ProjectConstraintLogic.project_id == project.id)
            result_logic = await db.execute(stmt_logic)
            logics = result_logic.scalars().all()
            
            adj = defaultdict(list)
            in_degree = {t_id: 0 for t_id in tasks}
            
            for logic in logics:
                u = logic.predecessor_id
                v = logic.successor_id
                lag = logic.lag_days or 0.0
                if u in tasks and v in tasks:
                    adj[u].append((v, lag))
                    in_degree[v] += 1
                    
            # Initialize
            project_start = project.created_at or datetime.now()
            start_times = {}
            
            q = deque()
            for t_id, deg in in_degree.items():
                if deg == 0:
                    q.append(t_id)
                    start_times[t_id] = project_start
                    
            while q:
                u_id = q.popleft()
                u_task = tasks[u_id]
                u_start = start_times[u_id]
                
                # Assume duration_days is used, default to 1 if missing
                dur_days = float(u_task.duration_days or 1)
                u_end = u_start + timedelta(days=dur_days)
                
                for v_id, lag in adj[u_id]:
                    v_start_candidate = u_end + timedelta(days=float(lag))
                    if v_id not in start_times or start_times[v_id] < v_start_candidate:
                        start_times[v_id] = v_start_candidate
                        
                    in_degree[v_id] -= 1
                    if in_degree[v_id] == 0:
                        q.append(v_id)
                        
            # Update DB
            for t_id, start_time in start_times.items():
                tasks[t_id].baseline_start = start_time
                db.add(tasks[t_id])
                
        await db.commit()
    print("Done computing baseline starts.")

if __name__ == "__main__":
    asyncio.run(run())
