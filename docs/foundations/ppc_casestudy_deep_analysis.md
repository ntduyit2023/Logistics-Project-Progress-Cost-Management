# 📋 Phân Tích Sâu PPC Case Study (MFET 3008/5040)

Tài liệu này mở rộng và phân tích chuyên sâu toàn bộ nội dung của **PPC_casestudy_2010_V1.pdf**, bao gồm bối cảnh dự án, phân tích chi tiết từng câu hỏi (Q1-Q7), tính toán đầy đủ CPM, biểu đồ tài nguyên, phương pháp giải từng bước, và kết quả đối chứng (ground truth).

---

## 1. Bối Cảnh Dự Án (Project Context)

### 1.1 Mô tả dự án
Công ty **Conveyer Systems Ltd (CSL)** là nhà cung cấp hệ thống băng chuyền tích hợp cho ngành công nghiệp. Dự án là thiết kế, phát triển và lắp đặt một hệ thống phân loại hàng hóa tự động (Automated Sorting System) bao gồm:
*   **Phần cứng (Hardware):** Băng chuyền cơ khí, cảm biến, actuators
*   **Phần mềm (Software):** Hệ điều hành điều khiển, giao diện hệ thống
*   **Tích hợp (Integration):** Kết nối HW/SW, kiểm thử hệ thống

### 1.2 Quy mô & Ràng buộc
| Thông số | Giá trị |
|----------|---------|
| Tổng số hoạt động | **21 (A → U)** |
| Số nhóm kỹ năng nhân sự | **8 nhóm** |
| Tổng nhân sự nội bộ | **10 người** |
| Tuần làm việc | **5 ngày** (Thứ 2 → Thứ 6) |
| Overhead (chi phí gián tiếp) | **$500/tuần** |
| Deadline mục tiêu | **12 tuần** (60 ngày làm việc) |
| Tiền phạt trễ | **$2,000/tuần** |
| Tiền thưởng sớm | **$3,000/tuần** |

### 1.3 Chuỗi câu hỏi đề bài (Q1 → Q7)
```
Q1: Vẽ sơ đồ AON → Xác định cấu trúc đồ thị DAG
Q2: Tính CPM (ES, EF, LS, LF, Slack) → Tìm đường găng
Q3: Vẽ Gantt Chart → Trực quan hóa lịch trình
Q4: Vẽ biểu đồ tài nguyên (Resource Histogram) → Phát hiện xung đột
Q5: Giải RCPSP → Xếp lịch khi tài nguyên bị giới hạn
Q6a: Tính chi phí thuê ngoài (Subcontracting)
Q6b: Tối ưu hóa crashing (Overtime scheduling)
Q7: Phân tích EVM (Earned Value Management) tại tuần 5
```

---

## 2. Phân Tích Chi Tiết Đồ Thị DAG (Q1)

### 2.1 Bảng tổng hợp 21 hoạt động

| Task | Tên đầy đủ | Duration (ngày) | Predecessors | Nhóm HW/SW |
|:---:|---|:---:|---|:---:|
| **A** | Architectural decisions | 4 | — | Chung |
| **B** | Hardware specifications | 6 | A | HW |
| **C** | Software specifications | 7 | A | SW |
| **D** | Conveyor design | 8 | B | HW |
| **E** | Hardware design | 6 | B | HW |
| **F** | Software design | 12 | C | SW |
| **G** | Operating system documentation | 10 | C | SW |
| **H** | Hardware detail drawings | 8 | E, F | HW+SW |
| **I** | Software programming | 16 | G | SW |
| **J** | Software verification/testing | 12 | I | SW |
| **K** | Conveyor detailed drawings | 7 | D | HW |
| **L** | Drawing verification/Minor integration | 9 | H, K | Tích hợp |
| **M** | Prototype development | 4 | H | HW |
| **N** | Prototype installation | 7 | J, M | Tích hợp |
| **O** | Hardware order/delivery | 7 | L | HW |
| **P** | System Interface | 5 | L | Tích hợp |
| **Q** | Hardware assembly | 4 | O, P | HW |
| **R** | Hardware/software Integration | 5 | N, Q | Tích hợp |
| **S** | Hardware/software documentation | 2 | R | Doc |
| **T** | System verification | 3 | R | Tích hợp |
| **U** | Acceptance test | 2 | S, T | Final |

