from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator


class TaskBase(BaseModel):
    task_id: Optional[str] = Field(None, max_length=100, description="Mã công việc (ví dụ C2011-07_1). Tự động sinh nếu để trống.")
    task_name: str = Field(..., max_length=255, description="Tên hiển thị công việc")
    baseline_start: Optional[datetime] = Field(None, description="Mốc thời gian bắt đầu thi công (Datetime)")
    duration_hours: float = Field(0.0, ge=0, description="Thời gian thi công thực tế (giờ)")
    total_cost: Optional[float] = Field(0.0, ge=0, description="Tổng chi phí của Task (Tự động cộng dồn hoặc chỉ định)")
    
    # 1. Chi phí Trực tiếp & Vật tư (Nhập tay hoặc tự động)
    labor: Optional[float] = Field(0.0, ge=0, description="Chi phí nhân công (Tự động tính từ Resource hoặc nhập tay)")
    material: Optional[float] = Field(0.0, ge=0, description="Chi phí vật tư/vật liệu")
    equipment: Optional[float] = Field(0.0, ge=0, description="Chi phí ca máy/thiết bị")
    energy: Optional[float] = Field(0.0, ge=0, description="Chi phí nhiên liệu/năng lượng")
    testing_inspection: Optional[float] = Field(0.0, ge=0, description="Chi phí kiểm định/thí nghiệm")
    
    # 2. Chi phí Gián tiếp & Quản lý
    project_management: Optional[float] = Field(0.0, ge=0, description="Chi phí ban quản lý dự án")
    facility: Optional[float] = Field(0.0, ge=0, description="Chi phí lán trại/mặt bằng")
    utilities: Optional[float] = Field(0.0, ge=0, description="Chi phí điện nước thi công")
    communication: Optional[float] = Field(0.0, ge=0, description="Chi phí thông tin liên lạc")
    training: Optional[float] = Field(0.0, ge=0, description="Chi phí đào tạo/an toàn lao động")
    quality_management: Optional[float] = Field(0.0, ge=0, description="Chi phí quản lý chất lượng")
    
    # 3. Chi phí Phụ thuộc Thời gian
    overtime: Optional[float] = Field(0.0, ge=0, description="Chi phí lương tăng ca")
    delay_penalty: Optional[float] = Field(0.0, ge=0, description="Chi phí phạt trễ công việc")
    inventory_holding: Optional[float] = Field(0.0, ge=0, description="Chi phí lưu kho vật tư")
    waiting_cost: Optional[float] = Field(0.0, ge=0, description="Chi phí chờ đợi/tạm dừng")
    idle_resource: Optional[float] = Field(0.0, ge=0, description="Chi phí tài nguyên nhàn rỗi")
    revenue_delay: Optional[float] = Field(0.0, ge=0, description="Chi phí mất doanh thu trễ")
    expediting: Optional[float] = Field(0.0, ge=0, description="Chi phí đẩy nhanh tiến độ")
    
    # 4. Chi phí Rủi ro & Tuân thủ
    insurance: Optional[float] = Field(0.0, ge=0, description="Chi phí bảo hiểm công trình")
    rework: Optional[float] = Field(0.0, ge=0, description="Chi phí làm lại/sửa chữa")
    warranty: Optional[float] = Field(0.0, ge=0, description="Chi phí bảo hành")
    litigation: Optional[float] = Field(0.0, ge=0, description="Chi phí pháp lý/tranh chấp")
    regulatory_compliance: Optional[float] = Field(0.0, ge=0, description="Chi phí tuân thủ quy định")
    contingency_reserve: Optional[float] = Field(0.0, ge=0, description="Dự phòng rủi ro công việc")
    management_reserve: Optional[float] = Field(0.0, ge=0, description="Dự phòng quản lý")
    
    # 5. Chi phí Chuỗi cung ứng & Logistics
    transportation: Optional[float] = Field(0.0, ge=0, description="Chi phí vận chuyển/logistics")
    ordering: Optional[float] = Field(0.0, ge=0, description="Chi phí đặt hàng/procurement")
    packaging: Optional[float] = Field(0.0, ge=0, description="Chi phí đóng gói/bảo quản")
    reverse_logistics: Optional[float] = Field(0.0, ge=0, description="Chi phí logistics ngược")
    customs: Optional[float] = Field(0.0, ge=0, description="Chi phí thủ tục hải quan")
    supplier_coordination: Optional[float] = Field(0.0, ge=0, description="Chi phí phối hợp nhà thầu phụ")
    
    # 6. Chi phí Chiến lược & Tài chính
    opportunity_cost: Optional[float] = Field(0.0, ge=0, description="Chi phí cơ hội")
    capital_cost: Optional[float] = Field(0.0, ge=0, description="Chi phí vốn")
    financing_cost: Optional[float] = Field(0.0, ge=0, description="Chi phí lãi vay/tài chính")
    npv_loss: Optional[float] = Field(0.0, ge=0, description="Tổn thất NPV")
    esg_cost: Optional[float] = Field(0.0, ge=0, description="Chi phí môi trường/ESG")
    carbon_tax: Optional[float] = Field(0.0, ge=0, description="Thuế carbon")
    reputation_cost: Optional[float] = Field(0.0, ge=0, description="Chi phí rủi ro uy tín")

    cost_features: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata dictionary chi phí")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    task_id: Optional[str] = Field(None, max_length=100)
    task_name: Optional[str] = Field(None, max_length=255)
    baseline_start: Optional[datetime] = Field(None)
    duration_hours: Optional[float] = Field(None, ge=0)
    total_cost: Optional[float] = Field(None, ge=0)
    
    labor: Optional[float] = Field(None, ge=0)
    material: Optional[float] = Field(None, ge=0)
    equipment: Optional[float] = Field(None, ge=0)
    energy: Optional[float] = Field(None, ge=0)
    testing_inspection: Optional[float] = Field(None, ge=0)
    project_management: Optional[float] = Field(None, ge=0)
    facility: Optional[float] = Field(None, ge=0)
    utilities: Optional[float] = Field(None, ge=0)
    communication: Optional[float] = Field(None, ge=0)
    training: Optional[float] = Field(None, ge=0)
    quality_management: Optional[float] = Field(None, ge=0)
    overtime: Optional[float] = Field(None, ge=0)
    delay_penalty: Optional[float] = Field(None, ge=0)
    inventory_holding: Optional[float] = Field(None, ge=0)
    waiting_cost: Optional[float] = Field(None, ge=0)
    idle_resource: Optional[float] = Field(None, ge=0)
    revenue_delay: Optional[float] = Field(None, ge=0)
    expediting: Optional[float] = Field(None, ge=0)
    insurance: Optional[float] = Field(None, ge=0)
    rework: Optional[float] = Field(None, ge=0)
    warranty: Optional[float] = Field(None, ge=0)
    litigation: Optional[float] = Field(None, ge=0)
    regulatory_compliance: Optional[float] = Field(None, ge=0)
    contingency_reserve: Optional[float] = Field(None, ge=0)
    management_reserve: Optional[float] = Field(None, ge=0)
    transportation: Optional[float] = Field(None, ge=0)
    ordering: Optional[float] = Field(None, ge=0)
    packaging: Optional[float] = Field(None, ge=0)
    reverse_logistics: Optional[float] = Field(None, ge=0)
    customs: Optional[float] = Field(None, ge=0)
    supplier_coordination: Optional[float] = Field(None, ge=0)
    opportunity_cost: Optional[float] = Field(None, ge=0)
    capital_cost: Optional[float] = Field(None, ge=0)
    financing_cost: Optional[float] = Field(None, ge=0)
    npv_loss: Optional[float] = Field(None, ge=0)
    esg_cost: Optional[float] = Field(None, ge=0)
    carbon_tax: Optional[float] = Field(None, ge=0)
    reputation_cost: Optional[float] = Field(None, ge=0)
    
    cost_features: Optional[Dict[str, Any]] = Field(None)


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    task_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def populate_costs_from_cost_features(cls, data: Any) -> Any:
        """
        Tự động bung 38 chi phí từ cost_features JSONB ra các thuộc tính trực tiếp nếu chưa có
        """
        if hasattr(data, 'cost_features') and isinstance(data.cost_features, dict):
            cf = data.cost_features
            for k, v in cf.items():
                if not hasattr(data, k) or getattr(data, k, None) is None:
                    try:
                        setattr(data, k, float(v or 0.0))
                    except Exception:
                        pass
        elif isinstance(data, dict) and 'cost_features' in data and isinstance(data['cost_features'], dict):
            cf = data['cost_features']
            for k, v in cf.items():
                if k not in data or data[k] is None:
                    try:
                        data[k] = float(v or 0.0)
                    except Exception:
                        pass
        return data


# --- Task Resource Assignment ---

class TaskResourceCreate(BaseModel):
    resource_id: str = Field(..., description="Mã tài nguyên (ví dụ R1)")
    request_quantity: float = Field(1.0, ge=0, description="Số lượng tài nguyên yêu cầu")


class TaskResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    project_id: int
    task_id: str
    resource_id: str
    resource_name: Optional[str] = None
    resource_type: Optional[str] = None
    request_quantity: float = 1.0
    unit_cost: Optional[float] = 0.0
