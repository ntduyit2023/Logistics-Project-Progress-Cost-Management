import os
import glob
import pandas as pd
import re
import sys
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../data/raw/DSLIB/Excel/"))
PROCESSED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../data/processed/"))

def main():
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    excel_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.xlsx"))
    print(f"[ETL Cleaner] Bat dau lam sach (Clean) va dong goi {len(excel_files)} du an.\n")
    
    project_id_counter = 1
    
    for file_path in excel_files:
        project_name = os.path.basename(file_path).replace('.xlsx', '')
        project_dir = os.path.join(PROCESSED_DIR, project_name)
        
        # Luôn ghi đè để Clean dữ liệu cũ
        os.makedirs(project_dir, exist_ok=True)
        print(f"-> Dang lam sach Do thi: {project_name}")
        
        try:
            xl = pd.ExcelFile(file_path)
            
            # 1. Đọc Baseline Schedule
            df_baseline = pd.read_excel(xl, sheet_name='Baseline Schedule', header=1)
            
            # 2. Đọc Risk Analysis
            df_risk = pd.DataFrame()
            if 'Risk Analysis' in xl.sheet_names:
                df_risk = pd.read_excel(xl, sheet_name='Risk Analysis', header=1)
                if 'ID' in df_risk.columns:
                    df_risk['ID'] = df_risk['ID'].astype(str)
                
            # 3. Đọc Agenda (Header=None vì Protrack không có header cho sheet này)
            if 'Agenda' in xl.sheet_names:
                df_agenda = pd.read_excel(xl, sheet_name='Agenda', header=None)
                
                working_hours = []
                working_days = []
                
                for _, r in df_agenda.iterrows():
                    # Cột 0, 1: Giờ làm việc (Ví dụ: "8:00 - 9:00" | "Yes")
                    if pd.notna(r.iloc[0]) and len(r) > 1 and pd.notna(r.iloc[1]) and str(r.iloc[1]).strip() == 'Yes':
                        working_hours.append(str(r.iloc[0]))
                    
                    # Cột 3, 4: Ngày làm việc (Ví dụ: "Monday" | "Yes")
                    if len(r) > 4 and pd.notna(r.iloc[3]) and pd.notna(r.iloc[4]) and str(r.iloc[4]).strip() == 'Yes':
                        working_days.append(str(r.iloc[3]))
                        
                # Lưu dưới định dạng JSON siêu sạch thay vì CSV rác
                with open(os.path.join(project_dir, "calendar.json"), 'w', encoding='utf-8') as f:
                    json.dump({
                        "working_hours": working_hours,
                        "working_days": working_days
                    }, f, indent=4)
                    
            nodes = []
            edges = []
            valid_tasks = set()
            
            for idx, row in df_baseline.iterrows():
                task_id = str(row.get('ID', ''))
                if pd.isna(task_id) or str(task_id).strip() == '':
                    continue
                    
                start_time = str(row.get('Baseline Start', '')).strip()
                end_time = str(row.get('Baseline End', '')).strip()
                
                # [CLEANING 1]: Lọc bỏ WBS Summary Tasks (Dấu hiệu: Không có Baseline Start)
                if start_time == 'nan' or start_time == 'NaT' or start_time == '':
                    continue 
                    
                valid_tasks.add(task_id)
                    
                task_name = str(row.get('Name', f"Task_{task_id}"))
                wbs = str(row.get('WBS', ''))
                duration_raw = str(row.get('Baseline duration (in calendar days)', row.get('Duration', 0)))
                
                # [CLEANING 2]: Bắt số thập phân (float) thay vì ép int
                dur_match = re.findall(r'\d+\.?\d*', duration_raw)
                duration = float(dur_match[0]) if dur_match else 0.0
                
                resource_demand = row.get('Resource Demand', '')
                total_cost = row.get('Total Cost', 0)
                
                # Lấy dữ liệu rủi ro (Nếu có)
                opt_time = duration
                pess_time = duration
                if not df_risk.empty and 'ID' in df_risk.columns:
                    risk_row = df_risk[df_risk['ID'] == task_id]
                    if not risk_row.empty:
                        opt_pct = risk_row.iloc[0].get('Optimistic (%)')
                        pess_pct = risk_row.iloc[0].get('Pessimistic (%)')
                        
                        # Backup nếu cột bị thiếu %
                        if pd.isna(opt_pct): opt_pct = risk_row.iloc[0].get('Optimistic', 100)
                        if pd.isna(pess_pct): pess_pct = risk_row.iloc[0].get('Pessimistic', 100)
                        
                        try:
                            if pd.notna(opt_pct): opt_time = round(duration * float(opt_pct) / 100.0, 2)
                            if pd.notna(pess_pct): pess_time = round(duration * float(pess_pct) / 100.0, 2)
                        except (ValueError, TypeError):
                            pass
                
                nodes.append({
                    "node_id": task_id,
                    "wbs": wbs,
                    "task_name": task_name,
                    "duration": duration,
                    "optimistic_time": opt_time,
                    "pessimistic_time": pess_time,
                    "baseline_start": start_time,
                    "baseline_end": end_time,
                    "resource_demand": resource_demand,
                    "total_cost": total_cost
                })
                
                # 4. Trích xuất Cạnh
                preds = row.get('Predecessors', '')
                if not pd.isna(preds) and str(preds).strip() != '':
                    pred_list = str(preds).split(',')
                    for p in pred_list:
                        num_matches = re.findall(r'\d+', p)
                        if num_matches:
                            pred_id = num_matches[0]
                            edges.append({
                                "source": pred_id,
                                "target": task_id,
                                "type": "FS"
                            })
                            
            # [CLEANING 3]: Lọc bỏ các Cạnh mồ côi (Nối vào WBS Summary)
            clean_edges = [e for e in edges if e["source"] in valid_tasks and e["target"] in valid_tasks]
            
            # Ghi đè file mới
            pd.DataFrame(nodes).to_csv(os.path.join(project_dir, "nodes.csv"), index=False)
            pd.DataFrame(clean_edges).to_csv(os.path.join(project_dir, "edges.csv"), index=False)
            
            # Xóa file calendar.csv cũ nếu còn sót lại
            old_cal = os.path.join(project_dir, "calendar.csv")
            if os.path.exists(old_cal): os.remove(old_cal)
            
        except Exception as e:
            print(f"   [Loi] Loi khi lam sach {project_name}: {e}")
            
        project_id_counter += 1

    print(f"\n[HOAN TAT] Data Cleaning thanh cong cho {project_id_counter - 1} du an!")

if __name__ == "__main__":
    main()