### 2.2 Phân tích cấu trúc đồ thị

```
Topology Analysis:
─────────────────
  Tổng nodes: 21
  Tổng edges: 25 (mối quan hệ phụ thuộc)
  Nút nguồn (Source): A (in-degree = 0)
  Nút đích (Sink): U (out-degree = 0)
  Chiều rộng tối đa (Max Width): 4 nodes (layer D,E,F,G)
  Chiều sâu tối đa (Max Depth): 10 layers
  
  Nút hội tụ (Merge nodes): H(2), L(2), N(2), Q(2), R(2), U(2)
  → 6 merge nodes = 6 điểm chờ đồng bộ (synchronization points)
  
  Nút phân nhánh (Fork nodes): A(2), B(2), C(2), L(2), R(2)
  → 5 fork nodes = 5 điểm phân chia song song
```

### 2.3 Sơ đồ ASCII của DAG

```
Layer 0:                    [A:4d]
                           /      \
Layer 1:              [B:6d]      [C:7d]
                     /    \        /    \
Layer 2:        [D:8d] [E:6d] [F:12d] [G:10d]
                  |      \    /          |
Layer 3:        [K:7d]   [H:8d]       [I:16d]
                  \      / \             |
Layer 4:         [L:9d]  [M:4d]       [J:12d]
                 / \       \           /
Layer 5:    [O:7d] [P:5d]  [N:7d]----┘
                \   /         \
Layer 6:        [Q:4d]        |
                   \         /
Layer 7:           [R:5d]---┘
                   /    \
Layer 8:      [S:2d]   [T:3d]
                 \      /
Layer 9:          [U:2d]
```

---

## 3. Tính Toán CPM Đầy Đủ (Q2)

### 3.1 Forward Pass (Duyệt xuôi: Tính ES, EF)

Quy tắc: $ES_j = \max(EF_i)$ cho mọi predecessor $i$ của $j$; $EF_j = ES_j + d_j$

| Task | Duration | ES | EF | Giải thích |
|:---:|:---:|:---:|:---:|---|
| A | 4 | **0** | **4** | Nút đầu tiên |
| B | 6 | 4 | 10 | ES = EF(A) = 4 |
| C | 7 | 4 | 11 | ES = EF(A) = 4 |
| D | 8 | 10 | 18 | ES = EF(B) = 10 |
| E | 6 | 10 | 16 | ES = EF(B) = 10 |
| F | 12 | 11 | **23** | ES = EF(C) = 11 |
| G | 10 | 11 | 21 | ES = EF(C) = 11 |
| H | 8 | **23** | **31** | ES = max(EF(E)=16, EF(F)=**23**) = 23 |
| I | 16 | 21 | 37 | ES = EF(G) = 21 |
| J | 12 | 37 | **49** | ES = EF(I) = 37 |
| K | 7 | 18 | 25 | ES = EF(D) = 18 |
| L | 9 | **31** | **40** | ES = max(EF(H)=**31**, EF(K)=25) = 31 |
| M | 4 | 31 | 35 | ES = EF(H) = 31 |
| N | 7 | **49** | **56** | ES = max(EF(J)=**49**, EF(M)=35) = 49 |
| O | 7 | 40 | 47 | ES = EF(L) = 40 |
| P | 5 | 40 | 45 | ES = EF(L) = 40 |
| Q | 4 | 47 | 51 | ES = max(EF(O)=47, EF(P)=45) = 47 |
| R | 5 | **56** | **61** | ES = max(EF(N)=**56**, EF(Q)=51) = 56 |
| S | 2 | 61 | 63 | ES = EF(R) = 61 |
| T | 3 | 61 | **64** | ES = EF(R) = 61 |
| U | 2 | **64** | **66** | ES = max(EF(S)=63, EF(T)=**64**) = 64 |

