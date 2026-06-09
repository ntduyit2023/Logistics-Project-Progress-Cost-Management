# 📦 Phân Tích Chi Tiết Các Dataset cho Dự Án GLPO

> **Mục tiêu:** Liệt kê, thống kê chi tiết nội dung dữ liệu (cột, hàng, định dạng), và giải thích tại sao từng dataset phù hợp với 91 features trong 12 nhóm đặc trưng của dự án Graph-Based Logistics Project Optimizer.

---

## 📋 Tóm Tắt Nhanh

| # | Tên Dataset | Kích thước | Số cột | Định dạng | Giấy phép | Mức ưu tiên |
|---|---|---|---|---|---|---|
| 1 | PSPLIB | 2,040+ instances | ~6 trường/instance | `.sm` text | Miễn phí học thuật | ⭐⭐⭐⭐⭐ |
| 2 | OR&S UGent Empirical | 200+ dự án thực | ~15 trường/dự án | Excel, ProTrack | Miễn phí (đăng ký) | ⭐⭐⭐⭐⭐ |
| 3 | DataCo Supply Chain | ~180,000 dòng | 53 cột | CSV | CC BY 4.0 | ⭐⭐⭐⭐ |
| 4 | Construction PM (Kaggle) | ~1,000+ dòng | ~20-30 cột | CSV | Open | ⭐⭐⭐⭐ |
| 5 | Delay Causes (Mendeley) | ~200-500 khảo sát | 30-67 yếu tố | Excel/CSV | Open Data | ⭐⭐⭐ |
| 6 | EPA GHG Factors | 1,000+ hàng hóa | ~6 cột | CSV/Excel | Public Domain | ⭐⭐⭐ |
| 7 | IBM HR Analytics | 1,470 dòng | 35 cột | CSV | Open | ⭐⭐⭐ |
| 8 | VRP-REP Benchmark | 100+ instances | ~5 trường/instance | XML/TSPLIB | Open | ⭐⭐ |
| 9 | Stochastic VRP (HuggingFace) | 10-1000 khách hàng | ~4 trường/instance | JSON | Open | ⭐⭐ |
| 10 | **Case Study MFET 3008** | 21 công việc | ~8 trường/công việc | Text (có sẵn) | Nội bộ | ⭐⭐⭐⭐⭐ |

---

## 1️⃣ PSPLIB — Project Scheduling Problem Library

| Thuộc tính | Chi tiết |
|---|---|
| **Tổ chức** | TU München (Germany) |
| **URL** | https://www.om-db.wi.tum.de/psplib/main.html |
| **Kích thước** | 2,040+ instances (J30: 480, J60: 480, J90: 480, J120: 600) |
| **Phiên bản mở rộng** | MMRCPSP: 2,160 instances (Multi-Mode), RCPSP/max (time-lag) |
| **Định dạng** | `.sm` text files (Patterson format) |
| **Python package** | `pip install psplib` |
| **Giấy phép** | Miễn phí cho nghiên cứu học thuật |

### 📊 Các trường dữ liệu có trong mỗi instance

| Trường | Kiểu dữ liệu | Mô tả | Ví dụ giá trị |
|---|---|---|---|
| `num_jobs` | Integer | Tổng số công việc (bao gồm 2 dummy: start/end) | 32 (J30 = 30 thực + 2 dummy) |
| `num_resources` | Integer | Số loại tài nguyên tái tạo | 4 |
| `successors[]` | List[Int] | Danh sách công việc kế nhiệm cho mỗi task | [3, 5, 8] |
| `duration` | Integer | Thời gian thực hiện (đơn vị thời gian) | 7 |
| `demands[]` | List[Int] | Vector nhu cầu tài nguyên theo từng loại | [3, 0, 2, 1] |
| `capacities[]` | List[Int] | Giới hạn tài nguyên khả dụng mỗi chu kỳ | [12, 13, 4, 12] |
| `renewable` | Boolean[] | Loại tài nguyên: tái tạo (nhân sự) hay không (vật tư) | [True, True, True, True] |
| `modes[]` | List[Mode] | (MMRCPSP) Nhiều chế độ thực hiện khác nhau | Mode 1: dur=5, R=[3,2]; Mode 2: dur=8, R=[1,1] |

### 🔗 Ánh xạ với Features GLPO (17 features phủ)

| Feature GLPO (ID) | Trường PSPLIB tương ứng | Giải thích |
|---|---|---|
| Thời gian thực hiện kế hoạch (33) | `duration` | Thời gian hoàn thành mỗi task |
| Nhu cầu tài nguyên theo loại (46) | `demands[]` | Vector tài nguyên cần thiết |
| Tổng nhu cầu tài nguyên (47) | `sum(demands)` | Tính từ tổng vector demand |
| Mức độ khan hiếm tài nguyên (48) | `demands / capacities` | Tính tỷ lệ |
| Chế độ thực hiện (51) | `modes[]` | Đa chế độ trong MMRCPSP |
| Tài nguyên tái tạo vs không (54) | `renewable` | Phân loại trực tiếp |
| Bậc vào (55) | Tính từ `successors` | Đếm predecessors |
| Bậc ra (56) | `len(successors)` | Đếm successors |
| Lớp Topo (58) | Tính từ cấu trúc DAG | Topological sort |
| Loại ràng buộc phụ thuộc (59) | Mặc định FS, RCPSP/max có lag | Finish-to-Start |
| Số lượng đường đi qua nút (60) | Tính từ đồ thị | Graph traversal |
| Chiều dài đường đi dài nhất (61) | Tính từ đồ thị | Critical path |
| Thời điểm ES (36), EF (37) | Tính từ Forward Pass | CPM calculation |
| Thời điểm LS (38), LF (39) | Tính từ Backward Pass | CPM calculation |
| Thời gian dự trữ toàn bộ (34) | `LS - ES` | Slack calculation |
| Thời gian dự trữ tự do (35) | `min(ES_succ) - EF` | Free float |
| Số lượng công việc tranh chấp (49) | Tính khi lập lịch | Resource contention |

