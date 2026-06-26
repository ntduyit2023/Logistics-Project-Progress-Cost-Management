# Kiến trúc Đánh giá Phân cấp 3 Tầng (Hierarchical 3-Level Evaluation)
*Giữa Feature ↔ Feature, Feature ↔ Group, Group ↔ Group*

---

## Tổng quan Kiến trúc

Thay vì "nấu" tất cả 91 features vào 1 hàm duy nhất, chúng ta xử lý theo chuỗi **3 tầng (Bottom-Up)**:

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

## TẦNG 1: Feature ↔ Feature (Intra-group Aggregation)

### Mục tiêu
Xử lý **bên trong từng Nhóm** trước. Mỗi Nhóm $g$ chứa $n_g$ features. Các features này không độc lập — chúng **cạnh tranh, bổ trợ, hoặc triệt tiêu** lẫn nhau.

### Các loại Quan hệ Feature ↔ Feature (trong cùng nhóm)

| Ký hiệu | Loại quan hệ | Ví dụ cụ thể |
| :---: | :--- | :--- |
| ⚔️ | **Cạnh tranh (Competitive)** | $F_{1.1}$ (Nhân công nội bộ) vs $F_{1.2}$ (Thuê ngoài): Tăng cái này thì giảm cái kia |
| 🤝 | **Bổ trợ (Complementary)** | $F_{1.4}$ (Nguyên vật liệu) + $F_{1.6}$ (Vận chuyển): Mua nhiều vật liệu thì phí ship cũng tăng |
| 🔄 | **Thay thế (Substitutable)** | $F_{1.1}$ (Nội bộ) ↔ $F_{1.2}$ (Thuê ngoài): Dùng cái này thì không cần cái kia |
| 📈 | **Khuếch đại (Amplifying)** | $F_{9.1}$ (Xác suất trễ) × $F_{9.5}$ (Xác suất làm lại): Trễ càng nhiều, làm lại càng nhiều |

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
| $F_{6.1}$ (Planned Duration) | → **G2** (Chi phí Gián tiếp) | Duration kéo dài → Toàn bộ Nhóm G2 tăng (Thuê VP, Tiện ích, PM) |
| $F_{6.8}$ (Wait/Queue Time) | → **G5** (Logistics & SCM) | Chờ đợi lâu → Lưu kho ($F_{5.1}$), Hết hạn ($F_{5.4}$) đều tăng |
| $F_{7.3}$ (Resource Scarcity) | → **G1** (Chi phí Trực tiếp) | Khan hiếm tài nguyên → Giá thuê ngoài ($F_{1.2}$), OT ($F_{1.3}$) tăng |
| $F_{9.1}$ (Delay Probability) | → **G4** (Hợp đồng & Pháp lý) | Xác suất trễ cao → Penalty ($F_{4.1}$) gần như chắc chắn phải trả |
| $F_{8.2}$ (Out-degree) | → **G9** (Rủi ro) | Node có Out-degree cao → Rủi ro lan truyền ($F_{9.4}$) tăng mạnh |
| $F_{11.4}$ (Fatigue Risk) | → **G10** (Chất lượng) | Nhân sự kiệt sức → Phải làm lại ($F_{9.5}$), CPI giảm ($F_{10.2}$) |

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

