"""
Ma trận Tương tác Feature 72×72 (Sparse Format)
Dự án: GLPO - Graph Logistics Project Optimization
Nguồn: PMBOK 7th Ed, RCPSP Literature, SCM Cost Interaction Research

Quy ước giá trị:
  +1.0  = Khuếch đại mạnh (Strong Amplification)
  +0.5  = Bổ trợ vừa (Moderate Complementary)  
  +0.3  = Bổ trợ nhẹ (Weak Complementary)
  -1.0  = Cạnh tranh mạnh (Strong Competition)
  -0.5  = Đối kháng vừa (Moderate Offset)
  -0.3  = Đối kháng nhẹ (Weak Offset)
   0    = Không tương tác (mặc định, không liệt kê)
"""

# ============================================================================
# DANH SÁCH 72 FEATURES (Đánh Index 0-71)
# ============================================================================
FEATURE_INDEX = {
    # === Hub (0-6) ===
    0:  "baseline_start_relative",
    1:  "duration_months",
    2:  "duration_weeks",
    3:  "duration_days",
    4:  "duration_hours",
    5:  "calendar_type_agenda",    # One-hot
    6:  "calendar_type_247",       # One-hot
    
    # === G1: Direct Costs (7-14) ===
    7:  "internal_labor_cost",
    8:  "subcontracting_cost",
    9:  "overtime_crashing_cost",
    10: "material_cost",
    11: "equipment_cost",
    12: "direct_transportation",
    13: "energy_fuel_cost",
    14: "testing_and_inspection",
    
    # === G2: Indirect Costs (15-20) ===
    15: "pm_overhead",
    16: "facility_rent",
    17: "utilities",
    18: "communication_cost",
    19: "internal_training",
    20: "quality_mgmt_overhead",
    
    # === G4: Contractual (21-24) ===
    21: "permits_and_licensing",
    22: "project_insurance",
    23: "warranty_and_after_sales",
    24: "regulatory_compliance",
    
    # === G5: Logistics & SCM (25-31) ===
    25: "inventory_holding_cost",
    26: "ordering_cost",
    27: "shortage_stockout",
    28: "obsolescence_cost",
    29: "international_freight",
    30: "packaging_and_handling",
    31: "reverse_logistics",
    
    # === G6: Temporal Extended (32-36) ===
    32: "wait_queue_time",
    33: "setup_transition_time",
    34: "induction_time",
    35: "lead_time",
    36: "pert_3_point_estimate",
    
    # === G7: Resources (37-41) ===
    37: "request_quantity",
    38: "allocated_quantity",
    39: "labor_productivity",
    40: "equipment_utilization",
    41: "resource_substitutability",
    
    # === G9: Risks (42-48) ===
    42: "technical_complexity",
    43: "rework_probability",
    44: "external_dependency_level",
    45: "contingency_reserve",
    46: "management_reserve",
    47: "weather_seasonal_risk",
    48: "technology_risk",
    
    # === G11: Human & Org (49-54) ===
    49: "required_skill_level",
    50: "staff_experience",
    51: "learning_curve_effect",
    52: "hr_stability_risk",
    53: "cross_functional_coordination",
    54: "occupational_safety_risk",
    
    # === G12: ESG (55-59) ===
    55: "environmental_impact",
    56: "waste_disposal_cost",
    57: "community_social_impact",
    58: "carbon_tax_credit",
    59: "esg_compliance",
    
    # === G3🤖: Opportunity Cost (60-62) ===
    60: "schedule_flexibility",
    61: "resource_alternative_cost",
    62: "delay_impact_cost",
    
    # === G8🤖: Network Topology (63-67) ===
    63: "in_degree",
    64: "out_degree",
    65: "is_critical",
    66: "total_float",
    67: "path_length",
    
    # === G10🤖: Earned Value (68-71) ===
    68: "planned_value",
    69: "earned_value",
    70: "cpi",
    71: "spi",
}

