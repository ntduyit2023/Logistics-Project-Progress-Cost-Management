"""
Package Thuật Toán Cốt Lõi GLPO
================================
Package này chứa các thuật toán lập lịch và tối ưu hóa chính:
    - cpm: Phương pháp Đường Găng tĩnh (CPM)
    - pert: Lập lịch xác suất dựa trên ước lượng 3 điểm (PERT)
    - monte_carlo: Mô phỏng xác suất dưới tác động của sự bất định dự báo bởi GNN (Cấp độ 2)
    - nsga2: Tối ưu hóa tiến độ đa mục tiêu (NSGA-II) (Thời gian - Chi phí - Rủi ro)
    - cpsat_solver: Lập lịch gán tài nguyên ràng buộc (RCPSP) bằng Google OR-Tools CP-SAT
"""
from ai_pipeline.src.algorithms.cpm import build_project_graph, calculate_cpm, get_critical_path, get_cpm_summary
from ai_pipeline.src.algorithms.pert import calculate_task_pert, calculate_project_pert, calculate_completion_probability
from ai_pipeline.src.algorithms.monte_carlo import run_monte_carlo_simulation
from ai_pipeline.src.algorithms.nsga2 import run_nsga2_optimization
from ai_pipeline.src.algorithms.cpsat_solver import run_cpsat_scheduling