### ✅ Vì sao phù hợp với GLPO?

1. **Cấu trúc DAG sẵn có:** Mỗi instance là một đồ thị có hướng không chu trình (DAG) với quan hệ precedence rõ ràng → hoàn hảo để kiểm thử thuật toán CPM, Topological Sort, Cycle Detection.
2. **Bài toán RCPSP chuẩn:** Đây là benchmark quốc tế số 1 cho bài toán xếp lịch giới hạn tài nguyên → trực tiếp cho Pha 3 (MILP + GA Optimizer).
3. **Quy mô đa dạng:** J30 (nhỏ, validate nhanh) → J120 (lớn, test hiệu năng) → scale dần.
4. **Có parser Python sẵn:** `psplib` package giúp đọc dữ liệu dễ dàng, chuyển sang PyTorch Geometric.
5. **Multi-mode:** Phiên bản MMRCPSP cho phép mỗi task có nhiều phương án thực hiện (trade-off thời gian/tài nguyên).

---

## 2️⃣ OR&S UGent — Empirical Project Database

| Thuộc tính | Chi tiết |
|---|---|
| **Tổ chức** | Operations Research & Scheduling, Ghent University (Belgium) |
| **URL** | https://www.projectmanagement.ugent.be/research/data |
| **Download** | https://www.or-as.be/downloads |
| **Kích thước** | 200+ dự án thực tế + 30,000+ instances nhân tạo (RanGen) |
| **Định dạng** | Excel, ProTrack files, PMConverter output |
| **Giấy phép** | Miễn phí (đăng ký email) |

### 📊 Các trường dữ liệu (Empirical Projects)

| Trường | Kiểu | Mô tả |
|---|---|---|
| Activity ID | String | Mã hoạt động duy nhất |
| Duration (Planned) | Float | Thời lượng kế hoạch |
| Duration (Actual) | Float | Thời lượng thực tế |
| Predecessors | List | Danh sách hoạt động tiên quyết |
| Resource Name/ID | String | Tên loại tài nguyên |
| Resource Type | Category | Loại: Work/Material/Cost |
| Resource Availability | Integer | Số lượng khả dụng |
| Cost/Use | Float ($) | Chi phí mỗi lần sử dụng |
| Cost/Unit | Float ($/hr) | Chi phí đơn vị thời gian |
| **Planned Value (PV)** | Float ($) | Giá trị kế hoạch (EVM) |
| **Actual Cost (AC)** | Float ($) | Chi phí thực tế (EVM) |
| **Earned Value (EV)** | Float ($) | Giá trị đạt được (EVM) |
| CPI | Float | Cost Performance Index = EV/AC |
| SPI | Float | Schedule Performance Index = EV/PV |
| Project completeness | Color-coded | Mức độ đầy đủ dữ liệu (Green/Yellow/Red) |

### 📊 Các trường dữ liệu (RanGen Artificial — 30,000+ instances)

| Trường | Kiểu | Mô tả |
|---|---|---|
| Network structure | Graph | Cấu trúc DAG với độ phức tạp kiểm soát |
| OS (Order Strength) | Float [0,1] | Mật độ quan hệ phụ thuộc |
| RF (Resource Factor) | Float [0,1] | Tỷ lệ tài nguyên bị ràng buộc |
| RC (Resource Constrainedness) | Float [0,1] | Mức độ khan hiếm tài nguyên |
| Duration | Integer | Thời gian mỗi task |
| Resources | Vector | Nhu cầu tài nguyên |

### 🔗 Ánh xạ với Features GLPO (22 features phủ)

| Feature GLPO (ID) | Trường OR&S | Giải thích |
|---|---|---|
| Toàn bộ nhóm Thời gian (33-45) | Duration, Planned/Actual | Cung cấp cả planned & actual duration |
| **Giá trị đạt được (72)** | EV | Earned Value trực tiếp |
| **Chỉ số CPI (73)** | CPI | Cost Performance Index |
| **Chỉ số SPI (74)** | SPI | Schedule Performance Index |
| Nhu cầu tài nguyên (46) | Resources | Resource demand vector |
| Mức độ khan hiếm (48) | RC | Resource constrainedness |
| Bậc vào/ra (55, 56) | Network structure | Tính từ đồ thị |
| Phương sai thời gian (44) | Actual - Planned | Tính deviation |
| Xác suất trễ hạn (62) | Từ dữ liệu thực | Tính từ historical data |
| Chỉ số găng (63) | Monte Carlo sim | Từ network structure |

