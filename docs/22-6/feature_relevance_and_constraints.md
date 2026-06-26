# Mô Hình Đánh Giá Mức Độ Liên Quan (Relevance) & Ràng Buộc (Constraints)
*Dựa trên Đồ thị Đặc trưng (Feature Relationship Graph)*

Tài liệu này chuẩn hóa **12 Nhóm Đặc trưng (91 Features)**, thiết lập **Công thức Tính Mức độ Liên quan (Relevance/Impact Score)** giữa các Features dựa trên Đồ thị, và tổng hợp **Hệ Ràng Buộc (Constraints)** cho bài toán.

---

## 1. Phân chia 12 Nhóm Đặc trưng (91 Features)

Theo cấu trúc toàn diện, 91 Features được phân loại chính xác thành 12 nhóm sau:

| Nhóm | Tên Nhóm | Số lượng Features | Bản chất trong thuật toán |
| :--- | :--- | :---: | :--- |
| **G1** | Chi phí Trực tiếp (Direct Costs) | 9 | Biến số tài chính cộng dồn (Cost variables) |
| **G2** | Chi phí Gián tiếp (Indirect Costs) | 6 | Biến số tài chính phụ thuộc thời gian (Time-dependent) |
| **G3** | Chi phí Cơ hội & Chìm (Opportunity/Sunk) | 4 | Bù trừ (Offsets) |
| **G4** | Hợp đồng & Pháp lý (Contractual/Legal) | 7 | Phạt/Thưởng dựa trên mốc thời gian (Time bounds) |
| **G5** | Logistics & Chuỗi cung ứng (Logistics/SCM) | 7 | Biến số kho bãi, luân chuyển vật lý |
| **G6** | Yếu tố Thời gian (Temporal Factors) | 13 | Biến trạng thái & Ràng buộc cứng (Hard Constraints) |
| **G7** | Yếu tố Tài nguyên (Resource Factors) | 9 | Ràng buộc sức chứa (Capacity Constraints) |
| **G8** | Cấu trúc Đồ thị (Graph Topology) | 7 | Trọng số điều hướng học tập (Graph Embeddings) |
| **G9** | Rủi ro & Bất định (Risk & Uncertainty) | 10 | Hệ số khuếch đại / Biến ngẫu nhiên (Multipliers) |
| **G10**| Chất lượng & Giá trị (Quality & Value) | 7 | Tham số trừ hao chi phí (Value offset) |
| **G11**| Con người & Tổ chức (Human/Org Factors)| 7 | Hệ số rủi ro tác động năng suất (Productivity modifiers) |
| **G12**| Môi trường & Xã hội (ESG) | 5 | Tiêu chuẩn/Thuế phụ trội (Tax/Penalties) |

---

## 2. Công thức Đánh giá Mức độ Liên quan (Relevance/Impact Score)

Dựa trên cấu trúc mạng lưới của `feature_relationship_graph.html`, không phải Feature nào cũng có tầm quan trọng như nhau. Mức độ liên quan (Relevance Score - $R_i$) của một Feature $i$ đối với toàn bộ dự án được đánh giá bằng **Thuật toán truyền bá trên Đồ thị (Graph Propagation / PageRank-like Metric)**.

### 2.1. Ma trận Trọng số Quan hệ (Adjacency & Weight Matrix)
Gọi $W$ là ma trận quan hệ giữa 91 Features. $w_{i,j}$ là trọng số (sức mạnh) của cạnh nối từ Feature $i$ tác động lên Feature $j$.
*   Nếu $i$ không tác động lên $j$, $w_{i,j} = 0$.
*   Nếu $i$ tác động mạnh lên $j$ (VD: Thời gian chờ $F_{6.8}$ tác động cực mạnh lên Chi phí lưu kho $F_{5.1}$), $w_{i,j}$ sẽ có giá trị cao (từ 0.1 đến 1.0).

### 2.2. Phương trình Tính Mức độ Liên quan (Relevance Score - $R_i$)
Điểm số liên quan của một Feature $i$ (ký hiệu $R_i$) được tính bằng chính bản chất nội tại của nó (Base Weight) cộng với tổng các tác động mà nó nhận được từ các Feature khác (Graph Propagation).

