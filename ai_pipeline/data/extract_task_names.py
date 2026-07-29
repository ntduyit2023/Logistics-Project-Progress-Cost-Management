"""
GLPO Task Name Extractor & Processor
=====================================
Thư mục: ai_pipeline/data/extract_task_names.py

Chức năng:
  Trích xuất tên gốc (Original Task Names) của tất cả các công việc từ các tập tin .xlsx 
  trong ai_pipeline/data/raw/DSLIB/Excel/ và cập nhật lại tasks.csv cho 5 dự án tiêu chuẩn.
"""

import os
import sys
import glob
import pandas as pd
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

root_dir = Path(__file__).resolve().parent.parent.parent
excel_dir = root_dir / "ai_pipeline" / "data" / "raw" / "DSLIB" / "Excel"
processed_dir = root_dir / "ai_pipeline" / "data" / "processed"

# Mẫu tên file Excel tương ứng với 5 dự án
PROJECT_EXCEL_MAP = {
    "C2011-07": "C2011-07 Patient Transport System.xlsx",
    "C2012-04": "C2012-04 Asti-Cuneo Highway.xlsx",
    "C2012-08": "C2012-08 Sea Electricity.xlsx",
    "C2018-09": "C2018-09 CarSharing platform.xlsx",
    "C2019-16": "C2019-16 Lock Ganzepoot Excel.xlsx"
}


def extract_names_for_project(project_code: str, excel_filename: str):
    excel_path = excel_dir / excel_filename
    project_proc_dir = processed_dir / project_code
    tasks_csv_path = project_proc_dir / "tasks.csv"

    if not excel_path.exists():
        print(f"[WARNING] Không tìm thấy file Excel: {excel_path}")
        return

    if not tasks_csv_path.exists():
        print(f"[WARNING] Không tìm thấy tasks.csv: {tasks_csv_path}")
        return

    print(f"\n[EXTRACTOR] Đang trích xuất Tên Task cho: {project_code} ({excel_filename})...")

    # Đọc sheet 'Baseline Schedule'
    try:
        df_xl = pd.read_excel(excel_path, sheet_name='Baseline Schedule', header=None)
    except Exception as e:
        print(f"[ERROR] Không đọc được Excel {excel_filename}: {e}")
        return

    # Tìm hàng chứa từ khóa 'ID' và 'Name'
    header_row_idx = -1
    for r_idx in range(min(15, len(df_xl))):
        row_vals = [str(val).strip().lower() for val in df_xl.iloc[r_idx].values]
        if 'id' in row_vals and 'name' in row_vals:
            header_row_idx = r_idx
            id_col = row_vals.index('id')
            name_col = row_vals.index('name')
            break

    if header_row_idx == -1:
        # Mặc định cột 0 là ID, cột 1 là Name
        id_col, name_col = 0, 1
        header_row_idx = 1

    # Trích xuất dict: activity_id (int) -> task_name (str)
    id_name_map = {}
    for r_idx in range(header_row_idx + 1, len(df_xl)):
        raw_id = df_xl.iloc[r_idx, id_col]
        raw_name = df_xl.iloc[r_idx, name_col]

        if pd.notna(raw_id) and pd.notna(raw_name):
            try:
                act_id = int(raw_id)
                t_name = str(raw_name).strip()
                if act_id > 0 and t_name and t_name.lower() != 'nan':
                    id_name_map[act_id] = t_name
            except Exception:
                continue

    # Đọc tasks.csv hiện tại
    df_tasks = pd.read_csv(tasks_csv_path)

    # Cập nhật cột task_name theo mapping
    updated_count = 0
    new_task_names = []
    for idx, row in df_tasks.iterrows():
        t_id_str = str(row['task_id'])
        # task_id có dạng C2011-07_1, trích số đằng sau
        try:
            num_part = int(t_id_str.split('_')[-1])
            if num_part in id_name_map:
                new_task_names.append(id_name_map[num_part])
                updated_count += 1
            else:
                new_task_names.append(row.get('task_name', t_id_str))
        except Exception:
            new_task_names.append(row.get('task_name', t_id_str))

    df_tasks['task_name'] = new_task_names
    df_tasks.to_csv(tasks_csv_path, index=False)
    print(f"   ✓ Cập nhật thành công {updated_count}/{len(df_tasks)} Tên công việc gốc cho {project_code}!")


def main():
    print("================================================================================")
    print("[START] TRÍCH XUẤT TÊN CÔNG VIỆC GỐC TỪ FILE EXCEL BENCHMARK")
    print("================================================================================")
    for p_code, x_file in PROJECT_EXCEL_MAP.items():
        extract_names_for_project(p_code, x_file)
    print("\n================================================================================")
    print("[DONE] HOÀN TẤT TRÍCH XUẤT TÊN CÔNG VIỆC!")
    print("================================================================================")


if __name__ == "__main__":
    main()