### ✅ Vì sao phù hợp với GLPO?

1. **Dữ liệu EVM thực tế duy nhất:** Đây là **nguồn duy nhất** cung cấp cả Planned Value, Actual Cost, Earned Value từ dự án thực → thiết yếu cho Pha 5 (EVM Dashboard).
2. **Dữ liệu thực (Empirical):** 200+ dự án thật, không phải dữ liệu giả lập → mô hình ML có ý nghĩa thực tế.
3. **RanGen cho scale testing:** 30,000+ instances nhân tạo với kiểm soát độ khó → benchmark cho thuật toán tối ưu hóa.
4. **So sánh planned vs actual:** Cho phép huấn luyện mô hình dự đoán biến động thời gian (DAGNN/GAT).
5. **Phân loại chất lượng dữ liệu:** Hệ thống màu Green/Yellow/Red giúp lọc dữ liệu đáng tin cậy.

---

## 3️⃣ DataCo Smart Supply Chain — Kaggle

| Thuộc tính | Chi tiết |
|---|---|
| **URL** | https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis |
| **Kích thước** | ~180,000 bản ghi giao dịch (3 năm) |
| **Số cột** | 53 cột |
| **Định dạng** | CSV (+ file mô tả + access logs) |
| **Giấy phép** | CC BY 4.0 |

### 📊 Các cột dữ liệu chính (chọn lọc 25/53 cột quan trọng)

| Cột | Kiểu | Mô tả | Ví dụ |
|---|---|---|---|
| `Days for shipping (real)` | Integer | Số ngày giao hàng thực tế | 3 |
| `Days for shipment (scheduled)` | Integer | Số ngày giao hàng kế hoạch | 4 |
| `Delivery Status` | Category | Trạng thái: Advance/Late/On-time/Canceled | "Late delivery" |
| `Late_delivery_risk` | Binary (0/1) | Có nguy cơ trễ hay không | 1 |
| `Shipping Mode` | Category | Phương thức: Standard/First/Second/Same Day | "Standard Class" |
| `Order Item Total` | Float ($) | Tổng giá trị đơn hàng | 299.98 |
| `Benefit per order` | Float ($) | Lợi nhuận trên đơn hàng | 91.25 |
| `Sales per customer` | Float ($) | Tổng doanh số theo khách hàng | 235.83 |
| `Order Item Discount` | Float ($) | Giá trị chiết khấu | 14.99 |
| `Order Item Discount Rate` | Float (%) | Tỷ lệ chiết khấu | 0.05 |
| `Order Item Product Price` | Float ($) | Giá sản phẩm | 327.75 |
| `Product Category` | Category | Ngành hàng | "Technology" |
| `Product Name` | String | Tên sản phẩm | "Smart TV 55 inch" |
| `Customer City` | String | Thành phố khách hàng | "Ho Chi Minh City" |
| `Customer Country` | String | Quốc gia | "Vietnam" |
| `Customer Segment` | Category | Phân khúc: Consumer/Corporate/Home Office | "Corporate" |
| `Order City` | String | Thành phố đơn hàng | "Los Angeles" |
| `Order Region` | String | Khu vực | "Southeast Asia" |
| `Order Date` | DateTime | Ngày đặt hàng | 2017-01-15 |
| `Shipping Date` | DateTime | Ngày giao hàng | 2017-01-18 |
| `Latitude` / `Longitude` | Float | Tọa độ giao hàng | 10.823, 106.629 |
| `Market` | Category | Thị trường | "Pacific Asia" |
| `Type` | Category | Loại thanh toán | "DEBIT" |

### 🔗 Ánh xạ với Features GLPO (12 features phủ)

| Feature GLPO (ID) | Cột DataCo | Cách ánh xạ |
|---|---|---|
| Chi phí vận chuyển trực tiếp (5) | `Order Item Total` − `Benefit per order` | Trừ lợi nhuận = chi phí thực |
| Chi phí vận chuyển quốc tế (30) | `Shipping Mode` + `Market` | Lọc cross-border orders |
| Thời gian dẫn đầu - Lead Time (43) | `Days for shipping (real)` | Trực tiếp |
| Phương sai thời gian (44) | `real − scheduled` | Schedule Variance |
| Xác suất trễ hạn (62) | `Late_delivery_risk` | Binary classifier target |
| Rủi ro thời tiết & mùa vụ (70) | `Order Date` + `Latitude` | Phân tích mùa vụ theo vùng |
| Mức độ phụ thuộc bên ngoài (67) | `Delivery Status` | "Canceled" = rủi ro bên ngoài |
| Chỉ số SPI tại nút (74) | `scheduled / real` | SPI approximation |
| Chi phí lưu kho (26) | Suy luận từ `Days shipping` | Thời gian chờ giao = chi phí giữ hàng |
| Chi phí đặt hàng (27) | Suy luận từ volume | Frequency analysis |
| Chi phí thiếu hụt (28) | `Delivery Status = Canceled` | Shortage indicator |
| Đóng góp vào NPV (78) | `Benefit per order` | Revenue proxy |

### ✅ Vì sao phù hợp với GLPO?

