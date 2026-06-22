# Thiết kế Pipeline Tối ưu hóa (AI Optimizer Engine)

Dưới đây là phương hướng xử lý thuật toán chi tiết (Algorithm Pipeline) của Backend AI. Mục tiêu tối thượng của Pipeline này là: **Trích xuất ra các giải pháp tối ưu nhất (ROI cao nhất) mà không bị vi phạm luật thi công thực tế, đồng thời loại bỏ tối đa các phép tính thừa thãi.**

## Phương Hướng Xử Lý Chi Tiết (The Processing Pipeline)

Pipeline của AI được chia làm 5 lớp (Layers) chạy tuần tự như sau:

### Bước 1: Khởi tạo Đồ thị & Quét hiện trạng (Graph Ingestion Layer)
*   **Action:** Đọc dữ liệu từ file Excel (Baseline Schedule, Risk Analysis, Resources).
*   **Process:** AI dựng toàn bộ dữ liệu thành một Đồ thị có hướng (Directed Acyclic Graph - DAG).
*   **Output:** Thuật toán duyệt đồ thị (Forward/Backward Pass) sẽ tự động tính toán ra các thông số mấu chốt tại thời điểm hiện tại: `Early Start`, `Late Finish`, `Total Float` và xác định chính xác các công việc tạo nên **Đường Găng (Critical Path)**.

### Bước 2: Lớp Cắt Tỉa & Giảm tải Công việc (Pruning Layer)
Đây là trái tim của việc giải quyết "Bài toán phình to không gian trạng thái" mà bạn vừa đề cập:
*   **Critical Path Pruning (Cho Crashing/Fast-Tracking):** Lập tức VỨT BỎ toàn bộ các tasks có `Total Float > 0` khỏi danh sách ứng viên rút ngắn tiến độ. Đẩy nhanh các task không nằm trên đường găng chẳng đem lại lợi ích gì về mặt thời gian, giúp loại bỏ 80% không gian tìm kiếm vô ích.
*   **Soft-Pruning cho Resource Leveling (Chấp nhận trễ hạn để tối ưu chi phí):** Không cấm tuyệt đối việc dời lịch các task trên đường găng (`Total Float = 0`). Thuật toán sẽ tính **Hàm Phạt (Penalty Function)**: Nếu tiền phạt trễ dự án (Schedule Delay Penalty) rẻ hơn rất nhiều so với việc thuê thêm thợ ngoài giờ (Crashing Cost), AI sẽ "mạnh dạn" đề xuất dời lịch task đó và chấp nhận trễ Deadline dự án để tối ưu Dòng tiền (Cashflow).

### Bước 3: Lớp Sinh Kịch bản (Action Generation Layer)
Chỉ trên một tập hợp rất nhỏ ứng viên (Candidates) còn sống sót sau Bước 2, AI mới bắt đầu kết hợp các `action_type`:
*   **Tạo Crashing Action:** Giảm `Duration` của task ứng viên đi 20% (Chạm mốc ranh giới `Optimistic`), tính lại `Cost/Unit` tăng thêm.
*   **Tạo Agenda Action:** Ghi đè biến `Working_Days_Array` thành `[1, 1, 1, 1, 1, 1, 1]` (Làm nguyên tuần).
*   **Tạo Compound Action:** Sinh ra các biến thể kết hợp (Vừa làm ngày nghỉ + Vừa tăng thợ).

### Bước 4: Lớp Kiểm duyệt Ràng buộc & Cắt nhánh (Validation & Beam Search Layer)
Với sự bùng nổ của Compound Actions, nếu tạo ra quá nhiều trường hợp sẽ gây lãng phí bộ nhớ. Lớp này không chỉ kiểm duyệt mà còn chặn số lượng nhánh sinh ra:
*   **Beam Search (Giới hạn Kịch bản):** Thuật toán chỉ giữ lại $N$ kịch bản tiềm năng nhất ở mỗi vòng lặp (Ví dụ: Chỉ giữ Top 50 nhánh có Tỉ lệ Time/Cost tốt nhất). Cắt bỏ ngay hàng vạn nhánh kém hiệu quả trước khi đi vào Validation sâu.
*   **Check Logic:** Dùng thuật toán phát hiện chu trình (Cycle Detection). Nếu hành động Fast Tracking tạo ra vòng lặp vô tận ➔ Reject!
*   **Check Time Constraint:** Nếu hành động làm `Duration` bị âm ➔ Reject!
*   **Check Resource Constraint:** Nếu tổng Demand vượt `Max_Availability`, thay vì vứt bỏ, hệ thống sinh ra một **Sub-task Leveling** (Gọi lại Lớp 2) để nỗ lực làm phẳng biểu đồ.

### Bước 5: Lớp Đánh giá Lợi ích & Xuất Output (Impact & ROI Evaluation Layer)
Những kịch bản "sống sót" qua được Bước 4 chắc chắn là những kịch bản **Khả thi 100% trong thực tế thi công**.
*   AI bắt đầu tính điểm `ROI Score` = (Tiền cứu được do không bị phạt trễ hạn) - (Tiền Cost Penalty do tăng ca).
*   Sắp xếp mảng (Sort) từ cao xuống thấp. Lấy Top 3 Insights ngon ăn nhất.
*   Format thành **JSON Schema** và xuất kết quả cuối cùng (End of Pipeline).

---
*(Kế hoạch này là tài liệu cốt lõi để xây dựng hệ thống AI Optimizer Engine bằng Python, NetworkX và Pandas).*
