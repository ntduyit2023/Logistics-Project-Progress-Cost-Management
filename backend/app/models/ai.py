from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, ForeignKey, DateTime, JSON, Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


class AISimulationRun(Base):
    """
    Theo dõi các lần chạy mô phỏng AI (Monte Carlo, GNN...).
    """
    __tablename__ = "ai_simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    ai_weights: Mapped[Dict[str, Any]] = mapped_column(JSON, default={"time": 50, "cost": 50})
    status: Mapped[str] = mapped_column(String(50), default="Running")
    results_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["AppProject"] = relationship(back_populates="simulation_runs")
    insights: Mapped[List["AIInsight"]] = relationship(back_populates="simulation_run", cascade="all, delete-orphan")


class AIInsight(Base):
    """
    Kết quả phân tích/khuyến nghị cụ thể từ AI.
    """
    __tablename__ = "ai_insights"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    simulation_run_id: Mapped[int] = mapped_column(ForeignKey("ai_simulation_runs.id", ondelete="CASCADE"))
    
    action_type: Mapped[List[str]] = mapped_column(JSON) # e.g. ["CRASHING", "AGENDA_OVERRIDE"]
    target_tasks: Mapped[List[str]] = mapped_column(JSON) # e.g. ["T12", "T15"]
    human_message: Mapped[Optional[str]] = mapped_column(Text)
    modifications: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    impact: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    risk: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    simulation_run: Mapped["AISimulationRun"] = relationship(back_populates="insights")