1. **Volume lớn (180K dòng):** Đủ dữ liệu cho huấn luyện ML/Deep Learning trên chuỗi cung ứng.
2. **Trực tiếp phủ Nhóm 4 (Logistics & SCM):** 7 features về logistics hầu hết đều ánh xạ được.
3. **Có biến mục tiêu sẵn:** `Late_delivery_risk` là biến nhị phân, sẵn sàng cho classification models.
4. **Dữ liệu thời gian (3 năm):** Cho phép phân tích xu hướng mùa vụ, seasonality.
5. **Dữ liệu toàn cầu:** Bao gồm nhiều khu vực → mô phỏng supply chain đa quốc gia.

---

## 4️⃣ Construction Project Management Dataset — Kaggle

| Thuộc tính | Chi tiết |
|---|---|
| **URL** | https://www.kaggle.com/datasets/felixzhao/projectmanagementfailed |
| **Kích thước** | ~1,000-1,300 bản ghi từ dự án hạ tầng |
| **Số cột** | ~20-30 cột |
| **Định dạng** | CSV |
| **Giấy phép** | Open |

### 📊 Các cột dữ liệu chính

| Cột | Kiểu | Mô tả |
|---|---|---|
| `Project_ID` / `Task_ID` | String | Mã định danh |
| `Project_Type` | Category | Loại: Residential/Commercial/Infrastructure |
| `Planned_Duration` | Integer (ngày) | Thời gian kế hoạch |
| `Actual_Duration` | Integer (ngày) | Thời gian thực tế |
| `Schedule_Deviation` | Float (%) | Chênh lệch tiến độ |
| `Project_Budget_USD` | Float ($) | Ngân sách dự kiến |
| `Actual_Cost` | Float ($) | Chi phí thực tế |
| `Budget_Utilization_Rate` | Float (%) | Tỷ lệ sử dụng ngân sách |
| `Labor_Required` | Integer | Nhân công cần thiết |
| `Equipment_Usage` | Integer | Số thiết bị sử dụng |
| `Complexity_Score` | Integer (1-5) | Độ phức tạp kỹ thuật |
| `Risk_Level` | Category | Mức rủi ro: Low/Medium/High |
| `Resource_Availability` | Float (%) | Tỷ lệ tài nguyên sẵn có |
| `Change_Request_Frequency` | Integer | Số lần thay đổi phạm vi |
| `Project_Manager_Experience` | Integer (năm) | Kinh nghiệm PM |
| `Team_Turnover_Rate` | Float (%) | Tỷ lệ nghỉ việc |
| `Status` | Category | Completed/Overdue/Failed |
| `Location` | String | Vị trí dự án |

### 🔗 Ánh xạ với Features GLPO (15 features phủ)

| Feature GLPO (ID) | Cột Dataset | Giải thích |
|---|---|---|
| Thời gian thực hiện kế hoạch (33) | `Planned_Duration` | Trực tiếp |
| Phương sai thời gian (44) | `Actual − Planned` | Tính deviation |
| Chi phí nhân công (0) | Từ `Labor_Required` | Suy luận chi phí |
| Chi phí mua sắm thiết bị (4) | `Equipment_Usage` | Proxy |
| Mức độ phức tạp kỹ thuật (65) | `Complexity_Score` | Trực tiếp |
| Xác suất trễ hạn (62) | `Status = Overdue` | Binary target |
| Mức độ khan hiếm tài nguyên (48) | `Resource_Availability` | 1 − availability = scarcity |
| Rủi ro nhân sự nghỉ việc (83) | `Team_Turnover_Rate` | Trực tiếp |
| Kinh nghiệm nhân sự (80) | `Project_Manager_Experience` | Trực tiếp |
| Rủi ro làm lại (66) | `Change_Request_Frequency` | Proxy: nhiều thay đổi = nhiều rework |

### ✅ Vì sao phù hợp với GLPO?

1. **Có biến "Failed":** Cho phép xây dựng mô hình dự đoán thất bại dự án → trực tiếp phục vụ module rủi ro.
2. **Kết hợp cost + schedule + risk:** Ba chiều dữ liệu cùng tồn tại → phân tích đa mục tiêu.
3. **Có Complexity Score:** Đầu vào cho GNN feature → đặc trưng nút cho mô hình dự đoán trễ.
4. **Dữ liệu nhân sự:** Turnover rate, PM experience → phủ Nhóm 10 (Con người & Tổ chức).

---

## 5️⃣ Causes of Delays in Construction Projects — Mendeley Data

| Thuộc tính | Chi tiết |
|---|---|
| **URL** | https://data.mendeley.com/datasets/zb6wm7h6z6 |
| **Kích thước** | ~200-500 phiếu khảo sát, 67+ yếu tố trễ |
| **Định dạng** | Excel/CSV |
| **Giấy phép** | Open Data (CC BY 4.0) |

### 📊 Cấu trúc dữ liệu

| Nhóm cột | Mô tả | Ví dụ giá trị |
|---|---|---|
| **Thông tin người trả lời** | Vai trò, kinh nghiệm, học vấn | Contractor, 10+ năm, Master |
| **30-67 yếu tố trễ (Likert 1-5)** | Mỗi cột = 1 nguyên nhân trễ, đánh giá tần suất & mức độ | "Thiếu trang thiết bị": 4/5 |
| **Nhóm yếu tố** | Owner / Contractor / External / Design | "Contractor-related" |

