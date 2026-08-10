# Phân tích Chuyên sâu Cơ chế: HeteroGraph và HGT Model

Tài liệu này phân tích chi tiết về cơ chế hoạt động, các hàm toán học/lập trình được sử dụng và lập luận (trade-off) tại sao lại lựa chọn kiến trúc HeteroGraph và HGT (Heterogeneous Graph Transformer) thay vì các hướng tiếp cận khác trong bài toán Quản lý Tiến độ và Chi phí Dự án.

---

## 1. Giai đoạn 1: HeteroGraph Builder (Xây dựng Đồ thị Dị thể)

### 1.1 Cơ chế hoạt động
Mục tiêu của giai đoạn này là chuyển đổi dữ liệu dạng bảng/dòng chảy tuyến tính (từ cơ sở dữ liệu quan hệ hoặc file Excel/JSON) thành một cấu trúc mạng lưới phi tuyến tính. Hệ thống phân định rõ rệt thực thể nào đóng vai trò gì trong dự án.

Đồ thị dị thể $G = (V, E, \tau, \phi)$ được xây dựng với:
- **Tập đỉnh $V$ (Nodes):** Chia làm 3 loại (types) $\tau(v)$:
  - `Task`: Đại diện cho công việc (vector 39 chiều).
  - `Resource`: Đại diện cho tài nguyên nhân công/máy móc (vector 6 chiều).
  - `Shift`: Đại diện cho lịch làm việc/ca kíp (vector 5 chiều).
- **Tập cạnh $E$ (Edges):** Chia làm 3 loại quan hệ $\phi(e)$:
  - `(Task, precedes, Task)`: Quan hệ phụ thuộc tiến độ (Dependency - FS, SS, FF).
  - `(Task, uses, Resource)`: Quan hệ phân bổ tài nguyên (Allocation).
  - `(Task, constrained_by, Shift)`: Quan hệ ràng buộc thời gian làm việc thực tế.

### 1.2 Hàm thực hiện
Việc hiện thực hóa (implementation) được thông qua class **`HeteroData`** của thư viện **PyTorch Geometric (PyG)**.

```python
import torch
from torch_geometric.data import HeteroData

data = HeteroData()
# 1. Khởi tạo Node Features (x) thông qua hàm torch.Tensor
data['task'].x = torch.tensor(task_features, dtype=torch.float)       # [N, 39]
data['resource'].x = torch.tensor(resource_features, dtype=torch.float) # [R, 6]
data['shift'].x = torch.tensor(shift_features, dtype=torch.float)       # [S, 5]

# 2. Khởi tạo Edge Indices (COO format) qua tập ma trận thưa
data['task', 'precedes', 'task'].edge_index = torch.tensor(task_edges, dtype=torch.long)
data['task', 'uses', 'resource'].edge_index = torch.tensor(uses_edges, dtype=torch.long)
```
*Các đặc trưng (features) trước khi đưa vào tensor được đi qua một lớp **MinMaxScaler** hoặc **StandardScaler** để chuẩn hóa về dải `[0, 1]` hoặc `[-1, 1]` tránh hiện tượng bùng nổ gradient.*

### 1.3 Tại sao chọn HeteroData mà không phải cấu trúc khác?
**Hướng tiếp cận thay thế:** 
1. **Dữ liệu bảng truyền thống (Tabular / MLP):** Chạy Random Forest, XGBoost hoặc Multi-Layer Perceptron.
2. **Đồ thị đồng thể (Homogeneous Graph / GCN):** Gom tất cả thành 1 loại Node duy nhất (Node chung), nhồi chung vào 1 vector.

