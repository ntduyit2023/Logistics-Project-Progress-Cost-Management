from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class TaskBase(BaseModel):
    """
    Schema cơ sở cho Công việc (Task).

    Attributes:
        task_name (str): Tên task.
        task_type (Optional[str]): Phân loại task.
        status (str): Trạng thái.
        base_cost (Optional[float]): Chi phí gốc.
        total_cost (Optional[float]): Tổng chi phí.
        risk_factor (Optional[float]): Hệ số rủi ro.
        baseline_start (Optional[datetime]): Ngày bắt đầu.
        type (Optional[str]): Phân loại.
    """
    task_name: str = Field(..., max_length=255)
    task_type: Optional[str] = Field(None, max_length=100)
    status: str = Field("Pending", max_length=50)
    base_cost: Optional[float] = Field(0.0)
    total_cost: Optional[float] = Field(0.0)
    risk_factor: Optional[float] = Field(1.0)
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
    overtime_cost: Optional[float] = None
    equipment_fuel_cost: Optional[float] = None
    qa_qc_cost: Optional[float] = None
    material_cost: Optional[float] = None
    outsourcing_cost: Optional[float] = None
    
    # G2: Indirect Costs
    training_cost: Optional[float] = None
    facility_rent: Optional[float] = None
    communication_cost: Optional[float] = None
    utilities_cost: Optional[float] = None
    
    # G4: Contractual
    insurance_cost: Optional[float] = None
    licensing_cost: Optional[float] = None
    warranty_cost: Optional[float] = None
    
    # G5: Risk Coefficients
    complexity: Optional[float] = None
    weather_contingency: Optional[float] = None
    general_contingency: Optional[float] = None
    rework_risk: Optional[float] = None
    
    # G6: Logistics
    holding_cost: Optional[float] = None
    international_freight: Optional[float] = None
    handling_cost: Optional[float] = None
    reverse_logistics: Optional[float] = None
    defect_cost: Optional[float] = None
    
    # G7: Time Components
    overtime_hours: Optional[float] = None
    lag_time: Optional[float] = None
    
    # Metadata JSON
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TaskCreate(TaskBase):
    """
    Schema dùng để tạo Task mới.
    """
    id: Optional[str] = Field(None)
    project_id: Optional[int] = Field(None)


class TaskUpdate(BaseModel):
    """
    Schema dùng để cập nhật Task (chỉ gửi các trường cần update).
    """
    task_name: Optional[str] = Field(None, max_length=255)
    task_type: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    base_cost: Optional[float] = None
    total_cost: Optional[float] = None
    risk_factor: Optional[float] = None
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
    overtime_cost: Optional[float] = None
    equipment_fuel_cost: Optional[float] = None
    qa_qc_cost: Optional[float] = None
    material_cost: Optional[float] = None
    outsourcing_cost: Optional[float] = None
    
    # G2: Indirect Costs
    training_cost: Optional[float] = None
    facility_rent: Optional[float] = None
    communication_cost: Optional[float] = None
    utilities_cost: Optional[float] = None
    
    # G4: Contractual
    insurance_cost: Optional[float] = None
    licensing_cost: Optional[float] = None
    warranty_cost: Optional[float] = None
    
    # G5: Risk Coefficients
    complexity: Optional[float] = None
    weather_contingency: Optional[float] = None
    general_contingency: Optional[float] = None
    rework_risk: Optional[float] = None
    
    # G6: Logistics
    holding_cost: Optional[float] = None
    international_freight: Optional[float] = None
    handling_cost: Optional[float] = None
    reverse_logistics: Optional[float] = None
    defect_cost: Optional[float] = None
    
    # G7: Time Components
    overtime_hours: Optional[float] = None
    lag_time: Optional[float] = None
    metadata_json: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase):
    """
    Schema trả về thông tin Task.
    
    Attributes:
        id (str): Khóa chính của Task.
        project_id (int): Khóa ngoại liên kết tới project.
    """
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

