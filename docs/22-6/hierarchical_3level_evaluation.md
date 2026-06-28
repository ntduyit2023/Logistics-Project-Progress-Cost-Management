# Kiến trúc Đánh giá Phân cấp 3 Tầng (Hierarchical 3-Level Evaluation)
*Giữa Feature ↔ Feature, Feature ↔ Group, Group ↔ Group*

> **Phiên bản 2.0** — Đã đồng bộ với ERD.drawio (53 User-Input Features + 12 AI-Computed Features = 72 tổng)

---

## Tổng quan Kiến trúc

Thay vì "nấu" tất cả 72 features vào 1 hàm duy nhất, chúng ta xử lý theo chuỗi **3 tầng (Bottom-Up)**:

```
Tầng 1 (Nền tảng):   Feature ↔ Feature   (Trong cùng 1 Nhóm)
                              ↓
Tầng 2 (Trung gian):  Feature ↔ Group     (Feature tác động lên Nhóm khác)
                              ↓
Tầng 3 (Đỉnh):        Group ↔ Group       (12 Nhóm cạnh tranh/hỗ trợ nhau)
                              ↓
                     Total Generalized Cost (TGC)
```

---

## PHÂN LOẠI NGUỒN DỮ LIỆU (Data Source Classification)

12 Groups được chia thành 2 nguồn dữ liệu rõ ràng:

### Nhóm A: User Input (9 Groups — Lưu trong Database/CSV)
Đây là dữ liệu mà con người nhập vào hoặc trích xuất từ file MS Project/DSLIB.

| Group | Tên | Số Features | Nguồn CSV |
|:---:|:---|:---:|:---|
| **Hub** | Core Temporal | 7 | `tasks.csv` (duration_*, baseline_start, calendar_type) |
| **G1** | Direct Costs | 8 | `tasks.csv` (material_cost, internal_labor_cost) + DB |
| **G2** | Indirect Costs | 6 | Database (pm_overhead, facility_rent...) |
| **G4** | Contractual | 4 | Database (permits, insurance...) |
| **G5** | Logistics & SCM | 7 | Database (inventory, ordering...) |
| **G6** | Temporal (Extended) | 5 | `tasks.csv` (pert_3_point_estimate) + DB |
| **G7** | Resources | 5 | `task_resources.csv` (request_quantity) + DB |
| **G9** | Risks | 7 | `tasks.csv` (contingency_reserve) + DB |
| **G11** | Human & Org | 6 | Database |
| **G12** | ESG | 5 | Database |
| | **Tổng User Input** | **60** | |

### Nhóm B: AI-Computed (3 Groups — AI tự tính, KHÔNG lưu Database)
Đây là dữ liệu mà chỉ có thuật toán mới tính được, không ai "nhập tay".

| Group | Tên | Số Features | AI tính bằng cách nào? |
|:---:|:---|:---:|:---|
| **G3** | Opportunity Cost | 3 | So sánh kịch bản thay thế → `schedule_flexibility`, `resource_alternative_cost`, `delay_impact_cost` |
| **G8** | Network Topology | 5 | Phân tích đồ thị `predecessors.csv` → `in_degree`, `out_degree`, `is_critical`, `total_float`, `path_length` |
| **G10** | Earned Value | 4 | So sánh lịch đề xuất vs Baseline → `planned_value`, `earned_value`, `cpi`, `spi` |
| | **Tổng AI-Computed** | **12** | |

### Tổng Feature Vector: 60 + 12 = **72 Features**

---

## QUY TRÌNH TÍNH TOÁN 3 GROUP AI-COMPUTED (G3🤖, G8🤖, G10🤖)

Dưới đây là thuật toán chi tiết để AI tự sinh ra 12 Features thuộc 3 Groups mà con người không nhập được.

### G8🤖: Network Topology (5 Features) — Tính từ Đồ thị

**Nguồn dữ liệu:** `predecessors.csv` (Edge List) + `tasks.csv` (Node List)

**Thời điểm tính:** Ngay lập tức khi đọc CSV (Bước 0.5), trước cả khi vào 3 Tầng.

| Feature | Công thức | Ý nghĩa |
|:---|:---|:---|
| `in_degree` | Đếm số cạnh **hướng vào** node $i$: $\text{in}(i) = \|\{j : (j \to i) \in E\}\|$ | Task phụ thuộc nhiều task khác = Rủi ro bị chặn (Blocking Risk) cao |
| `out_degree` | Đếm số cạnh **hướng ra** từ node $i$: $\text{out}(i) = \|\{j : (i \to j) \in E\}\|$ | Task ảnh hưởng nhiều task khác = Rủi ro lan truyền (Propagation Risk) cao |
| `is_critical` | $= 1$ nếu `total_float = 0`, ngược lại $= 0$ | Task nằm trên Critical Path — trễ 1 ngày = cả dự án trễ 1 ngày |
| `total_float` | $TF_i = LS_i - ES_i$ (Late Start - Early Start) | Thời gian dự phòng. $TF = 0$ → Critical Path |
| `path_length` | Khoảng cách (số bước nhảy) từ node $i$ đến Sink Node (task cuối) | Task xa đích = ít áp lực deadline, Task gần đích = áp lực cao |

**Thuật toán tính Critical Path (CPM):**

```
Bước 1 (Forward Pass): Tính Early Start & Early Finish
   ES[source] = 0
   For each task i theo thứ tự Topological Sort:
       ES[i] = max(EF[predecessor] + lag) cho mọi predecessor
       EF[i] = ES[i] + duration[i]

Bước 2 (Backward Pass): Tính Late Start & Late Finish
   LF[sink] = EF[sink]
   For each task i theo thứ tự NGƯỢC Topological Sort:
       LF[i] = min(LS[successor] - lag) cho mọi successor
       LS[i] = LF[i] - duration[i]

Bước 3: Tính Float & Criticality
   total_float[i] = LS[i] - ES[i]
   is_critical[i] = 1 nếu total_float[i] == 0
```

**Quan hệ nội bộ G8 (Feature ↔ Feature):**
- `in_degree` 📈 `is_critical`: Nhiều phụ thuộc → dễ bị nằm trên Critical Path.
- `out_degree` 📈 `path_length`: Nhiều "đệ tử" thường đi kèm vị trí trung tâm đồ thị.
- `total_float` ⚔️ `is_critical`: Float cao ↔ Không critical (nghịch đảo hoàn toàn).