# ============================================================================
# MA TRẬN TƯƠNG TÁC (Sparse Format)
# Format: (source_idx, target_idx, value, rationale)
# Nguồn tham khảo: PMBOK, RCPSP Literature, SCM Cost Research
# ============================================================================
INTERACTIONS = [
    # =========================================================================
    # TẦNG 1: INTRA-GROUP (Trong cùng 1 Group)
    # =========================================================================

    # --- Hub: Duration components ---
    (1, 2, +0.5, "Months bổ trợ Weeks: cùng mô tả thời lượng"),
    (1, 3, +0.5, "Months bổ trợ Days"),
    (2, 3, +0.5, "Weeks bổ trợ Days"),
    (3, 4, +0.5, "Days bổ trợ Hours"),
    (5, 6, -1.0, "Agenda vs 24/7: loại trừ lẫn nhau (One-hot)"),
    
    # --- G1: Direct Costs ---
    (7, 8, -1.0, "Internal Labor ⚔️ Subcontracting: thay thế lẫn nhau (PMBOK Time-Cost Tradeoff)"),
    (7, 9, +0.5, "Internal Labor 🤝 Overtime: OT là phần mở rộng của nội bộ"),
    (8, 9, -0.5, "Subcontracting ⚔️ Overtime: thuê ngoài thì không cần OT nội bộ"),
    (10, 12, +1.0, "Material 📈 Transportation: mua nhiều → ship nhiều (SCM Classic Trade-off)"),
    (10, 30, +0.5, "Material 🤝 Packaging: mua nhiều → đóng gói nhiều"),
    (11, 13, +0.5, "Equipment 🤝 Energy: máy móc chạy → tiêu hao năng lượng"),
    (7, 14, +0.3, "Internal Labor 🤝 Testing: nhân sự nội bộ thường thực hiện kiểm tra"),
    (9, 7, +0.5, "Overtime 🤝 Internal Labor: OT tăng → chi phí labor tăng"),
    (12, 13, +1.0, "Transportation 📈 Energy: vận chuyển → nhiên liệu (SCM Research)"),
    
    # --- G2: Indirect Costs ---
    (15, 16, +0.3, "PM Overhead 🤝 Facility: quản lý dự án cần văn phòng"),
    (15, 17, +0.3, "PM Overhead 🤝 Utilities: quản lý → tiện ích (điện, nước)"),
    (15, 18, +0.5, "PM Overhead 🤝 Communication: quản lý → họp hành, liên lạc"),
    (19, 20, +0.5, "Training 🤝 Quality Overhead: đào tạo nâng cao chất lượng"),
    (16, 17, +0.5, "Facility 🤝 Utilities: thuê VP → phải trả tiện ích"),
    
    # --- G4: Contractual ---
    (21, 24, +0.5, "Permits 🤝 Regulatory: giấy phép gắn liền tuân thủ pháp luật"),
    (22, 23, +0.3, "Insurance 🤝 Warranty: bảo hiểm liên quan bảo hành"),
    (22, 24, +0.3, "Insurance 🤝 Regulatory: bảo hiểm bắt buộc theo quy định"),
    
    # --- G5: Logistics & SCM ---
    (25, 27, -1.0, "Inventory ⚔️ Shortage: giữ nhiều hàng → giảm thiếu hụt (Classic SCM Trade-off)"),
    (25, 28, +1.0, "Inventory 📈 Obsolescence: tồn kho lâu → hàng hết hạn/lỗi thời"),
    (26, 25, +0.5, "Ordering 🤝 Inventory: đặt hàng → tồn kho tăng"),
    (29, 30, +0.5, "International Freight 🤝 Packaging: hàng quốc tế cần đóng gói kỹ hơn"),
    (29, 12, +1.0, "International Freight 📈 Direct Transport: cùng nhóm vận chuyển"),
    (31, 56, +0.5, "Reverse Logistics 🤝 Waste Disposal: trả hàng → xử lý rác"),
    (27, 29, +0.5, "Shortage 🤝 Freight: thiếu hàng → phải nhập khẩn cấp (đắt)"),
    
    # --- G6: Temporal Extended ---
    (32, 35, +1.0, "Wait Time 📈 Lead Time: chờ đợi kéo dài lead time"),
    (33, 35, +0.5, "Setup Time 🤝 Lead Time: setup lâu → lead time dài"),
    (34, 35, +0.3, "Induction Time 🤝 Lead Time: thời gian khởi động tăng lead time"),
    (35, 36, +0.5, "Lead Time 🤝 PERT: lead time ảnh hưởng ước tính PERT"),
    (32, 33, +0.3, "Wait Time 🤝 Setup: chờ lâu → setup lại khi chạy"),
    
    # --- G7: Resources ---
    (37, 38, +0.5, "Request 🤝 Allocated: nhu cầu → phân bổ theo"),
    (37, 38, +0.5, "Duplicated intentionally — strong link"),  # Will use first match
    (39, 40, +0.5, "Labor Productivity 🤝 Equipment Util: năng suất người + máy tương quan"),
    (41, 8, +0.3, "Resource Substitutability 🤝 Subcontracting: có thể thay thế → dễ thuê ngoài"),
    (37, 41, -0.5, "Request ⚔️ Substitutability: nhu cầu cao → ít lựa chọn thay thế"),
    
    # --- G9: Risks ---
    (42, 43, +1.0, "Technical Complexity 📈 Rework: phức tạp → phải làm lại (PMBOK)"),
    (42, 48, +1.0, "Technical Complexity 📈 Tech Risk: phức tạp → rủi ro công nghệ"),
    (43, 45, +0.5, "Rework 🤝 Contingency: làm lại → cần dự phòng"),
    (44, 47, +0.5, "External Dependency 🤝 Weather Risk: phụ thuộc bên ngoài → rủi ro thời tiết"),
    (45, 46, +0.5, "Contingency 🤝 Management Reserve: cả hai đều là quỹ dự phòng"),
    (47, 44, +0.3, "Weather 🤝 External Dependency: thời tiết là yếu tố ngoại vi"),
    
    # --- G11: Human & Org ---
    (49, 50, +0.5, "Skill Level 🤝 Experience: kỹ năng cao thường đi kèm kinh nghiệm"),
    (50, 51, +1.0, "Experience 📈 Learning Curve: kinh nghiệm tăng → hiệu ứng học tập mạnh"),
    (52, 54, +0.5, "HR Stability Risk 🤝 Safety Risk: bất ổn nhân sự → an toàn kém"),
    (49, 53, +0.3, "Skill Level 🤝 Cross-functional: kỹ năng cao → phối hợp tốt hơn"),
    (51, 39, +0.5, "Learning Curve 🤝 Labor Productivity: học nhanh → năng suất tăng"),
    
    # --- G12: ESG ---
    (55, 56, +1.0, "Environmental Impact 📈 Waste Disposal: ô nhiễm → chi phí xử lý"),
    (55, 58, -1.0, "Environmental Impact ⚔️ Carbon Credit: ô nhiễm → mất tín chỉ carbon"),
    (57, 59, +0.5, "Social Impact 🤝 ESG Compliance: tác động xã hội → tuân thủ ESG"),
    (55, 59, +0.5, "Environmental 🤝 ESG Compliance: xả thải ảnh hưởng ESG score"),
    (56, 58, -0.5, "Waste Cost ⚔️ Carbon Credit: chi phí rác cao → mất credit"),
    
    # --- G3🤖: Opportunity Cost ---
    (60, 62, -0.5, "Flexibility ⚔️ Delay Impact: linh hoạt → ít thiệt hại khi trễ"),
    (61, 62, +0.5, "Resource Alt Cost 🤝 Delay Impact: thuê ngoài đắt → trễ càng đắt"),
    
    # --- G8🤖: Network Topology ---
    (63, 65, +0.5, "In-degree 🤝 Critical: nhiều phụ thuộc → dễ nằm Critical Path"),
    (64, 67, +0.5, "Out-degree 🤝 Path Length: nhiều 'đệ tử' → thường ở giữa đồ thị"),
    (65, 66, -1.0, "Is Critical ⚔️ Total Float: Critical ↔ Float = 0 (nghịch đảo)"),
    (66, 60, +1.0, "Total Float 📈 Schedule Flexibility: Float lớn = linh hoạt"),
    
    # --- G10🤖: Earned Value ---
    (68, 69, +0.5, "PV 🤝 EV: cả hai cùng tăng theo tiến độ"),
    (70, 71, -0.3, "CPI ⚔️ SPI: đôi khi đối nghịch (tiến nhanh nhưng đắt)"),
    (71, 69, +1.0, "SPI 📈 EV: tiến độ nhanh → EV tăng mạnh"),
    
    # =========================================================================
    # TẦNG 2: CROSS-GROUP (Feature → Group khác)
    # =========================================================================
    
    # --- Duration (Hub) → ảnh hưởng nhiều Group ---
    (1, 15, +1.0, "Duration → PM Overhead: dự án kéo dài → quản lý tốn hơn"),
    (1, 16, +1.0, "Duration → Facility Rent: dự án kéo dài → thuê VP lâu hơn"),
    (1, 17, +0.5, "Duration → Utilities: dự án dài → tiện ích tăng"),
    (1, 25, +0.5, "Duration → Inventory: dự án dài → tồn kho lâu hơn"),
    (1, 28, +0.5, "Duration → Obsolescence: dự án dài → hàng dễ lỗi thời"),
    (1, 22, +0.3, "Duration → Insurance: dự án dài → phí bảo hiểm tăng"),
    
    (3, 15, +0.5, "Days → PM Overhead: ngày làm nhiều → quản lý nặng"),
    (3, 16, +0.5, "Days → Facility: ngày nhiều → thuê VP tốn"),
    (3, 25, +0.3, "Days → Inventory: nhiều ngày → tồn kho"),
    
    # --- Calendar Type → Duration Semantics ---
    (5, 32, +0.3, "Agenda → Wait Time: lịch Agenda có thời gian nghỉ → wait time"),
    (6, 32, -0.3, "24/7 → Wait Time: lịch 24/7 giảm thời gian chờ"),
    
    # --- Direct Costs (G1) → Others ---
    (10, 25, +0.5, "Material → Inventory: mua nhiều vật liệu → tồn kho tăng"),
    (10, 29, +0.5, "Material → Freight: mua nhiều → cước vận chuyển tăng"),
    (12, 55, +1.0, "Transportation → Environmental: vận chuyển → khí thải (ESG Research)"),
    (12, 13, +1.0, "Transportation → Energy: vận chuyển → nhiên liệu"),
    (9, 52, +0.5, "Overtime → HR Stability: làm OT nhiều → nhân sự bất ổn"),
    (9, 54, +0.5, "Overtime → Safety Risk: làm OT → tai nạn lao động tăng (OSHA)"),
    (7, 19, +0.3, "Internal Labor → Training: nhân sự nội bộ cần đào tạo"),
    
    # --- Indirect Costs (G2) → Others ---
    (20, 14, +0.3, "Quality Overhead → Testing: quản lý CL → kiểm tra nhiều hơn"),
    (19, 50, +0.5, "Training → Experience: đào tạo → kinh nghiệm tăng"),
    (19, 51, +0.5, "Training → Learning Curve: đào tạo → học nhanh hơn"),
    
    # --- Contractual (G4) → Others ---
    (21, 32, +0.3, "Permits → Wait Time: chờ giấy phép → delay"),
    (24, 55, +0.3, "Regulatory → Environmental: quy định môi trường"),
    (24, 59, +0.5, "Regulatory → ESG Compliance: tuân thủ quy định = ESG"),
    
    # --- Logistics (G5) → Others ---
    (25, 16, +0.3, "Inventory → Facility: tồn kho → cần kho bãi (thuê)"),
    (27, 9, +0.5, "Shortage → Overtime: thiếu hàng → phải OT bù"),
    (27, 29, +0.5, "Shortage → Freight: thiếu → nhập khẩn cấp (đắt)"),
    (29, 55, +1.0, "Intl Freight → Environmental: vận tải quốc tế → khí thải lớn"),
    (29, 13, +1.0, "Intl Freight → Energy: freight → nhiên liệu"),
    
    # --- Temporal (G6) → Others ---
    (32, 25, +0.5, "Wait Time → Inventory: chờ lâu → tồn kho phình"),
    (32, 28, +0.5, "Wait Time → Obsolescence: chờ lâu → hàng hết hạn"),
    (35, 15, +0.5, "Lead Time → PM Overhead: lead time dài → quản lý nặng"),
    (35, 25, +0.5, "Lead Time → Inventory: lead time dài → tồn kho lâu"),
    (35, 22, +0.3, "Lead Time → Insurance: lead time dài → rủi ro → bảo hiểm"),
    (36, 45, +0.5, "PERT → Contingency: ước tính PERT → cần dự phòng tương ứng"),
    
    # --- Resources (G7) → Others ---
    (37, 7, +0.5, "Request Qty → Labor Cost: nhu cầu → chi phí nhân sự"),
    (37, 11, +0.5, "Request Qty → Equipment Cost: nhu cầu → chi phí thiết bị"),
    (37, 8, +0.3, "Request Qty → Subcontracting: nhu cầu vượt → phải thuê ngoài"),
    (39, 9, -0.5, "Labor Productivity → Overtime: năng suất cao → ít cần OT"),
    (39, 1, -0.3, "Labor Productivity → Duration: năng suất cao → rút ngắn thời gian"),
    (40, 11, -0.3, "Equipment Util → Equipment Cost: dùng hiệu quả → tiết kiệm"),
    
    # --- Risks (G9) → Others ---
    (42, 9, +0.5, "Tech Complexity → Overtime: phức tạp → cần OT để giải quyết"),
    (42, 49, +0.5, "Tech Complexity → Skill Level: phức tạp → cần kỹ năng cao"),
    (43, 1, +0.5, "Rework → Duration: làm lại → kéo dài thời gian"),
    (43, 7, +0.5, "Rework → Labor Cost: làm lại → tốn nhân công"),
    (43, 10, +0.3, "Rework → Material: làm lại → hao vật liệu"),
    (44, 35, +0.5, "External Dependency → Lead Time: phụ thuộc ngoài → lead time dài"),
    (44, 27, +0.5, "External Dependency → Shortage: phụ thuộc → dễ thiếu hàng"),
    (47, 32, +0.5, "Weather Risk → Wait Time: thời tiết xấu → phải chờ"),
    (47, 12, +0.3, "Weather Risk → Transportation: thời tiết → ảnh hưởng vận chuyển"),
    (48, 42, +0.5, "Tech Risk → Complexity: rủi ro CN → tăng phức tạp"),
    
    # --- Human/Org (G11) → Others ---
    (49, 7, +0.5, "Skill Level → Labor Cost: kỹ năng cao → lương cao"),
    (50, 39, +0.5, "Experience → Productivity: kinh nghiệm → năng suất (PMBOK)"),
    (52, 9, +0.3, "HR Instability → Overtime: nhân sự bỏ → phải OT bù"),
    (52, 8, +0.5, "HR Instability → Subcontracting: nhân sự bỏ → phải thuê ngoài"),
    (52, 43, +0.3, "HR Instability → Rework: nhân sự mới → dễ làm sai"),
    (54, 22, +0.3, "Safety Risk → Insurance: rủi ro an toàn → bảo hiểm tăng"),
    (53, 18, +0.3, "Cross-functional → Communication: phối hợp → liên lạc tăng"),
    
    # --- ESG (G12) → Others ---
    (55, 24, +0.5, "Environmental → Regulatory: ô nhiễm → tuân thủ quy định"),
    (55, 22, +0.3, "Environmental → Insurance: ô nhiễm → bảo hiểm môi trường"),
    (58, 12, -0.3, "Carbon Credit → Transportation: tín chỉ giảm → hạn chế vận chuyển"),
    (59, 21, +0.3, "ESG Compliance → Permits: ESG tốt → dễ xin giấy phép"),
    
    # --- G3🤖 → Others ---
    (60, 45, -0.3, "Flexibility → Contingency: linh hoạt → ít cần dự phòng"),
    (62, 43, +0.5, "Delay Impact → Rework: trễ hạn → áp lực làm lại"),
    (62, 9, +0.5, "Delay Impact → Overtime: trễ → buộc OT bù tiến độ"),
    (61, 8, +0.5, "Resource Alt Cost → Subcontracting: chi phí thay thế = giá thuê ngoài"),
    
    # --- G8🤖 → Others ---
    (63, 44, +0.5, "In-degree → External Dependency: nhiều predecessor → phụ thuộc cao"),
    (64, 62, +1.0, "Out-degree → Delay Impact: nhiều successor → thiệt hại trễ lan rộng"),
    (65, 43, +0.5, "Is Critical → Rework Prob: critical → áp lực → dễ sai"),
    (65, 45, +0.5, "Is Critical → Contingency: critical → cần dự phòng nhiều"),
    (65, 9, +0.5, "Is Critical → Overtime: critical → phải OT giữ tiến độ"),
    (66, 60, +1.0, "Float → Flexibility: float = linh hoạt"),
    (67, 62, +0.5, "Path Length → Delay Impact: gần đích → thiệt hại trễ lớn hơn"),
    
    # --- G10🤖 → Others ---
    (70, 45, -0.3, "CPI Good → Contingency: chi phí hiệu quả → ít cần dự phòng"),
    (71, 9, -0.3, "SPI Good → Overtime: tiến độ tốt → ít cần OT"),
    (71, 62, -0.5, "SPI Good → Delay Impact: tiến độ tốt → ít thiệt hại trễ"),
    (70, 46, -0.3, "CPI Good → Management Reserve: CPI tốt → ít cần quỹ quản lý"),
]


