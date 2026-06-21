"""
GLPO Backend - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.schemas import HealthCheckResponse, APIResponse
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Quản lý vòng đời (Lifespan) của FastAPI Application.

    Thực hiện kiểm tra kết nối DB khi khởi động (Startup) và đóng engine khi tắt (Shutdown).

    Args:
        app (FastAPI): Ứng dụng FastAPI.

    Yields:
        None

    Raises:
        SQLAlchemyError: Nếu không thể khởi tạo kết nối cơ sở dữ liệu ban đầu.
    """
    async with engine.begin() as conn:
        pass
    yield
    await engine.dispose()


app = FastAPI(
    title="GLPO - AI Project Scheduling API",
    description="API Backend cho hệ thống AI Lập lịch Dự án Xây dựng (RCPSP)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký tập hợp các API Routes (Thêm prefix /api/v1 cho chuẩn REST)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_model=APIResponse[Dict[str, str]], tags=["System"])
async def root() -> APIResponse[Dict[str, str]]:
    """
    Kiểm tra xem API Server có đang hoạt động hay không.

    Returns:
        APIResponse[Dict[str, str]]: Một object JSON chứa thông báo chào mừng.
    """
    return APIResponse(
        success=True,
        message="GLPO Backend API is running!",
        data={"status": "online"}
    )


@app.get("/health", response_model=APIResponse[HealthCheckResponse], tags=["System"])
async def health_check() -> APIResponse[HealthCheckResponse]:
    """
    Kiểm tra tình trạng kết nối Cơ sở dữ liệu và sức khỏe toàn hệ thống.

    Returns:
        APIResponse[HealthCheckResponse]: Trạng thái hệ thống (healthy/unhealthy).

    Raises:
        HTTPException: Lỗi 500 nếu kết nối DB thất bại.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return APIResponse(
            success=True,
            message="Database connection verified",
            data=HealthCheckResponse(status="healthy", database="connected")
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System error: {str(e)}"
        )
