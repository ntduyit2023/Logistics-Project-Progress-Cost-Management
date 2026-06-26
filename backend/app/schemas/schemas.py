"""
GLPO Backend - Pydantic Schemas (API Contracts)
Định nghĩa cấu trúc dữ liệu vào/ra cho mỗi API endpoint, áp dụng strict validation theo Rule.
"""
from datetime import datetime
from typing import Optional, Dict, List, Generic, TypeVar, Any
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


# ==============================================================================
# DIMENSION SCHEMAS
# ==============================================================================

class TimeTopicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="ID của Topic Time")
    duration: Optional[float] = Field(None, ge=0, description="Thời gian thực hiện (>= 0)")
    baseline_start: Optional[datetime] = Field(None, description="Thời gian bắt đầu cơ sở")
    baseline_end: Optional[datetime] = Field(None, description="Thời gian kết thúc cơ sở")


class CostTopicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="ID của Topic Cost")
    resource_cost: Optional[float] = Field(0.0, ge=0, description="Chi phí biến đổi (nhân công)")
    fixed_cost: Optional[float] = Field(0.0, ge=0, description="Chi phí cố định (vật tư)")
    total_cost: Optional[float] = Field(0.0, ge=0, description="Tổng chi phí (resource + fixed)")


class RiskTopicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="ID của Topic Risk")
    optimistic_time: Optional[float] = Field(None, ge=0)
    pessimistic_time: Optional[float] = Field(None, ge=0)
    variance: Optional[float] = Field(None, ge=0)
    criticality_index: Optional[float] = Field(None, ge=0, le=1)


class ResourceTopicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="ID của Topic Resources")
    resource_demand: Optional[str] = Field(None, description="Chi tiết nhu cầu tài nguyên (JSON/Text)")


# ==============================================================================
# TASK SCHEMAS
# ==============================================================================

class TaskBase(BaseModel):
    task_label: str = Field(..., min_length=1, max_length=50, description="Mã hiệu công việc")
    wbs: Optional[str] = Field(None, max_length=100)
    task_name: Optional[str] = Field(None, max_length=255)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tính năng mở rộng động")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    task_label: Optional[str] = Field(None, min_length=1, max_length=50)
    wbs: Optional[str] = Field(None, max_length=100)
    task_name: Optional[str] = Field(None, max_length=255)
    metadata_json: Optional[Dict[str, Any]] = Field(None)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: int
    project_id: int
    task_label: str
    wbs: Optional[str]
    task_name: Optional[str]
    metadata_json: Optional[Dict[str, Any]]
    
    time_info: Optional[TimeTopicSchema] = None
    cost_info: Optional[CostTopicSchema] = None
    risk_info: Optional[RiskTopicSchema] = None
    resource_info: Optional[ResourceTopicSchema] = None


# ==============================================================================
# CONSTRAINT SCHEMAS (THE 3 AXES)
# ==============================================================================

# Trục 1: Logic
class ConstraintLogicBase(BaseModel):
    predecessor_id: int = Field(..., gt=0)
    successor_id: int = Field(..., gt=0)
    dependency_type: str = Field("FS", min_length=2, max_length=10)
    lag_days: int = Field(0)


class ConstraintLogicResponse(ConstraintLogicBase):
    model_config = ConfigDict(from_attributes=True)
    project_id: int


# Trục 2: Resource
class ConstraintResourceBase(BaseModel):
    resource_name: str = Field(..., max_length=100)
    resource_type: str = Field(..., max_length=50) # Renewable / Consumable
    max_availability: float = Field(..., ge=0)
    cost_per_use: Optional[float] = Field(0, ge=0)
    cost_per_unit: Optional[float] = Field(0, ge=0)


class ConstraintResourceResponse(ConstraintResourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int


# Trục 3: Time (Agenda)
class ConstraintTimeBase(BaseModel):
    weekly_schedule: Dict[str, Any] = Field(..., description="Lịch làm việc chi tiết từng ngày")
    holidays_list: Optional[List[Any]] = Field(default_factory=list)
    overtime_multiplier: Optional[float] = Field(1.5, ge=1.0)


class ConstraintTimeResponse(ConstraintTimeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int


# ==============================================================================
# PROJECT SCHEMAS
# ==============================================================================

class ProjectBase(BaseModel):
    project_name: str = Field(..., min_length=3, max_length=255)
    status: str = Field("Planning", max_length=50)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata động của Project")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, min_length=3, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    metadata_json: Optional[Dict[str, Any]] = Field(None)


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_name: str
    metadata_json: Optional[Dict[str, Any]]
    num_tasks: int
    num_edges: int
    network_density: Optional[float]
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ProjectDetail(ProjectSummary):
    tasks: List[TaskResponse] = Field(default_factory=list)
    constraint_logic: List[ConstraintLogicResponse] = Field(default_factory=list)
    constraint_resources: List[ConstraintResourceResponse] = Field(default_factory=list)
    constraint_time: Optional[ConstraintTimeResponse] = None


# ==============================================================================
# AI SIMULATION SCHEMAS
# ==============================================================================

class AIInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    simulation_run_id: int
    action_type: List[str]
    target_tasks: List[str]
    human_message: Optional[str]
    modifications: Optional[Dict[str, Any]]
    impact: Optional[Dict[str, Any]]
    risk: Optional[Dict[str, Any]]
    created_at: Optional[datetime]


class SimulationCreate(BaseModel):
    ai_weights: Dict = Field(default={"time": 50, "cost": 50})


class SimulationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    ai_weights: Dict
    status: str
    results_summary: Optional[Dict]
    created_at: Optional[datetime]
    insights: List[AIInsightResponse] = Field(default_factory=list)


# ==============================================================================
# COMMON RESPONSES
# ==============================================================================

class APIResponse(BaseModel, Generic[T]):
    success: bool = Field(True)
    message: str = Field("Success")
    data: Optional[T] = Field(None)
    errors: Optional[Any] = Field(None)


class PaginatedResponse(BaseModel, Generic[T]):
    total: int = Field(..., ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    items: List[T] = Field(...)


class HealthCheckResponse(BaseModel):
    status: str = Field("healthy")
    database: str = Field("connected")
    version: str = Field("1.0.0")

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., max_length=255)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    created_at: Optional[datetime]
