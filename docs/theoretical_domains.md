# Miền Giá Trị Lý Thuyết (Theoretical Value Domains)

Bên cạnh dữ liệu khảo sát thực tế (Empirical Data), dưới góc độ Toán học và Quản lý Dự án (Operations Research), mỗi Feature đều có một **Miền Xác Định Lý Thuyết**. Việc định nghĩa chính xác miền này giúp AI không bao giờ đưa ra các đề xuất "phi thực tế" (ảo tưởng), đồng thời làm cơ sở cho hàm Constraint Validation.

---

## 1. Nhóm Đặc trưng Thời gian & Cấu trúc (Time & Topology)

| Feature Name | Theoretical Domain | Giải thích Toán học & Thực tiễn |
| :--- | :--- | :--- |
| **Duration** | `(0, +∞)` | Thời lượng không thể âm và không thể bằng 0 (nếu = 0 thì nó là Milestone, không phải Task). |
| **Total Float** | `(-∞, +∞)` | Khoảng thời gian dự trữ. Thường là `[0, +∞)`. Tuy nhiên, nếu dự án bị áp một Hard Deadline (Hạn chót cứng) và tiến độ hiện tại đã trễ, Total Float sẽ mang **giá trị âm** (âm bao nhiêu ngày là trễ bấy nhiêu ngày). |
| **Lag (Độ trễ liên kết)**| `(-∞, +∞)` | Lag dương (VD: FS+2) nghĩa là đợi 2 ngày. Lag âm (VD: FS-2) còn gọi là Lead Time, nghĩa là bắt đầu sớm 2 ngày trước khi task trước đó xong. |
| **Topological Float (TF)** | `[0, 1]` | Chỉ số đo độ "rỗng" của mạng lưới. 0 = Mạng lưới đặc (Tất cả là đường găng), 1 = Mạng lưới trống rỗng. |

## 2. Nhóm Đặc trưng Chi phí & Tài nguyên (Cost & Resource)

| Feature Name | Theoretical Domain | Giải thích Toán học & Thực tiễn |
| :--- | :--- | :--- |
| **Cost (Resource/Fixed/Total)**| `[0, +∞)` | Chi phí không thể âm. Thường có giá trị phân phối Log-Normal. |
| **Resource Demand** | `[0, Max_Availability]` | Nhu cầu tài nguyên của 1 task không thể vượt quá giới hạn vật lý của công trường (Ví dụ: Chỉ có 20 thợ phụ thì Demand tối đa là 20). |
| **SPI (Schedule Performance)**| `(0, +∞)` | Chỉ số hiệu suất thời gian (EV/PV). `SPI < 1`: Trễ tiến độ. `SPI = 1`: Đúng tiến độ. `SPI > 1`: Vượt tiến độ. |
| **CPI (Cost Performance)** | `(0, +∞)` | Chỉ số hiệu suất chi phí (EV/AC). `CPI < 1`: Lỗ. `CPI > 1`: Lãi. |

## 3. Nhóm Đặc trưng Rủi ro (Risk & Sensitivity)

| Feature Name | Theoretical Domain | Giải thích Toán học & Thực tiễn |
| :--- | :--- | :--- |
| **Optimistic (%)** | `(0, 100%]` | Thời gian làm nhanh nhất. Không thể ép xuống 0 ngày (0%), và không thể lớn hơn 100% (vì nếu >100% thì nó thành Pessimistic mất rồi). |
| **Pessimistic (%)** | `[100%, +∞)` | Thời gian trễ nhất. Rủi ro trễ tiến độ là vô tận, không có trần giới hạn. |
| **Cruciality Index (CRI-r)** | `[-1, 1]` | Đây là hệ số Tương quan Pearson (Pearson Correlation). `1`: Tương quan thuận hoàn toàn (Task trễ -> Dự án chắc chắn trễ). `0`: Không liên quan. `-1`: Tương quan nghịch. |

## 4. Phân tích Miền giá trị theo 3 Trục Ràng buộc (Constraint Domains)

Các ràng buộc vĩ mô của dự án được chia làm 3 trục độc lập. Việc nới lỏng (Relaxation) ở bất kỳ trục nào cũng đòi hỏi sự am hiểu sâu sắc về miền xác định của các biến số tương ứng.

