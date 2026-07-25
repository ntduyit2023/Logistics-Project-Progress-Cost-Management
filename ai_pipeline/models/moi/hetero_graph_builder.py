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
        Nạp dữ liệu từ các file CSV và đẻ ra đối tượng HeteroData với 4 loại nút.
        """
        data = HeteroData()
        
        # 1. Nạp dữ liệu các file CSV
        tasks_path = os.path.join(self.project_dir, 'tasks.csv')
        edges_path = os.path.join(self.project_dir, 'predecessors.csv')
        res_path = os.path.join(self.project_dir, 'resources.csv')
        task_res_path = os.path.join(self.project_dir, 'task_resources.csv')
        project_info_path = os.path.join(self.project_dir, 'project_info.csv')
        
        tasks_df = pd.read_csv(tasks_path) if os.path.exists(tasks_path) else pd.DataFrame()
        edges_df = pd.read_csv(edges_path) if os.path.exists(edges_path) else pd.DataFrame()
        res_df = pd.read_csv(res_path) if os.path.exists(res_path) else pd.DataFrame()
        task_res_df = pd.read_csv(task_res_path) if os.path.exists(task_res_path) else pd.DataFrame()
        
        # 1.5. Nạp project_type và Agenda parameters
        project_type = 'ITLG'
        hours_per_day = 8.0
        days_per_week = 5.0
        if os.path.exists(project_info_path):
            try:
                info_df = pd.read_csv(project_info_path)
                if not info_df.empty:
                    project_type = str(info_df.get('project_type', ['ITLG'])[0])
                    hours_per_day = float(info_df.get('working_hours_per_day', [8.0])[0])
                    days_per_week = float(info_df.get('working_days_per_week', [5.0])[0])
            except Exception:
                pass
                
        from ai_pipeline.models.moi.domain_normalizers import NormalizerRegistry
        self.normalizer = NormalizerRegistry.get_normalizer(
            project_type=project_type,
            hours_per_day=hours_per_day,
            days_per_week=days_per_week
        )
        
        # --- NÚT 1: TASK NODES ---
        for idx, row in tasks_df.iterrows():
            t_id = str(row.get('id', row.get('task_id', idx)))
            self.task_id_map[t_id] = idx
            
        data['task'].x = self.normalizer.encode_task_df(tasks_df) if not tasks_df.empty else torch.zeros((0, 72), dtype=torch.float32)

        
        # --- NÚT 2: RESOURCE NODES ---
        res_features = []
        for idx, row in res_df.iterrows():
            r_id = str(row.get('id', row.get('resource_id', idx)))
            self.resource_id_map[r_id] = idx
            
            unit_cost = float(row.get('unit_cost', 0.0))
            capacity = float(row.get('capacity', 1.0))
            res_type = 1.0 if str(row.get('resource_type', '')).lower() == 'labor' else 0.0
            res_features.append([unit_cost, capacity, res_type, 0.0])
            
        data['resource'].x = torch.tensor(res_features, dtype=torch.float32) if res_features else torch.zeros((0, 4), dtype=torch.float32)
        
        # --- NÚT 3: TIME AGENDA NODES ---
        agenda_features = [
            [8.0, 5.0, 0.0],  # Standard Agenda: 8h/day, 5 days/week
            [10.0, 6.0, 0.0], # Overtime Agenda
            [0.0, 0.0, 1.0]   # Holiday / Non-working
        ]
        self.agenda_id_map = {"standard": 0, "overtime": 1, "holiday": 2}
        data['time_agenda'].x = torch.tensor(agenda_features, dtype=torch.float32)
        
        # --- NÚT 4: PROJECT NODE ---
        data['project'].x = torch.tensor([[len(tasks_df), len(res_df), 1.0]], dtype=torch.float32)
        
        # --- CẠNH 1: TASK PRECEDENCE ('task', 'precedes', 'task') ---
        src_tasks, dst_tasks, edge_attrs = [], [], []
        for _, row in edges_df.iterrows():
            p_id = str(row.get('predecessor_task_id', ''))
            s_id = str(row.get('successor_task_id', ''))
            
            if p_id in self.task_id_map and s_id in self.task_id_map:
                src_tasks.append(self.task_id_map[p_id])
                dst_tasks.append(self.task_id_map[s_id])
                
                lag_h = float(row.get('lag_hours', 0.0)) + float(row.get('lag_days', 0.0)) * 8.0
                edge_attrs.append([lag_h, 1.0, 0.0, 0.0])
                
        if src_tasks:
            data['task', 'precedes', 'task'].edge_index = torch.tensor([src_tasks, dst_tasks], dtype=torch.long)
            data['task', 'precedes', 'task'].edge_attr = torch.tensor(edge_attrs, dtype=torch.float32)
        else:
            data['task', 'precedes', 'task'].edge_index = torch.zeros((2, 0), dtype=torch.long)
            data['task', 'precedes', 'task'].edge_attr = torch.zeros((0, 4), dtype=torch.float32)
            
        # --- CẠNH 2: TASK USES RESOURCE ('task', 'uses', 'resource') ---
        t_src, r_dst, req_qty = [], [], []
        for _, row in task_res_df.iterrows():
            t_id = str(row.get('task_id', ''))
            r_id = str(row.get('resource_id', ''))
            qty = float(row.get('request_quantity', 1.0))
            
            if t_id in self.task_id_map and r_id in self.resource_id_map:
                t_src.append(self.task_id_map[t_id])
                r_dst.append(self.resource_id_map[r_id])
                req_qty.append([qty])
                
        if t_src:
            data['task', 'uses', 'resource'].edge_index = torch.tensor([t_src, r_dst], dtype=torch.long)
            data['task', 'uses', 'resource'].edge_attr = torch.tensor(req_qty, dtype=torch.float32)
        else:
            data['task', 'uses', 'resource'].edge_index = torch.zeros((2, 0), dtype=torch.long)
            
        # --- CẠNH 3: TASK CONSTRAINED BY TIME AGENDA ('task', 'constrained_by', 'time_agenda') ---
        t_indices = list(range(len(tasks_df)))
        agenda_indices = [0] * len(tasks_df)
        data['task', 'constrained_by', 'time_agenda'].edge_index = torch.tensor([t_indices, agenda_indices], dtype=torch.long)
        
        # --- CẠNH 4: TASK BELONGS TO PROJECT ('task', 'belongs_to', 'project') ---
        proj_indices = [0] * len(tasks_df)
        data['task', 'belongs_to', 'project'].edge_index = torch.tensor([t_indices, proj_indices], dtype=torch.long)
        
        return data
