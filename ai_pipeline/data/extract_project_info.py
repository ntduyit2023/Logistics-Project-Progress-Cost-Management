import os
import pandas as pd
import glob
import cost_model

def extract_project_info(excel_path, processed_dir, project_id, project_name, project_type):
    print(f"Processing project info for {project_id}...")
    
    # 1. Agenda Info from Raw Excel
    df_agenda = pd.read_excel(excel_path, sheet_name='Agenda')
    hours_per_day = len(df_agenda[df_agenda['Unnamed: 1'] == 'Yes'])
    days_per_week = len(df_agenda[df_agenda['Unnamed: 4'] == 'Yes'])
    if hours_per_day == 0: hours_per_day = 8
    if days_per_week == 0: days_per_week = 5
    
    # 2. Extract Data from Processed CSVs
    tasks_csv_path = os.path.join(processed_dir, 'tasks.csv')
    schedules_csv_path = os.path.join(processed_dir, 'task_schedules.csv')
    
    df_tasks = pd.read_csv(tasks_csv_path)
    
    # Extract Resources data for Cost Model
    resources_csv_path = os.path.join(processed_dir, 'task_resources.csv')
    if os.path.exists(resources_csv_path):
        df_resources = pd.read_csv(resources_csv_path)
    else:
        df_resources = pd.DataFrame()
    
    # Calculate Total Effort Hours (Sum of g7_dur_hours)
    total_effort_hours = df_tasks['g7_dur_hours'].sum()
    
    # 3. Extract Schedule data for Calendar Hours
    schedules_csv_path = os.path.join(processed_dir, 'task_schedules.csv')
    if os.path.exists(schedules_csv_path):
        df_schedules = pd.read_csv(schedules_csv_path)
    else:
        df_schedules = pd.DataFrame()
    
    import numpy as np
    
    project_calendar_days = 0.0
    project_working_hours = 0.0
    proj_start_date = None
    if not df_schedules.empty and 'baseline_start' in df_schedules.columns and 'baseline_end' in df_schedules.columns:
        # Parse dates
        start_dates = pd.to_datetime(df_schedules['baseline_start'], errors='coerce')
        end_dates = pd.to_datetime(df_schedules['baseline_end'], errors='coerce')
        
        valid_starts = start_dates.dropna()
        valid_ends = end_dates.dropna()
        
        if not valid_starts.empty and not valid_ends.empty:
            min_start = valid_starts.min()
            max_end = valid_ends.max()
            proj_start_date = min_start
            calendar_duration = max_end - min_start
            
            # 1. Calendar Days
            project_calendar_days = calendar_duration.total_seconds() / (24 * 3600.0)
            
            # 2. Working Hours (assuming Mon-Fri working days)
            # np.busday_count returns the number of valid days between dates
            # We take the date part for busday_count
            working_days = np.busday_count(min_start.date(), max_end.date())
            # Add 1 if the end date is also a working day and we want inclusive, 
            # but usually MS Project includes fractional days based on time. 
            # For a rough exact working hours estimation:
            project_working_hours = float(working_days) * hours_per_day
    
    # Calculate Total Costs dynamically using the Cost Model
    total_baseline_cost, total_final_cost = cost_model.calculate_project_totals(df_tasks, df_resources, project_type)
            
    # Build dictionary
    project_info = {
        "project_id": project_id,
        "project_name": project_name,
        "project_type": project_type,
        "working_hours_per_day": hours_per_day,
        "working_days_per_week": days_per_week,
        "project_start": str(proj_start_date) if proj_start_date else None,
        "total_effort_hours": total_effort_hours,
        "project_calendar_days": project_calendar_days,
        "project_working_hours": project_working_hours,
        "total_baseline_cost": total_baseline_cost,
        "total_final_cost": total_final_cost
    }
    
    # Save to CSV
    os.makedirs(processed_dir, exist_ok=True)
    out_file = os.path.join(processed_dir, "project_info.csv")
    pd.DataFrame([project_info]).to_csv(out_file, index=False, encoding='utf-8')
    print(f"Saved {out_file}")
    
    return project_info

if __name__ == "__main__":
    projects = [
        {
            "id": "C2011-07",
            "name": "Patient Transport System",
            "type": "PRO",
            "file": r"E:\University\Year 3 - 3\DA3\ai_pipeline\data\raw\DSLIB\Excel\C2011-07 Patient Transport System.xlsx"
        },
        {
            "id": "C2012-04",
            "name": "Asti-Cuneo Highway",
            "type": "CON",
            "file": r"E:\University\Year 3 - 3\DA3\ai_pipeline\data\raw\DSLIB\Excel\C2012-04 Asti-Cuneo Highway.xlsx"
        },
        {
            "id": "C2012-08",
            "name": "Sea Electricity",
            "type": "CON",
            "file": r"E:\University\Year 3 - 3\DA3\ai_pipeline\data\raw\DSLIB\Excel\C2012-08 Sea Electricity.xlsx"
        },
        {
            "id": "C2018-09",
            "name": "CarSharing platform",
            "type": "ITLG",
            "file": r"E:\University\Year 3 - 3\DA3\ai_pipeline\data\raw\DSLIB\Excel\C2018-09 CarSharing platform.xlsx"
        },
        {
            "id": "C2019-16",
            "name": "Lock Ganzepoot Ypres",
            "type": "CON",
            "file": r"E:\University\Year 3 - 3\DA3\ai_pipeline\data\raw\DSLIB\Excel\C2019-16 Lock Ganzepoot Excel.xlsx"
        }
    ]
    
    for p in projects:
        processed_dir = fr"E:\University\Year 3 - 3\DA3\ai_pipeline\data\processed\{p['id']}"
        info = extract_project_info(
            excel_path=p['file'],
            processed_dir=processed_dir,
            project_id=p['id'],
            project_name=p['name'],
            project_type=p['type']
        )
        print(f"Extracted {p['id']}: Cost = {info['total_baseline_cost']}")
