import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
excel_dir = os.path.join(script_dir, "raw", "DSLIB", "Excel")

projects = {
    "C2011-07": "C2011-07 Patient Transport System.xlsx",
    "C2012-04": "C2012-04 Asti-Cuneo Highway.xlsx",
    "C2012-08": "C2012-08 Sea Electricity.xlsx",
    "C2018-09": "C2018-09 CarSharing platform.xlsx",
    "C2019-16": "C2019-16 Lock Ganzepoot Excel.xlsx"
}

for pid, filename in projects.items():
    filepath = os.path.join(excel_dir, filename)
    print("=" * 80)
    print(f"PROJECT: {pid} - {filename}")
    print("=" * 80)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
    
    try:
        xl = pd.ExcelFile(filepath)
        print(f"Sheet names: {xl.sheet_names}")
        
        for sheet in xl.sheet_names:
            if sheet in ['Baseline Schedule', 'Resources', 'Agenda', 'Risk Analysis', 'Risk']:
                print(f"\n--- Sheet: '{sheet}' ---")
                df = xl.parse(sheet, nrows=5)
                print(f"Columns: {df.columns.tolist()}")
                print("First 3 rows:")
                print(df.head(3))
    except Exception as e:
        print(f"Error reading {pid}: {e}")
