# Phân tích & Mapping Chi phí (Cost Features) trên DSLIB

Tài liệu này đánh giá khả năng ánh xạ các Cost Features trong `logistics_features_domain.md` với dữ liệu thực tế từ 19 dự án Logistics trong DSLIB_Logistics_Subset.

## 1. Khảo sát Dữ liệu Chi phí (Thực tế từ File Excel)

Bảng dưới đây thống kê các cột chứa số liệu tài chính > 0 trong sheet `Resources` của các dự án.

| Tên Dự án | Cost/Use (Cố định) | Cost/Unit (Theo giờ/đơn vị) | Total Cost (Tổng CP) |
| :--- | :---: | :---: | :---: |
| C2011-07 Patient Transport System.xlsx | ❌ | ✅ | ✅ |
| C2012-04 Asti-Cuneo Highway.xlsx | ❌ | ✅ | ✅ |
| C2012-07 Solar Park.xlsx | ❌ | ❌ | ❌ |
| C2012-08 Sea Electricity.xlsx | ❌ | ✅ | ✅ |
| C2016-08 SCM System.xlsx | ❌ | ❌ | ❌ |
| C2016-35 Sweetpack.xlsx | ❌ | ❌ | ❌ |
| C2017-03 Hydrogen Island.xlsx | ❌ | ❌ | ❌ |
| C2018-04 Christmas market (1).xlsx | ❌ | ❌ | ❌ |
| C2018-05 Music festival.xlsx | ❌ | ❌ | ❌ |
| C2018-09 CarSharing platform.xlsx | ❌ | ✅ | ✅ |
| C2018-11 Warehouse renovation.xlsx | ❌ | ❌ | ❌ |
| C2019-16 Lock Ganzepoot Excel.xlsx | ❌ | ✅ | ✅ |
| C2019-17 Wine production.xlsx | ❌ | ❌ | ❌ |
| C2022-01 Student kick-off Kramersplein.xlsx | ❌ | ❌ | ❌ |
| C2022-02 Student kick-off Sint-Pietersplein.xlsx | ❌ | ❌ | ❌ |
| C2023-06 Steel industry.xlsx | ❌ | ❌ | ❌ |
| C2023-11 Rail-net communication point 1.xlsx | ❌ | ❌ | ❌ |
| C2023-12 Railroad construction.xlsx | ❌ | ❌ | ❌ |
| C2023-13 Rail-net communication point 2.xlsx | ❌ | ❌ | ❌ |

**Kết luận Khảo sát:** Có **5/19** dự án có chứa sẵn dữ liệu tài chính (Chi phí > 0).

## 2. Mapping Cost Features (Có vs Không Có)

### 🟢 CÓ SẴN (Có thể trích xuất trực tiếp hoặc tính toán nội suy từ DSLIB)

1. **Chi phí nhân công nội bộ (Internal Labor Cost - ID 0)**
   - **Trạng thái:** Dễ dàng tính toán.
   - **Nguồn từ DSLIB:** Các file có cột `Cost/Unit` = Lương nhân công theo ngày/giờ. Nhân `Cost/Unit` với cột `Duration` của Task để ra chi phí nhân sự.

2. **Chi phí vận chuyển trực tiếp (Direct Transportation - ID 5)**
   - **Trạng thái:** Dễ dàng tính toán.
   - **Nguồn từ DSLIB:** Các file có cột `Cost/Use` = Phí gọi xe/tàu (Fixed cost per trip). Hoặc trích xuất từ `Total Cost` đối với các Task có liên quan đến Transport.

### 🟡 CHỈ CÓ MỘT PHẦN (Cần dùng Feature Engineering + Regex để gán nhãn)

3. **Chi phí lưu kho & bảo quản (Inventory Holding Cost - ID 26)**
   - **Trạng thái:** Không có sẵn một cột độc lập mang tên 'Holding Cost'.
   - **Cách xử lý:** Viết thuật toán Python đọc Tên Task. Nếu Tên Task chứa từ khóa `warehouse`, `storage` $ightarrow$ Ánh xạ `Total Cost` của Task đó vào biến `Inventory Holding Cost`.

4. **Chi phí đóng gói & xử lý (Packaging & Handling - ID 31)**
   - **Trạng thái:** Không có sẵn một cột độc lập.
   - **Cách xử lý:** Giống trên. Nếu Tên Task chứa từ khóa `pack`, `pallet`, `load`, `unload` $ightarrow$ Ánh xạ `Total Cost` vào biến `Packaging & Handling`.

### 🔴 KHÔNG CÓ SẴN (Cần Simulate/Generate bằng Thuật toán phân phối xác suất)

5. **Chi phí làm thêm giờ (Overtime/Crashing - ID 2)**
   - **Nguyên nhân:** DSLIB không cung cấp tham số `Ovt. Rate` ở hầu hết các dự án. Tiến độ trong file là 'Kế hoạch hoàn hảo' không tính đến làm thêm ngoài giờ.
   - **Cách xử lý (Simulation):** Tạo cột mới. Gán giá trị rỗng bằng `Cost/Unit * 1.5`.

6. **Chi phí thiếu hụt (Shortage/Stockout - ID 28)** & **Tiền phạt trễ hạn (Penalty - ID 19)**
   - **Nguyên nhân:** Dữ liệu DSLIB là 'Dự án thành công' (Success path), không hề có kịch bản bị đền bù hợp đồng.
   - **Cách xử lý (Simulation):** Viết Script tự động sinh ra Deadline (Dựa trên ngày Finish muộn nhất). Tính toán: `Penalty = Max(0, Actual Finish - Deadline) * Cost_per_day`.

7. **Thuế Carbon (Carbon Tax - ID 89)**
   - **Nguyên nhân:** Khái niệm ESG chưa phổ biến vào thời điểm các dataset này được tạo ra (2012-2023).
   - **Cách xử lý (Simulation):** Gắn hệ số phát thải ngẫu nhiên (từ 0.1 đến 1.5 kgCO2/ngày) cho các thiết bị như Truck, Ship, Forklift.

## 3. Đề xuất Hướng đi cho Data Pipeline

Dựa trên thực tế này, Script Data Pipeline `.py` của chúng ta sẽ thực hiện 2 nhiệm vụ song song:
1. **Data Extraction:** Lấy `Cost/Unit`, `Cost/Use` để ghép vào `Labor Cost` và `Transport Cost`.
2. **Data Generation (Synthesizer):** Tự động sinh thêm các cột `Penalty`, `Shortage Cost`, `Overtime Rate` dựa trên các hàm Toán học, để đảm bảo Dataset cuối cùng **khớp hoàn hảo 100%** với hệ sinh thái Features của đề tài.
