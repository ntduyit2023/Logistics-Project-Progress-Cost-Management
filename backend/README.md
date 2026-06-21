# GLPO Backend - Developer Guide

Chào mừng bạn đến với tài liệu hướng dẫn lập trình Backend cho dự án **GLPO (AI Project Scheduling Platform)**. Tài liệu này cung cấp các quy chuẩn kiến trúc và quy trình làm việc để đảm bảo code base luôn sạch, dễ bảo trì và mở rộng.

## 1. Công Nghệ Cốt Lõi (Tech Stack)
- **Framework:** FastAPI (Python 3.12)
- **Database ORM:** SQLAlchemy 2.0 (Asynchronous)
- **Database Driver:** `asyncpg`
- **Data Validation:** Pydantic V2
- **Database Migration:** Alembic
- **DBMS:** PostgreSQL 15 (với GIN Index / Full-Text Search)

---

## 2. Kiến Trúc Hệ Thống (Layered Architecture)
Hệ thống tuân thủ chặt chẽ kiến trúc 3 lớp (3-Tier Architecture) kết hợp Repository Pattern. Luồng dữ liệu đi theo hướng một chiều như sau:

**`Router / Endpoint` ➡️ `Service` ➡️ `Repository` ➡️ `Model / Database`**

1. **API Endpoints (`app/api/endpoints/`)**: Nhận HTTP Request, Validate Pydantic Schema, bọc HTTP Response. Không chứa Business Logic.
2. **Services (`app/services/`)**: Xử lý logic nghiệp vụ, thuật toán tính toán, tổng hợp dữ liệu từ nhiều Repositories.
3. **Repositories (`app/repositories/`)**: Thao tác trực tiếp với Database bằng SQLAlchemy ORM (CRUD). Kế thừa từ `BaseRepository`.
4. **Models (`app/models/`)**: Định nghĩa cấu trúc bảng (SQLAlchemy Mapped Classes).
5. **Schemas (`app/schemas/`)**: Pydantic models dùng để Validate đầu vào/đầu ra.

---

## 3. Quy Chuẩn Code (Coding Conventions)

### 3.1. Bao Bọc Response Tự Động (`APIResponse[T]`)
**Tuyệt đối không** trả về dữ liệu thô (raw data) từ Endpoint. Mọi API phải trả về `APIResponse[T]` để Frontend đồng bộ xử lý lỗi và dữ liệu.

```python
from app.schemas.schemas import APIResponse

@router.get("/{id}", response_model=APIResponse[ProjectDetail])
async def get_project(id: int):
    data = await service.get_project(id)
    return APIResponse(success=True, message="Lấy dữ liệu thành công", data=data)
```

### 3.2. Asynchronous Programming (Async/Await)
Mọi tương tác với I/O (Database, File, Request ra ngoài) đều phải dùng `await`. Cẩn thận với lỗi N+1 Query của SQLAlchemy trong môi trường Async. Sử dụng `selectinload` để Eager Load các bảng liên quan.

### 3.3. Type Hints và Docstrings
- Mọi hàm và class BẮT BUỘC phải có **Type Hints** đầy đủ cho cả tham số và kết quả trả về.
- Mọi hàm, class, module phải có **Docstrings** chuẩn Google mô tả rõ Args và Returns.

---

## 4. Quản Lý Cơ Sở Dữ Liệu & Alembic Migration

Dự án sử dụng **Alembic** để versioning cấu trúc Database. 

### Khi bạn thay đổi Models (Thêm bảng, thêm cột, đổi kiểu dữ liệu)
Bất cứ khi nào bạn sửa đổi file `app/models/models.py`, bạn BẮT BUỘC phải sinh file Migration và cập nhật Database.

**Bước 1: Sinh script tự động (Chạy trên Terminal của Host OS, đảm bảo Docker đang chạy)**
```bash
docker exec glpo_backend python -m alembic revision --autogenerate -m "Mô tả thay đổi, VD: Add new table configs"
```
*Bạn nên vào thư mục `backend/alembic/versions/` để kiểm tra lại file `.py` vừa được sinh ra xem Alembic đã nhận diện đúng thay đổi chưa.*

**Bước 2: Nâng cấp Database (Upgrade)**
```bash
docker exec glpo_backend python -m alembic upgrade head
```

### Nếu bạn lấy Code mới từ Git về (Pull)
Nếu team có thay đổi Database, khi bạn lấy code mới về, chỉ cần chạy lệnh Upgrade để đồng bộ DB local của bạn:
```bash
docker exec glpo_backend python -m alembic upgrade head
```

---

## 5. Môi Trường Docker và Các Profile

Hệ thống được thiết kế chạy qua Docker Compose với nhiều profiles cấu hình tài nguyên:
- **Profile `dev`**: Dùng cho lúc code. Hỗ trợ Hot-reload cho Backend và Frontend.
- **Profile `prod`**: Dùng khi deploy thật. Bật giới hạn RAM chặt chẽ.
- **Profile `db`**: Chỉ bật mỗi database (phục vụ việc chạy script ngoài).

**Khởi động môi trường Dev:**
```bash
docker compose --profile dev up -d
```
*Backend sẽ tự khởi động lại khi bạn nhấn Ctrl+S lưu file.*

**Xem log Backend:**
```bash
docker logs glpo_backend -f
```

---

> [!TIP]
> Hãy luôn ưu tiên viết Unit Tests cho các function phức tạp trong thư mục `tests/` trước khi đẩy code lên nhánh chính! Cảm ơn bạn đã đóng góp cho dự án.
