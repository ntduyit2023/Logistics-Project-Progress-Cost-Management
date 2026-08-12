# 📊 Graph-Based Logistics Project Optimizer (GLPO)
## Tài Liệu Định Hướng & Thiết Kế Kiến Trúc Hệ Thống (Ultimate Guide)

Chào mừng bạn đến với tài liệu định hướng tổng thể dự án **GLPO**. Tài liệu này đóng vai trò là kim chỉ nam giúp bạn hiểu rõ lộ trình thực hiện đồ án, các đầu việc cần làm của từng pha, và các mô hình đồ thị/AI sẽ được áp dụng xuyên suốt hệ thống.

---

## 🗺️ MỤC LỤC
1. [🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng (Quick Start)](#-1-huong-dan-cai-dat--chay-ung-dung-quick-start)
---

## 🚀 1. Hướng Dẫn Cài Đặt & Chạy Ứng Dụng (Quick Start)

### Bước 1: Yêu cầu hệ thống
Đảm bảo máy tính của bạn đã cài đặt sẵn:
- **Docker** và **Docker Compose**
- Không có ứng dụng nào khác đang chiếm dụng các cổng `5432` (PostgreSQL), `8000` (Backend FastAPI) và `5173` (Frontend Vite).

### Bước 2: Khởi động toàn bộ hệ thống bằng Docker
Từ thư mục gốc của dự án, mở terminal và chạy lệnh sau để khởi động Database, Backend và Frontend cùng lúc:
```bash
docker compose --profile dev up -d
```
*Lưu ý: Thêm cờ `-d` để chạy ngầm. Để xem log trực tiếp, bạn có thể bỏ cờ `-d`.*

### Bước 3: Truy cập vào các cổng của hệ thống (Ports)
Khi Docker thông báo `Running`, bạn có thể truy cập vào hệ thống qua các đường dẫn sau:
- **🖥️ Giao diện người dùng (Frontend):** [http://localhost:5173](http://localhost:5173)
- **⚙️ Máy chủ xử lý (Backend API):** [http://localhost:8000](http://localhost:8000)
- **📖 Tài liệu API tự động (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **🗄️ Cơ sở dữ liệu (PostgreSQL):** Cổng `localhost:5432` (User: `glpo_admin`, Pass: `glpo_password`)

### Bước 4: Cách Nạp Lại Dữ Liệu (Reload Data)
Hệ thống sử dụng mã nguồn `backend/scripts/reload_docker_db.py` để xóa trắng và nạp lại toàn bộ dữ liệu 5 dự án mẫu từ thư mục `ai_pipeline/data/processed` vào thẳng Database.

Khi bạn lỡ thao tác xóa nhầm hoặc muốn **reset Database về trạng thái gốc ban đầu**, chỉ cần đảm bảo các container đang chạy (`Running`) và mở terminal mới gõ lệnh sau:
```bash
docker exec -it glpo_backend python scripts/reload_docker_db.py
```
Tiến trình này sẽ tự động Drop cấu trúc cũ, tạo lại Schema theo SQLAlchemy Models, và Import chính xác thông tin, công việc, quan hệ và 38 phân loại chi phí (G1-G7) của Dataset.

---