$$ R_i = \alpha \cdot B_i + (1 - \alpha) \cdot \sum_{j \in In(i)} \left( w_{j,i} \cdot R_j \right) $$

**Trong đó:**
*   $R_i$: Điểm mức độ liên quan/quan trọng của Feature $i$ (0 đến 1).
*   $B_i$: Trọng số cơ sở (Base/Intrinsic Weight) của Feature $i$ (VD: Các Feature trực tiếp dính tới Tiền hoặc Deadline sẽ có $B_i$ cao).
*   $w_{j,i}$: Trọng số tác động từ Feature $j$ lên Feature $i$.
*   $\alpha$: Hệ số giảm chấn (Damping Factor), thường chọn 0.15 $\rightarrow$ 0.20, giúp cân bằng giữa giá trị nội tại và tác động từ mạn lưới.
*   $In(i)$: Tập hợp các Features trỏ tới $i$.

**Ý nghĩa:** Công thức này (tương tự PageRank của Google) đảm bảo rằng: Nếu một Feature bị rất nhiều Feature quan trọng khác tác động vào (như một cái "rốn vũ trụ" trong Đồ thị), thì Mức độ Liên quan $R_i$ của nó sẽ cực kỳ lớn. AI sẽ ưu tiên tối ưu các Feature có $R_i$ lớn nhất.

---

## 3. Hệ Ràng Buộc (Constraints) Toàn Diện

Dựa trên 12 Nhóm trên, đây là hệ thống các Ràng buộc (Constraints) mà bất kỳ kịch bản nào AI tạo ra cũng không được phép vi phạm:

### 3.1. Ràng Buộc Thời Gian & Trình Tự (Temporal & Sequential Constraints - Thuộc Nhóm 6 & 8)
*   **Trình tự thi công (Precedence Constraint):** Công việc $j$ chỉ được bắt đầu sau khi tất cả công việc $i$ đứng trước (Predecessors) đã hoàn thành, cộng thêm thời gian chờ bắt buộc (Lag/Wait Time).
    $$ Start_j \ge Finish_i + WaitTime_{i,j} \quad \forall i \in Pred(j) $$
*   **Khung giờ cho phép (Time Windows):** Công việc chỉ được thực hiện trong khung giờ quy định (ví dụ: bốc dỡ ban đêm).
    $$ EarlyStart_i \le Start_i \le LateFinish_i - Duration_i $$
*   **Thời gian thực hiện (Duration Integrity):** 
    $$ Finish_i = Start_i + Duration_i $$

### 3.2. Ràng Buộc Không Gian & Tài Nguyên (Resource & Capacity Constraints - Thuộc Nhóm 7 & 5)
*   **Năng lực Tối đa (Max Capacity):** Tại bất kỳ thời điểm $t$ nào, tổng lượng tài nguyên $k$ (Xe tải, Diện tích kho, Nhân sự) mà các công việc đang chạy (Active Tasks) tiêu thụ KHÔNG được vượt quá giới hạn tối đa.
    $$ \sum_{i \in Active(t)} Demand_{i,k} \le MaxCapacity_k \quad \forall t, \forall k $$
*   **Ràng buộc Không thể chia cắt (Non-preemption):** Một khi xe tải đã bắt đầu chạy hoặc công việc đã bắt đầu, nó không thể bị tạm dừng giữa chừng để làm việc khác.

### 3.3. Ràng Buộc Pháp Lý & Tiêu Chuẩn (Compliance Constraints - Thuộc Nhóm 4 & 12)
*   **Tiêu chuẩn ESG (ESG Compliance Limit):** Tổng lượng phát thải (Carbon Emission) hoặc mức độ ồn ào không được vượt quá mức trần (Cap) quy định bởi pháp luật hoặc Hợp đồng.
    $$ \sum_{i} Emission_i \le CarbonCap_{Project} $$
*   **Giấy phép (Permits Constraint):** Công việc $i$ không được kích hoạt nếu Giấy phép $P$ (thuộc $F_{4.3}$) chưa được chuyển trạng thái "Approved".