**Lý do bác bỏ và chọn HeteroGraph:**
- **Bác bỏ MLP:** MLP yêu cầu vector đầu vào cố định độ dài (fixed-size input). Tuy nhiên, mỗi dự án có số lượng Task và Resource khác nhau. MLP "làm phẳng" (flatten) các ma trận phụ thuộc, dẫn đến việc mất hoàn toàn logic Mạng lưới Đường găng (CPM Topology).
- **Bác bỏ Homogeneous Graph:** Nếu dùng Graph Convolutional Network (GCN) truyền thống, ta phải padding (nhồi thêm số 0) để ép Node Resource (6-dim) lên thành 39-dim cho bằng Node Task. Điều này gây nhiễu dữ liệu. Hơn nữa, GCN sẽ coi việc "Task A đứng trước Task B" hoàn toàn giống với "Task A dùng Máy C", điều này là sai lệch nghiêm trọng về mặt ngữ nghĩa (Semantic) trong Quản lý Dự án.
- **Tối ưu của HeteroGraph:** Cấu trúc HeteroGraph tôn trọng hoàn toàn cấu trúc dữ liệu tự nhiên. Nó bảo toàn được số chiều đặc trưng riêng biệt của từng loại thực thể và giữ nguyên được ngữ nghĩa của từng loại liên kết.

---

## 2. Giai đoạn 2: HGT Model (Heterogeneous Graph Transformer)

### 2.1 Cơ chế hoạt động
HGT áp dụng triết lý "Attention Is All You Need" của Transformer vào đồ thị dị thể. Khi một Task cập nhật trạng thái của nó, nó không nhận thông tin một cách cào bằng từ các hàng xóm. Nó sẽ đánh giá (Attention):
- *"Tài nguyên X này quan trọng tới mức nào đối với tôi?"*
- *"Công việc Y đứng trước tôi có khả năng làm trễ tiến độ của tôi bao nhiêu?"*

HGT sử dụng các ma trận trọng số (Weights) **riêng biệt cho từng loại quan hệ**.

### 2.2 Hàm thực hiện và Phương trình Toán học
Cốt lõi của HGT nằm ở lớp **`HGTConv`** (từ PyTorch Geometric). Quá trình **Message Passing (Truyền tin)** mô phỏng chính xác "Hiệu ứng domino" trên công trường (sự chậm trễ của móng truyền sang mái nhà dọc theo các cạnh). Quá trình này đi qua 3 hàm toán học chính:

**A. Hàm Tính Điểm Chú ý (Heterogeneous Mutual Attention):**
Đối với một cạnh từ node nguồn $s$ tới node đích $t$ thuộc loại quan hệ $e = (\tau(s), \phi(e), \tau(t))$:
$$ \text{Attention}(s, t) = \text{Softmax} \left( \frac{\left( \mathbf{H}_s^{(l)} \mathbf{W}_{K}^{\tau(s)} \right) \mathbf{W}_{ATT}^{\phi(e)} \left( \mathbf{H}_t^{(l)} \mathbf{W}_{Q}^{\tau(t)} \right)^T}{\sqrt{d}} \right) $$

