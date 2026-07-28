"""
GLPO New Pipeline Runner (End-to-End Orchestrator)
===================================================
Thư mục: ai_pipeline/models/moi/pipeline_runner.py

Chức năng:
    Orchestrator nối toàn bộ 5 bước của kiến trúc mới:
        Bước 1: Dựng đồ thị HeteroData 4 loại nút (Task, Resource, Shift, Project)
        Bước 2: Tải/Huấn luyện HGT Masked Autoencoder Pretrainer (Phase 0)
        Bước 3: Suy luận HGT dự đoán Duration Factor, Expected Delay, Uncertainty Sigma
        Bước 4: Chạy mô phỏng Monte Carlo CPM (Tùy chọn số vòng 1000/5000/10000)
        Bước 5: Lập lịch tối ưu CP-SAT xuất tập phương án Pareto Frontier
"""

import os
import sys
import json
import torch
import argparse
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Path resolution
script_dir = os.path.dirname(os.path.abspath(__file__))
cand = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))

if os.path.exists(os.path.join("/app", "checkpoints")) or os.path.exists(os.path.join("/app", "ai_pipeline")):
    project_root = "/app"
elif os.path.exists(os.path.join(cand, "ai_pipeline")) and cand != "/":
    project_root = cand
elif os.path.exists(os.path.join(os.getcwd(), "ai_pipeline")):
    project_root = os.getcwd()
else:
    project_root = os.getcwd()

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.models.moi.hetero_graph_builder import HeteroGraphBuilder
from ai_pipeline.models.moi.hgt_model import HGTTaskPredictor
from ai_pipeline.models.moi.pretrainer import HGTPretrainer
from ai_pipeline.models.moi.monte_carlo_cpm import MonteCarloCPMEngine
from ai_pipeline.models.moi.cpsat_pareto_solver import CPSATParetoSolver


