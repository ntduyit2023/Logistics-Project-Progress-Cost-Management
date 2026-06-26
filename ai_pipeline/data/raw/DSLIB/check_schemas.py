import os
import pandas as pd

path = r'e:\University\Year 3-3\DA3\ai_pipeline\data\raw\DSLIB\Excel'
files = [f for f in os.listdir(path) if f.endswith('.xlsx')]

# Lấy 1 file đại diện cho mỗi năm (C2011, C2012, C2013...)
years = {}
for f in files:
    year_prefix = f[:5] # e.g. "C2011"
    if year_prefix not in years:
        years[year_prefix] = f

print("--- KIỂM TRA SCHEMA FILE THEO NĂM ---")
for y, f in years.items():
    file_path = os.path.join(path, f)
    try:
        xl = pd.ExcelFile(file_path)
        sheets = xl.sheet_names
        print(f"\n[{y}] File: {f}")
        print(f"Sheets: {sheets}")
        
        if 'Baseline Schedule' in sheets:
            df = pd.read_excel(xl, sheet_name='Baseline Schedule', header=[0,1], nrows=1)
            columns = df.columns.tolist()
            # In ra các cột nhóm (Group) để xem cấu trúc
            groups = set([col[0] for col in columns if isinstance(col, tuple)])
            print(f"Baseline Groups: {groups}")
            # Lấy 1 số cột điển hình xem có bị đổi tên không
            col_names = [col[1] for col in columns if isinstance(col, tuple)]
            print(f"Baseline Columns (Count={len(col_names)}): {col_names[:5]} ... {col_names[-5:]}")
        else:
            print("NO 'Baseline Schedule' SHEET!")
            
    except Exception as e:
        print(f"Lỗi đọc file {f}: {e}")
