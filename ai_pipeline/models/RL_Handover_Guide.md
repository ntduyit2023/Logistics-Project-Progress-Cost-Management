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

print(node_embeddings.shape) # (Số_lượng_Task, 32) -> Dùng để ra Action cho từng Task
print(graph_embedding.shape) # (1, 32) -> Dùng để dự đoán Value (Actor-Critic)
```

> [!TIP]
> Trong mô hình **Actor-Critic (PPO)**:
> - Dùng `node_embeddings` để đưa vào mạng **Actor** $\to$ Dự đoán xác suất Action (Crash, Fast-track, Delay) cho từng Task.
> - Dùng `graph_embedding` để đưa vào mạng **Critic** $\to$ Đánh giá State Value hiện tại của cả dự án.

---

## 4. Nhiệm vụ CỦA BẠN (Phần chưa code)

Chúng tôi đã lo Khâu 1 & 2. Khâu 3 (PPO Environment) là sân chơi của bạn. Có 2 việc quan trọng bạn PHẢI tự xây dựng:

### A. Tầng 3 (Group-to-Group) & Hàm Mục Tiêu (TGC)
Mạng Nơ-ron của chúng tôi chỉ dừng lại ở Tầng 2 (Feature to Group). 
Hàm **Total Generalized Cost (TGC)** ở Tầng 3 chính là **Reward Function** của bạn. Bạn phải tự viết hàm tính Tổng Chi phí (Direct + Indirect + Phạt trễ hạn) dựa theo file `docs/22-6/hierarchical_3level_evaluation.md`. 
*Mỗi Step, nếu TGC giảm $\to$ Reward dương. Nếu TGC tăng $\to$ Reward âm.*

### B. Môi trường Mô phỏng (Simulator)
Mạng Nơ-ron của chúng tôi tĩnh (Static). Bạn cần viết một vòng lặp (Timeline / Environment Step) để:
1. Nhận Action từ Actor.
2. Dịch chuyển ngày bắt đầu/kết thúc của Task.
3. Check `env_data.global_resources` xem có lố Capacity không.
4. Check Logic (Predecessor) xem có vi phạm đường găng không.
5. Cập nhật lại G3 (Opportunity Cost) và G10 (Earned Value) rồi nhét ngược lại vào `env_data.data.x[60:62]` và `[68:71]`.

Chúc bạn may mắn với Khối PPO! Hệ thống Data & GNN đã vững như bàn thạch để bạn yên tâm "bay nhảy" rồi.
