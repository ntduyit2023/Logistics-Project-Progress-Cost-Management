# Kiến trúc Dữ liệu Tổng thể: Cấp độ Task, Ràng buộc và Cơ hội (Constraint Override)
*(Dựa trên phân tích toàn diện dataset DSLIB - Project C2011-01)*

Hệ thống AI Insights được xây dựng dựa trên ma trận dữ liệu phân rã thành 3 tầng: Tầng Đặc trưng cục bộ (Task-level), Tầng Ràng buộc vĩ mô (Project-level Constraints), và Tầng Cơ hội (Constraint Relaxation).

---

## TẦNG 1: TASK-LEVEL FEATURES (Đặc trưng Cấp độ Công việc)
Đây là các tham số lõi của từng công việc đơn lẻ. Khi AI thực hiện tối ưu (Trade-off), các tham số này sẽ bị biến thiên.

| Feature Name | Data Type | Tác động khi AI can thiệp (Crashing / Leveling) |
| :--- | :--- | :--- |
| **Duration** *(in calendar days)* | Numeric | Không đổi về mặt "giờ công" (Working hours), nhưng biến thiên về số "ngày lịch" (Calendar days) nếu AI thay đổi Agenda. |
| **Baseline Start / End** | Datetime | Toạ độ thời gian thực. Bị đẩy lùi về phía trước (Finish early) khi AI áp dụng Crashing hoặc Fast Tracking. |
| **Resource Cost** | Numeric | Chi phí nhân công/máy móc. Đồng biến nghịch với Duration. Sẽ **tăng vọt** nếu AI đề xuất làm thêm giờ (Overtime/Weekend). |
| **Fixed Cost** | Numeric | Bất biến. AI không được phép đụng vào (không bị ảnh hưởng bởi tiến độ hay lịch làm việc). |
| **Total Cost** | Numeric | Tổng của Resource + Fixed Cost. Điểm neo đánh giá độ đắt đỏ của kịch bản tối ưu. |
| **Predecessors / Successors** | String | Cấu trúc DAG cục bộ. Dùng để tính toán khoảng an toàn `Total_Float` và xác định `Critical_Path`. |
| **Optimistic / Pessimistic (%)**| Numeric | Biên độ ép tiến độ. Dự án này chặn mức ép tối đa ở **80%** (rút ngắn 20% thời gian). |

---

## TẦNG 2: PROJECT-LEVEL CONSTRAINTS (Ràng buộc Cấp độ Dự án)
Đây là các "luật chơi cứng" chi phối toàn bộ các Task ở Tầng 1. Dưới góc độ lập trình, các ràng buộc này được định nghĩa bởi các Features cụ thể sau:

| Loại Ràng buộc | Nguồn dữ liệu | Các Features cấu thành Ràng buộc | Mô tả Ràng buộc (Hard Limits) |
| :--- | :--- | :--- | :--- |
| **Logic Constraint** *(Ràng buộc Cấu trúc mạng lưới)* | `Baseline Schedule` | <ul><li>`Dependency_Type` (VD: FS, SS)</li><li>`Dependency_Lag` (VD: +2 ngày)</li></ul> | Các mũi tên phụ thuộc (VD: Đổ móng xong mới xây tường). Trừ khi loại liên kết là mềm, AI không được phép bẻ gãy. |
| **Resource Constraint** *(Ràng buộc Giới hạn Tài nguyên)* | `Resources Sheet` | <ul><li>`Max_Availability_Per_Type` (Sức chứa tối đa)</li><li>`Resource_Type` (Renewable/Consumable)</li><li>`Daily_Resource_Usage` (Tổng cầu)</li></ul> | Công trường chỉ có tối đa `20 Handlanger`. AI phải đảm bảo phương trình: `Daily_Resource_Usage <= Max_Availability_Per_Type` trên mọi ngày. |
| **Time/Agenda Constraint** *(Ràng buộc Lịch trình thi công)* | `Agenda Sheet` | <ul><li>`Working_Days_Array` (Mảng ngày làm việc)</li><li>`Working_Hours_Per_Day` (Số giờ/ngày)</li><li>`Holidays_List` (Danh sách ngày lễ)</li></ul> | Lịch mặc định: 8:00-17:00, **Nghỉ Thứ 7 & Chủ Nhật**. Chỉ tính tiến độ trên `Working_Days`. Khi AI đề xuất Vượt rào, nó sẽ sửa `Working_Days_Array`. |

---

## TẦNG 3: CƠ HỘI CỞI MỞ & WHAT-IF (Constraint Relaxation / Vượt Rào)
Thay vì chỉ tối ưu trong Tầng 1 & 2 (thuật toán cổ điển), AI được cấp quyền **"Mở khóa/Nới lỏng ràng buộc"** ở Tầng 3 khi phát hiện đường cùng (hết Float, hết Availability).

### Ví dụ: Kịch bản "Mở khóa ngày nghỉ" (Working on Weekends/Holidays)
Đây là chiến lược Trade-off mang tính đột phá của hệ thống:
1. **Lợi ích (Available Time +40%):** Bằng cách Override ràng buộc `Agenda` (biến T7-CN thành Working Days), AI có thêm quỹ thời gian mà không làm tăng Mật độ tài nguyên (không bị đụng trần `Availability` của Tầng 2). `Baseline End` của task sẽ kéo lùi về sớm hơn.
2. **Sự đánh đổi (Cost Penalty):** Tính năng này sẽ trực tiếp nhân hệ số làm ngoài giờ (Overtime Premium Rate) vào thuộc tính `Resource Cost` ở Tầng 1. `Fixed Cost` giữ nguyên.
3. **AI Insight Output:** Hệ thống sẽ sinh ra một thẻ đề xuất: *"Mở khóa lịch cuối tuần cho Cụm công việc WBS 1. Thời lượng lịch (Calendar Duration) rút ngắn 4 ngày. Tổng Resource Cost tăng thêm X USD. Vẫn đảm bảo mức trần 20 Thợ/Ngày."*