|  | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 | G10 | G11 | G12 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **G1** | — | 🤝 | ⚔️ | 🤝 | 🤝 | 📈 | 📈 | · | · | ⚔️ | 📈 | · |
| **G2** | 🤝 | — | · | · | · | 📈 | · | · | · | · | · | · |
| **G3** | ⚔️ | · | — | · | · | · | · | · | · | ⚔️ | · | · |
| **G4** | 🤝 | · | · | — | 🤝 | 📈 | · | · | 📈 | ⚔️ | · | 🤝 |
| **G5** | 🤝 | · | · | 🤝 | — | 📈 | 📈 | · | 📈 | · | · | 🤝 |
| **G6** | 📈 | 📈 | · | 📈 | 📈 | — | 📈 | 📈 | 📈 | · | 📈 | · |
| **G7** | 📈 | · | · | · | 📈 | 📈 | — | · | 📈 | · | 📈 | · |
| **G8** | · | · | · | · | · | 📈 | · | — | 📈 | 📈 | · | · |
| **G9** | · | · | · | 📈 | 📈 | 📈 | 📈 | 📈 | — | ⚔️ | 📈 | 📈 |
| **G10** | ⚔️ | · | ⚔️ | ⚔️ | · | · | · | 📈 | ⚔️ | — | 📈 | 🤝 |
| **G11** | 📈 | · | · | · | · | 📈 | 📈 | · | 📈 | 📈 | — | 🤝 |
| **G12** | · | · | · | 🤝 | 🤝 | · | · | · | 📈 | 🤝 | 🤝 | — |

**Chú thích:** ⚔️ Cạnh tranh | 🤝 Bổ trợ | 📈 Khuếch đại | · Tác động yếu/không đáng kể

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
│  INPUT: Task i có vector 91 features (giá trị thô v_f)      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─ TẦNG 1: Feature ↔ Feature (trong nhóm) ───────────────────┐
│                                                              │
│  Nhóm G1: F1.1 ⚔️ F1.2 ⚔️ F1.3 🤝 F1.4 ...                │
│           → Attention → S₁                                   │
│  Nhóm G2: F2.1 🤝 F2.2 🤝 F2.3 ...                         │
│           → Attention → S₂                                   │
│  ...                                                         │
│  Nhóm G12: F12.1 📈 F12.4 ...                               │
│           → Attention → S₁₂                                  │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─ TẦNG 2: Feature ↔ Group (xuyên nhóm) ─────────────────────┐
│                                                              │
│  F6.1 (Duration) ──📈──→ S₂ (Gián tiếp): S'₂ = S₂ × (1+X) │
│  F6.8 (Wait Time) ──📈──→ S₅ (Logistics): S'₅ = S₅ × (1+X)│
│  F7.3 (Scarcity) ──📈──→ S₁ (Trực tiếp): S'₁ = S₁ × (1+X) │
│  F9.1 (Delay Prob) ─📈──→ S₄ (Hợp đồng): S'₄ = S₄ × (1+X)│
│  ...                                                         │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─ TẦNG 3: Group ↔ Group (liên nhóm) ────────────────────────┐
│                                                              │
│  TGC = Σ βg·S'g + Σ γgh·S'g·S'h                            │
│                                                              │
│  G6 (Thời gian) × G9 (Rủi ro) = Cộng hưởng thảm họa       │
│  G1 (Trực tiếp) × G10 (Giá trị) = Bù trừ                  │
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
| "Vận chuyển container từ cảng A → B" | G1, G5, G6, G7, G9, G12 | G2, G3, G4, G8, G10, G11 |
| "Xin giấy phép hải quan" | G2, G4, G6 | G1, G3, G5, G7, G8, G9, G10, G11, G12 |
| "Bốc xếp pallet tại kho" | G1, G5, G6, G7, G11, G12 | G2, G3, G4, G8, G9, G10 |
| "Họp đánh giá rủi ro dự án" | G2, G9, G10 | G1, G3, G4, G5, G6, G7, G8, G11, G12 |

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

Task "Vận chuyển container" có $\mathbf{m} = [1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1]$

Số nhóm hoạt động: **6/12** → Giảm 50% phép tính.

```
Tầng 1: Chỉ tính S₁, S₅, S₆, S₇, S₉, S₁₂  (Bỏ qua 6 nhóm trống)
Tầng 2: Chỉ xét Cross-influence vào 6 nhóm sống
Tầng 3: Tích chéo chỉ tính C(6,2) = 15 cặp thay vì C(12,2) = 66 cặp
```

