from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

# Trục 1: Logic (logic.csv)
class ConstraintLogicBase(BaseModel):
    predecessor_id: str = Field(..., description="ID của Task đứng trước")
    successor_id: str = Field(..., description="ID của Task đứng sau")
    dependency_type: str = Field("FS", min_length=2, max_length=10)
    lag_hours: Optional[float] = Field(0.0, description="Số giờ độ trễ (lag_hours)")


class ConstraintLogicResponse(ConstraintLogicBase):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    project_id: int


# Trục 2: Resource (resources.csv)
class ConstraintResourceBase(BaseModel):
    resource_id: str = Field(..., max_length=100, description="Mã tài nguyên (ví dụ R1)")
    name: Optional[str] = Field(None, max_length=255)
    type: str = Field("Human", max_length=50, description="Loại tài nguyên: Human / Machine")
    max_availability: float = Field(1.0, ge=0)
    unit_cost: float = Field(0.0, ge=0)
    energy: float = Field(0.0, ge=0)
    overtime_multi: float = Field(1.5, ge=1.0)
    max_overtime_per_day: float = Field(4.0, ge=0)


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
