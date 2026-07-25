# Kiến trúc Phân bổ 38 Nhóm Chi phí & Hệ thống Rủi ro Tiến độ Monte Carlo

Tài liệu này chuẩn hóa toàn bộ cấu trúc 38 nhóm chi phí thành phần (Cost Sub-groups), Quy định Trích xuất Dữ liệu, Phạm vi Dataloader và cơ chế Mô phỏng Rủi ro Tiến độ (Monte Carlo Schedule Risk) áp dụng cho 3 Loại Dự án chính thức: CON (Xây dựng), ITLG (Công nghệ & Logistics) và PRO (Tư vấn & Dịch vụ).

---

## I. Quy tắc Cốt lõi & Phân định Phạm vi Dataloader

1. Thống nhất về Base Cost & Total Cost:
   - Chi phí tài chính duy nhất đại diện cho công việc là Base Cost.
   - Total Cost bằng Base Cost (Total Cost = Base Cost).
   - Hoàn toàn loại bỏ việc nhân phần trăm Rủi ro ảo vào Chi phí tài chính.

2. Quy tắc Phân định Rõ ràng: Labor vs Equipment vs Energy:
   - labor: Chỉ bao gồm chi phí con người 100% (Công nhân, Kỹ sư, Chuyên gia, Dev...). Tuyệt đối không gộp ca máy hay thiết bị vào labor.
   - equipment: Chi phí thuê máy móc, khấu hao thiết bị, phần cứng, server rack.
   - energy: Nhiên liệu (dầu diesel, xăng) và điện năng tiêu thụ trực tiếp để vận hành máy móc/server ở nhóm equipment.

3. Quy định Phạm vi Dataloader vs Người dùng Nhập:
   - Dataloader CHỈ tự động tính toán 2 nhóm chi phí dựa trên Resource Demand & Thời gian:
     * labor (Tính động từ nguồn lực con người)
     * equipment (Tính động từ nguồn lực máy móc/phần cứng)
   - Tất cả 36 nhóm chi phí còn lại (material, energy, overhead, insurance, logistics, financial costs...): Sẽ do NGƯỜI DÙNG TỰ NHẬP / ĐIỀU CHỈNH trên hệ thống. Công thức phân bổ phần trăm % ở dưới CHỈ dùng cho mục đích Trích xuất dữ liệu ban đầu (Data Extraction Pipeline).

---

## II. Bộ Công thức Trích xuất Dữ liệu (Extraction Formulas)

### 1. Công thức Chi phí Trực tiếp (Direct Costs - G1)
- Labor (Nhân công con người 100% - Tính động trong Dataloader & Extraction):
  labor = Tổng các nguồn lực con người (Số lượng nhân sự * duration_hours * hourly_rate)

- Equipment (Máy móc / Thiết bị / Phần cứng - Tính động trong Dataloader & Extraction):
  equipment = Tổng các nguồn lực máy móc (Số lượng máy * duration_hours * hourly_rate)

- Material (Vật tư / Vật liệu):
  material = Lump_Sum_Cost_From_Excel
  (Trích xuất trực tiếp tổng số tiền mua vật tư/dịch vụ cố định từ cột chi phí trong file Excel thô, không tính theo số lượng * đơn giá).

- Energy (Năng lượng / Nhiên liệu chạy máy - Trích xuất ban đầu):
  energy = equipment * energy_pct
  (Trong đó energy_pct ban đầu: CON = 30%, ITLG = 20%, PRO = 5% của chi phí equipment).

- Testing & Inspection (QA/QC / Kiểm định - Trích xuất ban đầu):
  testing_inspection = (labor + material + equipment + energy) * testing_pct

- Direct Cost (Tổng Chi phí Trực tiếp):
  Direct Cost = labor + material + equipment + energy + testing_inspection

### 2. Công thức Chi phí Làm thêm giờ (Overtime)
- Overtime (Chi phí OT):
  overtime = Tổng các nguồn lực con người (Số lượng nhân sự * overtime_hours * hourly_rate * 1.5)

