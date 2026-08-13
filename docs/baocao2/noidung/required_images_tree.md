# Danh mục Biểu đồ và Hình ảnh Yêu cầu (Required Figures Tree)
*Dựa trên tiêu chuẩn của Kỹ sư Nghiên cứu (Research-Engineer) để đảm bảo tính trực quan và số liệu khoa học.*

Báo cáo Đồ án khoa học kỹ thuật yêu cầu mức độ trực quan hóa dữ liệu rất cao. Dưới đây là Cây cấu trúc (Tree Content) liệt kê chính xác các Hình ảnh (Figures), Biểu đồ (Charts) và Sơ đồ (Diagrams) cần phải có hoặc cần tạo/chụp thêm để chèn vào thư mục `image`.

```text
Danh mục Biểu đồ & Hình ảnh Báo cáo Đồ án GLPO
├── CHƯƠNG 1: TỔNG QUAN LÝ THUYẾT VÀ CƠ SỞ NGHIÊN CỨU
│   ├── Hình 1.1: Sơ đồ mô phỏng Mô hình tham chiếu SCOR trong chuỗi cung ứng.
│   ├── Hình 1.2: Minh họa Hiệu ứng Bullwhip (Sự khuếch đại dao động nhu cầu).
│   ├── Hình 1.3: Cấu trúc cơ bản của Sơ đồ mạng lưới AON (Đỉnh là Công việc, Cạnh là Quan hệ).
│   ├── Hình 1.4: Lưu đồ trực quan phép tính CPM (Minh họa các thông số ES, EF, LS, LF trên 1 Node).
│   ├── Hình 1.5: Đồ thị thể hiện mối quan hệ nghịch biến giữa Thời gian và Chi phí (Time-Cost Trade-off).
│   ├── Hình 1.6: Biểu đồ mô tả Đường biên Pareto (Pareto Frontier) trong không gian Đa mục tiêu.
│   ├── Hình 1.7: Đồ thị minh họa các đường cơ sở của EVM (Sự hội tụ / phân kỳ của PV, EV, AC).
│   ├── Hình 1.8: Cấu trúc truyền tin (Message Passing Mechanism) trong Mạng nơ-ron đồ thị (GNN).
│   └── Hình 1.9: Kiến trúc cốt lõi của Heterogeneous Graph Transformer (HGT) và cơ chế Attention.
│
├── CHƯƠNG 2: KIẾN TRÚC HỆ THỐNG VÀ PHƯƠNG PHÁP LUẬN ĐỀ XUẤT
│   ├── Hình 2.1: Sơ đồ Kiến trúc Tổng thể Hệ thống (Microservices Architecture Diagram).
│   ├── Hình 2.2: Sơ đồ Tuần tự (Sequence Diagram) luồng giao tiếp giữa Frontend, FastAPI và AI Pipeline.
│   ├── Hình 2.3: Lược đồ Cơ sở Dữ liệu Thực thể Liên kết (ERD) trên hệ quản trị PostgreSQL.
│   ├── Hình 2.4: Lưu đồ khối (Flowchart) mô tả thuật toán Recursive CTE quét qua mạng lưới DAG.
│   ├── Hình 2.5: Phân tích trực quan luồng Tiền xử lý Dữ liệu (ETL Pipeline) từ file DSLIB thành Tensor.
│   ├── Hình 2.6: Sơ đồ cấu trúc thuật toán Tối ưu hóa Ràng buộc CP-SAT (Constraint Programming).
│   ├── Hình 2.7: Lưu đồ tích hợp kết quả HGT và mô phỏng Monte Carlo vào mô hình CP-SAT.
│   ├── Hình 2.8: Pipeline Huấn luyện AI: Tự giám sát (MAE) kết hợp Tinh chỉnh có giám sát (Fine-tuning).
│   └── Hình 2.9: Sơ đồ hạ tầng Triển khai (Deployment Topology) với Docker và Docker Compose.
│
├── CHƯƠNG 3: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN
│   ├── Hình 3.1: Giao diện trực quan của mạng lưới dự án MFET 3008 (Render từ phần mềm React-Flow).
│   ├── Hình 3.2: Biểu đồ cột (Bar Chart) so sánh Query Latency của CTE so với truy vấn đệ quy thông thường.
│   ├── Hình 3.3: Biểu đồ sử dụng tài nguyên (Resource Histogram) TRƯỚC khi tối ưu hóa.
│   ├── Hình 3.4: Biểu đồ phân bổ nguồn lực (Resource Leveling Chart) SAU khi chạy tối ưu hóa.
│   ├── Hình 3.5: Biểu đồ đường cong Pareto (Pareto Frontier) so sánh sự đánh đổi giữa Makespan và Cost.
│   ├── Hình 3.6: Biểu đồ Learning Curve (Sự hội tụ của Loss và R2 Score) của mô hình AI HGT.
│   ├── Hình 3.7: Biểu đồ Scatter Plot đối chiếu sai số Hồi quy (Predicted Days vs Actual Days).
│   ├── Hình 3.8: Bản đồ Nhiệt trọng số Chú ý (Attention Heatmap) giải thích mức độ ảnh hưởng của Node.
│   └── Hình 3.9: Ảnh chụp (Screenshot) giao diện EVM Dashboard và Gantt Chart hoạt động thực tế.
│
└── CHƯƠNG 4: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
    └── Hình 4.1: Sơ đồ Concept đề xuất kiến trúc Cơ chế Chú ý Nâng cao (Advanced Attention) thay thế cho HGT cơ bản.
```

## Các Công cụ Cần dùng để Vẽ:
1. **Sơ đồ Kiến trúc & ERD (Hình 2.1 - 2.4, Hình 2.9):** Sử dụng `Mermaid.js`, `Draw.io` (app.diagrams.net), hoặc `Lucidchart`.
2. **Sơ đồ Thuật toán AI & Toán học (Hình 1.8, 1.9, Hình 2.6, 2.7, 2.8):** Đề xuất dùng `OmniGraffle`, `Visio` hoặc tự vẽ bằng Python (`Graphviz`).
3. **Biểu đồ Dữ liệu định lượng (Hình 1.5, Hình 1.7, toàn bộ Hình Chương 3 trừ Ảnh chụp):** Chắc chắn phải gen bằng mã nguồn Python (sử dụng thư viện `matplotlib`, `seaborn`, hoặc `plotly`) để đảm bảo tính hàn lâm (độ phân giải 300 DPI, xuất file `.pdf` hoặc `.png`).
4. **Ảnh giao diện (Hình 3.1, Hình 3.9):** Ảnh chụp màn hình (Screenshots) chất lượng cao từ dự án frontend.
