# ⚡ Phương Pháp Tối Ưu Hóa Đồ Thị Cho Dự Án GLPO

Tài liệu này phân tích chuyên sâu **lý thuyết, nguyên lý hoạt động, và ví dụ thực tế** của các phương pháp tối ưu hóa xếp lịch dự án trên đồ thị DAG: từ phương pháp chính xác (MILP), đến meta-heuristic (GA), và chiến lược kết hợp lai (Hybrid).

---

## 1. Toàn Cảnh Bài Toán Tối Ưu Trên Đồ Thị DAG

### 1.1 Ba bài toán cốt lõi

Khi mô hình hóa dự án logistics thành đồ thị DAG, có **3 bài toán tối ưu chính** cần giải quyết, xếp theo độ khó tăng dần:

| # | Bài toán | Mô tả | Độ khó | Ví dụ thực tế |
|---|---------|-------|--------|---------------|
| 1 | **CPM Scheduling** | Tìm đường găng, tính thời gian dự trữ | Polynomial — giải được nhanh | "Dự án 21 tasks, tìm đường găng A→C→G→I→J→N→R→T→U = 66 ngày" |
| 2 | **Crashing** | Rút ngắn tiến độ với chi phí tối thiểu | LP/MILP — giải được chính xác | "Rút từ 14 tuần xuống 12 tuần, chi thêm $4,500 OT thay vì bị phạt $4,000" |
| 3 | **RCPSP** | Xếp lịch khi tài nguyên bị giới hạn | **NP-Hard** — cực kỳ khó | "21 tasks nhưng chỉ có 1 Design_Comp → phải xếp tuần tự → 96 ngày" |

### 1.2 Tại sao RCPSP là NP-Hard?

Hãy hình dung bạn có 21 tasks cần xếp lịch. Với bài toán CPM thuần túy, bạn chỉ cần respect ràng buộc tiên quyết — có đúng 1 cách tính (forward/backward pass). Nhưng khi thêm ràng buộc tài nguyên:

**Ví dụ cụ thể từ Case Study:**
> Tại ngày thứ 10, cả 3 tasks B, D, E đều "eligible" (đủ predecessors). Nhưng:
> - B cần Design_Comp (1/1 available)
> - D cần Dev_Mech (1/1 available)  
> - E cần Design_Comp + Design_Mech + Dev_Mech (cần 3 slots, chỉ có 3)
>
> Nếu B và D chạy song song → E phải chờ (B chiếm Design_Comp, D chiếm Dev_Mech).
> Nếu E chạy trước → B và D phải chờ.
>
> Mỗi quyết định "ai trước ai sau" tại mỗi thời điểm tạo ra **một nhánh cây quyết định**. Với 21 tasks, số lượng tổ hợp có thể lên đến hàng triệu → không thể thử hết trong thời gian hợp lý.

Đây chính là bản chất NP-Hard: **không có thuật toán nào giải chính xác trong thời gian đa thức** cho mọi trường hợp.

### 1.3 Hệ quả: Cần nhiều phương pháp bổ trợ nhau

```
Quy mô nhỏ (< 30 tasks):
  → MILP giải chính xác trong vài giây ✅
  → Case Study 21 tasks thuộc nhóm này

Quy mô vừa (30-100 tasks):
  → MILP có thể mất vài phút đến vài giờ
  → GA hoặc CP-SAT cho kết quả gần tối ưu trong vài giây

Quy mô lớn (> 100 tasks):
  → MILP không khả thi (timeout)
  → GA/RL là lựa chọn duy nhất
  → Dự án logistics thực tế thường ở quy mô này
```

---

## 2. MILP — Mixed-Integer Linear Programming

### 2.1 Nguyên lý cốt lõi

MILP (Quy hoạch tuyến tính nguyên hỗn hợp) là phương pháp **chính xác toán học** — nếu tìm được nghiệm, đó chắc chắn là **nghiệm tối ưu toàn cục** (global optimal).

