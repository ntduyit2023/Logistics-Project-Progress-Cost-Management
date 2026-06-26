# Đề xuất Lựa chọn Mô hình Học Máy (Model Architecture)
*Dành cho Input 91 Features, Phân cấp 3 Tầng và Dữ liệu Đồ thị*

Với cấu trúc Input cực kỳ đặc thù mà chúng ta đã thiết kế (91 features, có Masking thưa thớt, có Attention nội bộ, và có Ràng buộc cứng), các mô hình truyền thống (như Random Forest, SVM, hay thậm chí Mạng nơ-ron đa lớp FFN bình thường) sẽ **thất bại hoàn toàn**. 

Chúng ta cần một cấu trúc lai ghép (Hybrid Architecture) gồm 3 khối:

---

## 1. Khối Xử lý Đặc trưng (Feature Encoder): Custom Hierarchical Attention

Khối này sẽ "tiêu hóa" vector 91 chiều thô và biến nó thành Vector Đại diện (State Representation) dựa trên chính lý thuyết 3 Tầng của chúng ta.

*   **Lớp 1 (Task Type Embedding):** Đọc tên Task, map vào không gian Vector để lấy ra Trọng số $w$ (Lớp lọc 1).
*   **Lớp 2 (Sparse Masking Layer):** Tự động nhân vector với Mask $m$ (Lớp lọc 2).
*   **Lớp 3 (Intra-group Attention):** Chạy cơ chế Softmax để tìm điểm đại diện cho 9 Nhóm.
*   **Kết quả đầu ra:** 1 Vector nén (Compressed Embedding) đại diện cho trạng thái thực của Task, không còn bị nhiễu bởi các số 0 vô nghĩa.

---

## 2. Khối Học Cấu Trúc (Graph Learning): Mạng GAT (Graph Attention Network)

Bài toán của chúng ta là Lập lịch Dự án (RCPSP), nghĩa là các công việc liên kết với nhau thành một mạng lưới (Đồ thị). Nếu Task A trễ, Task B sẽ trễ theo. 

*   **Mô hình tốt nhất:** **Graph Attention Network (GAT)** hoặc **GraphSAGE**.
*   **Lý do chọn GAT:** GAT có sẵn cơ chế Attention. Nó cho phép một Node (Công việc) "nhìn" sang các Node lân cận (Predecessors / Successors) và tự đánh giá xem Node lân cận nào đang ảnh hưởng đến mình nhiều nhất.
*   **Hoạt động:** GAT sẽ nhận Input từ *Khối 1* gán lên các Node của Đồ thị. Sau nhiều lớp truyền bá (Message Passing), GAT xuất ra một Vector cực mạnh (Node Embedding) chứa cả thông tin nội tại của task LẪN thông tin cấu trúc của cả chuỗi Logistics.

---

## 3. Khối Ra Quyết Định (Decision Agent): Deep Reinforcement Learning (DRL)

Tại sao không dùng Học có giám sát (Supervised Learning)? Vì chúng ta **không có nhãn (Label)**! Chúng ta không có sẵn 100,000 kịch bản lập lịch "hoàn hảo" để dạy máy. Chúng ta chỉ có **Hàm Mục Tiêu (TGC)** và **Hệ Ràng Buộc (Constraints)**.

*   **Mô hình tốt nhất:** **PPO (Proximal Policy Optimization)** — Thuật toán Reinforcement Learning đang làm mưa làm gió (được dùng để train ChatGPT).
*   **Cơ chế hoạt động (Reinforcement Learning):**
    *   **State (Trạng thái):** Lấy từ mạng GAT (biết task nào đang chờ, tài nguyên còn bao nhiêu).
    *   **Action (Hành động):** Quyết định chọn Task nào chạy tiếp, và phân bổ bao nhiêu xe tải/nhân công cho nó.
    *   **Reward (Phần thưởng):** Bằng đúng âm Tổng chi phí (**Reward = -TGC**). 
    *   **Penalty (Phạt Constraint):** Nếu PPO chọn hành động vi phạm Ràng buộc (VD: xếp lịch chồng chéo), môi trường sẽ ném trả **Reward = -1,000,000**. PPO sẽ "đau" và tự học cách né các hành động vi phạm.

---

## TỔNG KẾT KIẾN TRÚC: GAT-PPO (Graph Attention Network + PPO)

Luồng hoạt động của hệ thống AI sẽ là:

```text
[Vector 91 Features thô] + [Đồ thị DSLIB]
         │
         ▼
 ┌────────────────────────────────────────┐
 │ 1. Custom Attention Encoder            │  ← Thực thi 3 tầng, Masking, Task Type
 └────────────────────────────────────────┘
         │ (Vector 9 chiều tinh gọn)
         ▼
 ┌────────────────────────────────────────┐
 │ 2. GAT (Graph Attention Network)       │  ← Đọc cấu trúc đồ thị, truyền bá rủi ro
 └────────────────────────────────────────┘
         │ (Node/Graph Embeddings)
         ▼
 ┌────────────────────────────────────────┐
 │ 3. PPO Agent (Reinforcement Learning)  │  ← Ra quyết định lập lịch
 └────────────────────────────────────────┘
         │
         ▼
[ Lịch trình (Schedule) ] ──(Đánh giá bằng TGC)──> Reward / Penalty
```

### Tại sao Kiến trúc này là "Độc cô cầu bại"?
1. **Chống Overfitting cực tốt:** Nhờ Sparse Masking ở Khối 1, mô hình GAT không bị học những dữ liệu rác (số 0).
2. **Giải quyết triệt để Synergy:** Hàm Reward (TGC) chứa phần Tích chéo phi tuyến (Cross-product), ép PPO phải học được những chiến thuật cực khó (VD: thà chịu phạt tiền Hợp đồng còn hơn dồn xe tải gây bùng nổ rủi ro Xả thải).
3. **Tuân thủ Constraints 100%:** Cơ chế Masking Action (chặn hành động sai trái) kết hợp Penalty hủy diệt ép AI không bao giờ đưa ra lịch trình lỗi.
