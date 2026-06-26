# Mô hình Toán học Toàn diện (Comprehensive Mathematical Model): Tối ưu hóa 91 Features

Dựa trên bảng 91 Node Features, đây là **Mô hình Khối (Generalized Objective Function)** tích hợp toàn bộ các khía cạnh Kinh tế, Quản trị, Rủi ro, Cấu trúc, và ESG của một dự án. 

Đây không chỉ là hàm chi phí cơ bản, mà là một **Hàm Thưởng/Phạt (Reward Function)** dành cho thuật toán AI (Reinforcement Learning / GNN) để đánh giá chất lượng của một kịch bản lập lịch (Schedule $S$).

---

## 1. PHƯƠNG TRÌNH HÀM MỤC TIÊU TỔNG QUÁT (TGC)

Mục tiêu của AI là **Tối thiểu hóa Tổng Chi phí Quy đổi (Total Generalized Cost - TGC)** của toàn bộ dự án (bao gồm $N$ công việc).

$$ \min TGC(S) = \sum_{i=1}^{N} \Big( C^{Direct}_i + C^{Indirect}_i + C^{Logistics}_i + C^{Contract}_i + C^{ESG}_i + C^{Risk}_i - V^{Value}_i \Big) + C^{Opportunity} $$

Trong đó, mỗi thành phần được phân rã từ 91 Features như sau:

---

### 1.1. Cụm Chi phí Trực tiếp (Direct Costs) - Nhóm 1
Đây là dòng tiền lõi chảy ra khi thực hiện công việc $i$. Bị ảnh hưởng bởi **Năng suất nhân sự ($F_{7.7}$)** và **Đường cong học tập ($F_{11.3}$)**.

$$ C^{Direct}_i = \frac{F_{1.1} + F_{1.2} + F_{1.3}}{F_{7.7} \times F_{11.3}} + F_{1.4} + F_{1.5} + F_{1.6} + F_{1.7} + F_{1.8} + F_{1.9} $$
*(Nhân công nội bộ, Thuê ngoài, OT, Vật liệu, Thiết bị, Vận tải, Khấu hao, Năng lượng, Kiểm định)*

### 1.2. Cụm Chi phí Gián tiếp (Indirect/Overhead) - Nhóm 2
Chi phí rải đều theo thời gian thực hiện kế hoạch ($F_{6.1}$).

$$ C^{Indirect}_i = (F_{2.1} + F_{2.2} + F_{2.3} + F_{2.6}) \times F_{6.1} + F_{2.4} + F_{2.5} $$
*(PM Overhead, Mặt bằng, Tiện ích, QMS, Phối hợp, Đào tạo)*

### 1.3. Cụm Chi phí Logistics & Chuỗi cung ứng - Nhóm 5
Tác động cực mạnh đến luân chuyển vật lý của dự án. 
Phụ thuộc vào **Thời gian chờ ($F_{6.8}$)** và **Thời gian dẫn đầu ($F_{6.11}$)**.

$$ C^{Logistics}_i = F_{5.1} \times (F_{6.1} + F_{6.8}) + F_{5.2} + F_{5.5} + F_{5.6} + F_{5.7} + C^{Stockout}_i $$
*(Lưu kho tính theo thời gian chờ, Phí đặt hàng, Vận tải Quốc tế, Đóng gói, Logistics Ngược)*

### 1.4. Cụm Hợp đồng & Pháp lý - Nhóm 4
Xác định mức đền bù nếu trễ hạn (so với **Late Finish - $F_{6.7}$**) hoặc thưởng nếu xong sớm (so với **Early Finish - $F_{6.5}$**).

$$ C^{Contract}_i = \begin{cases} 
F_{4.1} \times (Finish_i - F_{6.7}) & \text{nếu } Finish_i > F_{6.7} \\
-F_{4.2} \times (F_{6.5} - Finish_i) & \text{nếu } Finish_i < F_{6.5}
\end{cases} $$
$$ + \ F_{4.3} + F_{4.4} + F_{4.5} + F_{4.6} + F_{4.7} $$

### 1.5. Cụm Tác động ESG - Nhóm 12
Hình phạt cho việc xả thải và ảnh hưởng cộng đồng.

$$ C^{ESG}_i = (F_{12.1} \times F_{12.4}) + F_{12.2} + \text{Penalty}(F_{12.3}, F_{12.5}) $$
*(Lượng xả thải $\times$ Thuế Carbon, Phí xử lý rác, Phạt vi phạm cộng đồng)*