**Hình dung bằng phép ẩn dụ:**
> Hãy tưởng tượng bạn đang ở đỉnh núi và muốn tìm **điểm thấp nhất trong thung lũng** (chi phí tối thiểu). MILP giống như có bản đồ 3D chính xác của toàn bộ địa hình — bạn tính toán toán học và chỉ ra chính xác điểm thấp nhất. Không cần leo trèo, không cần thử nghiệm. Nhưng nếu địa hình quá phức tạp (nhiều thung lũng nhỏ, nhiều gờ đá), việc vẽ bản đồ 3D sẽ mất rất lâu.

### 2.2 Ba thành phần của MILP

Mọi bài toán MILP đều có 3 phần:

#### A. Biến quyết định — "Bạn cần quyết định gì?"

Trong bài toán crashing cho GLPO:
*   **Thời điểm bắt đầu** mỗi task: "Task F bắt đầu ngày nào?"
*   **Số ngày làm thêm Thứ 7** cho mỗi task: "Task I làm thêm mấy ngày T7?"
*   **Số ngày làm thêm Chủ Nhật** cho mỗi task: "Task I làm thêm mấy ngày CN?"
*   **Có thuê ngoài hay không** cho mỗi vị trí: "Dev_Mech cho task D — thuê hay không?"

#### B. Hàm mục tiêu — "Bạn muốn tối ưu cái gì?"

$$\text{Tối thiểu hóa Tổng Chi Phí} = \underbrace{\text{Chi phí OT}}_{\text{Tăng khi crash}} + \underbrace{500 \times W}_{\text{Giảm khi ngắn hơn}} + \underbrace{\text{Phạt}}_{\text{Giảm khi ≤ 12 tuần}} - \underbrace{\text{Thưởng}}_{\text{Tăng khi < 12 tuần}}$$

**Ví dụ tính toán:**
> Nếu crash 5 ngày → dự án rút từ 14 xuống 13 tuần:
> - Chi phí OT: +$1,710 (crash 5 tasks rẻ nhất)
> - Overhead: $500 × 13 = $6,500 (giảm $500 so với 14 tuần)
> - Penalty: $2,000 × 1 = $2,000 (chỉ trễ 1 tuần so với mốc 12)
> - Bonus: $0
> - **Tổng = Base + $10,210**
>
> Nếu KHÔNG crash → 14 tuần:
> - Chi phí OT: $0
> - Overhead: $500 × 14 = $7,000
> - Penalty: $2,000 × 2 = $4,000
> - **Tổng = Base + $11,000**
>
> → Crash 5 ngày **tiết kiệm $790**. MILP tìm ra con số chính xác này.

#### C. Ràng buộc — "Quy tắc bắt buộc phải tuân theo"

| Loại ràng buộc | Ý nghĩa | Ví dụ |
|----------------|---------|-------|
| **Tiên quyết** | Task con chỉ bắt đầu sau khi task cha hoàn thành | "H chỉ bắt đầu sau khi CẢ E và F đều xong" |
| **Crash tối đa** | Không thể crash vô hạn | "Task I (16 ngày) crash tối đa 3 ngày T7 + 1 ngày CN = 4 ngày" |
| **Thứ tự OT** | Phải dùng hết T7 trước khi dùng CN | "Nếu I chỉ crash 2 ngày → bắt buộc phải là 2 ngày T7, không được 2 ngày CN" |
| **Tài nguyên** | Số nhân sự tại mỗi thời điểm ≤ giới hạn | "Tối đa 1 Design_Comp làm việc cùng lúc" |
| **Phi âm** | Thời gian không thể âm | "Mọi task bắt đầu từ ngày 0 trở đi" |

### 2.3 Solver hoạt động như thế nào?

MILP solver (như CBC, GLPK, Gurobi) sử dụng thuật toán **Branch-and-Bound**:

