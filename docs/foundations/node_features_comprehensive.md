# 🎯 Bảng Thống Kê Toàn Diện: Các Yếu Tố Tác Động Lên Mỗi Node Trong Đồ Thị Dự Án

Tài liệu này liệt kê **đầy đủ nhất** tất cả các yếu tố (features/factors) tác động lên mỗi Node (công việc/task) trong đồ thị dự án, giúp hình thành trọng số cho thuật toán tìm đường đi hợp lý nhất (Optimal Path Finding). Được tổng hợp từ các nguồn: PMBOK Guide, RCPSP Literature, GNN/ML Research, Logistics & Supply Chain Management, và ESG Frameworks.

---

## NHÓM 1: CHI PHÍ TRỰC TIẾP (Direct Costs)

Là các chi phí phát sinh **trực tiếp và có thể quy trách nhiệm rõ ràng** cho từng công việc cụ thể.

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 1.1 | **Chi phí nhân công nội bộ (Internal Labor Cost)** | Lương cơ bản × số ngày × số nhân sự cần cho task. Tính riêng theo từng nhóm kỹ năng. | $/ngày/người | PMBOK Ch.7, Case Study |
| 1.2 | **Chi phí thuê ngoài (Subcontracting / Outsourcing Cost)** | Lương thầu phụ × (duration + thời gian đào tạo). Đơn giá thầu phụ thường cao hơn nội bộ 40-75%. | $/ngày/người | PMBOK, Case Study Q6a |
| 1.3 | **Chi phí làm thêm giờ (Overtime / Crashing Cost)** | Hệ số nhân lương: 1.5× (thứ 7), 2.0× (đêm), 3.0× (chủ nhật/lễ). Chi phí biên tăng dần khi crash nhiều. | $/ngày | Case Study Q6b |
| 1.4 | **Chi phí nguyên vật liệu (Material / Raw Material Cost)** | Giá mua nguyên liệu, linh kiện, bán thành phẩm cần thiết cho task. Biến động theo thị trường. | $/đơn vị | PMBOK Ch.7 |
| 1.5 | **Chi phí mua sắm thiết bị (Equipment Procurement Cost)** | Giá mua hoặc giá thuê thiết bị chuyên dụng gắn với task cụ thể. | $/thiết bị | PMBOK Ch.7 |
| 1.6 | **Chi phí vận chuyển trực tiếp (Direct Transportation Cost)** | Phí vận chuyển nguyên vật liệu đầu vào hoặc sản phẩm đầu ra gắn liền với task đó. Phụ thuộc khoảng cách, trọng lượng, phương thức. | $/chuyến | Logistics/SCM |
| 1.7 | **Chi phí khấu hao máy móc (Equipment Depreciation)** | Phần khấu hao thiết bị sử dụng trong thời gian thực hiện task. | $/giờ sử dụng | PMBOK Ch.7 |
| 1.8 | **Chi phí năng lượng / nhiên liệu (Energy / Fuel Cost)** | Điện, nước, nhiên liệu tiêu thụ trực tiếp cho quá trình thực hiện task (ví dụ: chạy máy hàn, máy CNC). | $/kWh hoặc $/lít | Manufacturing |
| 1.9 | **Chi phí kiểm thử / kiểm định (Testing & Inspection Cost)** | Chi phí kiểm tra chất lượng đầu ra của task (phân tích mẫu, kiểm thử phần mềm, kiểm định an toàn). | $/lần kiểm | PMBOK Ch.8 |

---

## NHÓM 2: CHI PHÍ GIÁN TIẾP (Indirect Costs / Overhead)

