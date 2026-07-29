from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.task import TaskResponse
from app.schemas.constraint import ConstraintLogicResponse, ConstraintResourceResponse, ConstraintTimeResponse


class ProjectBase(BaseModel):
    project_code: str = Field(..., min_length=2, max_length=100, description="Mã dự án (ví dụ: C2011-07)")
    project_name: str = Field(..., min_length=3, max_length=255, description="Tên hiển thị dự án")
    project_type: Optional[str] = Field("CON", max_length=50, description="CON, ITLG hoặc PRO")
    status: str = Field("Planning", max_length=50, description="Planning, Executing, Closed")
    
    target_deadline: Optional[datetime] = Field(None, description="Hạn chót hoàn thành (Datetime)")
    penalty_per_day: Optional[float] = Field(0.0, ge=0, description="Phạt trễ ($/ngày)")
    bonus_per_day: Optional[float] = Field(0.0, ge=0, description="Thưởng làm sớm ($/ngày)")
    
    base_cost: Optional[float] = Field(0.0, ge=0, description="Tự động tính từ các Tasks (Mặc định: 0.0)")
    total_cost: Optional[float] = Field(0.0, ge=0, description="Tự động tính từ AI/Solver (Mặc định: 0.0)")
    
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata động")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_code: Optional[str] = Field(None, min_length=2, max_length=100)
    project_name: Optional[str] = Field(None, min_length=3, max_length=255)
    project_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    
    target_deadline: Optional[datetime] = Field(None)
    penalty_per_day: Optional[float] = Field(None, ge=0)
    bonus_per_day: Optional[float] = Field(None, ge=0)
    
    base_cost: Optional[float] = Field(None, ge=0)
    total_cost: Optional[float] = Field(None, ge=0)
    metadata_json: Optional[Dict[str, Any]] = Field(None)


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_code: str
    project_name: str
    project_type: Optional[str] = "CON"
    status: str = "Planning"
    
    target_deadline: Optional[datetime] = None
    penalty_per_day: Optional[float] = 0.0
    bonus_per_day: Optional[float] = 0.0
    
    base_cost: Optional[float] = 0.0
    total_cost: Optional[float] = 0.0
    num_tasks: int = 0
    num_edges: int = 0
    network_density: Optional[float] = 0.0
    
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectDetail(ProjectSummary):
    tasks: List[TaskResponse] = Field(default_factory=list)
    constraint_logic: List[ConstraintLogicResponse] = Field(default_factory=list)
    constraint_resources: List[ConstraintResourceResponse] = Field(default_factory=list)
    constraint_time: Optional[ConstraintTimeResponse] = None


class ProjectGraphResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: int
    nodes: List[TaskResponse] = Field(default_factory=list)
    edges: List[ConstraintLogicResponse] = Field(default_factory=list)
