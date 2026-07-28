"""
Domain-Specific Feature Normalizers & Decoders System
=====================================================
Thư mục: ai_pipeline/models/moi/domain_normalizers.py

Chức năng:
    Quản lý Chuẩn hóa (Encoder) và Giải mã (Decoder) chuyên biệt cho từng loại hình dự án:
        - Civil Construction (CON): Scale chi phí lớn ($100k) cho vật tư & thiết bị.
        - IT & Logistics (ITLG): Scale chi phí vừa ($10k) cho nhân công & giờ trễ/OT.
        - Professional Services (PRO): Scale chi phí nhỏ ($5k) cho dịch vụ & tư vấn.

    Xử lý 9 nhóm feature (Group 0 -> Group 8):
        - Group 0: Thời lượng dựa trên Agenda ca làm việc thực tế (hours_per_day, days_per_week).
        - Group 1-3 & 5 & 8: Chi phí trực tiếp, gián tiếp, hợp đồng, logistics, dự toán -> Log-scale.
        - Group 4: Hệ số rủi ro -> Bounded MinMax.
        - Group 6: Thời gian tăng ca & Lag -> Log-scale.
        - Group 7: Cấu trúc đồ thị -> Graph MinMax.
"""

import os
import torch
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional


class WorkingCalendarEngine:
    """
    Động cơ Lịch Agenda tính toán thời gian động chi tiết theo ca làm việc của từng Thứ (Thứ 2 -> Chủ Nhật)
    và danh sách ngày nghỉ lễ (holidays_list). Tuyệt đối không dùng số giờ khóa cứng!
    """
    def __init__(
        self,
        weekly_schedule: Optional[Dict[Any, float]] = None,
        holidays_list: Optional[list] = None,
        default_hours_per_day: float = 8.0,
        default_days_per_week: float = 5.0
    ):
        self.weekly_schedule = {}
        day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
        
        if weekly_schedule and isinstance(weekly_schedule, dict):
            for k, v in weekly_schedule.items():
                k_lower = str(k).strip().lower()
                day_idx = day_map.get(k_lower)
                if day_idx is None:
                    try:
                        day_idx = int(k) % 7
                    except (ValueError, TypeError):
                        continue
                
                # Tính tổng số giờ từ số hoặc cấu trúc shifts dict
                if isinstance(v, (int, float)):
                    self.weekly_schedule[day_idx] = max(0.0, float(v))
                elif isinstance(v, dict):
                    if not v.get('is_working', True):
                        self.weekly_schedule[day_idx] = 0.0
                    else:
                        shifts = v.get('shifts', [])
                        if shifts:
                            total_h = sum(float(s.get('hours', 0.0)) for s in shifts if isinstance(s, dict))
                            self.weekly_schedule[day_idx] = max(0.0, total_h)
                        else:
                            self.weekly_schedule[day_idx] = default_hours_per_day

        if not self.weekly_schedule or sum(self.weekly_schedule.values()) <= 0:
            # Lịch mặc định tiêu chuẩn: T2->T6: 8h, T7/CN: 0h
            self.weekly_schedule = {
                0: default_hours_per_day,
                1: default_hours_per_day,
                2: default_hours_per_day,
                3: default_hours_per_day,
                4: default_hours_per_day,
                5: 0.0,
                6: 0.0
            }

        self.holidays_set = set(holidays_list or [])
        self.hours_per_week = sum(self.weekly_schedule.values())
        if self.hours_per_week <= 0:
            self.hours_per_week = max(1.0, default_hours_per_day * default_days_per_week)

        self.hours_per_month = round(self.hours_per_week * 4.33, 2)
        self.working_days_per_week = sum(1 for h in self.weekly_schedule.values() if h > 0)
        self.avg_hours_per_day = round(self.hours_per_week / max(1.0, float(self.working_days_per_week or 5.0)), 2)

    def get_shift_hours(self, weekday: int) -> float:
        """Lấy số giờ ca làm việc của 1 Thứ trong tuần (0=Thứ 2, ..., 6=Chủ Nhật)."""
        return self.weekly_schedule.get(int(weekday) % 7, 0.0)

    def calculate_task_total_hours(self, task_data: Dict[str, Any]) -> float:
        """
        Quy đổi tổng số giờ thi công thực tế của công việc dựa trên duration_hours hoặc lịch ca làm việc.
        """
        d_h = float(task_data.get('duration_hours', task_data.get('duration', 0.0)) or 0.0)
        if d_h > 0.0:
            return max(0.1, d_h)
            
        d_m = float(task_data.get('duration_months', 0.0) or 0.0)
        d_w = float(task_data.get('duration_weeks', 0.0) or 0.0)
        d_d = float(task_data.get('duration_days', 0.0) or 0.0)
        
        total_hours = d_m * self.hours_per_month + d_w * self.hours_per_week + d_d * self.avg_hours_per_day
        return max(0.1, total_hours)


