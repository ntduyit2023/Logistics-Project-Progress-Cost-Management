import json
with open('e:/University/Year 3 - 3/DA3/ai_pipeline/data/processed/C2011-07/cpsat_pareto_solutions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
opt = data.get('pareto_options', [])[0]
print('\n--- CHI TIET PHUONG AN ---')
print(f"Ten phuong an: {opt.get('option_name', '')}")
print(f"Makespan: {opt.get('makespan_hours', 0)} h")
print(f"Tong chi phi: {opt.get('total_cost', 0)}")
print(f"Chi phi phat: {opt.get('penalty_cost', 0)}")
print(f"Tien thuong: {opt.get('bonus_amount', 0)}")

print('\n--- CHI TIET 2 TASKS ---')
for idx, t in enumerate(list(opt['tasks_schedule'].values())[:2]):
    print(f"Task {idx+1}: {t.get('task_id', '')}")
    print(f"  Duration: {t.get('duration_hours', 0)} h (Base: {t.get('base_effort_hours', 0)} h)")
    print(f"  Start: {t.get('start_datetime', '')} - End: {t.get('finish_datetime', '')}")
    print(f"  Crashing Strategy: {t.get('crashing_strategy', '')}")