### Các yếu tố trễ tiêu biểu (mỗi cái = 1 cột)

| Yếu tố | Likert Scale (1-5) | Ánh xạ GLPO |
|---|---|---|
| Chậm thanh toán từ chủ đầu tư | Tần suất + Mức độ | Mức độ phụ thuộc bên ngoài (67) |
| Thiếu thiết bị tại công trường | Tần suất + Mức độ | Mức độ khan hiếm tài nguyên (48) |
| Thiếu nhân sự có chuyên môn | Tần suất + Mức độ | Mức độ chuyên môn yêu cầu (79) |
| Thay đổi thiết kế liên tục | Tần suất + Mức độ | Rủi ro làm lại (66) |
| Tranh chấp hợp đồng | Tần suất + Mức độ | Chi phí tranh chấp (24) |
| Điều kiện thời tiết | Tần suất + Mức độ | Rủi ro thời tiết (70) |
| Quản lý yếu kém | Tần suất + Mức độ | Rủi ro mệt mỏi & kiệt sức (82) |
| Nhân sự nghỉ việc | Tần suất + Mức độ | Rủi ro nhân sự nghỉ việc (83) |
| Vấn đề giấy phép | Tần suất + Mức độ | Chi phí giấy phép (21) |
| Tai nạn lao động | Tần suất + Mức độ | Rủi ro an toàn lao động (85) |

### ✅ Vì sao phù hợp với GLPO?

1. **Phủ Nhóm 8 (Rủi ro) sâu nhất:** 67 yếu tố rủi ro cụ thể → xây dựng Risk Register định lượng.
2. **Dữ liệu khảo sát chuyên gia:** Có giá trị nghiên cứu học thuật, trích dẫn được trong đồ án.
3. **Phủ Nhóm 3 (Hợp đồng & Pháp lý):** Tranh chấp, giấy phép, thanh toán → ít dataset nào có.
4. **Phương pháp RII (Relative Importance Index):** Xếp hạng yếu tố theo tầm quan trọng → trọng số cho mô hình.

---

## 6️⃣ EPA Supply Chain GHG Emission Factors

| Thuộc tính | Chi tiết |
|---|---|
| **Tổ chức** | US Environmental Protection Agency |
| **URL** | https://data.gov (search "USEEIO Supply Chain GHG") |
| **GitHub** | https://github.com/USEPA/supply-chain-factors |
| **Kích thước** | 1,016 hàng hóa (NAICS 2017) |
| **Định dạng** | CSV, Excel, R-compatible |
| **Giấy phép** | Public Domain (US Government) |

### 📊 Các cột dữ liệu

| Cột | Kiểu | Mô tả | Đơn vị |
|---|---|---|---|
| `NAICS Code` | String | Mã ngành hàng hóa | "236210" |
| `Commodity Name` | String | Tên hàng hóa/dịch vụ | "Commercial building construction" |
| `SEF (without margins)` | Float | Phát thải chuỗi sản xuất | kg CO₂e / USD |
| `MEF (margins)` | Float | Phát thải vận chuyển + phân phối | kg CO₂e / USD |
| `SEF + MEF` | Float | Tổng phát thải chuỗi cung ứng | kg CO₂e / USD |
| `CO₂` | Float | Lượng CO₂ riêng | kg CO₂ / USD |
| `CH₄` | Float | Lượng Methane riêng | kg CH₄ / USD |
| `N₂O` | Float | Lượng Nitrous Oxide riêng | kg N₂O / USD |

### 🔗 Ánh xạ với Features GLPO (5 features phủ — Nhóm 11: ESG)

| Feature GLPO (ID) | Cột EPA | Giải thích |
|---|---|---|
| Tác động môi trường (86) | `SEF + MEF` | Trực tiếp: CO₂e / USD chi tiêu |
| Chi phí xử lý chất thải (87) | Suy luận từ `SEF` | Emission = proxy cho waste |
| Thuế Carbon / Tín chỉ Carbon (89) | `CO₂` × giá carbon | Tính: kg CO₂ × $/tấn |
| Yêu cầu tuân thủ ESG (90) | Ngưỡng `SEF + MEF` | Vượt ngưỡng = không tuân thủ |
| Tác động cộng đồng (88) | Suy luận gián tiếp | Khu vực emission cao = impact cao |

### ✅ Vì sao phù hợp với GLPO?

1. **Nguồn chính phủ uy tín:** EPA = cơ quan chính thức → dữ liệu tin cậy, trích dẫn mạnh.
2. **Phủ hoàn toàn Nhóm 11 (ESG):** Là nguồn **duy nhất** cung cấp dữ liệu ESG định lượng.
3. **Áp dụng spend-based:** Chi phí mua sắm (từ Case Study) × emission factor = tính ngay được carbon footprint.
4. **1,016 hàng hóa:** Đủ chi tiết để ánh xạ mọi loại hoạt động trong dự án logistics.

---

## 7️⃣ IBM HR Analytics: Employee Attrition & Performance

| Thuộc tính | Chi tiết |
|---|---|
| **URL** | https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset |
| **Kích thước** | 1,470 nhân viên |
| **Số cột** | 35 cột |
| **Dữ liệu thiếu** | Không có missing values |
| **Mất cân bằng** | 16% Attrition=Yes, 84% Attrition=No |
| **Giấy phép** | Open |

