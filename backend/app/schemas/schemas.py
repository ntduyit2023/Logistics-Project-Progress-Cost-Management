"""
GLPO Backend - Pydantic Schemas (API Contracts)
Định nghĩa cấu trúc dữ liệu vào/ra cho mỗi API endpoint, áp dụng strict validation theo Rule.
"""
from datetime import datetime
from typing import Optional, Dict, List, Generic, TypeVar, Any
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


# ==============================================================================
# DIMENSION SCHEMAS (Read-only, nhúng vào Task response)
# ==============================================================================

class TimeTopicSchema(BaseModel):
    """
    Thông tin thời gian của một Task.

    Attributes:
        id (int): ID của Topic Time.
        duration (Optional[float]): Thời lượng thực hiện công việc (>= 0).
        baseline_start (Optional[datetime]): Thời gian bắt đầu cơ sở.
        baseline_end (Optional[datetime]): Thời gian kết thúc cơ sở.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID của Topic Time")
    duration: Optional[float] = Field(None, ge=0, description="Thời gian thực hiện (>= 0)")
    baseline_start: Optional[datetime] = Field(None, description="Thời gian bắt đầu cơ sở")
    baseline_end: Optional[datetime] = Field(None, description="Thời gian kết thúc cơ sở")


class CostTopicSchema(BaseModel):
    """
    Thông tin chi phí tĩnh của một Task.

    Attributes:
        id (int): ID của Topic Cost.
        total_cost (Optional[float]): Tổng chi phí ước tính (>= 0).
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID của Topic Cost")
    total_cost: Optional[float] = Field(0.0, ge=0, description="Tổng chi phí ước tính (>= 0)")


class RiskTopicSchema(BaseModel):
    """
    Thông tin rủi ro của một Task tính theo phương pháp PERT.

    Attributes:
        id (int): ID của Topic Risk.
        optimistic_time (Optional[float]): Thời gian hoàn thành lạc quan nhất (>= 0).
        pessimistic_time (Optional[float]): Thời gian hoàn thành bi quan nhất (>= 0).
        variance (Optional[float]): Phương sai rủi ro tính từ PERT.
        criticality_index (Optional[float]): Chỉ số độ tới hạn, biểu thị % khả năng nằm trên đường găng (0-1).
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID của Topic Risk")
    optimistic_time: Optional[float] = Field(None, ge=0, description="Thời gian lạc quan nhất")
    pessimistic_time: Optional[float] = Field(None, ge=0, description="Thời gian bi quan nhất")
    variance: Optional[float] = Field(None, ge=0, description="Phương sai rủi ro")
    criticality_index: Optional[float] = Field(None, ge=0, le=1, description="Chỉ số quan trọng (0-1)")


class ResourceTopicSchema(BaseModel):
    """
    Thông tin về nhu cầu tài nguyên của một Task.

    Attributes:
        id (int): ID của Topic Resources.
        resource_demand (Optional[str]): Nội dung chi tiết về nhân công, vật tư (Text/JSON).
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID của Topic Resources")
    resource_demand: Optional[str] = Field(None, description="Chi tiết nhu cầu tài nguyên (JSON/Text)")


# ==============================================================================
# TASK SCHEMAS
# ==============================================================================

class TaskBase(BaseModel):
    """
    Các trường dữ liệu chung để định nghĩa một Công việc (Task).

    Attributes:
        task_label (str): Mã hiệu ngắn của công việc (Vd: A1).
        wbs (Optional[str]): Mã Work Breakdown Structure (Vd: 1.1.2).
        task_name (Optional[str]): Tên đầy đủ của công việc.
        duration (Optional[float]): Thời lượng dự kiến.
        baseline_start (Optional[datetime]): Ngày bắt đầu.
        baseline_end (Optional[datetime]): Ngày kết thúc.
        total_cost (Optional[float]): Chi phí dự kiến.
        optimistic_time (Optional[float]): Thời gian lạc quan để phòng rủi ro.
        pessimistic_time (Optional[float]): Thời gian bi quan để phòng rủi ro.
        resource_demand (Optional[str]): Yêu cầu tài nguyên.
    """
    task_label: str = Field(..., min_length=1, max_length=50, description="Mã hiệu công việc", examples=["A1"])
    wbs: Optional[str] = Field(None, max_length=100, description="Cấu trúc phân chia công việc (WBS)", examples=["1.1.2"])
    task_name: Optional[str] = Field(None, max_length=255, description="Tên chi tiết công việc", examples=["Đào móng công trình"])
    duration: Optional[float] = Field(None, ge=0, description="Thời lượng công việc", examples=[14.0])
    baseline_start: Optional[datetime] = Field(None, description="Ngày bắt đầu")
    baseline_end: Optional[datetime] = Field(None, description="Ngày kết thúc")
    total_cost: Optional[float] = Field(None, ge=0, description="Chi phí dự kiến", examples=[50000.0])
    optimistic_time: Optional[float] = Field(None, ge=0, description="Thời gian lạc quan")
    pessimistic_time: Optional[float] = Field(None, ge=0, description="Thời gian bi quan")
    resource_demand: Optional[str] = Field(None, description="Nhu cầu tài nguyên")


