# Phân tích Chuyên sâu Cơ chế: CP-SAT Pareto Optimization

Tài liệu này phân tích chi tiết về cơ chế hoạt động, sự khác biệt so với các phần mềm truyền thống, ưu nhược điểm và vai trò chốt chặn cuối cùng của module **CP-SAT Pareto Optimization** trong hệ thống lõi AI Pipeline.

---

## 1. Cơ chế hoạt động (How it works)

Module `CPSATParetoSolver` (tại `ai_pipeline/models/moi/cpsat_pareto_solver.py`) sử dụng thư viện OR-Tools của Google. Bản chất của nó là giải bài toán Xếp lịch Dự án Đa kỹ năng (RCPSP). Nó vận hành qua 4 bước cốt lõi:

### Bước 1: Xây dựng Chế độ thi công (Modes Builder)
Đầu tiên, hệ thống không coi mỗi công việc là một khối cứng ngắc. Với mỗi Task, module `build_task_modes` sẽ tạo ra 4 phương án thi công (Execution Modes):
1. **Normal:** Làm việc giờ hành chính tiêu chuẩn, chi phí gốc.
2. **OT (Overtime):** Làm thêm giờ, thời gian thi công rút ngắn nhưng đơn giá nhân công sẽ bị nhân với hệ số phụ trội (Overtime Multiplier). Hệ số này **hoàn toàn động**, được hệ thống nội suy từ cơ sở dữ liệu của từng loại Tài nguyên (ví dụ: Thợ bậc cao có hệ số tăng ca x2.0, Thợ phụ x1.5).
3. **AddRes (Add Resources):** Thuê thêm máy móc/nhân công ngoài, thời gian rút ngắn nhưng tốn chi phí thuê ngoài.
4. **Hybrid:** Kết hợp cả làm thêm giờ và thuê thêm người (Siêu tốc độ, Siêu đắt đỏ).

### Bước 2: Khai báo Biến quyết định (Decision Variables)
Đây là bước định hình không gian toán học cho toàn bộ dự án. Cần lưu ý: Việc khai báo biến được **thực hiện lặp lại cho TỪNG TASK một**, nhưng cái đích cuối cùng của thuật toán là **tối ưu hóa cho TOÀN BỘ DỰ ÁN**. 

Với mỗi công việc (Task), bộ giải CP-SAT tạo ra một "bộ khung biến số" như sau:

1. **Biến Miền Giá trị (`start` và `end`):**
   - Không giống lập trình định lượng truyền thống, biến `start` là một **Miền giá trị (Domain)** liên tục. Ban đầu, hệ thống thiết lập miền giá trị từ ngày 0 đến đường chân trời thời gian (Horizon).
   - Giá trị `start` do bộ giải CP-SAT nội suy thông qua quá trình lan truyền và thỏa mãn các phương trình ràng buộc.
   - Giá trị `end` là biến phụ thuộc, được liên kết toán học với `start` và thời lượng (duration) của công việc.

2. **Biến chỉ báo (Boolean `presence_var`):**
   - Với 4 phương án thi công (4 Modes), mô hình khởi tạo 4 "Khoảng thời gian tùy chọn" (Optional Intervals) giới hạn giữa `start` và `end`.
   - Mỗi khoảng tùy chọn này được kiểm soát bởi một biến Boolean (giá trị 0 hoặc 1). Thuật toán thiết lập ràng buộc cứng: **$Mode_1 + Mode_2 + Mode_3 + Mode_4 = 1$**.
   - Bộ giải chỉ được phép kích hoạt một Mode duy nhất. Nếu $Mode_2$ (Overtime - 7 ngày) được gán giá trị 1, hệ thống xác lập phương trình động: `end = start + 7`.
   
Thông qua mô hình Boolean này, thuật toán có khả năng đánh giá hàng triệu tổ hợp phương án thi công giữa các công việc mà không bị bùng nổ tổ hợp (combinatorial explosion).