> **Lợi ích:** Mỗi task có một "bộ nhóm hoạt động" (Active Group Set) riêng. AI tự động co giãn (elastic) theo đặc thù của từng task — không phí tài nguyên, không bị nhiễu.

---

## HỆ RÀNG BUỘC (Constraints) Tích hợp vào Kiến trúc 3 Tầng

Phương trình $TGC$ ở trên chỉ là **Hàm Mục tiêu** (Objective Function). Để kịch bản lập lịch $S$ hợp lệ (Feasible), nó phải vượt qua **Hệ Ràng buộc** dưới đây. Các ràng buộc này cũng được phân cấp theo 3 tầng tương ứng.

### Ràng buộc Tầng 1: Trong nội bộ Nhóm (Intra-group Constraints)

Đây là các giới hạn vật lý/logic mà các feature trong cùng 1 nhóm phải tuân thủ.

| Nhóm | Ràng buộc nội bộ | Công thức |
| :--- | :--- | :--- |
| **G1** (Trực tiếp) | Tổng nhân lực phân bổ ≤ Ngân sách nhân sự | $F_{1.1} + F_{1.2} + F_{1.3} \le Budget^{Labor}_i$ |
| **G1** (Trực tiếp) | Thuê ngoài và Nội bộ loại trừ một phần | $F_{1.1} \times F_{1.2} \le \epsilon$ (Không thể dùng cả 2 ở mức tối đa) |
| **G5** (Logistics) | Lưu kho + Vận chuyển phải đủ cho nhu cầu | $F_{5.1} + F_{5.5} \ge MinServiceLevel_i$ |
| **G6** (Thời gian) | Thời gian hoàn thành = Bắt đầu + Kéo dài | $Finish_i = Start_i + Duration_i$ |
| **G6** (Thời gian) | Float không âm | $F_{6.2} \ge 0$ |
| **G7** (Tài nguyên) | Nhu cầu ≤ Khả dụng | $F_{7.1,k} \le F_{7.3,k}^{-1} \times Capacity_k$ |
| **G9** (Rủi ro) | Tổng xác suất rủi ro ≤ 1 | $\sum F_{9.x} \le 1$ cho các xác suất cùng sự kiện |
| **G12** (ESG) | Phát thải ≤ Hạn mức | $F_{12.1,i} \le EmissionCap_i$ |

### Ràng buộc Tầng 2: Xuyên Nhóm (Cross-group Constraints)

Đây là các ràng buộc liên kết giữa một Feature cụ thể và toàn bộ một Nhóm khác.

| Feature nguồn | Nhóm bị ràng buộc | Ràng buộc | Công thức |
| :--- | :--- | :--- | :--- |
| $F_{6.1}$ (Duration) | **G2** (Gián tiếp) | Duration = 0 → Toàn bộ G2 = 0 | $m_{i,2} = \mathbb{1}[F_{6.1} > 0]$ |
| $F_{7.3}$ (Scarcity > 1) | **G1** (Trực tiếp) | Khan hiếm → Buộc phải Thuê ngoài | $F_{7.3} > 1 \Rightarrow F_{1.2} > 0$ |
| $F_{6.2}$ (Float = 0) | **G9** (Rủi ro) | Task Critical → Rủi ro trễ tăng | $F_{6.2} = 0 \Rightarrow F_{9.2} = 1$ (Criticality = 100%) |
| $F_{9.1}$ (Delay > 0.5) | **G4** (Hợp đồng) | Xác suất trễ cao → Phải dự phòng Penalty | $F_{9.1} > 0.5 \Rightarrow F_{9.7} \ge F_{4.1} \times E[Delay]$ |
| $F_{11.4}$ (Fatigue > 0.8) | **G1** (Trực tiếp) | Kiệt sức → Cấm OT thêm | $F_{11.4} > 0.8 \Rightarrow F_{1.3} = 0$ |

### Ràng buộc Tầng 3: Giữa các Nhóm (Inter-group Constraints)

