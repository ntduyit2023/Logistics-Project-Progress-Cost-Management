from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.task import TaskResponse
from app.schemas.constraint import ConstraintLogicResponse, ConstraintResourceResponse, ConstraintTimeResponse


class ProjectBase(BaseModel):
    project_name: str = Field(..., min_length=3, max_length=255)
    type: Optional[str] = Field(None, max_length=50)
    status: str = Field("Planning", max_length=50)
    base_cost: Optional[float] = Field(0.0)
    total_cost: Optional[float] = Field(0.0)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata động của Project")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, min_length=3, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    metadata_json: Optional[Dict[str, Any]] = Field(None)


class ProjectSummary(BaseModel):
    """
    Schema đại diện cho dữ liệu dự án tóm tắt trả về cho Frontend ở màn hình Dashboard.

    Attributes:
        id (int): Khóa chính của dự án.
        project_name (str): Tên hiển thị của dự án.
        metadata_json (Optional[Dict[str, Any]]): Metadata JSON.
        num_tasks (int): Số lượng tasks.
        num_edges (int): Số lượng edges.
        network_density (Optional[float]): Mật độ mạng lưới đồ thị.
        status (str): Trạng thái (Planning, Executing, Closed).
        type (Optional[str]): Loại dự án (CON, PRO, ITLG).
        base_cost (Optional[float]): Chi phí cơ bản.
        total_cost (Optional[float]): Tổng chi phí.
    """
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_name: str
    metadata_json: Optional[Dict[str, Any]]
    num_tasks: int
    num_edges: int
    network_density: Optional[float]
    type: Optional[str]
    status: str
    base_cost: Optional[float]
    total_cost: Optional[float]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ProjectDetail(ProjectSummary):
    """
    Schema đại diện cho dữ liệu dự án chi tiết, bao gồm cả Tasks và Constraints.

    Attributes:
        tasks (List[TaskResponse]): Danh sách task.
        constraint_logic (List[ConstraintLogicResponse]): Ràng buộc logic (Edges).
        constraint_resources (List[ConstraintResourceResponse]): Ràng buộc tài nguyên.
        constraint_time (Optional[ConstraintTimeResponse]): Ràng buộc thời gian.
    """
    tasks: List[TaskResponse] = Field(default_factory=list)
    constraint_logic: List[ConstraintLogicResponse] = Field(default_factory=list)
    constraint_resources: List[ConstraintResourceResponse] = Field(default_factory=list)
    constraint_time: Optional[ConstraintTimeResponse] = None


class ProjectGraphResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: int
    nodes: List[TaskResponse] = Field(default_factory=list)
    edges: List[ConstraintLogicResponse] = Field(default_factory=list)