3. **Cơ chế Tìm kiếm không gian nghiệm (Search Mechanism):**
   Thay vì thử nghiệm tuyến tính (brute-force), CP-SAT tích hợp 3 chiến thuật cốt lõi của Trí tuệ nhân tạo (AI Search) nhằm xác định giá trị `start`:
   - **Lan truyền ràng buộc (Domain Propagation):** Dựa trên cấu trúc đồ thị, nếu Task A kết thúc sớm nhất vào ngày 10 và tuân thủ liên kết Finish-to-Start (FS) với Task B, hệ thống tự động loại bỏ các giá trị từ 0 đến 9 khỏi miền `start` của Task B. Hiệu ứng lan truyền này loại bỏ tức thời các không gian nghiệm không khả thi dọc theo toàn bộ vòng đời dự án.
   - **Rẽ nhánh (Branching):** Khi quá trình lan truyền suy biến, thuật toán rẽ nhánh bằng cách dự phóng (assign) một giá trị cụ thể cho biến `start`, từ đó tiếp tục kích hoạt chuỗi lan truyền ràng buộc mới.
   - **Quay lui & Học lỗi (Backtracking & Clause Learning):** Khi một nhánh dự phóng dẫn đến mâu thuẫn ràng buộc (ví dụ: vượt ngưỡng giới hạn tài nguyên tại cuối chu kỳ), hệ thống kích hoạt quay lui (backtrack). Cơ chế \textbf{Clause Learning} tự động trích xuất nguyên nhân gây lỗi thành một quy tắc ràng buộc mới (learned clause), ngăn ngừa mô hình lặp lại sai lầm trong các nhánh tìm kiếm tương lai.

### Bước 3: Áp đặt Ràng buộc (Constraints)
- **Precedence Constraints (Ràng buộc Trình tự):** Công việc B chỉ được bắt đầu sau khi công việc A hoàn thành cộng thêm độ trễ (Lag). Áp dụng chặt chẽ cho 4 loại liên kết FS, SS, FF, SF.
- **Cumulative Constraints (Ràng buộc Tài nguyên Tuyến tính):** Đảm bảo tại bất kỳ một ngày nào trên công trường, tổng số nhân công/máy móc của TẤT CẢ các công việc đang thi công không được vượt quá năng lực tối đa của công ty. Đây là ràng buộc làm cho bài toán trở nên NP-Hard.

### Bước 4: Tối ưu đa mục tiêu (Grid Sweep Pareto)
Hàm mục tiêu được thiết lập để tối thiểu hóa đồng thời 3 yếu tố:
$$ \text{Minimize} \quad Z = \alpha \cdot \text{Makespan} + \beta \cdot \text{Total Cost} + \gamma \cdot \text{Total Risk} $$
Thay vì chạy 1 lần, hệ thống sử dụng vòng lặp (Grid Sweep) trượt các hệ số $\alpha, \beta, \gamma$ từ $0 \rightarrow 1$ để sinh ra một tập hợp các phương án (Ví dụ: Phương án 1 siêu rẻ nhưng mất 100 ngày, Phương án 5 cực nhanh chỉ 70 ngày nhưng tốn gấp đôi tiền). Tập hợp này tạo thành một **Đường cong Pareto (Pareto Front)**.

---

## 2. Giải phẫu kỹ thuật chuyên sâu (Deep Dive Workflow)

Để làm rõ các câu hỏi về cơ chế ngầm của luồng dữ liệu, đây là quy trình chi tiết:

### A. Máy tính biết Mode nào tốn bao nhiêu thời gian/chi phí từ đâu?
Trước khi đưa vào bộ giải, hàm `build_task_modes()` (trong `modes_builder.py`) sẽ đóng vai trò tính toán trước toàn bộ thông số cho 4 Modes. 
- **Tính Thời gian:** Dựa vào khối lượng công việc (Effort) và cấu hình tài nguyên. Ví dụ: Mode Normal làm 8 tiếng/ngày mất 10 ngày. Mode OT làm 12 tiếng/ngày sẽ rút xuống còn 7 ngày.
- **Tính Chi phí:** Mode Normal tính theo đơn giá gốc. Mode OT sẽ tra cứu hệ số phụ trội (Overtime Multiplier) từ cơ sở dữ liệu của loại nhân công đó (ví dụ x1.5) để cộng thêm vào chi phí.
- Sau khi tính xong, nó đóng gói thành một danh sách (Ví dụ: Mode 1: `dur=10, cost=100$`, Mode 2: `dur=7, cost=140$`) rồi ném vào cho CP-SAT chọn lựa.

