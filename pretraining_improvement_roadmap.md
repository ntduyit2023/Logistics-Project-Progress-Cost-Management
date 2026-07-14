# ROADMAP CẢI TIẾN: TIỀN HUẤN LUYỆN TỰ GIÁM SÁT ĐA NHIỆM (GAT & DAGNN)

---

## THẢO LUẬN & PHÂN TÍCH 4 VẤN ĐỀ CỐT LÕI

---

## VẤN ĐỀ 1: THỨ TỰ HUẤN LUYỆN — GAT TRƯỚC HAY DAGNN TRƯỚC?

### Phân tích
Hiện tại `pretrain_all()` (dòng 726–779, `unsupervised_pretrainer.py`) chạy theo thứ tự **GAT → DAGNN**, đây là **lựa chọn đúng** về mặt kiến trúc và không cần đảo lại.

**Lý do GAT phải đi trước:**
- DAGNN nhận đầu vào là vector nhúng `h` đầu ra của GAT (`h_dagnn = model.dagnn(h, edge_index)`).
- Nếu DAGNN được huấn luyện trước khi GAT hội tụ, nó đang học lan truyền thời gian trên một không gian nhúng `h` hoàn toàn nhiễu ngẫu nhiên → gradient của DAGNN sẽ sai hướng từ đầu.
- GAT (GAE + DGI) học trước giúp `h` mang ý nghĩa cấu trúc thực sự (liên kết cạnh, ngữ cảnh toàn cục), cung cấp bệ đỡ ổn định cho DAGNN học lan truyền thời gian.

**Cải tiến nhỏ:** Thêm bước **Warm Connectivity Check** — kiểm tra AUC-ROC của GAT đạt ngưỡng tối thiểu (vd: AUC ≥ 0.70) trước khi chuyển sang huấn luyện DAGNN. Nếu chưa đạt, tự động gia hạn thêm epoch cho GAT.

```python
# Pseudo-code Warm Connectivity Check
if gae_history['auc_scores'][-1] < 0.70:
    extra_gae = self.pretrain_gae(data, epochs=50, ...)  # fallback thêm epoch
```

**Kết luận:** ✅ Giữ nguyên thứ tự GAT → DAGNN. Chỉ bổ sung cơ chế kiểm tra chất lượng GAT trước khi bàn giao.

---

## VẤN ĐỀ 2: KHỐI NHIỆM VỤ TỰ GIÁM SÁT DAGNN

### 2a. Tỷ lệ Mask (mask_ratio = 0.15) — Cứng hay Thích ứng?

**Vấn đề của cố định 15%:**
- Dự án nhỏ (10–15 task): Mask 15% = chỉ 1–2 nút bị che → tín hiệu học quá yếu, mô hình không bị ép học từ ngữ cảnh.
- Dự án lớn (50+ task): Mask 15% = 7–8 nút → quá nhiều thông tin bị che cùng lúc, gây nhiễu gradient.

**Giải pháp: Adaptive Mask Ratio dựa trên số nút**

Sử dụng hàm tuyến tính có trần/sàn để điều chỉnh tỷ lệ mask theo quy mô đồ thị:

| Số nút N | mask_ratio đề xuất |
|:---:|:---:|
| N ≤ 15   | 0.30 (30%) — ép học mạnh hơn |
| 15 < N ≤ 30 | 0.20 |
| N > 30 | 0.12 |

Công thức tổng quát:
```
mask_ratio = clip(0.30 - 0.006 * N, min=0.10, max=0.35)
```

Ngoài ra, bổ sung **Span Masking** (che liên tiếp 2–3 nút liền kề theo thứ tự tô-pô) thay vì mask ngẫu nhiên hoàn toàn — cơ chế này tương đương BERT whole-word masking, ép mô hình học chuỗi phụ thuộc thời gian.

---

### 2b. Thay thế Topological Distance Prediction

