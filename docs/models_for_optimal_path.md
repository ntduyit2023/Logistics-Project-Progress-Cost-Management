# 🧠 Thống Kê Các Mô Hình Tìm Đường Đi Tối Ưu cho Dự Án GLPO

> **Mục tiêu:** Liệt kê và phân tích chi tiết các mô hình (models) có thể áp dụng để tìm đường đi hợp lý (optimal/critical path) trong đồ thị dự án logistics. Các mô hình được phân chia theo 3 tầng: **Toán học thuần túy → Tối ưu hóa → AI/ML đồ thị**.

---

## 📋 Tổng Quan Nhanh: 10 Mô Hình

| #   | Mô hình                        | Loại                 | Bài toán giải                         | Thư viện Python        | Dataset phù hợp        |
| --- | ------------------------------ | -------------------- | ------------------------------------- | ---------------------- | ---------------------- |
| 1   | **CPM** (Critical Path Method) | Toán đồ thị          | Đường găng, ES/EF/LS/LF, Slack        | NetworkX, tự viết      | PSPLIB, Case Study     |
| 2   | **PERT** (3-point estimation)  | Xác suất             | Xác suất hoàn thành đúng hạn          | SciPy (stats)          | Case Study, OR&S       |
| 3   | **Topological Sort + DFS**     | Thuật toán đồ thị    | Thứ tự thực hiện, phát hiện chu trình | NetworkX               | PSPLIB, Case Study     |
| 4   | **MILP** (Mixed Integer LP)    | Tối ưu hóa chính xác | Crashing tối ưu chi phí               | PuLP, OR-Tools         | Case Study, PSPLIB J30 |
| 5   | **GA** (Genetic Algorithm)     | Meta-heuristic       | RCPSP xếp lịch giới hạn tài nguyên    | DEAP, PyGAD            | PSPLIB J30-J120        |
| 6   | **Hybrid MILP+GA**             | Tối ưu hóa lai       | Đa mục tiêu (cost + time + resource)  | PuLP + DEAP            | PSPLIB, Case Study     |
| 7   | **DAGNN**                      | GNN (Deep Learning)  | Dự đoán thời gian thực tế             | PyTorch Geometric      | PSPLIB, OR&S           |
| 8   | **GAT**                        | GNN (Attention)      | Dự báo lan truyền trễ                 | PyTorch Geometric      | OR&S, DataCo           |
| 9   | **GNN + DRL (PPO)**            | RL + GNN             | Xếp lịch thông minh (auto-dispatch)   | Stable-Baselines3, PyG | PSPLIB, VRP            |
| 10  | **Monte Carlo Simulation**     | Mô phỏng             | Phân tích rủi ro, chỉ số găng         | NumPy, SciPy           | Case Study, OR&S       |

---

## 🏗️ TẦNG 1: MÔ HÌNH TOÁN HỌC THUẦN TÚY (Classical Graph Algorithms)

> Đây là nền tảng **bắt buộc phải có** trước khi áp dụng AI. Tất cả đều chạy trên DAG (Directed Acyclic Graph).

---

### 1️⃣ CPM — Critical Path Method (Phương pháp Đường Găng)

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Deterministic Graph Algorithm |
| **Đầu vào** | DAG + duration mỗi task |
| **Đầu ra** | ES, EF, LS, LF, Total Slack, Free Slack, Critical Path |
| **Độ phức tạp** | O(V + E) — tuyến tính |
| **Thư viện** | `networkx`, hoặc tự viết (khuyến nghị để hiểu sâu) |

#### Thuật toán chi tiết

```
FORWARD PASS (Duyệt xuôi — tính ES, EF):
  1. Sắp xếp topo: order = topological_sort(DAG)
  2. Với mỗi task i theo thứ tự topo:
     ES(i) = max(EF(j)) với mọi j là predecessor của i
     EF(i) = ES(i) + duration(i)
  3. Makespan T = max(EF(i)) với mọi i

BACKWARD PASS (Duyệt ngược — tính LS, LF):
  4. Với mỗi task i theo thứ tự topo ngược:
     LF(i) = min(LS(j)) với mọi j là successor của i
     LS(i) = LF(i) - duration(i)

SLACK CALCULATION:
  5. Total Slack: TS(i) = LS(i) - ES(i)
  6. Free Slack:  FS(i) = min(ES(j)) - EF(i) với mọi j là successor
  7. Critical Path: Tất cả task có TS(i) = 0
```