1.  **Relaxation:** Đầu tiên, bỏ qua ràng buộc "nguyên" (integer) → giải LP relaxation → được lower bound
2.  **Branching:** Chọn biến nguyên có giá trị phân số (ví dụ: x_sat = 1.7) → tạo 2 nhánh: x_sat ≤ 1 và x_sat ≥ 2
3.  **Bounding:** Mỗi nhánh giải LP relaxation → nếu giá trị ≥ nghiệm tốt nhất hiện tại → cắt bỏ nhánh (không cần khám phá thêm)
4.  **Lặp lại** cho đến khi tìm được nghiệm tối ưu

**Ví dụ minh họa:**
> Ban đầu, solver relaxation nói: "Chi phí tối thiểu có thể là $68,000." 
> Sau branching: "Nếu crash I = 2 ngày T7, chi phí = $69,500."
> Nhánh khác: "Nếu crash I = 3 ngày T7, chi phí = $69,200."
> Tiếp tục: "Nếu crash I = 3 T7 + crash G = 2 T7, chi phí = $70,100."
> ...Cuối cùng: **Nghiệm tối ưu: crash N(1T7) + G(2T7) + I(2T7) = $70,230** (không nhánh nào tốt hơn).

### 2.4 Ưu điểm & Hạn chế

| ✅ Ưu điểm | ❌ Hạn chế |
|-----------|-----------|
| Đảm bảo nghiệm tối ưu toàn cục — "không thể tốt hơn" | Chậm khi quy mô lớn (> 50 tasks + nhiều resource types) |
| Deterministic — cùng đầu vào luôn cho cùng kết quả | Chỉ xử lý được ràng buộc **tuyến tính** |
| Dễ thêm/bớt ràng buộc mới | Cần kiến thức toán tối ưu để formulate |
| Thư viện Python dễ dùng (PuLP, OR-Tools) | "Big-M" constraints có thể gây lỗi số |

### 2.5 Thư viện Python cho MILP

| Thư viện | Solver | Phù hợp cho |
|----------|--------|-------------|
| **PuLP** | CBC (mặc định, miễn phí) | Bài toán nhỏ-vừa, dễ học |
| **Google OR-Tools** | SCIP, GLPK, CBC | Bài toán vừa-lớn, nhiều tính năng |
| **Gurobi** | Gurobi (thương mại) | Bài toán lớn, hiệu suất cao nhất |
| **CVXPY** | Nhiều solver | Bài toán convex, giao diện toán học |

---

## 3. GA — Genetic Algorithm (Thuật Toán Di Truyền)

### 3.1 Nguyên lý cốt lõi — Tiến hóa tự nhiên

GA mô phỏng quá trình **chọn lọc tự nhiên** của Darwin: tạo ra một "quần thể" (population) các giải pháp ứng cử viên, cho chúng "cạnh tranh sinh tồn", "lai ghép" và "đột biến" qua nhiều thế hệ. Qua thời gian, quần thể **tiến hóa** về phía giải pháp tốt hơn.

**Hình dung:**
> Bạn có 100 PM (Project Manager) khác nhau, mỗi người đề xuất một cách xếp lịch riêng. Bạn cho họ thi đấu: PM nào đưa ra lịch trình có makespan ngắn nhất → "sống sót". Hai PM giỏi nhất kết hợp ý tưởng → tạo ra PM thế hệ mới. Thỉnh thoảng, một PM đột nhiên có ý tưởng hoàn toàn mới (đột biến). Sau 200 thế hệ, PM cuối cùng sẽ rất giỏi.

### 3.2 Bốn thành phần GA cho RCPSP

#### A. Chromosome (Nhiễm sắc thể) — Biểu diễn một giải pháp

Mỗi "cá thể" trong quần thể là một **priority list** — thứ tự ưu tiên xếp lịch cho 21 tasks.

**Ví dụ:**
> Chromosome 1: [A, C, B, G, D, E, F, I, K, H, J, L, M, O, P, N, Q, R, T, S, U]
> "Xếp A trước, rồi C, rồi B, rồi G... Khi có xung đột tài nguyên, task đứng trước trong danh sách được ưu tiên."
>
> Chromosome 2: [A, B, D, C, E, K, G, F, H, I, L, M, J, O, P, N, Q, R, S, T, U]
> "Ưu tiên nhánh hardware (B, D, K) trước, rồi mới đến software."