**→ Thời gian dự án (Makespan) = EF(U) = 66 ngày làm việc**

### 3.2 Backward Pass (Duyệt ngược: Tính LF, LS)

Quy tắc: $LF_j = \min(LS_k)$ cho mọi successor $k$ của $j$; $LS_j = LF_j - d_j$

| Task | Duration | LF | LS | Slack = LS - ES |
|:---:|:---:|:---:|:---:|:---:|
| U | 2 | **66** | **64** | **0** ⭐ |
| T | 3 | **64** | **61** | **0** ⭐ |
| S | 2 | 64 | 62 | 1 |
| R | 5 | **61** | **56** | **0** ⭐ |
| Q | 4 | 56 | 52 | 5 |
| P | 5 | 52 | 47 | 7 |
| O | 7 | 52 | 45 | 5 |
| N | 7 | **56** | **49** | **0** ⭐ |
| M | 4 | 49 | 45 | 14 |
| L | 9 | 45 | 36 | 5 |
| K | 7 | 36 | 29 | 11 |
| J | 12 | **49** | **37** | **0** ⭐ |
| I | 16 | **37** | **21** | **0** ⭐ |
| H | 8 | 36 | 28 | 5 |
| G | 10 | **21** | **11** | **0** ⭐ |
| F | 12 | 28 | 16 | 5 |
| E | 6 | 28 | 22 | 12 |
| D | 8 | 29 | 21 | 11 |
| C | 7 | **11** | **4** | **0** ⭐ |
| B | 6 | 16 | 10 | 6 |
| A | 4 | **4** | **0** | **0** ⭐ |

### 3.3 Đường Găng (Critical Path)

```
ĐƯỜNG GĂNG (Slack = 0):

A ──> C ──> G ──> I ──> J ──> N ──> R ──> T ──> U
(4)   (7)   (10)  (16)  (12)  (7)   (5)   (3)   (2)

Tổng = 4 + 7 + 10 + 16 + 12 + 7 + 5 + 3 + 2 = 66 ngày

⚠️ NHẬN XÉT:
- Đường găng chạy qua nhánh SOFTWARE (C→G→I→J)
- Nhánh phần mềm chiếm 45/66 = 68% thời gian dự án
- Nhánh phần cứng (B→D→K hoặc B→E) có slack 6-12 ngày → linh hoạt
- Nút N (Prototype install) là điểm hội tụ giữa SW và HW
```

### 3.4 Phân tích Slack chi tiết

| Nhóm | Tasks | Slack Range | Nhận xét |
|------|-------|:-----------:|----------|
| **Găng (Critical)** | A,C,G,I,J,N,R,T,U | 0 | Không được phép trễ |
| **Gần găng** | S | 1 | Chỉ có 1 ngày dự trữ |
| **Trung bình** | F,H,L,O,Q | 5 | Có ~1 tuần dự trữ |
| **Nhiều dự trữ** | B | 6 | > 1 tuần |
| **Rất linh hoạt** | D,K | 11 | > 2 tuần dự trữ |
| **Siêu linh hoạt** | E | 12 | Gần 2.5 tuần |
| **Tự do nhất** | M | 14 | Gần 3 tuần dự trữ |
| **Linh hoạt (P)** | P | 7 | > 1 tuần |

---

## 4. Phân Tích Tài Nguyên & Xung Đột (Q4, Q5)

### 4.1 Ma trận tài nguyên đầy đủ

