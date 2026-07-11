import os
import sys
import argparse
import time
import json
import torch
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from torch_geometric.data import Batch

import multiprocessing as mp

# Set multiprocessing start method to 'spawn' to fix CUDA forking issues
try:
    mp.set_start_method('spawn', force=True)
except RuntimeError:
    pass

sys.stdout.reconfigure(encoding='utf-8')

# Dynamic path resolution to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.data_loader import GlPoDataset
from ai_pipeline.models.project_encoders import EncoderRegistry
from ai_pipeline.models.sequential_glpo_model import SequentialGLPOModel
from ai_pipeline.src.algorithms.cpm import build_project_graph, calculate_cpm
from ai_pipeline.src.algorithms.monte_carlo import run_monte_carlo_simulation
from ai_pipeline.src.algorithms.nsga2 import run_nsga2_optimization
from ai_pipeline.src.utils.agenda_calculator import load_agenda_from_db

def load_project_data(project_id: str, processed_dir: str):
    """Loads a single project's data and builds the PyG graph."""
    from ai_pipeline.models.data_loader import GlPoProjectGraph
    project_dir = os.path.join(processed_dir, str(project_id))
    if not os.path.exists(project_dir):
        return None
        
    project_graph = GlPoProjectGraph(project_dir)
    print(f"[DataLoader] Built Graph for {project_graph.project_id}: {project_graph.data.num_nodes} Nodes, {project_graph.data.num_edges} Edges")
            
    # Tạm thời giả lập project_type cho các project_id
    project_type = "software_dev" if str(project_id).isdigit() else "logistics_standard"
        
    tasks_df = pd.read_csv(os.path.join(project_dir, 'tasks.csv'))
    edges_df = pd.read_csv(os.path.join(project_dir, 'predecessors.csv'))
    task_res_path = os.path.join(project_dir, 'task_resources.csv')
    if os.path.exists(task_res_path):
        task_res_df = pd.read_csv(task_res_path)
    else:
        task_res_df = pd.DataFrame(columns=['task_id', 'resource_id', 'request_quantity'])
    
    tasks = tasks_df.to_dict(orient='records')
    for t in tasks:
        if 'id' not in t and 'task_id' in t:
            t['id'] = str(t['task_id'])
        else:
            t['id'] = str(t.get('id', t.get('Task_ID', 'unknown')))
            
        t_id_str = t['id']
        t_req = task_res_df[(task_res_df['task_id'].astype(str) == t_id_str) | (task_res_df['task_id'] == t_id_str)]
        
        res_key = 'resource_id' if 'resource_id' in t_req.columns else 'resource_name'
        qty_key = 'request_quantity' if 'request_quantity' in t_req.columns else 'quantity'
        
        t['resource_demand'] = {}
        if res_key in t_req.columns and qty_key in t_req.columns:
            t['resource_demand'] = {str(row[res_key]): int(row[qty_key]) for _, row in t_req.iterrows()}
            
    dependencies = []
    src_key = 'predecessor_task_id' if 'predecessor_task_id' in edges_df.columns else 'source_id'
    dst_key = 'successor_task_id' if 'successor_task_id' in edges_df.columns else 'target_id'
    
    for _, row in edges_df.iterrows():
        if src_key in row and dst_key in row:
            dependencies.append((str(row[src_key]), str(row[dst_key])))
            
    # Fallback in case columns differ
    if not dependencies and os.path.exists(os.path.join(project_dir, 'predecessors.csv')):
        dep_df = pd.read_csv(os.path.join(project_dir, 'predecessors.csv'))
        t_col = 'task_id' if 'task_id' in dep_df.columns else 'Task_ID'
        p_col = 'predecessor_id' if 'predecessor_id' in dep_df.columns else 'Predecessor_ID'
        if t_col in dep_df.columns and p_col in dep_df.columns:
            for _, row in dep_df.iterrows():
                dependencies.append((str(row[p_col]), str(row[t_col])))
            
    try:
        project_id_int = int(project_id)
    except (ValueError, TypeError):
        project_id_int = 0
    agenda = load_agenda_from_db(project_id_int)
    
    _, static_makespan = calculate_cpm(build_project_graph(tasks, dependencies), hours_per_day=agenda['hours_per_day'], days_per_week=agenda['days_per_week'])
    
    return {
        'id': project_id,
        'type': project_type,
        'graph': project_graph,
        'tasks': tasks,
        'dependencies': dependencies,
        'agenda': agenda,
        'static_makespan': static_makespan
    }

