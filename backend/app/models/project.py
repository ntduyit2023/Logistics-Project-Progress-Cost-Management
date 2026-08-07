"""
App Project & Resource ORM Models
=====================================================
Thư mục: backend/app/models/project.py
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Numeric, ForeignKey, DateTime, JSON, Boolean, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


class AppProject(Base):
    """
    Quản lý thông tin Dự án & Tham số Hợp đồng.
    Khóa chính `id` chính là Mã dự án (ví dụ 'C2011-07').
    """
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), default="CON")
    status: Mapped[str] = mapped_column(String(50), default="Planning")
    
    target_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    penalty_per_day: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    bonus_per_day: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    
    base_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    total_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    num_tasks: Mapped[int] = mapped_column(Integer, default=0)
    num_edges: Mapped[int] = mapped_column(Integer, default=0)
    
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def project_code(self) -> str:
        return self.id

    # Relationships
    owner = relationship("User", back_populates="projects", lazy="selectin")
    calendar = relationship("ProjectCalendar", back_populates="project", uselist=False, cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="project", cascade="all, delete-orphan")
    logic_edges = relationship("TaskLogic", back_populates="project", cascade="all, delete-orphan")
    task_resources = relationship("TaskResource", back_populates="project", cascade="all, delete-orphan")
    pipeline_runs = relationship("AIPipelineRun", back_populates="project", cascade="all, delete-orphan")


class ProjectCalendar(Base):
    """
    Cấu hình Thời gian làm việc của Dự án (agenda.json).
    """
    __tablename__ = "project_calendars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String(100), ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False)
    weekly_schedule: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    holidays_list: Mapped[List[Any]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("AppProject", back_populates="calendar")


class Resource(Base):
    """
    Khai báo Tài nguyên (resources.csv).
    """
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String(100), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(50), default="Human")
    max_availability: Mapped[float] = mapped_column(Numeric(10, 2), default=1.0)
    unit_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    energy: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    overtime_multi: Mapped[float] = mapped_column(Numeric(5, 2), default=1.5)
    max_overtime_per_day: Mapped[float] = mapped_column(Numeric(5, 2), default=4.0)
    addres_efficiency: Mapped[float] = mapped_column(Numeric(5, 2), default=0.7)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("AppProject", back_populates="resources")


class TaskLogic(Base):
    """
    Mối quan hệ Phụ thuộc Logic giữa các Tasks (logic.csv).
    """
    __tablename__ = "task_logic"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String(100), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    predecessor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    successor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    dependency_type: Mapped[str] = mapped_column(String(10), default="FS")
    lag_hours: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    project = relationship("AppProject", back_populates="logic_edges")


class TaskResource(Base):
    """
    Phân bổ Tài nguyên cho Task (task_resources.csv).
    """
    __tablename__ = "task_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String(100), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    request_quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    project = relationship("AppProject", back_populates="task_resources")