| Task | Design_C | Design_M | Dev_C | Dev_M | Asm_C | Asm_M | Purchase | Doc | Tổng |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | 1 | 1 | - | - | - | - | - | - | 2 |
| B | 1 | 1 | - | 1 | - | 1 | - | - | 4 |
| C | 1 | - | 1 | - | 1 | - | - | - | 3 |
| D | - | 1 | - | 1 | - | - | - | - | 2 |
| E | 1 | 1 | - | 1 | - | - | - | - | 3 |
| F | 1 | - | 1 | - | - | - | - | - | 2 |
| G | - | - | 1 | - | - | - | - | 1 | 2 |
| H | - | - | 1 | 1 | - | - | - | 1 | 3 |
| I | 1 | - | - | - | - | - | - | 1 | 2 |
| J | - | - | 1 | - | 1 | - | - | 1 | 3 |
| K | - | - | 1 | 1 | - | - | - | 1 | 3 |
| L | - | - | 1 | - | 1 | 1 | - | - | 3 |
| M | - | - | 1 | 1 | - | - | - | - | 2 |
| N | - | - | - | - | 1 | 1 | - | - | 2 |
| O | - | - | - | 1 | - | - | 1 | - | 2 |
| P | - | - | - | 1 | - | 1 | - | - | 2 |
| Q | - | - | - | - | 1 | 1 | - | - | 2 |
| R | - | - | 1 | 1 | 1 | 1 | - | - | 4 |
| S | - | - | 1 | 1 | - | - | - | 1 | 3 |
| T | - | - | - | 1 | 1 | 1 | - | - | 3 |
| U | - | - | - | - | 1 | 1 | - | - | 2 |

### 4.2 Các xung đột tài nguyên chính (khi xếp Early Start)

Khi xếp tất cả tasks theo ES (Early Start scheduling), xảy ra **nhiều xung đột tài nguyên**:

#### Xung đột 1: Design (Computing) — Giới hạn: 1 người
```
Ngày 4-10:  B cần 1 DC + C cần 1 DC = 2 người ⚠️ VƯỢT (chỉ có 1)
Ngày 10-16: E cần 1 DC + F cần 1 DC = 2 người ⚠️ VƯỢT
Ngày 11-23: F cần 1 DC + I cần 1 DC = 2 người ⚠️ VƯỢT (overlap)
```

#### Xung đột 2: Dev (Mechanical) — Giới hạn: 1 người
```
Ngày 10-16: E cần 1 DM
Ngày 10-18: D cần 1 DM
→ Overlap 10-16: 2 người cần ⚠️ VƯỢT
```

#### Xung đột 3: Dev (Computing) — Giới hạn: 2 người
```
Ngày 11-21: G cần 1 + F cần 1 = 2 (vừa đủ)
Ngày 18-25: K cần 1 + H cần 1 = 2 (vừa đủ)
Ngày 21-37: I cần DC (nhưng dùng Design_Comp slot)
→ Nhiều thời điểm 3 tasks cùng cần Dev_Comp ⚠️
```

### 4.3 Kết quả RCPSP (Q5)

Khi áp dụng resource-constrained scheduling (xếp lại lịch để tôn trọng giới hạn tài nguyên):

```
Thời gian dự án TRƯỚC resource leveling: 66 ngày
Thời gian dự án SAU resource leveling:   96 ngày ⚠️

Tăng thêm: 30 ngày (45% kéo dài!)
Tương đương: 66/5 = 13.2 tuần → 96/5 = 19.2 tuần

→ Thời gian vượt deadline (12 tuần) = 7.2 tuần
→ Tiền phạt tối thiểu: 7 × $2,000 = $14,000
```

**Các tasks bị dời lịch nhiều nhất:**
| Task | ES gốc | ES mới (RCPSP) | Bị dời | Lý do |
|:---:|:---:|:---:|:---:|---|
| E | 10 | 18 | +8d | Chờ Design_Comp (B chiếm) |
| F | 11 | 23 | +12d | Chờ Design_Comp (E chiếm) |
| H | 23 | 35 | +12d | Chờ F + Dev_Mech |
| K | 18 | 25 | +7d | Chờ Dev_Comp |

---

## 5. Phân Tích Thuê Ngoài Chi Tiết (Q6a)

### 5.1 Xác định tasks cần thuê ngoài

Từ phân tích xung đột tài nguyên, xác định các thời điểm cần thuê ngoài:

```
Nguyên tắc: Khi 2+ tasks cùng cần 1 loại tài nguyên
mà chỉ có 1 người nội bộ → phải thuê ngoài cho 1 task

Ưu tiên: Giữ nhân viên nội bộ cho tasks TRÊN đường găng
         Thuê ngoài cho tasks NGOÀI đường găng
```

