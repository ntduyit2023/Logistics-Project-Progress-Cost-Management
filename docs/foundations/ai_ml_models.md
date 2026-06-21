# 🤖 Mô Hình AI/ML Đồ Thị Cho Dự Án GLPO

Tài liệu này phân tích chuyên sâu **lý thuyết, cơ chế hoạt động, và ứng dụng thực tế** của các mô hình Machine Learning trên đồ thị (Graph ML) có thể áp dụng vào dự án tối ưu hóa logistics GLPO.

---

## 1. Tại Sao Cần AI Trên Đồ Thị?

### 1.1 Hạn chế của thuật toán truyền thống

Các thuật toán cổ điển như CPM, PERT hoạt động dựa trên **giả định tĩnh**: mỗi công việc có một thời gian cố định và không thay đổi. Nhưng trong thực tế logistics:

*   **Thời tiết xấu** khiến vận chuyển đường biển chậm 3-5 ngày
*   **Nhà cung cấp trễ nguyên vật liệu** làm toàn bộ nhánh sản xuất bị đình trệ
*   **Nhân sự nghỉ ốm** tạo ra bottleneck tài nguyên bất ngờ
*   **Biến động giá nguyên liệu** thay đổi chi phí crashing

→ Cần một hệ thống **học từ dữ liệu lịch sử** để dự đoán những biến động này và **cảnh báo sớm** trước khi chúng ảnh hưởng đến đường găng.

### 1.2 Tại sao GNN chứ không phải ML thông thường?

Dữ liệu dự án có **cấu trúc đồ thị** (nodes = tasks, edges = dependencies). Các mô hình ML truyền thống (Random Forest, XGBoost) chỉ xử lý được dữ liệu bảng — chúng **không hiểu được mối quan hệ phụ thuộc** giữa các công việc.

**Ví dụ thực tế:**
> Trong một dự án xây kho lạnh logistics, hoạt động "Lắp đặt hệ thống làm lạnh" (Task H) phụ thuộc vào 2 tasks: "Hoàn thiện khung kho" (Task E) và "Nhập thiết bị lạnh" (Task F). Nếu dùng ML thông thường, ta chỉ biết Task H có "2 predecessors". Nhưng GNN hiểu được rằng Task F nằm trên đường găng và Task E có 12 ngày slack → sự trễ của F **quan trọng gấp bội** so với E đối với H. GNN nắm bắt được "bối cảnh cấu trúc" này.

---

## 2. DAGNN — Directed Acyclic Graph Neural Networks

### 2.1 Bài toán giải quyết
**Dự đoán thời gian thực tế** ($d_{actual}$) của mỗi công việc dựa trên "áp lực tích lũy" từ các công việc tiên quyết.

### 2.2 Ý tưởng cốt lõi

GCN (Graph Convolutional Network) thông thường xử lý đồ thị **vô hướng** — thông tin lan truyền đều theo mọi hướng. Nhưng dự án là **DAG** — thông tin chỉ chảy theo một chiều (từ task đầu đến task cuối). DAGNN khai thác **thứ tự phần (partial ordering)** này.

**Hình dung bằng phép ẩn dụ "Dòng sông":**

> Hãy tưởng tượng đồ thị dự án là một mạng lưới sông suối. Nước (thông tin) chỉ chảy xuôi theo dòng, không bao giờ chảy ngược. Mỗi nhánh sông mang theo "trầm tích" — đó là áp lực thời gian tích lũy. Khi hai nhánh sông hợp lưu (merge node), nhánh nào mang nhiều trầm tích hơn sẽ quyết định dòng chảy tiếp theo.
>
> Trong Case Study: Nhánh A→C→F mang 23 ngày trầm tích, nhánh A→B→E mang 16 ngày. Khi hợp lưu tại H, DAGNN hiểu rằng H chịu áp lực chủ yếu từ nhánh phần mềm (23 ngày) — đó là "dòng chảy chính" quyết định khi nào H có thể bắt đầu.

