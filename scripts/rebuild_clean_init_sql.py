"""
Script Tái Tạo Lại TOÀN BỘ database/init.sql Sạch Đẹp 100%
================================================================================
Thư mục: scripts/rebuild_clean_init_sql.py

Chức năng:
  1. Tạo lại toàn bộ Cấu trúc Bảng (Schema DDL) chuẩn xác cho PostgreSQL
     khớp 100% với SQLAlchemy ORM Models trong backend.
  2. Nạp dữ liệu thực tế của 5 dự án benchmark (C2011-07, C2012-04, C2012-08, C2018-09, C2019-16)
     qua câu lệnh INSERT INTO chuẩn.
  3. Xóa bỏ hoàn toàn các dòng COPY cũ lỗi thời.
"""

import os
import sys
import glob
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

INIT_SQL_PATH = os.path.join("database", "init.sql")
PROCESSED_DIR = os.path.join("ai_pipeline", "data", "processed")

DDL_HEADER = """-- ============================================================================
-- GLPO DATABASE INITIALIZATION & SCHEMA DEFINITION (POSTGRESQL 15+)
-- ============================================================================

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

-- DROP ALL TABLES IF EXISTS (CLEAN REBUILD)
DROP TABLE IF EXISTS public.ai_recommendations CASCADE;
DROP TABLE IF EXISTS public.ai_simulation_runs CASCADE;
DROP TABLE IF EXISTS public.project_baselines CASCADE;
DROP TABLE IF EXISTS public.task_resources CASCADE;
DROP TABLE IF EXISTS public.project_constraint_logic CASCADE;
DROP TABLE IF EXISTS public.project_constraint_resource CASCADE;
DROP TABLE IF EXISTS public.project_constraint_time CASCADE;
DROP TABLE IF EXISTS public.tasks CASCADE;
DROP TABLE IF EXISTS public.projects CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- 1. USERS TABLE
CREATE TABLE public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. PROJECTS TABLE
CREATE TABLE public.projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
    project_name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Planning',
    base_cost NUMERIC(15, 2) DEFAULT 0.00,
    total_cost NUMERIC(15, 2) DEFAULT 0.00,
    target_deadline TIMESTAMP,
    penalty_per_day NUMERIC(15, 2) DEFAULT 0.00,
    bonus_per_day NUMERIC(15, 2) DEFAULT 0.00,
    search_vector TSVECTOR,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    num_tasks INTEGER DEFAULT 0,
    num_edges INTEGER DEFAULT 0,
    network_density NUMERIC(5, 4) DEFAULT 0.0000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. PROJECT CONSTRAINT TIME TABLE
CREATE TABLE public.project_constraint_time (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    weekly_schedule JSONB NOT NULL,
    holidays_list JSONB DEFAULT '[]'::jsonb,
    overtime_multiplier NUMERIC(5, 2) DEFAULT 1.50
);

-- 4. PROJECT CONSTRAINT RESOURCE TABLE
CREATE TABLE public.project_constraint_resource (
    id INTEGER NOT NULL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    resource_name VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    max_availability NUMERIC(10, 2) NOT NULL,
    cost_per_use NUMERIC(15, 2) DEFAULT 0.00,
    cost_per_unit NUMERIC(15, 2) DEFAULT 0.00
);

-- 5. TASKS TABLE (WIDE TABLE)
CREATE TABLE public.tasks (
    id VARCHAR(255) PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    baseline_start TIMESTAMP,
    type VARCHAR(255),
    base_cost NUMERIC(15, 2) DEFAULT 0.00,
    total_cost NUMERIC(15, 2) DEFAULT 0.00,
    risk_factor NUMERIC(10, 4) DEFAULT 1.0000,
    duration_months NUMERIC(15, 2),
    duration_weeks NUMERIC(15, 2),
    duration_days NUMERIC(15, 2),
    duration_hours NUMERIC(15, 2),
    calendar_type VARCHAR(50),
    labor NUMERIC(15, 2) DEFAULT 0.00,
    material NUMERIC(15, 2) DEFAULT 0.00,
    equipment NUMERIC(15, 2) DEFAULT 0.00,
    energy NUMERIC(15, 2) DEFAULT 0.00,
    testing_inspection NUMERIC(15, 2) DEFAULT 0.00,
    project_management NUMERIC(15, 2) DEFAULT 0.00,
    facility NUMERIC(15, 2) DEFAULT 0.00,
    utilities NUMERIC(15, 2) DEFAULT 0.00,
    communication NUMERIC(15, 2) DEFAULT 0.00,
    training NUMERIC(15, 2) DEFAULT 0.00,
    quality_management NUMERIC(15, 2) DEFAULT 0.00,
    overtime NUMERIC(15, 2) DEFAULT 0.00,
    delay_penalty NUMERIC(15, 2) DEFAULT 0.00,
    inventory_holding NUMERIC(15, 2) DEFAULT 0.00,
    waiting_cost NUMERIC(15, 2) DEFAULT 0.00,
    idle_resource NUMERIC(15, 2) DEFAULT 0.00,
    revenue_delay NUMERIC(15, 2) DEFAULT 0.00,
    expediting NUMERIC(15, 2) DEFAULT 0.00,
    insurance NUMERIC(15, 2) DEFAULT 0.00,
    rework NUMERIC(15, 2) DEFAULT 0.00,
    warranty NUMERIC(15, 2) DEFAULT 0.00,
    litigation NUMERIC(15, 2) DEFAULT 0.00,
    regulatory_compliance NUMERIC(15, 2) DEFAULT 0.00,
    contingency_reserve NUMERIC(15, 2) DEFAULT 0.00,
    management_reserve NUMERIC(15, 2) DEFAULT 0.00,
    transportation NUMERIC(15, 2) DEFAULT 0.00,
    ordering NUMERIC(15, 2) DEFAULT 0.00,
    packaging NUMERIC(15, 2) DEFAULT 0.00,
    reverse_logistics NUMERIC(15, 2) DEFAULT 0.00,
    customs NUMERIC(15, 2) DEFAULT 0.00,
    supplier_coordination NUMERIC(15, 2) DEFAULT 0.00,
    opportunity_cost NUMERIC(15, 2) DEFAULT 0.00,
    capital_cost NUMERIC(15, 2) DEFAULT 0.00,
    financing_cost NUMERIC(15, 2) DEFAULT 0.00,
    npv_loss NUMERIC(15, 2) DEFAULT 0.00,
    esg_cost NUMERIC(15, 2) DEFAULT 0.00,
    carbon_tax NUMERIC(15, 2) DEFAULT 0.00,
    reputation_cost NUMERIC(15, 2) DEFAULT 0.00,
    complexity NUMERIC(10, 4),
    weather_contingency NUMERIC(10, 4),
    general_contingency NUMERIC(10, 4),
    rework_risk NUMERIC(10, 4),
    overtime_hours NUMERIC(15, 2),
    lag_time NUMERIC(15, 2),
    metadata_json JSONB DEFAULT '{}'::jsonb
);

-- 6. PROJECT CONSTRAINT LOGIC TABLE
CREATE TABLE public.project_constraint_logic (
    predecessor_id VARCHAR(255) NOT NULL REFERENCES public.tasks(id) ON DELETE CASCADE,
    successor_id VARCHAR(255) NOT NULL REFERENCES public.tasks(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'FS' NOT NULL,
    lag_months NUMERIC(15, 2) DEFAULT 0,
    lag_weeks NUMERIC(15, 2) DEFAULT 0,
    lag_days NUMERIC(15, 2) DEFAULT 0,
    lag_hours NUMERIC(15, 2) DEFAULT 0,
    PRIMARY KEY (predecessor_id, successor_id, project_id)
);

-- 7. TASK RESOURCES TABLE
CREATE TABLE public.task_resources (
    task_id VARCHAR(255) NOT NULL REFERENCES public.tasks(id) ON DELETE CASCADE,
    resource_id INTEGER NOT NULL REFERENCES public.project_constraint_resource(id) ON DELETE CASCADE,
    request_quantity NUMERIC(15, 2) NOT NULL,
    allocated_quantity NUMERIC(15, 2),
    labor_productivity NUMERIC(15, 2),
    equipment_utilization NUMERIC(15, 2),
    resource_substitutability INTEGER,
    PRIMARY KEY (task_id, resource_id)
);

-- 8. AI SIMULATION RUNS TABLE
CREATE TABLE public.ai_simulation_runs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    ai_weights JSONB DEFAULT '{"cost": 50, "time": 50}'::jsonb,
    status VARCHAR(50) DEFAULT 'Running',
    results_summary JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. AI RECOMMENDATIONS TABLE
CREATE TABLE public.ai_recommendations (
    id SERIAL PRIMARY KEY,
    simulation_run_id INTEGER NOT NULL REFERENCES public.ai_simulation_runs(id) ON DELETE CASCADE,
    option_name VARCHAR(255),
    action_type JSONB NOT NULL,
    target_tasks JSONB NOT NULL,
    human_message TEXT,
    modifications JSONB,
    impact JSONB,
    risk JSONB,
    is_applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. PROJECT BASELINES TABLE
CREATE TABLE public.project_baselines (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    simulation_run_id INTEGER REFERENCES public.ai_simulation_runs(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SEED DATA SECTION FOR 5 BENCHMARK PROJECTS
-- ============================================================================
"""