Đây là các ràng buộc vĩ mô ở cấp độ dự án, điều chỉnh sự tương tác giữa các nhóm.

**① Ràng buộc Trình tự Tuyệt đối (Precedence - G6 ↔ G8):**
Task $j$ chỉ được bắt đầu khi tất cả Predecessors ($Pred(j)$ từ cấu trúc đồ thị G8) đã hoàn thành:
$$ Start_j \ge \max_{i \in Pred(j)} \left( Finish_i + WaitTime_{i,j} \right) $$

**② Ràng buộc Sức chứa Toàn cục (Capacity - G7 tác động G1, G5):**
Tại bất kỳ thời điểm $t$, tổng nhu cầu tài nguyên loại $k$ của tất cả task đang chạy không vượt giới hạn:
$$ \sum_{i \in Active(t)} Demand_{i,k} \le MaxCapacity_k \quad \forall t, \forall k $$

**③ Ràng buộc Ngân sách Tổng (Budget - G1 + G2 + G4 + G5):**
Tổng tất cả chi phí tiền tệ của toàn bộ dự án không vượt ngân sách:
$$ \sum_{i=1}^{N} TGC_i \le TotalBudget $$

**④ Ràng buộc ESG Toàn Dự án (G12 tổng thể):**
Tổng phát thải Carbon của toàn bộ chuỗi Logistics không vượt mức trần cam kết:
$$ \sum_{i=1}^{N} F_{12.1,i} \le CarbonCap_{Project} $$

**⑤ Ràng buộc Deadline Dự án (G4 ↔ G6):**
Thời điểm hoàn thành của task cuối cùng (Sink node) không vượt Deadline hợp đồng:
$$ Finish_{sink} \le Deadline_{Contract} $$

**⑥ Ràng buộc Chất lượng Tối thiểu (G10):**
Earned Value tối thiểu phải đạt ngưỡng (không được cắt xén chất lượng để tiết kiệm):
$$ \frac{\sum EV_i}{\sum PV_i} \ge MinQualityThreshold \quad (\text{thường } \ge 0.9) $$

---

## Luồng xử lý HOÀN CHỈNH (Có Masking + Constraints)