### 4.1. Trục Ràng buộc Lịch trình (Time / Agenda Constraints)
Trục này quy định ranh giới thời gian hợp lệ cho các công việc. AI sẽ tác động vào trục này khi muốn áp dụng chiến lược **"Làm thêm giờ / Làm ngày nghỉ"**.

| Feature Name | Theoretical Domain | Giải thích Toán học & Thực tiễn |
| :--- | :--- | :--- |
| **Working_Days_Array** | `{0, 1}^7` | Mảng nhị phân 7 phần tử đại diện cho 1 tuần. `1` = Làm việc, `0` = Nghỉ. <br>Ví dụ chuẩn: `[1,1,1,1,1,0,0]`. Biên độ cởi mở tối đa (Max Override): `[1,1,1,1,1,1,1]`. |
| **Working_Hours/Day** | `[1, 24]` | Số giờ làm việc 1 ngày không thể vượt quá 24h. Thường bị chặn ở giới hạn sức người `[8, 16]`. |

### 4.2. Trục Ràng buộc Tài nguyên (Resource Constraints)
Trục này kiểm soát năng lực thi công và dòng tiền. AI tác động vào trục này khi muốn áp dụng **Resource Leveling** (San bằng) hoặc **Crashing** (Đổ thêm tiền mua tài nguyên).

| Feature Name | Theoretical Domain | Giải thích Toán học & Thực tiễn |
| :--- | :--- | :--- |
| **Max_Availability** | `ℕ (0, +∞)` | Số lượng tài nguyên tối đa (Sức chứa) phải là số tự nhiên. Công trường không thể có "nửa cái máy cẩu" hoặc "âm 2 người thợ". |
| **Resource Type** | `{Renewable, Consumable}`| Biến phân loại. `Renewable` (nhân công, máy) hồi phục mỗi ngày. `Consumable` (xi măng, tiền) tiêu hao vĩnh viễn theo tích phân thời gian. |
| **Cost/Use** *(Phí khởi động)* | `[0, +∞)` | Phí cố định mỗi lần điều động tài nguyên, không phụ thuộc thời gian làm việc. Ngăn chặn AI "băm nhỏ" task (Task Splitting) vì sẽ bị phạt phí này nhiều lần. |
| **Cost/Unit** *(Đơn giá)* | `[0, +∞)` | Hệ số góc (Slope) tính `Resource Cost`. Khi làm thêm giờ/cuối tuần, AI phải kích hoạt hàm `Cost/Unit * Overtime_Premium`. |

### 4.3. Trục Ràng buộc Logic (Topology / Network Constraints)
Trục này quy định trình tự thi công cốt lõi. AI tác động vào trục này khi muốn áp dụng chiến lược **Fast Tracking** (Đẩy nhanh bằng cách làm song song).

| Feature Name | Theoretical Domain | Giải thích Toán học & Thực tiễn |
| :--- | :--- | :--- |
| **Dependency Type** | `{FS, SS, FF, SF}` | Tập hợp biến phân loại. 90% liên kết thực tế là FS (Xong mới Bắt đầu). Chuyển `FS` thành `SS` (Bắt đầu cùng lúc) chính là bản chất Toán học của Fast Tracking. |

## 💡 Ứng dụng vào AI (Boundary Constraints & Validation)
Khi AI sinh ra một kịch bản tối ưu (Optimization Scenario), nó phải đi qua một lớp kiểm duyệt (Validation Layer) được lập trình cứng theo các quy tắc của 3 trục này:
- **Vi phạm Trục Lịch trình:** AI đề xuất `Duration` âm ➔ Bị từ chối.
- **Vi phạm Trục Logic:** AI đảo ngược liên kết gây ra Vòng lặp vô hạn (Cyclic Graph) ➔ Lỗi đồ thị ➔ Bị từ chối.
- **Vi phạm Trục Tài nguyên:** AI chồng 3 task lại với nhau khiến tổng `Resource Demand` tại ngày T = 25 (Vượt Max = 20) ➔ Bị từ chối, ép buộc phải gọi hàm dịch chuyển (Leveling).
