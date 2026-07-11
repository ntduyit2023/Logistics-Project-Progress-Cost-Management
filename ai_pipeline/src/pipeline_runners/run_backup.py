import os
import sys
import argparse
import time
import json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

# Dynamic path resolution to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.src.algorithms.cpm import build_project_graph, calculate_cpm, get_critical_path
from ai_pipeline.src.algorithms.nsga2 import run_nsga2_optimization
from ai_pipeline.src.algorithms.cpsat_solver import run_cpsat_scheduling

def run_pure_or_monte_carlo(tasks, dependencies, num_iterations=10000):
    """
    Monte Carlo Level 1: Pure Operations Research (OR) without AI.
    Uses classical Beta-PERT distribution with synthesized 3-point estimates
    (Optimistic, Most Probable, Pessimistic).
    """
    node_ids = [t['id'] for t in tasks]
    n = len(node_ids)
    node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    
    # Pre-calculate 3-point estimates
    durations = {}
    for t in tasks:
        m = float(t.get('most_probable_duration', t.get('duration', 0.0)))
        o = m * 0.8  # Optimistic (-20%)
        p = m * 1.5  # Pessimistic (+50%)
        durations[t['id']] = (o, m, p)
        
    adj = {i: [] for i in range(n)}
    rev_adj = {i: [] for i in range(n)}
    for edge in dependencies:
        u, v = edge[0], edge[1]
        if u in node_to_idx and v in node_to_idx:
            u_idx = node_to_idx[u]
            v_idx = node_to_idx[v]
            adj[u_idx].append(v_idx)
            rev_adj[v_idx].append(u_idx)
            
    # Topological sort
    in_degree = [len(rev_adj[i]) for i in range(n)]
    queue = [i for i in range(n) if in_degree[i] == 0]
    topo_order = []
    while queue:
        u = queue.pop(0)
        topo_order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    critical_counts = np.zeros(n)
    makespans = np.zeros(num_iterations)
    
    for i in range(num_iterations):
        # Sample durations using triangular distribution as approximation for Beta-PERT
        sampled_d = np.zeros(n)
        for j, nid in enumerate(node_ids):
            o, m, p = durations[nid]
            if p > o:
                sampled_d[j] = np.random.triangular(o, m, p)
            else:
                sampled_d[j] = m
                
        # Forward pass
        EST = np.zeros(n)
        EFT = np.zeros(n)
        for u in topo_order:
            if rev_adj[u]:
                EST[u] = np.max([EFT[p] for p in rev_adj[u]])
            else:
                EST[u] = 0.0
            EFT[u] = EST[u] + sampled_d[u]
            
        makespan = np.max(EFT)
        makespans[i] = makespan
        
        # Backward pass
        LST = np.zeros(n)
        LFT = np.zeros(n)
        for u in reversed(topo_order):
            if adj[u]:
                LFT[u] = np.min([LST[s] for s in adj[u]])
            else:
                LFT[u] = makespan
            LST[u] = LFT[u] - sampled_d[u]
            
            # Check critical (slack <= 0)
            if LFT[u] - EFT[u] <= 0.001:
                critical_counts[u] += 1
                
    mean_makespan = np.mean(makespans)
    p90 = np.percentile(makespans, 90)
    criticality_indices = {node_ids[i]: float(critical_counts[i] / num_iterations) for i in range(n)}
    
    return {
        'mean_makespan': float(mean_makespan),
        'percentiles': {'P90': float(p90)},
        'criticality_indices': criticality_indices
    }

