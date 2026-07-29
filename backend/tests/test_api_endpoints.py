"""
GLPO Backend API Unit Test Suite
=====================================================
Thư mục: backend/tests/test_api_endpoints.py
Mô tả: Bộ kiểm thử tự động toàn bộ API endpoints của Backend GLPO.
"""
import pytest
import requests

BASE_URL = "http://localhost:8000"
PROJECT_ID = "C2011-07"


def test_01_health_check():
    """Test API /health"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"


def test_02_get_projects_list():
    """Test API GET /api/v1/projects danh sách dự án có phân trang & tìm kiếm"""
    response = requests.get(f"{BASE_URL}/api/v1/projects?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert len(data["data"]["items"]) >= 5


def test_03_search_projects():
    """Test API GET /api/v1/projects với từ khóa tìm kiếm & bộ lọc"""
    response = requests.get(f"{BASE_URL}/api/v1/projects?q=C2011-07")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["items"]) >= 1
    assert data["data"]["items"][0]["id"] == PROJECT_ID


def test_04_get_project_summary():
    """Test API GET /api/v1/projects/{project_id}/summary tóm tắt dự án"""
    response = requests.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == PROJECT_ID
    assert data["data"]["num_tasks"] == 49


def test_05_get_project_detail():
    """Test API GET /api/v1/projects/{project_id} chi tiết dự án"""
    response = requests.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == PROJECT_ID


def test_06_get_project_graph():
    """Test API GET /api/v1/projects/{project_id}/graph đồ thị DAG"""
    response = requests.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "nodes" in data["data"]
    assert "edges" in data["data"]


def test_07_get_project_tasks():
    """Test API GET /api/v1/projects/{project_id}/tasks danh sách công việc"""
    response = requests.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 49


def test_08_get_task_detail():
    """Test API GET /api/v1/projects/{project_id}/tasks/{task_id} chi tiết task"""
    task_id = "C2011-07_1"
    response = requests.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["task_id"] == task_id
    assert data["data"]["project_id"] == PROJECT_ID
    assert "labor" in data["data"]
    assert "total_cost" in data["data"]


def test_09_create_and_delete_task():
    """Test API POST & DELETE /api/v1/projects/{project_id}/tasks tạo và xóa task"""
    new_task_payload = {
        "task_name": "UnitTest Dummy Task",
        "duration_hours": 16.0,
        "labor": 100.0,
        "material": 200.0
    }
    # Create Task
    create_resp = requests.post(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/tasks", json=new_task_payload)
    assert create_resp.status_code == 200
    create_data = create_resp.json()
    assert create_data["success"] is True
    created_task_id = create_data["data"]["task_id"]
    assert create_data["data"]["total_cost"] == 300.0

    # Delete Task
    delete_resp = requests.delete(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/tasks/{created_task_id}")
    assert delete_resp.status_code == 200
    delete_data = delete_resp.json()
    assert delete_data["success"] is True


def test_10_get_constraints_logic():
    """Test API GET /api/v1/projects/{project_id}/constraints/logic"""
    response = requests.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/constraints/logic")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 56


def test_11_get_constraints_resource():
    """Test API GET /api/v1/projects/{project_id}/constraints/resource"""
    response = requests.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/constraints/resource")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1


def test_12_get_constraints_time():
    """Test API GET /api/v1/projects/{project_id}/constraints/time"""
    response = requests.get(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/constraints/time")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "weekly_schedule" in data["data"]


def test_13_get_ai_pipeline_runs():
    """Test API GET /api/v1/ai/pipeline/runs/{project_id} danh sách AI runs"""
    response = requests.get(f"{BASE_URL}/api/v1/ai/pipeline/runs/{PROJECT_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_14_export_dataset():
    """Test API POST /api/v1/projects/{project_id}/export-dataset xuất dữ liệu ra thư mục AI train"""
    response = requests.post(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/export-dataset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "path" in data["data"]


def test_15_import_dataset():
    """Test API POST /api/v1/projects/{project_id}/import-dataset nạp đồng bộ dữ liệu từ tệp vào DB"""
    response = requests.post(f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/import-dataset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["project_id"] == PROJECT_ID


def test_16_ai_pipeline_4step_workflow():
    """Test API POST /api/v1/ai/{project_id}/glpo-optimize quy trình 4 bước AI hoàn chỉnh"""
    response = requests.post(
        f"{BASE_URL}/api/v1/ai/{PROJECT_ID}/glpo-optimize",
        params={"mc_iterations": 100, "pareto_count": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "Completed"
    assert "pareto_solutions" in data["data"]
