"""
GLPO Backend - SQLAlchemy ORM Models
Sử dụng SQLAlchemy 2.0 Type Hinting (Mapped, mapped_column) cho Type Safety tuyệt đối.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Numeric, Text, Boolean,
    ForeignKey, DateTime, JSON, Index, Integer
)
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


# ==============================================================================
# 1. APPLICATION MANAGEMENT LAYER
# ==============================================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    projects: Mapped[List["AppProject"]] = relationship(back_populates="owner")


class AppProject(Base):
    __tablename__ = "app_projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    project_name: Mapped[str] = mapped_column(String(255))
    search_vector = mapped_column(TSVECTOR)
    
    # DYNAMIC FEATURES: Biến Project thành dạng NoSQL kết hợp SQL
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    num_tasks: Mapped[int] = mapped_column(default=0)
    num_edges: Mapped[int] = mapped_column(default=0)
    network_density: Mapped[float] = mapped_column(Numeric(5, 4), default=0)
    status: Mapped[str] = mapped_column(String(50), default="Planning")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped[Optional["User"]] = relationship(back_populates="projects")
    tasks: Mapped[List["FactTask"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    simulation_runs: Mapped[List["AISimulationRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    baselines: Mapped[List["ProjectBaseline"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    
    # Constraint Relationships
    constraint_time: Mapped[Optional["ProjectConstraintTime"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    constraint_resources: Mapped[List["ProjectConstraintResource"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    constraint_logic: Mapped[List["ProjectConstraintLogic"]] = relationship(back_populates="project", cascade="all, delete-orphan")


# ==============================================================================
# 2. THE 3 CONSTRAINT DOMAINS (3 TRỤC RÀNG BUỘC)
# ==============================================================================

class ProjectConstraintTime(Base):
    __tablename__ = "project_constraint_time"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"), unique=True)
    
    weekly_schedule: Mapped[Dict[str, Any]] = mapped_column(JSON) # Ca làm việc chi tiết từng ngày
    holidays_list: Mapped[Optional[List[Any]]] = mapped_column(JSON, default=list)
    overtime_multiplier: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), default=1.5)
    
    project: Mapped["AppProject"] = relationship(back_populates="constraint_time")


class ProjectConstraintResource(Base):
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
    __tablename__ = "project_constraint_logic"

    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    predecessor_id: Mapped[int] = mapped_column(ForeignKey("fact_tasks.task_id", ondelete="CASCADE"), primary_key=True)
    successor_id: Mapped[int] = mapped_column(ForeignKey("fact_tasks.task_id", ondelete="CASCADE"), primary_key=True)
    
    dependency_type: Mapped[str] = mapped_column(String(10), default="FS")
    lag_days: Mapped[int] = mapped_column(default=0)
    
    project: Mapped["AppProject"] = relationship(back_populates="constraint_logic")
    predecessor: Mapped["FactTask"] = relationship(foreign_keys=[predecessor_id])
    successor: Mapped["FactTask"] = relationship(foreign_keys=[successor_id])


# ==============================================================================
# 3. AI SIMULATION & INSIGHTS
# ==============================================================================

class AISimulationRun(Base):
    __tablename__ = "ai_simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    ai_weights: Mapped[Dict[str, Any]] = mapped_column(JSON, default={"time": 50, "cost": 50})
    status: Mapped[str] = mapped_column(String(50), default="Running")
    results_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["AppProject"] = relationship(back_populates="simulation_runs")
    insights: Mapped[List["AIInsight"]] = relationship(back_populates="simulation_run", cascade="all, delete-orphan")


class AIInsight(Base):
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


class ProjectBaseline(Base):
    __tablename__ = "project_baselines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    simulation_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_simulation_runs.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["AppProject"] = relationship(back_populates="baselines")


# ==============================================================================
# 4. DIMENSION TOPICS (Snowflake)
# ==============================================================================

class DimTopicTime(Base):
    __tablename__ = "dim_topic_time"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    duration: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))
    baseline_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    baseline_end: Mapped[Optional[datetime]] = mapped_column(DateTime)


class DimTopicCost(Base):
    __tablename__ = "dim_topic_cost"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resource_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0)
    fixed_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0)
    # total_cost = resource_cost + fixed_cost (Được tính ở cấp độ DB hoặc property)
    @property
    def total_cost(self) -> float:
        return float((self.resource_cost or 0) + (self.fixed_cost or 0))


class DimTopicRisk(Base):
    __tablename__ = "dim_topic_risk"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    optimistic_time: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))
    pessimistic_time: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))
    variance: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    criticality_index: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))


class DimTopicResources(Base):
    __tablename__ = "dim_topic_resources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resource_demand: Mapped[Optional[str]] = mapped_column(Text)


# ==============================================================================
# 5. CORE FACT
# ==============================================================================

class FactTask(Base):
    __tablename__ = "fact_tasks"

    task_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    task_label: Mapped[str] = mapped_column(String(50))
    wbs: Mapped[Optional[str]] = mapped_column(String(100))
    task_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # DYNAMIC FEATURES CHO TASK
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    topic_time_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dim_topic_time.id", ondelete="SET NULL"))
    topic_cost_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dim_topic_cost.id", ondelete="SET NULL"))
    topic_risk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dim_topic_risk.id", ondelete="SET NULL"))
    topic_resources_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dim_topic_resources.id", ondelete="SET NULL"))

    project: Mapped["AppProject"] = relationship(back_populates="tasks")
    time_info: Mapped[Optional["DimTopicTime"]] = relationship(lazy="joined")
    cost_info: Mapped[Optional["DimTopicCost"]] = relationship(lazy="joined")
    risk_info: Mapped[Optional["DimTopicRisk"]] = relationship(lazy="joined")
    resource_info: Mapped[Optional["DimTopicResources"]] = relationship(lazy="joined")
