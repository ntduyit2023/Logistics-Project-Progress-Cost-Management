# PHÂN TÍCH CHUYÊN SÂU & HƯỚNG DẪN TRIỂN KHAI CƠ CHẾ LOẠI HÌNH DỰ ÁN (PROJECT TYPE)
==================================================================================

Báo cáo này cung cấp giải pháp thiết kế chi tiết ở mức mã nguồn và sơ đồ dữ liệu để tích hợp cơ chế Phân loại dự án (IT, Business, Logistics,...) nhằm đảm bảo tính đồng bộ hoàn toàn với workflow và pipeline chính hiện có của hệ thống GLPO.

---

## 📁 1. CƠ CẤU THÔNG TIN ĐẦU VÀO (DATA INGESTION UPDATE)

Để hệ thống nhận biết loại hình dự án, chúng ta sử dụng một tệp siêu dữ liệu `metadata.json` đặt bên trong thư mục của từng dự án (ví dụ: `ai_pipeline/data/processed/C2019-16/metadata.json`):
```json
{
  "project_id": "C2019-16",
  "project_type": "IT"
}
```

### Cách cập nhật trong [data_loader.py](file:///c:/CNTT/KY8-2026/Logistics-Project-Progress-Cost-Management/ai_pipeline/models/data_loader.py):
Chúng ta đọc tệp này trong constructor của `GlPoProjectGraph`:
```python
# Cập nhật trong GlPoProjectGraph.__init__
import json

metadata_path = os.path.join(project_dir, 'metadata.json')
if os.path.exists(metadata_path):
    with open(metadata_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
        self.project_type = meta.get('project_type', 'Logistics')
else:
    self.project_type = 'Logistics'

# Lưu project_type vào PyG Data để truyền đi trong mô hình
self.data.project_type = self.project_type
```

---

## 🛠️ 2. PHƯƠNG ÁN 1: DÙNG CHUNG GNN BACKBONE + DYNAMIC TGC & HAE
**Triết lý:** GAT và DAGNN được chia sẻ chung trọng số để học "vật lý đồ thị" ( message passing, phân bổ đường găng, lan truyền trễ). Các tầng Tri thức miền (Domain-specific Knowledge) gồm **Tầng 1 (HAE)** và **Tầng 3 (TGC)** sẽ tải động ma trận tương tác chi phí tương ứng với loại hình dự án.

```
                    ┌────────────────────────────┐
                    │       data.x (72-D)        │
                    └─────────────┬──────────────┘
                                  │
                                  ▼  (Nhận project_type từ PyG Data)
                    ┌────────────────────────────┐
                    │    TẦNG 1: Dynamic HAE     │ <-- Tải ma trận F-G (Feature to Group) tương ứng
                    └─────────────┬──────────────┘
                                  │ S'_g (13-D)
                                  ▼
                    ┌────────────────────────────┐
                    │   Shared GAT & DAGNN       │ <-- Dùng chung bộ mã hóa cấu trúc & thời gian
                    └─────────────┬──────────────┘
                                  │ H_final (32-D)
                                  ▼
                    ┌────────────────────────────┐
                    │    TẦNG 3: Dynamic TGC     │ <-- Tải ma trận tương tác nhóm γ tương ứng
                    └────────────────────────────┘
```

### Bước 1: Sửa đổi [feature_interaction_matrix.py](file:///c:/CNTT/KY8-2026/Logistics-Project-Progress-Cost-Management/ai_pipeline/models/feature_interaction_matrix.py)
Định nghĩa các ma trận tương tác chi phí riêng biệt cho các miền dự án khác nhau:
```python
def _build_gamma_matrix_logistics() -> np.ndarray:
    # Ma trận đối xứng tương tự như hiện tại (mặc định)
    gamma = np.zeros((13, 13), dtype=np.float32)
    gamma[0, 2] = gamma[2, 0] = 0.8  # Hub 📈 G2
    gamma[1, 7] = gamma[7, 1] = 0.8  # G1 📈 G7
    return gamma

def _build_gamma_matrix_it() -> np.ndarray:
    gamma = np.zeros((13, 13), dtype=np.float32)
    # Luật IT: Lương nhân sự (G1) và Quản lý chất lượng/Rework (G9) có tương tác cực cao
    gamma[1, 9] = gamma[9, 1] = 0.9  # G1 📈 G9 (Nhân sự & Rủi ro lỗi)
    gamma[0, 9] = gamma[9, 0] = 0.8  # Thời gian dự án kéo dài làm tăng mạnh rủi ro tích hợp
    return gamma

def get_gamma_matrix(project_type: str) -> np.ndarray:
    if project_type.upper() == "IT":
        return _build_gamma_matrix_it()
    return _build_gamma_matrix_logistics()
```

### Bước 2: Sửa đổi [tgc_layer3.py](file:///c:/CNTT/KY8-2026/Logistics-Project-Progress-Cost-Management/ai_pipeline/models/tgc_layer3.py)
Cập nhật lớp `TGCLayer3` để nhận ma trận $\gamma$ động:
```python
class TGCLayer3(nn.Module):
    def __init__(self, project_type: str = "Logistics", learnable_beta: bool = True, learnable_gamma: bool = False):
        super(TGCLayer3, self).__init__()
        self.project_type = project_type
        
        # Tải động ma trận gamma dựa trên loại dự án
        from feature_interaction_matrix import get_gamma_matrix
        gamma_np = get_gamma_matrix(project_type)
        
        self.interaction_matrix = nn.Parameter(torch.tensor(gamma_np, dtype=torch.float), requires_grad=learnable_gamma)
        ...
```

