# Cấu trúc Cây Báo cáo Đồ án Chi tiết (Detailed Thesis Tree Content)
*Áp dụng tiêu chuẩn Kỹ sư Nghiên cứu (Research-Engineer) - Định lượng, Sâu sắc, Khoa học.*

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
│   │   ├── 1.3.1 Bài toán RCPSP: Giới hạn tài nguyên tái tạo (Renewable) và không tái tạo (Non-renewable)
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
├── CHƯƠNG 2: KIẾN TRÚC HỆ THỐNG VÀ PHƯƠNG PHÁP LUẬN ĐỀ XUẤT
│   ├── 2.1 Thiết kế Hệ thống và Phân tích Yêu cầu (System Design)
│   │   ├── 2.1.1 Sơ đồ Kiến trúc Tổng thể (Microservices, RESTful API với FastAPI)
│   │   ├── 2.1.2 Sơ đồ Tuần tự (Sequence Diagram): Luồng tương tác giữa Frontend, Backend và AI Pipeline
│   │   └── 2.1.3 Thiết kế Cơ sở Dữ liệu Quan hệ (ERD - Entity Relationship Diagram) trên PostgreSQL
│   ├── 2.2 Động cơ Đồ thị Cốt lõi (Core Graph Engine)
│   │   ├── 2.2.1 Lưu trữ Đồ thị phân cấp: Ứng dụng Recursive CTE để truy vấn cấu trúc mạng lưới (O(V+E))
│   │   ├── 2.2.2 Thuật toán CPM Cải tiến: Tính toán mảng ES, EF, LS, LF và Slack
│   │   └── 2.2.3 Phân hệ Xác định Đường găng (Critical Path) và Cảnh báo Xung đột Tài nguyên (Resource Conflict Detection)
│   ├── 2.3 Thu thập, Tiền xử lý và Chuẩn hóa Dữ liệu Dự án
│   │   ├── 2.3.1 Nguồn dữ liệu MFET 3008/5040 (DSLIB Format)
│   │   ├── 2.3.2 Phân tách 38 loại chi phí (G1-G7) cho từng Node
│   │   └── 2.3.3 Pipeline Chuẩn hóa: Imputation (xử lý thiếu hụt) và Min-Max Scaling
│   ├── 2.4 Bộ Tối ưu hóa Lai (Hybrid Optimization Engine)
│   │   ├── 2.4.1 Mô hình Toán học MILP cho Crashing: 
│   │   │   ├── Định nghĩa biến quyết định (Binary/Integer variables)
│   │   │   ├── Hàm mục tiêu (Objective Function): Min(Total Cost)
│   │   │   └── Tập Ràng buộc (Constraints): Ràng buộc logic (Precedence) và Ràng buộc năng lực (Capacity)
│   │   ├── 2.4.2 Thuật toán Di truyền (GA) cho cấu trúc Lịch trình:
│   │   │   ├── Mã hóa Nhiễm sắc thể (Chromosome Encoding): Priority-based hoặc Permutation-based
│   │   │   ├── Hàm Độ thích nghi (Fitness Function) kết hợp Penalty
│   │   │   └── Các toán tử di truyền: Lai ghép (Crossover) và Đột biến (Mutation) duy trì đồ thị DAG
│   │   └── 2.4.3 Kỹ thuật lai (Hybridization): Tiêm nghiệm MILP làm "Hạt giống ưu tú" (Elite Seed) cho quần thể GA
│   ├── 2.5 Kiến trúc AI Dự báo rủi ro (AI Predictive Pipeline)
│   │   ├── 2.5.1 Trích xuất đặc trưng Tô-pô (In/Out-degree) và Huấn luyện Tự giám sát (Pre-training với MAE)
│   │   ├── 2.5.2 Tinh chỉnh mô hình Học có giám sát (Supervised Fine-tuning): Cấu trúc mạng HGT và Attention Heads
│   │   └── 2.5.3 Cấu hình Hàm suy hao (Loss Function) cho bài toán dự báo liên tục (MSE/MAE) và phân loại nhị phân (Cross-Entropy)
│   ├── 2.6 Thiết kế Giao diện Trực quan (UI/UX Design)
│   │   ├── 2.6.1 Tích hợp React-Flow: Node-based Editor và Custom Nodes cho Tasks
│   │   ├── 2.6.2 Thuật toán Dagre (Cytoscape.js): Auto-layout mạng lưới AON tránh chồng chéo
│   │   └── 2.6.3 Phân hệ Quản lý Giá trị Đạt được (EVM Dashboard) & Biểu đồ Gantt Tương tác
│   └── 2.7 Triển khai Hệ thống và Vận hành (Deployment & DevOps)
│       ├── 2.7.1 Containerization bằng Docker và cấu hình Docker Compose (Dev/Prod Profiles)
│       └── 2.7.2 Phân phối dữ liệu nội bộ bằng Scripts (reload_docker_db.py)
│
├── CHƯƠNG 3: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN
│   ├── 3.1 Môi trường Thực nghiệm và Dữ liệu Test
│   │   ├── 3.1.1 Cấu hình phần cứng (CPU/RAM) và Môi trường Docker (Dev Profile)
│   │   └── 3.1.2 Tổng quan  C2012-04 
│   ├── 3.2 Đánh giá Hiệu năng Hệ thống Đồ thị (System Performance)
│   │   ├── 3.2.1 Thời gian thực thi truy vấn (Query Latency): So sánh Recursive CTE vs ORM tiêu chuẩn
│   │   └── 3.2.2 Mức tiêu thụ Bộ nhớ (Memory Footprint) khi scale lên đồ thị 1000+ nodes
│   ├── 3.3 Đánh giá Kết quả Tối ưu hóa (Optimization Evaluation)
│   │   ├── 3.3.1 Kết quả Crashing: Mức độ giảm thời gian (Makespan) và Chi phí gia tăng (Marginal Cost)
│   │   ├── 3.3.2 Tối ưu hóa Tài nguyên (Resource Leveling): Giảm phương sai biểu đồ phân bổ nhân lực
│   │   └── 3.3.3 Biểu đồ đánh đổi Pareto (Pareto Frontier) của CP-SAT và thời gian phân bổ không gian tìm kiếm
│   ├── 3.4 Đánh giá Mô hình Trí tuệ Nhân tạo (AI Metrics)
│   │   ├── 3.4.1 Độ chính xác dự báo thời gian: MAE, RMSE, MAPE
│   │   └── 3.4.2 Mức độ giải thích (Explainability): Trọng số Attention trên các nút Đường găng
│   └── 3.5 Bàn luận (Discussion)
│       ├── 3.5.1 Tính hiệu quả của việc phân ly 38 loại chi phí (G1-G7) vào thực tiễn Logistics
│       └── 3.5.2 Hạn chế của hệ thống: Hiện tượng bùng nổ tổ hợp (Combinatorial Explosion) của CP-SAT với dự án siêu lớn
│
└── CHƯƠNG 4: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
    ├── 4.1 Kết luận chung về đề tài
    │   ├── 4.1.1 Đóng góp về mặt lý luận khoa học (Graph AI + Hybrid Optimization)
    │   └── 4.1.2 Đóng góp về mặt thực tiễn kỹ thuật (Microservices, Recursive CTE)
    └── 4.2 Đề xuất hướng phát triển
        ├── 4.2.1 Cải tiến Bộ Tối ưu hóa: Áp dụng Tìm kiếm Lân cận Lớn (Large Neighborhood Search - LNS) kết hợp CP-SAT cho dự án quy mô tỷ trọng cao
        ├── 4.2.2 Nâng cấp Kiến trúc Học máy Đồ thị: Áp dụng cơ chế Chú ý Nâng cao (Advanced Attention Mechanisms) như Graphormer
        └── 4.2.3 Mở rộng Dữ liệu Huấn luyện (Data Scaling): Thu thập thêm các bộ dữ liệu dự án thực tế để tăng cường tính tổng quát (Generalization) của mô hình AI
```

## Ghi chú Triển khai (Implementation Notes)
- Toàn bộ các công thức ở Chương 1 (EVM, Crashing, HGT) bắt buộc phải trình bày bằng chuẩn **LaTeX**.
- Các bảng so sánh ở Chương 3 cần hiển thị rõ ràng độ lệch chuẩn (Standard Deviation) và mức ý nghĩa thống kê (p-value nếu có).
- Trích dẫn (Citation) ở mục 1.6 tuân thủ nghiêm ngặt tiêu chuẩn IEEE từ các kho lưu trữ uy tín.