```
┌──────────────────────────────────────────────────────────────────┐
│  INPUT: Task i có vector 91 features (giá trị thô v_f)           │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌─ BƯỚC 0: Adaptive Masking ──────────────────────────────────────┐
│                                                                  │
│  Quét 12 nhóm → Tạo mặt nạ m = [1,0,0,0,1,1,1,0,1,0,0,1]      │
│  Nhóm sống: {G1, G5, G6, G7, G9, G12}  (6/12)                  │
│  Nhóm chết: {G2, G3, G4, G8, G10, G11} → SKIP hoàn toàn        │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌─ TẦNG 1: Feature ↔ Feature (chỉ nhóm sống) ────────────────────┐
│                                                                  │
│  G1: F1.1 ⚔️ F1.2 ⚔️ F1.3 🤝 F1.6 → Attention → S₁           │
│  G5: F5.1 ⚔️ F5.5 🤝 F5.6        → Attention → S₅             │
│  G6: F6.1 📈 F6.8                 → Attention → S₆             │
│  G7: F7.1 📈 F7.3                 → Attention → S₇             │
│  G9: F9.1 📈 F9.5                 → Attention → S₉             │
│  G12: F12.1 📈 F12.4              → Attention → S₁₂            │
│                                                                  │
│  ⚠️ Kiểm tra Ràng buộc Tầng 1:                                  │
│     F1.1 + F1.2 + F1.3 ≤ Budget? ✅                             │
│     F6.2 ≥ 0? ✅                                                 │
│     F12.1 ≤ EmissionCap? ✅                                      │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌─ TẦNG 2: Feature ↔ Group (xuyên nhóm, chỉ nhóm sống) ─────────┐
│                                                                  │
│  F6.1 (Duration) ──📈──→ S₅ (Logistics): S'₅ = S₅ × (1 + X)   │
│  F7.3 (Scarcity) ──📈──→ S₁ (Trực tiếp): S'₁ = S₁ × (1 + X)  │
│  F9.1 (Delay Prob) ─📈──→ S₁₂ (ESG):     S'₁₂= S₁₂× (1 + X)  │
│                                                                  │
│  ⚠️ Kiểm tra Ràng buộc Tầng 2:                                  │
│     F7.3 > 1 → Buộc F1.2 > 0? ✅                                │
│     F11.4 > 0.8 → Cấm F1.3? (G11 đã mask → Bỏ qua) ✅          │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌─ TẦNG 3: Group ↔ Group (chỉ các cặp nhóm sống) ────────────────┐
│                                                                  │
│  Cặp hoạt động: (1,5), (1,6), (1,7), (1,9), (1,12),            │
│                 (5,6), (5,7), (5,9), (5,12),                    │
│                 (6,7), (6,9), (6,12),                            │
│                 (7,9), (7,12), (9,12)     → 15 cặp              │
│                                                                  │
│  TGC = Σ βg·S'g + Σ γgh·S'g·S'h                                │
│                                                                  │
│  ⚠️ Kiểm tra Ràng buộc Tầng 3:                                  │
│     Σ TGC ≤ TotalBudget? ✅                                      │
│     Finish_sink ≤ Deadline? ✅                                    │
│     Σ Emission ≤ CarbonCap? ✅                                   │
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
Ma trận 91×91 là **tổng thể (Global)**. Nhưng thực tế, mỗi loại công việc có cơ chế tương tác khác nhau:
*   Task "Vận chuyển": Duration tăng → Chi phí nhiên liệu tăng mạnh, nhưng Chi phí phòng họp = 0.
*   Task "Họp đánh giá": Duration tăng → Chi phí phòng họp tăng mạnh, nhưng Chi phí nhiên liệu = 0.

Cùng 1 ô trong ma trận (`a[Duration, Fuel]`), nhưng giá trị đúng phải khác nhau cho từng loại task. Một ma trận cố định không diễn tả được điều này.

### Giải pháp: Task Type + Vector Trọng số

Thay vì tạo nhiều ma trận riêng biệt (tốn bộ nhớ), chúng ta giữ nguyên 1 ma trận gốc và tạo thêm **Bảng Trọng số theo Loại Task (Task Type Weight Table)**.

### Định nghĩa 7 Loại Task trong Logistics

| Ký hiệu | Loại Task | Ví dụ trong DSLIB | Nhóm Feature nổi bật |
|:---:|:---|:---|:---|
| **T1** | Vận chuyển (Transport) | "Delivery of pin-piles", "Transport to Vlissingen" | G1, G5, G6, G7, G12 |
| **T2** | Bốc xếp / Kho (Warehouse) | "Loading jack-up platform", "Placing containers" | G1, G5, G6, G7, G11 |
| **T3** | Hành chính / Họp (Admin) | "Kick-off meeting", "Project charter" | G2, G4, G6, G9 |
| **T4** | Thi công / Lắp đặt (Construction) | "Foundation Work", "Crane installation" | G1, G6, G7, G9, G11 |
| **T5** | Kiểm tra / Nghiệm thu (Inspection) | "Testing supply hoppers", "Final check-up" | G1, G6, G9, G10 |
| **T6** | Chờ đợi / Milestone (Wait) | "Concrete aging", "Approval milestone" | G3, G6 |
| **T7** | Mua sắm / Đặt hàng (Procurement) | "Order 35 chalets", "Bottle supply" | G4, G5, G6 |

### Cơ chế hoạt động

```
Ma trận gốc A[91×91]  ←  CỐ ĐỊNH (Domain Knowledge chung)
        ×
Vector loại Task w[91] ←  THAY ĐỔI theo loại Task (T1...T7)
        =
