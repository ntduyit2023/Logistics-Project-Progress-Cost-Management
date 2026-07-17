import os
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import torch
from torch_geometric.data import Data, Dataset

class GlPoProjectGraph:
    """
    Mô tả (Description):
        Đọc các file CSV của một dự án và xây dựng thành đối tượng Đồ thị (PyTorch Geometric Data).
        Tự động tính toán các feature mồi (In-degree, Out-degree, Float...)
        và ép khuôn 72-Dim Feature Vector (60 Cost user + 12 Feature AI).
        
    Đầu vào (Args):
        project_dir (str): Đường dẫn đến thư mục chứa các file CSV của dự án.
        
    Đầu ra / Thuộc tính (Outputs / Attributes):
        project_id (str): Mã dự án được trích xuất từ tên thư mục.
        node_to_idx (dict): Từ điển ánh xạ từ Mã Task (string) sang số thứ tự Đỉnh trong Đồ thị (int).
        idx_to_node (dict): Từ điển ánh xạ ngược từ số thứ tự Đỉnh (int) sang Mã Task (string).
        data (torch_geometric.data.Data): Đối tượng Đồ thị cuối cùng, bao gồm:
            - data.x: Tensor [Số_lượng_Task, 72] chứa các tính năng của Đỉnh.
            - data.edge_index: Tensor [2, Số_lượng_Cạnh] chứa Bản đồ liên kết logic.
            - data.edge_attr: Tensor [Số_lượng_Cạnh, 8] chứa Tính năng của Cạnh (FS, SS, FF, SF, Lags).
            - data.u: Tensor [1, 3] chứa Luật Ràng buộc Toàn cục (Giờ/ngày, Ngày/tuần, Số ngày nghỉ).
    """
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.project_id = os.path.basename(os.path.normpath(project_dir))
        
        # Bi-directional ID Dictionary
        self.node_to_idx = {}
        self.idx_to_node = {}
        
        self.data = self._process()
        
    def _process(self):
        # 1. Load CSVs
        tasks_df = pd.read_csv(os.path.join(self.project_dir, 'tasks.csv'))
        edges_df = pd.read_csv(os.path.join(self.project_dir, 'predecessors.csv'))
        try:
            task_resources_df = pd.read_csv(os.path.join(self.project_dir, 'task_resources.csv'))
        except FileNotFoundError:
            task_resources_df = pd.DataFrame(columns=['task_id', 'resource_id', 'request_quantity'])
            
        try:
            resources_df = pd.read_csv(os.path.join(self.project_dir, 'resources.csv'))
        except FileNotFoundError:
            resources_df = pd.DataFrame(columns=['ID', 'resource_name', 'resource_type', 'unit_cost', 'capacity'])
            
        try:
            agenda_df = pd.read_csv(os.path.join(self.project_dir, 'agenda_working_hours.csv'))
        except FileNotFoundError:
            agenda_df = pd.DataFrame(columns=['Time Range', 'Working'])
            
        try:
            holidays_df = pd.read_csv(os.path.join(self.project_dir, 'agenda_holidays.csv'))
        except (FileNotFoundError, pd.errors.EmptyDataError):
            holidays_df = pd.DataFrame()
            
        try:
            working_days_df = pd.read_csv(os.path.join(self.project_dir, 'agenda_working_days.csv'))
        except FileNotFoundError:
            working_days_df = pd.DataFrame(columns=['Day', 'Working'])
        
        # Fallback: nếu không có agenda CSV, thử load từ database
        _agenda_from_db = None
        if agenda_df.empty and working_days_df.empty:
            try:
                from ai_pipeline.src.utils.agenda_calculator import load_agenda_from_db
                _agenda_from_db = load_agenda_from_db(int(self.project_id))
            except Exception:
                pass
            
        # 2. Build ID Mapping
        for idx, row in tasks_df.iterrows():
            t_id = str(row.get('id', row.get('task_id', row.get('ID', ''))))
            self.node_to_idx[t_id] = idx
            self.idx_to_node[idx] = t_id
            
        # 3. Resource Cost Mapping
        res_cost_map = {}
        if not resources_df.empty:
            id_col = 'ID' if 'ID' in resources_df.columns else ('id' if 'id' in resources_df.columns else resources_df.columns[0])
            cost_col = 'unit_cost' if 'unit_cost' in resources_df.columns else ('Cost/Unit' if 'Cost/Unit' in resources_df.columns else 'cost')
            for _, row in resources_df.iterrows():
                try:
                    res_id = str(row[id_col])
                    res_cost_map[res_id] = float(row.get(cost_col, 0.0) or 0.0)
                except Exception:
                    pass

        # 3.5 Resource Aggregation
        res_agg = {}
        if not task_resources_df.empty:
            grouped = task_resources_df.groupby('task_id')
            req_col = 'request_quantity' if 'request_quantity' in task_resources_df.columns else task_resources_df.columns[-1]
            res_col = 'resource_id' if 'resource_id' in task_resources_df.columns else task_resources_df.columns[1]
            for t_id, group in grouped:
                total_demand = group[req_col].sum() if req_col in group else 0.0
                
                cost_estimate = 0.0
                if req_col in group and res_col in group:
                    for _, tr_row in group.iterrows():
                        r_id = str(tr_row[res_col])
                        qty = float(tr_row[req_col] or 0.0)
                        u_cost = res_cost_map.get(r_id, 0.0)
                        cost_estimate += qty * u_cost
                        
                res_agg[str(t_id)] = {
                    'total_demand': total_demand,
                    'cost_estimate': cost_estimate
                }
                
        # 3.5 Parse Agenda for CPM & Global Constraints
        hours_per_day = 8.0
        if not agenda_df.empty:
            yes_count = len(agenda_df[agenda_df['Working'].astype(str).str.lower() == 'yes'])
            if yes_count > 0:
                hours_per_day = float(yes_count)
        elif _agenda_from_db:
            hours_per_day = _agenda_from_db['hours_per_day']
                
        days_per_week = 5.0
        if not working_days_df.empty:
            working_days_count = len(working_days_df[working_days_df['Working'].astype(str).str.lower() == 'yes'])
            if working_days_count > 0:
                days_per_week = float(working_days_count)
        elif _agenda_from_db:
            days_per_week = _agenda_from_db['days_per_week']
                
        total_holidays = float(len(holidays_df)) if not holidays_df.empty else 0.0
        
        # 4. Compute G8 AI-Computed Features (Network Topology)
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        adj_forward = defaultdict(list)
        adj_backward = defaultdict(list)
        
        for _, row in edges_df.iterrows():
            pred_id = str(row.get('predecessor_task_id', row.get('source_id', '')))
            succ_id = str(row.get('successor_task_id', row.get('target_id', '')))
            if pred_id in self.node_to_idx and succ_id in self.node_to_idx:
                u = self.node_to_idx[pred_id]
                v = self.node_to_idx[succ_id]
                out_degree[u] += 1
                in_degree[v] += 1
                adj_forward[u].append(v)
                adj_backward[v].append(u)
                
        # Simple Critical Path Method (CPM) for Float and Criticality
        num_nodes = len(tasks_df)
        durations = np.zeros(num_nodes)
        for idx, row in tasks_df.iterrows():
            d_m = float(row.get('duration_months', 0))
            d_w = float(row.get('duration_weeks', 0))
            d_d = float(row.get('duration_days', 0))
            d_h = float(row.get('duration_hours', 0))
            cal_type = str(row.get('calendar_type', 'Agenda')).lower()
            
            if '24/7' in cal_type:
                total_h = d_m * 30 * 24 + d_w * 7 * 24 + d_d * 24 + d_h
            else:
                # 1 month ~ 4 weeks. Use agenda-based multipliers.
                total_h = d_m * (4 * days_per_week * hours_per_day) + d_w * (days_per_week * hours_per_day) + d_d * hours_per_day + d_h
                
            durations[idx] = total_h  # Uniform unit: hours
            
        # Topological Sort
        in_deg_temp = in_degree.copy()
        topo_order = []
        queue = deque([i for i in range(num_nodes) if in_deg_temp[i] == 0])
        while queue:
            u = queue.popleft()
            topo_order.append(u)
            for v in adj_forward[u]:
                in_deg_temp[v] -= 1
                if in_deg_temp[v] == 0:
                    queue.append(v)
                    
        # Forward Pass (Early Start/Finish)
        ES = np.zeros(num_nodes)
        EF = np.zeros(num_nodes)
        for u in topo_order:
            EF[u] = ES[u] + durations[u]
            for v in adj_forward[u]:
                ES[v] = max(ES[v], EF[u])
                
        # Backward Pass (Late Start/Finish)
        LS = np.zeros(num_nodes)
        LF = np.zeros(num_nodes)
        project_duration = max(EF) if len(EF) > 0 else 0
        LF.fill(project_duration)
        for u in reversed(topo_order):
            LS[u] = LF[u] - durations[u]
            for p in adj_backward[u]:
                LF[p] = min(LF[p], LS[u])
                
        total_float = LS - ES
        is_critical = (total_float == 0).astype(float)
        
        # Path Length (BFS from Source)
        path_length = np.zeros(num_nodes)
        for u in topo_order:
            for v in adj_forward[u]:
                path_length[v] = max(path_length[v], path_length[u] + 1)
        
        # 5. Node Feature Engineering (72 Dimensions)
        node_features = []
        for idx, row in tasks_df.iterrows():
            t_id = str(row.get('id', row.get('task_id', row.get('ID', ''))))
            
            # Initialize 36-dim feature vector explicitly
            x_row = [0.0] * 36
            
            # === Hub Time (0-4) ===
            x_row[0] = float(row.get('duration_months', 0))
            x_row[1] = float(row.get('duration_weeks', 0))
            x_row[2] = float(row.get('duration_days', 0))
            x_row[3] = float(row.get('duration_hours', 0))
            cal_type = str(row.get('calendar_type', 'Agenda'))
            x_row[4] = 1.0 if '24/7' in cal_type else 0.0
            
            # === G1: Direct Costs (5-10) ===
            x_row[5] = float(row.get('internal_labor_cost', 0))
            x_row[6] = float(row.get('overtime_cost', 0))
            x_row[7] = float(row.get('equipment_fuel_cost', 0))
            x_row[8] = float(row.get('qa_qc_cost', 0))
            x_row[9] = float(row.get('material_cost', 0))
            x_row[10] = float(row.get('outsourcing_cost', 0))
            
            # === G2: Indirect Costs (11-14) ===
            x_row[11] = float(row.get('training_cost', 0))
            x_row[12] = float(row.get('facility_rent', 0))
            x_row[13] = float(row.get('communication_cost', 0))
            x_row[14] = float(row.get('utilities_cost', 0))
            
            # === G3: Contractual (15-17) ===
            x_row[15] = float(row.get('insurance_cost', 0))
            x_row[16] = float(row.get('licensing_cost', 0))
            x_row[17] = float(row.get('warranty_cost', 0))
            
            # === G4: Risk (18-21) ===
            x_row[18] = float(row.get('complexity', 0))
            x_row[19] = float(row.get('weather_contingency', 0))
            x_row[20] = float(row.get('general_contingency', 0))
            x_row[21] = float(row.get('rework_risk', 0))
            
            # === G5: Logistics (22-26) ===
            x_row[22] = float(row.get('holding_cost', 0))
            x_row[23] = float(row.get('international_freight', 0))
            x_row[24] = float(row.get('handling_cost', 0))
            x_row[25] = float(row.get('reverse_logistics', 0))
            x_row[26] = float(row.get('defect_cost', 0))
            
            # === G6: Time (27-28) ===
            x_row[27] = float(row.get('overtime_hours', 0))
            x_row[28] = float(row.get('lag_time', 0))
            
            # === G7: AI Topology (29-33) ===
            x_row[29] = float(in_degree[idx])
            x_row[30] = float(out_degree[idx])
            x_row[31] = float(is_critical[idx])
            x_row[32] = float(total_float[idx])
            x_row[33] = float(path_length[idx])
            
            # === G8: Resources & Demands (34-35) ===
            t_res_info = res_agg.get(t_id, {'total_demand': 0.0, 'cost_estimate': 0.0})
            x_row[34] = float(t_res_info.get('total_demand', 0.0))
            x_row[35] = float(t_res_info.get('cost_estimate', 0.0))
            
            node_features.append(x_row)
            
        # 5.5 Optimal Feature Group Normalization Layer (36-D Matrix)
        node_features_mat = np.array(node_features, dtype=np.float32)
        node_features_mat = np.nan_to_num(node_features_mat, nan=0.0, posinf=0.0, neginf=0.0)
        
        # 1. Log Transform for Costs (G1, G2, G3, G4, G5 + G8 Cost: 5-26, 35) -> Maps [0, 5e8] to [0, 20.03]
        cost_indices = list(range(5, 27)) + [35]
        node_features_mat[:, cost_indices] = np.log1p(np.maximum(0.0, node_features_mat[:, cost_indices]))

        # 2. Log Scaling for Durations (Hub 0-3, G6 27-28, G7 topology 32) -> Maps [0, 1500h] to [0, 7.31]
        dur_indices = [0, 1, 2, 3, 27, 28, 32]
        node_features_mat[:, dur_indices] = np.log1p(np.maximum(0.0, node_features_mat[:, dur_indices]))

        # 3. Min-Max Graph Scaling for Topology & Resource Demands (G7: 29-30, 32-33 + G8 Demand: 34) -> Maps to [0, 1]
        topo_res_indices = [29, 30, 32, 33, 34]
        for c in topo_res_indices:
            max_v = float(np.max(np.abs(node_features_mat[:, c])))
            if max_v > 1e-6:
                node_features_mat[:, c] /= max_v
                
        x = torch.tensor(node_features_mat, dtype=torch.float)
        
        # 6. Edge Topology & Features (8 Dims)
        source_nodes = []
        target_nodes = []
        edge_features = []
        
        for _, row in edges_df.iterrows():
            pred_id = str(row.get('predecessor_task_id', row.get('source_id', '')))
            succ_id = str(row.get('successor_task_id', row.get('target_id', '')))
            
            if pred_id in self.node_to_idx and succ_id in self.node_to_idx:
                source_idx = self.node_to_idx[pred_id]
                target_idx = self.node_to_idx[succ_id]
                
                source_nodes.append(source_idx)
                target_nodes.append(target_idx)
                
                dep = str(row.get('dependency_type', 'FS')).upper()
                is_fs = 1.0 if dep == 'FS' else 0.0
                is_ss = 1.0 if dep == 'SS' else 0.0
                is_ff = 1.0 if dep == 'FF' else 0.0
                is_sf = 1.0 if dep == 'SF' else 0.0
                
                l_m = float(row.get('lag_months', 0))
                l_w = float(row.get('lag_weeks', 0))
                l_d = float(row.get('lag_days', 0))
                l_h = float(row.get('lag_hours', 0))
                
                edge_features.append([is_fs, is_ss, is_ff, is_sf, l_m, l_w, l_d, l_h])
                
        if len(source_nodes) > 0:
            edge_index = torch.tensor([source_nodes, target_nodes], dtype=torch.long)
            edge_attr = torch.tensor(edge_features, dtype=torch.float)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_attr = torch.empty((0, 8), dtype=torch.float)
            
        # 7. Global Constraints (Graph-level attributes 'U')
        # (Parsed earlier at step 3.5)
                
        u = torch.tensor([[hours_per_day, days_per_week, total_holidays]], dtype=torch.float)
        
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, u=u)
        return data

