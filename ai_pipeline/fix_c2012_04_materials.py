import os
import pandas as pd

proj_dir = r"E:\University\Year 3 - 3\DA3\ai_pipeline\data\processed\C2012-04"

tasks_csv = os.path.join(proj_dir, "tasks.csv")
tr_csv = os.path.join(proj_dir, "task_resources.csv")
res_csv = os.path.join(proj_dir, "resources.csv")

df_tasks = pd.read_csv(tasks_csv)
df_tr = pd.read_csv(tr_csv)
df_res = pd.read_csv(res_csv)

print(f"Original tasks shape: {df_tasks.shape}")
print(f"Original task_resources shape: {df_tr.shape}")
print(f"Original resources shape: {df_res.shape}")

# Identify material resource names / IDs
mat_names = df_res[df_res['Name'].astype(str).str.lower().str.contains('material') | (df_res['Type'].astype(str).str.lower() == 'consumable')]['Name'].tolist()
print("Material Resource Names to remove:", mat_names)

# Filter material rows from task_resources
is_mat_row = df_tr['role'].isin(mat_names) | (df_tr['type'].astype(str).str.lower() == 'consumable')
df_mat = df_tr[is_mat_row].copy()
df_tr_clean = df_tr[~is_mat_row].copy()

# Map task_id string format to match tasks.csv task_id
# If task_id in tasks.csv is int or string e.g. 1 or '1'
df_tasks['task_id_str'] = df_tasks['task_id'].astype(str)
df_mat['task_id_str'] = df_mat['task_id'].astype(str)

# Calculate added material cost per task
added_mat_cost = {}
for _, row in df_mat.iterrows():
    t_id = str(row['task_id_str'])
    qty = float(row['quantity'] or 0.0)
    rate = float(row.get('hourly_rate', 1.0) or 1.0)
    cost = qty * rate
    added_mat_cost[t_id] = added_mat_cost.get(t_id, 0.0) + cost

print(f"\nCalculated material costs for {len(added_mat_cost)} tasks:")
for t_id, cost in list(added_mat_cost.items())[:10]:
    print(f"  Task {t_id}: +${cost:,.2f}")

# Update g1_material in tasks.csv
if 'g1_material' not in df_tasks.columns:
    df_tasks['g1_material'] = 0.0

for t_id, cost in added_mat_cost.items():
    mask = df_tasks['task_id_str'] == t_id
    if mask.any():
        curr = df_tasks.loc[mask, 'g1_material'].fillna(0.0).iloc[0]
        df_tasks.loc[mask, 'g1_material'] = curr + cost

df_tasks.drop(columns=['task_id_str'], inplace=True, errors='ignore')

# Remove material resources from resources.csv
df_res_clean = df_res[~df_res['Name'].isin(mat_names) & (df_res['Type'].astype(str).str.lower() != 'consumable')].copy()

print(f"\nCleaned tasks shape: {df_tasks.shape}")
print(f"Cleaned task_resources shape: {df_tr_clean.shape} (Removed {len(df_mat)} rows)")
print(f"Cleaned resources shape: {df_res_clean.shape} (Removed {len(mat_names)} material resources)")

# Save updated CSV files
df_tasks.to_csv(tasks_csv, index=False)
df_tr_clean.to_csv(tr_csv, index=False)
df_res_clean.to_csv(res_csv, index=False)

print("\n[SUCCESS] Successfully moved Material costs to tasks.csv (g1_material) and cleaned task_resources.csv & resources.csv for C2012-04!")