**Giải phẫu cơ chế và sự phối hợp của các Ma trận Trọng số ($\mathbf{W}$):**
- **$\mathbf{H}$ (Hidden State):** Là vector đại diện cho thực thể (ví dụ 39-chiều của Task) tại vòng học $l$.
- **Sự phối hợp của $\mathbf{W}_K, \mathbf{W}_Q, \mathbf{W}_{ATT}$:** Cách hiểu của bạn về `w_task * w_edge * w_resource` là **rất chính xác về mặt cấu trúc**. Cụ thể hơn, HGT vay mượn khái niệm truy vấn cơ sở dữ liệu (Database Retrieval) của Transformer:
  - $\mathbf{W}_Q^{\tau(t)}$ (Query - Câu hỏi): Node đích $t$ dùng ma trận này để tạo ra một "Câu hỏi". Ví dụ Task Đổ bê tông tạo Query: *"Tôi đang cần tìm máy móc có công suất lớn"*.
  - $\mathbf{W}_K^{\tau(s)}$ (Key - Chìa khóa/Đặc điểm): Node nguồn $s$ dùng ma trận này để tạo ra "Lời quảng cáo". Ví dụ Máy xúc tạo Key: *"Tôi là máy xúc, công suất cực mạnh, đơn giá 50$/h"*.
  - **Phép thuật đồng bộ kích thước Ma trận:** Task có 39 chiều ($d_{task} = 39$), Resource có 6 chiều ($d_{res} = 6$). Trực tiếp nhân nhau là bất khả thi. Ma trận $W_K$ và $W_Q$ đóng vai trò như các "bộ chuyển đổi" (Adapters) để ép chúng về chung một không gian (ví dụ $d = 64$):
    - Nhu cầu của Task ($1 \times 39$) nhân với $W_Q$ ($39 \times 64$) $\rightarrow$ ra Query ($1 \times 64$).
    - Đặc điểm của Resource ($1 \times 6$) nhân với $W_K$ ($6 \times 64$) $\rightarrow$ ra Key ($1 \times 64$).
  - $\mathbf{W}_{ATT}^{\phi(e)}$: Có kích thước $64 \times 64$. Khi Key và Query đã cùng dải 64 chiều, phép nhân $Key_{(1 \times 64)} \times \mathbf{W}_{ATT(64 \times 64)} \times Query_{(64 \times 1)}^T$ diễn ra hoàn hảo và kết quả cuối cùng thu về đúng 1 con số vô hướng duy nhất (Attention Score). Mức độ càng cao, Task càng chú ý đến Máy xúc này.
- **$d$ và Softmax:**
  - **Chia cho $\sqrt{d}$ (Kích thước vector Key/Query):** Kìm hãm lại độ lớn của tích vô hướng, ngăn ngừa bùng nổ giá trị khiến Gradient bị triệt tiêu (Vanishing Gradient).
  - **Hàm Softmax:** Ép các điểm số này thành dải xác suất (tổng = 100%). Khống chế mô hình bằng một "ngân sách sự chú ý". Nếu Task B quan trọng hơn, Softmax sẽ dồn 90% chú ý cho B, chỉ chừa 10% cho các task kia.

**B. Hàm Truyền Tin (Message Passing):**
$$ \text{Message}(s, t) = \left( \mathbf{H}_s^{(l)} \mathbf{W}_{V}^{\tau(s)} \right) \mathbf{W}_{MSG}^{\phi(e)} $$
- **Nguồn gốc của các ma trận:** Giống y hệt bộ 3 $\mathbf{W}_K, \mathbf{W}_{ATT}, \mathbf{W}_Q$, hai ma trận $\mathbf{W}_{V}$ và $\mathbf{W}_{MSG}$ này cũng là các **Trọng số học được (Learnable Weights)**. Chúng khởi đầu là các con số ngẫu nhiên. Mô hình sẽ tự vặn chỉnh các con số này qua hàng ngàn vòng lặp huấn luyện (Gradient Descent) để tìm ra quy luật tối ưu.
- **Sự phối hợp của $\mathbf{W}_V$ và $\mathbf{W}_{MSG}$:**
  - $\mathbf{W}_{V}^{\tau(s)}$ (Value Adapter): Đóng vai trò là "Bộ chuyển đổi Giá trị" dành riêng cho từng loại Node. Nó chiếu đặc trưng của Node nguồn (ví dụ Resource đang là 6 chiều) về không gian $d$ chiều quy chuẩn (ví dụ 64 chiều). Bước này gói toàn bộ đặc tính của Node nguồn vào một "kiện hàng tiêu chuẩn".
  - $\mathbf{W}_{MSG}^{\phi(e)}$ (Message Translator): Là ma trận dành riêng cho *loại Cạnh*. Nó nhận "kiện hàng" 64 chiều ở trên và "nhào nặn" lại sao cho phù hợp với **ngữ nghĩa của liên kết**. Ví dụ: kiện hàng truyền qua đường ống "Uses Resource" sẽ bị nhào nặn thành một thông điệp mang ý nghĩa "công suất/chi phí"; nhưng nếu qua đường ống "Precedes Task", nó sẽ bị nhào nặn thành thông điệp về "độ trễ thời gian".