#### Công thức toán học

$$ES_i = \max_{j \in \text{Pred}(i)} EF_j, \quad EF_i = ES_i + d_i$$

$$LF_i = \min_{j \in \text{Succ}(i)} LS_j, \quad LS_i = LF_i - d_i$$

$$TS_i = LS_i - ES_i = LF_i - EF_i$$

#### Áp dụng cho GLPO

| Ứng dụng | Chi tiết |
|---|---|
| **Tìm Đường Găng** | Xác định chuỗi A→C→G→I→J→N→R→T→U (Case Study) |
| **Tính Slack** | Biết task nào có dự trữ thời gian, task nào không |
| **Cơ sở cho Crashing** | Chỉ crash task trên đường găng mới giảm được Makespan |
| **Features cho GNN** | ES, EF, LS, LF, TS, FS → đầu vào node features cho DAGNN/GAT |

#### Validation với Case Study

| Kết quả mong đợi | Giá trị |
|---|---|
| Makespan | **66 ngày** |
| Critical Path | **A → C → G → I → J → N → R → T → U** |
| Slack(A) | 0 (trên đường găng) |
| Slack(B) | > 0 (có dự trữ) |

---

### 2️⃣ PERT — Program Evaluation and Review Technique

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Probabilistic CPM |
| **Đầu vào** | 3 ước lượng/task: O (lạc quan), M (khả thi nhất), P (bi quan) |
| **Đầu ra** | Expected Duration, Variance, P(hoàn thành đúng hạn) |
| **Thư viện** | `scipy.stats` (phân phối chuẩn, phân phối Beta) |

#### Công thức

$$t_e = \frac{O + 4M + P}{6} \quad \text{(Thời gian kỳ vọng)}$$

$$\sigma^2 = \left(\frac{P - O}{6}\right)^2 \quad \text{(Phương sai)}$$

$$Z = \frac{T_{deadline} - T_{project}}{\sqrt{\sum_{i \in CP} \sigma_i^2}} \quad \text{(Z-score)}$$

$$P(\text{đúng hạn}) = \Phi(Z) \quad \text{(Tra bảng phân phối chuẩn)}$$

#### Áp dụng cho GLPO

- **Nhóm 5 Features:** Phương sai thời gian (44), Ước lượng 3 điểm PERT (45)
- **Nhóm 8 Features:** Xác suất trễ hạn (62), Chỉ số găng (63)
- **Dataset:** OR&S (có actual vs planned → suy ra O, M, P), Case Study

---

### 3️⃣ Topological Sort + Cycle Detection (DFS)

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Graph Traversal Algorithm |
| **Đầu vào** | Directed Graph (adjacency list) |
| **Đầu ra** | Thứ tự topo hợp lệ, hoặc cảnh báo chu trình |
| **Độ phức tạp** | O(V + E) |
| **Thư viện** | `networkx.topological_sort()`, `networkx.is_directed_acyclic_graph()` |

#### Thuật toán Cycle Detection (3-State DFS)

```
Trạng thái: WHITE (chưa thăm), GRAY (đang thăm), BLACK (đã xong)

def has_cycle(node):
    state[node] = GRAY
    for neighbor in successors(node):
        if state[neighbor] == GRAY:
            return True  # Phát hiện chu trình!
        if state[neighbor] == WHITE:
            if has_cycle(neighbor):
                return True
    state[node] = BLACK
    return False
```

#### Áp dụng cho GLPO

