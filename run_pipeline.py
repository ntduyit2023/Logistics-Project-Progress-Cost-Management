import sys
sys.path.append('/')
import json
import os
from ai_pipeline.models.moi.pipeline_runner import run_new_pipeline

result = run_new_pipeline(
    project_id='C2011-07',
    target_deadline='2011-05-30 17:00:00',
    penalty_per_day=500.0,
    bonus_per_day=200.0,
    mc_iterations=1000,
    pareto_count=20,
    output_json='/ai_pipeline/data/processed/C2011-07/cpsat_pareto_solutions.json'
)

print("\n--- CHI TIET PHUONG AN ---")
opt = result['pareto_options'][0]
print(f"Ten phuong an: {opt['option_name']}")
print(f"Makespan: {opt['makespan_hours']} h")
print(f"Tong chi phi: {opt['total_cost']}")
print(f"Chi phi phat: {opt.get('penalty_cost', 0)}")
print(f"Tien thuong: {opt.get('bonus_amount', 0)}")

print("\n--- CHI TIET 2 TASKS ---")
for idx, t in enumerate(list(opt['tasks_schedule'].values())[:2]):
    print(f"Task {idx+1}: {t['task_id']}")
    print(f"  Duration: {t['duration_hours']} h (Base: {t.get('base_effort_hours', 0)} h)")
    print(f"  Start: {t.get('start_datetime')} - End: {t.get('finish_datetime')}")
    print(f"  Crashing Strategy: {t.get('crashing_strategy')}")
    print(f"  Chi phi task: {t.get('total_cost')}")