def calculate_task_total_hours(
    task_data: Dict[str, Any],
    hours_per_day: float = 8.0,
    days_per_week: float = 5.0
) -> float:
    engine = WorkingCalendarEngine(default_hours_per_day=hours_per_day, default_days_per_week=days_per_week)
    return engine.calculate_task_total_hours(task_data)


class BaseProjectNormalizer:
    """
    Lớp chuẩn hóa & giải mã cơ sở cho từng loại hình dự án.
    """
    def __init__(
        self,
        project_type: str = "general",
        s_domain: float = 10000.0,
        hours_per_day: float = 8.0,
        days_per_week: float = 5.0
    ):
        self.project_type = project_type.upper()
        self.s_domain = max(1.0, s_domain)
        self.hours_per_day = max(1.0, hours_per_day)
        self.days_per_week = max(1.0, days_per_week)
        self.hours_per_week = self.days_per_week * self.hours_per_day
        self.hours_per_month = 4.0 * self.hours_per_week

    def encode_task_df(self, tasks_df: pd.DataFrame) -> torch.Tensor:
        """
        Chuyển đổi DataFrame tasks.csv thành Tensor [N, 39] chuẩn hóa gồm 1 chỉ số thời gian duration_hours + 38 cột chi phí chuẩn.
        """
        features_list = []
        
        # Danh sách 38 cột chi phí chuẩn theo đúng sơ đồ INPUT của hệ thống
        cost_columns = [
            # Group 1: Resource Costs (6)
            'labor', 'material', 'equipment', 'energy', 'testing_inspection', 'project_management',
            # Group 2: Overhead Costs (5)
            'facility', 'utilities', 'communication', 'training', 'quality_management',
            # Group 3: Time-dependent Costs (7)
            'overtime', 'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay', 'expediting',
            # Group 4: Risk & Compliance Costs (7)
            'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance', 'contingency_reserve', 'management_reserve',
            # Group 5: Supply Chain & External Costs (6)
            'transportation', 'ordering', 'packaging', 'reverse_logistics', 'customs', 'supplier_coordination',
            # Group 6: Strategic & Financial Costs (7)
            'opportunity_cost', 'capital_cost', 'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
        ]

        # Ánh xạ Alias đọc linh hoạt các tên cột tương đương từ CSV/DB
        aliases = {
            'labor': ['internal_labor_cost', 'labor'],
            'material': ['material_cost', 'material'],
            'equipment': ['equipment_fuel_cost', 'equipment'],
            'testing_inspection': ['qa_qc_cost', 'testing_inspection'],
            'facility': ['facility_rent', 'facility'],
            'utilities': ['utilities_cost', 'utilities'],
            'communication': ['communication_cost', 'communication'],
            'training': ['training_cost', 'training'],
            'overtime': ['overtime_cost', 'overtime'],
            'inventory_holding': ['holding_cost', 'inventory_holding'],
            'insurance': ['insurance_cost', 'insurance'],
            'warranty': ['warranty_cost', 'warranty'],
            'regulatory_compliance': ['licensing_cost', 'regulatory_compliance'],
            'transportation': ['international_freight', 'transportation']
        }

        for idx, row in tasks_df.iterrows():
            feat = []
            
            # --- 1. Duration Metric (1 feature tiêu chuẩn) ---
            d_h = float(row.get('duration_hours', row.get('duration', 0.0)) or 0.0)
            feat.append(np.log1p(max(0.0, d_h)))
            
            # --- 2. Standard 38 Cost Columns (38 features) ---
            for col in cost_columns:
                val = 0.0
                possible_names = aliases.get(col, [col])
                for pname in possible_names:
                    if pname in row and pd.notna(row[pname]):
                        try:
                            val = float(row[pname])
                            break
                        except (ValueError, TypeError):
                            pass
                feat.append(np.log1p(max(0.0, val) / self.s_domain))

            features_list.append(feat)
            
        if not features_list:
            return torch.zeros((0, 39), dtype=torch.float32)
            
        tensor_x = torch.tensor(features_list, dtype=torch.float32)
        
        # Z-Score Normalization theo từng chiều đặc trưng để giữ phân phối chuẩn N(0, 1)
        mean = torch.mean(tensor_x, dim=0, keepdim=True)
        std = torch.std(tensor_x, dim=0, keepdim=True) + 1e-6
        norm_tensor_x = (tensor_x - mean) / std
        
        # Clamp biên độ đặc trưng trong khoảng an toàn [-5.0, 5.0] chống ngoại lệ (Outliers)
        norm_tensor_x = torch.clamp(norm_tensor_x, min=-5.0, max=5.0)
        return norm_tensor_x


    def decode_predictions(self, preds_dict: Dict[str, torch.Tensor]) -> Dict[str, np.ndarray]:
        """
        Giải mã các thông số AI đầu ra ra đúng đơn vị thực tế (giờ, hệ số rủi ro).
        """
        duration_factor = preds_dict['duration_factor'].cpu().numpy()
        expected_delay_norm = preds_dict['expected_delay'].cpu().numpy()
        sigma_norm = preds_dict['uncertainty_sigma'].cpu().numpy()
        
        # Decode expected delay từ log-space sang số giờ thực tế
        expected_delay_hours = np.expm1(expected_delay_norm)
        
        return {
            'duration_factor': duration_factor,
            'expected_delay_hours': expected_delay_hours,
            'uncertainty_sigma': sigma_norm
        }

    def decode_reconstructed_features(self, norm_tensor: torch.Tensor) -> np.ndarray:
        """
        Giải mã Tensor tái tạo [N, 39] từ Phase 0 Pretrainer trở lại giá trị quy mô thực tế.
        """
        arr = norm_tensor.detach().cpu().numpy()
        raw = np.zeros_like(arr)
        
        # Index 0: Duration hours
        raw[:, 0] = np.expm1(arr[:, 0])
        
        # Indices 1-38: Standard 38 Cost features
        if arr.shape[1] > 1:
            raw[:, 1:] = np.expm1(arr[:, 1:]) * self.s_domain
            
        return raw