### 📊 Các cột dữ liệu chính (25/35 cột)

| Cột | Kiểu | Mô tả | Ví dụ |
|---|---|---|---|
| `Attrition` | Binary (Yes/No) | **Biến mục tiêu:** Nhân viên nghỉ việc? | Yes |
| `Age` | Integer | Tuổi nhân viên | 35 |
| `Department` | Category | Phòng ban | "Research & Development" |
| `Education` | Ordinal (1-5) | Trình độ: Below College → Doctor | 3 (Bachelor) |
| `EducationField` | Category | Lĩnh vực chuyên môn | "Technical Degree" |
| `JobLevel` | Ordinal (1-5) | Cấp bậc công việc | 2 |
| `JobRole` | Category | Vai trò | "Manufacturing Director" |
| `JobSatisfaction` | Ordinal (1-4) | Độ hài lòng: Low → Very High | 4 |
| `EnvironmentSatisfaction` | Ordinal (1-4) | Hài lòng môi trường làm việc | 3 |
| `MonthlyIncome` | Integer ($) | Thu nhập tháng | 5,993 |
| `PercentSalaryHike` | Integer (%) | % tăng lương gần nhất | 11 |
| `TotalWorkingYears` | Integer | Tổng số năm kinh nghiệm | 8 |
| `YearsAtCompany` | Integer | Số năm tại công ty | 6 |
| `YearsInCurrentRole` | Integer | Số năm ở vị trí hiện tại | 4 |
| `YearsSinceLastPromotion` | Integer | Năm kể từ lần thăng tiến cuối | 0 |
| `YearsWithCurrManager` | Integer | Năm làm việc với quản lý hiện tại | 5 |
| `NumCompaniesWorked` | Integer | Số công ty đã làm | 3 |
| `OverTime` | Binary (Yes/No) | Có làm thêm giờ? | Yes |
| `WorkLifeBalance` | Ordinal (1-4) | Cân bằng cuộc sống: Bad → Best | 3 |
| `PerformanceRating` | Ordinal (1-4) | Đánh giá hiệu suất | 3 |
| `TrainingTimesLastYear` | Integer | Số lần đào tạo năm trước | 3 |
| `StockOptionLevel` | Ordinal (0-3) | Mức quyền chọn cổ phiếu | 1 |
| `DistanceFromHome` | Integer (km) | Khoảng cách nhà → công ty | 9 |
| `RelationshipSatisfaction` | Ordinal (1-4) | Hài lòng quan hệ đồng nghiệp | 1 |
| `BusinessTravel` | Category | Tần suất công tác | "Travel_Frequently" |

### 🔗 Ánh xạ với Features GLPO (7 features — Nhóm 10: Con người & Tổ chức)

| Feature GLPO (ID) | Cột IBM HR | Giải thích |
|---|---|---|
| Mức độ chuyên môn yêu cầu (79) | `JobLevel`, `Education` | Cấp bậc + trình độ |
| Kinh nghiệm nhân sự (80) | `TotalWorkingYears`, `YearsAtCompany` | Trực tiếp |
| Hiệu ứng đường cong học tập (81) | `TrainingTimesLastYear` | Proxy cho learning effort |
| Rủi ro mệt mỏi & kiệt sức (82) | `OverTime`, `WorkLifeBalance` | Overtime + WLB thấp = rủi ro |
| **Rủi ro nhân sự nghỉ việc (83)** | `Attrition` | **Biến mục tiêu chính** |
| Năng suất nhân sự (52) | `PerformanceRating` | Đánh giá hiệu suất |
| Mức độ phối hợp liên phòng ban (84) | `Department` + `BusinessTravel` | Cross-functional indicator |

### ✅ Vì sao phù hợp với GLPO?

1. **Phủ hoàn toàn Nhóm 10 (Con người & Tổ chức):** 7/7 features đều ánh xạ được.
2. **Dữ liệu sạch, không missing:** Sẵn sàng sử dụng ngay, không cần preprocessing nặng.
3. **Biến mục tiêu rõ ràng:** `Attrition` = nhân viên nghỉ việc → huấn luyện model dự đoán rủi ro nhân sự.
4. **1,470 mẫu:** Đủ cho ML classification (Logistic Regression, Random Forest, XGBoost).
5. **Liên kết OT → Fatigue → Attrition:** Cho phép mô hình hóa chuỗi nhân quả trong GLPO graph.

---

## 8️⃣ VRP-REP — Vehicle Routing Problem Repository

| Thuộc tính | Chi tiết |
|---|---|
| **URL** | https://www.vrp-rep.org |
| **CVRPLIB** | http://vrp.atd-lab.inf.puc-rio.br/index.php/en/ |
| **Kích thước** | 100+ bộ instances, hàng nghìn instance riêng lẻ |
| **Định dạng** | XML (chuẩn VRP-REP) + TSPLIB text |
| **Giấy phép** | Open |

### 📊 Các trường dữ liệu trong mỗi instance