Là các chi phí **không gắn trực tiếp** vào một task cụ thể nhưng phát sinh do sự tồn tại và kéo dài của dự án.

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 2.1 | **Chi phí quản lý dự án (Project Management Overhead)** | Lương PM, PMO, nhân viên hành chính, chi phí văn phòng, phần mềm quản lý. Tỷ lệ thuận với thời gian dự án. | $/tuần | PMBOK Ch.7, Case Study ($500/tuần) |
| 2.2 | **Chi phí mặt bằng / thuê văn phòng (Facility / Office Rent)** | Tiền thuê nhà xưởng, văn phòng, phòng lab dùng chung cho nhiều task. | $/tháng | PMBOK |
| 2.3 | **Chi phí tiện ích chung (Utilities)** | Điện, nước, internet, điều hòa phục vụ toàn bộ dự án (không gắn riêng 1 task). | $/tháng | PMBOK |
| 2.4 | **Chi phí truyền thông & phối hợp (Communication & Coordination Cost)** | Thời gian họp, báo cáo tiến độ, đồng bộ liên phòng ban. Đặc biệt cao tại các Merge Nodes. | giờ/tuần | PMI Research |
| 2.5 | **Chi phí đào tạo nội bộ (Internal Training Cost)** | Chi phí đào tạo nhân sự nội bộ để thực hiện task mới hoặc công nghệ mới. | $/người | PMBOK Ch.9 |
| 2.6 | **Chi phí quản lý chất lượng chung (Quality Management Overhead)** | Chi phí duy trì hệ thống QMS (ISO 9001), kiểm toán nội bộ, quy trình phê duyệt. | $/dự án | PMBOK Ch.8 |

---

## NHÓM 3: CHI PHÍ CƠ HỘI & CHI PHÍ CHÌM (Opportunity & Sunk Costs)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 3.1 | **Chi phí cơ hội nhân sự (Labor Opportunity Cost)** | Giá trị mà nhân sự bị mất khi phải chờ đồng bộ tại merge node thay vì làm việc khác có giá trị. | $/ngày/người | Economics |
| 3.2 | **Chi phí cơ hội vốn (Capital Opportunity Cost)** | Lợi nhuận mất đi do vốn bị "khóa" trong hàng tồn kho hoặc thiết bị chờ sử dụng. | %/năm × giá trị | Finance, TCO |
| 3.3 | **Chi phí chìm (Sunk Cost)** | Chi phí đã chi không thể thu hồi. Theo PMBOK: **không nên** dùng để ra quyết định tiếp tục/dừng dự án. | $ | PMBOK Ch.7 |
| 3.4 | **Chi phí trì hoãn doanh thu (Revenue Delay Cost)** | Mỗi ngày dự án kéo dài = mỗi ngày sản phẩm chưa ra thị trường = mất doanh thu tiềm năng. | $/ngày | Finance |

---

## NHÓM 4: CHI PHÍ HỢP ĐỒNG & PHÁP LÝ (Contractual & Legal Costs)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 4.1 | **Tiền phạt trễ hạn (Penalty / Liquidated Damages)** | Phạt hợp đồng khi hoàn thành sau deadline. Có thể tính theo ngày hoặc tuần. | $/tuần | Case Study ($2,000/tuần) |
| 4.2 | **Tiền thưởng hoàn thành sớm (Early Completion Bonus)** | Thưởng hợp đồng khi bàn giao trước hạn. Tạo động lực rút ngắn tiến độ. | $/tuần | Case Study ($3,000/tuần) |
| 4.3 | **Chi phí giấy phép / phê duyệt (Permits & Licensing)** | Phí xin giấy phép xây dựng, giấy phép vận hành, chứng nhận an toàn. | $/lần | Construction PM |
| 4.4 | **Chi phí bảo hiểm dự án (Project Insurance)** | Bảo hiểm tai nạn lao động, bảo hiểm thiết bị, bảo hiểm trách nhiệm nghề nghiệp. | $/giai đoạn | PMBOK Ch.11 |
| 4.5 | **Chi phí bảo hành & hậu mãi (Warranty & After-sales)** | Cam kết bảo hành sau bàn giao. Chất lượng task kém → chi phí bảo hành tăng. | $/năm | Contract Law |
| 4.6 | **Chi phí tranh chấp & kiện tụng (Dispute & Litigation)** | Chi phí phát sinh khi xảy ra tranh chấp hợp đồng với nhà thầu phụ hoặc khách hàng. | $/vụ | Legal |
| 4.7 | **Chi phí tuân thủ quy định (Regulatory Compliance)** | Chi phí đáp ứng các tiêu chuẩn bắt buộc (an toàn lao động, môi trường, PCCC). | $/task | ESG, PMBOK |

