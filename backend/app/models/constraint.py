from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Numeric, ForeignKey, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


class ProjectConstraintTime(Base):
    """
    Ràng buộc Thời gian (Time Constraint) của Dự án.
    """
    __tablename__ = "project_constraint_time"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"), unique=True)
    
    weekly_schedule: Mapped[Dict[str, Any]] = mapped_column(JSON) # Ca làm việc chi tiết từng ngày
    holidays_list: Mapped[Optional[List[Any]]] = mapped_column(JSON, default=list)
    overtime_multiplier: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), default=1.5)
    
    project: Mapped["AppProject"] = relationship(back_populates="constraint_time")


class ProjectConstraintResource(Base):
    """
    Ràng buộc Tài nguyên (Resource Constraint) cấp Dự án.
    """
    __tablename__ = "project_constraint_resource"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    
    resource_name: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(50)) # Renewable / Consumable
    max_availability: Mapped[float] = mapped_column(Numeric(10, 2))
    cost_per_use: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0)
    cost_per_unit: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0)
    
    project: Mapped["AppProject"] = relationship(back_populates="constraint_resources")


class ProjectConstraintLogic(Base):
    """
    Ràng buộc Logic (Edges) giữa các Công việc.
    """
    __tablename__ = "project_constraint_logic"

    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    predecessor_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    successor_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    
    dependency_type: Mapped[str] = mapped_column(String(10), default="FS")
    lag_months: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), default=0)
    lag_weeks: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), default=0)
    lag_days: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), default=0)
    lag_hours: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), default=0)
    
    project: Mapped["AppProject"] = relationship(back_populates="constraint_logic")
    predecessor: Mapped["Task"] = relationship(foreign_keys=[predecessor_id])
    successor: Mapped["Task"] = relationship(foreign_keys=[successor_id])