def build_clean_init_sql():
    print(f"[REBUILD] Bắt đầu xây dựng lại toàn bộ database/init.sql từ {PROCESSED_DIR}...")
    
    project_dirs = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*")))
    sql_lines = [DDL_HEADER]
    
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

        p_name_escaped = p_name.replace("'", "''")

        # 1. INSERT INTO projects
        p_sql = f"""INSERT INTO public.projects (id, user_id, project_name, type, status, base_cost, total_cost, num_tasks, num_edges, metadata_json)
VALUES ({proj_id_counter}, NULL, '{p_name_escaped} ({p_code})', '{p_type}', 'Planning', {base_cost:.2f}, {base_cost:.2f}, {num_tasks}, {num_edges}, '{{"project_code": "{p_code}"}}');"""
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
                r_name = str(r.get('resource_name', r.get('Name', r.get('id', 'Res')))).replace("'", "''")
                r_type = str(r.get('resource_type', r.get('Type', 'Renewable'))).replace("'", "''")
                avail = float(r.get('max_availability', r.get('Availability', 1.0)))
                r_cost = float(r.get('cost_per_unit', r.get('cost', 0.0)))
                
                r_sql = f"""INSERT INTO public.project_constraint_resource (id, project_id, resource_name, resource_type, max_availability, cost_per_unit)
VALUES ({res_counter}, {proj_id_counter}, '{r_name}', '{r_type}', {avail:.2f}, {r_cost:.2f});"""
                sql_lines.append(r_sql)
                res_id_map[r_name] = res_counter
                res_counter += 1

        # 4. INSERT INTO tasks
        task_id_set = set()
        for _, t in tasks_df.iterrows():
            t_id = str(t.get('task_id', t.get('id', ''))).strip()
            if not t_id:
                continue
            task_id_set.add(t_id)
            t_name = str(t.get('task_name', t_id)).replace("'", "''")
            
            b_start = str(t.get('baseline_start', '')).strip()
            b_start_sql = f"'{b_start}'" if b_start and b_start.lower() != 'nan' else "NULL"
            
            d_m = float(t.get('duration_months', 0.0) or 0.0)
            d_w = float(t.get('duration_weeks', 0.0) or 0.0)
            d_d = float(t.get('duration_days', 0.0) or 0.0)
            d_h = float(t.get('duration_hours', 0.0) or 0.0)
            
            dur_h = d_m * 160.0 + d_w * 40.0 + d_d * 8.0 + d_h
            if dur_h <= 0.0:
                dur_h = float(t.get('duration', 8.0) or 8.0)
                if d_d <= 0.0:
                    d_d = round(dur_h / 8.0, 2)

            t_cost = float(t.get('total_cost', t.get('base_cost', 0.0)))
            b_cost = float(t.get('base_cost', t_cost))
            risk_f = float(t.get('risk_factor', 1.0))

            # Direct costs
            labor = float(t.get('labor', 0.0))
            mat = float(t.get('material', 0.0))
            equip = float(t.get('equipment', 0.0))
            energy = float(t.get('energy', 0.0))
            testing = float(t.get('testing_inspection', 0.0))

            # Overhead
            pm = float(t.get('project_management', 0.0))
            facility = float(t.get('facility', 0.0))
            utilities = float(t.get('utilities', 0.0))
            comm = float(t.get('communication', 0.0))
            training = float(t.get('training', 0.0))
            qm = float(t.get('quality_management', 0.0))

            # Time-dependent
            ot = float(t.get('overtime', 0.0))
            delay_p = float(t.get('delay_penalty', 0.0))
            inv_hold = float(t.get('inventory_holding', 0.0))
            wait_c = float(t.get('waiting_cost', 0.0))
            idle_r = float(t.get('idle_resource', 0.0))
            rev_d = float(t.get('revenue_delay', 0.0))
            exped = float(t.get('expediting', 0.0))

            # Risk & Compliance
            ins = float(t.get('insurance', 0.0))
            rework = float(t.get('rework', 0.0))
            warr = float(t.get('warranty', 0.0))
            litig = float(t.get('litigation', 0.0))
            reg_comp = float(t.get('regulatory_compliance', 0.0))
            cont_res = float(t.get('contingency_reserve', 0.0))
            mgmt_res = float(t.get('management_reserve', 0.0))

            # Supply Chain
            transp = float(t.get('transportation', 0.0))
            order = float(t.get('ordering', 0.0))
            pack = float(t.get('packaging', 0.0))
            rev_log = float(t.get('reverse_logistics', 0.0))
            cust = float(t.get('customs', 0.0))
            supp_coord = float(t.get('supplier_coordination', 0.0))

            # Strategic
            opp_c = float(t.get('opportunity_cost', 0.0))
            cap_c = float(t.get('capital_cost', 0.0))
            fin_c = float(t.get('financing_cost', 0.0))
            npv_l = float(t.get('npv_loss', 0.0))
            esg_c = float(t.get('esg_cost', 0.0))
            carb_t = float(t.get('carbon_tax', 0.0))
            rep_c = float(t.get('reputation_cost', 0.0))

            # Risk factors
            cmplx = float(t.get('complexity', 0.0))
            w_cont = float(t.get('weather_contingency', 0.0))
            g_cont = float(t.get('general_contingency', 0.0))
            rw_risk = float(t.get('rework_risk', 0.0))
            ot_h = float(t.get('overtime_hours', 0.0))
            lag_t = float(t.get('lag_time', 0.0))

            t_sql = f"""INSERT INTO public.tasks (id, project_id, task_name, status, base_cost, total_cost, risk_factor, baseline_start, duration_months, duration_weeks, duration_days, duration_hours, labor, material, equipment, energy, testing_inspection, project_management, facility, utilities, communication, training, quality_management, overtime, delay_penalty, inventory_holding, waiting_cost, idle_resource, revenue_delay, expediting, insurance, rework, warranty, litigation, regulatory_compliance, contingency_reserve, management_reserve, transportation, ordering, packaging, reverse_logistics, customs, supplier_coordination, opportunity_cost, capital_cost, financing_cost, npv_loss, esg_cost, carbon_tax, reputation_cost, complexity, weather_contingency, general_contingency, rework_risk, overtime_hours, lag_time)
VALUES ('{t_id}', {proj_id_counter}, '{t_name}', 'Pending', {b_cost:.2f}, {t_cost:.2f}, {risk_f:.2f}, {b_start_sql}, {d_m:.2f}, {d_w:.2f}, {d_d:.2f}, {dur_h:.2f}, {labor:.2f}, {mat:.2f}, {equip:.2f}, {energy:.2f}, {testing:.2f}, {pm:.2f}, {facility:.2f}, {utilities:.2f}, {comm:.2f}, {training:.2f}, {qm:.2f}, {ot:.2f}, {delay_p:.2f}, {inv_hold:.2f}, {wait_c:.2f}, {idle_r:.2f}, {rev_d:.2f}, {exped:.2f}, {ins:.2f}, {rework:.2f}, {warr:.2f}, {litig:.2f}, {reg_comp:.2f}, {cont_res:.2f}, {mgmt_res:.2f}, {transp:.2f}, {order:.2f}, {pack:.2f}, {rev_log:.2f}, {cust:.2f}, {supp_coord:.2f}, {opp_c:.2f}, {cap_c:.2f}, {fin_c:.2f}, {npv_l:.2f}, {esg_c:.2f}, {carb_t:.2f}, {rep_c:.2f}, {cmplx:.2f}, {w_cont:.2f}, {g_cont:.2f}, {rw_risk:.2f}, {ot_h:.2f}, {lag_t:.2f});"""
            sql_lines.append(t_sql)

        # 5. INSERT INTO project_constraint_logic
        if not preds_df.empty:
            for _, pr in preds_df.iterrows():
                p_pred = str(pr.get('source_id', pr.get('predecessor_id', pr.get('pred', '')))).strip()
                p_succ = str(pr.get('target_id', pr.get('successor_id', pr.get('succ', '')))).strip()
                if not p_pred or not p_succ or p_pred.lower() == 'nan' or p_succ.lower() == 'nan':
                    continue
                if p_pred not in task_id_set or p_succ not in task_id_set:
                    continue
                p_lag = float(pr.get('lag_hours', 0.0))
                
                logic_sql = f"""INSERT INTO public.project_constraint_logic (predecessor_id, successor_id, project_id, dependency_type, lag_hours)
VALUES ('{p_pred}', '{p_succ}', {proj_id_counter}, 'FS', {p_lag:.2f}) ON CONFLICT DO NOTHING;"""
                sql_lines.append(logic_sql)

        # 6. INSERT INTO task_resources
        if os.path.exists(task_res_file):
            tr_df = pd.read_csv(task_res_file)
            for _, tr in tr_df.iterrows():
                tr_t = str(tr.get('task_id', '')).strip()
                if tr_t not in task_id_set:
                    continue
                tr_r_name = str(tr.get('role', tr.get('resource_id', ''))).replace("'", "''")
                tr_qty = float(tr.get('quantity', tr.get('request_quantity', 1.0)))
                r_db_id = res_id_map.get(tr_r_name)
                if not r_db_id:
                    continue
                
                tr_sql = f"""INSERT INTO public.task_resources (task_id, resource_id, request_quantity, allocated_quantity)
VALUES ('{tr_t}', {r_db_id}, {tr_qty:.2f}, {tr_qty:.2f}) ON CONFLICT DO NOTHING;"""
                sql_lines.append(tr_sql)

        print(f"   * [OK] Đã tạo DDL + SQL Insert sạch cho dự án [{proj_id_counter}] {p_code} ({num_tasks} tasks, {num_edges} edges).")
        proj_id_counter += 1

    # Cập nhật sequence của bảng projects để không đụng id mới
    sql_lines.append(f"\nSELECT setval('public.projects_id_seq', {proj_id_counter});")

    full_sql = "\n".join(sql_lines) + "\n"
    with open(INIT_SQL_PATH, "w", encoding="utf-8") as f:
        f.write(full_sql)

    print(f"\n[SUCCESS] Đã tạo lại toàn bộ file {INIT_SQL_PATH} sạch đẹp 100%!")


if __name__ == "__main__":
    build_clean_init_sql()
