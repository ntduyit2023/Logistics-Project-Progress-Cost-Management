# Phân tích Chuyên sâu Cơ chế: Monte Carlo CPM Engine (Stochastic Simulation)

Tài liệu này phân tích chi tiết về cơ chế hoạt động, sự khác biệt so với các giải pháp hiện có, ưu nhược điểm và lập luận tại sao đồ án Quản lý Tiến độ và Chi phí Dự án lại bắt buộc phải cần đến cơ chế **Monte Carlo CPM Engine**.

---

## 1. Cơ chế hoạt động (How it works)

Mô-đun `MonteCarloCPMEngine` (tại `ai_pipeline/models/moi/monte_carlo_cpm.py`) không phải là một thuật toán AI học máy, mà là một **bộ giả lập ngẫu nhiên học (Stochastic Simulator)** dựa trên Mạng lưới Đường găng (CPM). Quá trình này diễn ra qua 4 bước:

### Bước 1: Khởi tạo & Sắp xếp Tô-pô (Topological Sort)
- Đọc danh sách Công việc (Tasks) và Quan hệ (Dependencies: FS, SS, FF, SF) để xây dựng đồ thị có hướng không chu trình (DAG).
- Dùng thuật toán sắp xếp Tô-pô (`nx.topological_sort`) để đảm bảo rằng khi tính toán cho một công việc, tất cả các công việc đứng trước nó (predecessors) đều đã được tính xong.

### Bước 2: Lấy mẫu thời lượng Beta-PERT có tích hợp AI
Trong hàng chục ngàn vòng lặp (ví dụ 10,000 iterations), thời lượng của mỗi công việc không cố định. Nó được "làm nhiễu" một cách khoa học bằng phân phối xác suất **Beta-PERT**:
- **Đầu vào từ AI:** Mô hình HGT (ở giai đoạn trước) truyền sang 3 thông số: `duration_factor`, `expected_delay` và `uncertainty_sigma`.
- **Đỉnh phân phối (Most Likely - $m$):** $m = \text{base\_duration} \times \text{duration\_factor} + \text{expected\_delay}$.
- **Cận dưới (Optimistic - $a$):** $a = m \times (1 - 2\sigma)$.
- **Cận trên (Pessimistic - $b$):** $b = m \times (1 + 3\sigma)$.
Hàm `sample_beta_pert(a, m, b)` sẽ sinh ra một con số ngẫu nhiên hội tụ quanh đỉnh $m$ nhưng có độ trải dài về 2 phía dựa vào độ rủi ro $\sigma$.

### Bước 3: Lan truyền CPM (Forward & Backward Pass)
Với tập hợp thời lượng vừa được lấy mẫu, hệ thống chạy thuật toán CPM kinh điển:
- **Forward Pass:** Quét từ đầu đến cuối mạng lưới, cộng dồn độ trễ (Lag) và xử lý linh hoạt 4 loại liên kết (FS, SS, FF, SF) để tìm ra Thời điểm bắt đầu sớm nhất (Early Start - ES) và Hoàn thành sớm nhất (Early Finish - EF). Trả về tổng thời gian hoàn thành dự án (Project Makespan).
- **Backward Pass:** Quét ngược từ cuối lên đầu mạng lưới để tìm ra Thời điểm muộn nhất (Late Start - LS và Late Finish - LF) mà không làm trễ dự án.
- **Tính Slack (Độ dự trữ):** $\text{Slack} = LS - ES$. Nếu $\text{Slack} = 0$, công việc đó rơi vào **Đường găng (Critical Path)** của vòng lặp hiện tại.

### Bước 4: Thống kê chỉ số (Statistics Aggregation)
Sau 10,000 vòng lặp, hệ thống gom dữ liệu lại và tính toán:
- **P50, P80, P95:** Xác suất hoàn thành dự án. (Ví dụ: P80 = 120 ngày nghĩa là có 80% cơ hội dự án xong trước 120 ngày).
- **Criticality Index (CI%):** Tỷ lệ % số lần một công việc trở thành Nút thắt (Nằm trên Đường găng). Ví dụ, Task A có $CI = 85\%$ nghĩa là trong 10,000 vòng mô phỏng, nó có mặt trên đường găng 8,500 lần.

---

## 2. Điểm khác biệt so với các phần mềm bên ngoài (MS Project, Primavera, v.v.)