**Quy tắc bắt buộc:** Mọi chromosome phải là **thứ tự topo hợp lệ** — tức là task cha luôn đứng trước task con. Ví dụ: [B, A, C, ...] là **vi phạm** vì A là prerequisite của B nhưng lại đứng sau.

#### B. Fitness Function — Đánh giá chất lượng

Mỗi chromosome được **decode** thành lịch trình thực tế bằng **Serial Schedule Generation Scheme (SSGS)**:

1.  Lấy task đầu tiên từ priority list
2.  Tìm thời điểm sớm nhất có thể bắt đầu:
    *   ✅ Tất cả predecessors đã hoàn thành?
    *   ✅ Đủ tài nguyên available tại thời điểm đó?
3.  Gán start time và finish time
4.  Lặp lại cho task tiếp theo trong list

**Fitness = Makespan** (thời gian hoàn thành cuối cùng) — càng nhỏ càng tốt.

**Ví dụ:**
> Chromosome 1 → SSGS decode → Makespan = 72 ngày (Fitness = -72)
> Chromosome 2 → SSGS decode → Makespan = 68 ngày (Fitness = -68, **tốt hơn**)

#### C. Crossover (Lai ghép) — Kết hợp ý tưởng tốt

Hai "cha mẹ" giỏi kết hợp DNA để tạo "con" mới:

**Ví dụ Precedence Preserving Crossover:**
> Parent 1: [A, **C**, B, **G**, D, E, **F**, **I**, K, H, ...]
> (Ưu tiên nhánh Software: C, G, F, I đứng sớm)
>
> Parent 2: [A, **B**, **D**, C, **E**, **K**, G, F, H, I, ...]
> (Ưu tiên nhánh Hardware: B, D, E, K đứng sớm)
>
> Child: [A, C, B, D, G, E, F, K, I, H, ...]
> (Kết hợp: vẫn ưu tiên C sớm từ P1, nhưng chen D, E sớm hơn từ P2)

**Quy tắc:** Con phải giữ nguyên thứ tự topo hợp lệ — nếu crossover tạo ra thứ tự vi phạm, phải sửa lại.

#### D. Mutation (Đột biến) — Khám phá ý tưởng mới

Thỉnh thoảng (xác suất ~10-20%), đổi chỗ ngẫu nhiên 2 tasks trong chromosome — miễn là kết quả vẫn topo hợp lệ.

**Ví dụ:**
> Trước: [..., G, D, E, F, K, I, H, ...]
> Đổi D ↔ F: [..., G, F, E, D, K, I, H, ...]  ← OK (cả D và F đều ở cùng layer topo)
> Đổi A ↔ I: **Không được** (A là ancestor của I, không thể đổi vị trí)

### 3.3 Ví dụ thực tế — GA cho kho bãi logistics

**Bài toán:** Công ty ABC Logistics mở rộng 3 trung tâm phân phối đồng thời, tổng cộng 80 tasks, 12 loại tài nguyên (kỹ sư xây dựng, xe cẩu, nhà thầu phụ điện, nước...). MILP chạy 2 giờ vẫn chưa tìm được nghiệm tối ưu.

**GA giải quyết:**
*   Quần thể: 200 chromosomes
*   200 thế hệ: ~15 giây chạy
*   Nghiệm tốt nhất: Makespan = 145 ngày (so với CPM lý thuyết 120 ngày)
*   GA không đảm bảo 145 là tối ưu, nhưng **đủ tốt** so với thời gian chờ 2 giờ+ của MILP

### 3.4 Selection — Chọn lọc

Có nhiều chiến lược chọn "cha mẹ" cho thế hệ tiếp theo:

| Chiến lược | Cách hoạt động | Ưu/nhược |
|-----------|----------------|----------|
| **Tournament** | Chọn k cá thể ngẫu nhiên, giữ tốt nhất | Dễ triều chỉnh áp lực chọn lọc (k lớn = khắc nghiệt hơn) |
| **Roulette Wheel** | Xác suất được chọn tỷ lệ thuận fitness | Cá thể tốt có nhiều cơ hội hơn nhưng không chắc chắn |
| **Elitism** | Luôn giữ lại top-N tốt nhất qua thế hệ | Đảm bảo không mất nghiệm tốt nhất |

**Đề xuất cho GLPO:** Kết hợp **Tournament (k=3) + Elitism (top 5%)** — vừa đa dạng vừa giữ được nghiệm tốt.

### 3.5 Ưu điểm & Hạn chế

| ✅ Ưu điểm | ❌ Hạn chế |
|-----------|-----------|
| Xử lý tốt bài toán NP-Hard — GA không cần biết bài toán "dạng gì" | Không đảm bảo tối ưu toàn cục — chỉ "gần tối ưu" |
| Rất linh hoạt — dễ thêm ràng buộc phi tuyến, đa mục tiêu | Cần tuning hyperparameters (pop_size, cxpb, mutpb, ngen) |
| Song song hóa tự nhiên — mỗi chromosome evaluate độc lập | Kết quả không deterministic — chạy 2 lần cho 2 kết quả khác nhau |
| Tốc độ nhanh cho quy mô lớn | Có thể mắc kẹt local optima nếu quần thể thiếu đa dạng |

---

## 4. Hybrid MILP + GA — Phương Pháp Lai (Đề Xuất Chính Cho GLPO)

### 4.1 Tại sao cần kết hợp?

Mỗi phương pháp có **điểm mạnh bù trừ** cho nhau:

**Hạn chế nếu chỉ dùng MILP:**
> Khi giải RCPSP cho Case Study 21 tasks với đầy đủ 8 loại resource constraints + overtime + subcontracting, MILP phải xử lý hàng nghìn biến binary → solver có thể mất 10-30 phút. Với dự án 100+ tasks → timeout.

**Hạn chế nếu chỉ dùng GA:**
> Quần thể khởi tạo ngẫu nhiên → GA mất 50-100 thế hệ đầu tiên chỉ để "đi vào vùng khả thi" (tìm các chromosome cho makespan chấp nhận được). Lãng phí thời gian tính toán.

**Giải pháp Hybrid:**
> Dùng MILP giải bài toán **đơn giản hóa** (relaxation) → lấy nghiệm tốt nhất → chuyển thành chromosome → "gieo hạt" vào quần thể GA. GA bắt đầu từ vùng tốt → hội tụ nhanh gấp 2-3 lần.

### 4.2 Pipeline Hybrid chi tiết

```
Stage 1: MILP Relaxation (Gieo hạt — Seed Generation)
══════════════════════════════════════════════════════
Input:  DAG dự án + Ràng buộc tài nguyên (đơn giản hóa)
Process: Giải MILP với ràng buộc nới lỏng
         (VD: bỏ qua resource constraints phức tạp,
         chỉ giữ precedence + crashing)
Output: Nghiệm tối ưu cho bài toán đơn giản
        → Chuyển thành priority list (seed chromosome)
Thời gian: ~1-5 giây

         │ Seed chromosome
         ↓

Stage 2: GA Evolution (Tinh chỉnh — Refinement)
══════════════════════════════════════════════════════
Input:  Quần thể 100 chromosomes:
        - 10 seeds từ MILP (10%)
        - 90 random topo-feasible (90%)
Process: Evolve 200 generations
        - Selection: Tournament(k=3) + Elitism(5%)
        - Crossover: Precedence-preserving (cxpb=0.7)
        - Mutation: Topo-feasible swap (mutpb=0.2)
        - Fitness: SSGS decode → đầy đủ resource constraints
Output: Best chromosome → Lịch trình tối ưu
Thời gian: ~5-15 giây

         │ Best solution
         ↓

Output: Lịch trình + Chi phí tối ưu + Gantt Chart
```

### 4.3 Ví dụ minh họa từ Case Study

