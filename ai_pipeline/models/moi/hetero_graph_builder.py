"""
Heterogeneous Graph Builder (4 Node Types, 4 Edge Relations)
============================================================
Thư mục: ai_pipeline/models/moi/hetero_graph_builder.py

Chức năng:
    Xây dựng đối tượng HeteroData từ dữ liệu tiêu chuẩn (CSV / JSON) của dự án.
    Hỗ trợ 4 loại nút:
        - task: Nút công việc (39-dim feature vector: 1 thời gian duration_hours + 38 chi phí chuẩn)
        - resource: Nút tài nguyên (6-dim feature vector: unit_cost, capacity, type, energy, ot_multi, max_ot_day)
        - shift: Nút ca thi công thực tế (5-dim feature vector: start_h, end_h, dur, day_of_week, is_working)
        - project: Nút dự án tổng thể (3-dim feature vector)

    Và 4 loại cạnh quan hệ:
        - ('task', 'precedes', 'task'): Quan hệ mối nối thứ tự logic
        - ('task', 'uses', 'resource'): Nhu cầu sử dụng tài nguyên của công việc
        - ('task', 'constrained_by', 'shift'): Ràng buộc khung giờ ca thi công
        - ('task', 'belongs_to', 'project'): Công việc thuộc dự án
"""

import os
import json
import torch
import pandas as pd
import numpy as np
from torch_geometric.data import HeteroData


