import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import glob
import json
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

def parse_pg_date(d):
    if pd.isna(d) or str(d).strip() in ['NaT', 'NaN', 'None', '']: return None
    try:
        dt = pd.to_datetime(d, dayfirst=True, format='mixed', errors='coerce')
        return dt.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(dt) else None
    except:
        return None

def main():
    print("Đang kết nối tới PostgreSQL (glpo_db)...")
    try:
        conn = psycopg2.connect(
            dbname="glpo_db",
            user="glpo_admin",
            password="glpo_password",
            host="localhost",
            port="5432"
        )
    except Exception as e:
        print("Lỗi kết nối CSDL. Bạn đã cài thư viện psycopg2 chưa? (pip install psycopg2-binary)")
        print(e)
        return

    conn.autocommit = False
    cur = conn.cursor()

    # Dọn dẹp Database cũ để tránh bị trùng lặp nếu chạy lại script
    print("Đang dọn dẹp Database cũ...")
    cur.execute("TRUNCATE TABLE app_projects, dim_topic_time, dim_topic_cost, dim_topic_risk, dim_topic_resources CASCADE")
    conn.commit()

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROCESSED_DIR = os.path.join(SCRIPT_DIR, '..', 'data', 'processed')
    # Lọc bỏ thư mục rác Excel
    project_dirs = [d for d in glob.glob(os.path.join(PROCESSED_DIR, '*')) if not os.path.basename(d).startswith('~$')]
    
    print(f"Tìm thấy {len(project_dirs)} dự án hợp lệ. Bắt đầu nạp dữ liệu Snowflake Schema...")

    count = 0
    for pdir in project_dirs:
        pname = os.path.basename(pdir)
        nodes_file = os.path.join(pdir, 'nodes.csv')
        edges_file = os.path.join(pdir, 'edges.csv')
        cal_file = os.path.join(pdir, 'calendar.json')
        
        if not os.path.exists(nodes_file): 
            continue
            
        df_n = pd.read_csv(nodes_file)
        try:
            df_e = pd.read_csv(edges_file)
        except pd.errors.EmptyDataError:
            df_e = pd.DataFrame(columns=['source', 'target', 'type'])
            
        num_nodes = len(df_n)
        num_edges = len(df_e)
        density = num_edges / (num_nodes * (num_nodes - 1) / 2) if num_nodes > 1 else 0
        
        if num_nodes == 0:
            continue
            
        working_hours = '{}'
        working_days = '[]'
        if os.path.exists(cal_file):
            with open(cal_file, 'r', encoding='utf-8') as f:
                cal_data = json.load(f)
                working_hours = json.dumps(cal_data.get('working_hours', {}))
                working_days = json.dumps(cal_data.get('working_days', []))

        # 1. Insert app_projects
        cur.execute("""
            INSERT INTO app_projects (project_name, working_hours, working_days, num_tasks, num_edges, network_density)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (pname, working_hours, working_days, num_nodes, num_edges, float(density)))
        project_id = cur.fetchone()[0]

        node_db_map = {}

        for _, row in df_n.iterrows():
            # Xử lý an toàn NaN và NaT thành None cho PostgreSQL
            r_dict = row.to_dict()
            for k, v in r_dict.items():
                if pd.isna(v) or str(v).strip() in ['NaT', 'NaN', '']:
                    r_dict[k] = None

            # 2. Insert dim_topic_time
            start_date = parse_pg_date(r_dict.get('baseline_start'))
            end_date = parse_pg_date(r_dict.get('baseline_end'))
            cur.execute("""
                INSERT INTO dim_topic_time (duration, baseline_start, baseline_end)
                VALUES (%s, %s, %s) RETURNING id
            """, (r_dict.get('duration'), start_date, end_date))
            time_id = cur.fetchone()[0]

            # 3. Insert dim_topic_cost
            cur.execute("""
                INSERT INTO dim_topic_cost (total_cost)
                VALUES (%s) RETURNING id
            """, (r_dict.get('total_cost'),))
            cost_id = cur.fetchone()[0]

            # 4. Insert dim_topic_risk
            cur.execute("""
                INSERT INTO dim_topic_risk (optimistic_time, pessimistic_time)
                VALUES (%s, %s) RETURNING id
            """, (r_dict.get('optimistic_time'), r_dict.get('pessimistic_time')))
            risk_id = cur.fetchone()[0]

            # 5. Insert dim_topic_resources
            cur.execute("""
                INSERT INTO dim_topic_resources (resource_demand)
                VALUES (%s) RETURNING id
            """, (r_dict.get('resource_demand'),))
            res_id = cur.fetchone()[0]

            # 6. Insert fact_tasks
            cur.execute("""
                INSERT INTO fact_tasks (project_id, task_label, wbs, task_name, topic_time_id, topic_cost_id, topic_risk_id, topic_resources_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING task_id
            """, (project_id, str(r_dict['node_id']), str(r_dict.get('wbs')), str(r_dict.get('task_name')), time_id, cost_id, risk_id, res_id))
            task_id = cur.fetchone()[0]
            
            node_db_map[str(r_dict['node_id'])] = task_id

        # 7. Insert bridge_task_dependencies
        edge_records = []
        for _, row in df_e.iterrows():
            src_str = str(row['source'])
            tgt_str = str(row['target'])
            if src_str in node_db_map and tgt_str in node_db_map:
                edge_records.append((
                    project_id,
                    node_db_map[src_str],
                    node_db_map[tgt_str],
                    row.get('type', 'FS')
                ))
                
        if edge_records:
            execute_values(cur, """
                INSERT INTO bridge_task_dependencies (project_id, predecessor_id, successor_id, dependency_type)
                VALUES %s
                ON CONFLICT (predecessor_id, successor_id) DO NOTHING
            """, edge_records)

        conn.commit()
        count += 1
        if count % 20 == 0:
            print(f"... Đã nạp được {count} dự án...")

    cur.close()
    conn.close()
    print("=========================================================")
    print(f"THÀNH CÔNG! Đã nạp toàn bộ {count} dự án vào PostgreSQL Database.")

if __name__ == "__main__":
    main()