- **Bắt buộc** trước khi chạy CPM: Nếu đồ thị có chu trình → CPM vô hạn
- **Nhóm 7 Features:** Lớp Topo (58), Bậc vào (55), Bậc ra (56)
- **Validation:** 21 tasks A→U phải tạo DAG hợp lệ (không có chu trình)

---

## ⚙️ TẦNG 2: MÔ HÌNH TỐI ƯU HÓA (Optimization Models)

> Các mô hình giải bài toán **tìm lịch trình tối ưu** khi có ràng buộc tài nguyên và chi phí.

---

### 4️⃣ MILP — Mixed Integer Linear Programming

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Exact Optimization (Tối ưu chính xác) |
| **Bài toán** | Project Crashing (rút ngắn tiến độ tối thiểu chi phí) |
| **Thư viện** | `PuLP` (CBC solver), `OR-Tools` (CP-SAT) |
| **Ưu điểm** | Nghiệm chính xác 100% cho bài toán nhỏ-vừa |
| **Nhược điểm** | NP-hard, chậm với >100 tasks |

#### Mô hình toán học cho Project Crashing

**Biến quyết định:**
- $S_i$: Thời điểm bắt đầu task $i$
- $d_i$: Thời gian thực hiện (có thể crash) của task $i$

**Hàm mục tiêu:**
$$\min \quad C_{max} + \sum_{i \in A} c_i^{crash} \cdot (d_i^{normal} - d_i)$$

**Ràng buộc:**
$$S_j \geq S_i + d_i \quad \forall (i,j) \in E \quad \text{(Precedence)}$$
$$d_i^{min} \leq d_i \leq d_i^{normal} \quad \forall i \quad \text{(Crash limits)}$$
$$\sum_{i \in Active(t)} r_{i,k} \leq R_k \quad \forall t, k \quad \text{(Resource capacity)}$$

#### Áp dụng cho GLPO

| Bài toán Case Study | MILP giải được |
|---|---|
| Q6a: Tìm cách outsource tối ưu | ✅ — Min cost khi chọn contractor vs company staff |
| Q6b: Crashing tuần 14→12 | ✅ — Chọn task nào OT Saturday/Sunday rẻ nhất |
| RCPSP nhỏ (J30) | ✅ — Tối ưu makespan dưới ràng buộc tài nguyên |

#### Python Code Pattern

```python
from pulp import *

prob = LpProblem("ProjectCrashing", LpMinimize)

# Biến: thời gian bắt đầu mỗi task
S = {i: LpVariable(f"S_{i}", lowBound=0) for i in tasks}

# Biến: thời gian thực hiện (có thể crash)
d = {i: LpVariable(f"d_{i}", lowBound=d_min[i], upBound=d_normal[i]) 
     for i in tasks}

# Hàm mục tiêu: minimize tổng chi phí crash
prob += lpSum(crash_cost[i] * (d_normal[i] - d[i]) for i in tasks)

# Ràng buộc precedence
for (i, j) in edges:
    prob += S[j] >= S[i] + d[i]

prob.solve()
```

---

### 5️⃣ GA — Genetic Algorithm (Thuật toán Di truyền)

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Meta-heuristic (Nghiệm gần đúng) |
| **Bài toán** | RCPSP — Resource-Constrained Project Scheduling |
| **Thư viện** | `DEAP`, `PyGAD` |
| **Ưu điểm** | Xử lý được bài toán lớn (J60, J120), phi tuyến tính |
| **Nhược điểm** | Không đảm bảo tối ưu toàn cục, cần tuning hyperparameters |

#### Kiến trúc GA cho RCPSP

```
CHROMOSOME (Nhiễm sắc thể):
  = Hoán vị thứ tự ưu tiên của các task
  Ví dụ: [A, C, B, G, D, E, F, I, K, H, J, M, L, N, O, P, Q, R, S, T, U]
  (Phải tôn trọng ràng buộc precedence)

FITNESS (Hàm thích nghi):
  = Makespan sau khi áp dụng Serial Schedule Generation Scheme (SSGS)
  Mục tiêu: MINIMIZE fitness

OPERATORS:
  - Selection:  Tournament Selection (k=3)
  - Crossover:  Order Crossover (OX) hoặc Precedence Preserving Crossover
  - Mutation:   Swap Mutation (hoán đổi 2 task, kiểm tra precedence)
  
POPULATION: 100-500 cá thể
GENERATIONS: 200-1000 thế hệ
```