class CivilConstructionNormalizer(BaseProjectNormalizer):
    """
    Normalizer chuyên biệt cho Xây dựng công trình (CON).
    Scale chi phí s_domain = $100,000.
    """
    def __init__(self, hours_per_day: float = 8.0, days_per_week: float = 5.0):
        super().__init__(project_type="CON", s_domain=100000.0, hours_per_day=hours_per_day, days_per_week=days_per_week)


class ITLogisticsNormalizer(BaseProjectNormalizer):
    """
    Normalizer chuyên biệt cho IT & Logistics (ITLG).
    Scale chi phí s_domain = $10,000.
    """
    def __init__(self, hours_per_day: float = 8.0, days_per_week: float = 5.0):
        super().__init__(project_type="ITLG", s_domain=10000.0, hours_per_day=hours_per_day, days_per_week=days_per_week)


class ProfessionalServicesNormalizer(BaseProjectNormalizer):
    """
    Normalizer chuyên biệt cho Dịch vụ Chuyên môn (PRO).
    Scale chi phí s_domain = $5,000.
    """
    def __init__(self, hours_per_day: float = 8.0, days_per_week: float = 5.0):
        super().__init__(project_type="PRO", s_domain=5000.0, hours_per_day=hours_per_day, days_per_week=days_per_week)


class NormalizerRegistry:
    """
    Registry Factory nạp đúng Normalizer theo mã project_type.
    """
    _normalizers = {
        'con': CivilConstructionNormalizer,
        'civil_construction': CivilConstructionNormalizer,
        'itlg': ITLogisticsNormalizer,
        'it_logistics': ITLogisticsNormalizer,
        'pro': ProfessionalServicesNormalizer,
        'professional_services': ProfessionalServicesNormalizer,
    }
    
    @classmethod
    def get_normalizer(
        cls,
        project_type: str,
        hours_per_day: float = 8.0,
        days_per_week: float = 5.0
    ) -> BaseProjectNormalizer:
        key = str(project_type).lower().strip()
        normalizer_cls = cls._normalizers.get(key, ITLogisticsNormalizer)
        return normalizer_cls(hours_per_day=hours_per_day, days_per_week=days_per_week)
