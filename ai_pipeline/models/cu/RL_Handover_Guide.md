# Hướng Dẫn Bàn Giao: Khối Neural Network (Cho Nhóm RL / PPO)

> [!NOTE]
> Tài liệu này được viết riêng cho Kỹ sư Reinforcement Learning (Nhóm phát triển Khối 3 - PPO Environment).
> Chức năng của tài liệu là hướng dẫn cách gọi API để lấy dữ liệu Đồ thị (Graph Data), thông tin Tài nguyên (Resources), Lịch trình (Agenda), và cách chạy Mạng Nơ-ron (GAT).

---

## 1. Tổng Quan Kiến Trúc (Ranh Giới)

Hệ thống đã hoàn thiện **Khối 1 (Xử lý Dữ liệu thô)** và **Khối 2 (Mạng Nơ-ron GAT)**. 
Nhiệm vụ của Khối 1 & 2 là chuẩn bị **State Representation (Trạng thái)** cho thuật toán PPO của bạn.

Chúng tôi đã thiết kế sẵn một lớp API bọc ngoài (Wrapper) tên là `ProjectEnvironmentWrapper`. Bạn **không cần** phải tự đọc file CSV hay xử lý tính toán gì ở khâu nạp dữ liệu. Chỉ cần gọi Wrapper này, mọi thứ sẽ được dâng tận miệng.

---

## 2. Hướng Dẫn Nạp Dữ Liệu (The Environment Wrapper)

Trong môi trường PPO của bạn (ví dụ: ở hàm `__init__` của class `LogisticsEnv`), bạn chỉ cần import và gọi Wrapper như sau:

```python
import sys
# Trỏ đường dẫn tới thư mục models nếu cần
sys.path.append(r"E:\University\Year 3-3\DA3\ai_pipeline\models")

from data_loader import ProjectEnvironmentWrapper

# Khởi tạo Môi trường cho 1 dự án cụ thể
processed_dir = r"E:\University\Year 3-3\DA3\ai_pipeline\data\processed"
env_data = ProjectEnvironmentWrapper(processed_dir=processed_dir, project_id="C2012-08")

# In ra tóm tắt để kiểm tra
env_data.summary()
```

### 3 "Bảo bối" bạn nhận được từ Wrapper này:

#### A. `env_data.data` (Đồ thị PyTorch Geometric)
Đây là cấu trúc Đồ thị chứa toán bộ thông tin của dự án, sẵn sàng để nạp vào Mạng GAT.
*   `env_data.data.x`: Tensor `[Số_Task, 72]`. Mỗi hàng là 72 Features chuẩn PMBOK (Chi phí, Rủi ro, Thời gian...).
*   `env_data.data.edge_index`: Tensor `[2, Số_Cạnh]`. Bản đồ liên kết các Task (Predecessor -> Successor).
*   `env_data.data.u`: Tensor `[1, 3]`. Vector toàn cục chứa `[hours_per_day, days_per_week, total_holidays]`.

#### B. `env_data.global_resources` (Giới hạn Tài nguyên)
Để bạn check xem AI có vi phạm luật (Hard Constraints) hay không.
```python
print(env_data.global_resources)
# Output ví dụ:
# {
#   'R_001': {'name': 'Cần cẩu', 'capacity': 2.0, 'cost_use': 1500.0, 'cost_unit': 0.0},
#   'R_002': {'name': 'Kỹ sư', 'capacity': 10.0, 'cost_use': 0.0, 'cost_unit': 50.0}
# }
```
> [!IMPORTANT]
> Khi PPO Action quyết định cho 2 Task chạy song song, bạn phải tự cộng dồn Demand (từ `data.x[37]`) và so sánh với `capacity` ở biến này. Nếu vượt quá $\to$ Bạn phải code hàm phạt (Penalty) trong Reward.

#### C. `env_data.agenda` (Lịch trình)
Dùng để tính thời gian thực tế trong quá trình mô phỏng (Môi trường của bạn).
```python
print(env_data.agenda['hours_per_day'])  # Ví dụ: 8.0
print(env_data.agenda['days_per_week'])  # Ví dụ: 5.0
```

---

## 3. Hướng Dẫn Chạy Mạng Nơ-ron (GAT Model)

Mạng Nơ-ron đã được chúng tôi thiết kế sẵn dựa trên **Cơ chế Attention Phân cấp (Hierarchical Attention)**. Nhiệm vụ của nó là nén 72 Features thành một Vector Tinh Hoa (Embedding).

```python
import torch
from gat_model import LogisticsGATModel

# Khởi tạo Mô hình (Chỉ làm 1 lần)
model = LogisticsGATModel(feature_dim=72, hidden_dim=64, num_groups=13, out_dim=32, heads=4)

# Nếu bạn đang test thì nhớ set eval mode, nếu train PPO thì để train mode
model.eval() 

with torch.no_grad():
    # Nạp Đồ thị vào não AI
    node_embeddings, graph_embedding = model(env_data.data)

print(node_embeddings.shape) # (Số_lượng_Task, 32) 
print(graph_embedding.shape) # (1, 32) 
```