#### Serial Schedule Generation Scheme (SSGS)

```
Đầu vào: priority_list (từ chromosome)
Đầu ra:  schedule (start_time mỗi task)

for task in priority_list:
    t = max(EF(predecessor)) cho mọi predecessor của task
    while resource_conflict(task, t):
        t += 1  # Lùi thời điểm bắt đầu cho đến khi đủ tài nguyên
    schedule[task] = t
```

#### Áp dụng cho GLPO

| Dataset | Kích thước | GA performance |
|---|---|---|
| Case Study (21 tasks) | Nhỏ | ~optimal trong <1 giây |
| PSPLIB J30 (30 tasks) | Vừa | Tốt, gap <5% so với optimal |
| PSPLIB J60 (60 tasks) | Trung bình | Tốt, gap <10% |
| PSPLIB J120 (120 tasks) | Lớn | Chấp nhận được, gap ~15% |

---

### 6️⃣ Hybrid MILP + GA (Tối ưu hóa Lai)

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Hybrid Optimization |
| **Ý tưởng** | Nghiệm MILP làm **hạt giống (seed)** khởi tạo GA |
| **Ưu điểm** | GA hội tụ nhanh hơn 3-5× so với random initialization |

#### Quy trình

```
Bước 1: Giải MILP relaxed (bỏ qua resource constraints)
         → Nghiệm tối ưu tuyến tính (lower bound)
         
Bước 2: Chuyển nghiệm MILP → chromosome cho GA
         → Seed 10-20% population với nghiệm MILP
         → 80-90% population còn lại = random
         
Bước 3: Chạy GA với resource constraints đầy đủ
         → GA tinh chỉnh nghiệm, xử lý xung đột tài nguyên
         
Bước 4: Kết quả = lịch trình khả thi, gần optimal
```

#### Áp dụng cho GLPO

- **Case Study Q6:** MILP giải crashing cost → GA giải resource allocation
- **Đa mục tiêu:** Minimize (Cost, Makespan, Risk) đồng thời

---

## 🤖 TẦNG 3: MÔ HÌNH AI/ML ĐỒ THỊ (Graph-Based AI Models)

> Các mô hình học sâu trên cấu trúc đồ thị, sử dụng GNN để **dự đoán** và **tối ưu hóa** trước khi thực thi.

---

### 7️⃣ DAGNN — Directed Acyclic Graph Neural Network

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Graph Neural Network (Supervised Learning) |
| **Mục đích** | Dự đoán thời gian thực tế ($d_i^{actual}$) của mỗi task |
| **Paper gốc** | ICLR 2021 — "DAGNN" |
| **GitHub** | https://github.com/vthost/DAGNN |
| **Framework** | PyTorch + PyTorch Geometric |

#### Kiến trúc

```
INPUT LAYER:
  Node features x_i = [duration, resource_demand_1..k, 
                        complexity_score, in_degree, out_degree,
                        topo_layer, es, ef]
  Edge features e_ij = [dependency_type, lag_time]

MESSAGE PASSING (theo chiều DAG — partial ordering):
  Lớp 1: h_i^(1) = σ(W_1 · AGG({h_j^(0) : j ∈ Pred(i)}) + b_1)
  Lớp 2: h_i^(2) = σ(W_2 · AGG({h_j^(1) : j ∈ Pred(i)}) + b_2)
  ...
  Lớp L: h_i^(L) = final node embedding

  ĐẶC BIỆT: Thông tin chỉ chảy theo CHIỀU CÓ HƯỚNG của cạnh
  (predecessor → successor), không phải 2 chiều như GCN thông thường

OUTPUT LAYER:
  d_i^predicted = MLP(h_i^(L))  →  Regression: dự đoán duration thực tế

LOSS FUNCTION:
  L = MSE(d_predicted, d_actual) + λ · |Makespan_pred - Makespan_actual|
```