---

### G10🤖: Earned Value (4 Features) — Tính từ Baseline vs Lịch trình Đề xuất

**Nguồn dữ liệu:** `tasks.csv` (Baseline Schedule) + Lịch trình mà AI đang xây dựng (Proposed Schedule)

**Thời điểm tính:** Trong quá trình tối ưu hóa (RL Agent đề xuất lịch trình mới → so sánh với Baseline → tính EV).

| Feature | Công thức | Ý nghĩa |
|:---|:---|:---|
| `planned_value` | $PV_i = \text{BudgetedCost}_i \times \frac{T_{elapsed}}{T_{planned}}$ | Giá trị công việc **dự kiến** hoàn thành tại thời điểm hiện tại |
| `earned_value` | $EV_i = \text{BudgetedCost}_i \times \text{PercentComplete}_i$ | Giá trị công việc **thực tế** đã hoàn thành |
| `cpi` | $CPI_i = \frac{EV_i}{AC_i}$ (Actual Cost) | Hiệu suất chi phí: CPI < 1 = vượt ngân sách |
| `spi` | $SPI_i = \frac{EV_i}{PV_i}$ | Hiệu suất tiến độ: SPI < 1 = chậm tiến độ |

**Thuật toán tính Earned Value:**

```
For each task i:
    budgeted_cost[i] = material_cost[i] + internal_labor_cost[i]  (từ CSV)
    
    # Planned Value: dựa trên Baseline Schedule
    IF task i đã bắt đầu theo Baseline:
        planned_progress = (current_time - baseline_start[i]) / duration[i]
        PV[i] = budgeted_cost[i] × min(planned_progress, 1.0)
    ELSE:
        PV[i] = 0

    # Earned Value: dựa trên Proposed Schedule (AI đề xuất)
    IF task i đã hoàn thành theo Proposed Schedule:
        EV[i] = budgeted_cost[i]
    ELIF task i đang chạy:
        EV[i] = budgeted_cost[i] × actual_progress
    ELSE:
        EV[i] = 0

    # Performance Indices
    AC[i] = actual_cost[i]  (chi phí thực tế phát sinh)
    CPI[i] = EV[i] / AC[i]  nếu AC[i] > 0, ngược lại = 1.0
    SPI[i] = EV[i] / PV[i]  nếu PV[i] > 0, ngược lại = 1.0
```

**Quan hệ nội bộ G10 (Feature ↔ Feature):**
- `earned_value` 🤝 `planned_value`: Cả hai cùng tăng theo tiến độ dự án.
- `cpi` ⚔️ `spi`: Đôi khi đối nghịch — Tiến nhanh (SPI cao) nhưng đắt (CPI thấp).
- `spi` 📈 `earned_value`: Tiến độ nhanh → EV tăng mạnh.

---

### G3🤖: Opportunity Cost (3 Features) — Tính từ So sánh Kịch bản

**Nguồn dữ liệu:** Kết quả từ nhiều lần chạy tối ưu hóa (PPO Agent thử nhiều kịch bản lập lịch khác nhau)

**Thời điểm tính:** Chỉ có ý nghĩa khi PPO Agent đã có **ít nhất 2 kịch bản** để so sánh. Ở lần chạy đầu tiên, G3 sẽ được khởi tạo bằng 0 (chưa có gì để so sánh).

| Feature | Công thức | Ý nghĩa |
|:---|:---|:---|
| `schedule_flexibility` | $SF_i = \frac{TF_i}{\max(TF)}$ (Float chuẩn hóa so với task "thoải mái" nhất) | Mức độ linh hoạt khi dời Task. $SF = 0$ → Không thể dời, $SF = 1$ → Rất linh hoạt |
| `resource_alternative_cost` | $RAC_i = \text{Cost}_{external} - \text{Cost}_{internal}$ cho tài nguyên Task $i$ | Chênh lệch chi phí nếu dùng tài nguyên thay thế (thuê ngoài vs nội bộ) |
| `delay_impact_cost` | $DIC_i = \sum_{j \in Successors(i)} TGC_j^{delayed} - TGC_j^{ontime}$ | Tổng thiệt hại dây chuyền xuống các task con nếu Task $i$ bị trễ |

**Thuật toán tính Opportunity Cost:**

```
# Schedule Flexibility (Tính ngay sau CPM - G8)
For each task i:
    SF[i] = total_float[i] / max(total_float)  # Chuẩn hóa [0, 1]

# Resource Alternative Cost (Tính từ resources.csv)
For each task i:
    internal = sum(internal_cost[r] × qty[i,r]) cho mọi resource r
    external = sum(external_cost[r] × qty[i,r]) cho mọi resource r
    RAC[i] = external - internal  # Dương = thuê ngoài đắt hơn

# Delay Impact Cost (Tính bằng Simulation — PHỨC TẠP NHẤT)
For each task i:
    Scenario A: Chạy TGC bình thường (on-time)
    Scenario B: Giả lập Task i bị trễ 1 đơn vị → Chạy lại TGC
    DIC[i] = TGC_B - TGC_A  # Chênh lệch = Thiệt hại do trễ
```

> ⚠️ **Lưu ý quan trọng:** `delay_impact_cost` là feature **tốn kém nhất** để tính (phải mô phỏng nhiều lần). Trong giai đoạn training ban đầu, có thể dùng **xấp xỉ** bằng: $DIC_i \approx \text{out\_degree}(i) \times \text{avg\_TGC}$ (Nhiều "đệ tử" × Chi phí trung bình).

**Quan hệ nội bộ G3 (Feature ↔ Feature):**
- `schedule_flexibility` ⚔️ `delay_impact_cost`: Task linh hoạt (Float lớn) thì thiệt hại khi trễ cũng ít hơn.
- `resource_alternative_cost` 🤝 `delay_impact_cost`: Nếu thuê ngoài đắt, trễ hạn càng đắt hơn.

---

### Thứ tự Tính toán Bắt Buộc (Dependency Chain)

