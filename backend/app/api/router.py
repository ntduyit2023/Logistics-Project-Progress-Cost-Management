"""
GLPO Backend - Main API Router
Gom nhóm tất cả các sub-routers.
"""
from fastapi import APIRouter
from app.api.endpoints import projects, tasks, constraints, ai

api_router = APIRouter()

# Đăng ký các router con vào router chính
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(tasks.router, prefix="/projects", tags=["Tasks"])
api_router.include_router(constraints.router, prefix="/projects", tags=["Constraints"])
api_router.include_router(ai.router, tags=["AI Simulation"])