### Bước 3: Sửa đổi [sequential_glpo_model.py](file:///c:/CNTT/KY8-2026/Logistics-Project-Progress-Cost-Management/ai_pipeline/models/sequential_glpo_model.py)
Cập nhật forward pass để truyền `project_type` từ `data` xuống các tầng con:
```python
def forward(self, data) -> Dict[str, torch.Tensor]:
    x, edge_index = data.x, data.edge_index
    project_type = getattr(data, 'project_type', 'Logistics')
    
    # Khởi tạo hoặc cập nhật động ma trận tương tác trong tgc theo project_type
    self.tgc.update_project_type(project_type) 
    self.encoder.update_project_type(project_type)
    
    ...
```

---

## 🛡️ 3. PHƯƠNG ÁN 2: TÁCH BIỆT HOÀN TOÀN CHECKPOINTS (SPECIALIST MODELS)
**Triết lý:** Giữ nguyên 100% mã nguồn của các lớp mô hình. Sự khác biệt chỉ nằm ở tập dữ liệu huấn luyện và file lưu trọng số. Pipeline sẽ tự động nạp đúng tệp checkpoint phù hợp.

```
                    ┌────────────────────────────┐
                    │      data.project_type     │
                    └─────────────┬──────────────┘
                                  │
                  ┌───────────────┼───────────────┐
                  ▼ (IT)          ▼ (Logistics)   ▼ (Business)
             ┌──────────┐    ┌──────────┐    ┌──────────┐
             │ gat_IT   │    │ gat_Log  │    │ gat_Biz  │
             │ dagnn_IT │    │ dagnn_Log│    │ dagnn_Biz│
             └────┬─────┘    └────┬─────┘    └────┬─────┘
                  └───────────────┼───────────────┘
                                  ▼
                    ┌────────────────────────────┐
                    │  SequentialGLPOModel Load  │
                    └────────────────────────────┘
```

### Cách cập nhật trong [run_main.py](file:///c:/CNTT/KY8-2026/Logistics-Project-Progress-Cost-Management/ai_pipeline/src/pipeline_runners/run_main.py) và [project_state_manager.py](file:///c:/CNTT/KY8-2026/Logistics-Project-Progress-Cost-Management/ai_pipeline/src/state/project_state_manager.py):
Cập nhật hàm nạp weights để sinh đường dẫn động:
```python
# Lấy loại hình dự án từ đồ thị đầu vào
project_type = getattr(project_graph, 'project_type', 'Logistics').lower()

gat_filename = f"gat_pretrained_{project_type}.pth"
dagnn_filename = f"dagnn_pretrained_{project_type}.pth"

gat_path = os.path.join(checkpoint_dir, gat_filename)
dagnn_path = os.path.join(checkpoint_dir, dagnn_filename)

# Tải dự phòng nếu file chuyên hóa không tồn tại
if not os.path.exists(gat_path):
    print(f"⚠️ Không tìm thấy model IT, dùng model mặc định: gat_pretrained.pth")
    gat_path = os.path.join(checkpoint_dir, "gat_pretrained.pth")
    dagnn_path = os.path.join(checkpoint_dir, "dagnn_pretrained.pth")

# Nạp vào mô hình chính
model.load_state_dict(torch.load(dagnn_path, map_location=device), strict=False)
```

---

## 📈 4. BẢNG SO SÁNH PHƯƠNG ÁN & ĐỀ XUẤT LỘ TRÌNH

| Tiêu chí so sánh | Phương án 1 (GAT/DAGNN Chung + Dynamic TGC) | Phương án 2 (Tách Checkpoints Độc lập) | Phương án 3 (Conditional GNN - FiLM) |
| :--- | :---: | :---: | :---: |
| **Độ khó lập trình** | Thấp | **Rất Thấp (Không đổi model)** | Rất Cao (Thay đổi cấu trúc toán học) |
| **Độ phức tạp huấn luyện** | Trung bình (Train chung 1 model) | Thấp (Train riêng từng tập) | Rất cao (Học đa miền đồng thời) |
| **Khả năng tổng quát hóa** | Cao (Backbone học được pattern chung) | Trung bình (Chỉ tốt trên miền của nó) | **Rất Cao (AI tự thích ứng đầu vào)** |
| **Thời gian triển khai** | 1 - 2 ngày | **2 - 4 giờ** | 1 - 2 tuần |

### 🛠️ Lộ trình triển khai khuyến nghị:
1. **Giai đoạn 1 (Ngắn hạn - Triển khai trong ngày):** Áp dụng **Phương án 2 (Tách Checkpoints)**. Gom dữ liệu dự án IT để chạy tiền huấn luyện SSL riêng và nạp checkpoint động. Giải pháp này giúp kiểm chứng nhanh tính hiệu quả của các mô hình chuyên biệt mà không rủi ro về mặt phần mềm.
2. **Giai đoạn 2 (Dài hạn - Nâng cấp tối ưu):** Triển khai kết hợp **Phương án 1**. Xây dựng ma trận tương tác chi phí $\gamma$ riêng cho ngành IT để điều chỉnh hàm phạt TGC và Reward của PPO Agent phù hợp với cấu trúc tài chính phần mềm.
