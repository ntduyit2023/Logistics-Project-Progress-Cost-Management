"""
Dữ liệu Case Study PPC 2010 - Bảng 1, 2, 5, 6, 7
=====================================================
Tất cả dữ liệu từ bài tập tình huống cuối kỳ của 
Đại học South Australia (MFET 3008/MFET 5040).

Dự án: Thiết kế, chế tạo và vận hành hệ thống cơ sở dữ liệu, 
lưu trữ và vận chuyển bưu kiện tự động.
"""


# ====================================================================
# BẢNG 1: Danh sách công việc dự án (Project Tasks)
# ====================================================================
# Mỗi task: id, name, duration, predecessors, resources
TASKS = [
    {
        'id': 'A', 'name': 'Quyết định kiến trúc',
        'duration': 4,
        'resources': ['Design(Comp)', 'Design(Mech)']
    },
    {
        'id': 'B', 'name': 'Đặc tả phần cứng',
        'duration': 6,
        'resources': ['Design(Comp)', 'Design(Mech)', 'Dev(Mech)', 'Assm(Mech)']
    },
    {
        'id': 'C', 'name': 'Đặc tả phần mềm',
        'duration': 7,
        'resources': ['Design(Comp)', 'Dev(Comp)', 'Assm(Comp)']
    },
    {
        'id': 'D', 'name': 'Thiết kế băng chuyền',
        'duration': 8,
        'resources': ['Design(Mech)', 'Dev(Mech)']
    },
    {
        'id': 'E', 'name': 'Thiết kế phần cứng',
        'duration': 6,
        'resources': ['Design(Comp)', 'Design(Mech)', 'Dev(Mech)']
    },
    {
        'id': 'F', 'name': 'Thiết kế phần mềm',
        'duration': 12,
        'resources': ['Design(Comp)', 'Dev(Comp)']
    },
    {
        'id': 'G', 'name': 'Tài liệu hệ điều hành',
        'duration': 10,
        'resources': ['Dev(Comp)', 'Documentation']
    },
    {
        'id': 'H', 'name': 'Bản vẽ phần cứng chi tiết',
        'duration': 8,
        'resources': ['Dev(Comp)', 'Dev(Mech)', 'Documentation']
    },
    {
        'id': 'I', 'name': 'Lập trình phần mềm',
        'duration': 16,
        'resources': ['Design(Comp)', 'Documentation']
    },
    {
        'id': 'J', 'name': 'Xác minh/kiểm thử phần mềm',
        'duration': 12,
        'resources': ['Dev(Comp)', 'Assm(Comp)', 'Documentation']
    },
    {
        'id': 'K', 'name': 'Bản vẽ băng chuyền chi tiết',
        'duration': 7,
        'resources': ['Dev(Comp)', 'Dev(Mech)', 'Documentation']
    },
    {
        'id': 'L', 'name': 'Tích hợp nhỏ/Kiểm tra bản vẽ',
        'duration': 9,
        'resources': ['Dev(Comp)', 'Assm(Comp)', 'Assm(Mech)']
    },
    {
        'id': 'M', 'name': 'Phát triển nguyên mẫu',
        'duration': 4,
        'resources': ['Dev(Comp)', 'Dev(Mech)']
    },
    {
        'id': 'N', 'name': 'Cài đặt nguyên mẫu',
        'duration': 7,
        'resources': ['Assm(Comp)', 'Assm(Mech)']
    },
    {
        'id': 'O', 'name': 'Đặt hàng/Giao phần cứng',
        'duration': 7,
        'resources': ['Dev(Mech)', 'Purchase']
    },
    {
        'id': 'P', 'name': 'Giao diện hệ thống',
        'duration': 5,
        'resources': ['Dev(Mech)', 'Assm(Mech)']
    },
    {
        'id': 'Q', 'name': 'Lắp ráp phần cứng',
        'duration': 4,
        'resources': ['Assm(Comp)', 'Assm(Mech)']
    },
    {
        'id': 'R', 'name': 'Tích hợp phần cứng/phần mềm',
        'duration': 5,
        'resources': ['Dev(Comp)', 'Dev(Mech)', 'Assm(Comp)', 'Assm(Mech)']
    },
    {
        'id': 'S', 'name': 'Tài liệu phần cứng/phần mềm',
        'duration': 2,
        'resources': ['Dev(Comp)', 'Dev(Mech)', 'Documentation']
    },
    {
        'id': 'T', 'name': 'Xác minh hệ thống',
        'duration': 3,
        'resources': ['Dev(Mech)', 'Assm(Comp)', 'Assm(Mech)']
    },
    {
        'id': 'U', 'name': 'Kiểm tra nghiệm thu',
        'duration': 2,
        'resources': ['Assm(Comp)', 'Assm(Mech)']
    },
]


# ====================================================================
# Quan hệ phụ thuộc (Precedence / Dependencies)
# ====================================================================
DEPENDENCIES = [
    ('A', 'B'),    # B phụ thuộc A
    ('A', 'C'),    # C phụ thuộc A
    ('B', 'D'),    # D phụ thuộc B
    ('B', 'E'),    # E phụ thuộc B
    ('C', 'F'),    # F phụ thuộc C
    ('C', 'G'),    # G phụ thuộc C
    ('E', 'H'),    # H phụ thuộc E, F
    ('F', 'H'),
    ('G', 'I'),    # I phụ thuộc G
    ('I', 'J'),    # J phụ thuộc I
    ('D', 'K'),    # K phụ thuộc D
    ('H', 'L'),    # L phụ thuộc H, K
    ('K', 'L'),
    ('H', 'M'),    # M phụ thuộc H
    ('J', 'N'),    # N phụ thuộc J, M
    ('M', 'N'),
    ('L', 'O'),    # O phụ thuộc L
    ('L', 'P'),    # P phụ thuộc L
    ('O', 'Q'),    # Q phụ thuộc O, P
    ('P', 'Q'),
    ('N', 'R'),    # R phụ thuộc N, Q
    ('Q', 'R'),
    ('R', 'S'),    # S phụ thuộc R
    ('R', 'T'),    # T phụ thuộc R
    ('S', 'U'),    # U phụ thuộc S, T
    ('T', 'U'),
]


