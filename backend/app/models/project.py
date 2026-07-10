from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Numeric, ForeignKey, DateTime, JSON, Boolean
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


class AppProject(Base):
    """
    Lưu trữ thông tin gốc của một Dự án (Project).

    Attributes:
        id (int): Khóa chính của dự án.
        user_id (Optional[int]): Khóa ngoại liên kết tới bảng users.
        project_name (str): Tên hiển thị của dự án.
        search_vector (TSVECTOR): Vector tìm kiếm full-text.
        metadata_json (Optional[Dict[str, Any]]): Lưu trữ JSON linh hoạt cho NoSQL.
        num_tasks (int): Số lượng công việc trong dự án.
        num_edges (int): Số lượng phụ thuộc (edges).
        status (str): Trạng thái của dự án (Planning, Executing, Closed).
        type (Optional[str]): Phân loại dự án (PRO, CON, ITLG).
        base_cost (Optional[float]): Tổng chi phí cơ bản.
        total_cost (Optional[float]): Tổng chi phí dự báo.
        created_at (datetime): Thời gian tạo.
        updated_at (datetime): Thời gian cập nhật gần nhất.
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    project_name: Mapped[str] = mapped_column(String(255))
    search_vector = mapped_column(TSVECTOR)
    
    # DYNAMIC FEATURES: Biến Project thành dạng NoSQL kết hợp SQL
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    num_tasks: Mapped[int] = mapped_column(default=0)
    num_edges: Mapped[int] = mapped_column(default=0)
    network_density: Mapped[float] = mapped_column(Numeric(5, 4), default=0)
    type: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="Planning")
    base_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0.0)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped[Optional["User"]] = relationship(back_populates="projects")
    tasks: Mapped[List["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    simulation_runs: Mapped[List["AISimulationRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    baselines: Mapped[List["ProjectBaseline"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    
    # Constraint Relationships
    constraint_time: Mapped[Optional["ProjectConstraintTime"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    constraint_resources: Mapped[List["ProjectConstraintResource"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    constraint_logic: Mapped[List["ProjectConstraintLogic"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectBaseline(Base):
    """
    Lưu trữ các Baseline (mốc thời gian, chi phí chuẩn) của Dự án.
    """
    __tablename__ = "project_baselines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    simulation_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_simulation_runs.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["AppProject"] = relationship(back_populates="baselines")