---

## NHÓM 5: CHI PHÍ LOGISTICS & CHUỖI CUNG ỨNG (Logistics & Supply Chain Costs)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 5.1 | **Chi phí lưu kho / bảo quản (Inventory Holding / Carrying Cost)** | Chi phí lưu trữ hàng hóa chờ task tiếp theo sử dụng. Bao gồm thuê kho, bảo hiểm, hao hụt. | $/ngày/đơn vị | Logistics/SCM |
| 5.2 | **Chi phí đặt hàng (Ordering / Procurement Cost)** | Chi phí hành chính cho mỗi lần đặt mua vật tư: xử lý đơn, liên lạc nhà cung cấp, kiểm tra. | $/đơn hàng | SCM |
| 5.3 | **Chi phí thiếu hụt / hết hàng (Shortage / Stockout Cost)** | Khi vật tư cần cho task không có sẵn: phải chờ hoặc đặt gấp với giá cao hơn. | $/lần thiếu | SCM |
| 5.4 | **Chi phí hàng lỗi thời / hết hạn (Obsolescence / Expiry Cost)** | Vật tư mua sớm nhưng dự án bị trễ → hàng hết hạn hoặc lỗi thời công nghệ, phải mua lại. | $/đơn vị | SCM, TCO |
| 5.5 | **Chi phí vận chuyển quốc tế (International Freight)** | Cước container, phí hải quan, thuế nhập khẩu, phí bảo hiểm hàng hóa quốc tế. | $/container | Logistics |
| 5.6 | **Chi phí đóng gói & xử lý (Packaging & Handling)** | Chi phí đóng gói bảo vệ, bốc xếp, palletizing cho vật tư hoặc sản phẩm của task. | $/đơn vị | Logistics |
| 5.7 | **Chi phí logistics ngược (Reverse Logistics)** | Chi phí thu hồi, trả lại hàng lỗi, tái chế, tiêu hủy. | $/đơn vị | SCM, ESG |

---

## NHÓM 6: YẾU TỐ THỜI GIAN (Temporal Factors)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 6.1 | **Thời gian thực hiện kế hoạch (Planned Duration)** | Thời gian dự kiến hoàn thành task theo kế hoạch. | ngày | CPM, PMBOK |
| 6.2 | **Thời gian dự trữ toàn bộ (Total Float / Total Slack)** | Khoảng trễ tối đa mà task có thể chịu mà không làm trễ toàn bộ dự án. | ngày | CPM |
| 6.3 | **Thời gian dự trữ tự do (Free Float)** | Khoảng trễ tối đa mà task có thể chịu mà không làm trễ task kế tiếp (successor). | ngày | CPM |
| 6.4 | **Thời điểm bắt đầu sớm nhất (Early Start - ES)** | Thời điểm sớm nhất có thể bắt đầu task, sau khi tất cả predecessors hoàn thành. | ngày | CPM Forward Pass |
| 6.5 | **Thời điểm kết thúc sớm nhất (Early Finish - EF)** | EF = ES + Duration. | ngày | CPM |
| 6.6 | **Thời điểm bắt đầu muộn nhất (Late Start - LS)** | Thời điểm muộn nhất phải bắt đầu task để không trễ dự án. | ngày | CPM Backward Pass |
| 6.7 | **Thời điểm kết thúc muộn nhất (Late Finish - LF)** | Thời điểm muộn nhất phải hoàn thành task. | ngày | CPM |
| 6.8 | **Thời gian chờ đầu vào (Wait / Queue Time)** | Thời gian task phải chờ vì predecessor chưa xong hoặc tài nguyên chưa sẵn sàng. | ngày | Scheduling Theory |
| 6.9 | **Thời gian thiết lập / chuyển giao (Setup / Transition Time)** | Thời gian chuẩn bị khi nhân sự hoặc thiết bị chuyển từ task trước sang task hiện tại. | giờ | Manufacturing |
| 6.10 | **Thời gian đào tạo thầu phụ (Induction / Onboarding Time)** | Thời gian cố định (+3 ngày trong Case Study) để thầu phụ mới làm quen dự án. | ngày | Case Study |
| 6.11 | **Thời gian dẫn đầu (Lead Time)** | Thời gian từ khi đặt hàng vật tư đến khi nhận được (gồm sản xuất + vận chuyển). | ngày | SCM |
| 6.12 | **Phương sai thời gian (Duration Variance / σ²)** | Độ dao động thời gian thực tế so với kế hoạch, dựa trên lịch sử hoặc ước lượng 3 điểm (PERT). | ngày² | PERT, Monte Carlo |
| 6.13 | **Ước lượng 3 điểm PERT (Optimistic / Most Likely / Pessimistic)** | Thời gian lạc quan (O), thời gian hay xảy ra nhất (M), thời gian bi quan (P). Duration trung bình = (O + 4M + P) / 6. | ngày | PERT |

