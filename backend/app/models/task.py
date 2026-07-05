from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Numeric, ForeignKey, DateTime, JSON, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


class TaskResource(Base):
    """
    Phân bổ Tài nguyên cho một Công việc (G7 Resource Mapping).
    """
    __tablename__ = "task_resources"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("project_constraint_resource.id", ondelete="CASCADE"), primary_key=True)
    
    request_quantity: Mapped[float] = mapped_column(Numeric(15, 2))
    allocated_quantity: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    labor_productivity: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    equipment_utilization: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    resource_substitutability: Mapped[Optional[int]] = mapped_column(Integer)

    task: Mapped["Task"] = relationship(back_populates="resources")
    resource: Mapped["ProjectConstraintResource"] = relationship()


class Task(Base):
    """
    Siêu bảng (Wide Table) đại diện cho Công việc (Node) trong dự án.
    Bao gồm toàn bộ 60+ tính năng (Features) trải dài qua 12 nhóm (Cost, Risk, HR...).
    """
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    task_name: Mapped[str] = mapped_column(String(255))
    task_type: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="Pending")
    baseline_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    type: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Hub Time Components
    duration_months: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    duration_weeks: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    duration_days: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    duration_hours: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    calendar_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # G1: Direct Costs
    internal_labor_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    subcontracting_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    overtime_crashing_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    material_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    equipment_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    direct_transportation: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    energy_fuel_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    testing_and_inspection: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))

    # G2: Indirect Costs
    pm_overhead: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    facility_rent: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    utilities: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    communication_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    internal_training: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    quality_mgmt_overhead: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))

    # G4: Contractual
    permits_and_licensing: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    project_insurance: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    warranty_and_after_sales: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    regulatory_compliance: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))

    # G5: Logistics
    inventory_holding_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    ordering_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    shortage_stockout: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    obsolescence_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    international_freight: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    packaging_and_handling: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    reverse_logistics: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))

    # G6: Temporal
    wait_queue_time: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    setup_transition_time: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    induction_time: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    lead_time: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    pert_3_point_estimate: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))

    # G9: Risks
    technical_complexity: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    rework_probability: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    external_dependency_level: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    contingency_reserve: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    management_reserve: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    weather_seasonal_risk: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    technology_risk: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))

    # G11: Human & Org
    required_skill_level: Mapped[Optional[int]] = mapped_column(Integer)
    staff_experience: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    learning_curve_effect: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    hr_stability_risk: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    cross_functional_coordination: Mapped[Optional[int]] = mapped_column(Integer)
    occupational_safety_risk: Mapped[Optional[int]] = mapped_column(Integer)

    # G12: ESG
    environmental_impact: Mapped[Optional[int]] = mapped_column(Integer)
    waste_disposal_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    community_social_impact: Mapped[Optional[int]] = mapped_column(Integer)
    carbon_tax_credit: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    esg_compliance: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Metadata JSON cho AI Computed Data (G3, G8, G10)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    # Quan hệ
    project: Mapped["AppProject"] = relationship(back_populates="tasks")
    resources: Mapped[List["TaskResource"]] = relationship(back_populates="task", cascade="all, delete-orphan")
