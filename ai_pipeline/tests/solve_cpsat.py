import os
import sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

# Dynamic path resolution to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Thử import ortools. Nếu chưa cài đặt, tự động cài đặt qua pip.
try:
    from ortools.sat.python import cp_model
except ImportError:
    print("📦 Không tìm thấy thư viện ortools. Đang tự động cài đặt...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ortools"])
    from ortools.sat.python import cp_model

from ai_pipeline.models.data_loader import GlPoDataset
from ai_pipeline.envs.logistics_gym_env import create_env_from_project_graph

# 1. Nạp dữ liệu dự án C2019-16 (32 tasks)
processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
dataset = GlPoDataset(processed_dir)

demo_project_id = "C2019-16"
project_graph = None
for pg in dataset.graphs:
    if pg.project_id == demo_project_id:
        project_graph = pg
        break

if project_graph is None:
    print(f"❌ Không tìm thấy dự án {demo_project_id}.")
    sys.exit(1)

# 2. Thu thập thông tin từ môi trường Gym để xây dựng mô hình CP-SAT tương đương
env = create_env_from_project_graph(project_graph)
num_tasks = len(project_graph.idx_to_node)
topo_order = env._topo_order

# Lấy các thông số cơ bản
base_durations = env._base_durations.copy()
predecessors = env._adj_backward
successors = env._adj_forward
deadline = env._global_constraints.get('deadline', 1e9)

# 3. Tính toán chi phí trực tiếp cho từng mode của mỗi task
# Ta quy đổi về số nguyên (nhân với 100) vì CP-SAT chỉ làm việc với số nguyên
SCALE = 100

durations_matrix = np.zeros((num_tasks, 3), dtype=np.int32)
costs_matrix = np.zeros((num_tasks, 3), dtype=np.int32)

for i in range(num_tasks):
    d = float(base_durations[i])
    # Tính thời lượng tương ứng với từng chế độ
    durations_matrix[i, 0] = int(round(d))
    durations_matrix[i, 1] = int(round(d / 1.5))
    durations_matrix[i, 2] = int(round(d / 2.0))
    
    # Tính chi phí trực tiếp tương ứng (được rút trích từ đặc trưng 7-14 của task)
    features_i = env._original_features[i]
    c_direct_base = float(np.sum(features_i[7:15]))
    
    cost_normal = c_direct_base
    cost_crash = c_direct_base * 1.5
    cost_outsource = c_direct_base + d * 10.0
    
    costs_matrix[i, 0] = int(round(cost_normal * SCALE))
    costs_matrix[i, 1] = int(round(cost_crash * SCALE))
    costs_matrix[i, 2] = int(round(cost_outsource * SCALE))

# 4. Xây dựng mô hình CP-SAT
model = cp_model.CpModel()

# Định nghĩa các biến quyết định
# x[i][m] = 1 nếu task i chọn mode m (0: Normal, 1: Crash, 2: Outsource)
x = {}
for i in range(num_tasks):
    for m in range(3):
        x[i, m] = model.NewBoolVar(f"x_{i}_{m}")

# Biến thời gian bắt đầu, thời lượng và thời gian kết thúc của từng task
start = []
duration = []
end = []
interval = []

for i in range(num_tasks):
    # Thời gian bắt đầu tối đa bằng deadline
    s_var = model.NewIntVar(0, int(deadline), f"start_{i}")
    d_var = model.NewIntVar(0, int(base_durations[i]), f"duration_{i}")
    e_var = model.NewIntVar(0, int(deadline), f"end_{i}")
    
    # Liên kết interval variable
    i_var = model.NewIntervalVar(s_var, d_var, e_var, f"interval_{i}")
    
    start.append(s_var)
    duration.append(d_var)
    end.append(e_var)
    interval.append(i_var)

# Ràng buộc: Mỗi task chỉ được chọn duy nhất 1 chế độ hoạt động
for i in range(num_tasks):
    model.Add(sum(x[i, m] for m in range(3)) == 1)
    
    # Liên kết thời lượng với chế độ được chọn
    model.Add(duration[i] == sum(durations_matrix[i, m] * x[i, m] for m in range(3)))

# Ràng buộc: Quan hệ phụ thuộc (Precedence Constraints)
for u in range(num_tasks):
    for v in successors.get(u, []):
        model.Add(start[v] >= end[u])

# Biến Makespan (Thời điểm kết thúc dự án)
makespan = model.NewIntVar(0, int(deadline), "makespan")
for i in range(num_tasks):
    model.Add(makespan >= end[i])

# Giới hạn Makespan không vượt quá deadline dự án
model.Add(makespan <= int(deadline))

# Mục tiêu tối ưu hóa tuyến tính hóa:
# Minimize: Tổng chi phí trực tiếp + Makespan * (hệ số quy đổi PM Overhead ước lượng là 0.1)
PM_coef = int(0.1 * SCALE)
total_cost_expr = sum(costs_matrix[i, m] * x[i, m] for i in range(num_tasks) for m in range(3)) + makespan * PM_coef
model.Minimize(total_cost_expr)

# 5. Giải mô hình CP-SAT
print("🚀 Đang khởi động Google OR-Tools CP-SAT solver...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10.0  # Giới hạn 10s
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print(f"✅ CP-SAT Solver đã tìm thấy lời giải ({solver.StatusName(status)})!")
    
    # Trích xuất chế độ chạy tối ưu từ lời giải CP-SAT
    modes_assigned = []
    for i in range(num_tasks):
        selected_mode = -1
        for m in range(3):
            if solver.Value(x[i, m]) == 1:
                selected_mode = m
                break
        modes_assigned.append(selected_mode)
        
    print(f"🎯 Lập lịch các chế độ của CP-SAT: {modes_assigned}")
    
    # 6. Đưa lời giải CP-SAT vào môi trường LogisticsGymEnv thực tế để đánh giá công bằng
    obs_dict, info = env.reset()
    done = False
    step = 0
    total_reward = 0.0
    
    while not done:
        action = modes_assigned[step]
        obs_dict, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        total_reward += reward
        step += 1
        
    print("-" * 80)
    print("🏆 KẾT QUẢ SO SÁNH GIỮA CP-SAT VÀ PPO AGENT TRÊN MÔI TRƯỜNG THỰC TẾ:")
    print(f"   • CP-SAT Solver - Tổng chi phí TGC: {info['cumulative_tgc']:.2f}")
    print(f"   • CP-SAT Solver - Makespan: {info['makespan']:.1f} giờ")
    print(f"   • CP-SAT Solver - Điểm thưởng (Reward): {total_reward:.2f}")
    print("-" * 80)
    
else:
    print("❌ CP-SAT Solver không tìm thấy lời giải hợp lệ.")