### Chi Tiết Cấu Trúc Outputs (Đầu Ra)

Sau khi truyền Đồ thị qua `LogisticsGATModel`, bạn sẽ nhận được 2 Output cốt lõi, là nền tảng (State) để đưa vào tác tử PPO (Actor-Critic):

#### Output 1: `node_embeddings` (Kích thước: `[Số_Task, 32]`)
- **Bản chất:** Là các Vector đại diện cho từng công việc (Task). Kích thước mặc định là `32` (có thể tùy chỉnh qua `out_dim`).
- **Ý nghĩa học được:** Chứa thông tin đã được "nhúng" (embedded) về chi phí, rủi ro, và mức độ quan trọng (criticality) của chính Task đó, CỘNG VỚI thông tin lan truyền từ các Task lân cận.
- **Cách dùng (Actor Network):** 
  - Đưa `node_embeddings` này qua mạng MLP (Multi-Layer Perceptron) của Actor để xuất ra **Xác suất Hành động (Action Probabilities)** cho TỪNG TASK độc lập.
  - Ví dụ Action Space (Discrete): `0` = Giữ nguyên (Do Nothing), `1` = Rút ngắn thời gian/Làm thêm giờ (Crashing), `2` = Làm song song (Fast-tracking).

#### Output 2: `graph_embedding` (Kích thước: `[1, 32]`)
- **Bản chất:** Là Vector đại diện cho TOÀN BỘ DỰ ÁN. Được tạo ra bằng cơ chế Global Mean Pool, tổng hợp tinh hoa từ tất cả các `node_embeddings`.
- **Ý nghĩa học được:** Chứa "sức khỏe" tổng thể của dự án hiện tại (tổng chi phí đang cháy, tiến độ đang trễ hay sớm, tổng rủi ro...).
- **Cách dùng (Critic Network):**
  - Đưa `graph_embedding` này qua mạng MLP của Critic để dự đoán **Giá trị Trạng thái (State Value / V-value)** duy nhất (1 con số Scalar).
  - Giá trị này được dùng để tính Advantage $\to$ Cập nhật trọng số của PPO.

> [!TIP]
> Kiến trúc của bạn sẽ trông như thế này:
> - **Actor(node_embeddings)** $\to$ `Action_Logits [Số_Task, Số_Action]`
> - **Critic(graph_embedding)** $\to$ `State_Value [1]`

---

## 4. Nhiệm vụ CỦA BẠN (Phần chưa code)

Chúng tôi đã lo Khâu 1 & 2. Khâu 3 (PPO Environment) là sân chơi của bạn. Có 2 việc quan trọng bạn PHẢI tự xây dựng:

### A. Tầng 3 (Group-to-Group) & Hàm Mục Tiêu (TGC)
Mạng Nơ-ron của chúng tôi chỉ dừng lại ở Tầng 2 (Feature to Group). 
Hàm **Total Generalized Cost (TGC)** ở Tầng 3 chính là **Reward Function** của bạn. Bạn phải tự viết hàm tính Tổng Chi phí (Direct + Indirect + Phạt trễ hạn) dựa theo file `docs/22-6/hierarchical_3level_evaluation.md`. 
*Mỗi Step, nếu TGC giảm $\to$ Reward dương. Nếu TGC tăng $\to$ Reward âm.*

### B. Môi trường Mô phỏng (Simulator) & Dynamic State
Mạng Nơ-ron (GAT) của chúng tôi về bản chất là "Tĩnh" (Static) tại mỗi bước. Để AI hiểu được diễn biến thời gian thực, bạn cần viết một vòng lặp (Environment Step) để:
1. Nhận Action từ Actor.
2. Dịch chuyển ngày bắt đầu/kết thúc của Task, trừ lùi thời gian.
3. Check `env_data.global_resources` xem có lố Capacity không.
4. Check Logic (Predecessor) xem có vi phạm đường găng không.
5. **Cập nhật Dynamic State:** Bạn phải tính toán lại G3 (Opportunity Cost), G10 (Earned Value) và các thông số tiến độ... sau đó NHÉT NGƯỢC LẠI vào `env_data.data.x`. Chỉ khi `data.x` thay đổi, lần forward tiếp theo GAT mới nhả ra Embedding mới!

### C. Action Masking (Mặt nạ hành động)
Mạng Actor có thể thỉnh thoảng sẽ "ngốc nghếch" khi dự đoán ra hành động: *Rút ngắn thời gian (Crashing) cho một công việc ĐÃ HOÀN THÀNH*, hoặc *Bắt đầu một công việc khi CÔNG VIỆC TRƯỚC ĐÓ CHƯA XONG*.
$\to$ Bắt buộc bạn phải tự code một mảng `action_mask` (Boolean True/False array) trong hàm `step()` để đánh dấu các hành động bất hợp lý, và lọc bỏ chúng (set probability = 0) trước khi Agent ra quyết định cuối cùng.

Chúc bạn may mắn với Khối PPO! Hệ thống Data & GNN đã vững như bàn thạch để bạn yên tâm "bay nhảy" rồi.