- **Kết quả:** Tích thu được là một Message chuẩn hóa (vector $1 \times 64$), đã sẵn sàng để đem nhân với tỷ lệ phần trăm (Attention % tính ở phần A) trước khi Node đích $t$ hấp thụ.

**C. Hàm Cập nhật (Aggregation & Update):**
$$ \mathbf{H}_t^{(l+1)} = \text{GELU} \left( \text{Linear}^{\tau(t)} \left( \mathbf{H}_t^{(l)} + \sum_{s \in N(t)} \text{Attention}(s, t) \cdot \text{Message}(s, t) \right) \right) $$
- **Quá trình thực thi:** HGT nhân mức độ chú ý (Attention) với nội dung (Message) từ mọi hàng xóm, cộng dồn lại, rồi cộng tiếp với trạng thái cũ của chính nó (Residual Connection).
- **Linear ($y = \mathbf{W}x + b$):** Lớp này sinh ra để "Trộn chéo" thông tin. Phép cộng ở trên chỉ là cộng cục bộ (thông tin ở ô số 1 cộng với ô số 1). Nhờ đi qua ma trận $\mathbf{W}_{Linear}$ của lớp Linear, 64 ô thông tin sẽ được nhào nặn chéo với nhau. (Ví dụ: AI sẽ tự nhận ra quy luật "Nếu ô Giá cả tăng + ô Thời gian tăng $\rightarrow$ Khuếch đại ô Rủi ro lên").
- **Cơ chế hàm kích hoạt GELU (Gaussian Error Linear Unit):** 
  Sau khi đi qua Linear, kết quả vẫn chỉ là phương trình đường thẳng. Thực tế công trường không tuyến tính (không phải cứ tăng 100 thợ là giảm 100 ngày, sẽ có điểm bão hòa, vướng víu dẫm đạp nhau). GELU xuất hiện để "bẻ cong" đường thẳng đó.
  - **Phương trình Toán học:** 
    $$ \text{GELU}(x) = x \cdot \Phi(x) $$
    Trong đó $\Phi(x)$ là Hàm phân phối tích lũy (CDF) của phân phối chuẩn Gaussian. Trong thực tế lập trình máy tính, nó được tính xấp xỉ bằng công thức:
    $$ \text{GELU}(x) \approx 0.5x \left(1 + \tanh\left[\sqrt{\frac{2}{\pi}} (x + 0.044715 x^3)\right]\right) $$
  - **Bản chất xác suất (Stochastic Regularizer):** Không giống như hàm ReLU cũ kĩ (cứ hễ âm là vứt bỏ bằng $0$, gây ra lỗi "Chết nơ-ron - Dead Neurons" khiến AI ngừng học), GELU hoạt động dựa trên xác suất:
    - Nếu tín hiệu $x$ mang giá trị dương lớn (tốt): $\Phi(x) \approx 1 \rightarrow \text{GELU}(x) \approx x$ (Giữ nguyên tín hiệu cho đi qua).
    - Nếu tín hiệu $x$ mang giá trị âm sâu (xấu/rác): $\Phi(x) \approx 0 \rightarrow \text{GELU}(x) \approx 0$ (Triệt tiêu tín hiệu).
    - Nhưng tại vùng $x$ dao động quanh $0$ (những đặc trưng nửa thực nửa hư): GELU tạo ra một đường cong cực kỳ mượt mà, cho phép một tỷ lệ nhỏ tín hiệu âm đi qua. Điều này giúp đạo hàm (Gradient) không bao giờ bị đứt gãy, giữ cho mạng AI sâu (như HGT hay ChatGPT) học được những giới hạn tinh tế của thế giới thực.

---

