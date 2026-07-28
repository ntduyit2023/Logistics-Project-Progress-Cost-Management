"""
Heterogeneous Graph Builder (4 Node Types)
===========================================
Thư mục: ai_pipeline/models/moi/hetero_graph_builder.py

Chức năng:
    Xây dựng đối tượng HeteroData từ dữ liệu CSV / DB của dự án.
    Hỗ trợ 4 loại nút:
        - task: Nút công việc (72-dim feature vector)
        - resource: Nút tài nguyên (Capacity, Unit Cost, Type)
        - time_agenda: Nút thời gian/lịch làm việc (Mốc tiến độ, ngày lễ, khung giờ)
        - project: Nút dự án (Baseline Start, Deadline, Budget)

    Và các loại cạnh:
        - ('task', 'precedes', 'task'): Quan hệ thứ tự (FS, SS, FF, SF + Lags)
        - ('task', 'uses', 'resource'): Nhu cầu tài nguyên
        - ('task', 'constrained_by', 'time_agenda'): Ràng buộc thời gian (MSO, MFO, SNET, FNLT)
        - ('task', 'belongs_to', 'project'): Thuộc dự án
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
                
        from ai_pipeline.models.moi.domain_normalizers import NormalizerRegistry
        self.normalizer = NormalizerRegistry.get_normalizer(project_type=project_type)
        
        # --- NÚT 1: TASK NODES (42 Features) ---
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
        
        # --- NÚT 3: TIME AGENDA NODES (Động 100% từ Lịch Agenda: 7 ngày ca + Ngày lễ + Chỉ số động) ---
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        sched_vec = []
        for d in day_names:
            day_info = weekly_schedule.get(d, {})
            shifts = day_info.get('shifts', [])
            day_h = sum(float(s.get('hours', 0.0)) for s in shifts) if day_info.get('is_working', True) else 0.0
            sched_vec.append(day_h)
        
        num_holidays = float(len(holidays_list))
        active_days_count = float(sum(1 for h in sched_vec if h > 0.0))
        avg_hours = round(sum(sched_vec) / max(1.0, active_days_count), 2) if active_days_count > 0 else 0.0
        
        agenda_features = [sched_vec + [num_holidays, avg_hours, active_days_count]]
        self.agenda_id_map = {"project_agenda": 0}
        data['time_agenda'].x = torch.tensor(agenda_features, dtype=torch.float32)
        
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
            
        # --- CẠNH 3: TASK CONSTRAINED BY TIME AGENDA ('task', 'constrained_by', 'time_agenda') ---
        t_indices = list(range(len(tasks_df)))
        agenda_indices = [0] * len(tasks_df)
        data['task', 'constrained_by', 'time_agenda'].edge_index = torch.tensor([t_indices, agenda_indices], dtype=torch.long)
        
        # --- CẠNH 4: TASK BELONGS TO PROJECT ('task', 'belongs_to', 'project') ---
        proj_indices = [0] * len(tasks_df)
        data['task', 'belongs_to', 'project'].edge_index = torch.tensor([t_indices, proj_indices], dtype=torch.long)
        
        return data
