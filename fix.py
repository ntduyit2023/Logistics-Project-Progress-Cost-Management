import glob
import pandas as pd

for fpath in glob.glob('ai_pipeline/data/process_c*.py'):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add baseline_start/end to output_tasks.append
    old_output_append = """        output_tasks.append({
            "task_id": task_id,
            "task_name": task_name,
            "g1_direct_cost": g1,"""
    new_output_append = """        baseline_start = str(row['Baseline Start']) if 'Baseline Start' in row and pd.notna(row['Baseline Start']) else ""
        baseline_end = str(row['Baseline End']) if 'Baseline End' in row and pd.notna(row['Baseline End']) else ""
        
        output_tasks.append({
            "task_id": task_id,
            "task_name": task_name,
            "baseline_start": baseline_start,
            "baseline_end": baseline_end,
            "g1_direct_cost": g1,"""
    
    content = content.replace(old_output_append, new_output_append)

    # 2. Add to tasks_rows
    old_tasks_row = """        row = {
            "task_id": t["task_id"],
            "task_name": t["task_name"],
            # G1"""
    new_tasks_row = """        row = {
            "task_id": t["task_id"],
            "task_name": t["task_name"],
            "baseline_start": t.get("baseline_start", ""),
            "baseline_end": t.get("baseline_end", ""),
            # G1"""
    content = content.replace(old_tasks_row, new_tasks_row)

    # 3. Fix schedules
    old_schedules = """            "baseline_start": str(row['Baseline Start']) if 'Baseline Start' in row and pd.notna(row['Baseline Start']) else "",
            "baseline_end": str(row['Baseline End']) if 'Baseline End' in row and pd.notna(row['Baseline End']) else "","""
    new_schedules = """            "baseline_start": t.get("baseline_start", ""),
            "baseline_end": t.get("baseline_end", ""),"""
    content = content.replace(old_schedules, new_schedules)

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Fixed {fpath}')