### 5.2 Bảng chi phí thuê ngoài chi tiết

| Task cần thuê ngoài | Resource bị xung đột | Duration + Induction | Đơn giá | Chi phí |
|---|---|:---:|:---:|:---:|
| B (HW specs) | Design_Comp | 6 + 3 = 9d | $350 | $3,150 |
| E (HW design) | Design_Comp, Dev_Mech | (6+3)×350 + (6+3)×250 | mixed | $5,400 |
| D (Conveyor design) | Dev_Mech | 8 + 3 = 11d | $250 | $2,750 |
| K (Conveyor drawings) | Dev_Comp | 7 + 3 = 10d | $250 | $2,500 |
| H (HW detail drawings) | Dev_Comp, Dev_Mech | (8+3)×250×2 | $250 | $5,500 |
| M (Prototype dev) | Dev_Comp, Dev_Mech | (4+3)×250×2 | $250 | $3,500 |

### 5.3 Công thức tổng chi phí thuê ngoài

$$C_{sub} = \sum_{i \in \text{outsourced}} \sum_{r \in R_i^{sub}} (d_i + 3) \times \text{rate}_{r}^{contractor}$$

**Kết quả ước tính: ~$22,800** (phụ thuộc vào chiến lược chọn tasks)

### 5.4 Chi phí khi kết hợp subcontracting

```
Chi phí nhân sự nội bộ (66 ngày): ~$47,430
Chi phí thuê ngoài:                ~$22,800
Overhead (13.2 tuần × $500):       ~$6,600
                                   ─────────
Tổng chi phí cơ bản:              ~$76,830

So với kết quả đề bài (ground truth): $70,230
→ Cần tối ưu hóa chiến lược thuê ngoài để giảm chi phí
```

---

## 6. Phân Tích Crashing Chi Tiết (Q6b)

### 6.1 Quy tắc overtime (nhắc lại)

| Loại | Hệ số lương | Điều kiện |
|------|:-----------:|-----------|
| **Weekday (T2-T6)** | 1.0× | Bình thường |
| **Saturday (T7)** | 1.5× | Phải dùng hết T7 trước |
| **Sunday (CN)** | 3.0× | Chỉ khi đã hết T7 |

### 6.2 Bảng chi phí crash cho mỗi hoạt động găng

Chỉ crash các hoạt động **trên đường găng** (Slack = 0):

| Task găng | Dur | Resources | Chi phí 1 ngày T7 | Chi phí 1 ngày CN | Max crash (T7) |
|:---:|:---:|---|:---:|:---:|:---:|
| A | 4 | DC+DM | $200×1.5 + $200×1.5 = **$600** | $1,200 | ~1d |
| C | 7 | DC+DevC+AC | $200×1.5 + $150×1.5 + $100×1.5 = **$675** | $1,350 | ~1d |
| G | 10 | DevC+Doc | $150×1.5 + $80×1.5 = **$345** | $690 | ~2d |
| I | 16 | DC+Doc | $200×1.5 + $80×1.5 = **$420** | $840 | ~3d |
| J | 12 | DevC+AC+Doc | $150×1.5 + $100×1.5 + $80×1.5 = **$495** | $990 | ~2d |
| N | 7 | AC+AM | $100×1.5 + $100×1.5 = **$300** | $600 | ~1d |
| R | 5 | DevC+DM+AC+AM | $(150+150+100+100)×1.5 = **$750** | $1,500 | ~1d |
| T | 3 | DM+AC+AM | $(150+100+100)×1.5 = **$525** | $1,050 | ~1d |

### 6.3 Chiến lược Crashing tối ưu (Greedy)