class TaskCreate(TaskBase):
    """
    Schema nhận dữ liệu từ Frontend khi tạo Task mới.

    Attributes:
        (Tương tự như TaskBase)
    """
    pass


class TaskUpdate(BaseModel):
    """
    Schema nhận dữ liệu từ Frontend khi cập nhật Task.
    Tất cả các trường đều là Optional để hỗ trợ cập nhật một phần (PATCH).

    Attributes:
        (Tương tự TaskBase nhưng mọi trường đều Optional)
    """
    task_label: Optional[str] = Field(None, min_length=1, max_length=50, description="Mã hiệu công việc")
    wbs: Optional[str] = Field(None, max_length=100, description="WBS")
    task_name: Optional[str] = Field(None, max_length=255, description="Tên công việc")
    duration: Optional[float] = Field(None, ge=0, description="Thời lượng")
    baseline_start: Optional[datetime] = Field(None, description="Ngày bắt đầu")
    baseline_end: Optional[datetime] = Field(None, description="Ngày kết thúc")
    total_cost: Optional[float] = Field(None, ge=0, description="Chi phí")
    optimistic_time: Optional[float] = Field(None, ge=0, description="Thời gian lạc quan")
    pessimistic_time: Optional[float] = Field(None, ge=0, description="Thời gian bi quan")
    resource_demand: Optional[str] = Field(None, description="Nhu cầu tài nguyên")


class TaskResponse(BaseModel):
    """
    Schema đại diện cho một Task khi trả về cho Frontend.
    Chứa toàn bộ thông tin lõi và nhúng kèm dữ liệu từ các Dimensions.

    Attributes:
        task_id (int): ID của Task.
        project_id (int): ID của Project chứa Task.
        task_label (str): Mã hiệu.
        wbs (Optional[str]): Cấu trúc phân việc.
        task_name (Optional[str]): Tên công việc.
        time_info (Optional[TimeTopicSchema]): Đối tượng chứa thông tin thời gian.
        cost_info (Optional[CostTopicSchema]): Đối tượng chứa thông tin chi phí.
        risk_info (Optional[RiskTopicSchema]): Đối tượng chứa thông tin rủi ro.
        resource_info (Optional[ResourceTopicSchema]): Đối tượng chứa thông tin tài nguyên.
    """
    model_config = ConfigDict(from_attributes=True)

    task_id: int = Field(..., description="ID của Task")
    project_id: int = Field(..., description="ID của Project")
    task_label: str = Field(..., description="Mã hiệu công việc")
    wbs: Optional[str] = Field(None, description="WBS")
    task_name: Optional[str] = Field(None, description="Tên công việc")
    
    time_info: Optional[TimeTopicSchema] = Field(None, description="Dữ liệu chiều Thời gian")
    cost_info: Optional[CostTopicSchema] = Field(None, description="Dữ liệu chiều Chi phí")
    risk_info: Optional[RiskTopicSchema] = Field(None, description="Dữ liệu chiều Rủi ro")
    resource_info: Optional[ResourceTopicSchema] = Field(None, description="Dữ liệu chiều Tài nguyên")


# ==============================================================================
# DEPENDENCY (EDGE) SCHEMAS
# ==============================================================================

class DependencyBase(BaseModel):
    """
    Schema định nghĩa cạnh liên kết giữa 2 công việc.

    Attributes:
        predecessor_id (int): ID của công việc đứng trước.
        successor_id (int): ID của công việc đứng sau.
        dependency_type (str): Kiểu liên kết (FS, SS, FF, SF).
        lag_days (int): Số ngày trễ.
    """
    predecessor_id: int = Field(..., gt=0, description="ID của công việc đứng trước", examples=[1])
    successor_id: int = Field(..., gt=0, description="ID của công việc đứng sau", examples=[2])
    dependency_type: str = Field("FS", min_length=2, max_length=10, description="Loại liên kết (FS, SS, FF, SF)", examples=["FS"])
    lag_days: int = Field(0, description="Độ trễ (ngày)", examples=[0])