class GlPoDataset(Dataset):
    """
    Mô tả (Description):
        Bộ Dataset của PyTorch Geometric, làm nhiệm vụ quét toàn bộ thư mục gốc,
        nhặt tất cả các dự án đã xử lý (processed) và đóng gói thành một danh sách Đồ thị.
        
    Đầu vào (Args):
        processed_dir (str): Đường dẫn tuyệt đối đến thư mục gốc chứa nhiều dự án.
        
    Đầu ra / Thuộc tính (Outputs / Attributes):
        project_dirs (list): Danh sách các đường dẫn dự án hợp lệ tìm thấy.
        graphs (list): Danh sách các đối tượng GlPoProjectGraph đã được khởi tạo.
        
    Phương thức (Methods):
        len(): Trả về tổng số lượng Đồ thị dự án có trong bộ Dataset.
        get(idx): Trả về đối tượng Đồ thị (data) của dự án tại vị trí idx.
    """
    def __init__(self, base_dir):
        super().__init__(root=None, transform=None, pre_transform=None)
        self.base_dir = base_dir
        
        self.project_dirs = []
        for item in os.listdir(base_dir):
            path = os.path.join(base_dir, item)
            if os.path.isdir(path) and os.path.exists(os.path.join(path, 'tasks.csv')):
                self.project_dirs.append(path)
                
        self.graphs = []
        self._process_all()
        
    def _process_all(self):
        for pdir in self.project_dirs:
            pg = GlPoProjectGraph(pdir)
            self.graphs.append(pg)
            print(f"[DataLoader] Built Graph for {pg.project_id}: {pg.data.num_nodes} Nodes, {pg.data.num_edges} Edges")
            
    def len(self):
        return len(self.graphs)
        
    def get(self, idx):
        return self.graphs[idx].data