| Trường | Kiểu | Mô tả |
|---|---|---|
| Depot coordinates | (x, y) | Vị trí kho/trung tâm phân phối |
| Customer coordinates | (x, y)[] | Vị trí các điểm giao hàng |
| Demand | Integer[] | Nhu cầu hàng hóa tại mỗi điểm |
| Vehicle capacity | Integer | Tải trọng tối đa xe |
| Time windows | (a, b)[] | Khung thời gian giao hàng (VRPTW) |
| Service time | Integer[] | Thời gian phục vụ tại mỗi điểm |
| Distance matrix | Float[][] | Ma trận khoảng cách giữa các điểm |
| Best Known Solution (BKS) | Float | Tổng quãng đường tối ưu đã biết |

### 🔗 Ánh xạ với Features GLPO (5 features)

| Feature GLPO (ID) | Trường VRP | Giải thích |
|---|---|---|
| Chi phí vận chuyển trực tiếp (5) | Distance × cost/km | Tính từ routing solution |
| Chi phí vận chuyển quốc tế (30) | Distance matrix | Large-scale instances |
| Thời gian dẫn đầu - Lead Time (43) | Time windows + service time | Delivery scheduling |
| Chi phí lưu kho (26) | Demand + capacity mismatch | Overflow = storage needed |
| Tỷ lệ sử dụng thiết bị (53) | Load / capacity | Vehicle utilization |

### ✅ Vì sao phù hợp với GLPO?

1. **Bài toán vận tải chuẩn:** VRP là bài toán tối ưu tổ hợp kinh điển trong logistics.
2. **Benchmark có BKS:** So sánh nghiệm thuật toán với kết quả tối ưu đã biết.
3. **Đồ thị hoàn chỉnh:** Mỗi instance = đồ thị đầy đủ → test GNN/DRL routing.
4. **Đa biến thể:** CVRP, VRPTW, Multi-depot → phù hợp các kịch bản logistics khác nhau.

---

## 9️⃣ Stochastic VRP Benchmark — Hugging Face

| Thuộc tính | Chi tiết |
|---|---|
| **HuggingFace** | `Yahias21/vrp_benchmark` |
| **Kích thước** | Instances 10-1000 khách hàng |
| **Đặc biệt** | Có yếu tố ngẫu nhiên (stochastic delays) |
| **Giấy phép** | Open |

### 📊 Các trường dữ liệu

| Trường | Kiểu | Mô tả |
|---|---|---|
| Customer locations | (x, y)[] | Tọa độ khách hàng |
| Demands (stochastic) | Distribution[] | Nhu cầu ngẫu nhiên |
| Travel times (stochastic) | Distribution[] | Thời gian di chuyển biến động |
| Delay factors | Float[] | Hệ số trễ do thời tiết/giao thông |

### 🔗 Ánh xạ với Features GLPO (4 features)

| Feature GLPO (ID) | Trường | Giải thích |
|---|---|---|
| Phương sai thời gian (44) | Stochastic travel times | Variance trực tiếp |
| Rủi ro thời tiết & mùa vụ (70) | Delay factors | Weather risk component |
| Xác suất trễ hạn (62) | P(delay > threshold) | Tính từ distribution |
| Mức độ phụ thuộc bên ngoài (67) | Stochastic demands | External uncertainty |

### ✅ Vì sao phù hợp với GLPO?

1. **Yếu tố bất định:** Dataset **duy nhất** có stochastic factors → huấn luyện mô hình dự báo trễ.
2. **Scalable:** 10 → 1000 khách hàng → test từ nhỏ đến lớn.
3. **Trực tiếp cho Pha 5 (AI Predictive):** Dữ liệu biến động → GNN/GAT dự đoán delay propagation.

---

## 🔟 Case Study MFET 3008/5040 — Ground Truth (Đã có sẵn)

| Thuộc tính | Chi tiết |
|---|---|
| **File** | `e:\University\Year 3-3\DA3\casestudy_raw_text.txt` |
| **Kích thước** | 21 công việc (A → U) |
| **Định dạng** | Text (cần parse thủ công) |

### 📊 Các trường dữ liệu cho mỗi công việc

| Trường | Kiểu | Ví dụ (Task A) | Ví dụ (Task F) |
|---|---|---|---|
| Code | Char | A | F |
| Task Name | String | Architectural decisions | Software design |
| Duration (days) | Integer | 4 | 12 |
| Predecessors | List | − (Start) | [C] |
| Labor Resources | List[String] | [DC, DM] | [DC, DevC] |
| Company Staff Cost | Float ($/day) | DC=$200, DM=$200 | DC=$200, DevC=$150 |
| Contractor Cost | Float ($/day) | DC=$350, DM=$350 | DC=$350, DevC=$250 |
| Number Company Staff | Integer | DC=1, DM=1 | DC=1, DevC=1 |

### 📊 Dữ liệu cấp dự án (Ground Truth)

| Thông số | Giá trị |
|---|---|
| Tổng số công việc | 21 (A → U) |
| Thời gian bình thường (unlimited resources) | **66 ngày** |
| Đường găng | **A → C → G → I → J → N → R → T → U** |
| Thời gian khi giới hạn tài nguyên (RCPSP) | **96 ngày** |
| Chi phí cơ bản (Early Start) | **$49,510** |
| Chi phí tối ưu (với thầu phụ) | **$70,230** |
| Tiền phạt trễ hạn | $2,000/tuần (sau tuần 12) |
| Tiền thưởng hoàn thành sớm | $3,000/tuần (trước tuần 12) |
| Chi phí PM overhead | $500/tuần |
| OT Saturday multiplier | 1.5× |
| OT Sunday multiplier | 3.0× |
| Contractor induction time | 3 ngày |
| 8 loại nhân sự | DC, DM, DevC, DevM, AC, AM, Purchase, Doc |