def main():
    parser = argparse.ArgumentParser(description="GLPO Backup Pipeline (Pure OR)")
    parser.add_argument("--project_id", type=str, default="C2019-16", help="Project ID to run schedule")
    parser.add_argument("--deadline", type=float, default=None, help="Custom deadline (hours)")
    parser.add_argument("--budget", type=float, default=None, help="Custom budget threshold")
    parser.add_argument("--output_json", type=str, default=None, help="Path to save output JSON")
    
    args = parser.parse_args()
    
    project_id = args.project_id
    processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
    project_dir = os.path.join(processed_dir, project_id)
    
    if not os.path.exists(project_dir):
        print(f"❌ Project directory {project_dir} does not exist.")
        sys.exit(1)
        
    print(f"================================================================================")
    print(f"🛡️ KHỞI ĐỘNG NHÁNH DỰ PHÒNG (BACKUP PIPELINE: PURE OR) CHO DỰ ÁN: {project_id}")
    print(f"================================================================================")
    
    # ── BƯỚC 1: DATA INGESTION & TĨNH CPM ──────────────────────────────────────
    print("\n📥 [BƯỚC 1] Data Ingestion & G6 Analytic CPM Analysis...")
    tasks_df = pd.read_csv(os.path.join(project_dir, 'tasks.csv'))
    edges_df = pd.read_csv(os.path.join(project_dir, 'predecessors.csv'))
    res_df = pd.read_csv(os.path.join(project_dir, 'resources.csv'))
    task_res_df = pd.read_csv(os.path.join(project_dir, 'task_resources.csv'))
    
    tasks = tasks_df.to_dict(orient='records')
    dependencies = []
    for _, row in edges_df.iterrows():
        # Lọc bỏ giá trị NaN
        pred = str(row['predecessor_task_id'])
        succ = str(row['successor_task_id'])
        if pred != 'nan' and succ != 'nan':
            dependencies.append((pred, succ))
        
    resource_capacities = {}
    for _, row in res_df.iterrows():
        resource_capacities[str(row['ID'])] = float(row.get('Availability', 1.0))
        
    for t in tasks:
        t_id = t['id']
        t_req = task_res_df[task_res_df['task_id'] == t_id]
        t['resource_demand'] = {str(row['resource_id']): int(row['request_quantity']) for _, row in t_req.iterrows()}
        
    G = build_project_graph(tasks, dependencies)
    _, static_makespan = calculate_cpm(G)
    print(f"   • Số lượng công việc: {len(tasks)} tasks")
    print(f"   • Số cạnh phụ thuộc: {len(dependencies)}")
    print(f"   • Makespan CPM tĩnh: {static_makespan:.2f} giờ")
    
    # Set default values if not specified
    if args.deadline is None:
        deadline = static_makespan * 1.3
    else:
        deadline = args.deadline
        
    cost_keys = [
        'internal_labor_cost', 'subcontracting_cost', 'overtime_crashing_cost',
        'material_cost', 'equipment_cost', 'direct_transportation',
        'energy_fuel_cost', 'testing_and_inspection', 'pm_overhead',
        'facility_rent', 'utilities', 'communication_cost',
        'internal_training', 'quality_mgmt_overhead'
    ]
    total_normal_cost = sum(sum(float(t.get(k, 0.0)) for k in cost_keys) for t in tasks)
    
    if args.budget is None:
        budget = total_normal_cost * 1.5
        if budget == 0.0:
            budget = 48000.0
    else:
        budget = args.budget
        
    print(f"   • Hạn chót (Deadline): {deadline:.2f} giờ")
    print(f"   • Ngân sách (Budget): {budget:.2f}")
    
    # ── BƯỚC 2 & 3: HEURISTIC AGGREGATOR & MONTE CARLO LEVEL 1 ────────────────
    print("\n🎲 [BƯỚC 2 & 3] Heuristic Rules & Monte Carlo Level 1 (No AI)...")
    print("   • Sử dụng ước lượng 3 điểm (Beta-PERT Approximation).")
    mc_res = run_pure_or_monte_carlo(tasks, dependencies, num_iterations=10000)
    print(f"   • Mean makespan: {mc_res['mean_makespan']:.2f} giờ")
    print(f"   • Phân vị P90 makespan: {mc_res['percentiles']['P90']:.2f} giờ")
    
    # ── BƯỚC 4: NSGA-II OPTIMIZATION ──────────────────────────────────────────
    print("\n🧬 [BƯỚC 4] NSGA-II Multi-Objective Optimization (Pure OR)...")
    crit_indices = mc_res['criticality_indices']
    pareto_solutions = run_nsga2_optimization(
        tasks=tasks,
        dependencies=dependencies,
        criticality_indices=crit_indices,
        b_max=budget,
        k_max=10, 
        pop_size=40,
        n_generations=20
    )
    print(f"   • Tìm thấy {len(pareto_solutions)} phương án trên biên Pareto.")
    
    if pareto_solutions:
        pareto_solutions.sort(key=lambda s: s['makespan'])
    best_sol = pareto_solutions[0] if pareto_solutions else None
    if best_sol:
        print(f"   • Lựa chọn giải pháp Pareto: Makespan={best_sol['makespan']:.1f}h | Cost={best_sol['cost']:.2f} | Risk={best_sol['risk']:.4f}")
        selected_modes = best_sol['modes']
    else:
        print("   ⚠️ Không tìm thấy giải pháp Pareto, sử dụng Normal modes.")
        selected_modes = [0] * len(tasks)
        
    # ── BƯỚC 5: CP-SAT RCPSP SOLVER ────────────────────────────────────────────
    print("\n⚙️ [BƯỚC 5] CP-SAT Constraint Programming Solver (Offline Fallback)...")
    tasks_with_modes = []
    for idx, t in enumerate(tasks):
        mode = selected_modes[idx]
        t_copy = t.copy()
        d_val = float(t_copy.get('most_probable_duration', t_copy.get('duration', 0.0)))
        if mode == 1: # Crash
            t_copy['most_probable_duration'] = max(1, int(round(d_val / 1.5)))
        elif mode == 2: # Outsource
            t_copy['most_probable_duration'] = max(1, int(round(d_val / 2.0)))
        else:
            t_copy['most_probable_duration'] = max(1, int(round(d_val)))
        tasks_with_modes.append(t_copy)
        
    cpsat_res = run_cpsat_scheduling(
        tasks=tasks_with_modes,
        dependencies=dependencies,
        resource_capacities=resource_capacities,
        time_limit_sec=15.0
    )
    print(f"   • CP-SAT Solver Status: {cpsat_res['status']}")
    print(f"   • CP-SAT Baseline Makespan: {cpsat_res['makespan']} giờ")
    
    print("\n🤖 [BƯỚC 6] KHÔNG sử dụng PPO Agent (Nhánh dự phòng hoạt động 100% bằng toán học).")
    
    # ── BÁO CÁO KẾT QUẢ ────────────────────────────────────────────────────────
    print("\n📊 [BÁO CÁO] Kết quả chạy nhánh dự phòng (Backup Pipeline):")
    print(f"   • Makespan CP-SAT: {cpsat_res['makespan']:.1f}h")
    
    tasks_metadata = []
    for idx, t in enumerate(tasks):
        c_norm = sum(float(t.get(k, 0.0)) for k in cost_keys)
        tasks_metadata.append({
            'id': t['id'],
            'most_probable_duration': float(t.get('most_probable_duration', t.get('duration', 0.0))),
            'normal_cost': c_norm,
            'crash_cost': c_norm * 1.5,
            'outsource_cost': c_norm * 2.0 + float(t.get('most_probable_duration', 0.0)) * 10.0
        })

    output_data = {
        'project_id': project_id,
        'pipeline_type': 'BACKUP_PURE_OR',
        'cpm_static_makespan': static_makespan,
        'deadline': deadline,
        'budget': budget,
        'dependencies': dependencies,
        'tasks_metadata': tasks_metadata,
        'monte_carlo': {
            'mean_makespan': mc_res['mean_makespan'],
            'P90': mc_res['percentiles']['P90'],
            'criticality_indices': mc_res['criticality_indices']
        },
        'pareto_nsga2': {
            'solutions_found': len(pareto_solutions),
            'selected': best_sol,
            'options': pareto_solutions[:4] 
        },
        'cp_sat_schedule': {
            'status': cpsat_res['status'],
            'makespan': cpsat_res['makespan'],
            'schedule': cpsat_res['schedule']
        }
    }
    
    out_path = args.output_json
    if not out_path:
        out_path = os.path.join(project_root, 'ai_pipeline', 'data', f"output_{project_id}_backup.json")
        
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    print(f"\n💾 Đã xuất kết quả lịch trình dự phòng về: {out_path}")
    print(f"================================================================================")

if __name__ == "__main__":
    main()
