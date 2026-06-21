# 📐 Phân Tích Kỹ Thuật Case Study 21 Hoạt Động (A-U)

Tài liệu này chuyển đổi toàn bộ đề bài và dữ liệu của **MFET 3008/5040 Case Study** thành cấu trúc toán học, thuật toán và mô hình dữ liệu để bạn lập trình trực tiếp vào ứng dụng GLPO.

---

## 1. Biểu Diễn Đồ Thị DAG của Dự Án (JSON Format)

Để xây dựng module tính toán CPM (Đường găng), bạn cần định nghĩa cấu trúc đồ thị của 21 hoạt động (A → U) dưới dạng cấu trúc dữ liệu. Dưới đây là dữ liệu chuẩn hóa dạng JSON:

```json
{
  "A": { "name": "Architectural decisions", "duration": 4, "predecessors": [], "resources": {"Design_Comp": 1, "Design_Mech": 1} },
  "B": { "name": "Hardware specifications", "duration": 6, "predecessors": ["A"], "resources": {"Design_Comp": 1, "Design_Mech": 1, "Dev_Mech": 1, "Assembly_Mech": 1} },
  "C": { "name": "Software specifications", "duration": 7, "predecessors": ["A"], "resources": {"Design_Comp": 1, "Dev_Comp": 1, "Assembly_Comp": 1} },
  "D": { "name": "Conveyor design", "duration": 8, "predecessors": ["B"], "resources": {"Design_Mech": 1, "Dev_Mech": 1} },
  "E": { "name": "Hardware design", "duration": 6, "predecessors": ["B"], "resources": {"Design_Comp": 1, "Design_Mech": 1, "Dev_Mech": 1} },
  "F": { "name": "Software design", "duration": 12, "predecessors": ["C"], "resources": {"Design_Comp": 1, "Dev_Comp": 1} },
  "G": { "name": "Operating system documentation", "duration": 10, "predecessors": ["C"], "resources": {"Dev_Comp": 1, "Documentation": 1} },
  "H": { "name": "Hardware detail drawings", "duration": 8, "predecessors": ["E", "F"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1, "Documentation": 1} },
  "I": { "name": "Software programming", "duration": 16, "predecessors": ["G"], "resources": {"Design_Comp": 1, "Documentation": 1} },
  "J": { "name": "Software verification/testing", "duration": 12, "predecessors": ["I"], "resources": {"Dev_Comp": 1, "Assembly_Comp": 1, "Documentation": 1} },
  "K": { "name": "Conveyor detailed drawings", "duration": 7, "predecessors": ["D"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1, "Documentation": 1} },
  "L": { "name": "Drawing verification/Minor integration", "duration": 9, "predecessors": ["H", "K"], "resources": {"Dev_Comp": 1, "Assembly_Comp": 1, "Assembly_Mech": 1} },
  "M": { "name": "Prototype development", "duration": 4, "predecessors": ["H"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1} },
  "N": { "name": "Prototype installation", "duration": 7, "predecessors": ["J", "M"], "resources": {"Assembly_Comp": 1, "Assembly_Mech": 1} },
  "O": { "name": "Hardware order/delivery", "duration": 7, "predecessors": ["L"], "resources": {"Dev_Mech": 1, "Purchase": 1} },
  "P": { "name": "System Interface", "duration": 5, "predecessors": ["L"], "resources": {"Dev_Mech": 1, "Assembly_Mech": 1} },
  "Q": { "name": "Hardware assembly", "duration": 4, "predecessors": ["O", "P"], "resources": {"Assembly_Comp": 1, "Assembly_Mech": 1} },
  "R": { "name": "Hardware/software Integration", "duration": 5, "predecessors": ["N", "Q"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1, "Assembly_Comp": 1, "Assembly_Mech": 1} },
  "S": { "name": "Hardware/software documentation", "duration": 2, "predecessors": ["R"], "resources": {"Dev_Comp": 1, "Dev_Mech": 1, "Documentation": 1} },
  "T": { "name": "System verification", "duration": 3, "predecessors": ["R"], "resources": {"Dev_Mech": 1, "Assembly_Comp": 1, "Assembly_Mech": 1} },
  "U": { "name": "Acceptance test", "duration": 2, "predecessors": ["S", "T"], "resources": {"Assembly_Comp": 1, "Assembly_Mech": 1} }
}
```

---

## 2. Ràng Buộc Tài Nguyên & Đơn Giá (Resource Constraints & Cost Matrix)

Để giải bài toán san phẳng nguồn lực (Resource Smoothing) và xếp lịch có giới hạn (RCPSP), bạn cần lưu trữ cấu trúc giới hạn nhân sự của công ty và đơn giá thầu phụ (Contractor).

### Bảng cấu hình nhân sự:

| Nhóm kỹ năng (Expertise) | Giới hạn nội bộ (Table 2/3) | Lương nội bộ ($/ngày) | Lương thuê ngoài ($/ngày) |
|-------------------------|:--------------------------:|:---------------------:|:-------------------------:|
| **Design (Computing)** | 1 | 200 | 350 |
| **Design (Mechanical)** | 1 | 200 | 350 |
| **Dev (Computing)** | 2 | 150 | 250 |
| **Dev (Mechanical)** | 1 | 150 | 250 |
| **Assembly (Computing)**| 1 | 100 | 200 |
| **Assembly (Mechanical)**| 1 | 100 | 200 |
| **Purchase** | 1 | 80 | 150 |
| **Documentation** | 2 | 80 | 150 |

---

## 3. Thuật Toán & Quy Tắc Tính Chi Phí Thuê Ngoài (Q6a - Subcontracting)

Khi công ty bị thiếu nhân sự tại các thời điểm trùng lịch, bạn bắt buộc phải thuê ngoài (Contractor).

### Công thức tính chi phí thuê ngoài cho một hoạt động:
*   Mỗi khi thuê thêm 1 nhân sự thầu phụ cho hoạt động $i$, thời gian thuê thực tế phải cộng thêm **3 ngày đào tạo (induction)**.
*   Lưu ý: 3 ngày đào tạo này chỉ tính tiền cho thầu phụ, nhân viên nội bộ cùng làm việc đó vẫn làm từ ngày bắt đầu dự kiến (không cần đào tạo).
*   **Ví dụ (Đề bài trang 6):** Hoạt động S cần 1 nhân viên Dev (Mechanical). Nếu thuê thầu phụ:
    *   Thời gian hoạt động S: 2 ngày.
    *   Số ngày phải trả tiền thầu phụ: $2 \text{ ngày làm} + 3 \text{ ngày induction} = 5 \text{ ngày}$.
    *   Chi phí: $5 \text{ ngày} \times \$250/\text{ngày} = \$1,250$.

---

## 4. Mô Hình Tối Ưu Hóa Chi Phí Làm Thêm Giờ (Q6b - Crashing)

Mục tiêu là tìm cách cho phép nhân viên làm việc vào cuối tuần (Thứ 7 & Chủ Nhật) để rút ngắn tổng thời gian dự án sao cho **Tổng Chi Phí là nhỏ nhất**.

### Quy tắc làm thêm giờ:
1.  **Lương ngày thứ 7 (Saturday Rate):** Nhân viên nội bộ và thầu phụ đều nhận lương gấp **1.5 lần** lương ngày thường.
2.  **Lương ngày chủ nhật (Sunday Rate):** Nhận lương gấp **3.0 lần** lương ngày thường.
3.  *Quy tắc thứ tự:* Bắt buộc phải dùng hết tất cả các ngày Thứ 7 rảnh trước khi chuyển sang làm ngày Chủ Nhật.
4.  *Quy tắc ưu tiên:* Luôn ưu tiên rút ngắn (crash) hoạt động găng có chi phí tăng thêm **thấp nhất**.
5.  *Quy tắc trùng:* Nếu hai hoạt động có chi phí crash bằng nhau, chọn hoạt động bắt đầu **sớm hơn**.

### Hàm tối ưu hóa (Objective Function):
Tìm cấu hình số ngày làm thêm $x_{sat}, x_{sun}$ cho mỗi hoạt động găng để:
$$\text{Minimize } \text{Total Cost} = \text{Direct Cost}(x) + (500 \times \text{Weeks}) + \text{Penalty}(\text{Weeks}) - \text{Bonus}(\text{Weeks})$$
Trong đó:
*   **Weeks:** Tổng số tuần thực tế hoàn thành đồ thị dự án (1 tuần = 5 ngày làm việc thường + tối đa 2 ngày cuối tuần làm thêm).
*   **Penalty:** Lấy số tuần vượt quá 12 nhân với **$2,000/tuần**.
*   **Bonus:** Lấy số tuần hoàn thành trước 12 nhân với **$3,000/tuần**.

---

## 5. Dữ Liệu Earned Value Analysis tại Tuần 5 (Q7 - EVM)

Tại cuối tuần thứ 5 (ngày làm việc thứ 25), dữ liệu báo cáo thực tế được mô tả trong bảng dưới. Bạn cần nạp dữ liệu này vào CSDL để module EVM tính toán.

| Hoạt động (Task) | Dự kiến % hoàn thành (PV) | Thực tế % hoàn thành (EV) | Chi phí thực tế đã tiêu (AC) |
|:---:|:---:|:---:|:---:|
| **A** | 100% | 100% | $2,400 |
| **B** | 100% | 100% | $6,500 |
| **C** | 100% | 100% | $4,300 |
| **D** | 100% | 100% | $3,500 |
| **E** | 100% | 100% | $6,100 |
| **F** | 100% | 50% | $8,500 |
| **G** | 100% | 100% | $2,100 |
| **H** | 100% | 10% | $2,000 |
| **I** | 100% | 20% | $5,300 |
| **K** | 100% | 80% | $3,200 |

*Các công việc còn lại (L $\rightarrow$ U) chưa bắt đầu nên % hoàn thành = 0% và chi phí AC = 0.*