def build_sparse_matrix(interactions, size=72):
    """
    Mô tả (Description):
        Xây dựng Ma trận thưa (Sparse Matrix) kích thước 72x72 từ danh sách cấu hình.
        Đây là bước Số hóa "Cuốn Từ Điển PMBOK" để nạp vào PyTorch.
        
    Đầu vào (Args):
        interactions (list): Danh sách các bộ Tuple (index_nguồn, index_đích, giá_trị, ghi_chú).
        size (int): Kích thước ma trận vuông (mặc định 72).
        
    Đầu ra (Returns):
        matrix (np.ndarray): Ma trận Numpy 2D chứa các giá trị trọng số tương tác.
    """
    import numpy as np
    matrix = np.zeros((size, size), dtype=np.float32)
    
    # Diagonal = 1 (self-interaction)
    np.fill_diagonal(matrix, 1.0)
    
    for src, tgt, val, _ in interactions:
        if 0 <= src < size and 0 <= tgt < size:
            matrix[src][tgt] = val
            # Ma trận đối xứng (symmetric) cho Tầng 1 intra-group
            # Không đối xứng cho Tầng 2 cross-group (có hướng)
    
    return matrix


def get_interaction_stats(interactions):
    """
    Mô tả (Description):
        Hàm tiện ích để thống kê tổng quan về Ma trận Tương tác (Domain Knowledge).
        Đếm số lượng các mối quan hệ tích cực (Khuếch đại) và tiêu cực (Đối kháng).
        
    Đầu vào (Args):
        interactions (list): Danh sách các bộ Tuple tương tác.
        
    Đầu ra (Returns):
        dict: Từ điển chứa các con số thống kê (Tổng số, Số quan hệ dương, Số quan hệ âm, Độ thưa...).
    """
    total = len(interactions)
    positive = sum(1 for _, _, v, _ in interactions if v > 0)
    negative = sum(1 for _, _, v, _ in interactions if v < 0)
    strong = sum(1 for _, _, v, _ in interactions if abs(v) >= 1.0)
    
    return {
        "total_interactions": total,
        "positive (amplify/complement)": positive,
        "negative (compete/offset)": negative,
        "strong (|v| >= 1.0)": strong,
        "sparsity": f"{(1 - total / (72*72)) * 100:.1f}%"
    }


if __name__ == "__main__":
    stats = get_interaction_stats(INTERACTIONS)
    print("=== MA TRẬN TƯƠNG TÁC 72×72 - THỐNG KÊ ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    matrix = build_sparse_matrix(INTERACTIONS)
    non_zero = (matrix != 0).sum() - 72  # Trừ diagonal
    print(f"\n  Non-zero cells (excl diagonal): {non_zero}")
    print(f"  Matrix shape: {matrix.shape}")