class HeteroGraphBuilder:
    """
    Bộ dựng đồ thị 4 loại nút (HeteroData) cho hệ thống Hybrid AI Pipeline.
    """
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.project_id = os.path.basename(os.path.normpath(project_dir))
        
        self.task_id_map = {}
        self.resource_id_map = {}
        self.agenda_id_map = {}

    def build(self) -> HeteroData:
        """
        Nạp dữ liệu từ các file CSV/JSON tiêu chuẩn và dựng đối tượng HeteroData.
        """
        data = HeteroData()
        
        # 1. Nạp trực tiếp 5 File Dữ liệu Tiêu chuẩn
        tasks_df = pd.read_csv(os.path.join(self.project_dir, 'tasks.csv'))
        edges_df = pd.read_csv(os.path.join(self.project_dir, 'logic.csv'))
        res_df = pd.read_csv(os.path.join(self.project_dir, 'resources.csv'))
        task_res_df = pd.read_csv(os.path.join(self.project_dir, 'task_resources.csv'))
        info_df = pd.read_csv(os.path.join(self.project_dir, 'project_info.csv'))
        
        project_type = str(info_df['project_type'].iloc[0]) if 'project_type' in info_df.columns else 'ITLG'

        # Nạp Lịch Agenda từ agenda.json
        weekly_schedule = {}
        holidays_list = []
        agenda_json_path = os.path.join(self.project_dir, 'agenda.json')
        if os.path.exists(agenda_json_path):
            with open(agenda_json_path, 'r', encoding='utf-8') as f:
                ag_data = json.load(f)
                weekly_schedule = ag_data.get('weekly_schedule', {})
                holidays_list = ag_data.get('holidays_list', [])
                
        from ai_pipeline.models.moi.domain_normalizers import WorkingCalendarEngine, NormalizerRegistry
        self.calendar_engine = WorkingCalendarEngine(weekly_schedule=weekly_schedule, holidays_list=holidays_list)
        self.normalizer = NormalizerRegistry.get_normalizer(project_type=project_type)
        
        # --- NÚT 1: TASK NODES (39 Features) ---
        for idx, row in tasks_df.iterrows():
            t_id = str(row['task_id'])
            self.task_id_map[t_id] = idx
            
        data['task'].x = self.normalizer.encode_task_df(tasks_df)

        # --- NÚT 2: RESOURCE NODES (6 Features) ---
        res_features = []
        for idx, row in res_df.iterrows():
            r_id = str(row['ID'])
            self.resource_id_map[r_id] = idx
            
            unit_cost = float(row['unit_cost'])
            capacity = float(row['max_availability'])
            res_type = 1.0 if str(row['type']).lower() == 'human' else 0.0
            energy = float(row['energy'])
            ot_multi = float(row['overtime_multi'])
            max_ot_day = float(row.get('max_overtime_per_day', 4.0 if res_type == 1.0 else 16.0))

            res_features.append([unit_cost, capacity, res_type, energy, ot_multi, max_ot_day])
            
        data['resource'].x = torch.tensor(res_features, dtype=torch.float32)
        
        # --- NÚT 3: SHIFT NODES (Sinh Nút trực tiếp theo từng Ca thi công thực tế từ agenda.json) ---
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        shift_features = []
        shift_idx = 0
        self.shift_id_map = {}

        for d_idx, d_name in enumerate(day_names):
            day_info = weekly_schedule.get(d_name, {})
            is_working = 1.0 if day_info.get('is_working', True) else 0.0
            shifts = day_info.get('shifts', [])
            
            if is_working and shifts:
                for s in shifts:
                    start_str = str(s.get('start_time', '08:00')).strip()
                    end_str = str(s.get('end_time', '17:00')).strip()
                    
                    def parse_h(t_str, default_val):
                        try:
                            parts = t_str.split(':')
                            return float(parts[0]) + float(parts[1]) / 60.0
                        except Exception:
                            return default_val
                            
                    s_h = parse_h(start_str, 8.0)
                    e_h = parse_h(end_str, 17.0)
                    
                    if e_h < s_h:
                        # CA VẮT ĐÊM QUA MỐC 24:00: Tách thành 2 Nút Ca thuộc 2 Thứ liên tiếp!
                        # Đoạn 1: Đêm Thứ d_idx (s_h ➔ 24.0)
                        dur1 = round(24.0 - s_h, 2)
                        s_id1 = f"{d_name}_{start_str}_24:00"
                        self.shift_id_map[s_id1] = shift_idx
                        shift_idx += 1
                        shift_features.append([s_h, 24.0, dur1, float(d_idx), 1.0])
                        
                        # Đoạn 2: Rạng sáng Thứ d_idx + 1 (00:00 ➔ e_h)
                        next_d_idx = (d_idx + 1) % 7
                        next_d_name = day_names[next_d_idx]
                        dur2 = round(e_h, 2)
                        s_id2 = f"{next_d_name}_00:00_{end_str}"
                        self.shift_id_map[s_id2] = shift_idx
                        shift_idx += 1
                        shift_features.append([0.0, e_h, dur2, float(next_d_idx), 1.0])
                    else:
                        # Ca làm việc bình thường trong ngày (08:00 ➔ 17:00)
                        raw_dur = s.get('hours')
                        dur = float(raw_dur) if raw_dur is not None else round(e_h - s_h, 2)
                        
                        s_id = f"{d_name}_{start_str}_{end_str}"
                        self.shift_id_map[s_id] = shift_idx
                        shift_idx += 1
                        shift_features.append([s_h, e_h, dur, float(d_idx), 1.0])
            else:
                # Nút Ngày nghỉ không ca
                s_id = f"{d_name}_OFF"
                self.shift_id_map[s_id] = shift_idx
                shift_idx += 1
                shift_features.append([0.0, 0.0, 0.0, float(d_idx), 0.0])

        data['shift'].x = torch.tensor(shift_features, dtype=torch.float32)
        
        # Tính Tổng số giờ làm việc chuẩn trong 1 tuần tiêu chuẩn (weekly_working_hours)
        weekly_working_hours = float(sum(feat[2] for feat in shift_features if feat[4] == 1.0))
        if weekly_working_hours <= 0.0:
            weekly_working_hours = 40.0
        
        # --- NÚT 4: PROJECT NODE ---
        data['project'].x = torch.tensor([[len(tasks_df), len(res_df), 1.0]], dtype=torch.float32)
        
        # --- CẠNH 1: TASK PRECEDENCE ('task', 'precedes', 'task') ---
        src_tasks, dst_tasks, edge_attrs = [], [], []
        for _, row in edges_df.iterrows():
            p_id = str(row['predecessor_id'])
            s_id = str(row['successor_id'])
            
            if p_id in self.task_id_map and s_id in self.task_id_map:
                src_tasks.append(self.task_id_map[p_id])
                dst_tasks.append(self.task_id_map[s_id])
                
                lag_h = float(row.get('lag_hours', 0.0))
                edge_attrs.append([lag_h, 1.0, 0.0, 0.0])
                
        data['task', 'precedes', 'task'].edge_index = torch.tensor([src_tasks, dst_tasks], dtype=torch.long) if src_tasks else torch.zeros((2, 0), dtype=torch.long)
        data['task', 'precedes', 'task'].edge_attr = torch.tensor(edge_attrs, dtype=torch.float32) if edge_attrs else torch.zeros((0, 4), dtype=torch.float32)
            
        # --- CẠNH 2: TASK USES RESOURCE ('task', 'uses', 'resource') ---
        t_src, r_dst, req_qty = [], [], []
        for _, row in task_res_df.iterrows():
            t_id = str(row['task_id'])
            r_id = str(row['resource_id'])
            qty = float(row['request_quantity'])
            
            if t_id in self.task_id_map and r_id in self.resource_id_map:
                t_src.append(self.task_id_map[t_id])
                r_dst.append(self.resource_id_map[r_id])
                req_qty.append([qty])
                
        data['task', 'uses', 'resource'].edge_index = torch.tensor([t_src, r_dst], dtype=torch.long) if t_src else torch.zeros((2, 0), dtype=torch.long)
        data['task', 'uses', 'resource'].edge_attr = torch.tensor(req_qty, dtype=torch.float32) if req_qty else torch.zeros((0, 1), dtype=torch.float32)
            
        # --- CẠNH 3: TASK CONSTRAINED BY SHIFT ('task', 'constrained_by', 'shift') ---
        t_indices, shift_indices, shift_edge_attrs = [], [], []
        num_shifts = len(shift_features)
        
        # Tính toán offset ngày/tuần khởi công từ baseline_start (hỗ trợ cả datetime string và số)
        b_start_series = tasks_df.get('baseline_start', pd.Series([0.0] * len(tasks_df)))
        try:
            b_start_floats = b_start_series.astype(float).values
        except (ValueError, TypeError):
            try:
                b_dt = pd.to_datetime(b_start_series, errors='coerce')
                min_dt = b_dt.min()
                if pd.notna(min_dt):
                    b_start_floats = ((b_dt - min_dt).dt.total_seconds() / 86400.0).fillna(0.0).values
                else:
                    b_start_floats = np.zeros(len(tasks_df))
            except Exception:
                b_start_floats = np.zeros(len(tasks_df))

        # Tính toán max_project_weeks để chuẩn hóa MinMax Scaling về khoảng [0.0, 1.0]
        max_start_week = max(0.0, float(np.max(b_start_floats) / 7.0)) if len(b_start_floats) > 0 else 0.0
        tot_dur_weeks = sum(float(r.get('duration_hours', 0.0)) for _, r in tasks_df.iterrows()) / weekly_working_hours
        max_project_weeks = max(1.0, max_start_week + tot_dur_weeks)

        for t_idx, row in tasks_df.iterrows():
            dur_h = float(row.get('duration_hours', 0.0))
            b_start = float(b_start_floats[t_idx]) if t_idx < len(b_start_floats) else 0.0
            
            est_weeks_norm = round(min(1.0, max(0.0, (dur_h / weekly_working_hours) / max_project_weeks)), 4)
            start_week_norm = round(min(1.0, max(0.0, (b_start / 7.0) / max_project_weeks)), 4)
            start_day_norm = round(min(1.0, max(0.0, (b_start % 7.0) / 7.0)), 4)
            
            for s_idx in range(num_shifts):
                t_indices.append(t_idx)
                shift_indices.append(s_idx)
                shift_edge_attrs.append([est_weeks_norm, start_week_norm, start_day_norm])
                
        data['task', 'constrained_by', 'shift'].edge_index = torch.tensor([t_indices, shift_indices], dtype=torch.long) if t_indices else torch.zeros((2, 0), dtype=torch.long)
        data['task', 'constrained_by', 'shift'].edge_attr = torch.tensor(shift_edge_attrs, dtype=torch.float32) if shift_edge_attrs else torch.zeros((0, 3), dtype=torch.float32)
        
        # --- CẠNH 4: TASK BELONGS TO PROJECT ('task', 'belongs_to', 'project') ---
        proj_indices = [0] * len(tasks_df)
        data['task', 'belongs_to', 'project'].edge_index = torch.tensor([list(range(len(tasks_df))), proj_indices], dtype=torch.long) if len(tasks_df) > 0 else torch.zeros((2, 0), dtype=torch.long)
        
        return data