# ====================================================================
# BẢNG 2: Chi phí nhân sự (Resource Costs & Capacities)
# ====================================================================
RESOURCE_COSTS = {
    'Design(Comp)': 200,    # $200/ngày
    'Design(Mech)': 200,    # $200/ngày
    'Dev(Comp)': 150,       # $150/ngày
    'Dev(Mech)': 150,       # $150/ngày
    'Assm(Comp)': 100,      # $100/ngày
    'Assm(Mech)': 100,      # $100/ngày
    'Purchase': 80,         # $80/ngày
    'Documentation': 80,    # $80/ngày
}

RESOURCE_CAPACITIES = {
    'Design(Comp)': 1,
    'Design(Mech)': 1,
    'Dev(Comp)': 2,
    'Dev(Mech)': 1,
    'Assm(Comp)': 1,
    'Assm(Mech)': 1,
    'Purchase': 1,
    'Documentation': 2,
}


# ====================================================================
# BẢNG 6: Penalty / Bonus / Overhead
# ====================================================================
PENALTY_PER_WEEK = 2000     # $2,000 mỗi tuần trễ sau tuần 12
BONUS_PER_WEEK = 3000       # $3,000 mỗi tuần sớm trước tuần 12
OVERHEAD_PER_WEEK = 500     # $500/tuần chi phí gián tiếp
BASELINE_WEEKS = 12         # Mốc tuần chuẩn


# ====================================================================
# BẢNG 7: Dữ liệu kiểm soát cuối tuần 5 (cho EVA - Q7)
# ====================================================================
# actual_cost: Chi phí thực tế đã chi ($)
# percent_complete: % hoàn thành thực tế
EVA_ACTUAL_DATA_WEEK5 = {
    'A': {'actual_cost': 2400, 'percent_complete': 100},
    'B': {'actual_cost': 6500, 'percent_complete': 100},
    'C': {'actual_cost': 4300, 'percent_complete': 100},
    'D': {'actual_cost': 3500, 'percent_complete': 100},
    'E': {'actual_cost': 6100, 'percent_complete': 100},
    'F': {'actual_cost': 8500, 'percent_complete': 50},
    'G': {'actual_cost': 2100, 'percent_complete': 100},
    'H': {'actual_cost': 2000, 'percent_complete': 10},
    'I': {'actual_cost': 5300, 'percent_complete': 20},
    'K': {'actual_cost': 3200, 'percent_complete': 80},
}

# Time Now = cuối tuần 5 = ngày 25 (5 tuần × 5 ngày/tuần)
TIME_NOW_WEEK5 = 25


# ====================================================================
# KẾT QUẢ THAM CHIẾU (hand-calculated) từ Case Study
# ====================================================================
EXPECTED_RESULTS = {
    'project_duration': 66,         # Gợi ý Q2: 66 ngày
    'total_labor_cost': 49510,      # Gợi ý Q3c: $49,510

    # Kết quả CPM mong đợi (đã xác minh bằng thuật toán)
    # Format: task_id -> (ES, EF, LS, LF, Total_Slack, Free_Slack)
    # Đường găng: A → C → G → I → J → N → R → T → U (tổng = 66 ngày)
    'cpm_results': {
        'A': (0, 4, 0, 4, 0, 0),       # Critical
        'B': (4, 10, 15, 21, 11, 0),
        'C': (4, 11, 4, 11, 0, 0),      # Critical
        'D': (10, 18, 21, 29, 11, 0),
        'E': (10, 16, 22, 28, 12, 7),
        'F': (11, 23, 16, 28, 5, 0),
        'G': (11, 21, 11, 21, 0, 0),    # Critical
        'H': (23, 31, 28, 36, 5, 0),
        'I': (21, 37, 21, 37, 0, 0),    # Critical
        'J': (37, 49, 37, 49, 0, 0),    # Critical
        'K': (18, 25, 29, 36, 11, 6),
        'L': (31, 40, 36, 45, 5, 0),
        'M': (31, 35, 45, 49, 14, 14),
        'N': (49, 56, 49, 56, 0, 0),    # Critical
        'O': (40, 47, 45, 52, 5, 0),
        'P': (40, 45, 47, 52, 7, 2),
        'Q': (47, 51, 52, 56, 5, 5),
        'R': (56, 61, 56, 61, 0, 0),    # Critical
        'S': (61, 63, 62, 64, 1, 1),
        'T': (61, 64, 61, 64, 0, 0),    # Critical
        'U': (64, 66, 64, 66, 0, 0),    # Critical
    },

    # Đường găng (Critical Path): A → C → G → I → J → N → R → T → U
    'critical_path': ['A', 'C', 'G', 'I', 'J', 'N', 'R', 'T', 'U'],

    # Q5: Resource-constrained duration
    'resource_constrained_duration': 96,    # Gợi ý: 96 ngày

    # Q6b: Crashing to 13 weeks
    'crash_cost_13_weeks': 70345,    # Gợi ý: $70,345 cho tuần 13

    # Q6a: Full outsourcing cost
    'outsourcing_total': 70230,      # Gợi ý: $70,230
}
