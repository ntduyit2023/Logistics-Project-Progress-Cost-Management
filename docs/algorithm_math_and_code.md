# TOÁN HỌC VÀ MÃ NGUỒN CỐT LÕI (CORE ALGORITHMS)
## Đồ án Quản lý Tiến độ và Chi phí Logistics

Tài liệu này trình bày các mô hình toán học và đoạn mã Python (dựa trên thư viện `networkx`) được sử dụng trong hệ thống.

---

## 1. THUẬT TOÁN ĐƯỜNG GĂNG (CPM - Critical Path Method)

### 1.1. Mô hình Toán học
Ký hiệu đồ thị có hướng không chu trình $G = (V, E)$.
- $V$: Tập hợp các công việc (Nodes).
- $E$: Tập hợp sự phụ thuộc $i \rightarrow j$ (Edges).
- $d_i$: Thời gian thực hiện (Duration) của công việc $i$.

**A. Forward Pass (Lịch sớm)**
Tính thời điểm bắt đầu sớm ($ES$) và kết thúc sớm ($EF$):
* Điều kiện biên (Công việc gốc): $ES_{start} = 0$
* Công thức đệ quy:
  $$ES_i = \max_{j \in Pred(i)} \{ EF_j \}$$
  $$EF_i = ES_i + d_i$$

**B. Backward Pass (Lịch trễ)**
Tính thời điểm bắt đầu trễ ($LS$) và kết thúc trễ ($LF$):
* Điều kiện biên (Công việc cuối): $LF_{end} = \max_{v \in V} \{ EF_v \}$
* Công thức đệ quy:
  $$LF_i = \min_{j \in Succ(i)} \{ LS_j \}$$
  $$LS_i = LF_i - d_i$$

**C. Thời gian dự trữ (Slack) & Phân loại**
* Thời gian dự trữ: $Slack_i = LS_i - ES_i$
* Điều kiện Đường găng: Nếu $Slack_i = 0 \Rightarrow$ Công việc $i$ thuộc Đường găng (Critical Task).

### 1.2. Python Code (NetworkX)

```python
import networkx as nx

def calculate_cpm(G: nx.DiGraph):
    # 1. Forward Pass
    for node in nx.topological_sort(G):
        preds = list(G.predecessors(node))
        if not preds:
            G.nodes[node]['es'] = 0
        else:
            G.nodes[node]['es'] = max(G.nodes[p]['ef'] for p in preds)
        
        G.nodes[node]['ef'] = G.nodes[node]['es'] + G.nodes[node]['duration']

    # 2. Project End Time
    project_duration = max(nx.get_node_attributes(G, 'ef').values())

    # 3. Backward Pass
    for node in reversed(list(nx.topological_sort(G))):
        succs = list(G.successors(node))
        if not succs:
            G.nodes[node]['lf'] = project_duration
        else:
            G.nodes[node]['lf'] = min(G.nodes[s]['ls'] for s in succs)
            
        G.nodes[node]['ls'] = G.nodes[node]['lf'] - G.nodes[node]['duration']
        
        # Calculate Slack and Critical Flag
        G.nodes[node]['slack'] = G.nodes[node]['ls'] - G.nodes[node]['es']
        G.nodes[node]['is_critical'] = (G.nodes[node]['slack'] == 0)

    return G, project_duration
```

---

## 2. THUẬT TOÁN SAN BẰNG TÀI NGUYÊN (HEURISTIC RESOURCE SMOOTHING)

### 2.1. Mô hình Toán học
Gọi $R_{i}$ là số lượng tài nguyên cần cho công việc $i$.
Tổng tài nguyên sử dụng trong ngày $t$ là $U_t$:
$$U_t = \sum_{i \in Active(t)} R_i \quad \text{với} \quad Active(t) = \{ i \mid ES_i \le t < EF_i \}$$

**Mục tiêu (Objective Function):** Giảm thiểu sai số phân phối (hoặc hạ đỉnh Peak xuống dưới mức $Max\_Capacity$):
$$\min \sum_{t=1}^{T} (U_t - U_{target})^2$$

**Heuristic Constraint:** 
* Chỉ dịch chuyển ngày bắt đầu mới $ES'_i$ trong giới hạn dự trữ: $ES_i \le ES'_i \le LS_i$ (Nghĩa là $\Delta ES_i \le Slack_i$).

### 2.2. Python Code (Heuristic)

```python
def resource_smoothing(G: nx.DiGraph, max_capacity: int):
    T_project = max(nx.get_node_attributes(G, 'ef').values())
    
    # Hàm tính profile sử dụng tài nguyên
    def get_daily_usage(graph):
        usage = [0] * T_project
        for node, data in graph.nodes(data=True):
            for t in range(data['es'], data['ef']):
                usage[t] += data.get('resource_need', 0)
        return usage

    daily_usage = get_daily_usage(G)
    
    # Quét qua các ngày bị Overload
    for t in range(T_project):
        while daily_usage[t] > max_capacity:
            # Lọc các công việc đang chạy trong ngày t, không phải đường găng, còn slack
            candidates = [
                n for n in G.nodes() 
                if G.nodes[n]['es'] <= t < G.nodes[n]['ef'] 
                and G.nodes[n]['slack'] > 0
            ]
            
            if not candidates:
                break # Không thể san bằng thêm (Bất khả thi)
                
            # Heuristic: Chọn công việc có Slack lớn nhất để dời đi 1 ngày
            best_task = max(candidates, key=lambda x: G.nodes[x]['slack'])
            
            # Tịnh tiến ES và giảm Slack
            G.nodes[best_task]['es'] += 1
            G.nodes[best_task]['ef'] += 1
            G.nodes[best_task]['slack'] -= 1
            
            # Cập nhật lại biểu đồ tài nguyên
            daily_usage = get_daily_usage(G)
            
    return G
```