**Vấn đề với Topo Distance (BFS):**
- Khoảng cách BFS `D_topo(u, v)` là một đại lượng toàn cục của đồ thị, không phản ánh trực tiếp ngữ nghĩa thời gian lập lịch (một cặp nút có khoảng cách 3 hop có thể có Total Float hoàn toàn khác nhau).
- MSE trên khoảng cách nguyên (integer values) bão hòa sớm và không cung cấp gradient rõ ràng cho các nút nằm ở cuối chuỗi tô-pô.

**Nhiệm vụ thay thế đề xuất: Predecessor Chain Reconstruction (PCR)**

Ý tưởng: Với mỗi nút `v`, ép DAGNN dự đoán **tổng thời lượng tích lũy trên đường găng đến nút v** (`ES[v]` theo định nghĩa CPM tĩnh). Đây là bài toán "hồi quy thứ tự tô-pô" phù hợp hơn với bản chất lan truyền có hướng của DAGNN.

Tại sao PCR tốt hơn BFS Distance:
- **Liên kết trực tiếp với CPM:** ES[v] = max(EF[predecessors(v)]) — đây chính là công thức Forward Pass CPM. Huấn luyện PCR = ép DAGNN học forward pass CPM từ góc nhìn từng nút.
- **Không bị bão hòa:** Giá trị ES[v] là liên tục, biên độ rộng, gradient thông suốt.
- **Không cần BFS toàn đồ thị:** Chỉ cần tính từ dữ liệu CPM đã có sẵn (target đã được tính trong `_compute_cpm_targets()`).

**Nhiệm vụ thay thế khác (tùy chọn 2): Critical Subgraph Contrastive Learning**
- Tạo mẫu âm (negative): Xáo trộn thứ tự kết nối cạnh để tạo DAG ngẫu nhiên.
- Mẫu dương: DAG gốc.
- Ép DAGNN học phân biệt cấu trúc DAG hợp lệ vs DAG xáo trộn thông qua InfoNCE Loss.

---

## VẤN ĐỀ 3: BỔ SUNG NHIỆM VỤ CHO GAT — RÀNG BUỘC STRUCTURAL RELATIONSHIP

**Vấn đề hiện tại:** GAT chỉ học ở cấp độ cạnh (GAE = edge reconstruction) và cấp độ toàn đồ thị (DGI = global context). Không có nhiệm vụ học tương quan cục bộ theo vai trò vị trí của nút trong đồ thị.

**Nhiệm vụ đề xuất: Critical Path Node Triplet Loss (CPNT)**

**Cơ chế:** Dựa trên kết quả CPM tĩnh, xây dựng bộ ba nút (Anchor, Positive, Negative):
- **Anchor (a):** Một nút bất kỳ trên đường găng (IsCritical = 1).
- **Positive (p):** Một nút găng khác nằm cùng đoạn đường găng với `a` (kề nhau hoặc cách nhau 1 hop).
- **Negative (n):** Một nút không găng (Total Float > 0).

**Mục tiêu (Triplet Margin Loss):**
```
L_CPNT = max(0, ||z_a - z_p||² - ||z_a - z_n||² + margin)
```

Với `margin = 0.5` và `z` là GAT embedding. Nhiệm vụ này ép GAT học một không gian nhúng trong đó **các nút găng tự nhiên xếp gần nhau**, còn các nút không găng bị đẩy ra xa — phù hợp hoàn toàn với vai trò của GAT là học biểu diễn cấu trúc quan trọng.

**Cập nhật hàm loss GAT:**
```
L_GAT = λ_gae * L_GAE + λ_dgi * L_DGI + λ_cpnt * L_CPNT
```
Trọng số đề xuất: `λ_gae = 0.6`, `λ_dgi = 0.25`, `λ_cpnt = 0.15`.

> [!NOTE]
> CPNT cần dữ liệu CPM (IsCritical flag) — dữ liệu này có thể được tính trước bằng `_compute_cpm_targets()` và truyền vào hàm `pretrain_gae()` dưới dạng tham số bổ sung. Điều này không ảnh hưởng tính tự giám sát vì nhãn vẫn được sinh tự động.

