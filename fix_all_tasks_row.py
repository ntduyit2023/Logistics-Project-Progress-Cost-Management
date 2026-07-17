import glob
import re

for fpath in glob.glob('ai_pipeline/data/process_c*.py'):
    if '2011' in fpath:
        continue
        
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add baseline_start to tasks_rows
    # We look for:
    # "task_name": t["task_name"],
    # And we add "baseline_start" after it.
    
    content = re.sub(
        r'"task_name":\s*t\["task_name"\],',
        '"task_name": t["task_name"],\n            "baseline_start": t.get("baseline_start", ""),',
        content
    )

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Fixed {fpath}')