#### Tại sao DAGNN phù hợp hơn GCN thông thường?

| Đặc tính | GCN thông thường | DAGNN |
|---|---|---|
| Hướng truyền tin | 2 chiều (undirected) | 1 chiều theo DAG |
| Partial ordering | ❌ Không hiểu thứ tự | ✅ Tôn trọng thứ tự tiên quyết |
| Áp lực tích lũy | ❌ Không tính | ✅ Tích lũy từ predecessors |
| Phù hợp project schedule | Trung bình | **Rất cao** |

#### Dataset & Training

| Giai đoạn | Dữ liệu | Mô tả |
|---|---|---|
| **Training** | PSPLIB J30-J120 + OR&S Empirical | Node features + actual duration (from OR&S) |
| **Validation** | Case Study MFET (21 tasks) | Kiểm tra: dự đoán ≈ 66 ngày |
| **Test** | OR&S unseen projects | Generalization to new project topologies |

---

### 8️⃣ GAT — Graph Attention Network

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Graph Neural Network (Attention-based) |
| **Mục đích** | Dự báo **lan truyền trễ** (Delay Propagation) trên đường găng |
| **Paper gốc** | Veličković et al. (ICLR 2018) |
| **Framework** | PyTorch Geometric (`GATConv`) |

#### Kiến trúc

```
SELF-ATTENTION trên cạnh đồ thị:

  α_ij = softmax(LeakyReLU(a^T · [W·h_i || W·h_j]))
  
  Ý nghĩa: Mỗi cạnh (i→j) có TRỌNG SỐ CHÚ Ý khác nhau
  → Task trên đường găng → trọng số cao hơn
  → Task có slack lớn   → trọng số thấp hơn

MESSAGE PASSING:
  h_i^(l+1) = σ(Σ_{j∈N(i)} α_ij · W · h_j^(l))

MULTI-HEAD ATTENTION:
  h_i^(l+1) = ||_{k=1}^{K} σ(Σ_{j∈N(i)} α_ij^k · W^k · h_j^(l))
  
  K = 4-8 attention heads (mỗi head "nhìn" từ góc độ khác nhau)

OUTPUT:
  delay_risk_i = sigmoid(MLP(h_i^(L)))  → Xác suất task i bị trễ
```

#### Lợi thế của GAT cho GLPO

| Lợi thế | Giải thích |
|---|---|
| **Explainability (Giải thích được)** | Trọng số α_ij cho biết task nào ảnh hưởng mạnh nhất đến task nào |
| **Heterogeneous connections** | Không phải mọi predecessor đều quan trọng bằng nhau → attention học được điều này |
| **Cascading delay** | Nếu task A trên đường găng trễ 2 ngày → GAT dự đoán được impact lên B, C, D... |
| **Risk visualization** | α_ij → vẽ lên đồ thị → PM thấy ngay điểm nóng |

#### Dataset phù hợp

| Dataset | Vai trò | Features sử dụng |
|---|---|---|
| OR&S Empirical | Training | Planned vs Actual duration → label delay/no-delay |
| DataCo SCM | Augmentation | Late_delivery_risk, shipping variance |
| PSPLIB | Structure | DAG topology (đa dạng kích thước) |

---

### 9️⃣ GNN + Deep Reinforcement Learning (PPO Agent)

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Reinforcement Learning + Graph Neural Network |
| **Mục đích** | Tự động xếp lịch RCPSP, thay thế priority rules thủ công |
| **Thuật toán RL** | PPO (Proximal Policy Optimization) |
| **Framework** | Stable-Baselines3 + PyTorch Geometric |

#### Kiến trúc GNN-PPO cho RCPSP

