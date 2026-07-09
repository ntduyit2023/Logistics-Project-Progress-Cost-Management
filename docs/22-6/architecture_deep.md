# TRUTHMODEL: Phân tích Kiến trúc Khi Data Đủ + Vấn đề Song Song vs Bất Đồng Bộ

> [!NOTE]
> Giả định: Data đã đầy đủ (72 features, 50+ dự án). Bản phân tích này tập trung vào những điểm yếu **bản chất kiến trúc** mà không thể giải quyết bằng cách thêm data.

---

## Phần 1: Mâu thuẫn Triết học Cốt lõi — "GAT vs DAGNN"

Đây là vấn đề kiến trúc **nghiêm trọng nhất** mà sếp đã chạm đúng khi hỏi về song song vs bất đồng bộ.

### Hiện trạng: Hai "bộ não" đánh nhau

Hệ thống hiện tại chạy **tuần tự** qua 2 bước:

```
Bước 1: GAT (Song song / Synchronous)
   → Mọi task nhận thông tin từ hàng xóm ĐỒNG THỜI
   → Nhanh, tận dụng GPU
   → NHƯNG: Task B "nghe" thông tin từ Task A khi Task A CHƯA xử lý xong

Bước 2: DAGNN (Tuần tự / Sequential)  
   → Task được xử lý theo thứ tự Tô-pô (A → B → C)
   → Đúng về mặt nhân quả
   → NHƯNG: Không song song được, chạy trên CPU từng node một
```

### Vấn đề cốt lõi: "GAT cho kết quả sai, DAGNN xây trên nền sai"

**Ví dụ cụ thể:**

Giả sử có chuỗi: `Đào móng → Đổ bê tông → Xây tường → Lắp mái`

Khi GAT chạy ở Bước 1 (song song):
- `Xây tường` nhận message từ `Đổ bê tông`
- Nhưng `Đổ bê tông` **cũng đang nhận message cùng lúc** từ `Đào móng`
- Tức là `Xây tường` nhận được tín hiệu rủi ro từ `Đổ bê tông` khi `Đổ bê tông` chưa kịp "tiêu hóa" xong rủi ro từ `Đào móng`
- → Tín hiệu bị **"nửa chín nửa sống"**

Khi DAGNN chạy ở Bước 2 (tuần tự):
- DAGNN nhận input là `h_gat` — output bị "nửa chín" từ Bước 1
- DAGNN cố gắng sửa sai bằng cách lan truyền lại theo Tô-pô
- Nhưng nó đang **sửa trên nền đã bị nhiễu**, không phải trên data gốc

**Kết quả:** DAGNN không thực sự "sửa" được GAT. Nó chỉ thêm một lớp xử lý trên output đã bị lệch. Trong trường hợp xấu, hai bộ não này có thể **triệt tiêu lẫn nhau** thay vì bổ trợ.

---

## Phần 2: Ba Chiến lược — Và Kiến trúc Hiện Tại Chọn Cái Tệ Nhất

| Chiến lược | Ưu điểm | Nhược điểm | Kiến trúc hiện tại? |
|:---|:---|:---|:---:|
| **A. Chỉ GAT** (Song song hoàn toàn) | Nhanh, GPU-friendly | Không tôn trọng nhân quả DAG | ❌ |
| **B. Chỉ DAGNN** (Tuần tự hoàn toàn) | Đúng nhân quả 100% | Chậm, không song song | ❌ |
| **C. GAT rồi DAGNN** (Lai ghép) | "Có cả hai" | Hai bộ não đánh nhau | ✅ Đang dùng |
| **D. Topological Attention** (Phương án lý tưởng) | Đúng nhân quả + Song song theo lớp | Phức tạp hơn để code | ❌ Chưa có |

Kiến trúc hiện tại chọn **Phương án C** — trông có vẻ thông minh ("dùng cả hai cho chắc") nhưng thực ra là phương án **tệ nhất về mặt lý thuyết** vì nó không giải quyết được mâu thuẫn gốc rễ.

---

## Phần 3: Phương án Lý tưởng — Topological Attention

Thay vì chạy GAT (sai) rồi DAGNN (sửa), ta nên xây một kiến trúc duy nhất kết hợp cả hai:

```
Topological Attention = Attention (linh hoạt của GAT)
                      + Nhân quả (đúng đắn của DAGNN)
                      + Song song theo Tầng (hiệu quả GPU)
```

### Cơ chế hoạt động:

