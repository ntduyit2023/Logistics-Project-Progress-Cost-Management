"""
GLPO Backend - SQLAlchemy ORM Models
Sử dụng SQLAlchemy 2.0 Type Hinting (Mapped, mapped_column) cho Type Safety tuyệt đối.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Numeric, Text, Boolean,
    ForeignKey, DateTime, JSON, Index
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


# ==============================================================================
# 1. APPLICATION MANAGEMENT LAYER
# ==============================================================================

class User(Base):
    """
    Bảng lưu trữ thông tin người dùng quản lý dự án.

    Attributes:
        id (int): Khóa chính tự tăng.
        username (str): Tên đăng nhập duy nhất.
        email (str): Địa chỉ email duy nhất.
        created_at (datetime): Thời điểm tạo tài khoản.
        projects (List[AppProject]): Danh sách dự án thuộc về người dùng (Relationship).
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    projects: Mapped[List["AppProject"]] = relationship(back_populates="owner")


class AppProject(Base):
    """
    Bảng lưu trữ thông tin tổng quan của một dự án (Application Layer).

    Attributes:
        id (int): Khóa chính dự án.
        user_id (Optional[int]): ID người dùng sở hữu (Foreign Key).
        project_name (str): Tên hiển thị của dự án.
        working_hours (Optional[Dict[str, Any]]): Khung giờ làm việc lưu dạng JSON.
        working_days (Optional[List[Any]]): Các ngày làm việc trong tuần lưu dạng JSON.
        num_tasks (int): Tổng số lượng công việc (cache).
        num_edges (int): Tổng số liên kết giữa các công việc (cache).
        network_density (float): Mật độ đồ thị mạng lưới.
        status (str): Trạng thái hiện tại của dự án (Planning, Executing, Closed).
        created_at (datetime): Ngày tạo dự án.
        updated_at (datetime): Ngày cập nhật gần nhất.
        owner (Optional[User]): Đối tượng người dùng sở hữu (Relationship).
        tasks (List[FactTask]): Danh sách công việc thuộc dự án (Relationship).
        simulation_runs (List[AISimulationRun]): Danh sách các lần chạy AI mô phỏng (Relationship).
        baselines (List[ProjectBaseline]): Danh sách đường cơ sở của dự án (Relationship).
    """
    __tablename__ = "app_projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    project_name: Mapped[str] = mapped_column(String(255))
    search_vector = mapped_column(TSVECTOR)
    working_hours: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    working_days: Mapped[Optional[List[Any]]] = mapped_column(JSON)
    num_tasks: Mapped[int] = mapped_column(default=0)
    num_edges: Mapped[int] = mapped_column(default=0)
    network_density: Mapped[float] = mapped_column(Numeric(5, 4), default=0)
    status: Mapped[str] = mapped_column(String(50), default="Planning")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped[Optional["User"]] = relationship(back_populates="projects")
    tasks: Mapped[List["FactTask"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    simulation_runs: Mapped[List["AISimulationRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    baselines: Mapped[List["ProjectBaseline"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class AISimulationRun(Base):
    """
    Lưu trữ lịch sử và kết quả các lần chạy AI lập lịch (RCPSP).

    Attributes:
        id (int): Khóa chính phiên chạy AI.
        project_id (int): ID dự án liên kết.
        ai_weights (Dict[str, Any]): Trọng số ưu tiên (Time/Cost) dạng JSON.
        status (str): Trạng thái quá trình mô phỏng (Running, Success, Failed).
        results_summary (Optional[Dict[str, Any]]): Tóm tắt kết quả sau khi AI giải quyết (JSON).
        created_at (datetime): Thời điểm bắt đầu chạy.
        project (AppProject): Đối tượng dự án liên kết (Relationship).
    """
    __tablename__ = "ai_simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    ai_weights: Mapped[Dict[str, Any]] = mapped_column(JSON, default={"time": 50, "cost": 50})
    status: Mapped[str] = mapped_column(String(50), default="Running")
    results_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["AppProject"] = relationship(back_populates="simulation_runs")


class ProjectBaseline(Base):
    """
    Bảng lưu đường cơ sở (Baseline) của dự án sau khi chốt lịch trình.

    Attributes:
        id (int): Khóa chính Baseline.
        project_id (int): ID dự án.
        simulation_run_id (Optional[int]): ID của phiên chạy AI tạo ra baseline này.
        is_active (bool): Cờ đánh dấu baseline hiện hành đang được sử dụng.
        created_at (datetime): Ngày tạo baseline.
        project (AppProject): Đối tượng dự án (Relationship).
    """
    __tablename__ = "project_baselines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    simulation_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_simulation_runs.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["AppProject"] = relationship(back_populates="baselines")


# ==============================================================================
# 2. DIMENSION TOPICS (Snowflake)
# ==============================================================================

class DimTopicTime(Base):
    """
    Bảng chiều không gian lưu trữ dữ liệu thời gian của công việc.

    Attributes:
        id (int): Khóa chính Dimension.
        duration (Optional[float]): Thời lượng công việc (ngày/giờ).
        baseline_start (Optional[datetime]): Thời gian bắt đầu dự kiến.
        baseline_end (Optional[datetime]): Thời gian kết thúc dự kiến.
    """
    __tablename__ = "dim_topic_time"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    duration: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))
    baseline_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    baseline_end: Mapped[Optional[datetime]] = mapped_column(DateTime)


class DimTopicCost(Base):
    """
    Bảng chiều không gian lưu trữ chi phí của công việc.

    Attributes:
        id (int): Khóa chính Dimension.
        total_cost (Optional[float]): Tổng chi phí tĩnh của công việc.
    """
    __tablename__ = "dim_topic_cost"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0)


class DimTopicRisk(Base):
    """
    Bảng chiều không gian đánh giá rủi ro theo chuẩn PERT.

    Attributes:
        id (int): Khóa chính Dimension.
        optimistic_time (Optional[float]): Thời gian lạc quan nhất.
        pessimistic_time (Optional[float]): Thời gian bi quan nhất.
        variance (Optional[float]): Phương sai rủi ro tính toán từ PERT.
        criticality_index (Optional[float]): Chỉ số độ tới hạn (từ 0 đến 1).
    """
    __tablename__ = "dim_topic_risk"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    optimistic_time: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))
    pessimistic_time: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))
    variance: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    criticality_index: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))