### 1.6. Cụm Bù trừ Giá trị (Value Offset) - Nhóm 10
Trừ đi giá trị thực sự tạo ra (Làm giảm hàm chi phí). Phụ thuộc vào **NPV ($F_{10.7}$)** và **Earned Value ($F_{10.1}$)**.

$$ V^{Value}_i = F_{10.1} + F_{10.7} + \text{Bonus}(F_{10.5}) $$

### 1.7. Chi phí Cơ hội & Chìm (Dự án Tổng thể) - Nhóm 3
$$ C^{Opportunity} = F_{3.1} + F_{3.2} + F_{3.4} $$
*(Sunk Cost $F_{3.3}$ bị loại bỏ khỏi hàm tối ưu theo lý thuyết Kinh tế)*

---

## 2. HỆ SỐ RỦI RO (Risk Modifiers) & TRỌNG SỐ ĐỒ THỊ (Graph Weights)

Trong 91 features, có những feature không phải là "Tiền", mà là **Hệ số rủi ro (Risk Multiplier)** và **Đặc trưng Cấu trúc (Structural Embeddings)** để AI điều hướng học tập.

### 2.1. Biến đổi Chi phí kỳ vọng do Rủi ro (Expected Cost Variance) - Nhóm 9 & 11
Chi phí thực tế có thể bùng nổ dựa trên Xác suất rủi ro. Hàm chi phí lúc này nhân với hệ số Rủi ro:

$$ E[C_i] = C_i \times \Big(1 + F_{9.1} + F_{9.5} + F_{11.4} + F_{11.5} + F_{11.7} \Big) $$
*(Xác suất trễ hạn, Rủi ro làm lại, Kiệt sức, Nghỉ việc, An toàn lao động)*

### 2.2. Trọng số Cấu trúc Đồ thị (Dành cho AI GNN) - Nhóm 8
Khi AI phân bổ tài nguyên, nó không nhìn các node một cách bình đẳng. Nó ưu tiên các node có "Tầm quan trọng cấu trúc" lớn. Trọng số ưu tiên (Priority Score) của Node $i$:

$$ Priority_i = \alpha \cdot F_{8.2} + \beta \cdot F_{8.3} + \gamma \cdot F_{8.6} + \delta \cdot F_{9.2} $$
*(Bậc ra - Out-degree, Hệ số trung gian, Số lượng đường đi, Chỉ số găng - Criticality Index)*

---

## 3. HỆ RÀNG BUỘC (Constraints)

Để kịch bản $S$ hợp lệ (Feasible), nó phải vượt qua các bức tường ràng buộc (Hard Constraints) thuộc Nhóm 6 và Nhóm 7:

1. **Ràng buộc Thời gian (Nhóm 6):**
   $$ Start_j \ge Finish_i + WaitTime_{i,j} \quad \text{(Dependency - } F_{8.5}\text{)} $$
   $$ Duration_i = \text{PERT}(F_{6.13}) $$

2. **Ràng buộc Nguồn lực (Nhóm 7):**
   Tại mọi thời điểm $t$, tổng nhu cầu phải nhỏ hơn năng lực cung ứng:
   $$ \sum_{i \in Active(t)} F_{7.1, k} \le Capacity_k $$
   Mức độ khan hiếm ($F_{7.3}$) và Số lượng task tranh chấp ($F_{7.4}$) sẽ quyết định việc AI chọn Execution Mode ($F_{7.6}$) nào để phân bổ.

---

## TỔNG KẾT
Toàn bộ 91 Features đã được "Lắp ghép" vào đúng vị trí:
1. **Feature Tiền tệ (Nhóm 1, 2, 3, 4, 5, 10, 12):** Nằm trực tiếp trong Phương trình Tổng Chi phí.
2. **Feature Rủi ro & Con người (Nhóm 9, 11):** Trở thành Hệ số Khuếch đại (Multiplier) làm phình to chi phí.
3. **Feature Thời gian & Tài nguyên (Nhóm 6, 7):** Trở thành Hệ Ràng Buộc (Constraints).
4. **Feature Đồ thị (Nhóm 8):** Trở thành "Kim chỉ nam" (Priority Weights) cho thuật toán Graph Neural Network (GNN).
