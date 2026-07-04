from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

# Trục 1: Logic
class ConstraintLogicBase(BaseModel):
    predecessor_id: str = Field(..., description="ID của Task đứng trước")
    successor_id: str = Field(..., description="ID của Task đứng sau")
    dependency_type: str = Field("FS", min_length=2, max_length=10)
    lag_months: Optional[float] = Field(0)
    lag_weeks: Optional[float] = Field(0)
    lag_days: Optional[float] = Field(0)
    lag_hours: Optional[float] = Field(0)


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


# Trục 3: Time
class ConstraintTimeBase(BaseModel):
    weekly_schedule: Dict[str, Any] = Field(..., description="Lịch làm việc chi tiết từng ngày")
    holidays_list: Optional[List[Any]] = Field(default_factory=list)
    overtime_multiplier: Optional[float] = Field(1.5, ge=1.0)


class ConstraintTimeResponse(ConstraintTimeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