```
Bước 1: Sắp xếp hoạt động găng theo chi phí crash T7 tăng dần:
  N ($300) < G ($345) < I ($420) < J ($495) < T ($525)
  < A ($600) < C ($675) < R ($750)

Bước 2: Crash từ rẻ nhất trước (Greedy approach):
  Crash N 1 ngày T7: -1 ngày, +$300
  Crash G 1 ngày T7: -1 ngày, +$345
  Crash G 1 ngày T7: -1 ngày, +$345
  Crash I 1 ngày T7: -1 ngày, +$420
  ...tiếp tục cho đến khi đạt mục tiêu

Bước 3: Kiểm tra lại đường găng sau mỗi lần crash
  ⚠️ Sau khi crash, đường găng có thể THAY ĐỔI!
  Nếu nhánh HW (B→D→K→L→O→Q) trở thành găng mới
  → phải chuyển sang crash nhánh HW
```

### 6.4 Tính toán chi phí tổng hợp theo số tuần

| Tuần hoàn thành | Direct Cost bổ sung | Overhead | Penalty | Bonus | **Tổng Chi Phí** |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 14 (66d, no crash) | $0 | $7,000 | $4,000 | $0 | Base + $11,000 |
| 13 (crash 5d) | ~$1,710 | $6,500 | $2,000 | $0 | Base + $10,210 |
| 12 (crash 10d) | ~$4,500 | $6,000 | $0 | $0 | Base + $10,500 |
| 11 (crash 15d) | ~$9,200 | $5,500 | $0 | $3,000 | Base + $11,700 |
| 10 (crash 20d) | ~$17,000 | $5,000 | $0 | $6,000 | Base + $16,000 |

**→ Điểm tối ưu: ~13 tuần (crash 5 ngày)**
*Tại điểm này, chi phí crash thêm ít hơn phần penalty tiết kiệm được.*

---

## 7. Phân Tích EVM Chi Tiết (Q7)

### 7.1 Dữ liệu tuần 5 (ngày 25)

Đầu tiên, tính **Planned Value (PV)** dựa trên chi phí dự kiến theo kế hoạch ES:

| Task | Dur | Cost/day | Planned Cost | PV% (plan) | PV ($) | EV% (actual) | EV ($) | AC ($) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A | 4 | $400 | $1,600 | 100% | $1,600 | 100% | $1,600 | $2,400 |
| B | 6 | $600 | $3,600 | 100% | $3,600 | 100% | $3,600 | $6,500 |
| C | 7 | $450 | $3,150 | 100% | $3,150 | 100% | $3,150 | $4,300 |
| D | 8 | $350 | $2,800 | 100% | $2,800 | 100% | $2,800 | $3,500 |
| E | 6 | $550 | $3,300 | 100% | $3,300 | 100% | $3,300 | $6,100 |
| F | 12 | $350 | $4,200 | 100% | $4,200 | 50% | $2,100 | $8,500 |
| G | 10 | $230 | $2,300 | 100% | $2,300 | 100% | $2,300 | $2,100 |
| H | 8 | $380 | $3,040 | 100% | $3,040 | 10% | $304 | $2,000 |
| I | 16 | $280 | $4,480 | 100% | $4,480 | 20% | $896 | $5,300 |
| K | 7 | $380 | $2,660 | 100% | $2,660 | 80% | $2,128 | $3,200 |

### 7.2 Tính các chỉ số EVM

```
Tổng PV = $31,130  (công việc dự kiến hoàn thành đến ngày 25)
Tổng EV = $22,178  (công việc thực tế đã hoàn thành, tính theo giá KH)
Tổng AC = $43,900  (chi phí thực tế đã chi)
```

#### Chỉ số tiến độ (Schedule):
```
SV (Schedule Variance) = EV - PV = $22,178 - $31,130 = -$8,952
SPI (Schedule Performance Index) = EV/PV = 22,178/31,130 = 0.712

→ SPI = 0.712 < 1 ⚠️ DỰ ÁN ĐANG CHẬM TIẾN ĐỘ 28.8%
→ Chỉ hoàn thành 71.2% khối lượng dự kiến
```

#### Chỉ số chi phí (Cost):
```
CV (Cost Variance) = EV - AC = $22,178 - $43,900 = -$21,722
CPI (Cost Performance Index) = EV/AC = 22,178/43,900 = 0.505

→ CPI = 0.505 < 1 ⚠️ DỰ ÁN ĐANG VƯỢT NGÂN SÁCH 49.5%
→ Mỗi $1 chi ra chỉ tạo được $0.505 giá trị
```

