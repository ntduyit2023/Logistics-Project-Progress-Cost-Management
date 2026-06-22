# Phân tích Miền giá trị (Value Domain Analysis)
*(Dữ liệu trích xuất từ Project: `C2011-01 Nursing Home Noordhinder.xlsx`)*

Khi đưa dữ liệu dự án vào mô hình AI, việc hiểu rõ phân phối (Distribution) và biên độ (Min/Max) của các giá trị là bắt buộc để thực hiện **Data Normalization** và cấu hình **Hyperparameters**.

Dưới đây là bảng phân tích miền giá trị thống kê của 186 công việc (Tasks) trong dự án C2011-01.

---

## 1. Miền giá trị Thời gian & Rủi ro (Time & Risk Domain)

| Feature | Min | Max | Mean (Trung bình) | Độ lệch chuẩn (Std) | Phân tích Insight |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Duration** *(ngày)* | 0.04 (1 giờ) | 1,071.38 | 33.42 | 100.5 | Phân phối "đuôi dài" (Long-tail). Hầu hết task làm nhanh trong vài ngày, nhưng có task cực đại kéo dài tới 3 năm (1071 ngày). |
| **Optimistic** *(%)* | 80% | 99% | 83.37% | 7.2% | **Biên độ ép tối đa:** Giới hạn cứng của dự án này là chỉ có thể làm nhanh hơn 20% so với kế hoạch (80%). |
| **Pessimistic** *(%)* | 101% | 120% | 116.63% | 7.2% | **Biên độ trễ tối đa:** Giới hạn rủi ro xấu nhất là dự án bị kéo dài thêm 20% thời lượng. |

---

## 2. Miền giá trị Chi phí (Cost Domain)

| Feature | Min | Max | Mean (Trung bình) | Độ lệch chuẩn (Std) | Phân tích Insight |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Resource Cost** | $0 | $410,000 | $8,037 | $35,514 | Mức chênh lệch khủng khiếp giữa Mean và Max. Có những "siêu task" ngốn nửa triệu đô tiền nhân công. |
| **Fixed Cost** | $0 | $3,450,100 | $52,896 | $272,926 | Chi phí cố định lớn gấp 6-7 lần chi phí nhân công. |
| **Total Cost** | $0 | $4,679,795 | $71,847 | $364,520 | AI bắt buộc phải dùng Scale Logarit (Log-transform) hoặc Z-score cho cột Cost này, nếu không mô hình sẽ bị "nghiêng" (bias) hoàn toàn về các siêu task triệu đô. |

---

## 3. Miền giá trị Tài nguyên (Resource Constraint Domain)
Trích xuất từ danh sách các đội thầu/vật tư của công trường:

| Loại Tài nguyên | Nhóm (Type) | Availability (Trần cung ứng) | Cost/Unit (Đơn giá) |
| :--- | :--- | :--- | :--- |
| **Handlanger** *(Thợ phụ)* | Renewable | Tối đa **20** người/ngày | $30 / người |
| **Bekister** *(Thợ cốp pha)*| Renewable | Tối đa **10** người/ngày | $30 / người |
| **Ijzervlechter** *(Thợ sắt)* | Renewable | Tối đa **10** người/ngày | $30 / người |
| **Grondwerker** *(Thợ đất)* | Renewable | Tối đa **3** người/ngày | $30 / người |
| **Torenkraan** *(Cần cẩu)* | Renewable | Tối đa **2** chiếc/ngày | $4,000 / chiếc |

## 💡 Đề xuất Kỹ thuật (Actionable Output) từ Phân tích Cục bộ (C2011-01):
1. **Thuật toán Normalization:** Vì `Total Cost` lệch chuẩn quá lớn ($364k), trước khi nhồi vào Deep Learning (GNN), ta phải dùng hàm `np.log1p(Cost)`.
2. **Khởi tạo Boundary cho Crashing AI:** Hàm tối ưu của AI sẽ được set chặn (Boundary Bounds): `0.8 * Duration <= New_Duration <= 1.0 * Duration`.
3. **Mục tiêu Resource Leveling:** Biểu đồ nhân sự (Histogram) hàng ngày không được phép có cột nào vượt qua con số `20` (với thợ phụ) hoặc `2` (với Cần cẩu).

---

# Bức tranh Vĩ mô (Global Dataset Value Range)
*(Thống kê trên toàn bộ 235 dự án trong DSLIB)*

Để hệ thống AI không chỉ chạy tốt trên 1 dự án mà có khả năng **Tổng quát hóa (Generalization)** trên bất kỳ dự án nào, chúng ta cần nhìn vào biên độ của toàn bộ dataset:

| Global Feature | Min | Max | Mean | Ý nghĩa & Tác động đến AI Architecture |
| :--- | :--- | :--- | :--- | :--- |
| **Number of Activities** *(Số lượng Task)* | Vài task | 1,796 tasks | 102 tasks | AI Graph Neural Network (GNN) phải được thiết kế để xử lý **Large-Scale Graphs**. Các thuật toán duyệt đồ thị (như CPM) phải tối ưu O(V+E) để không bị treo máy khi gặp đồ thị 1,800 đỉnh. |
| **Project Duration** *(PD - Thời lượng dự án)* | 2 ngày | 2,804 ngày | 260 ngày | Có những dự án kéo dài gần **8 năm**. Việc thiết kế trục X cho biểu đồ UI (Gantt chart) phải hỗ trợ tính năng Zoom/Pan cực mượt. |
| **Budget at Completion** *(BAC - Tổng ngân sách)* | $1,210 | **$4.99 Tỷ Đô** | $61 Triệu | Phạm vi tài chính cực kỳ khủng khiếp. Biến số `Cost` tuyệt đối phải được chuẩn hóa về dạng tỷ lệ phần trăm (Percentage Variance) hoặc Log-scale để AI không bị tràn số (Gradient Explosion) khi huấn luyện. |
| **Serial/Parallel Indicator** *(SP)* | 0.01 | 1.00 | 0.40 | Chỉ số đo độ "song song" của dự án (Gần 1 là nối tiếp, gần 0 là song song). Mean = 0.40 cho thấy đa số dự án có cấu trúc mạng nhện chằng chịt, cơ hội để **Fast Tracking** (thi công song song) là rất lớn! |
| **Topological Float** *(TF)* | 0.00 | 0.99 | 0.37 | Đo lường độ "rỗng" của lịch trình. TF trung bình 0.37 nghĩa là dự án có khoảng 37% không gian "thở". Đây là "mỏ vàng" để AI áp dụng thuật toán **Resource Leveling** (Dịch chuyển task). |
