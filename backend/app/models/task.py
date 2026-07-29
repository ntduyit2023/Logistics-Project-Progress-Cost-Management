"""
Task ORM Model
=====================================================
Thư mục: backend/app/models/task.py
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    String, Numeric, ForeignKey, DateTime, JSON, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


class Task(Base):
    """
    Quản lý Danh sách Công việc (tasks.csv).
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    baseline_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_hours: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    total_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    cost_features: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict) # 38 cột chi phí chuẩn

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("AppProject", back_populates="tasks")