### 3. Công thức Trích xuất Chi phí Gián tiếp & Vận hành (Data Extraction Pipeline)
Các nhóm chi phí còn lại được khởi tạo ban đầu trong pipeline trích xuất dựa trên Direct Cost và tỷ lệ % phân bổ của Loại dự án (CON, ITLG, PRO):

  subgroup_cost = Direct Cost * profile_pct

  (Lưu ý: Các giá trị này sau khi trích xuất ban đầu sẽ cho phép Người dùng tự nhập/chỉnh sửa trên UI).

### 4. Công thức Base Cost và Total Cost
- Base Cost (Chi phí Cơ sở):
  Base Cost = Sum(Tất cả 38 nhóm chi phí thành phần từ G1 đến G6)

- Total Cost (Tổng Chi phí):
  Total Cost = Base Cost

---

## III. Quy trình Trích xuất Dữ liệu Ban đầu (Data Extraction Pipeline)

### Bước 1: Đọc Dữ liệu Đầu vào (Input Data từ Excel / Dataset)
- Thông tin Task: Tên Task, Thời gian (duration_hours), Số giờ OT (overtime_hours), Loại dự án (CON, ITLG, PRO).
- Nguồn lực gán cho Task (Resource Demand): Danh sách tài nguyên và số lượng được gán từ Excel.
- Chi phí thô từ Excel: Baseline Costs / Lump Sum Material Cost.

### Bước 2: Phân loại & Trích xuất Chi phí Trực tiếp
- Tính labor (Con người 100%).
- Tính equipment (Máy móc 100%).
- Trích xuất material = Số tiền cố định từ Excel.
- Khởi tạo energy và testing_inspection ban đầu.
- Tính Direct Cost = labor + material + equipment + energy + testing_inspection.

### Bước 3: Tính Chi phí Làm thêm giờ (overtime)
- Tính overtime khi overtime_hours > 0.

### Bước 4: Khởi tạo Chi phí Gián tiếp & Vận hành Ban đầu
- Khởi tạo 33 nhóm chi phí còn lại theo công thức subgroup_cost = Direct Cost * profile_pct (Để người dùng có dữ liệu mẫu ban đầu, sau đó người dùng có thể chỉnh sửa tự do).

### Bước 5: Tổng hợp Base Cost và Total Cost
- Base Cost = Sum(Tất cả 38 nhóm chi phí thành phần).
- Total Cost = Base Cost.

---

## IV. Danh mục 38 Nhóm Chi phí Thành phần (38 Sub-groups)

Toàn bộ chi phí được chia làm 6 khối chức năng chính:

### 1. Khối Chi phí Trực tiếp (Direct Costs - 5 Sub-groups)
* labor: Chi phí nhân công nội bộ (Tự động tính trong Dataloader).
* material: Chi phí vật tư (Số tiền cố định từ Excel / Người dùng nhập).
* equipment: Chi phí máy móc, thiết bị, phần cứng (Tự động tính trong Dataloader).
* energy: Chi phí nhiên liệu, điện năng chạy máy móc/server (Người dùng nhập / Khởi tạo ban đầu).
* testing_inspection: Chi phí kiểm định, thử nghiệm, QA/QC (Người dùng nhập / Khởi tạo ban đầu).

### 2. Khối Chi phí Gián tiếp & Quản lý (Overhead Costs - 6 Sub-groups)
* project_management: Chi phí ban quản lý dự án (PMO, điều hành).
* facility: Chi phí thuê mặt bằng, bãi, văn phòng.
* utilities: Chi phí điện, nước sinh hoạt/vận hành.
* communication: Chi phí viễn thông, cloud API, internet, họp.
* training: Chi phí đào tạo, chuyển giao công nghệ.
* quality_management: Chi phí quản lý hệ thống chất lượng (ISO, Audit).