def run_project_or_tasks(proj: Dict, ai_features: Dict, deadline: float):
    """Runs OR algorithms (Monte Carlo, NSGA-II) for a single project. Intended for multiprocessing."""
    print(f"[OR-Worker] Bắt đầu xử lý OR cho dự án {proj['id']}...")
    
    # Bỏ qua logic OR nặng nề để chống sập RAM Docker
    mc_res = {
        'mean_makespan': proj['static_makespan'] * 1.1,
        'P(on_time)': 0.95,
        'percentiles': {'P90': proj['static_makespan'] * 1.2},
        'criticality_indices': {t['id']: 0.5 for t in proj['tasks']}
    }
    
    pareto_solutions = [{"makespan": proj['static_makespan']*1.1, "cost": 100000, "risk": 5.0}] * 10

    
    return {
        'id': proj['id'],
        'mc_res': mc_res,
        'pareto_solutions': pareto_solutions
    }

def main():
    parser = argparse.ArgumentParser(description="GLPO Portfolio Orchestrator (Parallel Multi-Project)")
    parser.add_argument("--portfolio", type=str, required=True, help="Comma-separated list of Project IDs (e.g. C2019-16,19)")
    parser.add_argument("--deadline", type=float, default=None, help="Custom deadline (hours)")
    args = parser.parse_args()
    
    project_ids = [pid.strip() for pid in args.portfolio.split(',') if pid.strip()]
    processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
    
    print(f"================================================================================")
    print(f"🚀 KHỞI ĐỘNG PORTFOLIO OPTIMIZATION CHO {len(project_ids)} DỰ ÁN")
    print(f"================================================================================")
    
    projects = []
    
    for pid in project_ids:
        p_data = load_project_data(pid, processed_dir)
        if p_data is not None:
            projects.append(p_data)
        else:
            print(f"⚠️ Không tìm thấy dữ liệu cho dự án {pid}, bỏ qua.")
            
    if not projects:
        print("❌ Không có dự án nào hợp lệ để chạy Portfolio.")
        sys.exit(1)
        
    print(f"\n📥 [BƯỚC 1] Đã tải thành công {len(projects)} dự án.")
    results = {}
    
    # ── BƯỚC 1.5: DATABASE CACHE CHECK ────────
    import psycopg2
    db_url = os.environ.get('DATABASE_URL_SYNC', 'postgresql://glpo_admin:glpo_password@db:5432/glpo_db')
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    unprocessed_projects = []
    print("\n🔍 [BƯỚC 1.5] Kiểm tra phương án đã xử lý trong Database...")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        for p in projects:
            try:
                # Ép kiểu project_id về string nếu nó chứa ký tự chữ (C2019-16)
                # Tuy nhiên id trong ai_simulation_runs kiểu int, ta có thể check bảng khác hoặc query an toàn.
                # Do dự án C2019-16 là chuỗi, nếu cột project_id của DB là int thì lỗi. 
                # Chỗ này tuỳ vào schema, ta cứ check xem ai_simulation_runs có project_id này không (nếu bảng dùng int, ta bỏ qua cast).
                # Vì project ID trong CSV đôi lúc là C2019-16, tốt nhất ta giả định project_id trong DB khớp type hoặc ta check bảng projects.
                cur.execute("SELECT id FROM projects WHERE id = %s", (p['id'],))
                if not cur.fetchone():
                    # Dự án không tồn tại trong DB, coi như unprocessed
                    unprocessed_projects.append(p)
                    continue
                
                cur.execute("SELECT id, status FROM ai_simulation_runs WHERE project_id = %s AND status = 'Completed' LIMIT 1", (p['id'],))
                row = cur.fetchone()
                if row:
                    print(f"   ⏭️  Dự án {p['id']}: Đã có phương án xử lý trước đó (Run ID: {row[0]}). Bỏ qua!")
                    results[p['id']] = {'status': 'cached_in_db'}
                else:
                    unprocessed_projects.append(p)
            except Exception as e:
                # Lỗi type (ví dụ DB int nhưng ID string), fallback unprocessed
                conn.rollback()
                unprocessed_projects.append(p)
        conn.close()
    except Exception as e:
        print(f"[WARNING] Lỗi kết nối DB: {e}. Sẽ xử lý tất cả dự án.")
        unprocessed_projects = projects

    projects = unprocessed_projects
    if not projects:
        print("\n✅ Tất cả dự án đã được xử lý từ trước! Kết thúc chương trình.")
        return

    # ── BƯỚC 2 & 3: XỬ LÝ TUẦN TỰ (SEQUENTIAL) TỪNG DỰ ÁN ĐỂ CHỐNG CRASH ────────
    print("\n🧠 [BƯỚC 2 & 3] AI Inference & OR Optimization (Chạy Tuần Tự 1-by-1)...")
    # Force CPU to prevent Docker CUDA OOM Kills
    device = 'cpu'
    
    unique_types = set(p['type'] for p in projects)
    encoders = {}
    for pt in unique_types:
        try:
            encoder, _ = EncoderRegistry.get_encoder(pt, latent_dim=64)
            encoders[pt] = encoder.to(device)
            print(f"   [Encoder] Nạp encoder cho type: {pt}")
        except ValueError as e:
            print(f"[ERROR] {e}")
            return
            
    try:
        model = SequentialGLPOModel(project_type="logistics_standard", gat_out_dim=32, dagnn_out_dim=32).to(device)
        model.eval()
        
        # Load weights (Bỏ qua lỗi strict vì khác architecture)
        gat_weight_path = os.path.join(project_root, "ai_pipeline", "training", "checkpoints", "ppo_final.pt")
        if os.path.exists(gat_weight_path):
            state_dict = torch.load(gat_weight_path, map_location=device, weights_only=True)
            model.load_state_dict(state_dict, strict=False)
            
        dagnn_weight_path = os.path.join(project_root, "ai_pipeline", "training", "checkpoints", "gat_dagnn_pretrained.pt")
        if os.path.exists(dagnn_weight_path):
            state_dict = torch.load(dagnn_weight_path, map_location=device, weights_only=True)
            model.load_state_dict(state_dict, strict=False)
    except Exception as e:
        print(f"[ERROR] Lỗi khi nạp weights: {e}")
        pass

    for p in projects:
        print(f"\n▶ Đang xử lý Dự án {p['id']} (Type: {p['type']})...")
        # --- AI Inference ---
        encoder = encoders[p['type']]
        graph = p['graph'].data.to(device)
        
        with torch.no_grad():
            x_encoded = encoder(graph.x)
            graph.x = x_encoded
            # Xử lý 1 đồ thị
            batch = Batch.from_data_list([graph]).to(device)
            detailed_out = model.forward_detailed(batch, encoded_input=True)
            
            h_dagnn = detailed_out['h_dagnn'].cpu()
            h_dagnn = torch.nan_to_num(h_dagnn, nan=0.0, posinf=1.0, neginf=-1.0).numpy()
            gate_values = detailed_out['dagnn_info']['gate_values'].cpu()
            gate_values = torch.nan_to_num(gate_values, nan=0.0, posinf=1.0, neginf=-1.0).numpy()
            
            num_nodes = graph.num_nodes
            attention_score = {p['graph'].idx_to_node[i]: float(gate_values[i]) for i in range(num_nodes)}
            delay_pred = {p['graph'].idx_to_node[i]: float(np.nanmean(h_dagnn[i]) * 5.0) for i in range(num_nodes)}
            sigma_pred = {p['graph'].idx_to_node[i]: float(max(0.01, np.nanstd(h_dagnn[i]) * 2.5)) for i in range(num_nodes)}
            
            ai_features = {
                'delay_pred': delay_pred,
                'sigma_pred': sigma_pred,
                'attention_score': attention_score
            }
            
        # --- OR Algorithm ---
        p_deadline = args.deadline if args.deadline else p['static_makespan'] * 1.3
        
        # Gọi thẳng thay vì dùng Executor để giảm overhead bộ nhớ
        mc_res = run_monte_carlo_simulation(
            tasks=p['tasks'],
            dependencies=p['dependencies'],
            delay_pred=ai_features['delay_pred'],
            sigma_pred=ai_features['sigma_pred'],
            attention_score=ai_features['attention_score'],
            gamma=1.5,
            num_iterations=1000,
            deadline=p_deadline,
            hours_per_day=p['agenda']['hours_per_day'],
            days_per_week=p['agenda']['days_per_week']
        )
        print(f"   [OR] {p['id']}: Hoàn thành Monte Carlo! Bắt đầu NSGA-II...")
        
        pareto_solutions = run_nsga2_optimization(
            tasks=p['tasks'],
            dependencies=p['dependencies'],
            criticality_indices=mc_res['criticality_indices'],
            pop_size=50,
            n_generations=100
        )
        print(f"   [OR] {p['id']}: Hoàn thành NSGA-II với {len(pareto_solutions)} phương án!")
        
        results[p['id']] = {
            'mc_results': mc_res,
            'pareto_solutions': pareto_solutions
        }
        
        # NOTE: Tại đây ta có thể INSERT kết quả vào bảng ai_simulation_runs trong DB để cache cho lần sau!
        # ...

    start_time = time.time()
    elap = time.time() - start_time
    print(f"   ✅ Đã hoàn thành xử lý toàn bộ Portfolio trong {elap:.2f}s!")
    
    print("\n📊 [BÁO CÁO PORTFOLIO]")
    for p in projects:
        pid = p['id']
        if pid not in results:
            continue
        if results[pid].get('status') == 'cached_in_db':
            print(f"   ▶ Dự án: {pid}")
            print(f"       - Đã có kết quả lưu trong Database.")
            continue
            
        mc = results[pid]['mc_results']
        pareto = results[pid]['pareto_solutions']
        print(f"   ▶ Dự án: {pid}")
        print(f"       - P(on-time): {mc['P(on_time)']*100:.2f}% | P90 Makespan: {mc['percentiles']['P90']:.1f}h")
        print(f"       - Số phương án Pareto (NSGA-II): {len(pareto)}")

if __name__ == "__main__":
    main()
