"""
Standardize all resources.csv files across the repository:
1. Classify Type strictly into 'Human' or 'Machine'.
2. Clean 'max_availability' into pure INTEGER (e.g. 10, 6, 1, 2).
3. Rename 'Cost/Unit' / 'Cost/Use' to 'unit_cost' (float).
4. Add 'energy' column: 0.25 * unit_cost for Machine, 0.0 for Human.
5. Add 'overtime_multi' column: 1.5 for Human, 1.0 for Machine.
"""

import os
import re
import glob
import pandas as pd

HUMAN_KEYWORDS = [
    'labour', 'labor', 'personnel', 'worker', 'engineer', 'skipper', 'welder',
    'team', 'leader', 'marketeer', 'administrator', 'employee', 'coordinator',
    'nurse', 'committee', 'director', 'logisticians', 'diver', 'diver team'
]

def classify_type(name: str, current_type: str) -> str:
    name_lower = str(name).lower()
    curr_lower = str(current_type).lower()
    if curr_lower in ['human', 'labor', 'personnel']:
        return 'Human'
    if curr_lower in ['machine', 'equipment']:
        return 'Machine'
    
    if any(k in name_lower for k in HUMAN_KEYWORDS):
        return 'Human'
    return 'Machine'

def clean_int(val) -> int:
    if val is None or pd.isna(val):
        return 1
    val_str = str(val)
    match = re.search(r'\d+', val_str)
    if match:
        return int(match.group())
    return 1

def clean_float(val) -> float:
    if val is None or pd.isna(val):
        return 0.0
    val_str = str(val)
    match = re.search(r'[-+]?\d*\.\d+|\d+', val_str)
    if match:
        return float(match.group())
    return 0.0

def process_file(file_path: str):
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            return
        
        # Drop redundant Cost/Use if Cost/Unit exists
        cols_lower = [c.lower() for c in df.columns]
        if 'cost/unit' in cols_lower and 'cost/use' in cols_lower:
            df = df.drop(columns=[c for c in df.columns if c.lower() == 'cost/use'])

        # 1. Standardize column names
        rename_map = {}
        for c in df.columns:
            c_clean = c.strip()
            if c_clean.lower() in ['id', 'resource_id']:
                rename_map[c] = 'ID'
            elif c_clean.lower() in ['name', 'resource_name']:
                rename_map[c] = 'name'
            elif c_clean.lower() in ['type', 'resource_type']:
                rename_map[c] = 'type'
            elif 'avail' in c_clean.lower() or 'capa' in c_clean.lower() or 'max' in c_clean.lower():
                rename_map[c] = 'max_availability'
            elif 'cost/unit' in c_clean.lower() or 'cost/use' in c_clean.lower() or 'unit_cost' in c_clean.lower():
                rename_map[c] = 'unit_cost'
            elif 'overtime' in c_clean.lower() or 'multi' in c_clean.lower():
                rename_map[c] = 'overtime_multi'
        
        df = df.rename(columns=rename_map)
        df = df.loc[:, ~df.columns.duplicated()]

        # Ensure required columns exist
        if 'ID' not in df.columns:
            df['ID'] = range(1, len(df) + 1)
        if 'name' not in df.columns:
            df['name'] = [f"Resource_{i+1}" for i in range(len(df))]
        if 'type' not in df.columns:
            df['type'] = 'Machine'
        if 'max_availability' not in df.columns:
            df['max_availability'] = 1
        if 'unit_cost' not in df.columns:
            df['unit_cost'] = 0.0

        # 2. Classify Type (Human vs Machine)
        df['type'] = df.apply(lambda row: classify_type(row['name'], row['type']), axis=1)

        # 3. Clean max_availability to pure INTEGER (int)
        df['max_availability'] = df['max_availability'].apply(clean_int)

        # 4. Clean unit_cost to float
        df['unit_cost'] = df['unit_cost'].apply(clean_float)

        # 5. Add energy column: 0.25 * unit_cost for Machine, 0.0 for Human
        df['energy'] = df.apply(
            lambda row: round(0.25 * float(row['unit_cost']), 2) if row['type'] == 'Machine' else 0.0,
            axis=1
        )

        # 6. Add overtime_multi column: 1.5 for Human, 1.0 for Machine
        df['overtime_multi'] = df.apply(
            lambda row: 1.5 if row['type'] == 'Human' else 1.0,
            axis=1
        )

        # 7. Add max_overtime_per_day column: 4.0 for Human, 16.0 for Machine
        df['max_overtime_per_day'] = df.apply(
            lambda row: 4.0 if row['type'] == 'Human' else 16.0,
            axis=1
        )

        # Reorder standard 8 columns
        df = df[['ID', 'name', 'type', 'max_availability', 'unit_cost', 'energy', 'overtime_multi', 'max_overtime_per_day']]

        df.to_csv(file_path, index=False)
        print(f"[OK] Cleaned & Added max_overtime_per_day: {file_path}")
    except Exception as e:
        print(f"[ERROR] Error processing {file_path}: {e}")

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_files = glob.glob(os.path.join(repo_root, "**", "resources.csv"), recursive=True)
    print(f"Found {len(csv_files)} resources.csv files to standardize.")
    for f in csv_files:
        process_file(f)

if __name__ == "__main__":
    main()
