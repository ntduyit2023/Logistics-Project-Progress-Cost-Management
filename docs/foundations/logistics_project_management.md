# 📦 Kiến Thức Nền Tảng: Quản Lý Dự Án & Tối Ưu Hóa Logistics

Tài liệu này giải thích các thuật ngữ, mô hình quản lý dự án và các bài toán tối ưu chi phí mà ứng dụng của bạn sẽ giải quyết.

---

## 1. Mạng Công Việc AON (Activity-on-Node)

Trong quản lý dự án, sơ đồ mạng lưới hoạt động AON là cách trực quan hóa phổ biến nhất:
*   Mỗi **nút (node)** là một công việc (Task).
*   Bên trong nút chứa các thông tin thời gian:
    *   **ES (Early Start):** Thời điểm sớm nhất có thể bắt đầu công việc.
    *   **EF (Early Finish):** Thời điểm sớm nhất có thể hoàn thành công việc ($EF = ES + \text{Duration}$).
    *   **LS (Late Start):** Thời điểm muộn nhất phải bắt đầu công việc để không làm trễ dự án.
    *   **LF (Late Finish):** Thời điểm muộn nhất phải hoàn thành công việc ($LF = LS + \text{Duration}$).
    *   **Slack (Thời gian dự trữ):** Khoảng thời gian trì hoãn tối đa cho phép của công việc mà không ảnh hưởng tới tiến độ chung ($Slack = LS - ES$).
    *   **Nút găng (Critical Node):** Nút có $Slack = 0$.

---

## 2. Bài Toán Ràng Buộc Tài Nguyên (Resource Constraints)

Trong thực tế, bạn không có vô hạn nhân sự hay phương tiện vận chuyển.
*   **Ví dụ:** Hoạt động A và Hoạt động B đều cần xe tải chuyên dụng loại 1 để vận chuyển hàng hóa, nhưng công ty bạn chỉ có **đúng 1 chiếc xe**.
*   **Vấn đề:** Nếu xếp lịch theo lý thuyết sớm nhất (Early Start), cả A và B sẽ chạy song song $\rightarrow$ Xảy ra hiện tượng **quá tải tài nguyên (Resource Conflict)**.
*   **Giải pháp:** 
    1.  *Resource Smoothing:* Dịch chuyển hoạt động không găng (sử dụng thời gian Slack của nó) lùi lại để tránh trùng lịch dùng xe với hoạt động găng.
    2.  *Resource-Constrained Scheduling:* Nếu cả 2 đều là hoạt động găng, bắt buộc phải chọn 1 hoạt động chạy trước, hoạt động kia phải chờ $\rightarrow$ Thời gian dự án bị kéo dài ra (Ví dụ: từ 66 ngày kéo dài thành 96 ngày).

---

## 3. Bài Toán Rút Ngắn Tiến Độ & Tối Ưu Chi Phí (Crashing)

Chủ đầu tư yêu cầu bạn hoàn thành dự án sớm hơn kế hoạch ban đầu (ví dụ: rút ngắn từ 14 tuần xuống 12 tuần để kịp mùa cao điểm vận tải).

Để rút ngắn thời gian thực hiện một công việc, bạn phải bỏ thêm tiền (làm thêm giờ - Overtime, hoặc thuê ngoài - Contractor). Việc này gọi là **Crashing**.

### Công thức tính toán chi phí:
*   **Chi phí trực tiếp (Direct Cost):** Tăng lên khi bạn rút ngắn thời gian công việc (tiền trả thêm giờ 1.5x thứ Bảy, 3.0x Chủ Nhật, tiền thuê nhà thầu).
*   **Chi phí gián tiếp (Indirect Cost / Overhead):** Phí vận hành văn phòng, kho bãi. Chi phí này tính theo thời gian dự án (ví dụ: $500/tuần). Dự án càng ngắn, chi phí này càng giảm.
*   **Tiền phạt (Penalty):** Phạt nếu hoàn thành trễ hơn mốc yêu cầu (ví dụ: phạt $2,000/tuần trễ).
*   **Tiền thưởng (Bonus):** Thưởng nếu hoàn thành sớm (ví dụ: thưởng $3,000/tuần sớm).

$$\text{Tổng Chi Phí} = \text{Chi Phí Trực Tiếp} + (\text{Overhead} \times \text{Số Tuần}) + \text{Tiền Phạt} - \text{Tiền Thưởng}$$

*Thuật toán tối ưu (MILP / GA) của bạn cần tìm ra phương án rút ngắn những công việc nào trên đường găng để **Tổng Chi Phí** trên là nhỏ nhất.*

---

## 4. Quản Lý Giá Trị Đạt Được (Earned Value Management - EVM)

EVM là phương pháp đo lường tiến độ và chi phí tại một thời điểm kiểm tra (ví dụ: cuối tuần thứ 5 của dự án).

*   **PV (Planned Value - BCWS):** Giá trị công việc theo kế hoạch dự kiến sẽ hoàn thành tại thời điểm kiểm tra.
*   **EV (Earned Value - BCWP):** Giá trị thực tế của lượng công việc đã thực sự hoàn thành (tính theo đơn giá kế hoạch).
*   **AC (Actual Cost - ACWP):** Số tiền thực tế đã chi ra để hoàn thành lượng công việc đó.

### Các chỉ số đánh giá sức khỏe dự án:
*   **Chỉ số hiệu suất tiến độ (SPI):** $SPI = EV / PV$.
    *   $SPI > 1$: Dự án đang nhanh hơn tiến độ kế hoạch.
    *   $SPI < 1$: Dự án đang bị chậm tiến độ.
*   **Chỉ số hiệu suất chi phí (CPI):** $CPI = EV / AC$.
    *   $CPI > 1$: Dự án đang chi tiêu dưới ngân sách (tiết kiệm).
    *   $CPI < 1$: Dự án đang bị vượt ngân sách (lãng phí).

---

## 📚 5. Tài Liệu Tham Khảo Nền Tảng (Foundational References)

Để trích dẫn học thuật vào luận văn hoặc tìm hiểu sâu hơn các kiến thức quản lý dự án chuẩn quốc tế, bạn có thể tham khảo các nguồn sau:

1.  **Bài báo sáng lập Phương pháp Đường găng (Critical Path Method - CPM):**
    *   *James E. Kelley Jr. & Morgan R. Walker (1959)*. **"Critical-Path Planning and Scheduling"**. *1959 Proceedings of the Eastern Joint Computer Conference*.
    *   *Ý nghĩa:* Đây là tài liệu lịch sử đầu tiên đặt nền móng toán học cho CPM, chuyển đổi cách lập lịch dự án từ sơ đồ cột (Gantt cũ) sang đồ thị topo mạng công việc.
2.  **Sách giáo trình Quản lý dự án chuẩn mực:**
    *   *Project Management Institute (PMI) (2019)*. **"Practice Standard for Earned Value Management"** (3rd Edition).
    *   *Ý nghĩa:* Tiêu chuẩn thực hành chính thống toàn cầu của Viện Quản lý Dự án Hoa Kỳ (PMI) về EVM, cung cấp đầy đủ công thức và cách kiểm soát tiến độ dự án.
3.  **Sách hướng dẫn áp dụng thực tế:**
    *   *Quentin W. Fleming & Joel M. Koppelman (2010)*. **"Earned Value Project Management"** (4th Edition).
    *   *Ý nghĩa:* Cuốn sách chi tiết và dễ hiểu nhất giải thích cách áp dụng EVM vào thực tế doanh nghiệp để dự báo chính xác chi phí và tiến độ khi hoàn thành.
