"""
Mô-đun PERT (Program Evaluation and Review Technique)
======================================================
Mô-đun này triển khai phương pháp ước lượng 3 điểm cổ điển.
Nó tính toán thời lượng kỳ vọng và phương sai cho từng task riêng lẻ,
xác định giá trị trung bình và phương sai toàn dự án dựa trên đường găng,
và tính toán xác suất hoàn thành dự án trước một thời hạn (deadline) được chỉ định.
"""

import math
from typing import Dict, List, Tuple, Any

def calculate_task_pert(
    optimistic: float,
    most_likely: float,
    pessimistic: float
) -> Tuple[float, float]:
    """
    Tính toán thời lượng kỳ vọng và phương sai cho một task duy nhất bằng công thức PERT.

    Công thức:
        Thời lượng kỳ vọng (te) = (O + 4M + P) / 6
        Phương sai (v) = ((P - O) / 6)^2

    Args:
        optimistic (O): Thời lượng trong trường hợp thuận lợi nhất (lạc quan)
        most_likely (M): Thời lượng khả thi nhất (thường gặp)
        pessimistic (P): Thời lượng trong trường hợp khó khăn nhất (bi quan)

    Returns:
        Tuple gồm (thời_lượng_kỳ_vọng, phương_sai)
    """
    if not (optimistic <= most_likely <= pessimistic):
        raise ValueError(
            f"Các giá trị ước lượng PERT không hợp lệ: phải thỏa mãn lạc quan ({optimistic}) <= "
            f"khả thi nhất ({most_likely}) <= bi quan ({pessimistic})"
        )
    
    expected_duration = (optimistic + 4 * most_likely + pessimistic) / 6.0
    variance = ((pessimistic - optimistic) / 6.0) ** 2
    return expected_duration, variance

def calculate_project_pert(
    tasks: List[Dict[str, Any]],
    critical_path: List[Any]
) -> Tuple[float, float]:
    """
    Tính toán tổng thời lượng kỳ vọng và phương sai của toàn bộ dự án
    bằng cách cộng dồn các giá trị dọc theo đường găng (giả định các công việc độc lập).

    Args:
        tasks: Danh sách các dict của task, mỗi dict chứa ít nhất:
            - 'id': ID duy nhất của task
            - 'optimistic_time': Ước lượng thời gian lạc quan
            - 'pessimistic_time': Ước lượng thời gian bi quan
            - 'duration': Ước lượng thời gian khả thi nhất (thời lượng cơ sở)
        critical_path: Danh sách các ID công việc nằm trên đường găng

    Returns:
        Tuple gồm (tổng_thời_lượng_kỳ_vọng_dự_án, tổng_phương_sai_dự_án)
    """
    # Tạo bản đồ ánh xạ để tìm kiếm task nhanh chóng
    task_map = {t['id']: t for t in tasks}
    
    total_expected = 0.0
    total_variance = 0.0
    
    for task_id in critical_path:
        if task_id not in task_map:
            raise ValueError(f"Task ID '{task_id}' trên đường găng không được tìm thấy trong danh sách công việc.")
        
        task = task_map[task_id]
        
        # Đọc các ước lượng 3 điểm một cách linh hoạt
        m = float(task.get('most_probable_duration', task.get('duration', 0.0)))
        o = float(task.get('optimistic_duration', task.get('optimistic_time', m)))
        p = float(task.get('pessimistic_duration', task.get('pessimistic_time', m)))
        
        te, v = calculate_task_pert(o, m, p)
        
        total_expected += te
        total_variance += v
        
    return total_expected, total_variance

def calculate_completion_probability(
    expected_duration: float,
    variance: float,
    deadline: float
) -> float:
    """
    Tính toán xác suất hoàn thành dự án trước thời hạn (deadline)
    bằng cách sử dụng Hàm Phân Phối Tích Lũy Chuẩn (Normal CDF).

    Công thức:
        Z = (deadline - expected_duration) / sqrt(variance)
        P(T <= deadline) = Phi(Z)

    Args:
        expected_duration: Tổng thời lượng kỳ vọng của các task trên đường găng
        variance: Tổng phương sai của các task trên đường găng
        deadline: Thời hạn hoàn thành mục tiêu của dự án

    Returns:
        float: Xác suất hoàn thành, nằm trong khoảng [0.0, 1.0]
    """
    if variance <= 0:
        return 1.0 if expected_duration <= deadline else 0.0
        
    std_dev = math.sqrt(variance)
    z = (deadline - expected_duration) / std_dev
    
    # Tính Normal CDF bằng math.erf (thư viện chuẩn, không cần scipy)
    # Phi(z) = 0.5 * (1 + erf(z / sqrt(2)))
    probability = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return probability
