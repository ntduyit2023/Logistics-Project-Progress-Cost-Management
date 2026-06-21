"""
GLPO Backend - Database Configuration (Async)
Sử dụng asyncpg + SQLAlchemy Async cho hiệu năng cao.
"""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://glpo_admin:glpo_password@localhost:5432/glpo_db"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection: Cung cấp Database session (phiên kết nối) bất đồng bộ cho mỗi request.

    Yields:
        AsyncSession: Phiên kết nối SQLAlchemy bất đồng bộ.

    Raises:
        Exception: Các lỗi liên quan đến kết nối hoặc ngắt kết nối cơ sở dữ liệu.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