### 2.3 Cơ chế hoạt động chi tiết

DAGNN xử lý đồ thị theo **từng lớp topo** (topological layer):

**Lớp 0 (Nguồn):** Task A — không có áp lực đầu vào, chỉ phụ thuộc vào bản thân nó.

**Lớp 1:** Tasks B, C — mỗi task nhận thông tin tổng hợp từ A. DAGNN học được: "B và C cùng phụ thuộc A nhưng tính chất khác nhau (B là hardware, C là software) → khả năng trễ khác nhau."

**Lớp 2:** Tasks D, E, F, G — mỗi task tổng hợp thông tin từ parents. F nhận thông tin từ C (đường găng) nên được gán **trọng số cao hơn** trong mô hình.

**...tiếp tục cho đến lớp cuối cùng (U).**

Ở mỗi lớp, DAGNN thực hiện 3 bước:
1.  **Thu thập (Aggregate):** Gom thông tin từ tất cả các nút cha
2.  **Biến đổi (Transform):** Kết hợp thông tin thu được với đặc trưng của chính nút hiện tại
3.  **Cập nhật (Update):** Tạo ra biểu diễn mới cho nút, phản ánh toàn bộ "lịch sử" upstream

### 2.4 Đặc trưng đầu vào cho mỗi nút (Node Features)

Để DAGNN dự đoán chính xác, mỗi nút cần các thông tin sau:

| Đặc trưng | Ý nghĩa | Ví dụ (Task I - SW Programming) |
|-----------|---------|------|
| Duration dự kiến | Thời gian kế hoạch | 16 ngày |
| Số lượng tài nguyên | Nhân sự cần thiết | 2 (Design_Comp + Documentation) |
| In-degree | Số tasks tiên quyết | 1 (chỉ cần G xong) |
| Out-degree | Số tasks phụ thuộc vào nó | 1 (J phụ thuộc I) |
| Betweenness centrality | Mức độ "trung tâm" trong đồ thị | Cao (nằm trên đường găng) |
| Loại công việc | Hardware/Software/Integration | Software |
| Slack dự kiến | Thời gian dự trữ theo CPM | 0 (găng) |

### 2.5 Ứng dụng thực tế trong logistics

**Bài toán:** Công ty vận tải XYZ có dự án mở rộng mạng lưới kho bãi gồm 50 hoạt động. Dữ liệu lịch sử 3 năm cho thấy: các hoạt động liên quan đến xây dựng thường trễ 20-30% vào mùa mưa, trong khi hoạt động nhập thiết bị trễ 10-15% do logistics quốc tế.

**DAGNN làm gì:** Huấn luyện trên dữ liệu lịch sử, DAGNN học được pattern: khi một nút "xây dựng" nằm trên nhánh có nhiều nút "nhập thiết bị" phía trước, **xác suất trễ cộng dồn** cao hơn so với nhánh thuần xây dựng. Mô hình dự báo: "Task H có 73% khả năng trễ 3-5 ngày, chủ yếu do áp lực tích lũy từ nhánh F (nhập thiết bị lạnh)."

### 2.6 Tài liệu tham khảo