### 7.3 Dự báo chi phí & thời gian hoàn thành

```
BAC (Budget at Completion) = Tổng ngân sách dự kiến ≈ $70,230

EAC (Estimate at Completion) = BAC / CPI = $70,230 / 0.505 = $139,069
→ Chi phí dự báo khi hoàn thành: ~$139,000 (gấp đôi ngân sách!)

ETC (Estimate to Complete) = EAC - AC = $139,069 - $43,900 = $95,169
→ Cần thêm ~$95,000 để hoàn thành dự án

TCPI (To-Complete Performance Index) = (BAC - EV) / (BAC - AC)
= ($70,230 - $22,178) / ($70,230 - $43,900) = $48,052 / $26,330 = 1.825
→ Cần CPI = 1.825 cho phần còn lại để hoàn thành đúng ngân sách
→ GẦN NHƯ KHÔNG THỂ! (cần hiệu suất 182.5%)
```

### 7.4 Nhận xét & Khuyến nghị

```
⚠️ CẢNH BÁO CẤP ĐỘ: NGUY HIỂM (SPI < 0.8 VÀ CPI < 0.6)

Các công việc gây vấn đề:
┌──────────────────────────────────────────────────┐
│ F (Software design):  50% done vs 100% planned  │
│ → Chậm 50%, nhưng đã tiêu $8,500 (> budget)     │
│ → NÚT TRÊN ĐƯỜNG GẤN GĂng (F→H→L→...)         │
│                                                  │
│ H (HW detail drawings): 10% done vs 100%         │
│ → Chậm 90%! Chi phí $2,000 cho 10% công việc    │
│ → Bị block bởi F chưa xong                       │
│                                                  │
│ I (SW programming): 20% done vs 100%              │
│ → Chậm 80%! NẰM TRÊN ĐƯỜNG GĂNG!                │
│ → Là nút kéo dài nhất (16 ngày)                  │
│ → Mọi sự trễ ở I → trễ toàn bộ dự án            │
│                                                  │
│ K (Conveyor drawings): 80% done vs 100%           │
│ → Tương đối tốt, sắp hoàn thành                  │
└──────────────────────────────────────────────────┘

KHUYẾN NGHỊ:
1. Tập trung 100% nguồn lực vào I (SW Programming)
   → Nút găng kéo dài nhất, đang chậm nghiêm trọng
2. Đẩy nhanh F (Software design)
   → F phải xong để H có thể bắt đầu
3. Xem xét thuê thêm thầu phụ cho I và F
4. Chuẩn bị báo cáo rủi ro cho stakeholders
   → Dự án có khả năng vượt ngân sách 98%
```

---

## 8. Tổng Hợp Kết Quả Đối Chứng (Ground Truth)

| Mục | Giá trị |
|-----|---------|
| **Makespan (CPM, no resource)** | **66 ngày** (13.2 tuần) |
| **Đường găng** | **A → C → G → I → J → N → R → T → U** |
| **Số hoạt động găng** | **9/21** (42.8%) |
| **Makespan (RCPSP)** | **96 ngày** (19.2 tuần) |
| **Tăng thêm do resource** | **+30 ngày** (+45%) |
| **Chi phí tối ưu (với subcontracting)** | **$70,230** |
| **SPI tại tuần 5** | **0.712** (chậm 28.8%) |
| **CPI tại tuần 5** | **0.505** (vượt chi 49.5%) |

---

## 📚 9. Tài Liệu Tham Khảo

1.  **PPC_casestudy_2010_V1.pdf** — Đề bài gốc MFET 3008/5040
2.  **Project Management Institute (2019).** *"Practice Standard for Earned Value Management"* (3rd Ed.)
3.  **Kelley & Walker (1959).** *"Critical-Path Planning and Scheduling."* → Nền tảng CPM
4.  **Brucker et al. (1999).** *"Resource-Constrained Project Scheduling."* → Phân loại RCPSP