def run_new_pipeline(
    project_id: str = "C2011-07",
    mc_iterations: int = 10000,
    pareto_sort_by: str = "makespan_hours",
    pareto_count: int = 5,
    overtime_multiplier: float = 1.5,
    output_json: Optional[str] = None
) -> Dict[str, Any]:
    """
    Chạy quy trình pipeline hoàn chỉnh từ đầu đến cuối.
    """
    print("================================================================================")
    print(f"[START] KHOI DONG HE THONG PIPELINE MOI (AI + OR + MC-CPM) CHO DU AN: {project_id}")
    print("================================================================================")
    
    project_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed', project_id)
    if not os.path.exists(project_dir):
        raise FileNotFoundError(f"Thư mục dự án không tồn tại: {project_dir}")

    # 1. Dựng Đồ thị HeteroData 4 loại nút
    print("\n[BUOC 1] Dung Do thi HeteroData (4 Node Types)...")
    builder = HeteroGraphBuilder(project_dir)
    hetero_data = builder.build()
    print(f"   * Da tao do thi nut task: {hetero_data['task'].x.size(0)} nut, "
          f"tai nguyen: {hetero_data['resource'].x.size(0)} nut")

    # 2. Khởi tạo mô hình HGT & Pretrainer (Phase 0)
    model = HGTTaskPredictor({
        'task': hetero_data['task'].x.size(1),
        'resource': hetero_data['resource'].x.size(1),
        'shift': hetero_data['shift'].x.size(1),
        'project': hetero_data['project'].x.size(1)
    }, hidden_dim=128)
    
    ckpt_dir = os.path.join(project_root, "checkpoints")
    if project_root == "/" or not os.access(project_root, os.W_OK):
        ckpt_dir = os.path.join(os.getcwd(), "checkpoints")
    
    pretrainer = HGTPretrainer(model, checkpoint_dir=ckpt_dir)
    pretrainer.train_or_load(hetero_data, epochs=20)

    # 3. Suy luận dự báo AI
    with torch.no_grad():
        preds = model(hetero_data.x_dict, hetero_data.edge_index_dict)

    decoded_preds = builder.normalizer.decode_predictions(preds)

    ai_task_preds = {}
    for t_id, idx in builder.task_id_map.items():
        ai_task_preds[t_id] = {
            'duration_factor': float(decoded_preds['duration_factor'][idx]),
            'expected_delay': min(24.0, float(decoded_preds['expected_delay_hours'][idx])),
            'uncertainty_sigma': float(decoded_preds['uncertainty_sigma'][idx])
        }
    print(f"   * AI suy luan & gia ma (Decoder) thanh cong du bao cho {len(ai_task_preds)} task.")

    # 4. Mô phỏng Monte Carlo CPM dựa trên Lịch Agenda
    print(f"\n[BUOC 4] Mo phong Monte Carlo CPM voi {mc_iterations:,} vong chay...")
    tasks_df = pd.read_csv(os.path.join(project_dir, 'tasks.csv'))
    logic_df = pd.read_csv(os.path.join(project_dir, 'logic.csv'))
    res_df = pd.read_csv(os.path.join(project_dir, 'resources.csv'))
    task_res_df = pd.read_csv(os.path.join(project_dir, 'task_resources.csv'))

    tasks = tasks_df.to_dict(orient='records')
    for t in tasks:
        t['id'] = str(t.get('task_id', t.get('id', '')))

    dependencies = []
    for _, row in logic_df.iterrows():
        src = str(row['predecessor_id'])
        tgt = str(row['successor_id'])
        lag = float(row.get('lag_hours', 0.0))
        attr = {'lag_hours': lag, 'dependency_type': str(row.get('dependency_type', 'FS'))}
        dependencies.append((src, tgt, attr))

    mc_engine = MonteCarloCPMEngine(
        tasks,
        dependencies,
        calendar_engine=builder.calendar_engine
    )
    mc_results = mc_engine.run_simulation(num_iterations=mc_iterations, ai_preds=ai_task_preds)

    print(f"   * Ky vong thoi gian du an (Mean Makespan): {mc_results['makespan_mean']:.2f} gio")
    print(f"   * Moc rui ro P50: {mc_results['p50']:.2f}h | P80: {mc_results['p80']:.2f}h | P95: {mc_results['p95']:.2f}h")

    # 5. Lập lịch tối ưu CP-SAT Pareto
    print("\n[BUOC 5] Lap lich toi uu CP-SAT Pareto (5-Tier Constraints)...")
    capacities = {}
    resources_dict = {}
    for _, r in res_df.iterrows():
        r_id = str(r['ID'])
        r_name = str(r.get('name', r_id))
        cap = float(r.get('max_availability', 1.0))
        capacities[r_id] = cap
        capacities[r_name] = cap
        resources_dict[r_id] = r.to_dict()

    task_resource_reqs = {}
    task_labor_rates = {}
    for _, tr in task_res_df.iterrows():
        t_id = str(tr['task_id'])
        r_id = str(tr['resource_id'])
        qty = float(tr.get('request_quantity', 1.0))
        
        r_info = resources_dict.get(r_id, {})
        u_cost = float(r_info.get('unit_cost', 0.0))
        
        task_resource_reqs[(t_id, r_id)] = qty
        task_labor_rates[t_id] = task_labor_rates.get(t_id, 0.0) + (qty * u_cost)

    solver = CPSATParetoSolver(
        tasks,
        dependencies,
        resource_capacities=capacities,
        task_resource_requirements=task_resource_reqs,
        resources_dict=resources_dict,
        criticality_index=mc_results['criticality_index'],
        ai_task_preds=ai_task_preds,
        task_labor_rates=task_labor_rates,
        overtime_multiplier=overtime_multiplier,
        mc_samples=mc_results.get('makespan_samples'),
        mc_iterations=mc_iterations,
        calendar_engine=builder.calendar_engine
    )
    pareto_options = solver.solve(time_limit_sec=15.0, pareto_count=pareto_count)

    # Sắp xếp kết quả Pareto theo tiêu chí người dùng chọn
    if pareto_sort_by in ['makespan_hours', 'total_cost', 'risk_score']:
        pareto_options = sorted(pareto_options, key=lambda x: x.get(pareto_sort_by, 0))

    print(f"   * Tim thay {len(pareto_options)} phuong an toi uu Pareto.")
    for idx, opt in enumerate(pareto_options, 1):
        tot_c = opt.get('total_cost', 0.0)
        r_pct = opt.get('risk_pct', 100.0)
        print(f"     [{idx}] {opt['option_name']} -> Thoi gian: {opt['makespan_hours']}h | Chi Phi: ${tot_c:,.2f} | Rui ro Tre: {r_pct}%")

    final_output = {
        'project_id': project_id,
        'ai_predictions': ai_task_preds,
        'monte_carlo_cpm': mc_results,
        'pareto_options': pareto_options
    }

    if output_json:
        os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
        print(f"\n[OUTPUT] Da luu ket qua dau ra JSON tai: {output_json}")

    print("\n[DONE] PIPELINE MOI HOAN THANH XUAT SAC!")
    return final_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GLPO New Hybrid Pipeline Orchestrator")
    parser.add_argument("--project_id", type=str, default="C2011-07", help="Mã dự án (ví dụ C2011-07)")
    parser.add_argument("--mc_iterations", type=int, default=10000, help="Số vòng mô phỏng Monte Carlo (1000, 5000, 10000)")
    parser.add_argument("--pareto_count", type=int, default=5, help="Số lượng phương án Pareto xuất ra (ví dụ 3, 5, 10)")
    parser.add_argument("--overtime_multiplier", type=float, default=1.5, help="Hệ số lương nhân công tăng ca (ví dụ 1.5, 2.0, 1.25)")
    parser.add_argument("--pareto_sort", type=str, default="makespan_hours", choices=["makespan_hours", "total_cost", "risk_score"], help="Tiêu chí sắp xếp tập Pareto")
    parser.add_argument("--output_json", type=str, default=None, help="Đường dẫn lưu file JSON đầu ra")

    args = parser.parse_args()
    run_new_pipeline(
        project_id=args.project_id,
        mc_iterations=args.mc_iterations,
        pareto_sort_by=args.pareto_sort,
        pareto_count=args.pareto_count,
        overtime_multiplier=args.overtime_multiplier,
        output_json=args.output_json
    )
