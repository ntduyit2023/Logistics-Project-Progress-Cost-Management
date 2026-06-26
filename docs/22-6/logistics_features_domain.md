# Hệ sinh thái Features & Constraints cho Logistics Domain
*(Trích xuất và tham chiếu từ hệ thống GLPO Node Features - `feature_relationship_graph.html`)*

Tài liệu này đóng vai trò là "Kim chỉ nam" (Baseline) cho Domain Logistics. Thay vì dàn trải trên toàn bộ 91 Features, chúng ta đã chắt lọc ra các đặc trưng có tính quyết định nhất đối với một bài toán Logistics / Supply Chain. Tài liệu này sẽ được dùng làm bộ lọc (Filter) để săn lùng Dataset thực tế.

---

## 1. Dữ liệu Cấp độ Công việc (Logistics Task Features)
Đây là các đặc trưng tĩnh/động của 1 Node (Task) trong chuỗi cung ứng. Một Task Logistics không chỉ tiêu tốn thời gian mà còn liên quan mật thiết đến sự dịch chuyển vật lý và chi phí con người.

| ID (HTML) | Nhóm Feature | Tên Feature (Từ Graph) | Giải thích trong ngữ cảnh Logistics |
| :--- | :--- | :--- | :--- |
| **`33`** | Thời gian | **Thời gian thực hiện kế hoạch (Planned Duration)** | Thời gian vận chuyển (Transit time) trên đường hoặc thời gian bốc xếp tại kho. |
| **`43`** | Thời gian | **Thời gian dẫn đầu (Lead Time)** | Thời gian từ lúc nhận order/booking đến khi nhận hàng. Chỉ số sinh tử trong SCM. |
| **`41`** | Thời gian | **Thời gian thiết lập (Setup/Transition Time)** | Thời gian xe tải chờ bốc dỡ tại dock, chờ làm thủ tục thông quan hải quan. |
| **`5`** | CP Trực tiếp | **Chi phí vận chuyển trực tiếp (Direct Transportation)** | Cước phí xe tải/tàu biển (Linehaul cost) gắn liền với quãng đường và tải trọng. |
| **`30`** | Logistics & SCM | **Chi phí vận chuyển quốc tế (International Freight)** | Cước container, thuế nhập khẩu, phí lưu bãi cảng biển (THC). |
| **`31`** | Logistics & SCM | **Chi phí đóng gói & xử lý (Packaging & Handling)** | Chi phí palletizing, dán nhãn, bốc dỡ hàng hóa tại trung tâm phân phối. |
| **`26`** | Logistics & SCM | **Chi phí lưu kho & bảo quản (Inventory Holding Cost)** | Phí lưu kho bãi, lưu container (Demurrage & Detention) phát sinh nếu hàng hóa bị ứ đọng. |
| **`28`** | Logistics & SCM | **Chi phí thiếu hụt (Shortage/Stockout)** | Chi phí đền bù hợp đồng hoặc tiền thuê xe khẩn cấp (Spot market) khi thiếu hụt năng lực vận tải. |
| **`0`** | CP Trực tiếp | **Chi phí nhân công nội bộ (Internal Labor Cost)** | Lương cơ bản của tài xế xe tải, công nhân bốc vác, thợ lái xe nâng (Forklift) tại kho. |
| **`1`** | CP Trực tiếp | **Chi phí thuê ngoài (Subcontracting Cost)** | Chi phí thuê dịch vụ 3PL (Third-party logistics) hoặc thuê thêm xe tải ngoài khi quá tải. |
| **`2`** | CP Trực tiếp | **Chi phí làm thêm giờ (Overtime/Crashing)** | Phụ phí trả cho tài xế chạy ca đêm, kho bãi bốc dỡ ngoài giờ để kịp Time Windows. |
| **`9`** | CP Gián tiếp | **Chi phí quản lý dự án (PM Overhead)** | Lương của đội ngũ Điều phối viên (Dispatcher), bộ phận CSKH theo dõi đơn hàng. |
| **`89`** | ESG | **Thuế Carbon / Tín chỉ Carbon (Carbon Tax)** | Áp lực hiện đại: Chọn tuyến đường hoặc phương thức vận tải tối ưu lượng phát thải CO2. |

---

## 2. Ràng buộc Vĩ mô (Logistics Constraints)
Các ràng buộc này quyết định tính hợp lệ của một kịch bản vận hành (Routing & Scheduling). Nếu AI vi phạm, kịch bản sẽ bị loại bỏ hoặc chịu Penalty.

### 2.1. Logic Constraint (Ràng buộc Mạng lưới & Tuyến đường)
*   **Sequential Routing (Bậc vào 55 / Bậc ra 56):** Hàng hóa bắt buộc phải đi qua các Hub trung chuyển theo đúng thứ tự mạc định (VD: Pick -> Pack -> Export Customs -> Ship -> Import Customs -> Deliver). 
*   **Mức độ phụ thuộc bên ngoài (External Dependency - ID 67):** Tàu biển, máy bay hay tàu hỏa đều có lịch trình cố định (Fixed Schedule). Nếu xe tải đến cảng trễ, toàn bộ chuỗi hậu duệ (Downstream) đứt gãy.

### 2.2. Resource Constraint (Ràng buộc Năng lực Vật lý)
Khác với xây dựng (giới hạn số người), Logistics bị trói buộc bởi Không gian vật lý.
*   **Nhu cầu tài nguyên theo loại (Demand Vector - ID 46):** Yêu cầu chính xác loại thiết bị chuyên dụng (Xe đông lạnh, Xe bồn hóa chất, Container 40ft, Cẩu siêu trường).
*   **Sức chứa & Tải trọng (Max Capacity):** Ràng buộc cực ngặt nghèo về **Thể tích (Volume / CBM)** và **Trọng tải (Weight / KG)** của thùng xe. Tổng hàng hóa trên xe không được phép vượt mốc này.
*   **Tỷ lệ sử dụng thiết bị (Equipment Utilization - ID 53):** Tối ưu hóa hệ số lấp đầy xe (Fill Rate) nhằm hạn chế tối đa việc chạy xe rỗng (Empty backhaul).

### 2.3. Time Constraint (Ràng buộc Khung giờ tĩnh)
*   **Thời gian chờ đầu vào (Wait/Queue Time - ID 40):** Thời gian xe tải bị chôn chân tại kho chờ đến lượt bốc dỡ, gây lãng phí chi phí cơ hội.
*   **Time Windows (Khung giờ giao nhận):** Đặc thù quan trọng bậc nhất của Logistics. Các điểm giao/nhận chỉ mở cửa trong một khung giờ tĩnh hẹp (VD: Siêu thị chỉ nhận hàng từ 2h-4h sáng). AI phải ép `Early Start` (36) và `Late Finish` (39) rơi đúng vào khung giờ này. Nếu vi phạm sẽ sinh ra **Tiền phạt trễ hạn (Penalty - ID 19)**.
*   **Rủi ro thời tiết (Weather Risk - ID 70):** Biển động, sương mù làm đóng cửa cảng biển/sân bay, ép toàn bộ ma trận thời gian phải tịnh tiến về tương lai.