---

## NHÓM 7: YẾU TỐ TÀI NGUYÊN (Resource Factors)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 7.1 | **Nhu cầu tài nguyên theo loại (Resource Demand Vector)** | Vector mô tả số lượng từng loại tài nguyên cần cho task. Ví dụ: [DC=1, DM=0, DevC=1, Doc=1]. | người/loại | RCPSP |
| 7.2 | **Tổng nhu cầu tài nguyên (Total Resource Intensity)** | Tổng số nhân sự / thiết bị cần dùng cho task. | người/task | RCPSP |
| 7.3 | **Mức độ khan hiếm tài nguyên (Resource Scarcity Index)** | Tỷ lệ: Nhu cầu tài nguyên / Số lượng khả dụng. Giá trị ≥ 1 = xung đột chắc chắn. | ratio | RCPSP |
| 7.4 | **Số lượng task tranh chấp cùng tài nguyên (Resource Contention Count)** | Số task khác đang cạnh tranh cùng loại tài nguyên tại cùng thời điểm. | task count | Scheduling |
| 7.5 | **Khả năng thay thế tài nguyên (Resource Substitutability)** | Tài nguyên loại A có thể được thay bằng loại B không? Nếu có → tăng tính linh hoạt. | boolean/score | MRCPSP |
| 7.6 | **Chế độ thực hiện (Execution Mode - Multi-mode)** | Một task có thể được thực hiện bằng nhiều cách khác nhau (kết hợp tài nguyên / thời gian / chi phí khác nhau). | mode ID | MRCPSP |
| 7.7 | **Năng suất nhân sự (Labor Productivity / Efficiency)** | Hiệu suất thực tế so với kế hoạch. Nhân sự mới/thầu phụ thường có năng suất thấp hơn (Learning Curve). | % | HR, Manufacturing |
| 7.8 | **Tỷ lệ sử dụng thiết bị (Equipment Utilization Rate)** | Phần trăm thời gian thiết bị đang được sử dụng thực sự so với thời gian khả dụng. | % | Manufacturing |
| 7.9 | **Tài nguyên tái tạo vs. không tái tạo (Renewable vs. Non-renewable)** | Nhân sự = tài nguyên tái tạo (dùng xong lại có). Vật tư = không tái tạo (dùng hết là hết). | category | RCPSP Theory |

---