```
G8 (Network Topology) ← Tính TRƯỚC (chỉ cần predecessors.csv)
        ↓
G3 (Opportunity Cost)  ← Tính SAU G8 (cần total_float từ G8)
        ↓
G10 (Earned Value)     ← Tính TRONG QUÁ TRÌNH tối ưu hóa
                         (cần Proposed Schedule từ PPO Agent)
```

> **Lưu ý:** G8 luôn có giá trị. G3 có giá trị sau khi CPM chạy xong. G10 chỉ có giá trị đầy đủ khi RL Agent đang chạy (vì cần so sánh Proposed vs Baseline).

---

## TẦNG 1: Feature ↔ Feature (Intra-group Aggregation)

### Mục tiêu
Xử lý **bên trong từng Nhóm** trước. Mỗi Nhóm $g$ chứa $n_g$ features. Các features này không độc lập — chúng **cạnh tranh, bổ trợ, hoặc triệt tiêu** lẫn nhau.

### Các loại Quan hệ Feature ↔ Feature (trong cùng nhóm)

| Ký hiệu | Loại quan hệ | Ví dụ cụ thể |
| :---: | :--- | :--- |
| ⚔️ | **Cạnh tranh (Competitive)** | `internal_labor_cost` vs `subcontracting_cost` (G1): Tăng cái này thì giảm cái kia |
| 🤝 | **Bổ trợ (Complementary)** | `material_cost` + `direct_transportation` (G1): Mua nhiều vật liệu thì phí ship cũng tăng |
| 🔄 | **Thay thế (Substitutable)** | `internal_labor_cost` ↔ `subcontracting_cost` (G1): Dùng cái này thì không cần cái kia |
| 📈 | **Khuếch đại (Amplifying)** | `rework_probability` × `technical_complexity` (G9): Dự án phức tạp → phải làm lại nhiều hơn |

### Công thức Tầng 1: Giá trị Đại diện của Nhóm ($S_g$)

Bước 1: Tính **Ma trận Tương tác nội bộ** $A^{intra}_g$ cho mỗi nhóm $g$

$$
A^{intra}_g = \begin{bmatrix}
  1      & a_{1,2} & \cdots & a_{1,n_g} \\
  a_{2,1} & 1      & \cdots & a_{2,n_g} \\
  \vdots  & \vdots  & \ddots & \vdots    \\
  a_{n_g,1} & a_{n_g,2} & \cdots & 1
\end{bmatrix}
$$

Trong đó:
*   $a_{p,q} > 0$: Feature $p$ **bổ trợ/khuếch đại** Feature $q$ (cùng tăng cùng giảm)
*   $a_{p,q} < 0$: Feature $p$ **cạnh tranh/triệt tiêu** Feature $q$ (tăng cái này ép giảm cái kia)
*   $a_{p,q} = 0$: Không có tương tác

Bước 2: Tính **Trọng số Attention nội bộ** ($\alpha$) cho mỗi feature trong nhóm

$$
\alpha_f = \frac{\exp\left(\sum_{q} a_{f,q} \cdot v_q\right)}{\sum_{p \in Group_g} \exp\left(\sum_{q} a_{p,q} \cdot v_q\right)}
$$

*   $v_q$: Giá trị thô (raw value) của feature $q$ tại task hiện tại.
*   $\alpha_f$: "Mức độ nổi bật" (Attention Weight) của feature $f$ trong bối cảnh cụ thể của task.

Bước 3: **Giá trị Đại diện (Summary Score)** của Nhóm $g$

$$ S_g = \sum_{f \in Group_g} \alpha_f \cdot v_f $$

> **Ý nghĩa:** Tầng 1 ép mỗi Nhóm phải "nội chiến" trước. Feature nào thắng (có $\alpha$ cao nhất) sẽ đại diện cho tiếng nói của cả Nhóm lên Tầng 2.

---

## TẦNG 2: Feature ↔ Group (Cross-group Feature Influence)

### Mục tiêu
Xử lý **quan hệ xuyên Nhóm**. Một feature đơn lẻ có thể tác động mạnh lên toàn bộ một Nhóm khác (không chỉ nhóm của nó).

### Các mối quan hệ Feature → Group (Xuyên nhóm) đặc biệt quan trọng

| Feature nguồn | → Nhóm bị tác động | Cơ chế |
| :--- | :--- | :--- |
| `duration_*` (Hub) | → **G2** (Gián tiếp) | Duration kéo dài → Toàn bộ G2 tăng (Thuê VP, Tiện ích, PM) |
| `wait_queue_time` (G6) | → **G5** (Logistics) | Chờ đợi lâu → Lưu kho, Hết hạn đều tăng |
| `request_qty / capacity` (G7) | → **G1** (Trực tiếp) | Khan hiếm tài nguyên → Giá thuê ngoài, OT tăng |
| `rework_probability` (G9) | → **G4** (Hợp đồng) | Xác suất trễ cao → Penalty gần như chắc chắn phải trả |
| `out_degree` (G8 🤖) | → **G9** (Rủi ro) | Node có Out-degree cao → Rủi ro lan truyền tăng mạnh |
| `hr_stability_risk` (G11) | → **G1** (Trực tiếp) | Nhân sự bất ổn → Phải làm lại, CPI giảm |

> 🤖 = AI-Computed Feature

### Công thức Tầng 2: Điều chỉnh Giá trị Nhóm

Gọi $X_{f \to g}$ là **Hệ số xuyên nhóm** (Cross-group Influence) từ Feature $f$ (thuộc nhóm $g'$) lên Nhóm $g$ (với $g' \neq g$).

$$ S'_g = S_g \times \prod_{f \in CrossInfluence(g)} \left(1 + X_{f \to g} \cdot \hat{v}_f \right) $$

Trong đó:
*   $S_g$: Giá trị đại diện nhóm $g$ từ Tầng 1.
*   $\hat{v}_f$: Giá trị chuẩn hóa (0 → 1) của feature $f$ gây ảnh hưởng.
*   $X_{f \to g} > 0$: Feature $f$ làm **phình to** (Amplify) chi phí Nhóm $g$.
*   $X_{f \to g} < 0$: Feature $f$ làm **co lại** (Dampen) chi phí Nhóm $g$.