---

## VẤN ĐỀ 4: CƠ CHẾ KIỂM SOÁT EPOCH — EARLY STOPPING & ADAPTIVE SCHEDULER

### 4a. Thay thế Epoch Cứng bằng Smart Training Controller

**Nguyên tắc thiết kế:**

| Cơ chế | Vai trò |
|:---|:---|
| **Early Stopping** | Dừng khi loss không cải thiện sau N patience epochs |
| **Best Model Snapshot** | Lưu checkpoint tốt nhất (không phải checkpoint cuối) |
| **Cosine LR Warmup + Decay** | Tránh learning rate quá lớn ở đầu và quá nhỏ ở cuối |
| **Epoch Budget (Max Epochs)** | Giới hạn trần để tránh chạy vô hạn |
| **Quality Gate** | Kiểm tra ngưỡng chất lượng tối thiểu trước khi dừng |

**Cấu hình đề xuất cho GAT:**
```python
# Training config GAT
max_epochs = 300         # Trần tối đa (tăng từ 100)
patience = 30            # Early stop nếu loss không giảm sau 30 epoch
min_improvement = 1e-4   # Ngưỡng cải thiện tối thiểu
quality_gate_auc = 0.72  # AUC-ROC tối thiểu để chấp nhận kết quả
warmup_epochs = 10       # Warmup LR tuyến tính từ lr/10 → lr
```

**Cấu hình đề xuất cho DAGNN:**
```python
# Training config DAGNN
max_epochs = 500         # Trần tối đa (tăng từ 150 để có đủ epoch cải thiện R²)
patience = 40
min_improvement = 1e-4
quality_gate_r2 = 0.80   # R² tối thiểu phải đạt
quality_gate_crit_acc = 0.90  # Critical accuracy tối thiểu
warmup_epochs = 15
```

---

### 4b. Vấn đề R² = 0.55 — Tại sao thấp dù Accuracy = 94.60%?

**Phân tích nguyên nhân:**

R² đo khả năng mô hình giải thích **biến thiên** của biến mục tiêu. Khi R² thấp trong khi Accuracy của nhãn nhị phân `IsCritical` cao:
- Mô hình **giỏi phân loại nhị phân** (Găng / Không Găng) nhờ BCE Loss với `weight = 2.0`.
- Nhưng **kém dự đoán chính xác giá trị liên tục** (ES, EF, LS, LF, TF) vì mô hình chưa đủ sâu để mô tả biến động giá trị tuyệt đối.

**Giải pháp để đưa R² ≥ 0.80:**

1. **Tăng trọng số CPM loss** cho các mục tiêu liên tục: Thay đổi loss weighting trong `CPMLoss` — tăng trọng số MSE cho ES, EF từ 1.0 lên 3.0, giảm nhẹ trọng số của BCE (IsCritical).

2. **Huấn luyện Progressive Curriculum:** 
   - **Giai đoạn 1 (epoch 1–100):** Chỉ tối ưu CPM Loss (tắt Mask và PCR).
   - **Giai đoạn 2 (epoch 101–300):** Bật Mask Duration Loss.
   - **Giai đoạn 3 (epoch 301–500):** Bật toàn bộ 3 nhiệm vụ.
   
   Lý do: Việc tối ưu đồng thời từ đầu gây nhiễu gradient, mô hình học nhiệm vụ dễ (phân loại) sớm và không có đủ tín hiệu để cải thiện dự đoán liên tục.

3. **Thêm Residual Connection trong CPM Head:** Prediction Head hiện chỉ là Linear → LeakyReLU → Linear. Thêm 1 lớp ẩn và batch normalization để tăng năng lực biểu diễn.

4. **Chuẩn hóa mục tiêu Z-score thay vì Min-Max:** Hiện tại ES, EF, LS, LF được chuẩn hóa bằng `/ makespan_norm`. Với các dự án có makespan chênh lệch lớn (200 giờ vs 2000 giờ), phân phối mục tiêu bị lệch. Z-score chuẩn hóa tốt hơn.

