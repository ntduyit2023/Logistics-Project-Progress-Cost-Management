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
            
        # 2. Build ID Mapping
        for idx, row in tasks_df.iterrows():
            t_id = str(row['id'])
            self.node_to_idx[t_id] = idx
            self.idx_to_node[idx] = t_id
            
        # 3. Resource Aggregation
        res_agg = {}
        if not task_resources_df.empty:
            grouped = task_resources_df.groupby('task_id')
            for t_id, group in grouped:
                res_agg[str(t_id)] = {
                    'total_demand': group['request_quantity'].sum(),
                    'unique_res': group['resource_id'].nunique()
                }
                
        # 3.5 Parse Agenda for CPM & Global Constraints
        hours_per_day = 8.0
        if not agenda_df.empty:
            yes_count = len(agenda_df[agenda_df['Working'].astype(str).str.lower() == 'yes'])
            if yes_count > 0:
                hours_per_day = float(yes_count)
                
        days_per_week = 5.0
        if not working_days_df.empty:
            working_days_count = len(working_days_df[working_days_df['Working'].astype(str).str.lower() == 'yes'])
            if working_days_count > 0:
                days_per_week = float(working_days_count)
                
        total_holidays = float(len(holidays_df)) if not holidays_df.empty else 0.0
        
        # 4. Compute G8 AI-Computed Features (Network Topology)
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        adj_forward = defaultdict(list)
        adj_backward = defaultdict(list)
        
        for _, row in edges_df.iterrows():
            pred_id = str(row['predecessor_task_id'])
            succ_id = str(row['successor_task_id'])
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
            t_id = str(row['id'])
            
            # Initialize 72-dim feature vector explicitly to avoid magic numbers
            x_row = [0.0] * 72
            
            # === Hub (0-6) ===
            x_row[0] = 0.0  # baseline_start_relative (Missing)
            x_row[1] = float(row.get('duration_months', 0))
            x_row[2] = float(row.get('duration_weeks', 0))
            x_row[3] = float(row.get('duration_days', 0))
            x_row[4] = float(row.get('duration_hours', 0))
            cal_type = str(row.get('calendar_type', 'Agenda'))
            x_row[5] = 1.0 if 'Agenda' in cal_type else 0.0
            x_row[6] = 1.0 if '24/7' in cal_type else 0.0
            
            # === G1: Direct Costs (7-14) ===
            x_row[7] = float(row.get('internal_labor_cost', 0))
            x_row[8] = float(row.get('subcontracting_cost', 0))
            x_row[9] = float(row.get('overtime_crashing_cost', 0))
            x_row[10] = float(row.get('material_cost', 0))
            x_row[11] = float(row.get('equipment_cost', 0))
            x_row[12] = float(row.get('direct_transportation', 0))
            x_row[13] = float(row.get('energy_fuel_cost', 0))
            x_row[14] = float(row.get('testing_and_inspection', 0))
            
            # === G2: Indirect Costs (15-20) ===
            x_row[15] = float(row.get('pm_overhead', 0))
            x_row[16] = float(row.get('facility_rent', 0))
            x_row[17] = float(row.get('utilities', 0))
            x_row[18] = float(row.get('communication_cost', 0))
            x_row[19] = float(row.get('internal_training', 0))
            x_row[20] = float(row.get('quality_mgmt_overhead', 0))
            
            # === G4: Contractual (21-24) ===
            x_row[21] = float(row.get('permits_and_licensing', 0))
            x_row[22] = float(row.get('project_insurance', 0))
            x_row[23] = float(row.get('warranty_and_after_sales', 0))
            x_row[24] = float(row.get('regulatory_compliance', 0))
            
            # === G5: Logistics (25-31) ===
            x_row[25] = float(row.get('inventory_holding_cost', 0))
            x_row[26] = float(row.get('ordering_cost', 0))
            x_row[27] = float(row.get('shortage_stockout', 0))
            x_row[28] = float(row.get('obsolescence_cost', 0))
            x_row[29] = float(row.get('international_freight', 0))
            x_row[30] = float(row.get('packaging_and_handling', 0))
            x_row[31] = float(row.get('reverse_logistics', 0))
            
            # === G6: Temporal (32-36) ===
            x_row[32] = float(row.get('wait_queue_time', 0))
            x_row[33] = float(row.get('setup_transition_time', 0))
            x_row[34] = float(row.get('induction_time', 0))
            x_row[35] = float(row.get('lead_time', 0))
            x_row[36] = float(row.get('pert_3_point_estimate', 0))
            
            # === G7: Resources (37-41) ===
            r_stats = res_agg.get(t_id, {'total_demand': 0.0, 'unique_res': 0.0})
            x_row[37] = float(r_stats['total_demand']) # request_quantity
            x_row[38] = float(row.get('allocated_quantity', 0))
            x_row[39] = float(row.get('labor_productivity', 0))
            x_row[40] = float(row.get('equipment_utilization', 0))
            x_row[41] = float(row.get('resource_substitutability', 0))
            
            # === G9: Risks (42-48) ===
            x_row[42] = float(row.get('technical_complexity', 0))
            x_row[43] = float(row.get('rework_probability', 0))
            x_row[44] = float(row.get('external_dependency_level', 0))
            x_row[45] = float(row.get('contingency_reserve', 0))
            x_row[46] = float(row.get('management_reserve', 0))
            x_row[47] = float(row.get('weather_seasonal_risk', 0))
            x_row[48] = float(row.get('technology_risk', 0))
            
            # === G11 & G12: Org & ESG (49-59) ===
            x_row[49] = float(row.get('required_skill_level', 0))
            x_row[50] = float(row.get('staff_experience', 0))
            x_row[51] = float(row.get('learning_curve_effect', 0))
            x_row[52] = float(row.get('hr_stability_risk', 0))
            x_row[53] = float(row.get('cross_functional_coordination', 0))
            x_row[54] = float(row.get('occupational_safety_risk', 0))
            x_row[55] = float(row.get('environmental_impact', 0))
            x_row[56] = float(row.get('waste_disposal_cost', 0))
            x_row[57] = float(row.get('community_social_impact', 0))
            x_row[58] = float(row.get('carbon_tax_credit', 0))
            x_row[59] = float(row.get('esg_compliance', 0))
            
            # === AI-Computed: G3, G8, G10 ===
            # G3: Opportunity Cost (60-62) initialized to 0.0, updated dynamically during simulation
            x_row[60] = 0.0  # schedule_flexibility
            x_row[61] = 0.0  # resource_alternative_cost
            x_row[62] = 0.0  # delay_impact_cost
            
            # G8: Network Topology (63-67) computed statically by Data Loader
            x_row[63] = float(in_degree[idx])
            x_row[64] = float(out_degree[idx])
            x_row[65] = float(is_critical[idx])
            x_row[66] = float(total_float[idx])
            x_row[67] = float(path_length[idx])
            
            # G10: Earned Value (68-71) initialized to 0.0, updated dynamically during execution
            x_row[68] = 0.0  # planned_value
            x_row[69] = 0.0  # earned_value
            x_row[70] = 0.0  # cpi
            x_row[71] = 0.0  # spi
            
            node_features.append(x_row)
            
        x = torch.tensor(node_features, dtype=torch.float)
        
        # 6. Edge Topology & Features (8 Dims)
        source_nodes = []
        target_nodes = []
        edge_features = []
        
        for _, row in edges_df.iterrows():
            pred_id = str(row['predecessor_task_id'])
            succ_id = str(row['successor_task_id'])
            
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
