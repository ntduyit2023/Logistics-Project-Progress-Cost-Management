from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class TaskBase(BaseModel):
    """
    Schema cơ sở cho Công việc (Task).
    """
    task_name: str = Field(..., max_length=255)
    task_type: Optional[str] = Field(None, max_length=100)
    status: str = Field("Pending", max_length=50)
    baseline_start: Optional[datetime] = None
    type: Optional[str] = Field(None, max_length=255)
    
    # Hub Time Components
    duration_months: Optional[float] = None
    duration_weeks: Optional[float] = None
    duration_days: Optional[float] = None
    duration_hours: Optional[float] = None
    calendar_type: Optional[str] = Field(None, max_length=50)
    
    # G1: Direct Costs
    internal_labor_cost: Optional[float] = None
    subcontracting_cost: Optional[float] = None
    overtime_crashing_cost: Optional[float] = None
    material_cost: Optional[float] = None
    equipment_cost: Optional[float] = None
    direct_transportation: Optional[float] = None
    energy_fuel_cost: Optional[float] = None
    testing_and_inspection: Optional[float] = None

    # G2: Indirect Costs
    pm_overhead: Optional[float] = None
    facility_rent: Optional[float] = None
    utilities: Optional[float] = None
    communication_cost: Optional[float] = None
    internal_training: Optional[float] = None
    quality_mgmt_overhead: Optional[float] = None

    # G4: Contractual
    permits_and_licensing: Optional[float] = None
    project_insurance: Optional[float] = None
    warranty_and_after_sales: Optional[float] = None
    regulatory_compliance: Optional[float] = None

    # G5: Logistics
    inventory_holding_cost: Optional[float] = None
    ordering_cost: Optional[float] = None
    shortage_stockout: Optional[float] = None
    obsolescence_cost: Optional[float] = None
    international_freight: Optional[float] = None
    packaging_and_handling: Optional[float] = None
    reverse_logistics: Optional[float] = None

    # G6: Temporal
    wait_queue_time: Optional[float] = None
    setup_transition_time: Optional[float] = None
    induction_time: Optional[float] = None
    lead_time: Optional[float] = None
    pert_3_point_estimate: Optional[float] = None

    # G9: Risks
    technical_complexity: Optional[float] = None
    rework_probability: Optional[float] = None
    external_dependency_level: Optional[float] = None
    contingency_reserve: Optional[float] = None
    management_reserve: Optional[float] = None
    weather_seasonal_risk: Optional[float] = None
    technology_risk: Optional[float] = None

    # G11: Human & Org
    required_skill_level: Optional[int] = None
    staff_experience: Optional[float] = None
    learning_curve_effect: Optional[float] = None
    hr_stability_risk: Optional[float] = None
    cross_functional_coordination: Optional[int] = None
    occupational_safety_risk: Optional[int] = None

    # G12: ESG
    environmental_impact: Optional[int] = None
    waste_disposal_cost: Optional[float] = None
    community_social_impact: Optional[int] = None
    carbon_tax_credit: Optional[float] = None
    esg_compliance: Optional[int] = None
    
    # Metadata JSON
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TaskCreate(TaskBase):
    id: str = Field(..., max_length=255, description="ID của Task")


class TaskUpdate(TaskBase):
    task_name: Optional[str] = Field(None, max_length=255)


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: int

# --- G7: Task Resource Assignment ---

class TaskResourceBase(BaseModel):
    request_quantity: float = Field(..., ge=0, description="Số lượng tài nguyên yêu cầu")
    allocated_quantity: Optional[float] = Field(None, ge=0)
    labor_productivity: Optional[float] = Field(None, ge=0)
    equipment_utilization: Optional[float] = Field(None, ge=0)
    resource_substitutability: Optional[int] = Field(None)

class TaskResourceCreate(TaskResourceBase):
    resource_id: int = Field(..., description="ID của ProjectConstraintResource")

class TaskResourceResponse(TaskResourceBase):
    model_config = ConfigDict(from_attributes=True)
    task_id: str
    resource_id: int
    resource_name: Optional[str] = None # Will be populated if joined
    resource_type: Optional[str] = None