Ma trận hiệu lực A'[91×91] ← Riêng cho loại Task đó
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
Ma trận 91×91 thực tế **~96% là 0**. Chỉ lưu và tính toán các ô ≠ 0 (~300 ô).

### Chiến lược 2: Gộp Nhóm Tương đồng (Group Merging)
Các nhóm có hành vi gần giống nhau có thể gộp lại:
*   G1 (Trực tiếp) + G2 (Gián tiếp) → **G_Cost**
*   G9 (Rủi ro) + G11 (Con người) → **G_Risk**
*   G3 (Cơ hội) + G10 (Giá trị) → **G_Value**

Kết quả: 12 Nhóm → 9 Nhóm. Giảm 45% phép tính Tầng 3.

### Chiến lược 3: Cắt tỉa Feature (Feature Pruning)
Tính Impact Score cho mỗi feature: $Impact_f = \sum_{q \neq f} |a_{f,q}| + \sum_{g} |X_{f \to g}|$

Loại bỏ các feature có $Impact_f < threshold$. Ước tính giữ lại ~60/91 features.

### Chiến lược 4: Lazy Evaluation + Masking
Kết hợp tất cả chiến lược trên:

| Chỉ số | Không tối ưu | Sau tối ưu | Giảm |
|:---|:---:|:---:|:---:|
| Số Feature xử lý | 91 | ~60 | 34% |
| Số Nhóm xử lý (mỗi task) | 12 | ~6 (trung bình) | 50% |
| Số ô Ma trận phải tính | 8,281 | ~300 (sparse) | 96% |
| Số cặp tích chéo Tầng 3 | 66 | ~15 (masked + merged) | 77% |
| **Tổng phép tính** | **~8,500** | **~400** | **~95%** |

### Lưu ý quan trọng: Ma trận KHÔNG bị cắt
Ma trận 91×91 **luôn giữ nguyên kích thước**. Việc tối ưu được thực hiện bằng **Mask (nhân với 0)** tại thời điểm tính toán, không phải bằng cách xóa hàng/cột. Điều này đảm bảo:
1. Cấu trúc ma trận không bị phá vỡ.
2. Công thức Attention vẫn cho kết quả chính xác — Feature bị mask sẽ có $\alpha_f = 0$ (tự loại khỏi cuộc bầu cử).
3. Khi có dữ liệu mới (task có thêm feature), chỉ cần bật mask lên $m_f = 1$ mà không cần sửa ma trận.

---

## TỔNG KẾT: Hệ thống Ma trận Domain Knowledge hoàn chỉnh

| Thành phần | Kích thước | Vai trò | Ai tạo? |
|:---|:---:|:---|:---|
| **Ma trận 1** (Feature Interaction) | 91 × 91 | Tầng 1 (đường chéo) + Tầng 2 (ngoài đường chéo) | Chuyên gia đặt cấu trúc |
| **Ma trận 2** (Group Interaction) | 12 × 12 | Tầng 3 (Group ↔ Group) | Chuyên gia đặt toàn bộ |
| **Bảng Task Type Weights** | 7 × 91 | Trọng số feature theo loại công việc | Chuyên gia + Regex |

### Pipeline xử lý 1 Task hoàn chỉnh

```
① Đọc tên Task → Regex → Xác định loại (VD: T1_Transport)
② Lấy Vector trọng số w_T1 từ Bảng Task Type Weights (7×91)
③ Ma trận hiệu lực A' = A_global ⊙ (w × wᵀ)
④ Adaptive Mask m[91] (feature nào có giá trị ≠ 0)
⑤ Tầng 1: Attention trên A' + Mask → S_g cho mỗi nhóm sống
⑥ Tầng 2: Cross-influence (chỉ nhóm sống) → S'_g
⑦ Tầng 3: Ma trận Group 12×12 → TGC
⑧ Kiểm tra Constraints ở cả 3 tầng → Feasible ✅ / Infeasible ❌
```

