"""
GLPO Backend - Main API Router
Gom nhóm tất cả các sub-routers.
"""
from fastapi import APIRouter
from app.api.endpoints import projects

api_router = APIRouter()

# Đăng ký các router con vào router chính
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
