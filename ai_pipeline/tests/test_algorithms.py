import os
import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

# Dynamic path resolution to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.src.algorithms.cpm import build_project_graph, calculate_cpm, get_critical_path
from ai_pipeline.src.algorithms.pert import calculate_project_pert, calculate_completion_probability
from ai_pipeline.src.algorithms.monte_carlo import run_monte_carlo_simulation
from ai_pipeline.src.algorithms.nsga2 import run_nsga2_optimization
from ai_pipeline.src.algorithms.cpsat_solver import run_cpsat_scheduling

def main():
    project_dir = os.path.join(project_root, "ai_pipeline", "data", "processed", "C2011-07")
    print(f"=== Đang nạp dữ liệu cho dự án: {os.path.basename(project_dir)} ===")
    
    # 1. Đọc dữ liệu từ CSV
    tasks_df = pd.read_csv(os.path.join(project_dir, 'tasks.csv'))
    edges_df = pd.read_csv(os.path.join(project_dir, 'predecessors.csv'))
    
    # Chuyển đổi sang định dạng đầu vào của thuật toán
    tasks = tasks_df.to_dict(orient='records')
    
    dependencies = []
    for _, row in edges_df.iterrows():
        pred = str(row['predecessor_task_id'])
        succ = str(row['successor_task_id'])
        dependencies.append((pred, succ))
        
    print(f"Nạp thành công {len(tasks)} tasks và {len(dependencies)} cạnh phụ thuộc.")
    
    # === TEST 1: CPM ===
    print("\n--- [TEST 1] Chạy CPM ---")
    G = build_project_graph(tasks, dependencies)
    G_cpm, project_duration = calculate_cpm(G)
    crit_path = get_critical_path(G_cpm)
    print(f" makespan của CPM tĩnh: {project_duration:.2f} giờ")
    print(f" Đường găng ({len(crit_path)} tasks): {crit_path}")
    
    # === TEST 2: PERT ===
    print("\n--- [TEST 2] Chạy PERT ---")
    te_project, var_project = calculate_project_pert(tasks, crit_path)
    std_project = np.sqrt(var_project)
    print(f" Kéo dài dự kiến (expected makespan): {te_project:.2f} giờ")
    print(f" Độ lệch chuẩn của đường găng: {std_project:.2f} giờ")
    
    # Tính thử xác suất đúng hạn với deadline = te_project + 10%
    deadline = te_project * 1.1
    prob = calculate_completion_probability(te_project, var_project, deadline)
    print(f" Xác suất đúng hạn lý thuyết trước {deadline:.2f}h: {prob*100:.2f}%")
    
    # === TEST 3: MONTE CARLO ===
    print("\n--- [TEST 3] Chạy Monte Carlo (Cấp độ 2) ---")
    # Giả lập điểm chú ý của GAT cho một số task trên đường găng
    dummy_attn = {node: 0.5 for node in crit_path[:3]}
    
    mc_res = run_monte_carlo_simulation(
        tasks=tasks,
        dependencies=dependencies,
        attention_score=dummy_attn,
        gamma=1.5,
        num_iterations=1000, # Chạy 1000 lần để test nhanh
        deadline=deadline
    )
    print(f" Mean makespan Monte Carlo: {mc_res['mean_makespan']:.2f} giờ")
    print(f" Std makespan Monte Carlo: {mc_res['std_makespan']:.2f} giờ")
    print(f" Xác suất đúng hạn Monte Carlo P(on_time): {mc_res['P(on_time)']*100:.2f}%")
    print(f" Phân vị P90 của Monte Carlo: {mc_res['percentiles']['P90']:.2f} giờ")
    
    # === TEST 4: NSGA-II ===
    print("\n--- [TEST 4] Chạy NSGA-II ---")
    # Lấy chỉ số găng từ Monte Carlo làm đầu vào cho NSGA-II
    crit_indices = mc_res['criticality_indices']
    
    res_nsga2 = run_nsga2_optimization(
        tasks=tasks,
        dependencies=dependencies,
        criticality_indices=crit_indices,
        pop_size=20,
        n_generations=10
    )
    print(f" Số lượng phương án tối ưu Pareto tìm được: {len(res_nsga2)}")
    if len(res_nsga2) > 0:
        first_opt = res_nsga2[0]
        print(f" Phương án Pareto đầu tiên: Makespan={first_opt['makespan']:.2f}h, Cost={first_opt['cost']:.2f}, Risk={first_opt['risk']:.4f}")
        print(f" Cấu hình thực thi các task: {first_opt['modes'][:5]}... (5 task đầu)")
        
    # === TEST 5: CP-SAT ===
    print("\n--- [TEST 5] Chạy CP-SAT (Google OR-Tools) ---")
    # Lấy tài nguyên khả dụng từ file resources.csv
    res_df = pd.read_csv(os.path.join(project_dir, 'resources.csv'))
    resource_capacities = {}
    for _, row in res_df.iterrows():
        r_id = str(row['ID'])
        r_cap = float(row.get('Availability', 1.0))
        resource_capacities[r_id] = r_cap
        
    # Thêm tài nguyên yêu cầu ngẫu nhiên làm giả lập để test bộ giải ràng buộc
    # vì mặc định tasks.csv có thể chưa gán tài nguyên thô
    task_res_df = pd.read_csv(os.path.join(project_dir, 'task_resources.csv'))
    for t in tasks:
        t_id = t['id']
        t_req = task_res_df[task_res_df['task_id'] == t_id]
        t['resource_demand'] = {str(row['resource_id']): int(row['request_quantity']) for _, row in t_req.iterrows()}
        
    cpsat_res = run_cpsat_scheduling(
        tasks=tasks,
        dependencies=dependencies,
        resource_capacities=resource_capacities,
        time_limit_sec=5.0
    )
    print(f" Trạng thái bộ giải CP-SAT: {cpsat_res['status']}")
    print(f" Makespan tối ưu tìm được: {cpsat_res['makespan']} giờ")
    if cpsat_res['schedule']:
        print(f" Lịch trình bắt đầu một số task: {list(cpsat_res['schedule'].items())[:3]}")

if __name__ == "__main__":
    main()
