# Phân tích Chuyên sâu: Tính Thưa thớt (Sparsity) và Cạnh tranh Nội bộ Nhóm (Intra-group Competition)

Khi scale bài toán lên 91 Features và chia thành 12 Nhóm, chúng ta đối mặt với 2 vấn đề lớn trong Học máy (Machine Learning) và Tối ưu hóa (Optimization): **Tính thưa thớt của dữ liệu (Data Sparsity)** và **Sự cạnh tranh (Trade-offs)**.

---

## 1. Tối ưu hóa bằng cách Loại bỏ Nhóm "Trống" (Sparsity & Masking)

Thực tế, **không phải công việc (Task) nào cũng chứa đủ 91 features**. 
*Ví dụ:* Một task "Xin giấy phép hải quan" sẽ không có *Chi phí máy móc* (Nhóm 1), không xả thải (Nhóm 12), và không cần lưu kho (Nhóm 5). 

Nếu chúng ta ép thuật toán AI phải tính toán những con số $0$ này, mô hình sẽ bị "nhiễu" và lãng phí tài nguyên tính toán (Computational Waste).

### Giải pháp Toán học: Ma trận Mặt nạ (Masking Matrix)
Chúng ta đưa vào một ma trận nhị phân $M_{i,g} \in \{0, 1\}$ để "Tắt" (Drop) các nhóm không có dữ liệu cho một task cụ thể.
*   $M_{i,g} = 1$: Task $i$ có chứa dữ liệu thuộc Nhóm $g$.
*   $M_{i,g} = 0$: Task $i$ hoàn toàn không có dữ liệu thuộc Nhóm $g$. Thuật toán sẽ bỏ qua toàn bộ phần tính toán của nhóm này.

**Công thức Hàm Mục tiêu mới (Sử dụng Masking):**
$$ TC_i = \sum_{g=1}^{12} \left( M_{i,g} \cdot CostFunction(Group_g) \right) $$

**Lợi ích:** 
*   Biến ma trận đặc trưng thành dạng **Ma trận thưa (Sparse Matrix)**.
*   Giảm số lượng phép tính của Graph Neural Network (GNN) xuống hàng chục lần. Tăng tốc độ hội tụ của AI.

---

## 2. Sự Cạnh Tranh Giữa Các Feature Trong Cùng Một Nhóm (Intra-group Competition)

Đây là một insight cực kỳ xuất sắc. Trong quá trình Tối ưu hóa, không chỉ các Nhóm cạnh tranh với nhau (ví dụ Nhóm Tiền tệ vs Nhóm Thời gian), mà **ngay bên trong 1 Nhóm, các Features cũng đang "giết" lẫn nhau** để tranh giành nguồn lực.

Dưới đây là phân tích sự cạnh tranh nội bộ (Trade-offs) trong các nhóm quan trọng:

### 2.1. Nhóm 1: Chi phí Trực tiếp (Direct Costs)
*   **Cạnh tranh:** *Nhân công nội bộ ($F_{1.1}$)* ⚔️ *Thuê ngoài ($F_{1.2}$)* ⚔️ *Làm thêm giờ ($F_{1.3}$)*
*   **Phân tích:** Cả 3 feature này đều giải quyết chung một vấn đề: Làm sao để có người làm việc? 
    *   Nếu muốn tiết kiệm tiền, bạn đẩy $F_{1.1}$ lên cao (dùng người nhà). Nhưng nếu thiếu người, bạn bắt buộc phải ép $F_{1.3}$ tăng (bắt người nhà OT).
    *   Nếu không muốn OT vì sợ rủi ro kiệt sức, bạn phải đẩy $F_{1.2}$ (thuê ngoài giá cắt cổ). 
    *   $\rightarrow$ **AI phải tìm điểm cân bằng Nash (Nash Equilibrium) giữa 3 biến số này.**

### 2.2. Nhóm 5: Logistics & Chuỗi cung ứng
*   **Cạnh tranh:** *Phí vận chuyển ($F_{5.5}$)* ⚔️ *Phí lưu kho ($F_{5.1}$)* ⚔️ *Phí thiếu hụt ($F_{5.3}$)*
*   **Phân tích:** 
    *   Nếu bạn gom hàng đợi chở 1 chuyến lớn để tối ưu cước Vận chuyển ($F_{5.5} \downarrow$), hàng sẽ nằm chờ ở cảng $\rightarrow$ Lưu kho tăng vọt ($F_{5.1} \uparrow$).
    *   Nếu bạn sợ lưu kho, bạn chạy xe liên tục dù xe trống $\rightarrow$ Vận chuyển tăng vọt ($F_{5.5} \uparrow$).
    *   Nếu cả xe và kho đều không có hàng $\rightarrow$ Phí đền bù đứt gãy chuỗi cung ứng ($F_{5.3} \uparrow$).

### 2.3. Nhóm 6: Yếu tố Thời gian
*   **Cạnh tranh:** *Thời gian chờ đợi ($F_{6.8}$)* ⚔️ *Thời gian dự trữ ($F_{6.2}$ - Total Float)*
*   **Phân tích:** Thời gian dự trữ (Float) là "tấm đệm" an toàn của task. Thời gian chờ (Wait) là khoảng thời gian chết. Nếu một task bị ép phải chờ quá lâu ($F_{6.8}$ tăng), nó sẽ "ăn lẹm" vào quỹ thời gian dự trữ ($F_{6.2}$ giảm dần về 0). Khi $F_{6.2} = 0$, task đó trở thành Critical Task (Nhiệm vụ găng), và nếu nó trễ thêm 1 giây, toàn bộ dự án sẽ bồi thường hợp đồng.

---

## 3. Ứng dụng Cơ chế Attention (Attention Mechanism) cho Sự cạnh tranh

Để giải quyết sự cạnh tranh ngầm này, mạng Neural của chúng ta sẽ sử dụng kỹ thuật **Intra-group Attention** (Kỹ thuật tương tự ChatGPT). 

Thay vì cộng gộp chi phí một cách tuyến tính, AI sẽ tính ra một "Trọng số tập trung" (Attention Weight - $\alpha$) cho mỗi feature bên trong nhóm $g$, dựa trên bối cảnh của Task.

$$ Cost(Group_g) = \sum_{f \in Group_g} \alpha_f \cdot Value(f) \quad \text{với } \sum \alpha_f = 1 $$

*   Nếu Task đang ở chặng rút đích (Deadline cận kề), $\alpha$ của *Tiền làm thêm giờ* sẽ tự động tăng vọt.
*   Nếu Task đang ở giai đoạn thong thả, $\alpha$ của *Lưu kho* sẽ tăng lên để ép hệ thống đi chậm lại, nhường nguồn lực cho task khác.
