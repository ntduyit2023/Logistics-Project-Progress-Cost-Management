from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.task import TaskResponse
from app.schemas.constraint import ConstraintLogicResponse, ConstraintResourceResponse, ConstraintTimeResponse


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


class ProjectGraphResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: int
    nodes: List[TaskResponse] = Field(default_factory=list)
    edges: List[ConstraintLogicResponse] = Field(default_factory=list)