### 3. Khối Chi phí Phụ thuộc Thời gian & Chậm trễ (Time-dependent - 7 Sub-groups)
* overtime: Chi phí làm thêm giờ con người (Tính tự động khi có overtime_hours).
* delay_penalty: Chi phí phạt hợp đồng do chậm tiến độ.
* inventory_holding: Chi phí lưu kho, lưu bãi vật tư.
* waiting_cost: Chi phí chờ đợi tài nguyên/máy móc.
* idle_resource: Chi phí tài nguyên rảnh rỗi nhàn rỗi.
* revenue_delay: Tổn thất doanh thu do chậm ra mắt/vận hành.
* expediting: Chi phí đẩy nhanh tiến độ khẩn cấp (Rush fee).

### 4. Khối Chi phí Pháp lý & Bảo hiểm (Contractual & Compliance - 7 Sub-groups)
* insurance: Chi phí bảo hiểm (công trình, thiết bị, trách nhiệm).
* rework: Chi phí khắc phục, làm lại trực tiếp.
* warranty: Chi phí dự phòng bảo hành.
* litigation: Chi phí tranh chấp pháp lý, hợp đồng, NDA, SLA.
* regulatory_compliance: Phí giấy phép, kiểm định môi trường, quy chuẩn.
* contingency_reserve: Chi phí dự phòng tài chính công việc.
* management_reserve: Chi phí dự phòng quản lý cấp dự án.

### 5. Khối Chi phí Chuỗi cung ứng & Logistics (Supply Chain - 6 Sub-groups)
* transportation: Chi phí vận chuyển vật tư, máy móc, hạ tầng.
* ordering: Chi phí đặt hàng, mua sắm, đấu thầu.
* packaging: Chi phí đóng gói, bảo quản.
* reverse_logistics: Chi phí logistics ngược (thu hồi phế liệu, giàn giáo, RMA).
* customs: Chi phí hải quan, thuế nhập khẩu thiết bị.
* supplier_coordination: Chi phí phối hợp nhà cung cấp / thầu phụ.

### 6. Khối Chi phí Tài chính & Chiến lược (Financial & Strategic - 7 Sub-groups)
* capital_cost: Chi phí vốn (Capital expenditure / Cost of capital).
* financing_cost: Chi phí lãi vay ngân hàng / tín dụng ngắn hạn / chiết khấu hóa đơn.
* opportunity_cost: Chi phí cơ hội (Mất hợp đồng mới khi bị giam nhân sự).
* npv_loss: Tổn thất giá trị hiện tại ròng khi dòng tiền bị đẩy lùi.
* esg_cost: Chi phí tiêu chuẩn môi trường, xã hội & quản trị (ESG).
* carbon_tax: Thuế phát thải carbon / phí môi trường.
* reputation_cost: Chi phí tổn hại uy tín thương hiệu.

---

## V. Ma trận Phân bổ Trích xuất Ban đầu theo 3 Loại Dự án (CON, ITLG, PRO)

