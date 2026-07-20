"""
Mô-đun Data Validator: Kiểm tra tính hợp lệ dữ liệu đầu vào
================================================================
Dự án: GLPO - Graph Logistics Project Optimization

Mô tả:
    Kiểm tra và sanitize dữ liệu CSV trước khi xây dựng đồ thị PyG.
    Phát hiện và tự động sửa các lỗi cấu trúc (chu trình, nút mồ côi,
    self-loop, cạnh trùng lặp, giá trị NaN/Inf, v.v.)

Luồng dữ liệu:
    CSV files → ProjectDataValidator.validate() → ValidationReport
    → Sanitized DataFrames → GlPoProjectGraph / run_main.py
"""

import os
import pandas as pd
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple


@dataclass
class ValidationReport:
    """Kết quả kiểm tra tính hợp lệ dữ liệu."""
    is_valid: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    sanitized_tasks_df: Optional[pd.DataFrame] = None
    sanitized_edges_df: Optional[pd.DataFrame] = None
    stats: dict = field(default_factory=dict)
    
    def add_warning(self, msg: str):
        self.warnings.append(msg)
        
    def add_error(self, msg: str):
        self.errors.append(msg)
        self.is_valid = False


class ProjectDataValidator:
    """
    Bộ kiểm tra tính hợp lệ dữ liệu dự án trước khi xây dựng đồ thị.
    
    Các kiểm tra:
        1. Missing Required Columns (task_id, task_name)
        2. Self-Loop Detection (predecessor_id == successor_id)
        3. Duplicate Edge Detection
        4. Orphan Node Detection (task in edges nhưng không có trong tasks)
        5. Cycle Detection (+ tự động gỡ)
        6. Zero/Negative Duration (trừ milestone)
        7. NaN/Inf Sanitization
        8. Resource Reference Integrity
    """
    
    # Các cột bắt buộc trong tasks.csv
    REQUIRED_TASK_COLUMNS = ['task_id', 'task_name']
    
    # Các cột bắt buộc trong predecessors.csv
    REQUIRED_EDGE_COLUMNS = ['predecessor_task_id', 'successor_task_id']
    
    # Các cột số cần sanitize NaN/Inf
    NUMERIC_COLUMNS_PATTERNS = [
        'g1_', 'g2_', 'g4_', 'g5_', 'g6_', 'g7_',
        'internal_labor', 'overtime', 'equipment', 'qa_qc',
        'material', 'outsourcing', 'training', 'facility',
        'communication', 'utilities', 'insurance', 'licensing',
        'warranty', 'complexity', 'weather', 'contingency',
        'rework', 'holding', 'international', 'handling',
        'reverse', 'defect', 'duration', 'cost'
    ]
    
    def validate(self, project_dir: str) -> ValidationReport:
        """
        Thực hiện toàn bộ kiểm tra trên dữ liệu của một dự án.
        
        Args:
            project_dir: Đường dẫn đến thư mục chứa các CSV đã xử lý.
            
        Returns:
            ValidationReport chứa kết quả kiểm tra và DataFrame đã sanitize.
        """
        report = ValidationReport()
        project_id = os.path.basename(os.path.normpath(project_dir))
        report.stats['project_id'] = project_id
        
        # --- Load files ---
        tasks_path = os.path.join(project_dir, 'tasks.csv')
        edges_path = os.path.join(project_dir, 'predecessors.csv')
        
        if not os.path.exists(tasks_path):
            report.add_error(f"[{project_id}] Thiếu file tasks.csv")
            return report
        if not os.path.exists(edges_path):
            report.add_error(f"[{project_id}] Thiếu file predecessors.csv")
            return report
            
        tasks_df = pd.read_csv(tasks_path)
        edges_df = pd.read_csv(edges_path)
        
        # Load optional files
        task_resources_df = None
        resources_df = None
        tr_path = os.path.join(project_dir, 'task_resources.csv')
        r_path = os.path.join(project_dir, 'resources.csv')
        if os.path.exists(tr_path):
            task_resources_df = pd.read_csv(tr_path)
        if os.path.exists(r_path):
            resources_df = pd.read_csv(r_path)
        
        # --- Run checks ---
        self._check_required_columns(tasks_df, edges_df, report, project_id)
        if not report.is_valid:
            return report
            
        # Build task ID set for reference
        task_ids = set(tasks_df['task_id'].astype(str).tolist())
        report.stats['num_tasks'] = len(task_ids)
        report.stats['num_edges_original'] = len(edges_df)
        
        edges_df = self._check_self_loops(edges_df, report, project_id)
        edges_df = self._check_duplicate_edges(edges_df, report, project_id)
        edges_df = self._check_orphan_nodes(edges_df, task_ids, report, project_id)
        edges_df = self._check_cycles(edges_df, task_ids, report, project_id)
        tasks_df = self._check_durations(tasks_df, report, project_id)
        tasks_df = self._sanitize_nan_inf(tasks_df, report, project_id)
        
        if task_resources_df is not None and resources_df is not None:
            self._check_resource_integrity(
                task_resources_df, resources_df, task_ids, report, project_id
            )
        
        report.stats['num_edges_sanitized'] = len(edges_df)
        report.sanitized_tasks_df = tasks_df
        report.sanitized_edges_df = edges_df
        
        return report
    
    def _check_required_columns(
        self, tasks_df: pd.DataFrame, edges_df: pd.DataFrame,
        report: ValidationReport, project_id: str
    ):
        """Kiểm tra các cột bắt buộc có tồn tại không."""
        for col in self.REQUIRED_TASK_COLUMNS:
            # Hỗ trợ tên cột thay thế: 'id' hoặc 'ID' thay cho 'task_id'
            if col == 'task_id' and col not in tasks_df.columns:
                alt_cols = ['id', 'ID', 'TaskID']
                found = any(c in tasks_df.columns for c in alt_cols)
                if not found:
                    report.add_error(
                        f"[{project_id}] tasks.csv thiếu cột bắt buộc: '{col}' "
                        f"(hoặc alternatives: {alt_cols})"
                    )
            elif col == 'task_name' and col not in tasks_df.columns:
                alt_cols = ['name', 'task_name', 'TaskName']
                found = any(c in tasks_df.columns for c in alt_cols)
                if not found:
                    report.add_warning(
                        f"[{project_id}] tasks.csv thiếu cột '{col}' — task names sẽ trống"
                    )
                    
        for col in self.REQUIRED_EDGE_COLUMNS:
            if col not in edges_df.columns:
                report.add_error(
                    f"[{project_id}] predecessors.csv thiếu cột bắt buộc: '{col}'"
                )
    
    def _check_self_loops(
        self, edges_df: pd.DataFrame, report: ValidationReport, project_id: str
    ) -> pd.DataFrame:
        """Phát hiện và xóa self-loops (predecessor_id == successor_id)."""
        pred_col = 'predecessor_task_id'
        succ_col = 'successor_task_id'
        
        self_loops = edges_df[
            edges_df[pred_col].astype(str) == edges_df[succ_col].astype(str)
        ]
        
        if len(self_loops) > 0:
            report.add_warning(
                f"[{project_id}] Phát hiện {len(self_loops)} self-loop(s), đã tự động xóa: "
                f"{list(self_loops[pred_col].values)}"
            )
            edges_df = edges_df[
                edges_df[pred_col].astype(str) != edges_df[succ_col].astype(str)
            ].reset_index(drop=True)
            
        return edges_df
    
    def _check_duplicate_edges(
        self, edges_df: pd.DataFrame, report: ValidationReport, project_id: str
    ) -> pd.DataFrame:
        """Phát hiện và xóa cạnh trùng lặp (giữ bản đầu tiên)."""
        pred_col = 'predecessor_task_id'
        succ_col = 'successor_task_id'
        
        # Tạo key (pred, succ) để phát hiện duplicate
        edges_df['_edge_key'] = (
            edges_df[pred_col].astype(str) + '_' + edges_df[succ_col].astype(str)
        )
        duplicates = edges_df[edges_df.duplicated(subset='_edge_key', keep='first')]
        
        if len(duplicates) > 0:
            report.add_warning(
                f"[{project_id}] Phát hiện {len(duplicates)} cạnh trùng lặp, "
                f"đã giữ bản đầu tiên"
            )
            edges_df = edges_df.drop_duplicates(
                subset='_edge_key', keep='first'
            ).reset_index(drop=True)
            
        edges_df = edges_df.drop(columns=['_edge_key'])
        return edges_df
    
    def _check_orphan_nodes(
        self, edges_df: pd.DataFrame, task_ids: Set[str],
        report: ValidationReport, project_id: str
    ) -> pd.DataFrame:
        """Phát hiện cạnh tham chiếu task không tồn tại và xóa chúng."""
        pred_col = 'predecessor_task_id'
        succ_col = 'successor_task_id'
        
        orphan_preds = set(edges_df[pred_col].astype(str)) - task_ids
        orphan_succs = set(edges_df[succ_col].astype(str)) - task_ids
        orphans = orphan_preds | orphan_succs
        
        # Loại bỏ 'nan' khỏi danh sách orphan
        orphans.discard('nan')
        orphans.discard('')
        
        if orphans:
            report.add_warning(
                f"[{project_id}] Phát hiện {len(orphans)} nút mồ côi trong predecessors.csv "
                f"(không có trong tasks.csv): {sorted(orphans)[:10]}... — đã xóa các cạnh liên quan"
            )
            mask = (
                edges_df[pred_col].astype(str).isin(task_ids) &
                edges_df[succ_col].astype(str).isin(task_ids)
            )
            edges_df = edges_df[mask].reset_index(drop=True)
            
        return edges_df
    
    def _check_cycles(
        self, edges_df: pd.DataFrame, task_ids: Set[str],
        report: ValidationReport, project_id: str
    ) -> pd.DataFrame:
        """Phát hiện và tự động gỡ chu trình bằng Kahn's algorithm."""
        pred_col = 'predecessor_task_id'
        succ_col = 'successor_task_id'
        
        # Build adjacency
        adj = defaultdict(list)
        in_degree = defaultdict(int)
        all_nodes = set()
        
        for _, row in edges_df.iterrows():
            u = str(row[pred_col])
            v = str(row[succ_col])
            if u in task_ids and v in task_ids:
                adj[u].append(v)
                in_degree[v] += 1
                all_nodes.add(u)
                all_nodes.add(v)
        
        # Initialize in_degree for nodes with no predecessors
        for node in all_nodes:
            if node not in in_degree:
                in_degree[node] = 0
        
        # Kahn's algorithm to detect if all nodes can be sorted
        queue = deque([n for n in all_nodes if in_degree[n] == 0])
        sorted_count = 0
        
        while queue:
            u = queue.popleft()
            sorted_count += 1
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        if sorted_count < len(all_nodes):
            # Có chu trình → tìm và gỡ
            cycle_nodes = {n for n in all_nodes if in_degree[n] > 0}
            report.add_warning(
                f"[{project_id}] Phát hiện chu trình liên quan đến {len(cycle_nodes)} nút: "
                f"{sorted(cycle_nodes)[:10]}... — đang tự động gỡ"
            )
            
            # Greedy cycle breaking: xóa cạnh có đích thuộc cycle_nodes
            # cho đến khi DAG
            edges_removed = 0
            max_iter = len(edges_df)
            
            while sorted_count < len(all_nodes) and edges_removed < max_iter:
                # Tìm một cạnh trong chu trình và xóa
                for idx, row in edges_df.iterrows():
                    v = str(row[succ_col])
                    u = str(row[pred_col])
                    if v in cycle_nodes and u in cycle_nodes:
                        edges_df = edges_df.drop(idx).reset_index(drop=True)
                        edges_removed += 1
                        break
                
                # Re-check with Kahn's
                adj_check = defaultdict(list)
                in_deg_check = defaultdict(int)
                nodes_check = set()
                
                for _, row in edges_df.iterrows():
                    u = str(row[pred_col])
                    v = str(row[succ_col])
                    if u in task_ids and v in task_ids:
                        adj_check[u].append(v)
                        in_deg_check[v] += 1
                        nodes_check.add(u)
                        nodes_check.add(v)
                
                for n in nodes_check:
                    if n not in in_deg_check:
                        in_deg_check[n] = 0
                
                q = deque([n for n in nodes_check if in_deg_check[n] == 0])
                sorted_count = 0
                while q:
                    u = q.popleft()
                    sorted_count += 1
                    for v in adj_check[u]:
                        in_deg_check[v] -= 1
                        if in_deg_check[v] == 0:
                            q.append(v)
                
                all_nodes = nodes_check
                cycle_nodes = {n for n in nodes_check if in_deg_check[n] > 0}
            
            if edges_removed > 0:
                report.add_warning(
                    f"[{project_id}] Đã xóa {edges_removed} cạnh để gỡ chu trình"
                )
        
        return edges_df
    
    def _check_durations(
        self, tasks_df: pd.DataFrame, report: ValidationReport, project_id: str
    ) -> pd.DataFrame:
        """Phát hiện task có duration ≤ 0 (trừ milestone)."""
        # Tìm các cột duration có thể tồn tại
        dur_cols = [c for c in tasks_df.columns if 'dur_' in c.lower() or 'duration' in c.lower()]
        
        if not dur_cols:
            return tasks_df
        
        zero_dur_tasks = []
        for idx, row in tasks_df.iterrows():
            total_dur = sum(
                abs(float(row.get(c, 0) or 0))
                for c in dur_cols
                if str(row.get(c, '')).replace('.', '').replace('-', '').isdigit()
                or isinstance(row.get(c), (int, float))
            )
            
            if total_dur <= 0:
                task_id = str(row.get('task_id', row.get('id', idx)))
                task_name = str(row.get('task_name', row.get('name', '')))
                zero_dur_tasks.append(f"{task_id} ({task_name[:30]})")
        
        if zero_dur_tasks:
            report.add_warning(
                f"[{project_id}] {len(zero_dur_tasks)} task(s) có duration=0 "
                f"(milestone hoặc thiếu dữ liệu): {zero_dur_tasks[:5]}"
            )
            
        return tasks_df
    
    def _sanitize_nan_inf(
        self, tasks_df: pd.DataFrame, report: ValidationReport, project_id: str
    ) -> pd.DataFrame:
        """Thay thế NaN và Inf bằng 0.0 cho tất cả cột số."""
        nan_count = 0
        inf_count = 0
        
        for col in tasks_df.columns:
            # Chỉ xử lý cột số
            if tasks_df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                nan_mask = tasks_df[col].isna()
                inf_mask = np.isinf(tasks_df[col].values) if tasks_df[col].dtype in ['float64', 'float32'] else pd.Series([False] * len(tasks_df))
                
                n_nan = nan_mask.sum()
                n_inf = inf_mask.sum() if isinstance(inf_mask, pd.Series) else inf_mask.sum()
                
                if n_nan > 0:
                    tasks_df[col] = tasks_df[col].fillna(0.0)
                    nan_count += n_nan
                if n_inf > 0:
                    tasks_df.loc[inf_mask, col] = 0.0
                    inf_count += n_inf
        
        if nan_count > 0 or inf_count > 0:
            report.add_warning(
                f"[{project_id}] Đã sanitize {nan_count} giá trị NaN và {inf_count} "
                f"giá trị Inf → 0.0"
            )
            
        return tasks_df
    
    def _check_resource_integrity(
        self, task_resources_df: pd.DataFrame, resources_df: pd.DataFrame,
        task_ids: Set[str], report: ValidationReport, project_id: str
    ):
        """Kiểm tra tham chiếu giữa task_resources và resources/tasks."""
        # Lấy tập resource IDs hợp lệ
        res_id_col = None
        for col_name in ['ID', 'id', 'resource_id']:
            if col_name in resources_df.columns:
                res_id_col = col_name
                break
        
        if res_id_col is None:
            report.add_warning(
                f"[{project_id}] Không tìm thấy cột ID trong resources.csv"
            )
            return
            
        valid_res_ids = set(resources_df[res_id_col].astype(str).tolist())
        
        # Kiểm tra task_resources tham chiếu resource không tồn tại
        if 'resource_id' in task_resources_df.columns:
            tr_res_ids = set(task_resources_df['resource_id'].astype(str).tolist())
            invalid_res = tr_res_ids - valid_res_ids
            invalid_res.discard('nan')
            invalid_res.discard('')
            
            if invalid_res:
                report.add_warning(
                    f"[{project_id}] task_resources.csv tham chiếu "
                    f"{len(invalid_res)} resource_id không tồn tại: "
                    f"{sorted(invalid_res)[:5]}"
                )
        
        # Kiểm tra task_resources tham chiếu task không tồn tại
        if 'task_id' in task_resources_df.columns:
            tr_task_ids = set(task_resources_df['task_id'].astype(str).tolist())
            invalid_tasks = tr_task_ids - task_ids
            invalid_tasks.discard('nan')
            invalid_tasks.discard('')
            
            if invalid_tasks:
                report.add_warning(
                    f"[{project_id}] task_resources.csv tham chiếu "
                    f"{len(invalid_tasks)} task_id không tồn tại: "
                    f"{sorted(invalid_tasks)[:5]}"
                )