**Bước 1 — MILP Seed:**
> MILP giải bài toán crashing đơn giản (chỉ precedence, không resource limits):
> - Nghiệm: Crash N(1 ngày T7, +$300), crash G(2 ngày T7, +$690), crash I(2 ngày T7, +$840)
> - Makespan: 61 ngày → 12.2 tuần
> - Priority list gợi ý: [A, C, G, I, B, D, J, E, K, F, N, H, M, L, O, P, Q, R, T, S, U]

**Bước 2 — GA Evolution:**
> 10 seeds MILP + 90 random chromosomes.
> Thế hệ 1: Best makespan = 68 ngày (seed MILP), Worst = 85 ngày (random)
> Thế hệ 50: Best = 66 ngày (GA đã refine seed bằng cách thay đổi thứ tự H, K)
> Thế hệ 100: Best = 64 ngày (GA tìm được cách xen kẽ HW/SW tasks hiệu quả hơn)
> Thế hệ 200: Best = 64 ngày (đã hội tụ)

**So sánh nếu chỉ dùng GA:**
> Thế hệ 1: Best = 82 ngày (random), Worst = 96 ngày
> Thế hệ 50: Best = 74 ngày (vẫn đang khám phá)
> Thế hệ 100: Best = 68 ngày (mới bằng seed MILP ban đầu!)
> Thế hệ 200: Best = 65 ngày
>
> → GA thuần mất **gấp đôi** số thế hệ để đạt cùng chất lượng.

### 4.4 Bảng so sánh hiệu suất

| Metric | MILP Only | GA Only | **Hybrid** |
|--------|-----------|---------|--------|
| **Thời gian giải (21 tasks)** | ~1-5s | ~5-10s | ~3-8s |
| **Thời gian giải (100 tasks)** | Timeout (>30 min) | ~30s | ~20s |
| **Chất lượng nghiệm** | 100% Optimal | 95-98% | **98-100%** |
| **Xử lý resource constraints** | Khó (cần Big-M) | ✅ Tốt | ✅ Tốt |
| **Xử lý phi tuyến** | ❌ Không | ✅ Tốt | ✅ Tốt |
| **Deterministic** | ✅ Có | ❌ Không | ❌ Không |

---

## 5. Constraint Programming (CP) — Phương Pháp Bổ Trợ

### 5.1 Nguyên lý

CP (Constraint Programming) là phương pháp **chính xác** nhưng tiếp cận khác MILP. Thay vì formulate thành bất đẳng thức tuyến tính, CP khai báo trực tiếp ràng buộc bằng ngôn ngữ tự nhiên hơn.

**Hình dung:**
> MILP giống viết bài toán bằng **phương trình đại số** — chính xác nhưng phức tạp.
> CP giống nói bằng **lời** — "Task A phải xong trước Task B" thay vì "start_B >= start_A + duration_A".

### 5.2 Ưu thế của CP cho scheduling

CP-SAT solver (Google OR-Tools) đặc biệt mạnh cho scheduling vì có các constraint **tích hợp sẵn**:

| Constraint tích hợp | Ý nghĩa | MILP phải làm gì? |
|---------------------|---------|-------------------|
| **Interval Variables** | Biến đại diện cho khoảng thời gian (start, duration, end) | Phải tạo 3 biến + 2 ràng buộc thủ công |
| **NoOverlap** | Hai tasks không được chồng lịch | Cần Big-M constraints phức tạp |
| **Cumulative** | Tổng tài nguyên tại mỗi thời điểm ≤ giới hạn | Cần biến time-indexed + nhiều ràng buộc |

### 5.3 Khi nào dùng CP thay MILP?

*   **CP tốt hơn:** RCPSP (nhiều resource types), scheduling với nhiều ràng buộc logic (if-then)
*   **MILP tốt hơn:** Crashing optimization (nhiều biến liên tục), bài toán chi phí tuyến tính