## NHÓM 8: YẾU TỐ CẤU TRÚC ĐỒ THỊ (Graph Topology / Structural Features)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 8.1 | **Bậc vào (In-degree)** | Số lượng predecessors (task tiên quyết). In-degree cao = nhiều nhánh phải chờ đồng bộ. | count | Graph Theory |
| 8.2 | **Bậc ra (Out-degree)** | Số lượng successors (task phụ thuộc). Out-degree cao = ảnh hưởng lan rộng nếu trễ. | count | Graph Theory |
| 8.3 | **Hệ số trung gian (Betweenness Centrality)** | Mức độ nút nằm trên các đường đi ngắn nhất/dài nhất giữa các cặp nút khác. | ratio | Graph Theory, GNN |
| 8.4 | **Lớp Topo (Topological Layer / Depth)** | Vị trí của task trong thứ tự topo (lớp 0 = task đầu, lớp cuối = task cuối). | layer index | Topological Sort |
| 8.5 | **Loại ràng buộc phụ thuộc (Dependency Constraint Type)** | FS (Finish-to-Start), SS (Start-to-Start), FF (Finish-to-Finish), SF (Start-to-Finish) + Lag/Lead Time. | category | PMBOK Ch.6 |
| 8.6 | **Số lượng đường đi qua node (Path Count Through Node)** | Tổng số đường đi từ Source đến Sink đi qua node này. Node nằm trên nhiều đường = quan trọng cao. | count | Graph Analysis |
| 8.7 | **Chiều dài đường đi dài nhất qua node (Longest Path Through Node)** | Đường đi dài nhất từ Source đến Sink đi qua node này. Nếu bằng Makespan = node nằm trên đường găng. | ngày | CPM |

---

## NHÓM 9: YẾU TỐ RỦI RO & BẤT ĐỊNH (Risk & Uncertainty Factors)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 9.1 | **Xác suất trễ hạn (Delay Probability)** | Tỷ lệ task bị trễ so với kế hoạch, dựa trên lịch sử ngành hoặc dữ liệu nội bộ. | % | Risk Management |
| 9.2 | **Chỉ số găng (Criticality Index)** | Tỷ lệ % task nằm trên đường găng qua N lần mô phỏng Monte Carlo. | % | Monte Carlo Simulation |
| 9.3 | **Chỉ số nhạy cảm (Cruciality / Sensitivity Index)** | Hệ số tương quan giữa thời gian task và tổng thời gian dự án. Task có SI cao = rất nhạy cảm. | correlation | PERT/Monte Carlo |
| 9.4 | **Mức độ phức tạp kỹ thuật (Technical Complexity Score)** | Đánh giá chủ quan hoặc dựa trên số lượng yêu cầu kỹ thuật, công nghệ mới, tích hợp đa hệ thống. | 1-5 scale | PMBOK Ch.11 |
| 9.5 | **Rủi ro chất lượng / Làm lại (Rework Probability)** | Xác suất task phải làm lại do lỗi kỹ thuật hoặc không đạt chuẩn nghiệm thu. | % | Quality Management |
| 9.6 | **Mức độ phụ thuộc bên ngoài (External Dependency Level)** | Mức phụ thuộc vào bên thứ 3 (nhà cung cấp, cơ quan phê duyệt, thời tiết). | 0-1 score | Risk Register |
| 9.7 | **Dự phòng rủi ro đã biết (Contingency Reserve - Known-Unknowns)** | Ngân sách dự phòng cho các rủi ro đã được nhận diện trong Risk Register. PM quản lý. | $ hoặc ngày | PMBOK Ch.11 |
| 9.8 | **Dự phòng rủi ro chưa biết (Management Reserve - Unknown-Unknowns)** | Ngân sách dự phòng cho các sự kiện chưa lường trước. Ban lãnh đạo quản lý. | $ | PMBOK Ch.11 |
| 9.9 | **Rủi ro thời tiết / mùa vụ (Seasonal / Weather Risk)** | Một số task bị ảnh hưởng bởi điều kiện thời tiết (xây dựng ngoài trời, vận tải đường biển mùa bão). | 0-1 score | Construction PM |
| 9.10 | **Rủi ro công nghệ (Technology Risk)** | Sử dụng công nghệ mới chưa được kiểm chứng đầy đủ hoặc phiên bản beta. | 0-1 score | IT PM |

---