```
MÔ HÌNH HÓA MDP (Markov Decision Process):

STATE (Trạng thái):
  s_t = GNN_encode(DAG_t)
  Trong đó DAG_t = đồ thị tại thời điểm t, gồm:
  - Các task đã hoàn thành (marked as done)
  - Các task đang chạy (in progress)
  - Các task sẵn sàng (eligible: predecessors done + resource available)
  - Tài nguyên còn trống

ACTION (Hành động):
  a_t = chọn 1 task từ tập eligible tasks để bắt đầu
  (Tương đương 1 "dispatching rule" thông minh)

REWARD (Phần thưởng):
  r_t = -1 tại mỗi timestep (khuyến khích kết thúc sớm)
  HOẶC
  r_T = -Makespan tại khi kết thúc (minimize total time)

POLICY NETWORK:
  π(a|s) = PPO_network(GNN_embed(s))
  → Xác suất chọn task nào tiếp theo
```

#### So sánh với Priority Rules truyền thống

| Priority Rule | Mô tả | Hạn chế |
|---|---|---|
| **SPT** (Shortest Processing Time) | Chọn task ngắn nhất | Không xét đường găng |
| **LFT** (Latest Finish Time) | Chọn task có LF sớm nhất | Không xét tài nguyên |
| **CPT-LS** (Case Study rule) | Longest path − Late Start | Cố định, không adaptive |
| **GNN-PPO (learned)** | Học từ dữ liệu, adaptive | **Tốt hơn tất cả trên benchmark** |

#### Kết quả benchmark (từ literature)

| Dataset | SPT gap | LFT gap | **GNN-PPO gap** |
|---|---|---|---|
| PSPLIB J30 | ~12% | ~8% | **~3-5%** vs optimal |
| PSPLIB J60 | ~18% | ~14% | **~6-8%** |
| PSPLIB J120 | ~25% | ~20% | **~10-12%** |

*(gap = khoảng cách so với nghiệm tối ưu đã biết)*

#### Training Pipeline

```
1. Tạo training environment từ PSPLIB instances
2. Encode mỗi instance thành PyG Data object
3. GNN encoder: 3-layer GCN/GAT (hidden_dim=64)
4. PPO agent: actor-critic, lr=3e-4, clip=0.2
5. Train: 500,000 timesteps trên J30 → fine-tune trên J60/J120
6. Test: Evaluate makespan trên unseen instances
```

---

### 🔟 Monte Carlo Simulation (Mô phỏng Monte Carlo)

| Thuộc tính | Chi tiết |
|---|---|
| **Loại** | Stochastic Simulation |
| **Mục đích** | Phân tích rủi ro, tính Criticality Index, xác suất trễ |
| **Thư viện** | `numpy.random`, `scipy.stats` |
| **Số lần chạy** | N = 1,000 - 10,000 lần mô phỏng |

#### Thuật toán

```
for sim in range(N):
    # 1. Sinh ngẫu nhiên duration cho mỗi task
    for task in tasks:
        d[task] = sample_from_distribution(O, M, P)  # Beta/Triangular
    
    # 2. Chạy CPM với duration ngẫu nhiên
    makespan[sim], critical_path[sim] = run_CPM(graph, d)

# 3. Thống kê kết quả
mean_makespan = mean(makespan)
std_makespan  = std(makespan)
P(on_time)    = count(makespan <= deadline) / N

# 4. Criticality Index cho mỗi task
for task in tasks:
    CI[task] = count(task in critical_path[sim]) / N
    # CI = 1.0 → luôn trên đường găng (100% critical)
    # CI = 0.3 → 30% thời gian nằm trên đường găng
```

#### Áp dụng cho GLPO

| Feature GLPO | Công thức Monte Carlo |
|---|---|
| Chỉ số găng (63) | CI = count(task ∈ CP) / N |
| Chỉ số nhạy cảm (64) | Correlation(d_task, Makespan) |
| Xác suất trễ hạn (62) | P(Makespan > Deadline) |
| Phương sai thời gian (44) | Var(d_task) từ N simulations |

---

## 📊 MA TRẬN SO SÁNH TỔNG HỢP

### Theo bài toán GLPO