> **Ý nghĩa:** Tầng 2 cho phép một Feature đơn lẻ "vươn tay" sang Nhóm khác và bóp méo toàn bộ kết quả của nhóm đó.

---

## TẦNG 3: Group ↔ Group (Inter-group Dynamics)

### Mục tiêu
Xử lý quan hệ **giữa 12 Nhóm với nhau** ở mức vĩ mô nhất. 12 Nhóm đã có Giá trị Đại diện ($S'_g$ từ Tầng 2) giờ phải "đàm phán" để tìm ra Tổng Chi phí cuối cùng.

### Ma trận Quan hệ Liên nhóm (Inter-group Interaction Matrix)

|  | G1 | G2 | G3🤖 | G4 | G5 | G6 | G7 | G8🤖 | G9 | G10🤖 | G11 | G12 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **G1** | — | 🤝 | ⚔️ | 🤝 | 🤝 | 📈 | 📈 | · | · | ⚔️ | 📈 | · |
| **G2** | 🤝 | — | · | · | · | 📈 | · | · | · | · | · | · |
| **G3🤖** | ⚔️ | · | — | · | · | · | · | · | · | ⚔️ | · | · |
| **G4** | 🤝 | · | · | — | 🤝 | 📈 | · | · | 📈 | ⚔️ | · | 🤝 |
| **G5** | 🤝 | · | · | 🤝 | — | 📈 | 📈 | · | 📈 | · | · | 🤝 |
| **G6** | 📈 | 📈 | · | 📈 | 📈 | — | 📈 | 📈 | 📈 | · | 📈 | · |
| **G7** | 📈 | · | · | · | 📈 | 📈 | — | · | 📈 | · | 📈 | · |
| **G8🤖** | · | · | · | · | · | 📈 | · | — | 📈 | 📈 | · | · |
| **G9** | · | · | · | 📈 | 📈 | 📈 | 📈 | 📈 | — | ⚔️ | 📈 | 📈 |
| **G10🤖** | ⚔️ | · | ⚔️ | ⚔️ | · | · | · | 📈 | ⚔️ | — | 📈 | 🤝 |
| **G11** | 📈 | · | · | · | · | 📈 | 📈 | · | 📈 | 📈 | — | 🤝 |
| **G12** | · | · | · | 🤝 | 🤝 | · | · | · | 📈 | 🤝 | 🤝 | — |

**Chú thích:** ⚔️ Cạnh tranh | 🤝 Bổ trợ | 📈 Khuếch đại | · Tác động yếu/không đáng kể | 🤖 AI-Computed

### Công thức Tầng 3: Hàm Tổng Chi phí Cuối cùng (TGC)

$$
TGC = \sum_{g=1}^{12} \left( \beta_g \cdot S'_g \right) + \sum_{g=1}^{12} \sum_{h>g}^{12} \left( \gamma_{g,h} \cdot S'_g \cdot S'_h \right)
$$

Trong đó:
*   $\beta_g$: **Trọng số tầm quan trọng** của Nhóm $g$ (Hyperparameter — AI tự học hoặc chuyên gia đặt).
*   $\gamma_{g,h}$: **Hệ số tương tác liên nhóm** giữa Nhóm $g$ và Nhóm $h$.
    *   $\gamma > 0$: Hai nhóm khuếch đại lẫn nhau (Synergy/Amplification).
    *   $\gamma < 0$: Hai nhóm triệt tiêu lẫn nhau (Offset/Hedge).
    *   $\gamma = 0$: Không tương tác.
*   $S'_g \cdot S'_h$: **Tích chéo (Cross-product Term)** — đại diện cho hiệu ứng tương tác phi tuyến giữa 2 nhóm.

> **Ý nghĩa:** Tầng 3 giải quyết vấn đề mà phép cộng tuyến tính không bao giờ giải được: **Hiệu ứng cộng hưởng (Synergy)**. Ví dụ: Nếu cả "Rủi ro" (G9) VÀ "Thời gian" (G6) đều xấu cùng lúc, chi phí tổng không chỉ tăng gấp đôi mà tăng theo cấp số nhân — vì chúng khuếch đại lẫn nhau.

---

## Tổng hợp: Luồng xử lý hoàn chỉnh

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: Task i có 60 User-Input features (từ CSV/Database)   │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─ BƯỚC 0.5: AI Compute (Derived Features) ───────────────────┐
│                                                               │
│  G8 🤖: Đếm in/out-degree, tính Critical Path, Float         │
│         từ cấu trúc đồ thị (predecessors.csv)                │
│  G10🤖: So sánh lịch đề xuất vs Baseline                     │
│         → planned_value, earned_value, cpi, spi              │
│  G3 🤖: Ước tính Opportunity Cost từ kịch bản thay thế       │
│         → schedule_flexibility, delay_impact_cost            │
│                                                               │
│  → Vector đầy đủ: 60 + 12 = 72 Features                     │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─ TẦNG 1: Feature ↔ Feature (trong nhóm) ───────────────────┐
│                                                              │
│  Nhóm G1: internal_labor ⚔️ subcontracting 🤝 material ...  │
│           → Attention → S₁                                   │
│  Nhóm G2: pm_overhead 🤝 facility_rent 🤝 utilities ...     │
│           → Attention → S₂                                   │
│  ...                                                         │
│  Nhóm G12: environmental_impact 📈 carbon_tax ...            │
│           → Attention → S₁₂                                  │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─ TẦNG 2: Feature ↔ Group (xuyên nhóm) ─────────────────────┐
│                                                              │
│  duration_* (Hub) ──📈──→ S₂ (Gián tiếp): S'₂ = S₂ × (1+X)│
│  wait_queue_time (G6) ─📈──→ S₅ (Logistics): S'₅ = ...     │
│  request/capacity (G7) ─📈──→ S₁ (Trực tiếp): S'₁ = ...    │
│  rework_prob (G9) ──📈──→ S₄ (Hợp đồng): S'₄ = ...        │
│  out_degree 🤖 (G8) ──📈──→ S₉ (Rủi ro): S'₉ = ...        │
│  ...                                                         │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─ TẦNG 3: Group ↔ Group (liên nhóm) ────────────────────────┐
│                                                              │
│  TGC = Σ βg·S'g + Σ γgh·S'g·S'h                            │
│                                                              │
│  G6 (Thời gian) × G9 (Rủi ro) = Cộng hưởng thảm họa       │
│  G1 (Trực tiếp) × G10🤖 (Giá trị) = Bù trừ                │
│  G5 (Logistics) × G12 (ESG) = Ràng buộc xanh               │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT: Total Generalized Cost (TGC) cho Task i             │
└─────────────────────────────────────────────────────────────┘
```

---

## CƠ CHẾ THÍCH ỨNG: Loại bỏ Nhóm Trống (Adaptive Group Masking)

### Vấn đề thực tế
Trong một dự án Logistics thực tế, **không phải task nào cũng chạm đến cả 12 nhóm**. Ví dụ:

| Task mẫu | Nhóm có dữ liệu | Nhóm trống (Không áp dụng) |
| :--- | :--- | :--- |
| "Vận chuyển container từ cảng A → B" | G1, G5, G6, G7, G8🤖, G9, G12 | G2, G3🤖, G4, G10🤖, G11 |
| "Xin giấy phép hải quan" | G2, G4, G6, G8🤖 | G1, G3🤖, G5, G7, G9, G10🤖, G11, G12 |
| "Bốc xếp pallet tại kho" | G1, G5, G6, G7, G8🤖, G11, G12 | G2, G3🤖, G4, G9, G10🤖 |
| "Họp đánh giá rủi ro dự án" | G2, G8🤖, G9, G10🤖 | G1, G3🤖, G4, G5, G6, G7, G11, G12 |

> **Lưu ý:** G8 (Network Topology) gần như **luôn "sống"** vì mọi Task đều có ít nhất 1 cạnh trong đồ thị. G3 và G10 thường chỉ sống khi AI đang ở giai đoạn tối ưu hóa (có kịch bản để so sánh).

Nếu ép nhóm trống tham gia tính toán ($S_g = 0$), sẽ xảy ra 2 vấn đề:
1. **Nhiễu toán học:** Tích chéo $\gamma_{g,h} \cdot S'_g \cdot S'_h$ sẽ bị triệt tiêu vô nghĩa (nhân với 0).
2. **Lãng phí tính toán:** AI vẫn phải chạy Attention cho nhóm rỗng → chậm và tốn bộ nhớ.

### Giải pháp: Ma trận Mặt nạ Thích ứng (Adaptive Mask - $M$)

Định nghĩa **Vector Mặt nạ** $\mathbf{m}_i \in \{0, 1\}^{12}$ cho mỗi Task $i$:

$$
m_{i,g} = \begin{cases}
  1 & \text{nếu Task } i \text{ có ít nhất 1 feature thuộc Nhóm } g \text{ có giá trị } \neq 0 \\
  0 & \text{nếu tất cả features thuộc Nhóm } g \text{ đều bằng } 0 \text{ hoặc NULL}
\end{cases}
$$

### Áp Mask vào từng Tầng

**Tầng 1 (đã mask):** Chỉ tính Attention cho các nhóm "sống":
$$ S_g = \begin{cases} \sum_{f \in G_g} \alpha_f \cdot v_f & \text{nếu } m_{i,g} = 1 \\ \text{SKIP (không tính)} & \text{nếu } m_{i,g} = 0 \end{cases} $$

**Tầng 2 (đã mask):** Feature xuyên nhóm chỉ tác động lên nhóm "sống":
$$ S'_g = S_g \times \prod_{f \in Cross(g)} \left(1 + m_{i,g} \cdot X_{f \to g} \cdot \hat{v}_f \right) $$

**Tầng 3 (đã mask):** Chỉ tính tích chéo giữa các nhóm đều "sống":
$$ TGC_i = \sum_{g=1}^{12} m_{i,g} \cdot \beta_g \cdot S'_g + \sum_{g<h} m_{i,g} \cdot m_{i,h} \cdot \gamma_{g,h} \cdot S'_g \cdot S'_h $$

### Ví dụ minh họa

Task "Vận chuyển container" có $\mathbf{m} = [1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1]$

Số nhóm hoạt động: **7/12** → Giảm ~42% phép tính.

```
Tầng 1: Chỉ tính S₁, S₅, S₆, S₇, S₈, S₉, S₁₂  (Bỏ qua 5 nhóm trống)
Tầng 2: Chỉ xét Cross-influence vào 7 nhóm sống
Tầng 3: Tích chéo chỉ tính C(7,2) = 21 cặp thay vì C(12,2) = 66 cặp
```

> **Lợi ích:** Mỗi task có một "bộ nhóm hoạt động" (Active Group Set) riêng. AI tự động co giãn (elastic) theo đặc thù của từng task — không phí tài nguyên, không bị nhiễu.

---

## HỆ RÀNG BUỘC (Constraints) Tích hợp vào Kiến trúc 3 Tầng

Phương trình $TGC$ ở trên chỉ là **Hàm Mục tiêu** (Objective Function). Để kịch bản lập lịch $S$ hợp lệ (Feasible), nó phải vượt qua **Hệ Ràng buộc** dưới đây. Các ràng buộc này cũng được phân cấp theo 3 tầng tương ứng.

### Ràng buộc Tầng 1: Trong nội bộ Nhóm (Intra-group Constraints)

Đây là các giới hạn vật lý/logic mà các feature trong cùng 1 nhóm phải tuân thủ.

| Nhóm | Ràng buộc nội bộ | Công thức |
| :--- | :--- | :--- |
| **G1** (Trực tiếp) | Tổng nhân lực phân bổ ≤ Ngân sách nhân sự | `internal_labor + subcontracting + overtime ≤ Budget_Labor` |
| **G1** (Trực tiếp) | Thuê ngoài và Nội bộ loại trừ một phần | `internal_labor × subcontracting ≤ ε` |
| **G5** (Logistics) | Lưu kho + Vận chuyển phải đủ cho nhu cầu | `inventory_holding + international_freight ≥ MinServiceLevel` |
| **Hub** (Thời gian) | Thời gian hoàn thành = Bắt đầu + Kéo dài | `Finish_i = Start_i + Duration_i` |
| **G8🤖** (Topology) | Float không âm | `total_float ≥ 0` |
| **G7** (Tài nguyên) | Nhu cầu ≤ Khả dụng | `request_quantity ≤ capacity` |
| **G9** (Rủi ro) | Tổng xác suất rủi ro ≤ 1 | `Σ risk_probabilities ≤ 1` |
| **G12** (ESG) | Phát thải ≤ Hạn mức | `environmental_impact ≤ EmissionCap` |

### Ràng buộc Tầng 2: Xuyên Nhóm (Cross-group Constraints)

Đây là các ràng buộc liên kết giữa một Feature cụ thể và toàn bộ một Nhóm khác.

| Feature nguồn | Nhóm bị ràng buộc | Ràng buộc | Công thức |
| :--- | :--- | :--- | :--- |
| `duration_*` (Hub) | **G2** (Gián tiếp) | Duration = 0 → Toàn bộ G2 = 0 | `m[G2] = 1 nếu duration > 0` |
| `request/capacity > 1` (G7) | **G1** (Trực tiếp) | Khan hiếm → Buộc phải Thuê ngoài | `scarcity > 1 ⇒ subcontracting > 0` |
| `total_float = 0` 🤖 (G8) | **G9** (Rủi ro) | Task Critical → Rủi ro trễ tăng | `total_float = 0 ⇒ is_critical = 1` |
| `rework_prob > 0.5` (G9) | **G4** (Hợp đồng) | Xác suất trễ cao → Phải dự phòng | `rework > 0.5 ⇒ management_reserve ≥ penalty × E[Delay]` |
| `hr_stability_risk > 0.8` (G11) | **G1** (Trực tiếp) | Nhân sự bất ổn → Cấm OT thêm | `hr_risk > 0.8 ⇒ overtime = 0` |

### Ràng buộc Tầng 3: Giữa các Nhóm (Inter-group Constraints)

Đây là các ràng buộc vĩ mô ở cấp độ dự án, điều chỉnh sự tương tác giữa các nhóm.

**① Ràng buộc Trình tự Tuyệt đối (Precedence — G8🤖 ↔ Hub):**
Task $j$ chỉ được bắt đầu khi tất cả Predecessors (từ cấu trúc đồ thị G8) đã hoàn thành:
$$ Start_j \ge \max_{i \in Pred(j)} \left( Finish_i + WaitTime_{i,j} \right) $$

**② Ràng buộc Sức chứa Toàn cục (Capacity — G7 tác động G1, G5):**
Tại bất kỳ thời điểm $t$, tổng nhu cầu tài nguyên loại $k$ của tất cả task đang chạy không vượt giới hạn:
$$ \sum_{i \in Active(t)} request\_quantity_{i,k} \le capacity_k \quad \forall t, \forall k $$

**③ Ràng buộc Ngân sách Tổng (Budget — G1 + G2 + G4 + G5):**
Tổng tất cả chi phí tiền tệ của toàn bộ dự án không vượt ngân sách:
$$ \sum_{i=1}^{N} TGC_i \le TotalBudget $$

**④ Ràng buộc ESG Toàn Dự án (G12 tổng thể):**
Tổng phát thải Carbon của toàn bộ chuỗi Logistics không vượt mức trần cam kết:
$$ \sum_{i=1}^{N} environmental\_impact_i \le CarbonCap_{Project} $$

**⑤ Ràng buộc Deadline Dự án (G4 ↔ Hub):**
Thời điểm hoàn thành của task cuối cùng (Sink node) không vượt Deadline hợp đồng:
$$ Finish_{sink} \le Deadline_{Contract} $$

**⑥ Ràng buộc Chất lượng Tối thiểu (G10🤖):**
Earned Value tối thiểu phải đạt ngưỡng (không được cắt xén chất lượng để tiết kiệm):
$$ \frac{\sum earned\_value_i}{\sum planned\_value_i} \ge MinQualityThreshold \quad (\text{thường } \ge 0.9) $$

---

## Luồng xử lý HOÀN CHỈNH (Có AI Compute + Masking + Constraints)

```
┌──────────────────────────────────────────────────────────────────┐
│  INPUT: Task i có 60 User-Input features (từ CSV/Database)       │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌─ BƯỚC 0.5: AI Compute (Derived Features) ────────────────────────┐
│                                                                   │
│  G8 🤖: in_degree, out_degree, is_critical, total_float,         │
│         path_length  (từ predecessors.csv)                        │
│  G10🤖: planned_value, earned_value, cpi, spi                    │
│         (so sánh Schedule vs Baseline)                            │
│  G3 🤖: schedule_flexibility, resource_alternative_cost,          │
│         delay_impact_cost (so sánh kịch bản)                     │
│                                                                   │
│  → Full Vector: 60 + 12 = 72 Features                            │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌─ BƯỚC 1: Adaptive Masking ───────────────────────────────────────┐
│                                                                   │
│  Quét 12 nhóm → Tạo mặt nạ m = [1,0,0,0,1,1,1,1,1,0,0,1]       │
│  Nhóm sống: {G1, G5, G6, G7, G8🤖, G9, G12}  (7/12)            │
│  Nhóm chết: {G2, G3🤖, G4, G10🤖, G11} → SKIP hoàn toàn        │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌─ TẦNG 1: Feature ↔ Feature (chỉ nhóm sống) ─────────────────────┐
│                                                                   │
│  G1: internal_labor ⚔️ subcontracting 🤝 material → Att → S₁    │
│  G5: inventory ⚔️ international_freight 🤝 packaging → Att → S₅ │
│  G6: wait_queue 📈 lead_time                      → Att → S₆    │
│  G7: request_qty 📈 labor_productivity             → Att → S₇    │
│  G8🤖: in_degree 📈 out_degree 📈 is_critical     → Att → S₈    │
│  G9: rework_prob 📈 technical_complexity           → Att → S₉    │
│  G12: environmental_impact 📈 carbon_tax           → Att → S₁₂   │
│                                                                   │
│  ⚠️ Kiểm tra Ràng buộc Tầng 1:                                   │
│     internal_labor + subcontracting + overtime ≤ Budget? ✅        │
│     total_float ≥ 0? ✅                                            │
│     environmental_impact ≤ EmissionCap? ✅                         │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌─ TẦNG 2: Feature ↔ Group (xuyên nhóm, chỉ nhóm sống) ──────────┐
│                                                                   │
│  duration_* (Hub) ──📈──→ S₅ (Logistics): S'₅ = S₅ × (1 + X)   │
│  request/capacity (G7) ─📈──→ S₁ (Trực tiếp): S'₁ = S₁ × (1+X)│
│  rework_prob (G9) ──📈──→ S₁₂ (ESG): S'₁₂= S₁₂× (1 + X)      │
│  out_degree 🤖 (G8) ──📈──→ S₉ (Rủi ro): S'₉ = S₉ × (1 + X)  │
│                                                                   │
│  ⚠️ Kiểm tra Ràng buộc Tầng 2:                                   │
│     scarcity > 1 → Buộc subcontracting > 0? ✅                    │
│     hr_risk > 0.8 → Cấm overtime? (G11 đã mask → Bỏ qua) ✅      │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌─ TẦNG 3: Group ↔ Group (chỉ các cặp nhóm sống) ────────────────┐
│                                                                   │
│  Cặp hoạt động: (1,5), (1,6), (1,7), (1,8), (1,9), (1,12),     │
│                 (5,6), (5,7), (5,8), (5,9), (5,12),             │
│                 (6,7), (6,8), (6,9), (6,12),                     │
│                 (7,8), (7,9), (7,12),                             │
│                 (8,9), (8,12), (9,12)     → 21 cặp               │
│                                                                   │
│  TGC = Σ βg·S'g + Σ γgh·S'g·S'h                                 │
│                                                                   │
│  ⚠️ Kiểm tra Ràng buộc Tầng 3:                                   │
│     Σ TGC ≤ TotalBudget? ✅                                       │
│     Finish_sink ≤ Deadline? ✅                                     │
│     Σ environmental_impact ≤ CarbonCap? ✅                        │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  OUTPUT: TGC cho Task i  (Feasible ✅ / Infeasible ❌)            │
│                                                                  │
│  Nếu vi phạm bất kỳ Constraint nào → TGC = +∞ (Penalty hủy)    │
└──────────────────────────────────────────────────────────────────┘
```

---

## PHÂN LOẠI LOẠI TASK (Task Type Classification)

### Vấn đề
Ma trận 72×72 là **tổng thể (Global)**. Nhưng thực tế, mỗi loại công việc có cơ chế tương tác khác nhau:
*   Task "Vận chuyển": Duration tăng → Chi phí nhiên liệu tăng mạnh, nhưng Chi phí phòng họp = 0.
*   Task "Họp đánh giá": Duration tăng → Chi phí phòng họp tăng mạnh, nhưng Chi phí nhiên liệu = 0.

Cùng 1 ô trong ma trận (`a[Duration, Fuel]`), nhưng giá trị đúng phải khác nhau cho từng loại task. Một ma trận cố định không diễn tả được điều này.

### Giải pháp: Task Type + Vector Trọng số

Thay vì tạo nhiều ma trận riêng biệt (tốn bộ nhớ), chúng ta giữ nguyên 1 ma trận gốc và tạo thêm **Bảng Trọng số theo Loại Task (Task Type Weight Table)**.

### Định nghĩa 7 Loại Task trong Logistics

| Ký hiệu | Loại Task | Ví dụ trong DSLIB | Nhóm Feature nổi bật |
|:---:|:---|:---|:---|
| **T1** | Vận chuyển (Transport) | "Delivery of pin-piles", "Transport to Vlissingen" | G1, G5, G6, G7, G8🤖, G12 |
| **T2** | Bốc xếp / Kho (Warehouse) | "Loading jack-up platform", "Placing containers" | G1, G5, G6, G7, G8🤖, G11 |
| **T3** | Hành chính / Họp (Admin) | "Kick-off meeting", "Project charter" | G2, G4, G6, G8🤖, G9 |
| **T4** | Thi công / Lắp đặt (Construction) | "Foundation Work", "Crane installation" | G1, G6, G7, G8🤖, G9, G11 |
| **T5** | Kiểm tra / Nghiệm thu (Inspection) | "Testing supply hoppers", "Final check-up" | G1, G6, G8🤖, G9, G10🤖 |
| **T6** | Chờ đợi / Milestone (Wait) | "Concrete aging", "Approval milestone" | G3🤖, G6, G8🤖 |
| **T7** | Mua sắm / Đặt hàng (Procurement) | "Order 35 chalets", "Bottle supply" | G4, G5, G6, G8🤖 |

> **Lưu ý:** G8 (Network Topology) xuất hiện trong **tất cả 7 loại Task** vì mọi công việc đều nằm trong đồ thị dự án.

### Cơ chế hoạt động

```
Ma trận gốc A[72×72]  ←  CỐ ĐỊNH (Domain Knowledge chung)
        ×
Vector loại Task w[72] ←  THAY ĐỔI theo loại Task (T1...T7)
        =
Ma trận hiệu lực A'[72×72] ← Riêng cho loại Task đó
```

**Công thức:**

$$ A'_{f,q} = A_{f,q} \times w^{type}_f \times w^{type}_q $$

Trong đó $w^{type}_f$ là trọng số của feature $f$ trong loại Task hiện tại:
*   $w^{type}_f = 1.0$: Feature rất quan trọng cho loại task này.
*   $w^{type}_f = 0.0$: Feature không liên quan đến loại task này → Toàn bộ hàng/cột bị triệt tiêu.
*   $0 < w^{type}_f < 1$: Feature có liên quan một phần.

### Xác định Loại Task tự động (Regex)

```python
TASK_TYPE_RULES = {
    "T1_Transport": ["transport", "deliver", "ship", "freight", "haul"],
    "T2_Warehouse": ["load", "unload", "container", "pallet", "warehouse", "storage"],
    "T3_Admin":     ["meeting", "approval", "review", "charter", "permit"],
    "T4_Build":     ["install", "construct", "build", "excavat", "pour", "weld"],
    "T5_Inspect":   ["test", "inspect", "check", "commissioning", "quality"],
    "T6_Wait":      ["aging", "curing", "milestone", "wait", "dry"],
    "T7_Procure":   ["order", "procure", "purchase", "supply", "buy"],
}
```

### Xử lý Ngoại lệ (Unexpected Features)

**Câu hỏi:** *Lỡ một task "Vận chuyển" (T1) lại phát sinh chi phí "Họp hành" (G3) hoặc "Kiểm tra" (G10) thì sao?*

Để tránh việc "nuốt mất" dữ liệu thực tế do phân loại sai hoặc thiếu, hệ thống sử dụng **2 lớp lọc chồng lên nhau**:
1. **Lớp 1: Task Type Weights ($w$)** ← Dự đoán dựa trên Tên Task.
2. **Lớp 2: Adaptive Mask ($m$)** ← Thực tế dựa trên Dữ liệu.

**Lớp 2 (Dữ liệu thực) LUÔN THẮNG Lớp 1 (Dự đoán).**

**Nguyên tắc Vàng:** Không bao giờ đặt trọng số $w = 0.0$ cho Lớp 1. Thay vào đó, sử dụng **Giá trị sàn (Floor Values)**:

| Mức quan trọng (Lớp 1) | Giá trị $w$ | Ý nghĩa & Tác động nếu Lớp 2 BẬT ($m=1$) |
|:---|:---:|:---|
| Rất quan trọng (Core) | **1.0** | Tác động toàn lực (1.0 × v) |
| Quan trọng vừa | **0.6** | Đóng góp khá mạnh (0.6 × v) |
| Ít quan trọng | **0.3** | Vẫn được tính nhưng giảm nhẹ (0.3 × v) |
| Không điển hình | **0.1** | *Trường hợp ngoại lệ.* Gần như không xảy ra, nhưng NẾU thực tế có dữ liệu, nó vẫn không bị mất đi (0.1 × v). |

Nhờ áp dụng mức sàn $0.1$, nếu task Vận chuyển thực tế có phát sinh chi phí Kiểm tra chất lượng (500$), hệ thống vẫn ghi nhận (500$ \times 0.1 \times 1 = 50$) thay vì xóa bỏ hoàn toàn (nhân với 0).

---

## CHIẾN LƯỢC TỐI ƯU TÍNH TOÁN

### Chiến lược 1: Khai thác Tính Thưa (Sparsity)
Ma trận 72×72 thực tế **~95% là 0**. Chỉ lưu và tính toán các ô ≠ 0 (~250 ô).

### Chiến lược 2: Gộp Nhóm Tương đồng (Group Merging)
Các nhóm có hành vi gần giống nhau có thể gộp lại:
*   G1 (Trực tiếp) + G2 (Gián tiếp) → **G_Cost**
*   G9 (Rủi ro) + G11 (Con người) → **G_Risk**
*   G3🤖 (Cơ hội) + G10🤖 (Giá trị) → **G_Value** (Cả 2 đều AI-Computed)

Kết quả: 12 Nhóm → 9 Nhóm. Giảm 45% phép tính Tầng 3.

### Chiến lược 3: Cắt tỉa Feature (Feature Pruning)
Tính Impact Score cho mỗi feature: $Impact_f = \sum_{q \neq f} |a_{f,q}| + \sum_{g} |X_{f \to g}|$

Loại bỏ các feature có $Impact_f < threshold$. Ước tính giữ lại ~50/72 features.

### Chiến lược 4: Lazy Evaluation + Masking
Kết hợp tất cả chiến lược trên:

| Chỉ số | Không tối ưu | Sau tối ưu | Giảm |
|:---|:---:|:---:|:---:|
| Số Feature xử lý | 72 | ~50 | 31% |
| Số Nhóm xử lý (mỗi task) | 12 | ~7 (trung bình) | 42% |
| Số ô Ma trận phải tính | 5,184 | ~250 (sparse) | 95% |
| Số cặp tích chéo Tầng 3 | 66 | ~21 (masked + merged) | 68% |
| **Tổng phép tính** | **~5,500** | **~350** | **~94%** |

### Lưu ý quan trọng: Ma trận KHÔNG bị cắt
Ma trận 72×72 **luôn giữ nguyên kích thước**. Việc tối ưu được thực hiện bằng **Mask (nhân với 0)** tại thời điểm tính toán, không phải bằng cách xóa hàng/cột. Điều này đảm bảo:
1. Cấu trúc ma trận không bị phá vỡ.
2. Công thức Attention vẫn cho kết quả chính xác — Feature bị mask sẽ có $\alpha_f = 0$ (tự loại khỏi cuộc bầu cử).
3. Khi có dữ liệu mới (task có thêm feature), chỉ cần bật mask lên $m_f = 1$ mà không cần sửa ma trận.

---

## TỔNG KẾT: Hệ thống Ma trận Domain Knowledge hoàn chỉnh

| Thành phần | Kích thước | Vai trò | Ai tạo? |
|:---|:---:|:---|:---|
| **Ma trận 1** (Feature Interaction) | 72 × 72 | Tầng 1 (đường chéo) + Tầng 2 (ngoài đường chéo) | Chuyên gia đặt cấu trúc |
| **Ma trận 2** (Group Interaction) | 12 × 12 | Tầng 3 (Group ↔ Group) | Chuyên gia đặt toàn bộ |
| **Bảng Task Type Weights** | 7 × 72 | Trọng số feature theo loại công việc | Chuyên gia + Regex |

### Pipeline xử lý 1 Task hoàn chỉnh

```
① Đọc CSV → 60 User-Input Features
② AI Compute → +12 Derived Features (G3🤖, G8🤖, G10🤖) → Tổng: 72
③ Đọc tên Task → Regex → Xác định loại (VD: T1_Transport)
④ Lấy Vector trọng số w_T1 từ Bảng Task Type Weights (7×72)
⑤ Ma trận hiệu lực A' = A_global ⊙ (w × wᵀ)
⑥ Adaptive Mask m[72] (feature nào có giá trị ≠ 0)
⑦ Tầng 1: Attention trên A' + Mask → S_g cho mỗi nhóm sống
⑧ Tầng 2: Cross-influence (chỉ nhóm sống) → S'_g
⑨ Tầng 3: Ma trận Group 12×12 → TGC
⑩ Kiểm tra Constraints ở cả 3 tầng → Feasible ✅ / Infeasible ❌
```
