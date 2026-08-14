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
│   │
│   ├── 3.1 Tổng quan Kết quả Thực nghiệm
│   │   ├── 3.1.1 Môi trường thực nghiệm và Tập dữ liệu
│   │   │   └── [Bảng] Thống kê 5 dự án trong DSLIB
│   │   │           (C2019-16 | C2018-09 | C2011-07 | C2012-04 | C2012-08)
│   │   │           Cột: Mã dự án, |V|, |E|, Ngân sách, Số tài nguyên
│   │   └── 3.1.2 Bảng tổng hợp chỉ số hiệu năng toàn hệ thống
│   │           └── [Bảng tóm tắt] Mỗi phân hệ → 1-2 chỉ số đại diện:
│   │                   - Graph DB:  Latency CTE 1,95 ms vs ORM 35,20 ms
│   │                   - AI HGT:    R² trung bình 0,3734 | Best R² 0,8023
│   │                   - CP-SAT:    Makespan giảm 21,1% | Risk giảm 36,5%
│   │
│   ├── 3.2 Hiệu năng Phân hệ Lưu trữ Đồ thị (Graph DB)
│   │   ├── 3.2.1 Độ trễ truy vấn: Recursive CTE vs ORM tiêu chuẩn
│   │   │   ├── [Bảng] Thời gian (ms) theo |V| = 20 → 5.000
│   │   │   └── [Hình] Biểu đồ cột so sánh hai phương pháp
│   │   └── 3.2.2 Mức tiêu thụ Bộ nhớ khi mở rộng quy mô
│   │           └── [Bảng] RAM CSDL + Backend API + VRAM theo |V|
│   │
│   ├── 3.3 Hiệu năng Phân hệ AI (HGT + Pre-training SSL)
│   │   ├── 3.3.1 Chiến lược chia dữ liệu xuyên dự án (LOPO CV)
│   │   │   ├── Giải thích tại sao k=5 (Leave-One-Project-Out,
│   │   │   │   không phải k-fold ngẫu nhiên vì 5 dự án = 5 folds)
│   │   │   └── [Bảng] LOPO CV vs Random Split
│   │   │           Cột: Train R², Val R², Val MSE, Hiện tượng rò rỉ
│   │   ├── 3.3.2 Quá trình huấn luyện và Hội tụ mô hình
│   │   │   ├── [Hình] Đường cong Loss Pre-training (NLL Loss + MAE/RMSE)
│   │   │   └── Phân tích: best epoch, Early Stopping patience=40
│   │   ├── 3.3.3 Độ chính xác dự báo: MAE, RMSE, MAPE, R²
│   │   │   ├── Công thức toán học 4 chỉ số
│   │   │   ├── [Bảng] Kết quả từng Fold (Fold 1→5 + Trung bình ± σ)
│   │   │   │           Cột: Fold, Số epochs, Best Val R², Min Val Loss, Val MSE
│   │   │   ├── [Hình] Đường cong R² Score và Loss qua 5-Fold (epoch.jpg)
│   │   │   └── [Hình] Scatter Plot dự báo vs thực tế (regression_scatter)
│   │   ├── 3.3.4 Ảnh hưởng Quy mô đồ thị đến hiệu năng AI
│   │   │   └── [Bảng] 5 dự án: |V|, |E|, Val Loss, Best R², Latency (ms)
│   │   │           (C2019-16 → C2012-08, sắp xếp theo |V| tăng dần)
│   │   └── 3.3.5 Định vị Nút thắt cổ chai (Bottleneck Attention)
│   │           ├── Cơ chế: Cosine Similarity giữa V_Task và V_Resource
│   │           └── [Hình] Bản đồ nhiệt (15 công việc găng × 8 tài nguyên)
│   │
│   ├── 3.4 Hiệu năng Phân hệ Tối ưu hóa (CP-SAT + Monte Carlo)
│   │   ├── 3.4.1 Phân phối Rủi ro Tiến độ (Monte Carlo CPM)
│   │   │   ├── Mô tả: Beta-PERT → 10.000 vòng lặp → CDF thực nghiệm
│   │   │   └── [Hình] Đường cong CDF với mốc P50, P80, P95
│   │   ├── 3.4.2 Kết quả Ép tiến độ (Crashing)
│   │   │   ├── [Bảng] 3 phương án tối ưu đại diện
│   │   │   │           Cột: Phương án, Makespan, Overtime (giờ/tasks),
│   │   │   │                Tổng chi phí, Risk%, Chiến lược
│   │   │   └── Biện luận đánh đổi Makespan - Chi phí
│   │   ├── 3.4.3 Tối ưu hóa Phân bổ Tài nguyên (Resource Leveling)
│   │   │   ├── Công thức hàm mục tiêu phương sai tài nguyên
│   │   │   ├── [Bảng] Chỉ số trước/sau tối ưu
│   │   │   │           (Peak, Min, Mean, Variance, Std Dev, Gini)
│   │   │   ├── [Hình] Biểu đồ nhân lực TRƯỚC tối ưu
│   │   │   └── [Hình] Biểu đồ nhân lực SAU tối ưu
│   │   └── 3.4.4 Đường biên Pareto Frontier
│   │           ├── [Bảng] Điểm Pareto P₁, P₂, P₃
│   │           │           Cột: Điểm nghiệm, Makespan, Cost, Risk%, Overtime
│   │           └── [Hình] Đường cong Pareto Frontier (Cost vs Makespan)
│   │
│   ├── 3.5 Đối chuẩn Toàn hệ thống (Benchmarking)
│   │   ├── [Bảng] GLPO (Opt.1) vs CPM vs GA vs Pure CP-SAT
│   │   │           Cột: Phương pháp, Makespan (h), Cost (USD),
│   │   │                Risk%, Số tasks tăng ca, Thời gian giải (CPU)
│   │   └── Biện luận 3 điểm:
│   │       ├── (a) Ảnh hưởng của ràng buộc tài nguyên hữu hạn
│   │       ├── (b) Cơ chế AI-Guided Optimization (Bottleneck → Crashing)
│   │       └── (c) Bài toán đánh đổi Chi phí - Rủi ro (Cost-Risk Trade-off)
│   │
│   └── 3.6 Bàn luận và Hạn chế
│       ├── 3.6.1 Tính hiệu quả của phân ly 38 loại chi phí trong Logistics
│       ├── 3.6.2 Hạn chế: Bùng nổ tổ hợp CP-SAT khi |V| > 1.000
│       └── 3.6.3 Hướng phát triển tiếp theo
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