---

## 3. THUẬT TOÁN ÉP TIẾN ĐỘ BẰNG THAM LAM (GREEDY CRASHING)

### 3.1. Mô hình Toán học
Tính Hệ số chi phí cận biên (Cost Slope) $S_i$ cho mỗi công việc:
$$S_i = \frac{C_{crash_i} - C_{normal_i}}{D_{normal_i} - D_{crash_i}}$$

Thuật toán tham lam sẽ tìm phần tử thuộc đường găng $CP$:
$$i^* = \arg\min_{i \in CP \text{ và } D_i > D_{crash_i}} S_i$$
Và thực hiện gán $D_{i^*} = D_{i^*} - 1$. Sau đó cập nhật lại toàn bộ đồ thị.

### 3.2. Python Code (Greedy Loop)

```python
def project_crashing(G: nx.DiGraph, target_duration: int):
    # Tính Cost Slope cho tất cả các node
    for node, data in G.nodes(data=True):
        delta_c = data['crash_cost'] - data['normal_cost']
        delta_d = data['normal_duration'] - data['crash_duration']
        data['cost_slope'] = delta_c / delta_d if delta_d > 0 else float('inf')
        
        # Gán thời gian chạy bằng normal_duration lúc khởi tạo
        data['duration'] = data['normal_duration']
        
    G, current_dur = calculate_cpm(G)
    total_added_cost = 0

    while current_dur > target_duration:
        # Lấy các task găng có thể crash
        critical_candidates = [
            n for n in G.nodes()
            if G.nodes[n]['is_critical'] 
            and G.nodes[n]['duration'] > G.nodes[n]['crash_duration']
        ]
        
        if not critical_candidates:
            raise Exception("Đã ép kịch kim, không thể rút ngắn hơn được nữa!")
            
        # Tìm Task có Cost Slope thấp nhất (Tham lam)
        cheapest_task = min(critical_candidates, key=lambda x: G.nodes[x]['cost_slope'])
        
        # Ép 1 đơn vị thời gian
        G.nodes[cheapest_task]['duration'] -= 1
        total_added_cost += G.nodes[cheapest_task]['cost_slope']
        
        # Re-calculate lại CPM vì đường găng có thể đã thay đổi
        G, current_dur = calculate_cpm(G)
        
    return G, total_added_cost
```

---

## 4. QUẢN LÝ GIÁ TRỊ THU ĐƯỢC (EVA - EARNED VALUE ANALYSIS)

### 4.1. Công thức Toán học
Giả sử dự án được kiểm tra tại thời điểm $T_{now}$.
*   **Giá trị kế hoạch (PV - Planned Value):**
    $$PV = \sum_{i \in Started} ( \text{Ngân sách}_i \times \text{Tỷ lệ % thời gian lý thuyết đã trôi qua} )$$
*   **Giá trị thu được (EV - Earned Value):**
    $$EV = \sum_{i=1}^{n} (\text{Ngân sách}_i \times \text{Tiến độ hoàn thành thực tế %}_i)$$
*   **Các chỉ số đánh giá (Indices):**
    $$SPI = \frac{EV}{PV} \quad (SPI < 1 \rightarrow \text{Trễ tiến độ})$$
    $$CPI = \frac{EV}{AC} \quad (CPI < 1 \rightarrow \text{Vượt chi phí})$$

### 4.2. Python Code

```python
def calculate_eva(tasks_data: list, current_time: int, total_actual_cost: float):
    PV = 0.0
    EV = 0.0
    
    for task in tasks_data:
        budget = task['normal_cost']
        actual_percent = task['percent_complete'] / 100.0
        
        # Cộng EV
        EV += budget * actual_percent
        
        # Tính PV lý thuyết
        if current_time >= task['ef']:
            PV += budget  # Đáng lẽ phải xong 100%
        elif current_time > task['es']:
            # Đáng lẽ phải xong 1 phần
            theoretical_percent = (current_time - task['es']) / task['duration']
            PV += budget * theoretical_percent

    SPI = EV / PV if PV > 0 else 1.0
    CPI = EV / total_actual_cost if total_actual_cost > 0 else 1.0
    
    # Dự báo EAC (Estimate At Completion)
    total_budget = sum(t['normal_cost'] for t in tasks_data)
    EAC = total_budget / CPI if CPI > 0 else float('inf')
    
    return {
        "PV": PV,
        "EV": EV,
        "AC": total_actual_cost,
        "SPI": round(SPI, 3),
        "CPI": round(CPI, 3),
        "EAC": round(EAC, 2)
    }
```
