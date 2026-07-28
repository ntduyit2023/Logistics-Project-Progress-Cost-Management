"""
Script Chuẩn Hóa Toàn Bộ Dataset Dự Án Benchmark (Standardize Entire Benchmark Datasets)
===========================================================================================
Thực hiện 5 tác vụ chuẩn hóa:
1. Tạo agenda.json từ 3 file agenda cũ (xóa 3 file cũ).
2. Chuẩn hóa project_info.csv giữ project_id, project_name, project_type, penalty_per_day, bonus_per_day.
3. Tinh gọn tasks.csv: Quy đổi duration về duration_hours theo Lịch Agenda, giữ 38 cột chi phí chuẩn, xóa các trường thừa.
4. Tinh gọn predecessors.csv về 4 cột: predecessor_id, successor_id, dependency_type, lag_hours.
5. Tinh gọn task_resources.csv về 3 cột: task_id, resource_id, request_quantity. Xóa file rác task_schedules.csv.
"""

import os
import json
import pandas as pd
import numpy as np

BASE_DATA_DIR = r"e:\University\Year 3 - 3\DA3\ai_pipeline\data\processed"
PROJECT_FOLDERS = ["C2011-07", "C2012-04", "C2012-08", "C2018-09", "C2019-16"]

COST_COLUMNS = [
    'labor', 'material', 'equipment', 'energy', 'testing_inspection', 'project_management',
    'facility', 'utilities', 'communication', 'training', 'quality_management',
    'overtime', 'delay_penalty', 'inventory_holding', 'waiting_cost', 'idle_resource', 'revenue_delay', 'expediting',
    'insurance', 'rework', 'warranty', 'litigation', 'regulatory_compliance', 'contingency_reserve', 'management_reserve',
    'transportation', 'ordering', 'packaging', 'reverse_logistics', 'customs', 'supplier_coordination',
    'opportunity_cost', 'capital_cost', 'financing_cost', 'npv_loss', 'esg_cost', 'carbon_tax', 'reputation_cost'
]

ALIASES = {
    'labor': ['internal_labor_cost', 'labor'],
    'material': ['material_cost', 'material'],
    'equipment': ['equipment_fuel_cost', 'equipment'],
    'testing_inspection': ['qa_qc_cost', 'testing_inspection'],
    'facility': ['facility_rent', 'facility'],
    'utilities': ['utilities_cost', 'utilities'],
    'communication': ['communication_cost', 'communication'],
    'training': ['training_cost', 'training'],
    'overtime': ['overtime_cost', 'overtime'],
    'inventory_holding': ['holding_cost', 'inventory_holding'],
    'insurance': ['insurance_cost', 'insurance'],
    'warranty': ['warranty_cost', 'warranty'],
    'regulatory_compliance': ['licensing_cost', 'regulatory_compliance'],
    'transportation': ['international_freight', 'transportation']
}

