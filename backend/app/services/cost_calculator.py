from enum import Enum
from typing import Dict, Any

class ProjectType(str, Enum):
    ITS = "ITS"
    CON = "CON"
    IND = "IND"
    PRO = "PRO"
    TRL = "TRL"

class CostCalculator:
    """
    Tính toán Total Cost (Chi phí tổng) và Base Cost (Chi phí thô) dựa trên mô hình 7 Nhóm Đặc trưng (7 Groups)
    áp dụng cho 5 loại dự án (Project Types).
    """

    @staticmethod
    def calculate_total_cost(project_type: ProjectType, task_data: Dict[str, float]) -> Dict[str, Any]:
        # ==========================================
        # LẤY CÁC BIẾN SỐ ĐẦU VÀO TỪ G3 VÀ G7
        # ==========================================
        # G3 - Nhân công
        worker_count = task_data.get("worker_count", 0.0)
        hourly_rate = task_data.get("hourly_rate", 0.0)
        ot_rate = task_data.get("ot_rate", 0.0)
        
        # G7 - Thời gian
        duration_hours = task_data.get("duration_hours", 0.0)
        ot_hours = task_data.get("ot_hours", 0.0)
        lag_days = task_data.get("lag_days", 0.0)
        duration_days = task_data.get("duration_days", 0.0)
        duration_months = task_data.get("duration_months", 0.0)

        # ==========================================
        # TÍNH TOÁN CÁC THÀNH PHẦN CHI PHÍ (G1, G2, G4, G6)
        # ==========================================
        # G1: Chi phí trực tiếp
        # Ghi chú: Thời gian được nhân trực tiếp vào bên trong công thức
        g1_internal_labor = worker_count * duration_hours * hourly_rate
        g1_ot = worker_count * ot_hours * ot_rate
        g1_fuel = task_data.get("fuel_consumption_per_day", 0.0) * task_data.get("fuel_price", 0.0) * duration_days
        g1_qa_qc = task_data.get("qa_qc_cost", 0.0)
        g1_material = task_data.get("material_cost", 0.0)
        g1_subcontracting = task_data.get("subcontracting_cost", 0.0)

        # G2: Chi phí gián tiếp
        g2_training = task_data.get("training_cost", 0.0)
        g2_facility_rent = task_data.get("facility_rent_per_month", 0.0) * duration_months
        g2_communication = task_data.get("communication_cost_per_month", 0.0) * duration_months
        g2_utilities = task_data.get("utilities_per_month", 0.0) * duration_months

        # G4: Chi phí hợp đồng
        g4_insurance = task_data.get("insurance_per_month", 0.0) * duration_months
        g4_licensing = task_data.get("licensing_cost", 0.0)
        g4_warranty = task_data.get("warranty_reserve", 0.0) # Có thể được tính lại bằng % của (G1+G2)

        # G6: Chi phí Logistic
        g6_holding = task_data.get("holding_cost_per_day", 0.0) * lag_days
        g6_intl_freight = task_data.get("intl_freight_cost", 0.0)
        g6_handling = task_data.get("handling_cost", 0.0)
        g6_reverse = task_data.get("reverse_logistics_cost", 0.0)
        g6_obsolescence = task_data.get("obsolescence_cost", 0.0)

        # ==========================================
        # HỆ SỐ RỦI RO (G5)
        # ==========================================
        # Giá trị truyền vào là phần trăm (vd: 0.05 = 5%)
        risk_complexity = task_data.get("risk_complexity", 0.0)
        risk_weather = task_data.get("risk_weather", 0.0)
        risk_rework = task_data.get("risk_rework", 0.0)
        risk_unexpected = task_data.get("risk_unexpected", 0.0)

        risk_multiplier = 1.0 + risk_complexity + risk_weather + risk_rework + risk_unexpected

        # ==========================================
        # TÍNH BASE COST CHO TỪNG LOẠI DỰ ÁN
        # ==========================================
        base_cost = 0.0

        if project_type == ProjectType.ITS:
            base_cost = (
                (g1_ot + g1_subcontracting + g1_qa_qc + g2_training) + # Fixed
                (g1_internal_labor + g2_facility_rent + g2_utilities + g2_communication) # Time-dependent
            )
        elif project_type == ProjectType.CON:
            base_cost = (
                (g1_material + g1_qa_qc + g1_subcontracting + g4_licensing + g4_warranty + g6_handling + g6_reverse + g6_obsolescence) + # Fixed
                (g1_internal_labor + g1_fuel + g2_facility_rent + g2_utilities + g4_insurance) + # Time-dependent
                (g6_holding) # Lag-dependent
            )
        elif project_type == ProjectType.IND:
            base_cost = (
                (g1_material + g1_subcontracting + g4_licensing + g4_warranty + g6_intl_freight + g6_handling) + # Fixed
                (g1_internal_labor + g1_fuel + g2_facility_rent + g2_utilities) + # Time-dependent
                (g6_holding) # Lag-dependent
            )
        elif project_type == ProjectType.PRO:
            base_cost = (
                (g1_subcontracting + g2_training) + # Fixed
                (g1_internal_labor + g2_facility_rent + g2_communication) # Time-dependent
            )
        elif project_type == ProjectType.TRL:
            base_cost = (
                (g1_subcontracting + g4_licensing + g6_intl_freight + g6_handling) + # Fixed
                (g1_fuel + g1_internal_labor + g4_insurance) + # Time-dependent
                (g6_holding) # Lag-dependent
            )
        else:
            raise ValueError(f"Project type {project_type} is not supported.")

        # ==========================================
        # TOTAL COST
        # ==========================================
        total_cost = base_cost * risk_multiplier
        
        return {
            "base_cost": base_cost,
            "total_cost": total_cost,
            "risk_multiplier": risk_multiplier,
            "breakdown": {
                "G1_Direct": g1_internal_labor + g1_ot + g1_fuel + g1_qa_qc + g1_material + g1_subcontracting,
                "G2_Indirect": g2_training + g2_facility_rent + g2_communication + g2_utilities,
                "G4_Contractual": g4_insurance + g4_licensing + g4_warranty,
                "G6_Logistics": g6_holding + g6_intl_freight + g6_handling + g6_reverse + g6_obsolescence
            }
        }