### TÓM TẮT BỨC TRANH TỔNG THỂ CỦA 5 VAI TRÒ MA TRẬN
Nhìn một cách hệ thống, HGT chia luồng xử lý thành 2 nhánh hoàn toàn độc lập với các vai trò chuyên biệt. 

*(Lưu ý: Nói là "5 ma trận" nhưng thực tế đây là **5 Họ/Vai trò ma trận**. Vì tính Dị thể (Heterogeneous), mô hình sẽ sinh ra riêng biệt: 3 ma trận $W_K$ cho 3 loại Node (Task, Resource, Shift), 3 ma trận $W_{ATT}$ cho 3 loại Cạnh... Do đó, tổng số lượng ma trận thực tế trong 1 vòng lặp là rất lớn, giúp AI không bị nhầm lẫn giữa các loại dữ liệu).*

1. **Nhánh Matchmaking (Khớp nối cung cầu) - Dùng để trả lời câu hỏi *"Tôi nên nghe ai?"***
   - Sinh ra **Attention Score** (Điểm số %).
   - **$\mathbf{W}_K$ (Key):** Tạo ra "Hồ sơ quảng cáo" bề ngoài của Node nguồn.
   - **$\mathbf{W}_Q$ (Query):** Tạo ra "Nhu cầu" của Node đích.
   - **$\mathbf{W}_{ATT}$ (Edge Interaction):** Ông tơ bà nguyệt, đánh giá xem Key và Query có khớp nhau qua Cạnh này không.

2. **Nhánh Payload (Truyền tải nội dung) - Dùng để trả lời câu hỏi *"Họ đang nói cái gì?"***
   - Sinh ra **Message** (Nội dung thực tế truyền đi).
   - **$\mathbf{W}_V$ (Value):** Đóng gói "Giá trị nội tại/Cốt lõi" thực sự của Node nguồn. NÓ HOÀN TOÀN KHÁC VỚI $\mathbf{W}_K$. (Ví dụ: $W_K$ là bức ảnh đại diện Tinder để quẹt phải, còn $W_V$ là tính cách thực sự khi đi hẹn hò).
   - **$\mathbf{W}_{MSG}$ (Edge Translation):** Ống dẫn truyền tin. Nội dung cốt lõi của $W_V$ khi đi qua ống dẫn này sẽ bị bóp méo/phiên dịch cho đúng ngữ cảnh của cái Cạnh (thành rủi ro, hay thành chi phí).

3. **Nhánh Tiến hóa (Aggregation & Update) - Dùng để trả lời câu hỏi *"Bản thân tôi sẽ thay đổi thế nào?"***
   - Node đích $t$ **KHÔNG HỀ CAN THIỆP** vào nội dung Message mà Node nguồn $s$ gửi tới. Message là "hàng đóng hộp" của nguồn.
   - Tuy nhiên, Node đích $t$ có quyền quyết định:
     - Dùng Attention (ở Nhánh 1) để xem có nên "mở hộp" hay ném thùng rác (hấp thụ bao nhiêu %).
     - Sau khi nhận quà từ tất cả hàng xóm, Node đích sẽ lấy **Trạng thái cũ của chính nó ($\mathbf{H}_t^{(l)}$)** đem trộn chung với đống quà vừa nhận thông qua bộ trộn **Linear** và **GELU** để tiến hóa lên một phiên bản thông minh hơn ($\mathbf{H}_t^{(l+1)}$).

Tóm lại, Mọi tương tác trong HGT luôn là sự kết hợp chặt chẽ giữa **Đặc tính của Bản thân Node ($W_K, W_Q, W_V$)** cộng sinh với **Ngữ cảnh của Cạnh ($W_{ATT}, W_{MSG}$)**. Đó là lý do nó được gọi là Đồ thị Dị thể (Heterogeneous).

---