## NHÓM 10: YẾU TỐ CHẤT LƯỢNG & GIÁ TRỊ (Quality & Value Factors)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 10.1 | **Giá trị đạt được (Earned Value - EV)** | Phần trăm khối lượng đã hoàn thành × ngân sách kế hoạch. Đo lường giá trị thực tế tạo ra. | $ | EVM, PMBOK Ch.7 |
| 10.2 | **Chỉ số hiệu suất chi phí tại node (Node CPI = EV/AC)** | Hiệu quả sử dụng ngân sách tại task cụ thể. CPI < 1 = lãng phí, CPI > 1 = tiết kiệm. | ratio | EVM |
| 10.3 | **Chỉ số hiệu suất tiến độ tại node (Node SPI = EV/PV)** | Tốc độ hoàn thành thực tế vs kế hoạch tại task cụ thể. SPI < 1 = chậm tiến độ. | ratio | EVM |
| 10.4 | **Mức độ ảnh hưởng downstream (Downstream Impact Score)** | Số lượng task và đường đi phía sau bị ảnh hưởng trực tiếp nếu node này trễ. | task count | Graph Analysis |
| 10.5 | **Giá trị chiến lược (Strategic Business Value)** | Tầm quan trọng của task đối với mục tiêu kinh doanh tổng thể (bàn giao sản phẩm, thu tiền, ký hợp đồng mới). | 1-10 scale | Portfolio Management |
| 10.6 | **Tiêu chuẩn chất lượng yêu cầu (Quality Standard Level)** | Tiêu chuẩn kỹ thuật cần đạt (ISO, Safety, Performance, regulatory). Tiêu chuẩn cao hơn = chi phí QC cao hơn. | category | PMBOK Ch.8 |
| 10.7 | **Giá trị hiện tại ròng (NPV Contribution)** | Đóng góp của task vào NPV tổng dự án, tính theo dòng tiền vào/ra tại thời điểm task thực hiện. | $ | Finance, RCPSP-NPV |

---

## NHÓM 11: YẾU TỐ CON NGƯỜI & TỔ CHỨC (Human & Organizational Factors)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 11.1 | **Mức độ chuyên môn yêu cầu (Required Skill Level)** | Trình độ kỹ năng tối thiểu cần thiết để thực hiện task. Task cần chuyên gia hiếm = rủi ro cao. | level (junior/mid/senior) | PMBOK Ch.9 |
| 11.2 | **Kinh nghiệm nhân sự gán cho task (Assigned Staff Experience)** | Số năm kinh nghiệm hoặc số dự án tương tự đã tham gia của nhân sự được giao task. | năm / số dự án | HR |
| 11.3 | **Hiệu ứng đường cong học tập (Learning Curve Effect)** | Nhân sự mới hoặc thầu phụ cần thời gian làm quen → năng suất thấp ban đầu, tăng dần. | % productivity | Manufacturing, HR |
| 11.4 | **Rủi ro mệt mỏi / kiệt sức (Fatigue / Burnout Risk)** | Nhân sự làm OT liên tục hoặc nhiều task liên tiếp → năng suất giảm, lỗi tăng. | 0-1 score | Human Factors, HSE |
| 11.5 | **Rủi ro nhân sự nghỉ việc / nghỉ ốm (Staff Turnover / Absence Risk)** | Xác suất nhân sự chủ chốt nghỉ giữa chừng, gây gián đoạn task. | % | HR |
| 11.6 | **Mức độ phối hợp liên phòng ban (Cross-functional Coordination Need)** | Số lượng phòng ban / đội nhóm cần phối hợp để hoàn thành task. Càng nhiều = càng phức tạp giao tiếp. | team count | Organizational Theory |
| 11.7 | **Rủi ro an toàn lao động (Occupational Safety Risk)** | Mức độ nguy hiểm của task đối với sức khỏe nhân sự (làm việc trên cao, tiếp xúc hóa chất, điện áp cao). | risk level | HSE, ESG |

---

## NHÓM 12: YẾU TỐ MÔI TRƯỜNG, XÃ HỘI & QUẢN TRỊ - ESG (Environmental, Social & Governance)

