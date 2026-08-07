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
from ai_pipeline.models.moi.utils.calendar_engine import WorkingCalendarEngine, calculate_task_total_hours

class BaseProjectNormalizer:
    """
    Lớp chuẩn hóa & giải mã cơ sở cho từng loại hình dự án.
    
    Quy định cách thức chuyển đổi các giá trị thô (raw values) như thời lượng thi công, 
    chi phí từ file CSV thành Tensors chuẩn hóa [0, 1] cho mô hình Neural Network HGT.
    Đồng thời đảm nhận chức năng Giải mã (Decode) đầu ra của AI trả về giá trị thực tế.
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
        Chuyển đổi DataFrame tasks.csv thành Tensor biểu diễn Node Task.

        Tensor kết quả có shape [N, 39], trong đó N là số lượng công việc.
        Bao gồm 1 đặc trưng thời gian (duration_hours) và 38 đặc trưng chi phí
        dàn trải qua 9 nhóm (Group 0 -> Group 8). Các chi phí được Normalize
        thông qua hàm Log-scale theo hệ số quy mô s_domain của từng dự án.

        Args:
            tasks_df (pd.DataFrame): DataFrame nạp từ tasks.csv.

        Returns:
            torch.Tensor: FloatTensor [N, 39].
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


    def decode_predictions(self, preds: Dict[str, torch.Tensor]) -> Dict[str, np.ndarray]:
        """
        Giải mã Tensor kết quả dự đoán của mô hình HGT về lại đơn vị thực tế.

        Args:
            preds (Dict[str, torch.Tensor]): Từ điển chứa kết quả đầu ra của mô hình 
                                             (duration_factor, expected_delay, uncertainty_sigma).

        Returns:
            Dict[str, np.ndarray]: Từ điển kết quả đã được chuyển đổi về Numpy Array gốc.
                                   Ví dụ: expected_delay_hours theo định dạng thời gian thực tế.
        """
        duration_factor = preds['duration_factor'].cpu().numpy()
        expected_delay_norm = preds['expected_delay'].cpu().numpy()
        sigma_norm = preds['uncertainty_sigma'].cpu().numpy()
        
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
    Bộ chuẩn hóa chuyên biệt cho dự án Xây dựng (Civil Construction - CON).
    Đặc tính: Scale chi phí s_domain cực lớn (100,000 USD).
    """
    def __init__(self, hours_per_day: float = 8.0, days_per_week: float = 5.0):
        super().__init__(project_type="CON", s_domain=100000.0, hours_per_day=hours_per_day, days_per_week=days_per_week)


class ITLogisticsNormalizer(BaseProjectNormalizer):
    """
    Bộ chuẩn hóa chuyên biệt cho dự án Công nghệ Thông tin & Logistics (ITLG).
    Đặc tính: Scale chi phí s_domain vừa phải (10,000 USD). Nhạy cảm với chậm trễ (Agile/Sprint).
    """
    def __init__(self, hours_per_day: float = 8.0, days_per_week: float = 5.0):
        super().__init__(project_type="ITLG", s_domain=10000.0, hours_per_day=hours_per_day, days_per_week=days_per_week)


class ProfessionalServicesNormalizer(BaseProjectNormalizer):
    """
    Bộ chuẩn hóa chuyên biệt cho dự án Dịch vụ / Tư vấn (Professional Services - PRO).
    Đặc tính: Scale chi phí s_domain nhỏ (5,000 USD). Phụ thuộc nhiều vào chi phí tư vấn.
    """
    def __init__(self, hours_per_day: float = 8.0, days_per_week: float = 5.0):
        super().__init__(project_type="PRO", s_domain=5000.0, hours_per_day=hours_per_day, days_per_week=days_per_week)


class NormalizerRegistry:
    """
    Nhà máy (Factory Pattern) sinh các lớp Normalizer tùy theo mã loại hình dự án.
    Nếu mã không nhận diện được, tự động Fallback về IT Logistics Normalizer.
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