## 3. Chiến lược Huấn luyện Mô hình (2 Giai đoạn)
Để AI có thể hiểu được bản chất phức tạp của công trường và đưa ra 3 con số dự báo cuối cùng, quá trình huấn luyện được chia làm 2 giai đoạn tách biệt:

### Giai đoạn 1: Pre-training (Học Tự giám sát - Self-Supervised)
- **Mục tiêu:** Dạy cho AI hiểu được "Quy luật sinh tồn" cơ bản của các mối quan hệ (Task, Resource, Lags) mà không cần ai chỉ bảo đáp án trước.
- **Cơ chế (Masked Feature Reconstruction):** Hệ thống lấy bộ dữ liệu lịch sử đầu vào, nhưng cố tình **ẩn đi (bịt mắt)** một vài đặc trưng của các Node (ví dụ: che đi ô "Chi phí kế hoạch" của một số Task). Sau đó, nó ép mạng HGT phải tự lan truyền thông tin từ hàng xóm để ĐOÁN LẠI cái ô bị che đó.
- **Nhãn (Label) ở đâu?** Ở giai đoạn này KHÔNG hề có nhãn Delay hay Duration. "Nhãn" chính là cái ô thông tin vừa bị che đi. Nếu AI đoán đúng ô bị che, nó được thưởng. Nếu đoán sai, nó tự vặn chỉnh lại ma trận trọng số.
- **Hiện tượng $R^2$ bị Âm:** Khi mới bắt đầu chạy Pre-training, các ma trận trọng số $W$ toàn là số ngẫu nhiên. AI sẽ đoán bừa các ô bị che, dẫn đến sai số khổng lồ (dự báo tệ hơn cả việc nhắm mắt đoán bằng giá trị trung bình). Hệ quả là chỉ số $R^2$ ở những vòng (Epochs) đầu tiên sẽ bị ÂM. Chạy đủ lâu để AI học được quy luật thì $R^2$ mới dần tăng lên dương.

### Giai đoạn 2: Fine-Tuning (Học Có giám sát - Supervised)
- **Mục tiêu:** Ép AI (lúc này đã rất khôn ngoan sau Giai đoạn 1) nhả ra đúng 3 con số dự báo phục vụ cho nghiệp vụ quản lý dự án.
- **Lớp Đầu Ra Dự Báo (Prediction Head):** 
  Sau khi lặp đi lặp lại các hàm Attention, Message Passing, Node Task đã tiến hóa thành một Vector Trạng Thái cuối cùng $\mathbf{H}_{task}^{(L)}$ kích thước $1 \times 64$.
  Ta sẽ tháo bỏ đầu ra của Giai đoạn 1, và cắm vào một lớp Linear mới toanh làm chốt chặn cuối cùng:
  $$ \text{Output} = \mathbf{H}_{task}^{(L)} \times \mathbf{W}_{output} $$
  Trong đó:
  - $\mathbf{H}_{task}^{(L)}$: Vector trạng thái $1 \times 64$.
  - $\mathbf{W}_{output}$: Ma trận trọng số đầu ra có kích thước $64 \times 3$.
  - **Kết quả:** Phép nhân sẽ triệt tiêu 64 chiều, trả về đúng 1 Vector kích thước $1 \times 3$, chứa chính xác 3 giá trị dự báo: `[duration_factor, expected_delay, uncertainty_sigma]`.
- **Nhãn (Label) ở đâu?** Lúc này, ta mới thực sự cần Nhãn nghiệp vụ. Nhãn chính là cột "Thời gian thực tế" trích xuất từ **sổ nhật ký nghiệm thu công trình trong lịch sử**. Hàm Mất Mát (Loss Function) sẽ đem 3 con số dự báo ra so sánh với hồ sơ thực tế. Nếu sai lệch, nó sẽ dùng thuật toán Lan truyền ngược để ép AI tinh chỉnh lại toàn bộ hệ thống ma trận nhằm dự báo chuẩn xác mức rủi ro và trễ hạn.