class DimTopicResources(Base):
    """
    Bảng chiều không gian lưu trữ yêu cầu tài nguyên (nhân công, máy móc).

    Attributes:
        id (int): Khóa chính Dimension.
        resource_demand (Optional[str]): Chuỗi mô tả nhu cầu tài nguyên.
    """
    __tablename__ = "dim_topic_resources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resource_demand: Mapped[Optional[str]] = mapped_column(Text)


# ==============================================================================
# 3. CORE FACT & GRAPH TABLES
# ==============================================================================

class FactTask(Base):
    """
    Bảng trung tâm Fact chứa thông tin chính của công việc và liên kết Dimensions.

    Attributes:
        task_id (int): Khóa chính công việc.
        project_id (int): ID dự án chứa công việc này.
        task_label (str): Mã hiệu ngắn của công việc (Vd: A, B1).
        wbs (Optional[str]): Cấu trúc phân tách công việc (Vd: 1.1.2).
        task_name (Optional[str]): Tên đầy đủ của công việc.
        topic_time_id (Optional[int]): Khóa ngoại tới bảng DimTopicTime.
        topic_cost_id (Optional[int]): Khóa ngoại tới bảng DimTopicCost.
        topic_risk_id (Optional[int]): Khóa ngoại tới bảng DimTopicRisk.
        topic_resources_id (Optional[int]): Khóa ngoại tới bảng DimTopicResources.
        project (AppProject): Relationship trỏ về Dự án mẹ.
        time_info (Optional[DimTopicTime]): Relationship Eager-load dữ liệu Thời gian.
        cost_info (Optional[DimTopicCost]): Relationship Eager-load dữ liệu Chi phí.
        risk_info (Optional[DimTopicRisk]): Relationship Eager-load dữ liệu Rủi ro.
        resource_info (Optional[DimTopicResources]): Relationship Eager-load dữ liệu Tài nguyên.
    """
    __tablename__ = "fact_tasks"

    task_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    task_label: Mapped[str] = mapped_column(String(50))
    wbs: Mapped[Optional[str]] = mapped_column(String(100))
    task_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    topic_time_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dim_topic_time.id", ondelete="SET NULL"))
    topic_cost_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dim_topic_cost.id", ondelete="SET NULL"))
    topic_risk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dim_topic_risk.id", ondelete="SET NULL"))
    topic_resources_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dim_topic_resources.id", ondelete="SET NULL"))

    project: Mapped["AppProject"] = relationship(back_populates="tasks")
    time_info: Mapped[Optional["DimTopicTime"]] = relationship(lazy="joined")
    cost_info: Mapped[Optional["DimTopicCost"]] = relationship(lazy="joined")
    risk_info: Mapped[Optional["DimTopicRisk"]] = relationship(lazy="joined")
    resource_info: Mapped[Optional["DimTopicResources"]] = relationship(lazy="joined")


class BridgeTaskDependency(Base):
    """
    Bảng lưu liên kết cạnh của đồ thị mạng lưới (Task Dependencies).

    Attributes:
        predecessor_id (int): ID công việc đứng trước (Node nguồn).
        successor_id (int): ID công việc đứng sau (Node đích).
        project_id (int): ID dự án chứa liên kết này.
        dependency_type (str): Kiểu liên kết (FS, SS, FF, SF). Mặc định là FS.
        lag_days (int): Số ngày trễ giữa 2 công việc.
    """
    __tablename__ = "bridge_task_dependencies"

    predecessor_id: Mapped[int] = mapped_column(ForeignKey("fact_tasks.task_id", ondelete="CASCADE"), primary_key=True)
    successor_id: Mapped[int] = mapped_column(ForeignKey("fact_tasks.task_id", ondelete="CASCADE"), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("app_projects.id", ondelete="CASCADE"))
    dependency_type: Mapped[str] = mapped_column(String(10), default="FS")
    lag_days: Mapped[int] = mapped_column(default=0)