| # | Yếu tố | Mô tả | Đơn vị đo | Nguồn tham khảo |
|:---:|:---|:---|:---:|:---|
| 12.1 | **Tác động môi trường (Environmental Impact)** | Lượng khí thải CO2, chất thải, tiếng ồn, nước thải phát sinh từ task. | tấn CO2 / kg chất thải | ESG, ISO 14001 |
| 12.2 | **Chi phí xử lý chất thải (Waste Disposal Cost)** | Chi phí thu gom, xử lý, tiêu hủy hoặc tái chế chất thải từ quá trình thực hiện task. | $/tấn | ESG |
| 12.3 | **Tác động cộng đồng (Community / Social Impact)** | Ảnh hưởng đến dân cư xung quanh: tiếng ồn, bụi, giao thông, việc làm địa phương. | qualitative score | ESG, Stakeholder Mgmt |
| 12.4 | **Chi phí Carbon / Thuế Carbon (Carbon Tax / Carbon Credit)** | Chi phí phải trả hoặc tín chỉ carbon phải mua do phát thải CO2 từ task (vận tải, sản xuất). | $/tấn CO2 | ESG, EU ETS |
| 12.5 | **Yêu cầu ESG từ nhà đầu tư / khách hàng (ESG Compliance Requirements)** | Các tiêu chuẩn ESG mà dự án phải đáp ứng để duy trì hợp đồng hoặc nguồn vốn. | compliance level | ESG Reporting |

---

## TỔNG KẾT

| Nhóm | Số lượng yếu tố | Phân loại |
|:---:|:---:|:---|
| 1. Chi phí Trực tiếp | 9 | Định lượng - Gắn trực tiếp vào task |
| 2. Chi phí Gián tiếp | 6 | Định lượng - Phân bổ theo thời gian |
| 3. Chi phí Cơ hội & Chìm | 4 | Định lượng - Kinh tế học |
| 4. Chi phí Hợp đồng & Pháp lý | 7 | Định lượng - Hợp đồng |
| 5. Chi phí Logistics & Chuỗi cung ứng | 7 | Định lượng - Logistics/SCM |
| 6. Yếu tố Thời gian | 13 | Định lượng - CPM/PERT |
| 7. Yếu tố Tài nguyên | 9 | Định lượng & Phân loại - RCPSP |
| 8. Yếu tố Cấu trúc Đồ thị | 7 | Định lượng - Graph Theory/GNN |
| 9. Yếu tố Rủi ro & Bất định | 10 | Xác suất - Risk Management |
| 10. Yếu tố Chất lượng & Giá trị | 7 | Định lượng & Định tính - EVM/Finance |
| 11. Yếu tố Con người & Tổ chức | 7 | Định tính & Xác suất - HR/HSE |
| 12. Yếu tố ESG | 5 | Định tính & Định lượng - Sustainability |
| **TỔNG CỘNG** | **91** | |

---

## 📚 Nguồn Tham Khảo Chính

1. **PMBOK Guide (7th Edition)** — Project Management Institute (PMI). Chapters 6 (Schedule), 7 (Cost), 8 (Quality), 9 (Resource), 11 (Risk).
2. **Brucker et al. (1999).** *"Resource-Constrained Project Scheduling: Notation, Classification, Models, and Methods."* European Journal of Operational Research.
3. **Kolisch & Hartmann (2006).** *"Experimental Investigation of Heuristics for RCPSP."* European Journal of Operational Research.
4. **Tassel et al. (2023).** *"A Reinforcement Learning Environment for RCPSP."* — GNN node features for scheduling.
5. **Veličković et al. (2018).** *"Graph Attention Networks."* ICLR 2018 — Attention-based node feature aggregation.
6. **Total Cost of Ownership (TCO)** — Supply Chain Management frameworks (Degraeve et al., 2000).
7. **ESG Integration in Project Management** — PMI Sustainability Report, ISO 14001, GRI Standards.
