"""
Ma trận Tương tác Feature 34x34 (Sparse Format)
Dự án: GLPO - Cập nhật Schema Task mới (tối giản từ 72x72)

Quy ước giá trị:
  +1.0  = Khuếch đại mạnh (Strong Amplification)
  +0.5  = Bổ trợ vừa (Moderate Complementary)  
  +0.3  = Bổ trợ nhẹ (Weak Complementary)
  -1.0  = Cạnh tranh mạnh (Strong Competition)
  -0.5  = Đối kháng vừa (Moderate Offset)
  -0.3  = Đối kháng nhẹ (Weak Offset)
   0    = Không tương tác (mặc định)
"""

import numpy as np

# ============================================================================
# DANH SÁCH 34 FEATURES (Khớp chính xác với app/models/task.py)
# ============================================================================
FEATURE_INDEX = {
    # === Hub Time (0-4) ===
    0: "duration_months",
    1: "duration_weeks",
    2: "duration_days",
    3: "duration_hours",
    4: "calendar_type_247",
    
    # === G1: Direct Costs (5-10) ===
    5: "internal_labor_cost",
    6: "overtime_cost",
    7: "equipment_fuel_cost",
    8: "qa_qc_cost",
    9: "material_cost",
    10: "outsourcing_cost",
    
    # === G2: Indirect Costs (11-14) ===
    11: "training_cost",
    12: "facility_rent",
    13: "communication_cost",
    14: "utilities_cost",
    
    # === G3: Contractual Costs (15-17) ===
    15: "insurance_cost",
    16: "licensing_cost",
    17: "warranty_cost",
    
    # === G4: Risk Costs (18-21) ===
    18: "complexity",
    19: "weather_contingency",
    20: "general_contingency",
    21: "rework_risk",
    
    # === G5: Logistics Costs (22-26) ===
    22: "holding_cost",
    23: "international_freight",
    24: "handling_cost",
    25: "reverse_logistics",
    26: "defect_cost",
    
    # === G6: Time & Schedule (27-28) ===
    27: "overtime_hours",
    28: "lag_time",
    
    # === G7: AI Topology (29-33) ===
    29: "in_degree",
    30: "out_degree",
    31: "is_critical",
    32: "total_float",
    33: "path_length",
    34: "total_resource_demand",
    35: "resource_cost_estimate",
}

# ============================================================================
# MA TRẬN TƯƠNG TÁC (Sparse Format)
# ============================================================================
INTERACTIONS = [
    # Hub Time Interactions
    (0, 1, 0.5, "Months bổ trợ Weeks"),
    (0, 2, 0.5, "Months bổ trợ Days"),
    
    # Direct Cost Interactions
    (5, 10, -1.0, "Internal Labor ⚔️ Outsourcing (Thay thế lẫn nhau)"),
    (5, 6, 0.5, "Internal 🤝 Overtime"),
    (10, 6, -0.5, "Outsourcing ⚔️ Overtime (Thuê ngoài thì ít OT)"),
    (9, 23, 1.0, "Material 📈 Freight (Mua vật liệu cần vận chuyển)"),
    (35, 5, 0.5, "Resource Cost 🤝 Internal Labor"),
    (35, 10, 0.5, "Resource Cost 🤝 Outsourcing"),
    
    # Indirect / Contractual
    (12, 14, 0.5, "Facility 🤝 Utilities"),
    
    # Risks
    (18, 21, 1.0, "Complexity 📈 Rework (Phức tạp dễ làm lại)"),
    (21, 20, 0.5, "Rework 🤝 Contingency (Làm lại tốn dự phòng)"),
    
    # Logistics
    (22, 26, 0.5, "Holding 🤝 Defect (Tồn kho lâu dễ hỏng)"),
    (23, 24, 0.5, "Freight 🤝 Handling (Vận chuyển cần bốc dỡ)"),
    
    # Time / AI Topology
    (27, 6, 1.0, "Overtime Hours 📈 Overtime Cost"),
    (29, 18, 0.5, "In-degree 🤝 Complexity (Nhiều input -> phức tạp)"),
    (31, 20, 0.5, "Critical 🤝 Contingency (Đường găng cần dự phòng)"),
    (32, 28, 1.0, "Total Float 📈 Lag Time (Có float dễ trễ)"),
    
    # Cross Group
    (0, 12, 1.0, "Duration 📈 Facility Rent (Kéo dài thì tốn tiền thuê)"),
    (0, 14, 0.5, "Duration 🤝 Utilities"),
    (9, 22, 0.5, "Material 🤝 Holding Cost"),
    (18, 8, 0.8, "Complexity 📈 QA/QC (Phức tạp cần test nhiều)"),
]

def build_sparse_matrix(interactions, size=36):
    matrix = np.zeros((size, size), dtype=np.float32)
    np.fill_diagonal(matrix, 1.0)
    for src, tgt, val, _ in interactions:
        if 0 <= src < size and 0 <= tgt < size:
            matrix[src][tgt] = val
    return matrix

def get_gamma_matrix(project_type: str = "Logistics") -> np.ndarray:
    """Xây dựng ma trận tương tác nhóm (8x8)"""
    # 8 Groups: Hub, G1_Direct, G2_Indirect, G3_Contractual, G4_Risk, G5_Logistics, G6_Time, G7_Topology
    gamma = np.zeros((8, 8), dtype=np.float32)
    
    if project_type.upper() == "IT" or project_type.upper() == "SOFTWARE":
        gamma[1, 4] = gamma[4, 1] = 0.9  # Direct Cost 📈 Risk Cost (Nhân sự vs Lỗi rủi ro)
        gamma[0, 4] = gamma[4, 0] = 0.8  # Time 📈 Risk 
    else:
        gamma[0, 2] = gamma[2, 0] = 0.8  # Time 📈 Indirect Cost
        gamma[1, 5] = gamma[5, 1] = 0.8  # Direct Cost 📈 Logistics
        
    return gamma

def get_interactions(project_type: str = "Logistics") -> list:
    base = INTERACTIONS.copy()
    if project_type.upper() == "IT" or project_type.upper() == "SOFTWARE":
        base.append((18, 21, 1.5, "IT: Phức tạp -> Rework cực cao"))
        base.append((31, 27, 0.8, "IT: Đường găng -> Ép OT mạnh"))
    return base

def get_feature_group_map(project_type: str = "Logistics") -> dict:
    """Ánh xạ 36 features thành 8 nhóm"""
    return {
        0: list(range(0, 5)),    # Hub
        1: list(range(5, 11)) + [34, 35],   # G1: Direct (thêm 34, 35)
        2: list(range(11, 15)),  # G2: Indirect
        3: list(range(15, 18)),  # G3: Contractual
        4: list(range(18, 22)),  # G4: Risk
        5: list(range(22, 27)),  # G5: Logistics
        6: list(range(27, 29)),  # G6: Time
        7: list(range(29, 34)),  # G7: Topology
    }

if __name__ == "__main__":
    matrix = build_sparse_matrix(INTERACTIONS)
    print(f"Matrix shape: {matrix.shape}")