| Mục | Chi tiết |
|-----|---------|
| **Paper gốc** | Thost & Chen. *"Directed Acyclic Graph Neural Networks."* ICLR 2021 |
| **GitHub** | [vthost/DAGNN](https://github.com/vthost/DAGNN) |
| **Framework** | PyTorch + PyTorch Geometric (PyG) |

---

## 3. GAT — Graph Attention Networks

### 3.1 Bài toán giải quyết
**Dự báo rủi ro lan truyền trễ** (Delay Propagation) và **giải thích** tại sao một công việc bị coi là rủi ro cao.

### 3.2 Ý tưởng cốt lõi — Cơ chế Attention

GCN coi tất cả hàng xóm (neighbors) **bằng nhau** — mỗi predecessor đều ảnh hưởng ngang nhau đến node con. Nhưng thực tế không phải vậy.

**Ví dụ thực tế:**
> Task H (Hardware detail drawings) phụ thuộc vào 2 tasks:
> - Task E (Hardware design, 6 ngày, Slack = 12): Nằm ngoài đường găng, có nhiều thời gian dự trữ
> - Task F (Software design, 12 ngày, Slack = 5): Gần đường găng, thời gian dài, rủi ro cao
>
> Nếu E trễ 2 ngày → H vẫn ổn (E còn 12 ngày slack).
> Nếu F trễ 2 ngày → H có thể bị ảnh hưởng nghiêm trọng (F chỉ có 5 ngày slack).
>
> **GAT tự học** rằng F quan trọng hơn E đối với H. Nó gán **trọng số attention** α = 0.72 cho cạnh F→H và α = 0.28 cho cạnh E→H.

### 3.3 Cơ chế Attention giải thích chi tiết

Attention hoạt động giống cách **một nhà quản lý dự án giàu kinh nghiệm** phân bổ sự chú ý:

**Bước 1 — Đánh giá từng mối quan hệ:**
Với mỗi cặp (predecessor → node), GAT tính một "điểm tương thích" (compatibility score). Điểm này phụ thuộc vào đặc trưng của CẢ HAI nút — không chỉ predecessor.

**Bước 2 — Chuẩn hóa thành trọng số:**
Các điểm tương thích được chuẩn hóa thành xác suất (tổng = 1) bằng hàm softmax. Đây chính là "trọng số attention" — cho biết mỗi predecessor ảnh hưởng **bao nhiêu phần trăm** đến node con.

**Bước 3 — Tổng hợp có trọng số:**
Thay vì lấy trung bình đều, GAT tính **trung bình có trọng số** theo attention. Predecessor nào có α cao hơn sẽ đóng góp nhiều hơn vào biểu diễn của node con.

### 3.4 Multi-Head Attention — Nhìn vấn đề từ nhiều góc

GAT sử dụng **nhiều "đầu attention" song song** (multi-head), mỗi đầu tập trung vào một khía cạnh khác nhau:

| Head | Khía cạnh tập trung | Ví dụ thực tế |
|------|---------------------|---------------|
| Head 1 | **Thời gian (Duration)** | "F kéo dài 12 ngày, gấp đôi E → attention cao hơn" |
| Head 2 | **Tài nguyên (Resource)** | "F và H cùng dùng Dev_Comp → attention cao do resource conflict" |
| Head 3 | **Vị trí cấu trúc** | "F nằm gần đường găng → attention cao do rủi ro hệ thống" |
| Head 4 | **Lịch sử trễ** | "Các tasks phần mềm có tỷ lệ trễ lịch sử 30% → attention cao" |

Kết quả cuối cùng **kết hợp tất cả các góc nhìn** này, cho ra đánh giá rủi ro toàn diện.

### 3.5 Sức mạnh giải thích (Explainability)

Đây là lợi thế lớn nhất của GAT so với các mô hình khác: **ta có thể trích xuất attention weights để giải thích cho người quản lý dự án.**

**Ví dụ báo cáo từ hệ thống GLPO:**
> 🚨 **Cảnh báo rủi ro cho Task R (HW/SW Integration):**
> - Rủi ro trễ: **82%** (Cao)
> - Nguyên nhân chính (theo attention weights):
>   - 45% do Task N (Prototype installation) — đang chậm 3 ngày so với kế hoạch
>   - 35% do Task Q (Hardware assembly) — tài nguyên Assembly_Mech đang bị overloaded
>   - 20% do hiệu ứng lan truyền từ nhánh phần mềm (I→J→N)
> - Khuyến nghị: Tập trung nguồn lực vào Task N ngay lập tức

### 3.6 So sánh GAT vs GCN qua ví dụ

Xét nút R (HW/SW Integration) phụ thuộc vào N và Q:

| | GCN (đối xử bằng nhau) | GAT (có attention) |
|---|---|---|
| **Ảnh hưởng N → R** | 50% | 68% (N trên đường găng, rủi ro cao) |
| **Ảnh hưởng Q → R** | 50% | 32% (Q có 5 ngày slack, ít rủi ro) |
| **Dự báo rủi ro R** | Trung bình, không phân biệt | Chính xác, phản ánh đúng thực tế |
| **Giải thích được?** | ❌ Không | ✅ Có (attention weights) |

### 3.7 Ứng dụng thực tế — Delay Propagation trong vận tải

**Bài toán thực tế:** Công ty logistics vận hành tuyến đường biển Thượng Hải → Hải Phòng → Nội Bài. Mạng lưới gồm 8 hoạt động liên kết: thông quan xuất khẩu → xếp container → vận chuyển biển → thông quan nhập khẩu → dỡ hàng → kiểm tra → vận chuyển nội địa → giao hàng.

**GAT phát hiện:** Qua phân tích attention, mô hình nhận ra rằng "thông quan nhập khẩu" (attention = 0.41) có ảnh hưởng lan truyền lớn nhất đến "giao hàng cuối" — lớn hơn cả "vận chuyển biển" (attention = 0.25). Lý do: thông quan nhập khẩu có **variance cao** (dao động 1-7 ngày tùy lô hàng), trong khi vận chuyển biển khá ổn định (±1 ngày).

### 3.8 Tài liệu tham khảo

| Mục | Chi tiết |
|-----|---------|
| **Paper gốc** | Veličković et al. *"Graph Attention Networks."* ICLR 2018 |
| **PyTorch Geometric** | Layer `GATConv` — tích hợp sẵn |
| **HuggingFace** | [keras-io/graph-attention-nets](https://huggingface.co/keras-io/graph-attention-nets) |
| **Ứng dụng tương tự** | Train Delay Propagation (ETH Zurich) — dùng GAT dự báo trễ tàu hỏa |

---

## 4. GNN + Deep Reinforcement Learning (Wheatley Framework)

### 4.1 Bài toán giải quyết
**Tự động xếp lịch** khi tài nguyên bị giới hạn (RCPSP) — thay vì con người phải thử hàng trăm phương án, AI tự học cách chọn task tối ưu.

### 4.2 Ý tưởng cốt lõi — Học cách ra quyết định

Hãy tưởng tượng bạn là một PM (Project Manager) đang xếp lịch cho dự án 21 tasks. Mỗi ngày, bạn phải quyết định: **"Hôm nay nên bắt đầu task nào?"** — với ràng buộc rằng các predecessors phải xong và đủ nhân sự.

Wheatley **huấn luyện một AI Agent** làm việc này. Agent quan sát trạng thái dự án (đồ thị hiện tại), đưa ra quyết định (chọn task), và nhận phản hồi (tốt hay xấu dựa trên makespan cuối cùng).

### 4.3 Ba thành phần chính

#### A. GNN Encoder — "Đôi mắt" của Agent

GNN đóng vai trò **nhìn và hiểu** trạng thái đồ thị dự án tại mỗi thời điểm. Nó nắm bắt:
*   Những task nào đã hoàn thành, đang thực hiện, chưa bắt đầu
*   Tài nguyên nào đang bận, tài nguyên nào rảnh
*   Cấu trúc phụ thuộc còn lại (subgraph chưa xử lý)
*   "Áp lực" từ deadline và penalties

**Ví dụ:** Tại ngày 30, GNN nhìn thấy: "A, B, C, D, E đã xong. F đang chạy (còn 5 ngày). G đã xong. Dev_Comp đang bận cho F. Design_Mech đang rảnh. I đủ điều kiện bắt đầu nhưng cần Design_Comp (đang bận)..."

#### B. Policy Network (PPO) — "Bộ não" ra quyết định

Dựa trên thông tin từ GNN, Policy Network tính xác suất cho mỗi task eligible (đủ điều kiện):

> "Tại ngày 30, các task eligible: H, I, K. Xác suất chọn:
> - K: 55% (không cần Design_Comp, có thể bắt đầu ngay, giải phóng bottleneck cho L)
> - H: 30% (cần Dev_Comp đang rảnh, nhưng phải chờ F)
> - I: 15% (cần Design_Comp đang bận cho F, không tối ưu)"

Agent chọn K → bắt đầu K, giải phóng luồng cho nhánh hardware.

#### C. Reward Signal — "Hệ quả" của quyết định

Sau khi toàn bộ dự án được xếp lịch xong, Agent nhận reward = -(makespan):
*   Makespan 66 ngày → reward = -66 (tốt)
*   Makespan 80 ngày → reward = -80 (xấu hơn)
*   Makespan 96 ngày → reward = -96 (rất xấu)

Agent học qua hàng nghìn episodes: **"Những lần tôi chọn K trước I ở ngày 30, makespan thường thấp hơn 5-8 ngày."**

### 4.4 PPO (Proximal Policy Optimization) — Tại sao chọn thuật toán này?

PPO là thuật toán RL hiện đại, được chọn vì:
*   **Ổn định:** Không thay đổi policy quá đột ngột giữa các lần cập nhật → tránh "quên" kinh nghiệm tốt
*   **Hiệu quả mẫu:** Học từ ít episodes hơn so với các thuật toán RL cũ (DQN, A2C)
*   **Liên tục + rời rạc:** Xử lý được cả action space liên tục (thời gian) và rời rạc (chọn task)

### 4.5 Schedule Generation Scheme (SGS) — Đảm bảo tính khả thi

Một vấn đề quan trọng: **Agent có thể đưa ra quyết định vi phạm ràng buộc** (ví dụ: chọn task chưa đủ predecessors). SGS đóng vai trò "bộ lọc":

1.  Agent đưa ra priority list (thứ tự ưu tiên)
2.  SGS lần lượt lấy task từ danh sách
3.  Kiểm tra: predecessors xong? Đủ tài nguyên?
    *   Nếu OK → xếp vào lịch
    *   Nếu không → bỏ qua, chuyển task tiếp theo
4.  Quay lại sau khi có thêm tài nguyên rảnh

→ SGS **đảm bảo 100%** lịch trình đầu ra luôn khả thi (feasible).

### 4.6 Ứng dụng thực tế — Xếp lịch khi bất định

**Bài toán:** Dự án Case Study 21 tasks. Trong thực tế, thời gian mỗi task dao động ±20% so với kế hoạch. Mỗi lần chạy, duration thực tế khác nhau. Phương pháp truyền thống (CPM + heuristic cố định) cho makespan trung bình 72 ngày.

**Wheatley làm gì:** Train Agent trên 10,000 lần mô phỏng với duration ngẫu nhiên. Agent học được **chiến lược bền vững (robust policy)**: "Luôn ưu tiên task trên đường găng dự kiến, nhưng nếu task phần cứng có duration thực tế ngắn bất thường → tranh thủ làm ngay để giải phóng tài nguyên sớm."

Kết quả: Makespan trung bình 67 ngày (giảm 7% so với heuristic cố định), và **variance thấp hơn** (ít rủi ro vượt deadline hơn).

### 4.7 Tài liệu tham khảo

| Mục | Chi tiết |
|-----|---------|
| **Paper** | Tassel et al. *"A Reinforcement Learning Environment for RCPSP."* |
| **GitHub** | [jolibrain/wheatley](https://github.com/jolibrain/wheatley) |
| **Framework** | PyTorch + DGL (Deep Graph Library) |
| **Hỗ trợ** | RCPSP, JSSP, Stochastic Scheduling |

---

## 5. Graphormer — Graph Transformer

### 5.1 Bài toán giải quyết
**Dự báo tổng thể dự án** (graph-level prediction) — thay vì dự đoán từng node, Graphormer đánh giá "sức khỏe" của toàn bộ đồ thị dự án.

### 5.2 Ý tưởng cốt lõi — Transformer cho đồ thị

Transformer đã cách mạng hóa xử lý ngôn ngữ (ChatGPT, BERT). Graphormer áp dụng ý tưởng này cho đồ thị: mỗi nút **chú ý đến MỌI nút khác** trong đồ thị (global attention), không chỉ hàng xóm trực tiếp.

**Hình dung:**
> GCN/GAT giống như hỏi thăm **hàng xóm sát vách** để biết tin tức khu phố.
> Graphormer giống như mở **cuộc họp toàn dự án** — mọi task đều có thể trao đổi thông tin với nhau, bất kể có kết nối trực tiếp hay không.

### 5.3 Ba loại encoding đặc biệt

Graphormer thêm 3 loại thông tin cấu trúc vào attention:

| Encoding | Ý nghĩa | Ví dụ |
|----------|---------|-------|
| **Centrality Encoding** | Mức độ quan trọng (degree) của nút | Task A có out-degree 2, Task R có in-degree 2 |
| **Spatial Encoding** | Khoảng cách ngắn nhất giữa 2 nút | A→R = 7 bước (qua C→G→I→J→N→R) |
| **Edge Encoding** | Trọng số/loại của cạnh trên đường đi | Cạnh C→G khác biệt với cạnh B→E (SW vs HW) |

### 5.4 Khi nào dùng Graphormer?

*   **Phù hợp:** Đánh giá tổng thể dự án, so sánh nhiều phương án xếp lịch, phát hiện cấu trúc dự án bất thường
*   **Không phù hợp:** Dự báo chi tiết từng node (DAGNN/GAT tốt hơn), dự án nhỏ (< 30 tasks) — quá phức tạp so với cần thiết

### 5.5 Tài liệu tham khảo

| Mục | Chi tiết |
|-----|---------|
| **Paper** | Ying et al. *"Do Transformers Really Perform Bad for Graph Representation?"* NeurIPS 2021 |
| **HuggingFace** | [microsoft/graphormer-base-pcqm4mv1](https://huggingface.co/microsoft/graphormer-base-pcqm4mv1) |

---

## 6. Các Mô Hình & Dataset Tham Khảo Trên HuggingFace

### 6.1 Models

| Model | Thể loại | Ứng dụng cho GLPO |
|-------|----------|-------------------|
| **[ICICLE-AI/FoodFlow_GNN_Model](https://huggingface.co/ICICLE-AI/FoodFlow_GNN_Model)** | GCN + GAT | Tham khảo cách GAT gán trọng số cho luồng logistics trong chuỗi cung ứng thực phẩm |
| **[keras-io/graph-attention-nets](https://huggingface.co/keras-io/graph-attention-nets)** | GAT (Keras) | Mã nguồn mẫu chuẩn hóa cho node classification trên đồ thị |
| **[HUANG1993/GreedRL-VRP-pretrained-v1](https://huggingface.co/HUANG1993/GreedRL-VRP-pretrained-v1)** | Deep RL | Giải bài toán tối ưu tổ hợp VRP/TSP trên đồ thị — tham khảo cách RL ra quyết định tuần tự |
| **[microsoft/graphormer-base-pcqm4mv1](https://huggingface.co/microsoft/graphormer-base-pcqm4mv1)** | Graphormer | Graph Transformer, pre-trained, có thể fine-tune cho graph-level prediction |

### 6.2 Datasets thử nghiệm

| Dataset | Mô tả | Ứng dụng |
|---------|--------|----------|
| **[Yahias21/vrp_benchmark](https://huggingface.co/datasets/Yahias21/vrp_benchmark)** | VRP 10-1000 khách hàng, có yếu tố ngẫu nhiên (trễ thời tiết, giao thông) | Huấn luyện mô hình dự báo trễ |
| **PSPLIB** | Bộ benchmark chuẩn quốc tế cho RCPSP (30-120 activities) | Đánh giá thuật toán xếp lịch, so sánh với kết quả đã công bố |
| **OGB (Open Graph Benchmark)** | Benchmark đa domain cho GNN | Pre-train GNN chung trước khi fine-tune cho GLPO |

---

## 7. Bảng So Sánh Tổng Hợp

| Tiêu chí | DAGNN | GAT | GNN+RL (Wheatley) | Graphormer |
|----------|-------|-----|-------------------|------------|
| **Mục đích chính** | Dự đoán duration | Dự báo delay propagation | Xếp lịch RCPSP tự động | Đánh giá tổng thể dự án |
| **Cấp độ dự báo** | Node-level | Node-level | Schedule-level | Graph-level |
| **Xử lý DAG** | ✅ Chuyên biệt | ⚠️ Cần điều chỉnh | ✅ Hỗ trợ sẵn | ⚠️ Cần encoding |
| **Giải thích được** | Trung bình | ✅ Rất tốt (attention) | Trung bình | Thấp |
| **Xử lý bất định** | Trung bình | Tốt | ✅ Rất tốt | Tốt |
| **Dữ liệu cần** | Lịch sử duration | Lịch sử trễ | Nhiều episode mô phỏng | Dataset lớn |
| **Độ phức tạp** | Trung bình | Thấp-TB | Cao | Cao |
| **Phase áp dụng** | Phase 5 | Phase 5 | Phase 3+5 | Phase 5 (optional) |

---

## 8. Lộ Trình Tích Hợp Đề Xuất

### Giai đoạn 1: Nền tảng (Phase 3)
Tích hợp **Wheatley** để giải RCPSP — đây là ứng dụng AI trực tiếp nhất, thay thế cho heuristic thủ công. Train trên PSPLIB benchmark, sau đó fine-tune trên Case Study 21 tasks.

### Giai đoạn 2: Dự báo (Phase 5)
*   **DAGNN** cho duration prediction — cần thu thập dữ liệu lịch sử hoặc mô phỏng
*   **GAT** cho delay propagation — cung cấp dashboard cảnh báo rủi ro với attention-based explanation

### Giai đoạn 3: Nâng cao (Optional)
*   **Graphormer** cho đánh giá tổng thể — so sánh nhiều kịch bản xếp lịch

---

## 📚 9. Tài Liệu Tham Khảo Tổng Hợp

### Papers:
1.  **Thost & Chen (2021).** *"Directed Acyclic Graph Neural Networks."* ICLR 2021.
2.  **Veličković et al. (2018).** *"Graph Attention Networks."* ICLR 2018.
3.  **Ying et al. (2021).** *"Do Transformers Really Perform Bad for Graph Representation?"* NeurIPS 2021.
4.  **Tassel et al. (2023).** *"A Reinforcement Learning Environment for RCPSP."*
5.  **CP 2024.** *"Learning Precedences for RCPSP with GNNs."* — GNN + CP Solver hybrid.

### GitHub:
*   [vthost/DAGNN](https://github.com/vthost/DAGNN) — Official DAGNN
*   [jolibrain/wheatley](https://github.com/jolibrain/wheatley) — GNN+RL scheduler
*   [pyg-team/pytorch_geometric](https://github.com/pyg-team/pytorch_geometric) — PyTorch Geometric
*   [dmlc/dgl](https://github.com/dmlc/dgl) — Deep Graph Library

### HuggingFace:
*   [HuggingFace Graph ML Guide](https://huggingface.co/blog/intro-graphml) — Giới thiệu Graph ML
*   [Graphormer docs](https://huggingface.co/docs/transformers/model_doc/graphormer) — Tài liệu chính thức
