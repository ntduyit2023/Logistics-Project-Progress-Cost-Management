"""
AI Pipeline Runs & Pareto Solutions ORM Models
=====================================================
Thư mục: backend/app/models/ai.py
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Numeric, ForeignKey, DateTime, JSON, Text, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


class AIPipelineRun(Base):
    """
    Theo dõi các phiên chạy Mô phỏng AI Pipeline (Monte Carlo, GNN, CP-SAT).
    """
    __tablename__ = "ai_pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String(100), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Running") # Running, Completed, Failed
    
    target_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    penalty_per_day: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    bonus_per_day: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    mc_iterations: Mapped[int] = mapped_column(Integer, default=10000)
    pareto_count: Mapped[int] = mapped_column(Integer, default=5)
    overtime_multiplier: Mapped[float] = mapped_column(Numeric(5, 2), default=1.5)

    ai_predictions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    mc_results: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    project = relationship("AppProject", back_populates="pipeline_runs")
    pareto_solutions = relationship("ParetoSolution", back_populates="pipeline_run", cascade="all, delete-orphan")


class ParetoSolution(Base):
    """
    Lưu trữ thông tin chi tiết từng Phương án Tối ưu Pareto Frontier.
    """
    __tablename__ = "pareto_solutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("ai_pipeline_runs.id", ondelete="CASCADE"), nullable=False)
    option_name: Mapped[str] = mapped_column(String(100), nullable=False)
    option_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    makespan_hours: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    finish_datetime: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    base_project_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    penalty_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    bonus_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    total_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False) # Net cost after bonus/penalty
    risk_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    tasks_schedule: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict) # Gantt schedule data
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    pipeline_run = relationship("AIPipelineRun", back_populates="pareto_solutions")
