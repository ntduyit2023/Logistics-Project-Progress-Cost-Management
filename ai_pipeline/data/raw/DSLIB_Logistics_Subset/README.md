# DSLIB Logistics Subset — Mô tả Dữ liệu (Dataset Description)

> **Nguồn gốc:** Trích xuất từ bộ dữ liệu [DSLIB (Dynamic Scheduling Library)](https://www.projectmanagement.ugent.be/research/data/dslib) — Đại học Ghent, Bỉ.
> 
> **Mục đích:** Phục vụ đề tài *"Xây dựng ứng dụng hỗ trợ quản lý tiến độ và chi phí dự án Logistics"*.
> 
> **Tổng số dự án:** 19
> 
> **Tiêu chí lọc:** Các dự án được chọn dựa trên phân tích nội dung cột `Name` (Tên Công việc) trong sheet `Baseline Schedule`. Chỉ giữ lại các dự án có Task liên quan trực tiếp đến hoạt động Logistics (Vận tải, Kho bãi, Chuỗi cung ứng, Giao nhận...).

---

## Cấu trúc chung của mỗi file Excel

Mỗi file chứa các sheet sau (tùy dự án):

| Sheet | Mô tả |
|-------|-------|
| **Baseline Schedule** | Kế hoạch cơ sở: ID, Name, Duration, Predecessors, Start/Finish |
| **Resources** | Danh sách tài nguyên (Nhân lực, Thiết bị) và phân bổ |
| **Risk Analysis** | Phân tích rủi ro dự án |
| **AC, EV, PV** | Dữ liệu Earned Value Management (Quản lý Giá trị Thu được) |
| **CPI, SPI(t)** | Chỉ số hiệu suất Chi phí và Tiến độ |
| **CV, SV(t)** | Phương sai Chi phí và Tiến độ |
| **Tracking Overview** | Tổng quan theo dõi tiến độ thực tế |
| **TP1, TP2, ...** | Tracking Periods — Dữ liệu cập nhật theo từng kỳ giám sát |

---

## Danh sách 19 Dự án Logistics

---

### 1. Patient Transport System ⭐
- **File:** `C2011-07 Patient Transport System.xlsx`
- **Mảng Logistics:** Healthcare Logistics (Vận chuyển Y tế)
- **Tổng Task:** 69 | **Task Logistics:** 7
- **Mô tả:** Dự án triển khai hệ thống vận chuyển bệnh nhân giữa các cơ sở y tế. Bao gồm nghiên cứu nhà cung cấp, đàm phán hợp đồng, lắp đặt hệ thống vận chuyển và đào tạo vận hành.
- **Task tiêu biểu:**
  - Request proposal suppliers transport system
  - Research suppliers transport systems
  - Negociation conditions final supplier transport system
  - Installation transport system
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI, 23 Tracking Periods

---

### 2. Asti-Cuneo Highway ⭐
- **File:** `C2012-04 Asti-Cuneo Highway.xlsx`
- **Mảng Logistics:** Logistics Hạ tầng Giao thông
- **Tổng Task:** 95 | **Task Logistics:** 7
- **Mô tả:** Dự án xây dựng đường cao tốc Asti-Cuneo (Ý). Bao gồm vận chuyển và bố trí container công trường, thi công nền đường, hệ thống thoát nước, cầu vượt và rào chắn âm thanh.
- **Task tiêu biểu:**
  - Containers placement
  - Road embankments
  - Alternative road system
  - Containers removal
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI

---

### 3. Solar Park
- **File:** `C2012-07 Solar Park.xlsx`
- **Mảng Logistics:** Vận tải & Cẩu hạng nặng
- **Tổng Task:** 217 | **Task Logistics:** 4
- **Mô tả:** Dự án xây dựng công viên năng lượng mặt trời quy mô lớn. Phần Logistics bao gồm kiểm tra ổn định vận chuyển thiết bị và tổ chức cẩu/vận chuyển tấm pin lên vị trí lắp đặt.
- **Task tiêu biểu:**
  - controle stabiliteit transport (Kiểm tra ổn định vận chuyển)
  - Logistiek: transport / hijswerken (Logistics: vận chuyển / cẩu)
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI

---

### 4. Sea Electricity ⭐
- **File:** `C2012-08 Sea Electricity.xlsx`
- **Mảng Logistics:** Vận tải Biển Hạng nặng (Heavy Maritime Logistics)
- **Tổng Task:** 467 | **Task Logistics:** 144
- **Mô tả:** Siêu dự án điện gió ngoài khơi. Đây là dự án có mật độ Logistics cao nhất trong toàn bộ DSLIB. Bao gồm vận chuyển cọc móng từ nhà máy (Hoboken) ra cảng (Vlissingen) bằng đường bộ, sau đó vận chuyển bằng tàu ra biển, lắp đặt bằng jack-up platform, rải cáp ngầm dưới đáy biển.
- **Task tiêu biểu:**
  - Delivery of pin-piles (24 chuyến)
  - Transport (Hoboken to Vlissingen) (24 chuyến)
  - Transport of the jacket foundations (24 chuyến)
  - Loading jack up transport and installation platform
  - Dredging shipping lane
  - Export cable laying on sea bed
  - Transportation of parts from factories to Ostend
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI

---

### 5. SCM System 
- **File:** `C2016-08 SCM System.xlsx`
- **Mảng Logistics:** Chuỗi Cung Ứng (Supply Chain Management)
- **Tổng Task:** 147 | **Task Logistics:** 10
- **Mô tả:** Dự án triển khai hệ thống quản lý chuỗi cung ứng (SCM) cho doanh nghiệp. Tích hợp dữ liệu tồn kho (Inventory), đơn hàng vận chuyển (Transport Orders), định tuyến (Routing) và tối ưu hóa phân phối hàng hóa đến các trung tâm phân phối khu vực (RDC).
- **Task tiêu biểu:**
  - Model integration of the inventory
  - Model integration of the feedback on Transport/Purchase orders
  - Model integration of intercompany Transport orders
  - Configure basic solvers (heuristics for capacity and inventory constraints)
  - Adapt Solver for pushing surplus inventory to RDC's
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI, 34 Tracking Periods

---

### 6. Sweetpack
- **File:** `C2016-35 Sweetpack.xlsx`
- **Mảng Logistics:** Sản xuất & Giao hàng (Manufacturing & Delivery)
- **Tổng Task:** 65 | **Task Logistics:** 8
- **Mô tả:** Dự án phát triển và giao hàng dây chuyền đóng gói tự động (Flowpacker) cho công ty kẹo Sweetpack. Bao gồm thiết kế, sản xuất, kiểm thử cấp liệu (Supply hoppers) và giao máy đến nhà máy khách hàng.
- **Task tiêu biểu:**
  - Testing supply hoppers candy
  - Production flowpacker
  - Delivery flowpacker at Sweetpack
  - Integration of hoppers and flowpacker in new production line
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI

---

### 7. Hydrogen Island
- **File:** `C2017-03 Hydrogen Island.xlsx`
- **Mảng Logistics:** Cảng biển & Vận tải Năng lượng
- **Tổng Task:** 105 | **Task Logistics:** 9
- **Mô tả:** Dự án xây dựng đảo năng lượng Hydro nhân tạo. Bao gồm xây dựng cảng biển (Port), lắp đặt cẩu (Crane), xây dựng đường vận chuyển (Roads), bể chứa (Storage tanks) và hệ thống cung cấp cáp/đường ống (Supply cables).
- **Task tiêu biểu:**
  - Port
  - Crane
  - Transport resources
  - Storage tanks
  - Roads and hardstands
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI

---

### 8. Christmas Market
- **File:** `C2018-04 Christmas market (1).xlsx`
- **Mảng Logistics:** Event Logistics (Logistics Sự kiện)
- **Tổng Task:** 39 | **Task Logistics:** 4
- **Mô tả:** Dự án tổ chức hội chợ Giáng sinh ngoài trời. Bao gồm đặt hàng và giao nhận vật tư (chalets, sân trượt băng, máy sưởi), điều phối nhà cung cấp đồ uống và lắp đặt cơ sở hạ tầng sự kiện.
- **Task tiêu biểu:**
  - Delivery Stad Gent
  - Delivery drinks
  - Order 35 chalets
  - Order ice skating rink
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI

---

### 9. Music Festival
- **File:** `C2018-05 Music festival.xlsx`
- **Mảng Logistics:** Event Logistics (Logistics Sự kiện)
- **Tổng Task:** 31 | **Task Logistics:** 3
- **Mô tả:** Dự án tổ chức lễ hội âm nhạc. Bao gồm đặt hàng vật tư (âm thanh, ánh sáng, quầy hàng), điều phối giao thông công cộng (public transport), giao cốc tái chế và lắp đặt sân khấu.
- **Task tiêu biểu:**
  - public transport
  - placing stands: food + drink + reloading points
  - deliver dishwasher cups
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI

---

### 10. CarSharing Platform ⭐
- **File:** `C2018-09 CarSharing platform.xlsx`
- **Mảng Logistics:** Last-mile Delivery & Triển khai Đội xe
- **Tổng Task:** 49 | **Task Logistics:** 9
- **Mô tả:** Dự án triển khai nền tảng chia sẻ xe ô tô. Bao gồm khảo sát và lắp đặt trạm sạc (Docking stations), giao xe đến các điểm đặt, lắp biển báo giao thông và thiết bị sạc.
- **Task tiêu biểu:**
  - Research for possible docking stations
  - Delivery and placing of the charging blocks
  - Installation of traffic signs (Trafiroad)
  - Delivery cars
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI

---

### 11. Warehouse Renovation
- **File:** `C2018-11 Warehouse renovation.xlsx`
- **Mảng Logistics:** Kho bãi (Warehousing)
- **Tổng Task:** 30 | **Task Logistics:** 8
- **Mô tả:** Dự án cải tạo nhà kho. Bao gồm đặt hàng và giao nhận container bốc dỡ, giao bê tông, giao hệ thống thông gió, giao và lắp đặt pallet sandwich lên tường kho.
- **Task tiêu biểu:**
  - Order + delivery containers for discharging wood
  - Order + delivery containers for discharging waste walls
  - Order + delivery sandwich pallets
  - Putting sandwich pallets against the walls
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, AC/EV/PV, CPI/SPI

---

### 12. Lock Ganzepoot ⭐
- **File:** `C2019-16 Lock Ganzepoot Excel.xlsx`
- **Mảng Logistics:** Logistics Xây dựng Cảng / Âu tàu
- **Tổng Task:** 33 | **Task Logistics:** 5
- **Mô tả:** Dự án xây dựng/sửa chữa âu tàu (Lock) tại Ypres, Bỉ. Bao gồm vận chuyển cổng âu tàu đến công trường, cung cấp khối bê tông và lắp đặt thiết bị.
- **Task tiêu biểu:**
  - Transport of gates to the site
  - Supply concrete blocks
  - Installation of power generators, lighting, toilets, fencing
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, Tracking Overview

---

### 13. Wine Production
- **File:** `C2019-17 Wine production.xlsx`
- **Mảng Logistics:** Supply Chain (Chuỗi cung ứng Sản phẩm)
- **Tổng Task:** 26 | **Task Logistics:** 2
- **Mô tả:** Dự án sản xuất rượu vang từ A-Z: Nghiên cứu men → Ép nho → Lên men → Lọc → Ủ → Đóng chai → Dán nhãn → Vận chuyển đến sự kiện. Đây là một chuỗi cung ứng sản phẩm hoàn chỉnh (End-to-end Supply Chain).
- **Task tiêu biểu:**
  - Bottle supply
  - Bottling
  - Transportation material to event
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, Tracking Overview

---

### 14. Student Kick-off Kramersplein 
- **File:** `C2022-01 Student kick-off Kramersplein.xlsx`
- **Mảng Logistics:** Logistics Sự kiện quy mô lớn (Container Operations)
- **Tổng Task:** 188 | **Task Logistics:** 68
- **Mô tả:** Dự án tổ chức sự kiện sinh viên quy mô lớn tại quảng trường Kramersplein. Đặc điểm nổi bật: Sử dụng hệ thống Container Modular làm quầy bar, kho hàng, phòng điều hành, phòng báo chí. Mỗi container phải được vận chuyển đến, đặt đúng vị trí, kết nối điện/nước và trang bị nội thất.
- **Task tiêu biểu:**
  - Placing bottom/top container (bar, warehouse, press, DJ booth...)
  - Equipping container with utilities
  - Positioning container fridge
  - Equipping with utilities (storage)
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, Tracking Overview

---

### 15. Student Kick-off Sint-Pietersplein 
- **File:** `C2022-02 Student kick-off Sint-Pietersplein.xlsx`
- **Mảng Logistics:** Logistics Sự kiện quy mô lớn (Container Operations)
- **Tổng Task:** 159 | **Task Logistics:** 62
- **Mô tả:** Dự án tương tự #14 nhưng tại quảng trường Sint-Pietersplein. Cùng mô hình Container Modular Logistics.
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, Tracking Overview

---

### 16. Steel Industry 
- **File:** `C2023-06 Steel industry.xlsx`
- **Mảng Logistics:** Logistics Công nghiệp Nặng (Industrial Logistics)
- **Tổng Task:** 802 | **Task Logistics:** 16
- **Mô tả:** Dự án bảo trì tổng thể nhà máy luyện thép (Intercampagne). Bao gồm vận hành hệ thống băng tải (Transportband), xe nâng hạng nặng (Heftruck H60), bốc dỡ pallet, quản lý container rác thải công nghiệp. Tên dự án ghi rõ: *"2958 ladingen"* (2958 chuyến tải).
- **Task tiêu biểu:**
  - Kap van S32 wegnemen en transportband achteruit rijden
  - Heftruck H60 koppelen aan tunnel
  - Verwijderen pallet met zand
  - Afvoeren van afval naar containers niveau 0m
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, 8 Tracking Periods

---

### 17. Rail-net Communication Point 1
- **File:** `C2023-11 Rail-net communication point 1.xlsx`
- **Mảng Logistics:** Railway Logistics IT (Công nghệ Quản lý Đường sắt)
- **Tổng Task:** 288 | **Task Logistics:** 4
- **Mô tả:** Dự án phát triển và triển khai hệ thống theo dõi tàu hỏa (Train tracking) cho ProRail (Công ty Đường sắt Hà Lan). Bao gồm tích hợp RFID, theo dõi vị trí toa tàu (wagon positions) và vận chuyển/lắp đặt container thiết bị viễn thông dọc tuyến đường sắt.
- **Task tiêu biểu:**
  - Transport and laying of container
  - Installatie kasten in container en aansluiting kabels
  - Tracking van treinnummer (Theo dõi số hiệu tàu)
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, 4 Tracking Periods

---

### 18. Railroad Construction
- **File:** `C2023-12 Railroad construction.xlsx`
- **Mảng Logistics:** Vận tải Đường sắt (Railway Freight Logistics)
- **Tổng Task:** 85 | **Task Logistics:** 13
- **Mô tả:** Dự án xây dựng tuyến đường sắt. Đặc trưng bởi chu trình lặp đi lặp lại: *Đóng gói → Vận chuyển → Giao hàng* (Packing, Transport and Delivery) cho từng phân đoạn tuyến đường.
- **Task tiêu biểu:**
  - Packing, Transport and Delivery (6 lần)
  - Transport & Delivery (7 lần)
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, 4 Tracking Periods

---

### 19. Rail-net Communication Point 2
- **File:** `C2023-13 Rail-net communication point 2.xlsx`
- **Mảng Logistics:** Railway Logistics IT (Công nghệ Quản lý Đường sắt)
- **Tổng Task:** 240 | **Task Logistics:** 25
- **Mô tả:** Dự án mở rộng hệ thống quản lý đường sắt cho ProRail (Phiên bản Train Three). Bao gồm thiết kế, sản xuất, vận chuyển và lắp đặt tủ thiết bị viễn thông tại các điểm trên tuyến đường sắt.
- **Task tiêu biểu:**
  - Levering kasten naar NL (Giao tủ thiết bị đến Hà Lan)
  - Levering kasten naar Venlo (Giao tủ thiết bị đến Venlo)
  - Levering reservedelen naar NL (Giao phụ tùng đến Hà Lan)
- **Sheets:** Baseline Schedule, Resources, Risk Analysis, 3 Tracking Periods

---

## Thống kê Tổng hợp

| Chỉ số | Giá trị |
|--------|---------|
| Tổng số Dự án | 19 |
| Tổng số Task | 2,834 |
| Tổng số Task Logistics | 454 |
| Dự án lớn nhất | Steel Industry (802 tasks) |
| Dự án nhiều Task Logistics nhất | Sea Electricity (144 tasks) |
| Dự án nhỏ nhất | Wine Production (26 tasks) |
