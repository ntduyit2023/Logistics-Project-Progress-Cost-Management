# Danh mục Biểu đồ và Hình ảnh Yêu cầu (Required Figures Tree)
*Dựa trên cấu trúc tuần tự và chuẩn mực khoa học của Báo cáo Đồ án 2 mẫu.*

Báo cáo Đồ án khoa học kỹ thuật yêu cầu mức độ trực quan hóa dữ liệu rất cao. Dưới đây là Cây cấu trúc (Tree Content) liệt kê chính xác các Hình ảnh (Figures), Biểu đồ (Charts) và Sơ đồ (Diagrams) trong thư mục `image` và vị trí sắp xếp, bố trí tương ứng của chúng trong mã nguồn các chương báo cáo:

```text
Danh mục Biểu đồ & Hình ảnh Báo cáo Đồ án GLPO
├── CHƯƠNG 1: TỔNG QUAN LÝ THUYẾT VÀ CƠ SỞ NGHIÊN CỨU
│   ├── Hình 1.1: Sơ đồ mô phỏng Mô hình tham chiếu SCOR trong chuỗi cung ứng.
│   ├── Hình 1.2: Minh họa Hiệu ứng Bullwhip (Sự khuếch đại dao động nhu cầu).
│   ├── Hình 1.3: Cấu trúc cơ bản của Sơ đồ mạng lưới AON (Đỉnh là Công việc, Cạnh là Quan hệ).
│   ├── Hình 1.4: Lưu đồ trực quan phép tính CPM (Minh họa các thông số ES, EF, LS, LF trên 1 Node).
│   ├── Hình 1.5: Đồ thị thể hiện mối quan hệ nghịch biến giữa Thời gian và Chi phí (Time-Cost Trade-off).
│   ├── Hình 1.6: Biểu đồ mô tả Đường biên Pareto (Pareto Frontier) trong không gian Đa mục tiêu (pareto_frontier.png).
│   ├── Hình 1.7: Đồ thị minh họa các đường cơ sở của EVM (Sự hội tụ / phân kỳ của PV, EV, AC).
│   ├── Hình 1.8: Cấu trúc truyền tin (Message Passing Mechanism) trong Mạng nơ-ron đồ thị (GNN).
│   └── Hình 1.9: Cơ chế tính toán Attention chi tiết trên các quan hệ dị thể trong lớp HGTConv (fig4_hgtconv_attention.drawio.png).
│
├── CHƯƠNG 2: PHƯƠNG TIỆN VÀ PHƯƠNG PHÁP NGHIÊN CỨU
│   ├── Hình 2.1: Sơ đồ luồng xử lý và kiến trúc hệ thống GLPO (fig1_pipeline_overview.drawio.png / TikZ Flowchart).
│   ├── Hình 2.2: Sơ đồ biểu diễn cấu trúc Đồ thị dị thể (Heterogeneous Graph Structure) của dự án C2012-04 (fig3_heterograph_structure.drawio.png).
│   ├── Hình 2.3: Sơ đồ quy trình tiền xử lý dữ liệu và làm sạch đồ thị (fig5_monte_carlo_cpm.drawio.png / TikZ Flowchart).
│   ├── Hình 2.4: Chiến lược phân tách dữ liệu Leave-One-Project-Out Cross-Validation (LOPO CV) cho hệ thống GNN (fig8_pretrain_finetune.drawio.png).
│   ├── Hình 2.5: Sơ đồ quy trình huấn luyện tiền kỳ tự giám sát Masked Autoencoder trên đồ thị dị thể (fig7_pretraining_flow.drawio.png).
│   ├── Hình 2.6: Kiến trúc mạng HGT Task Predictor tích hợp cơ chế Hybrid Readout Pooling và các đầu giải mã đa nhiệm (fig2_hgt_architecture.drawio.png).
│   ├── Hình 2.7: Sơ đồ luồng dữ liệu và tương tác kết xuất giữa Frontend React, Backend FastAPI, và PostgreSQL (fig10_frontend_rendering.drawio.png).
│   └── Hình 2.8: Sơ đồ khối lập trình logic CP-SAT Solver tối ưu đa mục tiêu (fig6_cpsat_pareto.drawio.png).
│
├── CHƯƠNG 3: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN
│   ├── [Mục 3.1] Hình 3.1: Giao diện trực quan mạng lưới đồ thị AON dự án trên ứng dụng web (hinh3_1_reactflow_network.jpg).
│   ├── [Mục 3.2] Hình 3.2: Biểu đồ Scatter Plot đối chiếu thời gian thi công dự báo của mô hình AI vs thời gian thi công thực tế (hinh3_7_regression_scatter.png).
│   ├── [Mục 3.3] Hình 3.3: Đường cong học tập đánh giá quá trình hội tụ Loss và R² Score qua 5-Fold Cross Validation (epoch.jpg / ket_qua_r2.jpg).
│   ├── [Mục 3.3] Hình 3.4: Bản đồ nhiệt trọng số Attention định vị các nút công việc tới hạn trên Dự án C2012-04 (hinh3_8_attention_heatmap.png).
│   ├── [Mục 3.3] Hình 3.5: Đường cong phân phối xác suất tích lũy CDF thời lượng dự án từ mô phỏng Monte Carlo CPM (cdf_risk.png).
│   ├── [Mục 3.3] Hình 3.6: Biểu đồ đánh giá năng lực dự báo phân loại rủi ro trễ tiến độ (hinh3_6_roc_confusion.png).
│   ├── [Mục 3.6] Hình 3.7: Biểu đồ hội tụ NLL Loss và các chỉ số sai số MAE, RMSE trong giai đoạn Pre-training (pretrain_loss.png).
│   ├── [Mục 3.7] Hình 3.8: Biểu đồ phân bổ nhu cầu tài nguyên nhân lực TRƯỚC khi tối ưu hóa trên Dự án C2012-04 (hinh3_3_resource_before.png).
│   ├── [Mục 3.7] Hình 3.9: Biểu đồ phân bổ nhu cầu tài nguyên nhân lực SAU khi tối ưu hóa làm mịn tài nguyên trên Dự án C2012-04 (hinh3_4_resource_after.png).
│   ├── [Mục 3.7] Hình 3.10: Biểu đồ đường cong Pareto Frontier thể hiện sự đánh đổi giữa Thời gian, Chi phí và Rủi ro trễ hạn (pareto_frontier.png).
│   ├── [Mục 3.7] Hình 3.11: Biểu đồ so sánh tiến trình hội tụ và chất lượng nghiệm của thuật toán di truyền GA với CP-SAT (hinh3_5_ga_convergence.png / sosanh.jpg).
│   ├── [Mục 3.8] Hình 3.12: Biểu đồ cột so sánh thời gian thực thi truy vấn đồ thị giữa ORM tiêu chuẩn và Recursive CTE (hinh3_2_query_latency.png).
│   └── [Mục 3.9] Hình 3.13: Bộ giao diện phần mềm trực quan Quản trị Tiến độ và Chi phí Dự án Logistics (hinh3_9a_dashboard.jpg - hinh3_9f_pareto_table.jpg / hinh3_9_evm_gantt_dashboard.png).
│
└── CHƯƠNG 4: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
    └── [Mục 4.2] Hình 4.1: Sơ đồ Concept đề xuất kiến trúc Cơ chế Chú ý Nâng cao (Advanced Attention) thay thế cho HGT cơ bản (hinh4_1_advanced_attention.png).
```

## Các Công cụ Cần dùng để Vẽ:
1. **Sơ đồ Kiến trúc & ERD (Hình 2.1 - 2.4, Hình 2.7):** Sử dụng `Mermaid.js`, `Draw.io` (app.diagrams.net), hoặc `Lucidchart`.
2. **Sơ đồ Thuật toán AI & Toán học (Hình 1.8, 1.9, Hình 2.5, 2.6):** Đề xuất dùng `OmniGraffle`, `Visio` hoặc tự vẽ bằng Python (`Graphviz`).
3. **Biểu đồ Dữ liệu định lượng (Hình 1.5, Hình 1.6, toàn bộ Hình Chương 3 trừ Ảnh chụp):** Sử dụng mã nguồn Python (sử dụng thư viện `matplotlib`, `seaborn`) để đảm bảo tính hàn lâm (độ phân giải 300 DPI, xuất file `.png` hoặc `.jpg`).
4. **Ảnh giao diện (Hình 3.1, Hình 3.9):** Ảnh chụp màn hình (Screenshots) chất lượng cao từ giao diện web React.js thực tế.