### 5.4 Thư viện: Google OR-Tools CP-SAT
*   Miễn phí, hiệu suất cao, hỗ trợ Python
*   Thường **nhanh hơn CBC/GLPK** gấp 5-10 lần cho scheduling

---

## 6. Simulated Annealing & Ant Colony — Các Phương Pháp Bổ Sung

### 6.1 Simulated Annealing (SA) — Luyện kim

**Nguyên lý:** Mô phỏng quá trình nung nóng và làm nguội kim loại. Ở nhiệt độ cao (đầu quá trình), chấp nhận cả giải pháp kém hơn để tránh mắc kẹt. Nhiệt độ giảm dần → chỉ chấp nhận cải thiện.

**Ví dụ:** Ở thế hệ đầu (T=100), SA có thể chuyển từ lịch 68 ngày sang lịch 72 ngày (xấu hơn) với xác suất 60% — để "nhảy" ra khỏi local optimum. Ở cuối (T=1), xác suất chấp nhận xấu hơn chỉ còn 2%.

**Khi nào dùng:** Prototype nhanh, ít hyperparameters hơn GA, phù hợp khi muốn thử nghiệm ý tưởng trước khi đầu tư vào GA/MILP.

### 6.2 Ant Colony Optimization (ACO) — Đàn kiến

**Nguyên lý:** Đàn kiến tìm đường ngắn nhất đến nguồn thức ăn bằng cách để lại **pheromone** (mùi hóa chất) trên đường đi. Đường tốt → nhiều kiến đi qua → nhiều pheromone → càng nhiều kiến chọn → tự tăng cường (positive feedback).

**Ứng dụng:** Đặc biệt phù hợp cho **bài toán routing** trong logistics (VRP — Vehicle Routing Problem). Kém hiệu quả hơn GA cho scheduling thuần túy.

---

## 7. Bảng So Sánh Tổng Hợp Toàn Bộ Phương Pháp

| Phương pháp | Loại | Tối ưu? | Quy mô | Ưu điểm chính | Nhược điểm chính | Phù hợp cho |
|-------------|------|:-------:|:------:|---------------|-----------------|-------------|
| **MILP** | Exact | ✅ Global | Nhỏ | Chính xác tuyệt đối | Chậm khi lớn | Crashing |
| **CP-SAT** | Exact | ✅ Global | Vừa | Nhanh cho scheduling | Ít phổ biến | RCPSP |
| **GA** | Meta | 🟡 Near | Lớn | Linh hoạt, nhanh | Cần tuning | RCPSP lớn |
| **SA** | Meta | 🟡 Near | Vừa-Lớn | Đơn giản | Chậm hội tụ | Prototype |
| **ACO** | Meta | 🟡 Near | Lớn | Routing tuyệt vời | Kém cho scheduling | VRP |
| **GNN+RL** | Learning | 🟡 Learned | Lớn | Xử lý bất định | Cần data/train | Uncertain RCPSP |
| **Hybrid** | Combined | ✅ Near-global | Mọi quy mô | Tốt nhất tổng thể | Phức tạp triển khai | **GLPO** |

---

## 📚 8. Tài Liệu Tham Khảo

### Papers:
1.  **Kolisch & Hartmann (2006).** *"Experimental Investigation of Heuristics for RCPSP."* European Journal of Operational Research. → Benchmark GA operators cho RCPSP.
2.  **Brucker et al. (1999).** *"Resource-Constrained Project Scheduling: Notation, Classification, Models, and Methods."* → Phân loại toàn diện RCPSP.
3.  **Kelley & Walker (1959).** *"Critical-Path Planning and Scheduling."* → Paper gốc CPM.
4.  **Deb et al. (2002).** *"A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II."* → GA đa mục tiêu.

### Thư viện Python:
*   **PuLP** — MILP solver interface, solver mặc định CBC (miễn phí)
*   **Google OR-Tools** — CP-SAT solver, mạnh nhất cho scheduling
*   **DEAP** — Distributed Evolutionary Algorithms in Python (GA framework)
*   **NetworkX** — Graph algorithms (Topo Sort, Longest Path, CPM)
