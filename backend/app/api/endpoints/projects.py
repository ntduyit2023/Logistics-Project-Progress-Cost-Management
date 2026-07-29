"""
GLPO Backend - Projects API Endpoints
Chứa các API xử lý vòng đời của một Dự án (Tạo, Sửa, Xóa, Lấy Graph).
"""
import json
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import (
    ProjectGraphResponse, APIResponse, PaginatedResponse, ProjectSummary, ProjectDetail,
    ProjectCreate, ProjectUpdate
)
from app.services import project_service
from app.services.ai_runner import run_simulation_background, simulation_event_manager

router = APIRouter()

# ==============================================================================
# QUERIES (GET)
# ==============================================================================

@router.get("", response_model=APIResponse[PaginatedResponse[ProjectSummary]], summary="Danh sách Dự án")
async def get_projects_api(
    q: Optional[str] = Query(None, description="Từ khóa tìm kiếm theo Tên hoặc Mã dự án"),
    project_type: Optional[str] = Query(None, description="Lọc theo loại hình dự án (ví dụ CON, ITLG, PRO)"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái (ví dụ Planning, Executing, Closed)"),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(20, ge=1, le=100, description="Kích thước trang"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[PaginatedResponse[ProjectSummary]]:
    """
    Lấy danh sách các Dự án, hỗ trợ Full-Text Search, Lọc theo Loại hình & Trạng thái, và Phân trang.
    """
    data = await project_service.search_projects(db, q, project_type, status, page, page_size)
    return APIResponse(success=True, message="Lấy danh sách dự án thành công.", data=data)


@router.get("/{project_id}", response_model=APIResponse[ProjectDetail], summary="Chi tiết Dự án")
async def get_project_api(
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ProjectDetail]:
    """
    Xem thông tin chi tiết một Dự án bao gồm toàn bộ Nodes (Tasks) và Edges (Logic).

    Args:
        project_id (int): ID dự án.
        db (AsyncSession): Phiên DB (Dependency Injection).

    Returns:
        APIResponse[ProjectDetail]: Dữ liệu chi tiết của Dự án.
        
    Raises:
        HTTPException: Nếu Dự án không tồn tại.
    """
    data = await project_service.get_project_detail(db, project_id)
    return APIResponse(success=True, message="Lấy chi tiết dự án thành công.", data=data)


@router.get("/{project_id}/summary", response_model=APIResponse[ProjectSummary], summary="Tóm tắt Dự án")
async def get_project_summary_api(
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ProjectSummary]:
    """
    Lấy thông tin tóm tắt của một Dự án (số task, số cạnh, trạng thái) mà KHÔNG tải toàn bộ các node/edge bên trong.

    Args:
        project_id (int): ID dự án.
        db (AsyncSession): Phiên DB (Dependency Injection).

    Returns:
        APIResponse[ProjectSummary]: Thông tin cơ bản của dự án.
        
    Raises:
        HTTPException: Nếu Dự án không tồn tại.
    """
    data = await project_service.get_project_summary(db, project_id)
    return APIResponse(success=True, message="Lấy tóm tắt dự án thành công.", data=data)


@router.get("/{project_id}/simulation-stream", summary="Luồng sự kiện chạy mô phỏng AI (SSE Stream)")
async def stream_simulation_events(
    project_id: int = Path(..., description="ID dự án")
):
    """
    Kết nối Server-Sent Events (SSE) để lắng nghe tiến trình chạy mô phỏng AI thời gian thực.
    """
    async def event_generator():
        queue = simulation_event_manager.subscribe(project_id)
        try:
            yield f"data: {json.dumps({'status': 'Simulating', 'message': 'Đã kết nối luồng sự kiện thời gian thực (SSE)'})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("status") in ["Planning", "Error", "Closed", "Completed"]:
                        break
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            simulation_event_manager.unsubscribe(project_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{project_id}/graph", response_model=APIResponse[ProjectGraphResponse], summary="Đồ thị Dự án")
async def get_project_graph_api(
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ProjectGraphResponse]:
    """
    Lấy toàn bộ dữ liệu Đồ thị mạng lưới (Nodes & Edges) của một Dự án.

    Args:
        project_id (int): ID dự án.
        db (AsyncSession): Phiên DB (Dependency Injection).

    Returns:
        APIResponse[ProjectGraphResponse]: Cấu trúc Đồ thị (Graph) của dự án.
        
    Raises:
        HTTPException: Nếu Dự án rỗng hoặc không tồn tại.
    """
    data = await project_service.get_project_graph(db, project_id)
    return APIResponse(success=True, message="Lấy dữ liệu đồ thị thành công.", data=data)


# ==============================================================================
# MUTATIONS (POST, PUT, DELETE)
# ==============================================================================

@router.post("", response_model=APIResponse[ProjectSummary], summary="Tạo Dự án mới")
async def create_project_api(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ProjectSummary]:
    """
    Tạo một Dự án mới với tên và trạng thái khởi tạo.

    Args:
        project_in (ProjectCreate): Dữ liệu khởi tạo Dự án.
        db (AsyncSession): Phiên DB (Dependency Injection).

    Returns:
        APIResponse[ProjectSummary]: Thông tin dự án vừa tạo.
    """
    data = await project_service.create_project(db, project_in)
    return APIResponse(success=True, message="Tạo dự án thành công.", data=data)


@router.put("/{project_id}", response_model=APIResponse[ProjectSummary], summary="Cập nhật Dự án")
async def update_project_api(
    project_id: int = Path(..., description="ID dự án"),
    project_in: ProjectUpdate = ...,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[ProjectSummary]:
    """
    Cập nhật thông tin cơ bản của Dự án (Tên, Trạng thái).

    Args:
        project_id (int): ID dự án.
        project_in (ProjectUpdate): Dữ liệu cập nhật Dự án.
        db (AsyncSession): Phiên DB (Dependency Injection).

    Returns:
        APIResponse[ProjectSummary]: Dữ liệu dự án sau khi cập nhật.
        
    Raises:
        HTTPException: Nếu Dự án không tồn tại.
    """
    data = await project_service.update_project(db, project_id, project_in)
    return APIResponse(success=True, message="Cập nhật dự án thành công.", data=data)


@router.delete("/{project_id}", response_model=APIResponse, summary="Xóa Dự án")
async def delete_project_api(
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse:
    """
    Xóa toàn bộ Dự án cùng mọi Tasks và Ràng buộc bên trong (Cascade Delete).

    Args:
        project_id (int): ID dự án.
        db (AsyncSession): Phiên DB (Dependency Injection).

    Returns:
        APIResponse: Trạng thái xóa.
        
    Raises:
        HTTPException: Nếu Dự án không tồn tại.
    """
    await project_service.delete_project(db, project_id)
    return APIResponse(success=True, message="Đã xóa dự án thành công.")

@router.post("/{project_id}/run-simulation", response_model=APIResponse, summary="Chạy mô phỏng tối ưu AI")
async def run_simulation_api(
    background_tasks: BackgroundTasks,
    project_id: int = Path(..., description="ID dự án"),
    db: AsyncSession = Depends(get_db)
) -> APIResponse:
    """
    Kích hoạt tiến trình chạy mô phỏng PPO/NSGA-II ngầm cho dự án.
    """
    # Lấy thông tin dự án
    project = await project_service.get_project_summary(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
        
    # Đổi trạng thái thành Simulating
    # Cần một phương thức update trực tiếp status, tạm dùng patch update
    await project_service.update_project(db, project_id, ProjectUpdate(status="Simulating"))
    
    # Ném tiến trình chạy Python script xuống Background
    # Chuyển project_type xuống cho AI
    background_tasks.add_task(run_simulation_background, str(project_id), project.type or "Logistics")
    
    return APIResponse(
        success=True, 
        message="Đã đưa tác vụ mô phỏng vào chạy ngầm. Trạng thái dự án đang là 'Simulating'."
    )