### B. Căn cứ xác định Miền giá trị khởi tạo (Horizon Bound)
Miền giá trị ban đầu là `[0, Horizon]`. Tham số **Horizon** (Đường chân trời thời gian) được ước lượng một cách hệ thống nhằm tránh lãng phí tài nguyên bộ nhớ:
- Hệ thống tổng hợp thời lượng dài nhất (chế độ Normal) của toàn bộ các tác vụ và nhân hệ số dự phòng 2.
- `Horizon = Sum(Duration_Normal) * 2`.
- Cơ chế này đảm bảo biến `start` luôn nằm trong giới hạn khả thi ngay cả ở tình huống xấu nhất (worst-case scenario), khi tất cả các công việc thi công nối tiếp tuyến tính.

### C. Cơ chế tạo ra nhiều phương án Pareto
Hệ thống không gọi hàm `solve()` 1 lần. Nó dùng một vòng lặp `for` (Grid Sweep) thay đổi 2 thứ:
1. **Trọng số $\alpha, \beta$:** Từ việc coi trọng Tiền bạc (Cost) dần dần dịch chuyển sang coi trọng Thời gian (Makespan).
2. **Số lượng Task được phép Crashing:** Phương án 1 (Rẻ nhất) hệ thống khoá 100% Task ở chế độ Normal. Phương án 5 (Nhanh nhất), hệ thống mở khoá cho phép 20% số lượng Task nguy hiểm nhất (dựa trên điểm rủi ro CI% của Monte Carlo) được quyền chọn làm OT hoặc AddRes. Mỗi lần thay đổi cấu hình, nó lại gọi CP-SAT giải lại 1 lần, từ đó thu được 1 phổ các phương án.

### D. Ràng buộc Lịch làm việc (Calendar / Agenda) nằm ở đâu?
Thực tế, **bộ giải CP-SAT không hề biết Thứ 7, Chủ Nhật hay Lễ Tết là gì.** Việc chèn Lịch làm việc vào thuật toán tối ưu toán học (vốn chỉ hiểu con số liên tục) là cực kỳ nặng nề. Do đó, hệ thống sử dụng một thủ thuật thông minh:
- **Bên trong CP-SAT:** Toàn bộ thời gian (start, end, duration) được quy đổi hết ra **Số giờ làm việc thực tế (Working Hours)** (dải số liên tục 1, 2, 3...). CP-SAT giải và xếp lịch trên không gian giờ liên tục này.
- **Bên ngoài (Sau khi giải xong):** Lúc xuất kết quả, file `schedule_extractor.py` sẽ sử dụng module `WorkingCalendarEngine`. Nó lấy con số "Giờ làm việc" của CP-SAT, chiếu lên Lịch thực tế, tự động nhảy cóc qua các ngày nghỉ lễ, cuối tuần để xuất ra DateTime thực (VD: 08:00 Ngày 15/08/2026) cho biểu đồ Gantt.

---

## 3. Điểm khác biệt so với các phần mềm/giải pháp bên ngoài

| Đặc điểm | MS Project / Primavera / Solver truyền thống | Cơ chế của Đồ án (CP-SAT Heuristic-Guided) |
| :--- | :--- | :--- |
| **Bản chất của Nghiệm** | Xuất ra **1 lịch trình duy nhất** (Thường là kết quả của việc ép tiến độ vô tội vạ). | Xuất ra **Nhiều Kịch bản Pareto** (Trade-off). Người dùng (Giám đốc) có quyền chọn phương án phù hợp với tình hình tài chính. |
| **Cách ép tiến độ (Crashing)** | Cào bằng. Ép người quản lý phải tự ngồi chọn bằng tay xem nên ép công việc nào. | **Heuristic-Guided:** Hệ thống khoá toàn bộ các công việc râu ria. Nó CHỈ cho phép mở tính năng OT/AddRes đối với các công việc có $CI > 0\%$ (do Monte Carlo báo cáo). |
| **Sức mạnh tính toán** | Dùng thuật toán Heuristic truyền thống, dễ bị kẹt ở nghiệm cục bộ (Local Optima). | Dùng **Google CP-SAT** (Constraint Programming - Satisfiability). Thuật toán tối ưu hóa tổ hợp hàng đầu thế giới, kết hợp chặt chẽ với logic AI. |

