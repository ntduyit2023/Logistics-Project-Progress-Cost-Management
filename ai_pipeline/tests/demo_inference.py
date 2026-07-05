import os
import sys
import torch
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

# Dynamic path resolution to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.data_loader import GlPoDataset
from ai_pipeline.envs.logistics_gym_env import create_env_from_project_graph
from ai_pipeline.training.ppo_trainer import ActorCritic, flatten_obs, RunningMeanStd

# 1. Đường dẫn các tệp tin
processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
checkpoint_path = os.path.join(project_root, 'ai_pipeline', 'checkpoints', 'ppo_final.pt')

if not os.path.exists(checkpoint_path):
    checkpoint_path = os.path.join(project_root, 'ai_pipeline', 'checkpoints', 'ppo_best.pt')

print(f"📂 Đang đọc dữ liệu từ: {processed_dir}")
dataset = GlPoDataset(processed_dir)

# Chọn dự án nhỏ nhất để demo trực quan: C2019-16 (32 tasks)
demo_project_id = "C2019-16"
project_graph = None
for pg in dataset.graphs:
    if pg.project_id == demo_project_id:
        project_graph = pg
        break

if project_graph is None:
    print(f"❌ Không tìm thấy dự án {demo_project_id}. Chọn dự án đầu tiên thay thế.")
    project_graph = dataset.graphs[0]
    demo_project_id = project_graph.project_id

print(f"🎯 Đang chạy thử nghiệm Agent trên Dự án: {demo_project_id} ({project_graph.data.num_nodes} tasks)")

# 2. Khởi tạo Môi trường
env = create_env_from_project_graph(project_graph)
obs_dim = 86
action_dim = 3

# 3. Khởi tạo Agent & Nạp Checkpoint
agent = ActorCritic(obs_dim=obs_dim, action_dim=action_dim)
checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'), weights_only=False)
agent.load_state_dict(checkpoint['agent_state_dict'])
agent.eval()

# Nạp Running Mean/Std để chuẩn hóa dữ liệu quan sát đầu vào
obs_normalizer = RunningMeanStd(shape=(obs_dim,))
if 'obs_normalizer' in checkpoint:
    norm_data = checkpoint['obs_normalizer']
    obs_normalizer.mean = norm_data['mean']
    obs_normalizer.var = norm_data['var']
    obs_normalizer.count = norm_data['count']

print(f"✅ Đã nạp checkpoint thành công!")
print("-" * 80)

# 4. Chạy mô phỏng step-by-step
obs_dict, info = env.reset()
done = False
step = 0
total_reward = 0.0

action_names = {0: "Normal (Chạy bình thường)", 1: "Crash (Tăng ca đẩy nhanh)", 2: "Outsource (Thuê ngoài)"}

print(f"| {'Bước':<5} | {'Mã Task':<8} | {'Hành động được chọn':<28} | {'Điểm thưởng':<12} | {'Makespan hiện tại':<18} |")
print(f"|{'-'*7}|{'-'*10}|{'-'*30}|{'-'*14}|{'-'*20}|")

while not done:
    step += 1
    task_idx = env._topo_order[env._state['current_topo_idx']]
    task_id_str = project_graph.idx_to_node[task_idx]
    
    # Chuẩn hóa quan sát đầu vào
    obs_flat = flatten_obs(obs_dict)
    obs_norm = obs_normalizer.normalize(obs_flat)
    obs_tensor = torch.tensor(obs_norm, dtype=torch.float32).unsqueeze(0)
    
    # Lấy mặt nạ hành động hợp lệ
    mask = env.action_masks()
    mask_tensor = torch.tensor(mask, dtype=torch.bool).unsqueeze(0)
    
    # Actor ra quyết định (chọn hành động có xác suất cao nhất)
    with torch.no_grad():
        dist, _ = agent(obs_tensor, mask_tensor)
        action = dist.probs.argmax(dim=-1).item()
        
    # Thực hiện hành động trong môi trường
    next_obs_dict, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
    total_reward += reward
    
    # In thông tin của bước này
    print(f"| {step:<5} | {task_id_str:<8} | {action_names[action]:<28} | {reward:<12.2f} | {info['makespan']:<13.1f} giờ |")
    
    obs_dict = next_obs_dict

print("-" * 80)
print(f"🏆 HUẤN LUYỆN ĐÁNH GIÁ KẾT THÚC:")
print(f"   • Tổng số bước đã lập lịch: {step} tasks")
print(f"   • Tổng điểm thưởng của Episode: {total_reward:.2f}")
print(f"   • Tổng chi phí quy đổi (TGC) cuối cùng: {info['cumulative_tgc']:.2f}")
print(f"   • Thời lượng dự án (Makespan) cuối cùng: {info['makespan']:.1f} giờ (Deadline: {env._global_constraints.get('deadline'):.1f} giờ)")
print(f"   • Các chế độ được gán: {info['modes_assigned']}")