| Bài toán | Model tốt nhất | Model hỗ trợ |
|---|---|---|
| **Tìm đường găng (Critical Path)** | CPM | Topo Sort, Monte Carlo |
| **Xếp lịch giới hạn tài nguyên (RCPSP)** | GA, GNN+PPO | MILP (small), Hybrid |
| **Rút ngắn tiến độ (Crashing)** | MILP | Hybrid MILP+GA |
| **Dự đoán trễ tiến độ** | GAT, DAGNN | Monte Carlo, PERT |
| **Phân tích rủi ro** | Monte Carlo | GAT, PERT |
| **Tối ưu đa mục tiêu (cost+time+risk)** | Hybrid MILP+GA | GNN+PPO |
| **Xếp lịch real-time (adaptive)** | GNN+PPO | GAT |

### Theo Pha GLPO

| Pha | Models sử dụng | Dataset |
|---|---|---|
| **Pha 1** — Core DAG Engine | CPM, Topo Sort, Cycle Detection | Case Study, PSPLIB J30 |
| **Pha 2** — Database & API | (Lưu kết quả models) | Case Study → PostgreSQL |
| **Pha 3** — Optimizer | MILP, GA, Hybrid MILP+GA | PSPLIB J30-J120, Case Study |
| **Pha 4** — Frontend UI | (Hiển thị kết quả models) | Case Study (demo) |
| **Pha 5** — AI Predictive | DAGNN, GAT, GNN+PPO, Monte Carlo | OR&S, PSPLIB, DataCo |

### Theo độ khó triển khai

| Mức độ | Models | Thời gian ước tính |
|---|---|---|
| ⭐ Dễ (Pure Python) | CPM, Topo Sort, PERT, Monte Carlo | 1-2 tuần |
| ⭐⭐ Trung bình (Thư viện) | MILP (PuLP), GA (DEAP) | 2-3 tuần |
| ⭐⭐⭐ Khó (Deep Learning) | DAGNN, GAT | 3-4 tuần |
| ⭐⭐⭐⭐ Nâng cao (RL) | GNN+PPO, Hybrid MILP+GA | 4-6 tuần |

---

## 🔧 Stack Công Nghệ Đề Xuất

```
Python 3.10+
├── networkx          # Đồ thị cơ bản, CPM, Topo Sort
├── numpy / scipy     # Tính toán số, phân phối xác suất, Monte Carlo
├── PuLP              # MILP solver (miễn phí, dùng CBC)
├── DEAP              # Genetic Algorithm framework
├── torch             # PyTorch core
├── torch_geometric   # PyTorch Geometric (GNN: DAGNN, GAT)
├── stable-baselines3 # PPO agent cho Reinforcement Learning
├── psplib            # Parser cho PSPLIB benchmark
├── matplotlib        # Visualization (Gantt chart, graphs)
└── pandas            # Data manipulation
```

---

## 📚 Tài Liệu Tham Khảo Chính

| # | Tài liệu | Nội dung | Link |
|---|---|---|---|
| 1 | DAGNN (ICLR 2021) | GNN cho DAG | https://github.com/vthost/DAGNN |
| 2 | GAT (Veličković 2018) | Graph Attention Networks | https://arxiv.org/abs/1710.10903 |
| 3 | Wheatley (2025) | GNN+DRL cho RCPSP | https://arxiv.org/abs/2309.07828 |
| 4 | DEAP Documentation | GA framework | https://deap.readthedocs.io |
| 5 | PuLP Documentation | MILP solver | https://coin-or.github.io/pulp/ |
| 6 | PyTorch Geometric | GNN framework | https://pyg.org |
| 7 | Stable-Baselines3 | PPO implementation | https://stable-baselines3.readthedocs.io |
| 8 | PSPLIB | Benchmark dataset | https://www.om-db.wi.tum.de/psplib |
| 9 | OR&S UGent | Empirical PM data | https://www.or-as.be/downloads |
| 10 | Vanhoucke (2012) | Project Scheduling book | ISBN: 978-1-4614-4684-5 |
