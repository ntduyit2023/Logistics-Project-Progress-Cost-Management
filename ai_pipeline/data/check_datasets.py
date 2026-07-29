import pandas as pd
from pathlib import Path

base_dir = Path('ai_pipeline/data/processed')
for p_dir in sorted(base_dir.glob('C*')):
    t_file = p_dir / 'tasks.csv'
    tr_file = p_dir / 'task_resources.csv'
    r_file = p_dir / 'resources.csv'
    if t_file.exists() and tr_file.exists():
        df_t = pd.read_csv(t_file)
        df_tr = pd.read_csv(tr_file)
        df_r = pd.read_csv(r_file)
        print(f"=== {p_dir.name} ===")
        res_assigned_tasks = set(df_tr['task_id'].astype(str).unique())
        no_res_tasks = df_t[~df_t['task_id'].astype(str).isin(res_assigned_tasks)]
        print(f"Total Tasks: {len(df_t)}, Tasks with NO resources: {len(no_res_tasks)}")
        count_anomalies = 0
        for idx, r in no_res_tasks.iterrows():
            energy_val = float(r.get('energy', 0.0) or 0.0)
            labor_val = float(r.get('labor', 0.0) or 0.0)
            equip_val = float(r.get('equipment', 0.0) or 0.0)
            if energy_val > 0 or labor_val > 0 or equip_val > 0:
                count_anomalies += 1
                if count_anomalies <= 10:
                    print(f"  Anomaly task {r['task_id']}: labor={labor_val}, equip={equip_val}, energy={energy_val}")
        if count_anomalies > 10:
            print(f"  ... total anomaly tasks in {p_dir.name}: {count_anomalies}")