---

## 3. Ưu và Nhược điểm (Pros & Cons)

### Ưu điểm vượt trội:
1. **Thu hẹp Không gian Tìm kiếm (Search Space Reduction):** Nếu dự án có 1000 tasks, mỗi task có 4 modes $\rightarrow$ Có $4^{1000}$ tổ hợp. Máy tính lượng tử cũng không giải nổi. Nhưng nhờ Monte Carlo chỉ điểm ra 50 tasks có nguy cơ trễ hạn (CI > 0%), CP-SAT chỉ áp dụng 4 Modes cho 50 tasks này. 950 tasks còn lại bị ép cứng ở Mode Normal. Không gian tìm kiếm bị thu hẹp hàng tỷ lần, giúp Solver xuất ra kết quả trong vài giây.
2. **Trao quyền cho con người:** Việc cung cấp một phổ (Spectrum) các phương án từ Rẻ đến Đắt giúp Ban Giám đốc có dữ liệu định lượng rõ ràng để ra quyết định đầu tư, thay vì ép AI chọn hộ 1 kết quả duy nhất.
3. **Thực thi ngay lập tức:** Kết quả trả ra không chỉ là con số dự báo, mà là tọa độ thời gian (Start Date, End Date) từng ngày của từng Task, có thể kết xuất thẳng ra biểu đồ Gantt.

### Nhược điểm & Thách thức:
1. **NP-Hard Barrier:** Dù đã dùng AI để thu hẹp không gian tìm kiếm, nếu dự án có quá nhiều ràng buộc tài nguyên đan chéo (Cumulative Constraint), OR-Tools vẫn có thể bị Time-Out (chạy hết 15-30 giây vẫn không chứng minh được nghiệm là Tối ưu tuyệt đối - Optimal, mà chỉ ra nghiệm Khả thi - Feasible).
2. **Khó tinh chỉnh Trọng số:** Việc thiết kế hàm mục tiêu kết hợp Thời gian, Tiền bạc và Rủi ro đòi hỏi việc chuẩn hóa (Normalize) các đơn vị rất phức tạp. (1 ngày trễ hạn thì tương đương bao nhiêu VNĐ?).

---

## 4. Tại sao đồ án lại CẦN cơ chế này? (Mảnh ghép cuối cùng)

Trong hệ sinh thái AI Pipeline của đồ án, nếu chỉ dừng lại ở HGT (dự báo) và Monte Carlo (đánh giá rủi ro), chúng ta mới chỉ đóng vai trò là "Nhà phân tích / Cố vấn". Chúng ta mới chỉ nói cho chủ đầu tư biết: *"Dự án này có nguy cơ trễ 20 ngày, nguyên nhân do đổ bê tông"*.

Nhưng Quản lý Dự án không chỉ cần lời cảnh báo, họ cần **GIẢI PHÁP HÀNH ĐỘNG**.

**CP-SAT Pareto Optimization** chính là "Nhà thiết kế giải pháp". Nó tiếp nhận lời cảnh báo của AI, và trả lời câu hỏi: *"Vậy bây giờ tôi phải bỏ thêm bao nhiêu tiền thuê thợ làm đêm vào khâu đổ bê tông để cứu dự án?"*. 

Nhờ cơ chế này, luồng đi của đồ án mới thực sự khép kín:
**Dữ liệu thô $\rightarrow$ Dự báo (HGT) $\rightarrow$ Phân tích rủi ro (Monte Carlo) $\rightarrow$ Đưa ra Giải pháp Tối ưu (CP-SAT Pareto).**
