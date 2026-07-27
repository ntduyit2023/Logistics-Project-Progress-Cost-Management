"""
Script Tự Động Sinh và Nạp Dữ Liệu Thực Tế của 5 Dự Án vào database/init.sql
================================================================================
Thư mục: scripts/seed_database_init_sql.py

Chức năng:
    Quét qua cả 5 thư mục dự án trong ai_pipeline/data/processed/
    (C2011-07, C2012-04, C2012-08, C2018-09, C2019-16) và chuyển đổi dữ liệu thực tế
    thành các câu lệnh PostgreSQL INSERT INTO chuẩn vào file database/init.sql.
"""

import os
import sys
import glob
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

INIT_SQL_PATH = os.path.join("database", "init.sql")
PROCESSED_DIR = os.path.join("ai_pipeline", "data", "processed")


def sql_quote(val):
    if pd.isna(val) or val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    val_str = str(val).replace("'", "''")
    return f"'{val_str}'"


def generate_seed_sql():
    print(f"[START] Khởi động sinh dữ liệu SQL đồng bộ cho database/init.sql từ {PROCESSED_DIR}...")
    
    project_dirs = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*")))
    if not project_dirs:
        print("[ERROR] Không tìm thấy thư mục dự án nào trong ai_pipeline/data/processed!")
        return

    sql_lines = []
    sql_lines.append("\n-- ============================================================================")
    sql_lines.append("-- SEED DATA CHO 5 DỰ ÁN BENCHMARK (C2011-07, C2012-04, C2012-08, C2018-09, C2019-16)")
    sql_lines.append("-- ============================================================================\n")
    
    # Xóa dữ liệu cũ trong các bảng trước khi nạp
    sql_lines.append("TRUNCATE TABLE public.task_resources CASCADE;")
    sql_lines.append("TRUNCATE TABLE public.project_constraint_logic CASCADE;")
    sql_lines.append("TRUNCATE TABLE public.project_constraint_resource CASCADE;")
    sql_lines.append("TRUNCATE TABLE public.project_constraint_time CASCADE;")
    sql_lines.append("TRUNCATE TABLE public.tasks CASCADE;")
    sql_lines.append("TRUNCATE TABLE public.projects CASCADE;\n")

    proj_id_counter = 1
    
    for p_dir in project_dirs:
        p_code = os.path.basename(p_dir)
        info_file = os.path.join(p_dir, "project_info.csv")
        tasks_file = os.path.join(p_dir, "tasks.csv")
        preds_file = os.path.join(p_dir, "predecessors.csv")
        res_file = os.path.join(p_dir, "resources.csv")
        task_res_file = os.path.join(p_dir, "task_resources.csv")

        if not os.path.exists(tasks_file):
            continue

        p_name = p_code
        p_type = "PRO"
        base_cost = 0.0
        
        if os.path.exists(info_file):
            info_df = pd.read_csv(info_file)
            if not info_df.empty:
                row = info_df.iloc[0]
                p_name = str(row.get("project_name", p_code))
                p_type = str(row.get("type", "PRO"))
                base_cost = float(row.get("total_baseline_cost", row.get("base_cost", 0.0)))

        tasks_df = pd.read_csv(tasks_file)
        num_tasks = len(tasks_df)
        
        preds_df = pd.read_csv(preds_file) if os.path.exists(preds_file) else pd.DataFrame()
        num_edges = len(preds_df)

        if base_cost <= 0.0 and not tasks_df.empty:
            base_cost = float(tasks_df.get('base_cost', tasks_df.get('total_cost', 0.0)).sum())

        # 1. INSERT INTO projects
        p_sql = f"""INSERT INTO public.projects (id, user_id, project_name, type, status, base_cost, total_cost, num_tasks, num_edges, metadata_json)
VALUES ({proj_id_counter}, NULL, '{p_name} ({p_code})', '{p_type}', 'Planning', {base_cost:.2f}, {base_cost:.2f}, {num_tasks}, {num_edges}, '{{"project_code": "{p_code}"}}');"""
        sql_lines.append(p_sql)

        # 2. INSERT INTO project_constraint_time
        time_sql = f"""INSERT INTO public.project_constraint_time (project_id, weekly_schedule, holidays_list, overtime_multiplier)
VALUES ({proj_id_counter}, '{{"working_days": [0,1,2,3,4], "hours_per_day": 8.0}}', '[]', 1.50);"""
        sql_lines.append(time_sql)

        # 3. INSERT INTO project_constraint_resource
        res_id_map = {}
        res_counter = (proj_id_counter * 1000) + 1
        if os.path.exists(res_file):
            res_df = pd.read_csv(res_file)
            for _, r in res_df.iterrows():
                r_name = str(r.get('resource_name', r.get('Name', r.get('id', 'Res'))))
                r_type = str(r.get('resource_type', r.get('Type', 'Renewable')))
                avail = float(r.get('max_availability', r.get('Availability', 1.0)))
                r_cost = float(r.get('cost_per_unit', r.get('cost', 0.0)))
                
                r_sql = f"""INSERT INTO public.project_constraint_resource (id, project_id, resource_name, resource_type, max_availability, cost_per_unit)
VALUES ({res_counter}, {proj_id_counter}, '{r_name}', '{r_type}', {avail:.2f}, {r_cost:.2f});"""
                sql_lines.append(r_sql)
                res_id_map[r_name] = res_counter
                res_counter += 1

        # 4. INSERT INTO tasks
        for _, t in tasks_df.iterrows():
            t_id = str(t.get('task_id', t.get('id', '')))
            t_name = str(t.get('task_name', t_id)).replace("'", "''")
            dur_h = float(t.get('duration_hours', t.get('duration', 8.0)))
            t_cost = float(t.get('total_cost', t.get('base_cost', 0.0)))
            labor = float(t.get('labor', 0.0))
            ot = float(t.get('overtime', 0.0))
            equip = float(t.get('equipment', 0.0))
            mat = float(t.get('material', 0.0))

            t_sql = f"""INSERT INTO public.tasks (id, project_id, task_name, status, base_cost, total_cost, duration_hours, labor, overtime, equipment, material)
VALUES ('{t_id}', {proj_id_counter}, '{t_name}', 'Pending', {t_cost:.2f}, {t_cost:.2f}, {dur_h:.2f}, {labor:.2f}, {ot:.2f}, {equip:.2f}, {mat:.2f});"""
            sql_lines.append(t_sql)

        # 5. INSERT INTO project_constraint_logic
        if not preds_df.empty:
            for _, pr in preds_df.iterrows():
                p_pred = str(pr.get('predecessor_id', pr.get('pred', ''))).strip()
                p_succ = str(pr.get('successor_id', pr.get('succ', ''))).strip()
                if not p_pred or not p_succ or p_pred.lower() == 'nan' or p_succ.lower() == 'nan':
                    continue
                p_lag = float(pr.get('lag_hours', 0.0))
                
                logic_sql = f"""INSERT INTO public.project_constraint_logic (predecessor_id, successor_id, project_id, dependency_type, lag_hours)
VALUES ('{p_pred}', '{p_succ}', {proj_id_counter}, 'FS', {p_lag:.2f});"""
                sql_lines.append(logic_sql)

        # 6. INSERT INTO task_resources
        if os.path.exists(task_res_file):
            tr_df = pd.read_csv(task_res_file)
            for _, tr in tr_df.iterrows():
                tr_t = str(tr.get('task_id', ''))
                tr_r_name = str(tr.get('role', tr.get('resource_id', '')))
                tr_qty = float(tr.get('quantity', tr.get('request_quantity', 1.0)))
                r_db_id = res_id_map.get(tr_r_name, res_counter)
                
                tr_sql = f"""INSERT INTO public.task_resources (task_id, resource_id, request_quantity, allocated_quantity)
VALUES ('{tr_t}', {r_db_id}, {tr_qty:.2f}, {tr_qty:.2f}) ON CONFLICT DO NOTHING;"""
                sql_lines.append(tr_sql)

        print(f"   * Đã sinh dữ liệu SQL thành công cho dự án [{proj_id_counter}] {p_code} ({num_tasks} tasks, {num_edges} edges).")
        proj_id_counter += 1

    # Đọc init.sql hiện tại và nối phần seed data mới vào
    with open(INIT_SQL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Tìm vị trí bắt đầu phần SEED DATA cũ nếu có, hoặc nối vào cuối file
    marker = "-- SEED DATA CHO 5 DỰ ÁN BENCHMARK"
    if marker in content:
        base_content = content.split(marker)[0].rstrip()
    else:
        base_content = content.rstrip()

    new_full_sql = base_content + "\n\n" + "\n".join(sql_lines) + "\n"
    
    with open(INIT_SQL_PATH, "w", encoding="utf-8") as f:
        f.write(new_full_sql)

    print(f"\n[SUCCESS] Đã cập nhật thành công {INIT_SQL_PATH}! Dữ liệu 5 dự án đã được đồng bộ 100%.")


if __name__ == "__main__":
    generate_seed_sql()
