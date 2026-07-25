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


def calculate_task_total_hours(
    task_data: Dict[str, Any],
    hours_per_day: float = 8.0,
    days_per_week: float = 5.0
) -> float:
    """
    Quy đổi tổng số giờ thực hiện công việc dựa trên các thuộc tính duration_months, duration_weeks,
    duration_days, duration_hours và cấu hình ca làm việc của Agenda.
    """
    h_per_day = max(1.0, float(hours_per_day))
    d_per_week = max(1.0, float(days_per_week))
    h_per_week = d_per_week * h_per_day
    h_per_month = 4.0 * h_per_week
    
    d_m = float(task_data.get('duration_months', 0.0) or 0.0)
    d_w = float(task_data.get('duration_weeks', 0.0) or 0.0)
    d_d = float(task_data.get('duration_days', 0.0) or 0.0)
    d_h = float(task_data.get('duration_hours', task_data.get('duration', 0.0)) or 0.0)
    
    total_hours = d_m * h_per_month + d_w * h_per_week + d_d * h_per_day + d_h
    return max(0.1, total_hours)


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
        Chuyển đổi DataFrame tasks.csv thành Tensor đã chuẩn hóa [N, 72].
        """
        features_list = []
        
        for idx, row in tasks_df.iterrows():
            feat = [0.0] * 72
            
            # --- Group 0: Time & Schedule (Indices 0 - 3) ---
            d_w = float(row.get('duration_weeks', 0.0) or 0.0)
            d_d = float(row.get('duration_days', 0.0) or 0.0)
            d_h = float(row.get('duration_hours', 0.0) or 0.0)
            
            # Quy đổi tổng giờ dựa trên Agenda
            total_hours = calculate_task_total_hours(row.to_dict(), self.hours_per_day, self.days_per_week)
            feat[0] = np.log1p(max(0.0, total_hours))
            feat[1] = np.log1p(max(0.0, d_w))
            feat[2] = np.log1p(max(0.0, d_d))
            feat[3] = np.log1p(max(0.0, d_h))
            
            # --- Group 1: Direct Costs (Indices 4 - 9) ---
            direct_cols = ['internal_labor_cost', 'overtime_cost', 'equipment_fuel_cost', 'qa_qc_cost', 'material_cost', 'outsourcing_cost']
            for i, col in enumerate(direct_cols, start=4):
                val = float(row.get(col, row.get(col.replace('internal_labor_cost', 'labor'), 0.0)) or 0.0)
                feat[i] = np.log1p(max(0.0, val) / self.s_domain)
                
            # --- Group 2: Indirect Overhead (Indices 10 - 13) ---
            indirect_cols = ['training_cost', 'facility_rent', 'communication_cost', 'utilities_cost']
            for i, col in enumerate(indirect_cols, start=10):
                val = float(row.get(col, 0.0) or 0.0)
                feat[i] = np.log1p(max(0.0, val) / self.s_domain)
                
            # --- Group 3: Contractual Costs (Indices 14 - 16) ---
            contract_cols = ['insurance_cost', 'licensing_cost', 'warranty_cost']
            for i, col in enumerate(contract_cols, start=14):
                val = float(row.get(col, 0.0) or 0.0)
                feat[i] = np.log1p(max(0.0, val) / self.s_domain)
                
            # --- Group 4: Risk & Contingencies (Indices 17 - 20) ---
            feat[17] = min(1.0, max(0.0, float(row.get('complexity', 0.1) or 0.1)))
            feat[18] = min(1.0, max(0.0, float(row.get('weather_contingency', 0.0) or 0.0)))
            feat[19] = min(1.0, max(0.0, float(row.get('general_contingency', 0.05) or 0.05)))
            feat[20] = min(1.0, max(0.0, float(row.get('rework_risk', 0.0) or 0.0)))
            
            # --- Group 5: Logistics Costs (Indices 21 - 25) ---
            logistics_cols = ['holding_cost', 'international_freight', 'handling_cost', 'reverse_logistics', 'defect_cost']
            for i, col in enumerate(logistics_cols, start=21):
                val = float(row.get(col, 0.0) or 0.0)
                feat[i] = np.log1p(max(0.0, val) / self.s_domain)
                
            # --- Group 6: Time Adjustments (Indices 26 - 27) ---
            feat[26] = np.log1p(max(0.0, float(row.get('overtime_hours', 0.0) or 0.0)))
            feat[27] = np.log1p(max(0.0, float(row.get('lag_time', 0.0) or 0.0)))
            
            # --- Group 7 & 8 & Other numerical columns (Indices 28 - 71) ---
            curr_idx = 28
            for col_name, col_val in row.items():
                if curr_idx >= 72:
                    break
                if col_name not in ['task_id', 'id', 'task_name', 'name', 'baseline_start']:
                    try:
                        v = float(col_val)
                        if not np.isnan(v) and not np.isinf(v):
                            if v > 100.0:
                                feat[curr_idx] = np.log1p(v / self.s_domain)
                            else:
                                feat[curr_idx] = v
                            curr_idx += 1
                    except (ValueError, TypeError):
                        pass

            features_list.append(feat)
            
        if not features_list:
            return torch.zeros((0, 72), dtype=torch.float32)
            
        tensor_x = torch.tensor(features_list, dtype=torch.float32)
        
        # Z-Score Normalization theo tung chieu dac trung de giu phan phoi phuan N(0, 1)
        mean = torch.mean(tensor_x, dim=0, keepdim=True)
        std = torch.std(tensor_x, dim=0, keepdim=True) + 1e-6
        norm_tensor_x = (tensor_x - mean) / std
        
        # Clamp bien do dac trung trong khoang an toan [-5.0, 5.0] chong ngoai le (Outliers)
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
        Giải mã Tensor tái tạo [N, 72] từ Phase 0 Pretrainer trở lại giá trị quy mô thực tế.
        """
        arr = norm_tensor.detach().cpu().numpy()
        raw = np.zeros_like(arr)
        
        # Group 0: Time (Indices 0 - 3)
        raw[:, 0] = np.expm1(arr[:, 0]) # Total hours
        raw[:, 1] = np.expm1(arr[:, 1]) # Weeks
        raw[:, 2] = np.expm1(arr[:, 2]) # Days
        raw[:, 3] = np.expm1(arr[:, 3]) # Hours
        
        # Group 1-3 & 5: Costs
        cost_indices = list(range(4, 17)) + list(range(21, 26))
        for idx in cost_indices:
            raw[:, idx] = np.expm1(arr[:, idx]) * self.s_domain
            
        # Group 4: Risk (Indices 17 - 20)
        raw[:, 17:21] = arr[:, 17:21]
        
        # Group 6: Time Adjustments (26 - 27)
        raw[:, 26] = np.expm1(arr[:, 26])
        raw[:, 27] = np.expm1(arr[:, 27])
        
        # Group 7-8: Rest
        raw[:, 28:] = arr[:, 28:]
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
