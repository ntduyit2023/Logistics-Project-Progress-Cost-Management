# Cấu trúc Cây Báo cáo Đồ án Chi tiết (Detailed Thesis Tree Content)
*Được đồng bộ hóa hoàn chỉnh theo cấu trúc khoa học của Báo cáo Đồ án 2 mẫu (Dự báo chất lượng không khí).*

```text
Báo cáo Đồ án: Hệ thống Quản trị Dự án Logistics (GLPO)
├── CHƯƠNG 1: TỔNG QUAN LÝ THUYẾT VÀ CƠ SỞ NGHIÊN CỨU
│   ├── 1.1 Đặc thù Dự án Logistics và Chuỗi cung ứng (Supply Chain)
│   │   ├── 1.1.1 Mô hình tham chiếu SCOR (Plan, Source, Make, Deliver, Return)
│   │   ├── 1.1.2 Hiệu ứng Bullwhip: Nguyên nhân và tác động đến chi phí dự trữ
│   │   └── 1.1.3 Các rủi ro đứt gãy tiến độ (Stochastic Disruptions): Biến động thời tiết, năng lực nhà cung cấp
│   ├── 1.2 Quản trị Dự án dựa trên Đồ thị (Graph-based Project Management)
│   │   ├── 1.2.1 Sơ đồ mạng lưới hoạt động AON (Activity-on-Node): Định nghĩa đỉnh (V) và cạnh (E)
│   │   ├── 1.2.2 Phân tích Hợp lệ: Sắp xếp Tô-pô (Topological Sort) và Phát hiện chu trình (Cycle Detection)
│   │   └── 1.2.3 Phương pháp Đường găng (CPM - Critical Path Method): ES, EF, LS, LF và Total/Free Slack
│   ├── 1.3 Tối ưu hóa Ràng buộc Tài nguyên và Ép tiến độ (RCPSP & Crashing)
│   │   ├── 1.3.1 Bài toán RCPSP: Giới hạn tài nguyên tái tạo (Renewable) và không tài tạo (Non-renewable)
│   │   ├── 1.3.2 Bài toán Crashing: Mối quan hệ Đổi chác Thời gian - Chi phí (Time-Cost Trade-off)
│   │   └── 1.3.3 Khái niệm Đường biên Pareto (Pareto Frontier) trong Tối ưu hóa Đa mục tiêu
│   ├── 1.4 Quản lý Giá trị Đạt được (EVM - Earned Value Management)
│   │   ├── 1.4.1 Các biến số cơ sở: PV (Planned Value), EV (Earned Value), AC (Actual Cost)
│   │   ├── 1.4.2 Phân tích Phương sai và Chỉ số Hiệu suất: SV, CV, SPI, CPI
│   │   └── 1.4.3 Dự báo tương lai: EAC (Estimate at Completion) và ETC (Estimate to Complete)
│   ├── 1.5 Trí tuệ Nhân tạo và Học máy trên Đồ thị (Graph ML/AI)
│   │   ├── 1.5.1 Mạng nơ-ron đồ thị (GNN): Cơ chế truyền tin (Message Passing)
│   │   ├── 1.5.2 Mạng nơ-ron đồ thị dị thể (HGT): Xử lý đa loại nút (Task, Resource) và cạnh (Precedence, Assignment)
│   │   ├── 1.5.3 Học biểu diễn Tự giám sát bằng Masked Autoencoder (MAE) trên đồ thị
│   │   └── 1.5.4 Học có giám sát (Supervised Learning): Các bài toán Hồi quy (Regression) và Phân loại (Classification) dự báo rủi ro
│   ├── 1.6 Cơ sở Toán học: Tiền xử lý Dữ liệu và Chỉ số Đánh giá
│   │   ├── 1.6.1 Các phương pháp Chuẩn hóa dữ liệu (Data Normalization): Min-Max Scaling, Z-Score (Standardization), Robust Scaling
│   │   ├── 1.6.2 Chỉ số đánh giá bài toán Hồi quy: MAE (Mean Absolute Error), RMSE (Root Mean Square Error), $R^2$
│   │   └── 1.6.3 Chỉ số đánh giá bài toán Phân loại: Accuracy, Precision, Recall, F1-Score, Ma trận nhầm lẫn (Confusion Matrix)
│   └── 1.7 Tổng quan các công trình nghiên cứu và Khoảng trống (Literature Review)
│       ├── 1.7.1 Các nghiên cứu trong nước về tối ưu tiến độ (Trích dẫn chuẩn IEEE)
│       ├── 1.7.2 Các nghiên cứu ngoài nước về ứng dụng Graph AI trong Logistics
│       └── 1.7.3 Khoảng trống nghiên cứu (Research Gap): Hạn chế của các mô hình truyền thống khi thiếu tích hợp AI
│
├── CHƯƠNG 2: PHƯƠNG TIỆN VÀ PHƯƠNG PHÁP NGHIÊN CỨU
│   ├── 2.1 Sơ đồ tổng quan giải pháp (TikZ Flowchart)
│   ├── 2.2 Phương tiện nghiên cứu
│   │   ├── 2.2.1 Ngôn ngữ lập trình và thư viện (Python, PyTorch, PyG, OR-Tools, React, FastAPI)
│   │   └── 2.2.2 Phần cứng thực nghiệm
│   ├── 2.3 Thu thập dữ liệu
│   │   ├── 2.3.1 Dữ liệu tiến độ và chi phí cơ sở (Tasks, costs, precedence)
│   │   ├── 2.3.2 Dữ liệu tài nguyên và ca kíp (Resources, calendars)
│   │   └── 2.3.3 Dữ liệu rủi ro và nhãn đánh giá (PERT 3-point, labels)
│   ├── 2.4 Khảo sát và chọn lọc dự án nghiên cứu
│   │   ├── 2.4.1 Sự cần thiết của bước chọn lọc dự án đối chuẩn
│   │   ├── 2.4.2 Hệ thống tiêu chí chọn lọc (Quy mô topo mạng công việc, độ phức tạp tài nguyên)
│   │   └── 2.4.3 Kết quả chọn lọc dự án nghiên cứu (Tập dữ liệu DSLIB & Case-study C2012-04)
│   ├── 2.5 Tiền xử lý dữ liệu và Làm sạch đồ thị
│   │   ├── 2.5.1 Lọc hạng mục lá (Leaf Node Filtering - openpyxl)
│   │   ├── 2.5.2 Phát hiện chu trình (DFS Cycle Detection)
│   │   ├── 2.5.3 Xử lý công việc cô lập (Orphan Node Resolution)
│   │   └── 2.5.4 Đồng bộ hóa giờ thi công (Timeline Alignment)
│   ├── 2.6 Kỹ nghệ đặc trưng
│   │   ├── 2.6.1 Trích xuất các tỷ lệ chi phí thành phần (Ratio_labor, Ratio_mat_eq)
│   │   ├── 2.6.2 Mã hóa lượng giác chu kỳ thời gian (Sin/Cos weekdays/hours)
│   │   └── 2.6.3 Tích hợp đặc trưng trễ (Lag) và thống kê trượt (rolling mean/std)
│   ├── 2.7 Chuẩn hóa dữ liệu
│   │   ├── 2.7.1 Biến đổi Log-scale cho chi phí và nhãn (log1p)
│   │   ├── 2.7.2 Chuẩn hóa Z-Score và kẹp giá trị (clamp)
│   │   └── 2.7.3 Cơ cấu Normalizer Registry thích ứng (CON, ITLG, PRO)
│   ├── 2.8 Chia tập dữ liệu
│   │   ├── 2.8.1 Đặc trưng cấu trúc topo rời rạc và rò rỉ dữ liệu GNN
│   │   └── 2.8.2 Chiến lược Kiểm thử chéo Loại bỏ một Dự án (Leave-One-Project-Out CV)
│   ├── 2.9 Huấn luyện mô hình
│   │   ├── 2.9.1 Huấn luyện tiền kỳ tự giám sát (Pre-training SSL HGT MAE)
│   │   └── 2.9.2 Huấn luyện tinh chỉnh đa nhiệm và Ước lượng Bất định (Supervised Fine-tuning)
│   ├── 2.10 Đánh giá mô hình
│   │   ├── 2.10.1 Các chỉ số đánh giá độ chính xác dự báo rủi ro tiến độ (MAE, RMSE, R2, MAPE)
│   │   └── 2.10.2 Các chỉ số đánh giá hiệu năng tối ưu hóa lập lịch (Resource variance, Gini index)
│   └── 2.11 Triển khai ứng dụng (Deployment)
│       ├── 2.11.1 Kiến trúc hệ thống vi dịch vụ container hóa (Docker & Docker Compose)
│       └── 2.11.2 Luồng hoạt động và Cơ chế kết xuất Frontend Rendering
│
├── CHƯƠNG 3: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN
│   ├── 3.1 Kết quả tổng hợp
│   │   ├── 3.1.1 Thiết lập tập dữ liệu C2012-04 và các baseline
│   │   └── 3.1.2 Kết quả tổng hợp thời gian, chi phí và rủi ro
│   ├── 3.2 Phân tích hiệu suất theo tầm nhìn dự báo (Phân tích sai số dự báo thời lượng)
│   │   ├── 3.2.1 Sai số tuyệt đối trung bình (MAE)
│   │   ├── 3.2.2 Sai số toàn phương trung bình (RMSE)
│   │   ├── 3.2.3 Hệ số xác định $R^2$
│   │   └── 3.2.4 Sai số phần trăm tuyệt đối trung bình (MAPE)
│   ├── 3.3 Đánh giá tính ổn định
│   │   ├── 3.3.1 Phân bố RMSE qua các cấu hình 5-Fold Cross Validation
│   │   ├── 3.3.2 Đánh giá năng lực tổng quát hóa zero-shot xuyên dự án
│   │   └── 3.3.3 Lượng hóa độ bất định dự báo (Uncertainty Estimation)
│   ├── 3.4 Ảnh hưởng của quy mô dự án (Quy mô đồ thị J30, J60, J120)
│   ├── 3.5 Ảnh hưởng của chiến lược chia dữ liệu (LOPO CV vs Random Split)
│   ├── 3.6 Tốc độ suy giảm hiệu suất (Thời gian hội tụ và độ trễ suy luận AI)
│   ├── 3.7 Đánh giá phương pháp kết hợp mô hình (AI-Guided CP-SAT vs Baselines)
│   ├── 3.8 Chi phí tính toán (Dung lượng bộ nhớ và độ trễ truy vấn Recursive CTE)
│   ├── 3.9 Ứng dụng web quản trị tiến độ và chi phí dự án (GLPO Web UI)
│   │   ├── 3.9.1 Kiến trúc ứng dụng vi dịch vụ container hóa
│   │   ├── 3.9.2 Giao diện tổng quan danh sách và Gantt Chart
│   │   └── 3.9.3 Giao diện phân tích tài chính S-Curve và Pareto
│   └── 3.10 Thảo luận
│       ├── 3.10.1 Đánh giá mức độ đạt mục tiêu
│       ├── 3.10.2 Ưu điểm của giải pháp đề xuất
│       └── 3.10.3 Hạn chế của nghiên cứu và hướng phát triển
│
└── CHƯƠNG 4: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
    ├── 4.1 Kết luận chung
    │   ├── 4.1.1 Về thu thập và tiền xử lý dữ liệu đồ thị
    │   ├── 4.1.2 Về kỹ nghệ đặc trưng và chuẩn hóa thích ứng
    │   ├── 4.1.3 Về hiệu năng mô hình AI dự báo rủi ro
    │   ├── 4.1.4 Về mô hình tối ưu đề xuất HGT-Guided CP-SAT
    │   ├── 4.1.5 Về chi phí tính toán và triển khai vi dịch vụ
    │   └── 4.1.6 Tổng hợp đánh giá chung
    ├── 4.2 Hạn chế của nghiên cứu
    │   ├── 4.2.1 Quy mô dữ liệu lịch sử và tính đa dạng dự án
    │   ├── 4.2.2 Hạn chế bùng nổ tổ hợp của CP-SAT với dự án siêu lớn
    │   └── 4.2.3 Thiếu thực nghiệm phân lập đặc trưng sâu
    └── 4.3 Đề xuất hướng phát triển
        ├── 4.3.1 Áp dụng thuật toán Tìm kiếm Lân cận Lớn (LNS) phối hợp CP-SAT
        ├── 4.3.2 Áp dụng các kiến trúc Transformer đồ thị nâng cao (Graphormer)
        └── 4.3.3 Mở rộng dữ liệu huấn luyện thực tế từ doanh nghiệp
```

## Ghi chú Triển khai (Implementation Notes)
- Toàn bộ các công thức ở Chương 1 (EVM, Crashing, HGT) bắt buộc phải trình bày bằng chuẩn **LaTeX**.
- Các bảng so sánh ở Chương 3 cần hiển thị rõ ràng độ lệch chuẩn (Standard Deviation) và mức ý nghĩa thống kê (p-value nếu có).
- Trích dẫn (Citation) tuân thủ nghiêm ngặt tiêu chuẩn IEEE từ các kho lưu trữ uy tín.
