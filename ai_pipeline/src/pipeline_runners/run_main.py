import os
import sys
import argparse
import time
import json
import torch
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

# Dynamic path resolution to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.data_loader import GlPoDataset
from ai_pipeline.models.sequential_glpo_model import SequentialGLPOModel
from ai_pipeline.training.unsupervised_pretrainer import UnsupervisedPretrainer
from ai_pipeline.envs.logistics_gym_env import create_env_from_project_graph
from ai_pipeline.training.ppo_trainer import ActorCritic, flatten_obs, RunningMeanStd
from ai_pipeline.src.algorithms.cpm import build_project_graph, calculate_cpm, get_critical_path
from ai_pipeline.src.algorithms.pert import calculate_project_pert
from ai_pipeline.src.algorithms.monte_carlo import run_monte_carlo_simulation
from ai_pipeline.src.algorithms.nsga2 import run_nsga2_optimization
from ai_pipeline.src.algorithms.cpsat_solver import run_cpsat_scheduling
from ai_pipeline.src.utils.agenda_calculator import load_agenda_from_db, calculate_duration_hours

def main():
    parser = argparse.ArgumentParser(description="GLPO Main Pipeline Orchestrator (AI + OR + RL)")
    parser.add_argument("--project_id", type=str, default="C2019-16", help="Project ID to run schedule (e.g. C2019-16)")
    parser.add_argument("--deadline", type=float, default=None, help="Custom deadline (hours)")
    parser.add_argument("--budget", type=float, default=None, help="Custom budget threshold")
    parser.add_argument("--pretrain_epochs", type=int, default=-1, help="Epochs for unsupervised pre-training (-1 for optimal defaults: GAT=300, DAGNN=500)")
    parser.add_argument("--output_json", type=str, default=None, help="Path to save output JSON")
    parser.add_argument("--force_pretrain", action="store_true", help="Force running offline pre-training")
    parser.add_argument("--only_pretrain", action="store_true", help="Run only offline pre-training phase and exit")
    
    args = parser.parse_args()
    
    project_id = args.project_id
    processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
    project_dir = os.path.join(processed_dir, project_id)
    
    if not os.path.exists(project_dir):
        print(f"❌ Project directory {project_dir} does not exist.")
        sys.exit(1)
        
    print(f"================================================================================")
    print(f"🚀 KHỞI ĐỘNG NHÁNH CHÍNH (MAIN PIPELINE: AI + OR + RL) CHO DỰ ÁN: {project_id}")
    print(f"================================================================================")
    
    # ── BƯỚC 1: DATA INGESTION & TĨNH CPM ──────────────────────────────────────
    print("\n📥 [BƯỚC 1] Data Ingestion & CPM Analysis...")
    from ai_pipeline.models.data_loader import GlPoProjectGraph
    project_graph = GlPoProjectGraph(project_dir)
    print(f"[DataLoader] Built Graph for {project_graph.project_id}: {project_graph.data.num_nodes} Nodes, {project_graph.data.num_edges} Edges")        
    if project_graph is None:
        print(f"❌ Project ID {project_id} not found in dataset.")
        sys.exit(1)
        
    tasks_df = pd.read_csv(os.path.join(project_dir, 'tasks.csv'))
    edges_df = pd.read_csv(os.path.join(project_dir, 'predecessors.csv'))
    res_df = pd.read_csv(os.path.join(project_dir, 'resources.csv'))
    task_res_df = pd.read_csv(os.path.join(project_dir, 'task_resources.csv'))
    
    tasks = tasks_df.to_dict(orient='records')
    dependencies = []
    for _, row in edges_df.iterrows():
        dependencies.append((str(row['predecessor_task_id']), str(row['successor_task_id'])))
        
    resource_capacities = {}
    for _, row in res_df.iterrows():
        resource_capacities[str(row['ID'])] = int(float(row.get('Availability', 1.0)))
        
    for t in tasks:
        t_id = t['id']
        t_req = task_res_df[task_res_df['task_id'] == t_id]
        t['resource_demand'] = {str(row['resource_id']): int(row['request_quantity']) for _, row in t_req.iterrows()}
        
    G = build_project_graph(tasks, dependencies)
    
    # Load agenda từ database
    try:
        project_id_int = int(project_id)
    except (ValueError, TypeError):
        project_id_int = 0
    agenda = load_agenda_from_db(project_id_int)
    hours_per_day = agenda['hours_per_day']
    days_per_week = agenda['days_per_week']
    overtime_multiplier = agenda['overtime_multiplier']
    print(f"   • Agenda: {hours_per_day}h/ngày, {days_per_week} ngày/tuần, OT x{overtime_multiplier}")
    
    import math
    def safe_float(v):
        try:
            val = float(v)
            return 0.0 if math.isnan(val) or math.isinf(val) else val
        except (ValueError, TypeError):
            return 0.0

    # Tính toán trước duration thực tế và lưu lại vào tasks (để xuất JSON không bị 0.0)
    for t in tasks:
        if 'most_probable_duration' not in t and 'duration' not in t:
            d_m = safe_float(t.get('duration_months', 0.0))
            d_w = safe_float(t.get('duration_weeks', 0.0))
            d_d = safe_float(t.get('duration_days', 0.0))
            d_h = safe_float(t.get('duration_hours', 0.0))
            cal_type = str(t.get('calendar_type', 'Agenda'))
            dur_calc = calculate_duration_hours(d_m, d_w, d_d, d_h, hours_per_day, days_per_week, cal_type)
            t['most_probable_duration'] = dur_calc
            if G.has_node(t['id']):
                G.nodes[t['id']]['most_probable_duration'] = dur_calc
                
    G_cpm, static_makespan = calculate_cpm(G, hours_per_day=hours_per_day, days_per_week=days_per_week)
    print(f"   • Số lượng công việc: {len(tasks)} tasks")
    print(f"   • Số cạnh phụ thuộc: {len(dependencies)}")
    print(f"   • Makespan CPM tĩnh: {static_makespan:.2f} giờ")
    
    # Validate baseline_start vs CPM ES
    import datetime
    baseline_starts = {}
    for t in tasks:
        bs = t.get('baseline_start')
        if bs and str(bs).lower() != 'nan':
            try:
                baseline_starts[t['id']] = pd.to_datetime(bs)
            except Exception:
                pass
    if baseline_starts:
        project_start = min(baseline_starts.values())
        mismatches = 0
        for node in G_cpm.nodes():
            if node in baseline_starts:
                bs_relative_hours = (baseline_starts[node] - project_start).total_seconds() / 3600.0
                cpm_es = G_cpm.nodes[node].get('es', 0.0)
                if abs(bs_relative_hours - cpm_es) > hours_per_day:  # Tolerance: 1 working day
                    mismatches += 1
        if mismatches > 0:
            print(f"   ⚠️ {mismatches} tasks có baseline_start lệch so với CPM ES > 1 ngày làm việc")
        else:
            print(f"   ✅ Baseline Start khớp với CPM ES cho tất cả {len(baseline_starts)} tasks")
    
    # Set default values if not specified
    if args.deadline is None:
        deadline = static_makespan * 1.3
    else:
        deadline = args.deadline
        
    if args.budget is None:
        cost_keys = [
            'internal_labor_cost', 'outsourcing_cost', 'overtime_cost',
            'material_cost', 'equipment_fuel_cost', 'qa_qc_cost',
            'training_cost', 'facility_rent', 'communication_cost', 'utilities_cost',
            'insurance_cost', 'licensing_cost', 'warranty_cost'
        ]
        def safe_float(v):
            try:
                val = float(v)
                import math
                return 0.0 if math.isnan(val) else val
            except (ValueError, TypeError):
                return 0.0
        total_normal_cost = sum(sum(safe_float(t.get(k, 0.0)) for k in cost_keys) for t in tasks)
        budget = total_normal_cost * 1.5
        # Fallback if cost columns are all 0
        if budget == 0.0:
            budget = 48000.0
    else:
        budget = args.budget
        
    print(f"   • Hạn chót (Deadline): {deadline:.2f} giờ")
    print(f"   • Ngân sách (Budget): {budget:.2f}")
    
    # Checkpoints path
    checkpoints_dir = os.path.join(project_root, 'ai_pipeline', 'checkpoints')
    os.makedirs(checkpoints_dir, exist_ok=True)
    gat_chk = os.path.join(checkpoints_dir, 'gat_pretrained.pth')
    dagnn_chk = os.path.join(checkpoints_dir, 'dagnn_pretrained.pth')

    # Quyết định chạy Offline Pretraining
    run_offline = False
    if args.force_pretrain:
        run_offline = True
        print("   • Yêu cầu huấn luyện lại bằng tham số --force_pretrain.")
    elif not os.path.exists(gat_chk) or not os.path.exists(dagnn_chk):
        run_offline = True
        print("   • Thiếu checkpoint gat_pretrained.pth hoặc dagnn_pretrained.pth.")

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = SequentialGLPOModel(project_type="logistics_standard", gat_out_dim=32, dagnn_out_dim=32).to(device)
    data_pyg = project_graph.data.to(device)

    if run_offline:
        print("\n----------------------------------------------------------------------")
        print("1. OFFLINE PRETRAINING (GAT + DAGNN Multi-Task SSL)")
        print("----------------------------------------------------------------------")
        pretrainer = UnsupervisedPretrainer(model, device=device)
        gae_eps = 300 if args.pretrain_epochs == -1 else args.pretrain_epochs
        cpm_eps = 500 if args.pretrain_epochs == -1 else args.pretrain_epochs
        print(f"   • Đang huấn luyện Offline: GAE + DGI + CPM + MASK + TOPO (GAT={gae_eps}, DAGNN={cpm_eps} epochs)...")
        pretrainer.pretrain_all(data_pyg, gae_epochs=gae_eps, cpm_epochs=cpm_eps, verbose=True)
        print("   • Đã lưu weights thành công.")
        
        # Nếu chỉ chạy ở chế độ offline, dừng tại đây
        if args.only_pretrain:
            print("\n✅ Đã hoàn thành OFFLINE PRETRAINING. Dừng chương trình theo yêu cầu.")
            sys.exit(0)
    else:
        print("\n----------------------------------------------------------------------")
        print("2. LOAD PRETRAINED ENCODER (GAT + DAGNN)")
        print("----------------------------------------------------------------------")
        from ai_pipeline.training.unsupervised_pretrainer import load_pretrained, load_pretrained_dagnn
        print(f"   • Đang tải weights từ: {os.path.basename(gat_chk)} và {os.path.basename(dagnn_chk)}")
        load_pretrained(model, gat_chk, device)
        load_pretrained_dagnn(model, dagnn_chk, device)
        print("   • Đã nạp weights thành công.")

    print("\n----------------------------------------------------------------------")
    print("3. ONLINE EXECUTION (CPM + Monte Carlo + NSGA-II + CP-SAT + PPO)")
    print("----------------------------------------------------------------------")
    
    # Run model forward pass to get topological/risk features
    model.eval()
    with torch.no_grad():
        detailed_out = model.forward_detailed(data_pyg)
        
    h_dagnn = detailed_out['h_dagnn'].cpu()
    # Sanitize NaN/Inf trong DAGNN output
    h_dagnn = torch.nan_to_num(h_dagnn, nan=0.0, posinf=1.0, neginf=-1.0)
    h_dagnn_np = h_dagnn.numpy()
    
    gate_values_raw = detailed_out['dagnn_info']['gate_values'].cpu()
    gate_values_raw = torch.nan_to_num(gate_values_raw, nan=0.0, posinf=1.0, neginf=-1.0)
    gate_values = gate_values_raw.numpy()
    
    # Map AI features to task parameters
    attention_score = {project_graph.idx_to_node[i]: float(gate_values[i]) for i in range(len(gate_values))}
    delay_pred = {project_graph.idx_to_node[i]: float(np.nanmean(h_dagnn_np[i]) * 5.0) for i in range(len(h_dagnn_np))}
    sigma_pred = {project_graph.idx_to_node[i]: float(max(0.01, np.nanstd(h_dagnn_np[i]) * 2.5)) for i in range(len(h_dagnn_np))}
    print(f"   • Trích xuất thành công GAT attention & DAGNN embeddings (NaN sanitized).")
    
    # ── BƯỚC 3: MONTE CARLO LEVEL 2 ───────────────────────────────────────────
    print("\n🎲 [BƯỚC 3] Monte Carlo Level 2 Simulation...")
    mc_res = run_monte_carlo_simulation(
        tasks=tasks,
        dependencies=dependencies,
        delay_pred=delay_pred,
        sigma_pred=sigma_pred,
        attention_score=attention_score,
        gamma=1.5,
        num_iterations=1000,
        deadline=deadline,
        hours_per_day=hours_per_day,
        days_per_week=days_per_week
    )
    print(f"   • Mean makespan: {mc_res['mean_makespan']:.2f} giờ")
    print(f"   • Xác suất đúng hạn (On-time Prob): {mc_res['P(on_time)'] * 100:.2f}%")
    print(f"   • Phân vị P90 makespan: {mc_res['percentiles']['P90']:.2f} giờ")
    
    # ── BƯỚC 4: NSGA-II OPTIMIZATION ──────────────────────────────────────────
    print("\n🧬 [BƯỚC 4] NSGA-II Multi-Objective Optimization...")
    crit_indices = mc_res['criticality_indices']
    pareto_solutions = run_nsga2_optimization(
        tasks=tasks,
        dependencies=dependencies,
        criticality_indices=crit_indices,
        b_max=budget,
        k_max=10, # Max outsource constraints
        pop_size=40,
        n_generations=20
    )
    print(f"   • Tìm thấy {len(pareto_solutions)} phương án trên biên Pareto.")
    
    # Select best solution (min makespan that satisfies budget)
    if pareto_solutions:
        pareto_solutions.sort(key=lambda s: s['makespan'])
    best_sol = pareto_solutions[0] if pareto_solutions else None
    if best_sol:
        print(f"   • Lựa chọn giải pháp Pareto: Makespan={best_sol['makespan']:.1f}h | Cost={best_sol['cost']:.2f} | Risk={best_sol['risk']:.4f}")
        selected_modes = best_sol['modes']
    else:
        print("   ⚠️ Không tìm thấy giải pháp Pareto hợp lệ, sử dụng Normal modes.")
        selected_modes = [0] * len(tasks)
        
    # ── BƯỚC 4.5: PROJECT STATE MANAGER (DYNAMIC PROJECT STATE EVOLUTION) ─────
    print("\n🔄 [BƯỚC 4.5] Project State Manager (Dynamic Project State Evolution)...")
    from ai_pipeline.src.state.action_model import ActionObject
    from ai_pipeline.src.state.project_state_manager import ProjectStateManager
    
    state_manager = ProjectStateManager(
        initial_project_graph=project_graph,
        initial_tasks=tasks,
        initial_dependencies=dependencies,
        initial_resource_capacities=resource_capacities,
        model=model,
        device=device,
        deadline=deadline
    )
    
    if best_sol:
        action_obj = ActionObject.from_pareto_option(best_sol, tasks)
        evolved_state = state_manager.apply_action(action_obj)
        comparison_report = state_manager.get_before_after_comparison(before_index=0, after_index=1)
        print(f"   • Trạng thái đồ thị tiến hóa: State 0 → State {evolved_state.state_id}")
        print(f"   • Re-inference GAT & DAGNN: Đã cập nhật embeddings mới mà không cần train lại.")
        print(f"   • Makespan tiến hóa: {comparison_report['metrics_comparison']['makespan']['before']:.1f}h → {comparison_report['metrics_comparison']['makespan']['after']:.1f}h ({comparison_report['metrics_comparison']['makespan']['percent_change']:.1f}%)")
    else:
        comparison_report = state_manager.get_before_after_comparison(before_index=0, after_index=0)

    # ── BƯỚC 5: CP-SAT RCPSP SOLVER ────────────────────────────────────────────
    print("\n⚙️ [BƯỚC 5] CP-SAT Constraint Programming Solver...")
    # Inject NSGA-II selected modes into tasks for CP-SAT baseline schedule
    tasks_with_modes = []
    for idx, t in enumerate(tasks):
        mode = selected_modes[idx]
        t_copy = t.copy()
        d_val = float(t_copy.get('most_probable_duration', t_copy.get('duration', 0.0)))
        if mode == 1: # Crash
            t_copy['most_probable_duration'] = max(1, int(round(d_val / 1.5)))
        elif mode == 2: # Outsource
            t_copy['most_probable_duration'] = max(1, int(round(d_val / 2.0)))
            # Giải phóng tài nguyên nội bộ khi thuê ngoài
            t_copy['resource_demand'] = {}
        else:
            t_copy['most_probable_duration'] = max(1, int(round(d_val)))
        tasks_with_modes.append(t_copy)
        
    cpsat_res = run_cpsat_scheduling(
        tasks=tasks_with_modes,
        dependencies=dependencies,
        resource_capacities=resource_capacities,
        time_limit_sec=15.0,
        hours_per_day=hours_per_day,
        days_per_week=days_per_week
    )
    print(f"   • CP-SAT Solver Status: {cpsat_res['status']}")
    print(f"   • CP-SAT Baseline Makespan: {cpsat_res['makespan']} giờ")
    
    # ── BƯỚC 6: PPO RUNTIME CONTROL ────────────────────────────────────────────
    print("\n🤖 [BƯỚC 6] PPO Agent Runtime Dynamic Control...")
    # Initialize env
    env = create_env_from_project_graph(project_graph)
    # Configure env constraints
    env._global_constraints['deadline'] = deadline
    env._global_constraints['budget'] = budget
    
    # Load checkpoint
    checkpoint_path = os.path.join(project_root, 'ai_pipeline', 'checkpoints', 'ppo_final.pt')
    if not os.path.exists(checkpoint_path):
        checkpoint_path = os.path.join(project_root, 'ai_pipeline', 'checkpoints', 'ppo_best.pt')
        
    ppo_reward = 0.0
    ppo_makespan = 0.0
    ppo_tgc = 0.0
    ppo_modes = []
    
    if os.path.exists(checkpoint_path):
        print(f"   • Đang nạp PPO Agent checkpoint từ: {os.path.basename(checkpoint_path)}")
        checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'), weights_only=False)
        
        # Đọc cấu hình từ checkpoint
        cfg_chk = checkpoint.get('config', {})
        use_pretrained = cfg_chk.get('use_pretrained', True)
        enable_relative_state = cfg_chk.get('enable_relative_state', True)
        obs_dim = 48 # Bắt buộc dùng 48 vì schema đã đổi
        action_dim = cfg_chk.get('action_dim', 3)
        hidden_dims = cfg_chk.get('hidden_dims', [256, 128])
        
        agent = ActorCritic(obs_dim=obs_dim, action_dim=action_dim, hidden_dims=hidden_dims, use_pretrained=use_pretrained)
        agent.use_pretrained = use_pretrained
        agent.project_pyg_data = [project_graph.data]
        if agent.use_pretrained:
            agent.setup_pretrained_encoder(torch.device('cpu'))
            
        try:
            agent.load_state_dict(checkpoint['agent_state_dict'])
            agent.eval()
        except RuntimeError as e:
            print(f"[WARNING] Không thể nạp weights cho PPO Agent do khác biệt kiến trúc: {e}")
            print("   • Đang khởi tạo PPO Agent ngẫu nhiên.")
        
        # Áp dụng cấu hình lên env
        env.enable_relative_state = enable_relative_state
        
        obs_normalizer = RunningMeanStd(shape=(obs_dim,))
        if 'obs_normalizer' in checkpoint:
            # Chỉ nạp nếu kích thước khớp
            norm_data = checkpoint['obs_normalizer']
            if norm_data['mean'].shape[0] == obs_dim:
                obs_normalizer.mean = norm_data['mean']
                obs_normalizer.var = norm_data['var']
                obs_normalizer.count = norm_data['count']
            else:
                print("   • Bỏ qua nạp obs_normalizer do khác biệt kích thước.")
            
        # Tìm project_idx
        project_idx = 0
            
        # Run episode with PPO Agent
        obs_dict, info = env.reset(options={'domain_randomization': False})
        done = False
        while not done:
            topo_idx = env._state['current_topo_idx']
            task_idx = env._topo_order[topo_idx] if topo_idx < len(env._topo_order) else 0
            
            obs_flat = flatten_obs(
                obs_dict,
                project_idx=project_idx,
                task_idx=task_idx,
                use_pretrained=use_pretrained,
                enable_relative_state=enable_relative_state
            )
            obs_norm = obs_normalizer.normalize(obs_flat)
            if use_pretrained:
                obs_norm[32] = float(project_idx)
                obs_norm[33] = float(task_idx)
                
            obs_tensor = torch.tensor(obs_norm, dtype=torch.float32).unsqueeze(0)
            # Sanitize NaN in observation before PPO forward pass
            obs_tensor = torch.nan_to_num(obs_tensor, nan=0.0, posinf=1.0, neginf=-1.0)
            
            mask = env.action_masks()
            mask_tensor = torch.tensor(mask, dtype=torch.bool).unsqueeze(0)
            
            with torch.no_grad():
                dist, _ = agent(obs_tensor, mask_tensor)
                action = dist.probs.argmax(dim=-1).item()
                
            next_obs_dict, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            ppo_reward += reward
            obs_dict = next_obs_dict
            
        ppo_makespan = float(info['makespan'])
        ppo_tgc = float(info['cumulative_tgc'])
        ppo_modes = info['modes_assigned']
        print(f"   • PPO Agent Simulation: Makespan={ppo_makespan:.1f}h | TGC={ppo_tgc:.2f} | Reward={ppo_reward:.2f}")
    else:
        print("   ⚠️ Không tìm thấy checkpoint PPO Agent, bỏ qua bước giả lập PPO.")
        
    # ── BÁO CÁO KẾT QUẢ ────────────────────────────────────────────────────────
    print("\n📊 [BÁO CÁO] Kết quả chạy nhánh chính:")
    print(f"   ┌───────────────────────────┬──────────────┬──────────────┐")
    print(f"   │ Chỉ số so sánh            │ CP-SAT (OR)  │ PPO (AI+RL)  │")
    print(f"   ├───────────────────────────┼──────────────┼──────────────┤")
    print(f"   │ Makespan (thời lượng)     │ {cpsat_res['makespan']:>9.1f}h  │ {ppo_makespan:>9.1f}h  │")
    print(f"   │ Chi phí quy đổi (TGC)     │ {best_sol['cost'] if best_sol else 0.0:>12.2f} │ {ppo_tgc:>12.2f} │")
    print(f"   └───────────────────────────┴──────────────┴──────────────┘")
    
    # Save output json
    # Map task resources
    task_resources_map = {}
    for _, row in task_res_df.iterrows():
        tid = str(row['task_id'])
        rid = str(row['resource_id'])
        qty = float(row['request_quantity'])
        if tid not in task_resources_map:
            task_resources_map[tid] = []
        task_resources_map[tid].append({
            'resource_id': rid,
            'quantity': qty
        })

    tasks_metadata = []
    for idx, t in enumerate(tasks):
        # Calculate normal cost
        c_norm = sum(safe_float(t.get(k, 0.0)) for k in cost_keys)
        tasks_metadata.append({
            'id': t['id'],
            'name': str(t.get('task_name', '')),
            'most_probable_duration': float(t.get('most_probable_duration', t.get('duration', 0.0))),
            'normal_cost': c_norm,
            'crash_cost': c_norm * 1.5,
            'outsource_cost': c_norm * 2.0 + float(t.get('most_probable_duration', 0.0)) * 10.0,
            'resources': task_resources_map.get(t['id'], [])
        })

    output_data = {
        'project_id': project_id,
        'cpm_static_makespan': static_makespan,
        'deadline': deadline,
        'budget': budget,
        'dependencies': dependencies,
        'tasks_metadata': tasks_metadata,
        'monte_carlo': {
            'mean_makespan': mc_res['mean_makespan'],
            'on_time_prob': mc_res['P(on_time)'],
            'P90': mc_res['percentiles']['P90'],
            'criticality_indices': mc_res['criticality_indices']
        },
        'pareto_nsga2': {
            'solutions_found': len(pareto_solutions),
            'selected': best_sol,
            'options': pareto_solutions[:4] # Export top 4 options
        },
        'cp_sat_schedule': {
            'status': cpsat_res['status'],
            'makespan': cpsat_res['makespan'],
            'schedule': cpsat_res['schedule']
        },
        'ppo_schedule': {
            'makespan': ppo_makespan,
            'tgc': ppo_tgc,
            'reward': ppo_reward,
            'modes': ppo_modes
        },
        'project_state_evolution': {
            'current_state_id': state_manager.get_current_state().state_id,
            'before_after_comparison': comparison_report,
            'state_history': state_manager.get_replay_history()
        }
    }
    
    out_path = args.output_json
    if not out_path:
        out_path = os.path.join(project_root, 'ai_pipeline', 'data', f"output_{project_id}_main.json")
        
    def sanitize_dict(d):
        if isinstance(d, dict):
            return {k: sanitize_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [sanitize_dict(v) for v in d]
        elif isinstance(d, float):
            return 0.0 if math.isnan(d) or math.isinf(d) else d
        return d
        
    sanitized_output = sanitize_dict(output_data)
        
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(sanitized_output, f, indent=4, ensure_ascii=False)
    print(f"\n💾 Đã xuất kết quả lịch trình chi tiết về: {out_path}")
    print(f"================================================================================")

if __name__ == "__main__":
    main()
