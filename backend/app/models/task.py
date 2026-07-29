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


from sqlalchemy import Computed

class Task(Base):
    """
    Quản lý Danh sách Công việc (tasks.csv).
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String(100), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    baseline_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_hours: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    
    # 38 Cột chi phí vật lý (Physical SQL Columns)
    labor: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    material: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    equipment: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    energy: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    testing_inspection: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    project_management: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    facility: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    utilities: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    communication: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    training: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    quality_management: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    overtime: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    delay_penalty: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    inventory_holding: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    waiting_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    idle_resource: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    revenue_delay: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    expediting: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    insurance: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    rework: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    warranty: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    litigation: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    regulatory_compliance: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    contingency_reserve: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    management_reserve: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    transportation: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    ordering: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    packaging: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    reverse_logistics: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    customs: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    supplier_coordination: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    opportunity_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    capital_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    financing_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    npv_loss: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    esg_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    carbon_tax: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    reputation_cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)

    # Cột tổng chi phí được CSDL PostgreSQL tự động tính (GENERATED ALWAYS AS STORED)
    total_cost: Mapped[float] = mapped_column(
        Numeric(15, 2),
        Computed(
            "COALESCE(labor, 0) + COALESCE(material, 0) + COALESCE(equipment, 0) + COALESCE(energy, 0) + "
            "COALESCE(testing_inspection, 0) + COALESCE(project_management, 0) + COALESCE(facility, 0) + "
            "COALESCE(utilities, 0) + COALESCE(communication, 0) + COALESCE(training, 0) + "
            "COALESCE(quality_management, 0) + COALESCE(overtime, 0) + COALESCE(delay_penalty, 0) + "
            "COALESCE(inventory_holding, 0) + COALESCE(waiting_cost, 0) + COALESCE(idle_resource, 0) + "
            "COALESCE(revenue_delay, 0) + COALESCE(expediting, 0) + COALESCE(insurance, 0) + "
            "COALESCE(rework, 0) + COALESCE(warranty, 0) + COALESCE(litigation, 0) + "
            "COALESCE(regulatory_compliance, 0) + COALESCE(contingency_reserve, 0) + "
            "COALESCE(management_reserve, 0) + COALESCE(transportation, 0) + COALESCE(ordering, 0) + "
            "COALESCE(packaging, 0) + COALESCE(reverse_logistics, 0) + COALESCE(customs, 0) + "
            "COALESCE(supplier_coordination, 0) + COALESCE(opportunity_cost, 0) + COALESCE(capital_cost, 0) + "
            "COALESCE(financing_cost, 0) + COALESCE(npv_loss, 0) + COALESCE(esg_cost, 0) + "
            "COALESCE(carbon_tax, 0) + COALESCE(reputation_cost, 0)",
            persisted=True
        )
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("AppProject", back_populates="tasks")