class DependencyCreate(DependencyBase):
    """
    Schema để tạo một liên kết mới.
    """
    pass


class DependencyResponse(DependencyBase):
    """
    Schema trả về thông tin của một liên kết đồ thị mạng lưới.

    Attributes:
        project_id (int): ID của dự án chứa liên kết này.
        (Kế thừa các trường từ DependencyBase).
    """
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="ID của Project chứa liên kết này")


# ==============================================================================
# PROJECT SCHEMAS
# ==============================================================================

class ProjectBase(BaseModel):
    """
    Các trường dữ liệu chung để định nghĩa một Dự án.

    Attributes:
        project_name (str): Tên hiển thị dự án.
        working_hours (Optional[Dict]): Lịch làm việc trong ngày.
        working_days (Optional[List]): Lịch làm việc trong tuần.
        status (str): Trạng thái quản lý dự án.
    """
    project_name: str = Field(..., min_length=3, max_length=255, description="Tên dự án", examples=["Xây dựng cầu Cần Thơ"])
    working_hours: Optional[List] = Field(None, description="Khung giờ làm việc (JSON)")
    working_days: Optional[List] = Field(None, description="Các ngày làm việc trong tuần (JSON)")
    status: str = Field("Planning", max_length=50, description="Trạng thái dự án", examples=["Planning", "Executing", "Closed"])


class ProjectCreate(ProjectBase):
    """
    Schema tạo Dự án mới.
    """
    pass


class ProjectUpdate(BaseModel):
    """
    Schema cập nhật Dự án. Hỗ trợ PATCH.

    Attributes:
        (Tương tự ProjectBase nhưng mọi trường là Optional)
    """
    project_name: Optional[str] = Field(None, min_length=3, max_length=255, description="Tên dự án")
    working_hours: Optional[List] = Field(None, description="Khung giờ làm việc")
    working_days: Optional[List] = Field(None, description="Ngày làm việc")
    status: Optional[str] = Field(None, max_length=50, description="Trạng thái", examples=["Planning"])


class ProjectSummary(BaseModel):
    """
    Schema trả về danh sách rút gọn các dự án (Không load Tasks để nhẹ tải).

    Attributes:
        id (int): ID dự án.
        project_name (str): Tên dự án.
        num_tasks (int): Số lượng Task.
        num_edges (int): Số lượng liên kết.
        network_density (Optional[float]): Mật độ liên kết.
        status (str): Trạng thái dự án.
        created_at (Optional[datetime]): Ngày tạo.
        updated_at (Optional[datetime]): Lần cập nhật cuối.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID dự án")
    project_name: str = Field(..., description="Tên dự án")
    num_tasks: int = Field(0, description="Tổng số công việc")
    num_edges: int = Field(0, description="Tổng số liên kết")
    network_density: Optional[float] = Field(0.0, description="Mật độ đồ thị")
    status: str = Field(..., description="Trạng thái dự án")
    created_at: Optional[datetime] = Field(None, description="Ngày tạo")
    updated_at: Optional[datetime] = Field(None, description="Ngày cập nhật")


class ProjectDetail(ProjectSummary):
    """
    Schema trả về Chi tiết Dự án, nhúng thêm toàn bộ Node (Tasks) và Edges (Dependencies).

    Attributes:
        working_hours (Optional[Dict]): Lịch làm việc trong ngày.
        working_days (Optional[List]): Lịch làm việc trong tuần.
        tasks (List[TaskResponse]): Danh sách công việc (Nodes).
        dependencies (List[DependencyResponse]): Danh sách liên kết (Edges).
    """
    working_hours: Optional[List] = Field(None, description="Khung giờ làm việc")
    working_days: Optional[List] = Field(None, description="Ngày làm việc")
    tasks: List[TaskResponse] = Field(default_factory=list, description="Danh sách các công việc")
    dependencies: List[DependencyResponse] = Field(default_factory=list, description="Danh sách các liên kết")


class ProjectGraphResponse(BaseModel):
    """
    Schema đại diện cho Đồ thị mạng lưới (Graph) của Dự án trả về cho Frontend vẽ biểu đồ.

    Attributes:
        project_id (int): ID dự án.
        nodes (List[TaskResponse]): Danh sách các đỉnh (công việc).
        edges (List[DependencyResponse]): Danh sách các cạnh (liên kết).
    """
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="ID của dự án")
    nodes: List[TaskResponse] = Field(default_factory=list, description="Danh sách các đỉnh (Nodes)")
    edges: List[DependencyResponse] = Field(default_factory=list, description="Danh sách các cạnh (Edges)")



# ==============================================================================
# AI SIMULATION SCHEMAS
# ==============================================================================

class SimulationCreate(BaseModel):
    """
    Schema Client gửi yêu cầu chạy Lập lịch AI.

    Attributes:
        ai_weights (Dict): Trọng số đánh đổi giữa Thời gian và Chi phí (Cost vs Time tradeoff).
    """
    ai_weights: Dict = Field(
        default={"time": 50, "cost": 50},
        description="Trọng số ưu tiên Thời gian vs Chi phí (tổng = 100)",
        examples=[{"time": 70, "cost": 30}]
    )


class SimulationResponse(BaseModel):
    """
    Schema trả về trạng thái của một luồng chạy AI mô phỏng.

    Attributes:
        id (int): ID luồng chạy.
        project_id (int): ID dự án liên quan.
        ai_weights (Dict): Trọng số đã sử dụng.
        status (str): Trạng thái của job (Running, Success...).
        results_summary (Optional[Dict]): Tóm tắt điểm số khi thành công.
        created_at (Optional[datetime]): Ngày tạo yêu cầu.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID của Simulation Run")
    project_id: int = Field(..., description="ID dự án")
    ai_weights: Dict = Field(..., description="Trọng số đã áp dụng")
    status: str = Field(..., description="Trạng thái (Running, Success, Failed)")
    results_summary: Optional[Dict] = Field(None, description="Kết quả tối ưu hóa (JSON)")
    created_at: Optional[datetime] = Field(None, description="Ngày tạo")