```
Tầng Tô-pô 0 (in_degree = 0):  [Đào móng]           → Xử lý SONG SONG
Tầng Tô-pô 1:                   [Đổ bê tông]          → Attend ONLY to Tầng 0
Tầng Tô-pô 2:                   [Xây tường, Ốp gạch]  → Attend ONLY to Tầng 0,1 (SONG SONG)
Tầng Tô-pô 3:                   [Lắp mái]             → Attend ONLY to Tầng 0,1,2
```

- Mỗi "Tầng Tô-pô" chứa các task không phụ thuộc nhau → **Chạy song song trên GPU**
- Task chỉ attend đến predecessors đã xử lý xong → **Đúng nhân quả**
- Dùng Attention Mask (giống Causal Mask trong Transformer) để chặn tín hiệu từ tương lai

### So sánh hiệu suất (Lý thuyết):

| Kiến trúc | Đúng nhân quả? | Song song? | Tốc độ (Dự án 1000 tasks) |
|:---|:---:|:---:|:---:|
| GAT only | ❌ | ✅ Full GPU | ~0.01s |
| DAGNN only | ✅ | ❌ CPU tuần tự | ~2s |
| GAT + DAGNN (hiện tại) | ⚠️ Gần đúng | ⚠️ Một nửa | ~1s |
| **Topological Attention** | ✅ | ✅ Theo tầng | ~0.05s |

---

## Phần 4: Những Điểm Kiến Trúc Cần Cải Thiện Khác (Khi Data Đủ)

### 4.1. GAT không dùng Edge Attributes
- Code tạo `edge_attr` tensor (8 chiều: FS/SS/FF/SF + 4 lag values)
- Nhưng `GATConv(hidden_dim, hidden_dim, heads=heads)` **không truyền `edge_attr` vào**
- → 8 chiều thông tin quý giá (loại dependency, thời gian lag) bị **vứt đi hoàn toàn**
- **Fix:** Dùng `GATConv(..., edge_dim=8)` hoặc chuyển sang `TransformerConv` có hỗ trợ edge features

### 4.2. DAGNN dùng Sum Aggregation quá đơn giản
- Dòng 228: `agg_state = hidden_states[pred_indices].sum(dim=0)`
- Cộng tất cả predecessors lại rồi bỏ vào MLP
- **Vấn đề:** Task có 1 predecessor nguy hiểm + 9 predecessors an toàn → Tín hiệu nguy hiểm bị "pha loãng" 10 lần
- **Fix:** Dùng **Attention Aggregation** — để task tự quyết định predecessor nào quan trọng nhất

### 4.3. Không có Residual Connections
- Output của GAT đi thẳng vào DAGNN, không có đường tắt (skip connection)
- Nếu DAGNN "học hỏng", thông tin từ Encoder sẽ bị mất hoàn toàn
- **Fix:** Thêm `h_final = h_dagnn + h_gat` (residual)

### 4.4. Encoder Attention ≠ Standard Attention
- Tầng 1 dùng `softmax(v @ A.T) * v` — đây KHÔNG phải Multi-Head Self-Attention chuẩn
- Nó thiếu cơ chế Query-Key-Value, không có Positional Encoding
- Với data đủ, một **Mini-Transformer** bên trong mỗi Group sẽ mạnh hơn nhiều

### 4.5. Gating Mechanism trong DAGNN rất tốt — nhưng chưa đủ
- Cổng `gate = sigmoid(...)` ở dòng 235 là ý tưởng hay (giống GRU)
- Nhưng nó chỉ có 1 cổng. Kiến trúc GRU/LSTM chuẩn có 2-3 cổng (Reset, Update, Output)
- Với data đủ, nên nâng lên **GRU-cell** hoặc **LSTM-cell** đầy đủ

---

## Tóm tắt Ưu tiên (Nếu data đủ)

| # | Cải thiện | Mức ưu tiên | Lý do |
|:---:|:---|:---:|:---|
| 1 | Thay GAT+DAGNN bằng **Topological Attention** | 🔴 Cao | Giải quyết mâu thuẫn triết học cốt lõi |
| 2 | Truyền `edge_attr` vào GNN | 🔴 Cao | Đang vứt đi 8 chiều data quý giá |
| 3 | DAGNN: Sum → **Attention Aggregation** | 🟡 Trung bình | Tránh pha loãng tín hiệu nguy hiểm |
| 4 | Thêm Residual Connections | 🟡 Trung bình | An toàn hơn, tránh vanishing gradient |
| 5 | Encoder: Custom Attention → **Mini-Transformer** | 🟢 Thấp | Chỉ cần khi data rất phong phú |
| 6 | DAGNN Gate: 1-gate → **GRU-cell** | 🟢 Thấp | Cải thiện nhỏ, phức tạp code |