---

## ROADMAP HÀNH ĐỘNG (ƯU TIÊN THEO MỨC ĐỘ TÁC ĐỘNG)

### PHASE 1 — Cải tiến ngay, không cần re-architecture (Tuần 1)

| # | Thay đổi | File cần sửa | Tác động dự kiến |
|:---:|:---|:---|:---|
| P1.1 | Thêm **Adaptive Mask Ratio** theo quy mô nút | `pretraining_utils.py` → `mask_node_duration()` | Cải thiện chất lượng gradient Mask task |
| P1.2 | Thêm **Early Stopping + Best Snapshot** cho cả GAT và DAGNN | `unsupervised_pretrainer.py` → `pretrain_gae()` & `pretrain_cpm_self_supervised()` | Tránh over/under-training, tiết kiệm compute |
| P1.3 | Thêm **Cosine LR Warmup + Decay** (thay Adam thuần) | `unsupervised_pretrainer.py` → phần khởi tạo optimizer | Hội tụ mượt mà hơn |
| P1.4 | Tăng **max_epochs GAT = 300, DAGNN = 500** kèm patience | `unsupervised_pretrainer.py` → `pretrain_all()` defaults | Cho mô hình đủ thời gian cải thiện |

### PHASE 2 — Cải tiến cấu trúc nhiệm vụ (Tuần 2)

| # | Thay đổi | File cần sửa | Tác động dự kiến |
|:---:|:---|:---|:---|
| P2.1 | **Thay Topo Distance → Predecessor Chain Reconstruction (PCR)** | `unsupervised_pretrainer.py`, `pretraining_losses.py` | Loại bỏ nhiệm vụ không phù hợp, gradient sạch hơn |
| P2.2 | **Bổ sung CPNT Triplet Loss cho GAT** | `unsupervised_pretrainer.py` → `pretrain_gae()`, `pretraining_losses.py` | GAT học không gian nhúng theo vai trò găng |
| P2.3 | **Progressive Curriculum cho DAGNN** (3 giai đoạn) | `unsupervised_pretrainer.py` → `pretrain_cpm_self_supervised()` | R² tăng lên ≥ 0.80 |

### PHASE 3 — Tinh chỉnh Loss & Architecture (Tuần 3)

| # | Thay đổi | File cần sửa | Tác động dự kiến |
|:---:|:---|:---|:---|
| P3.1 | Điều chỉnh loss weight CPM: tăng trọng số MSE cho ES, EF lên 3.0 | `pretraining_losses.py` → `CPMLoss` | R² ES cải thiện trực tiếp |
| P3.2 | Thay Z-score cho chuẩn hóa mục tiêu ES, EF, LS, LF | `unsupervised_pretrainer.py` → `_compute_cpm_targets()` | Giảm lệch phân phối target giữa dự án nhỏ/lớn |
| P3.3 | Thêm Residual + BatchNorm vào CPM Prediction Head | `unsupervised_pretrainer.py` → `_DAGNNPredictionHead` | Tăng năng lực biểu diễn của head |
| P3.4 | **Warm Connectivity Check** (GAT AUC ≥ 0.70 → mới chuyển sang DAGNN) | `unsupervised_pretrainer.py` → `pretrain_all()` | Đảm bảo bàn giao không gian nhúng tốt cho DAGNN |

---

## TÓM TẮT MỤC TIÊU CUỐI

| Chỉ số | Hiện tại | Mục tiêu sau Roadmap |
|:---|:---:|:---:|
| GAT AUC-ROC | 0.7980 | ≥ 0.85 |
| GAT AP | 0.7731 | ≥ 0.82 |
| DAGNN Critical Accuracy | 94.60% | ≥ 95% |
| DAGNN R² (ES) | 0.5530 | ≥ 0.80 |
| DAGNN MAE ES | 0.1387 | ≤ 0.08 |
| Cơ chế kiểm soát epoch | Cứng (100/150) | Dynamic (Early Stop + Best Snapshot) |