def standardize_project(proj_dir: str):
    proj_id = os.path.basename(os.path.normpath(proj_dir))
    print(f"\n==========================================")
    print(f"🔄 ĐANG CHUẨN HÓA PROJECT: {proj_id}")
    print(f"==========================================")

    # ----------------------------------------------------
    # 1. XỬ LÝ LỊCH AGENDA ➔ agenda.json
    # ----------------------------------------------------
    working_days_path = os.path.join(proj_dir, "agenda_working_days.csv")
    working_hours_path = os.path.join(proj_dir, "agenda_working_hours.csv")
    holidays_path = os.path.join(proj_dir, "agenda_holidays.csv")

    hours_per_day = 8.0
    if os.path.exists(working_hours_path):
        try:
            wh_df = pd.read_csv(working_hours_path)
            if 'Working' in wh_df.columns:
                working_slots = wh_df[wh_df['Working'].astype(str).str.upper().isin(['YES', 'TRUE', '1'])]
                if len(working_slots) > 0:
                    hours_per_day = float(len(working_slots))
        except Exception as e:
            print(f"   ⚠️ Lỗi đọc working_hours: {e}")

    days_per_week = 5.0
    weekly_schedule = {}
    day_name_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}

    if os.path.exists(working_days_path):
        try:
            wd_df = pd.read_csv(working_days_path)
            active_days = 0
            for _, row in wd_df.iterrows():
                d_name = str(row.get('Day', '')).strip()
                is_work = str(row.get('Working', '')).strip().upper() in ['YES', 'TRUE', '1']
                if d_name in day_name_map:
                    idx = day_name_map[d_name]
                    if is_work:
                        active_days += 1
                        weekly_schedule[d_name] = {
                            "is_working": True,
                            "shifts": [
                                {"start_time": "08:00", "end_time": "12:00", "hours": round(hours_per_day / 2, 1)},
                                {"start_time": "13:00", "end_time": f"{13 + int(hours_per_day / 2)}:00", "hours": round(hours_per_day / 2, 1)}
                            ]
                        }
                    else:
                        weekly_schedule[d_name] = {"is_working": False, "shifts": []}
            if active_days > 0:
                days_per_week = float(active_days)
        except Exception as e:
            print(f"   ⚠️ Lỗi đọc working_days: {e}")

    # Fallback weekly schedule if empty
    if not weekly_schedule:
        for d_name, idx in day_name_map.items():
            if idx < 5:
                weekly_schedule[d_name] = {
                    "is_working": True,
                    "shifts": [
                        {"start_time": "08:00", "end_time": "12:00", "hours": 4.0},
                        {"start_time": "13:00", "end_time": "17:00", "hours": 4.0}
                    ]
                }
            else:
                weekly_schedule[d_name] = {"is_working": False, "shifts": []}

    holidays_list = []
    if os.path.exists(holidays_path):
        try:
            h_df = pd.read_csv(holidays_path)
            col = h_df.columns[0]
            holidays_list = [str(val).strip() for val in h_df[col].dropna().tolist() if str(val).strip()]
        except Exception as e:
            print(f"   ⚠️ Lỗi đọc holidays: {e}")

    agenda_json_data = {
        "project_id": proj_id,
        "weekly_schedule": weekly_schedule,
        "holidays_list": holidays_list
    }

    agenda_json_path = os.path.join(proj_dir, "agenda.json")
    with open(agenda_json_path, 'w', encoding='utf-8') as f:
        json.dump(agenda_json_data, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Đã tạo file agenda.json ({hours_per_day}h/ngày, {days_per_week} ngày/tuần, {len(holidays_list)} ngày lễ)")

    # Xóa 3 file agenda cũ
    for old_file in [working_days_path, working_hours_path, holidays_path]:
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
                print(f"   🗑️ Đã xóa file rác cũ: {os.path.basename(old_file)}")
            except Exception:
                pass

    # ----------------------------------------------------
    # 2. CHUẨN HÓA project_info.csv
    # ----------------------------------------------------
    proj_info_path = os.path.join(proj_dir, "project_info.csv")
    proj_name = f"Project {proj_id}"
    proj_type = "ITLG"
    penalty_per_day = 500.0
    bonus_per_day = 200.0

    if os.path.exists(proj_info_path):
        try:
            pi_df = pd.read_csv(proj_info_path)
            if not pi_df.empty:
                proj_name = str(pi_df.get('project_name', [proj_name])[0] or proj_name)
                proj_type = str(pi_df.get('project_type', ['ITLG'])[0] or 'ITLG')
                penalty_per_day = float(pi_df.get('penalty_per_day', [500.0])[0] or 500.0)
                bonus_per_day = float(pi_df.get('bonus_per_day', [200.0])[0] or 200.0)
        except Exception as e:
            print(f"   ⚠️ Lỗi đọc project_info: {e}")

    clean_proj_info = pd.DataFrame([{
        'project_id': proj_id,
        'project_name': proj_name,
        'project_type': proj_type,
        'penalty_per_day': penalty_per_day,
        'bonus_per_day': bonus_per_day
    }])
    clean_proj_info.to_csv(proj_info_path, index=False)
    print(f"   ✅ Đã chuẩn hóa project_info.csv (Giữ project_type: '{proj_type}')")

    # ----------------------------------------------------
    # 3. CHUẨN HÓA tasks.csv
    # ----------------------------------------------------
    tasks_path = os.path.join(proj_dir, "tasks.csv")
    if os.path.exists(tasks_path):
        tasks_df = pd.read_csv(tasks_path)
        clean_tasks = []

        hours_per_week = days_per_week * hours_per_day
        hours_per_month = 4.0 * hours_per_week

        for _, row in tasks_df.iterrows():
            t_id = str(row.get('id', row.get('task_id', '')))
            b_start = str(row.get('baseline_start', '2026-01-01 08:00:00'))

            d_m = float(row.get('duration_months', 0.0) or 0.0)
            d_w = float(row.get('duration_weeks', 0.0) or 0.0)
            d_d = float(row.get('duration_days', 0.0) or 0.0)
            d_h = float(row.get('duration_hours', row.get('duration', 0.0)) or 0.0)

            # Quy đổi duration chuẩn theo Agenda
            total_dur_hours = round(d_m * hours_per_month + d_w * hours_per_week + d_d * hours_per_day + d_h, 2)
            if total_dur_hours <= 0.0:
                total_dur_hours = 8.0

            task_dict = {
                'task_id': t_id,
                'baseline_start': b_start,
                'duration_hours': total_dur_hours
            }

            # Nạp 38 cột chi phí chuẩn
            for col in COST_COLUMNS:
                val = 0.0
                possible_names = ALIASES.get(col, [col])
                for pname in possible_names:
                    if pname in row and pd.notna(row[pname]):
                        try:
                            val = float(row[pname])
                            break
                        except (ValueError, TypeError):
                            pass
                task_dict[col] = val

            clean_tasks.append(task_dict)

        clean_tasks_df = pd.DataFrame(clean_tasks)
        clean_tasks_df.to_csv(tasks_path, index=False)
        print(f"   ✅ Đã chuẩn hóa tasks.csv ({len(clean_tasks_df)} tasks, quy đổi duration_hours theo Agenda)")

    # ----------------------------------------------------
    # 4. CHUẨN HÓA predecessors.csv ➔ logic.csv
    # ----------------------------------------------------
    preds_path = os.path.join(proj_dir, "predecessors.csv")
    logic_path = os.path.join(proj_dir, "logic.csv")
    
    target_preds_file = preds_path if os.path.exists(preds_path) else (logic_path if os.path.exists(logic_path) else None)

    if target_preds_file:
        preds_df = pd.read_csv(target_preds_file)
        clean_preds = []

        hours_per_week = days_per_week * hours_per_day
        hours_per_month = 4.0 * hours_per_week

        for _, row in preds_df.iterrows():
            p_id = str(row.get('predecessor_id', row.get('source_id', row.get('predecessor_task_id', ''))))
            s_id = str(row.get('successor_id', row.get('target_id', row.get('successor_task_id', ''))))
            dep_type = str(row.get('dependency_type', 'FS')).upper()

            l_m = float(row.get('lag_months', 0.0) or 0.0)
            l_w = float(row.get('lag_weeks', 0.0) or 0.0)
            l_d = float(row.get('lag_days', 0.0) or 0.0)
            l_h = float(row.get('lag_hours', 0.0) or 0.0)

            total_lag_hours = round(l_m * hours_per_month + l_w * hours_per_week + l_d * hours_per_day + l_h, 2)

            clean_preds.append({
                'predecessor_id': p_id,
                'successor_id': s_id,
                'dependency_type': dep_type,
                'lag_hours': total_lag_hours
            })

        clean_preds_df = pd.DataFrame(clean_preds)
        clean_preds_df.to_csv(logic_path, index=False)
        print(f"   ✅ Đã chuẩn hóa và đổi tên ➔ logic.csv ({len(clean_preds_df)} quan hệ mối nối)")

        # Xóa file predecessors.csv cũ nếu tồn tại
        if os.path.exists(preds_path) and preds_path != logic_path:
            try:
                os.remove(preds_path)
                print(f"   🗑️ Đã xóa file predecessors.csv cũ")
            except Exception:
                pass

    # Xóa file project_meta.json nếu có
    pm_path = os.path.join(proj_dir, "project_meta.json")
    if os.path.exists(pm_path):
        try:
            os.remove(pm_path)
            print(f"   🗑️ Đã xóa file rác project_meta.json")
        except Exception:
            pass

    # ----------------------------------------------------
    # 5. CHUẨN HÓA task_resources.csv & XÓA task_schedules.csv
    # ----------------------------------------------------
    task_res_path = os.path.join(proj_dir, "task_resources.csv")
    if os.path.exists(task_res_path):
        tr_df = pd.read_csv(task_res_path)
        clean_tr = []
        for _, row in tr_df.iterrows():
            t_id = str(row.get('task_id', ''))
            r_id = str(row.get('resource_id', row.get('role', '')))
            qty = float(row.get('request_quantity', row.get('quantity', 1.0)) or 1.0)
            clean_tr.append({
                'task_id': t_id,
                'resource_id': r_id,
                'request_quantity': qty
            })
        clean_tr_df = pd.DataFrame(clean_tr)
        clean_tr_df.to_csv(task_res_path, index=False)
        print(f"   ✅ Đã chuẩn hóa task_resources.csv ({len(clean_tr_df)} phân bổ tài nguyên)")

    # Xóa file rác task_schedules.csv nếu có
    ts_path = os.path.join(proj_dir, "task_schedules.csv")
    if os.path.exists(ts_path):
        try:
            os.remove(ts_path)
            print(f"   🗑️ Đã xóa file rác task_schedules.csv")
        except Exception:
            pass

def main():
    print("=== BAT DAU CHUAN HOA DATASET 5 DU AN BENCHMARK ===")
    for proj_folder in PROJECT_FOLDERS:
        p_path = os.path.join(BASE_DATA_DIR, proj_folder)
        if os.path.exists(p_path):
            standardize_project(p_path)
    print("\n=== THANH CONG! DA CHUAN HOA TOAN BO DATASET VET CAU TRUC TIEU CHUAN ===")

if __name__ == "__main__":
    main()