| Đặc điểm | Các phần mềm QLDA truyền thống | Cơ chế của Đồ án (AI-Infused Monte Carlo) |
| :--- | :--- | :--- |
| **Bản chất đường găng** | **Tĩnh (Deterministic):** Chỉ có 1 đường găng duy nhất dựa trên số liệu ước tính ban đầu. | **Động (Stochastic):** Đường găng thay đổi liên tục. Sản lượng cuối cùng là Xác suất (CI%) thay vì câu trả lời "Có/Không". |
| **Xác định rủi ro (a, m, b)** | **Thủ công:** Con người phải tự điền tay 3 thông số Lạc quan, Khả dĩ, Bi quan cho từng công việc. Khó áp dụng cho dự án lớn. | **Tự động 100%:** AI (HGT) tự động ngoại suy độ trễ và độ lệch chuẩn ($\sigma$) dựa trên lịch sử để tính toán ra $a, m, b$. |
| **Mối tương quan (Correlation)** | Các rủi ro thường được xem xét độc lập. Cập nhật rủi ro của Task A hiếm khi tự động cập nhật rủi ro cho Task B. | **Graph-based:** Nhờ HGT ở khâu trước, nhiễu rủi ro của Task A đã ngầm chứa rủi ro của Task B và Resource C thông qua cơ chế Attention. |

---

## 3. Ưu và Nhược điểm (Pros & Cons)

### Ưu điểm vượt trội:
1. **Phản ánh đúng thực tế thi công (Realistic Risk Assessment):** Việc trễ hạn của dự án hiếm khi là một con số tuyến tính. Sự chậm trễ của móng sẽ kéo theo sự chậm trễ của mái nhà. Monte Carlo + CPM mô phỏng được "hiệu ứng domino" này.
2. **Khắc phục lỗi "Merge Bias" của phương pháp PERT cũ:** Phương pháp PERT truyền thống thường đánh giá thấp rủi ro tại các điểm hội tụ (nơi nhiều công việc kết thúc cùng lúc). Monte Carlo quét từng vòng lặp nên giải quyết triệt để vấn đề này.
3. **Phân loại mức độ ưu tiên:** Thay vì nói "Công việc X nằm trên đường găng", ta có thể nói "Công việc X có 92% rủi ro tạo thắt cổ chai, trong khi Công việc Y chỉ có 15%". Điều này giúp người quản lý phân bổ tài nguyên hiệu quả hơn.

### Nhược điểm & Thách thức:
1. **Chi phí tính toán (Computation Cost):** Việc chạy Forward & Backward Pass trên một đồ thị 10,000 lần là một tác vụ tốn CPU. Hệ thống hiện tại đang sử dụng cấu trúc `networkx` và vòng lặp `for` Python, có thể tạo ra điểm thắt cổ chai (bottleneck) nếu dự án có hàng chục ngàn Node. *(Trong tương lai có thể tối ưu bằng Cython hoặc vectorize bằng numpy).*
2. **Phụ thuộc vào chất lượng AI:** Nếu AI đưa ra $\sigma$ sai lệch, toàn bộ phân phối Beta-PERT sẽ bị sai, dẫn đến CI% bị sai.

---

## 4. Tại sao đồ án lại CẦN cơ chế này? (Sự tồn tại mang tính xương sống)

Trong toàn bộ luồng Pipeline (từ AI tới OR Solver), bộ mô phỏng Monte Carlo CPM đóng vai trò là **"Người phiên dịch và Chọn lọc" (Knowledge Bridge)**:

1. **Khắc phục khoảng trống ngôn ngữ giữa AI và OR:**
   - **AI (HGT)** chỉ học và nhả ra các con số mang tính dự báo, rời rạc cho từng Node (ví dụ: Task A trễ 2 tiếng, Task B trễ 5 tiếng).
   - **OR (CP-SAT Solver)** thì lại cần những bộ quy tắc logic Toán học cứng rắn (Ràng buộc thứ tự, Ngân sách...).
   - **Monte Carlo CPM** đứng ở giữa, nó nuốt các con số dự báo rời rạc của AI, nhào nặn qua quy luật đồ thị dự án (Network Logic), và sinh ra một bảng chỉ số duy nhất: **Criticality Index (CI%)**.

2. **Giảm tải cho bộ giải tối ưu hóa (CP-SAT):**
   - Bài toán xếp lịch dự án đa kỹ năng (RCPSP) là một bài toán NP-Hard. Nếu quăng toàn bộ 500 tasks vào bộ giải CP-SAT cùng với hàng chục ràng buộc, máy tính sẽ chạy mất hàng tuần không ra nghiệm.
   - Bằng cách sử dụng **CI%** thu được từ Monte Carlo, ta có thể xây dựng cơ chế **Heuristic-Guided Crashing**: Chỉ cho phép Solver tập trung tối ưu/đổ thêm tiền (Crashing) vào những công việc có **CI > 50%**. Những công việc râu ria ($CI \approx 0\%$) sẽ bị khóa lại. Điều này giúp không gian tìm kiếm (Search Space) của thuật toán OR thu hẹp lại hàng triệu lần.

**Tóm lại:** Nếu không có Monte Carlo CPM, đồ án sẽ bị đứt gãy. AI dự báo xong không biết để làm gì, còn bộ tối ưu CP-SAT thì sẽ bị treo cứng vì phải giải một khối lượng công việc khổng lồ, phi logic. Do đó, đây là "Trái tim" kết nối luồng Học máy (Machine Learning) và luồng Tối ưu hóa Vận trù (Operations Research).