### 🔗 Ánh xạ với Features GLPO (28+ features phủ)

Đây là dataset phủ **nhiều nhóm nhất** vì nó chứa đủ thông tin cho CPM, RCPSP, Crashing, và EVM:

| Nhóm Feature | Số features phủ | Chi tiết |
|---|---|---|
| Nhóm 0: Chi phí Trực tiếp | 3/9 | Nhân công (0), Thuê ngoài (1), Làm thêm giờ (2) |
| Nhóm 1: Chi phí Gián tiếp | 2/6 | PM Overhead (9), Đào tạo thầu phụ (13) |
| Nhóm 3: Hợp đồng & Pháp lý | 2/7 | Tiền phạt (19), Tiền thưởng (20) |
| Nhóm 5: Thời gian | 10/13 | Toàn bộ CPM: ES, EF, LS, LF, TS, FS, Duration, Induction (42) |
| Nhóm 6: Tài nguyên | 5/9 | Demand (46), Intensity (47), Scarcity (48), Contention (49), Renewable (54) |
| Nhóm 7: Cấu trúc Đồ thị | 6/7 | In/Out-degree, Topo Layer, Dependency Type, Path Count, Longest Path |

### ✅ Vì sao phù hợp với GLPO?

1. **Ground Truth đối chiếu:** Mọi thuật toán GLPO **phải** tái hiện được 66 ngày và đường găng chuẩn xác.
2. **Phủ 6/12 nhóm:** Một file duy nhất chứa đủ Cost + Time + Resource + Graph + Contract + Risk.
3. **Bài toán đa tầng:** Q2 (CPM) → Q4 (Slack Management) → Q5 (RCPSP) → Q6 (Crashing + Outsourcing) → Q7 (EVM).
4. **Đã có sẵn:** Không cần tải thêm, parse thủ công từ text file.
5. **Context học thuật:** Trực tiếp liên quan đến nội dung đồ án.

---

## 📈 Ma Trận Tổng Hợp: Dataset × Nhóm Feature

| Dataset \ Nhóm Feature | 0-CP TT | 1-CP GĐ | 2-CP Cơ hội | 3-HĐ & PL | 4-Logistics | 5-Thời gian | 6-Tài nguyên | 7-Đồ thị | 8-Rủi ro | 9-CL & GT | 10-Nhân sự | 11-ESG |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **PSPLIB** | | | | | | ✅✅✅ | ✅✅✅ | ✅✅✅ | ✅ | | | |
| **OR&S UGent** | | | | | | ✅✅✅ | ✅✅ | ✅✅ | ✅✅ | ✅✅✅ | | |
| **DataCo SCM** | ✅ | | | | ✅✅✅ | ✅✅ | | | ✅✅ | ✅ | | |
| **Construction PM** | ✅✅ | | | ✅ | | ✅✅ | ✅ | | ✅✅ | | ✅✅ | |
| **Mendeley Delays** | | | | ✅✅ | | | | | ✅✅✅ | | ✅✅ | |
| **EPA GHG** | | | | | | | | | | | | ✅✅✅ |
| **IBM HR** | | | | | | | ✅ | | | | ✅✅✅ | |
| **VRP-REP** | ✅ | | | | ✅✅ | ✅ | | | | | | |
| **Stochastic VRP** | | | | | | ✅ | | | ✅✅ | | | |
| **Case Study MFET** | ✅✅✅ | ✅✅ | | ✅✅ | | ✅✅✅ | ✅✅✅ | ✅✅✅ | | | | |

> **Chú thích:** ✅ = phủ nhẹ (1-2 features) | ✅✅ = phủ vừa (3-5 features) | ✅✅✅ = phủ sâu (6+ features)

---

## 🎯 Kết Luận

> [!IMPORTANT]
> **Không có dataset đơn lẻ nào phủ tất cả 91 features.** Chiến lược là kết hợp nhiều nguồn, mỗi nguồn phủ 1-3 nhóm mạnh nhất.

### Top 3 ưu tiên cao nhất (phải có):
1. **Case Study MFET 3008** — Ground truth, đã có sẵn, phủ 6 nhóm
2. **PSPLIB J30** — Benchmark quốc tế cho CPM/RCPSP, phủ 3 nhóm cốt lõi
3. **OR&S UGent** — Nguồn EVM thực tế duy nhất, phủ 5 nhóm

### Top 4 hỗ trợ (nên có):
4. **DataCo Supply Chain** — 180K dòng, phủ Logistics & SCM
5. **IBM HR Analytics** — Phủ hoàn toàn nhóm Nhân sự
6. **Construction PM** — Kết hợp cost/schedule/risk
7. **EPA GHG Factors** — Phủ hoàn toàn nhóm ESG

### Tùy chọn (bổ sung khi cần):
8. **Mendeley Delays** — Risk Register chi tiết
9. **VRP-REP** — Bài toán routing logistics
10. **Stochastic VRP** — Dữ liệu bất định cho AI