| Khối Chi Phí | Sub-group | CON (Xây dựng) | ITLG (CNTT & Logistics) | PRO (Tư vấn & Dịch vụ) |
| :--- | :--- | :---: | :---: | :---: |
| 1. Trực tiếp | labor | Có (Đội thầu/Công nhân) | Có (Kỹ sư/Dev/PM) | Có (Chuyên gia cao cấp) |
| | material | Lump Sum Excel | Lump Sum Excel / IT | Lump Sum Excel / Tài liệu |
| | equipment | Máy công trình | Server/Mạng/IoT | Thiết bị làm việc |
| | energy | Dầu diesel chạy máy | Điện Datacenter/Server | Điện VP |
| | testing_inspection | Thử tải/Kiểm định hàn | Testing/UAT/Security | Review/Thẩm định |
| 2. Gián tiếp | project_management | Ban QLDA công trường | Scrum Master/PMO | Chủ nhiệm dự án |
| | facility | Văn phòng công trường | Thuê Datacenter/VP | Văn phòng |
| | utilities | Điện nước công trường | Điện nước hạ tầng IT | Điện nước VP |
| | communication | Viễn thông công trường | Cloud API/Server | Khảo sát/Họp hành |
| | training | An toàn lao động | Đào tạo chuyển giao | Chuyển giao tri thức |
| | quality_management | ISO xây dựng | Security Audit/Code review | Thẩm định chất lượng |
| 3. Phụ thuộc thời gian | overtime | Theo giờ OT | Theo giờ OT | Theo giờ OT |
| | delay_penalty | Phạt hợp đồng | Phạt SLA | Phạt trễ hạn |
| | inventory_holding | Bãi vật tư | Kho linh kiện/bãi | Hồ sơ/Lưu trữ |
| | waiting_cost & idle_resource | Máy chờ ca | Nhân lực chờ task | Chuyên gia rảnh rỗi |
| | revenue_delay | Thu phí đường chậm | Chậm ra mắt app | Chậm thu Milestone |
| | expediting | Tăng tốc thi công | Rush release | Báo cáo gấp |
| 4. Pháp lý & Bảo hiểm | insurance | Bảo hiểm công trình | Cyber insurance/Hardware | Bảo hiểm trách nhiệm |
| | rework | Sửa bê tông/kết cấu | Fix bug/UAT rework | Sửa báo cáo |
| | warranty | Bảo hành công trình | Bảo hành phần mềm | Hỗ trợ sau tư vấn |
| | litigation | Tranh chấp thi công | Tranh chấp bản quyền/SLA | Tranh chấp NDA/Dịch vụ |
| | regulatory_compliance | Giấy phép xây dựng/ĐTM | License/Chứng nhận | Quy chuẩn tư vấn |
| | contingency & management_reserve | Dự phòng tài chính | Dự phòng tài chính | Dự phòng tài chính |
| 5. Chuỗi cung ứng | transportation | Vận tải nặng | Vận chuyển phần cứng | Di chuyển khảo sát |
| | ordering & packaging | Đặt & bó thép/xi măng | Mua linh kiện/đóng gói | In ấn/Đóng tập |
| | reverse_logistics | Dọn phế liệu/giàn giáo | Thu hồi/đổi trả RMA | Thu hồi hồ sơ/thiết bị |
| | customs | Nhập máy nặng/cáp biển | Nhập Server chuyên dụng | Hồ sơ quốc tế |
| | supplier_coordination | Hàng chục thầu phụ | Vendor Cloud/API | Cộng tác viên |
| 6. Tài chính & Chiến lược | capital_cost | Vốn xây dựng | Vốn CapEx hạ tầng | Vốn lưu động trả lương |
| | financing_cost | Lãi vay thi công | Nợ mạo hiểm/Leasing | Chiết khấu hóa đơn |
| | opportunity_cost | Cơ hội máy móc | First-mover advantage | Cơ hội chuyên gia |
| | npv_loss | Chậm thu tiền | Tổn thất dòng tiền | Trễ thanh toán |
| | esg_cost & carbon_tax | Phát thải/Môi trường | Xanh hóa Datacenter/Xe | Ít phát sinh |
| | reputation_cost | Uy tín nhà thầu | Sập app/Lộ tin | Báo cáo sai |

---

## VI. Mô hình Rủi ro Monte Carlo Schedule Risk

Hệ số phần trăm rủi ro được dùng để tính biến động thời gian thi công:

Simulated Duration = Baseline Duration * (1.0 + complexity + weather_contingency + general_contingency + rework_risk)

### Thiết lập theo Project Type:

1. CON (Xây dựng):
   - weather_contingency: 15% - 30% (Biến động cao do làm việc ngoài trời, biển).
   - complexity: 15% - 30% (Địa chất, tải trọng kĩ thuật).
   - rework_risk: 10% - 15% (Kiểm định bê tông/mối hàn không đạt phải làm lại).

2. ITLG (CNTT & Logistics):
   - weather_contingency: 0%.
   - complexity: 20% - 40% (Thuật toán, tích hợp API, hạ tầng phần mềm).
   - rework_risk: 15% - 25% (Fix bug, UAT, thay đổi Requirement).

3. PRO (Tư vấn & Dịch vụ):
   - weather_contingency: 0%.
   - complexity: 10% - 20% (Độ phức tạp quy trình & báo cáo).
   - rework_risk: 5% - 10% (Chỉnh sửa báo cáo theo ý Hội đồng).
