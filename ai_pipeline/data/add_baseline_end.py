import os
import glob
import json
import pandas as pd
import sys

# Ensure ai_pipeline is importable
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(script_dir, '..', '..')))

from ai_pipeline.models.moi.domain_normalizers import WorkingCalendarEngine

def run():
    processed_dir = os.path.join(script_dir, 'processed')
    projects = [d for d in os.listdir(processed_dir) if os.path.isdir(os.path.join(processed_dir, d))]
    
    for proj_id in projects:
        proj_dir = os.path.join(processed_dir, proj_id)
        tasks_csv = os.path.join(proj_dir, 'tasks.csv')
        agenda_json = os.path.join(proj_dir, 'agenda.json')
        
        if not os.path.exists(tasks_csv) or not os.path.exists(agenda_json):
            continue
            
        print(f"Adding baseline_end for {proj_id}...")
        
        with open(agenda_json, 'r', encoding='utf-8') as f:
            agenda = json.load(f)
            
        weekly_schedule = agenda.get('weekly_schedule', {})
        calendar_engine = WorkingCalendarEngine(weekly_schedule=weekly_schedule)
        
        df = pd.read_csv(tasks_csv)
        
        # Calculate baseline_end
        baseline_ends = []
        for _, row in df.iterrows():
            b_start = row.get('baseline_start')
            dur_h = float(row.get('duration_hours', 0.0))
            
            b_end = ""
            if pd.notna(b_start) and str(b_start).strip():
                try:
                    dt_end = calendar_engine.add_working_hours(str(b_start).strip(), dur_h)
                    b_end = dt_end.strftime('%Y-%m-%dT%H:%M:%S')
                except Exception:
                    pass
            baseline_ends.append(b_end)
            
        # Insert baseline_end right after baseline_start
        if 'baseline_end' in df.columns:
            df['baseline_end'] = baseline_ends
        else:
            col_idx = df.columns.get_loc('baseline_start') + 1
            df.insert(col_idx, 'baseline_end', baseline_ends)
            
        # Save back safely
        df.to_csv(tasks_csv, index=False, encoding='utf-8')
        print(f" -> Updated {tasks_csv}")

if __name__ == '__main__':
    run()
