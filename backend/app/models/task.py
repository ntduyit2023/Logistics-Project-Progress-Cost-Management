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

    Attributes:
        task_id (str): Khóa chính tham chiếu đến tasks.id.
        resource_id (int): Khóa chính tham chiếu đến project_constraint_resource.id.
        request_quantity (float): Số lượng tài nguyên yêu cầu.
        allocated_quantity (Optional[float]): Số lượng thực tế cấp.
        labor_productivity (Optional[float]): Năng suất lao động.
        equipment_utilization (Optional[float]): Tỷ lệ sử dụng thiết bị.
        resource_substitutability (Optional[int]): Khả năng thay thế.
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
    Bao gồm toàn bộ 60+ tính năng (Features) trải dài qua 7 nhóm (Cost, Risk, HR...).

    Attributes:
        id (str): Khóa chính của Task.
        project_id (int): ID dự án.
        task_name (str): Tên task.
        task_type (Optional[str]): Loại task.
        status (str): Trạng thái.
        base_cost (Optional[float]): Chi phí cơ sở.
        total_cost (Optional[float]): Tổng chi phí.
        risk_factor (Optional[float]): Yếu tố rủi ro.
        baseline_start (Optional[datetime]): Ngày bắt đầu.
        type (Optional[str]): Phân loại.
        
        # Hub Time Components
        duration_months (Optional[float]): Thời lượng (tháng).
        duration_weeks (Optional[float]): Thời lượng (tuần).
        duration_days (Optional[float]): Thời lượng (ngày).
        duration_hours (Optional[float]): Thời lượng (giờ).
        calendar_type (Optional[str]): Loại lịch.
        
        # G1: Direct Costs
        internal_labor_cost (Optional[float]): Chi phí nhân công nội bộ.
        overtime_cost (Optional[float]): Chi phí làm thêm.
        equipment_fuel_cost (Optional[float]): Chi phí nhiên liệu/thiết bị.
        qa_qc_cost (Optional[float]): Chi phí QA/QC.
        material_cost (Optional[float]): Chi phí vật tư.
        outsourcing_cost (Optional[float]): Chi phí thầu phụ.
        
        # G2: Indirect Costs
        training_cost (Optional[float]): Chi phí đào tạo.
        facility_rent (Optional[float]): Chi phí thuê bãi.
        communication_cost (Optional[float]): Chi phí viễn thông.
        utilities_cost (Optional[float]): Chi phí điện nước.
        
        # G4: Contractual Costs
        insurance_cost (Optional[float]): Chi phí bảo hiểm.
        licensing_cost (Optional[float]): Phí giấy phép.
        warranty_cost (Optional[float]): Chi phí bảo hành.
        
        # G5: Risk Costs
        complexity (Optional[float]): Độ phức tạp.
        weather_contingency (Optional[float]): Dự phòng thời tiết.
        general_contingency (Optional[float]): Dự phòng chung.
        rework_risk (Optional[float]): Rủi ro làm lại.
        
        # G6: Logistics Costs
        holding_cost (Optional[float]): Chi phí tồn kho.
        international_freight (Optional[float]): Cước phí quốc tế.
        handling_cost (Optional[float]): Chi phí bốc dỡ.
        reverse_logistics (Optional[float]): Chi phí thu hồi.
        defect_cost (Optional[float]): Chi phí lỗi hỏng.
        
        # G7: Time & Schedule
        overtime_hours (Optional[float]): Giờ làm thêm.
        lag_time (Optional[float]): Thời gian trễ.
    """
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    task_name: Mapped[str] = mapped_column(String(255))
    task_type: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="Pending")
    
    base_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0.0)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0.0)
    risk_factor: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), default=1.0)
    
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
    overtime_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    equipment_fuel_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    qa_qc_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    material_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    outsourcing_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    
    # G2: Indirect Costs
    training_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    facility_rent: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    communication_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    utilities_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    
    # G4: Contractual
    insurance_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    licensing_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    warranty_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    
    # G5: Risk Coefficients
    complexity: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    weather_contingency: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    general_contingency: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    rework_risk: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    
    # G6: Logistics
    holding_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    international_freight: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    handling_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    reverse_logistics: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    defect_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    
    # G7: Time Components
    overtime_hours: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    lag_time: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    
    # Metadata JSON cho AI Computed Data
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    # Quan hệ
    project: Mapped["AppProject"] = relationship(back_populates="tasks")
    resources: Mapped[List["TaskResource"]] = relationship(back_populates="task", cascade="all, delete-orphan")