# ==============================================================================
# COMMON RESPONSES (API WRAPPERS)
# ==============================================================================

class APIResponse(BaseModel, Generic[T]):
    """
    Schema quy chuẩn (Wrapper Envelope) cho mọi API Response gửi về Frontend.

    Attributes:
        success (bool): Trạng thái API (Thành công hay Thất bại).
        message (str): Thông điệp trả về (Vd: "Lấy dữ liệu thành công").
        data (Optional[T]): Dữ liệu trả về (Generic Type).
        errors (Optional[Any]): Chi tiết lỗi nếu có.
    """
    success: bool = Field(True, description="Trạng thái thành công")
    message: str = Field("Success", description="Thông điệp hệ thống")
    data: Optional[T] = Field(None, description="Dữ liệu chính")
    errors: Optional[Any] = Field(None, description="Chi tiết lỗi (nếu có)")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Schema chuẩn hóa trả về danh sách phân trang (Pagination).

    Attributes:
        total (int): Tổng lượng record thực tế trên Database.
        page (int): Chỉ số trang hiện tại đang xem.
        page_size (int): Kích thước một trang (limit).
        items (List): Mảng chứa dữ liệu của trang đó.
    """
    total: int = Field(..., ge=0, description="Tổng số bản ghi có trong DB", examples=[226])
    page: int = Field(1, ge=1, description="Trang hiện tại", examples=[1])
    page_size: int = Field(20, ge=1, le=100, description="Số lượng bản ghi trên một trang", examples=[20])
    items: List[T] = Field(..., description="Danh sách dữ liệu")


class HealthCheckResponse(BaseModel):
    """
    Schema phản hồi từ API Health Check.

    Attributes:
        status (str): Tình trạng hệ thống Backend.
        database (str): Tình trạng đường truyền đến Database.
        version (str): Phiên bản Release hiện tại.
    """
    status: str = Field("healthy", description="Tình trạng service")
    database: str = Field("connected", description="Tình trạng DB")
    version: str = Field("1.0.0", description="Phiên bản API")


# ==============================================================================
# USER SCHEMAS
# ==============================================================================

class UserCreate(BaseModel):
    """
    Schema khi đăng ký User mới.

    Attributes:
        username (str): Tên đăng nhập.
        email (str): Địa chỉ email hợp lệ.
    """
    username: str = Field(..., min_length=3, max_length=100, description="Tên đăng nhập", examples=["nguyenvana"])
    email: str = Field(..., max_length=255, description="Địa chỉ email", examples=["vana@example.com"])


class UserResponse(BaseModel):
    """
    Schema khi trả thông tin User.

    Attributes:
        id (int): ID người dùng.
        username (str): Tên đăng nhập.
        email (str): Địa chỉ email.
        created_at (Optional[datetime]): Ngày tạo tài khoản.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID người dùng")
    username: str = Field(..., description="Tên đăng nhập")
    email: str = Field(..., description="Email")
    created_at: Optional[datetime] = Field(None, description="Ngày tạo")
