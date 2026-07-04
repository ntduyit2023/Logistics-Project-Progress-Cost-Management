from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """
    Schema bao bọc mọi Response trả về từ API.

    Attributes:
        success (bool): Trạng thái thành công/thất bại.
        message (str): Thông báo từ hệ thống.
        data (Optional[T]): Payload dữ liệu thực tế.
        errors (Optional[Any]): Chi tiết lỗi nếu có.
    """
    success: bool = Field(True)
    message: str = Field("Success")
    data: Optional[T] = Field(None)
    errors: Optional[Any] = Field(None)


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Schema cho dữ liệu phân trang.

    Attributes:
        total (int): Tổng số bản ghi.
        page (int): Trang hiện tại.
        page_size (int): Kích thước một trang.
        items (List[T]): Danh sách dữ liệu của trang.
    """
    total: int = Field(..., ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    total_pages: Optional[int] = Field(None)
    items: List[T] = Field(...)


class HealthCheckResponse(BaseModel):
    status: str = Field("healthy")
    database: str = Field("connected")
    version: str = Field("1.0.0")