if __name__ == "__main__":
    # Test DataLoader
    processed_dir = r"E:\University\Year 3-3\DA3\ai_pipeline\data\processed"
    print(f"Loading datasets from {processed_dir}...\n")
    
    dataset = GlPoDataset(processed_dir)
    
    if len(dataset) > 0:
        first_graph = dataset.graphs[0]
        data = first_graph.data
        print("\n--- Example PyG Tensor Shapes ---")
        print(f"Project ID: {first_graph.project_id}")
        print(f"Node Features (X) shape: {data.x.shape} -> (Nodes, 72 Dims)")
        print(f"Edge Index shape: {data.edge_index.shape} -> (2, Edges)")
        print(f"Edge Attr (E) shape: {data.edge_attr.shape} -> (Edges, 8 Dims)")
        print(f"Global Constraints (U) shape: {data.u.shape} -> (1, 3 Dims) [Hours/Day, Days/Week, Holidays]")
        
        print("\n--- Feature G8 Check for First Node ---")
        print(f"Node 0: In-degree={data.x[0, 63]}, Out-degree={data.x[0, 64]}, Is_Critical={data.x[0, 65]}, Total_Float={data.x[0, 66]}, Path_Length={data.x[0, 67]}")


class ProjectEnvironmentWrapper:
    """
    Mô tả (Description):
        Một lớp tích hợp API cấp cao (Wrapper) viết riêng cho đồng nghiệp làm RL (PPO).
        Chỉ cần truyền ID Dự án, nó sẽ tự động nạp toàn bộ Dữ liệu Đồ thị (Graph),
        Sức chứa Tài nguyên (Capacity), và Luật Lịch trình (Agenda).
        
    Đầu vào (Args):
        processed_dir (str): Đường dẫn gốc chứa tất cả các thư mục dự án.
        project_id (str): Mã dự án cần load (Ví dụ: 'C2012-08').
        
    Đầu ra / Thuộc tính (Outputs / Attributes):
        project_id (str): Mã dự án đã load.
        project_dir (str): Đường dẫn cụ thể của dự án đó.
        graph (GlPoProjectGraph): Đối tượng khởi tạo đồ thị.
        data (torch_geometric.data.Data): Đồ thị PyTorch Geometric đã sẵn sàng nạp vào Mạng Nơ-ron.
        global_resources (dict): Từ điển chứa các Ràng buộc Tài nguyên toàn cục.
            Cấu trúc: {'Mã_Tài_Nguyên': {'name': str, 'type': str, 'capacity': float, 'cost_use': float, 'cost_unit': float}}
        agenda (dict): Từ điển chứa các Luật Lịch trình toàn cục.
            Cấu trúc: {'hours_per_day': float, 'days_per_week': float, 'total_holidays': float}
    """
    def __init__(self, processed_dir: str, project_id: str):
        self.project_id = project_id
        self.project_dir = os.path.join(processed_dir, project_id)
        
        if not os.path.exists(self.project_dir):
            raise FileNotFoundError(f"Project directory not found: {self.project_dir}")
            
        # 1. Load the Neural Network Graph Data
        self.graph = GlPoProjectGraph(self.project_dir)
        self.data = self.graph.data
        
        # 2. Load Global Resources (Supply / Capacity)
        self.global_resources = {}
        res_file = os.path.join(self.project_dir, 'resources.csv')
        if os.path.exists(res_file):
            res_df = pd.read_csv(res_file)
            for _, row in res_df.iterrows():
                r_id = str(row['ID'])
                self.global_resources[r_id] = {
                    'name': str(row.get('Name', '')),
                    'type': str(row.get('Type', '')),
                    'capacity': float(row.get('Availability', 1.0)),
                    'cost_use': float(row.get('Cost/Use', 0.0)),
                    'cost_unit': float(row.get('Cost/Unit', 0.0))
                }
                
        # 3. Expose Agenda Variables cleanly
        self.agenda = {
            'hours_per_day': float(self.data.u[0, 0]),
            'days_per_week': float(self.data.u[0, 1]),
            'total_holidays': float(self.data.u[0, 2])
        }
        
    def summary(self):
        print(f"=== Project Environment: {self.project_id} ===")
        print(f"- Graph Nodes: {self.data.num_nodes}")
        print(f"- Graph Edges: {self.data.num_edges}")
        print(f"- Global Resources Loaded: {len(self.global_resources)} types")
        print(f"- Agenda: {self.agenda['hours_per_day']}h/day, {self.agenda['days_per_week']}days/week, {self.agenda['total_holidays']} holidays")
