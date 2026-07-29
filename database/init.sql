-- ============================================================================
-- GLPO DATABASE INITIALIZATION & SCHEMA DEFINITION (POSTGRESQL 15+)
-- ============================================================================
-- Thư mục: database/init.sql
-- Mô tả: File khởi tạo cấu trúc Database chuẩn hóa 100% cho Hệ thống GLPO AI Pipeline
-- ============================================================================

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

-- ----------------------------------------------------------------------------
-- DROP SCHEMA AND RECREATE (CLEAN WIPE OF ALL OLD TABLES)
-- ----------------------------------------------------------------------------
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO glpo_admin;
GRANT ALL ON SCHEMA public TO public;

-- ----------------------------------------------------------------------------
-- 1. USERS TABLE (Quản lý Người dùng)
-- ----------------------------------------------------------------------------
CREATE TABLE public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. PROJECTS TABLE (Thông tin Dự án & Tham số Hợp đồng)
-- ----------------------------------------------------------------------------
CREATE TABLE public.projects (
    id VARCHAR(100) PRIMARY KEY,                 -- Mã dự án duy nhất (ví dụ: "C2011-07")
    user_id INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
    project_name VARCHAR(255) NOT NULL,
    project_type VARCHAR(50) DEFAULT 'CON',     -- Loai hình: CON, ITLG, PRO
    status VARCHAR(50) DEFAULT 'Planning',       -- Trang thai: Planning, Executing, Closed
    target_deadline TIMESTAMP WITH TIME ZONE,    -- Han chót chỉ định Datetime
    penalty_per_day NUMERIC(15, 2) DEFAULT 0.00, -- Tien phat tre $/ngay
    bonus_per_day NUMERIC(15, 2) DEFAULT 0.00,   -- Tien thuong lam som $/ngay
    base_cost NUMERIC(15, 2) DEFAULT 0.00,       -- Tong chi phi goc ban dau
    total_cost NUMERIC(15, 2) DEFAULT 0.00,      -- Tong chi phi du bao
    num_tasks INTEGER DEFAULT 0,                 -- So luong cong viec
    num_edges INTEGER DEFAULT 0,                 -- So luong quan he phu thuoc
    metadata_json JSONB DEFAULT '{}'::jsonb,     -- JSON metadata bo sung
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. PROJECT CALENDARS TABLE (Lịch Agenda thi công từ agenda.json)
-- ----------------------------------------------------------------------------
CREATE TABLE public.project_calendars (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    weekly_schedule JSONB NOT NULL DEFAULT '{}'::jsonb, -- Lich ca lam viec T2 -> CN
    holidays_list JSONB NOT NULL DEFAULT '[]'::jsonb,   -- Danh sach ngay nghi le
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_calendar UNIQUE (project_id)
);

-- ----------------------------------------------------------------------------
-- 4. TASKS TABLE (Danh sách Công việc từ tasks.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE public.tasks (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    task_id VARCHAR(100) NOT NULL,              -- Ma task (vi du: "C2011-07_1")
    task_name VARCHAR(255),
    baseline_start TIMESTAMP WITH TIME ZONE,     -- Moc khoi cong ban dau
    duration_hours NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- Thoi gian thi cong (gio)
    
    -- 38 Cot chi phi vat ly (Physical SQL Columns)
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

    -- Tong chi phi goc cong viec (Tu dong tinh & luu tru bang GENERATED ALWAYS AS STORED)
    total_cost NUMERIC(15, 2) GENERATED ALWAYS AS (
        COALESCE(labor, 0) + COALESCE(material, 0) + COALESCE(equipment, 0) + COALESCE(energy, 0) + 
        COALESCE(testing_inspection, 0) + COALESCE(project_management, 0) + COALESCE(facility, 0) + 
        COALESCE(utilities, 0) + COALESCE(communication, 0) + COALESCE(training, 0) + 
        COALESCE(quality_management, 0) + COALESCE(overtime, 0) + COALESCE(delay_penalty, 0) + 
        COALESCE(inventory_holding, 0) + COALESCE(waiting_cost, 0) + COALESCE(idle_resource, 0) + 
        COALESCE(revenue_delay, 0) + COALESCE(expediting, 0) + COALESCE(insurance, 0) + 
        COALESCE(rework, 0) + COALESCE(warranty, 0) + COALESCE(litigation, 0) + 
        COALESCE(regulatory_compliance, 0) + COALESCE(contingency_reserve, 0) + 
        COALESCE(management_reserve, 0) + COALESCE(transportation, 0) + COALESCE(ordering, 0) + 
        COALESCE(packaging, 0) + COALESCE(reverse_logistics, 0) + COALESCE(customs, 0) + 
        COALESCE(supplier_coordination, 0) + COALESCE(opportunity_cost, 0) + COALESCE(capital_cost, 0) + 
        COALESCE(financing_cost, 0) + COALESCE(npv_loss, 0) + COALESCE(esg_cost, 0) + 
        COALESCE(carbon_tax, 0) + COALESCE(reputation_cost, 0)
    ) STORED,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_task UNIQUE (project_id, task_id)
);

-- ----------------------------------------------------------------------------
-- 5. RESOURCES TABLE (Danh sách Tài nguyên từ resources.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE public.resources (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    resource_id VARCHAR(100) NOT NULL,          -- Ma tai nguyen (vi du: "R1", "Worker_1")
    name VARCHAR(255),
    type VARCHAR(50) NOT NULL DEFAULT 'Human',  -- Loai: Human, Machine
    max_availability NUMERIC(10, 2) DEFAULT 1.00, -- Năng luc cung ung toi da
    unit_cost NUMERIC(15, 2) DEFAULT 0.00,      -- Don gia theo gio
    energy NUMERIC(15, 2) DEFAULT 0.00,         -- Chi phi nang luong/nhien lieu
    overtime_multi NUMERIC(5, 2) DEFAULT 1.50,  -- He so luong tang ca (1.5x)
    max_overtime_per_day NUMERIC(5, 2) DEFAULT 4.00, -- Tran tang ca max/ngay (Bottleneck MIN)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_resource UNIQUE (project_id, resource_id)
);

-- ----------------------------------------------------------------------------
-- 6. TASK LOGIC TABLE (Mối quan hệ Phụ thuộc từ logic.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE public.task_logic (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    predecessor_id VARCHAR(100) NOT NULL,       -- Ma task tien nhiem
    successor_id VARCHAR(100) NOT NULL,         -- Ma task ke nhiem
    dependency_type VARCHAR(10) DEFAULT 'FS',   -- Loai quan he: FS, SS, FF, SF
    lag_hours NUMERIC(10, 2) DEFAULT 0.00,      -- Do trễ (gio)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_logic_predecessor FOREIGN KEY (project_id, predecessor_id) REFERENCES public.tasks(project_id, task_id) ON DELETE CASCADE,
    CONSTRAINT fk_logic_successor FOREIGN KEY (project_id, successor_id) REFERENCES public.tasks(project_id, task_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 7. TASK RESOURCES TABLE (Phân bổ Tài nguyên từ task_resources.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE public.task_resources (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    task_id VARCHAR(100) NOT NULL,              -- Ma task
    resource_id VARCHAR(100) NOT NULL,          -- Ma tai nguyen / Ten tai nguyen
    request_quantity NUMERIC(10, 2) NOT NULL DEFAULT 1.00, -- So luong tai nguyen yeu cau
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_task_res_task FOREIGN KEY (project_id, task_id) REFERENCES public.tasks(project_id, task_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 8. AI PIPELINE RUNS TABLE (Phiên chạy Mô phỏng & Tối ưu AI)
-- ----------------------------------------------------------------------------
CREATE TABLE public.ai_pipeline_runs (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'Running', -- Status: Running, Completed, Failed
    target_deadline TIMESTAMP WITH TIME ZONE,    -- Han chot truyen vao
    penalty_per_day NUMERIC(15, 2) DEFAULT 0.00, -- Tien phat trễ $/ngay
    bonus_per_day NUMERIC(15, 2) DEFAULT 0.00,   -- Tien thuong $/ngay
    mc_iterations INTEGER DEFAULT 10000,         -- So vong mo phong Monte Carlo
    pareto_count INTEGER DEFAULT 5,              -- So luong phuong an Pareto xuat
    overtime_multiplier NUMERIC(5, 2) DEFAULT 1.50,
    ai_predictions JSONB DEFAULT '{}'::jsonb,    -- Ket qua suy luan HGT Transformer
    mc_results JSONB DEFAULT '{}'::jsonb,        -- Ket qua mo phong Monte Carlo CPM
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE
);

-- ----------------------------------------------------------------------------
-- 9. PARETO SOLUTIONS TABLE (Tập Phương án Tối ưu Pareto Frontier)
-- ----------------------------------------------------------------------------
CREATE TABLE public.pareto_solutions (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES public.ai_pipeline_runs(id) ON DELETE CASCADE,
    option_name VARCHAR(100) NOT NULL,          -- Ten phuong an (vi du: "Phương án [1]")
    option_index INTEGER NOT NULL,               -- Thu tu phuong an (1, 2, 3...)
    makespan_hours NUMERIC(10, 2) NOT NULL,     -- Tong thoi gian thi cong (gio)
    finish_datetime VARCHAR(100),               -- Ngay gio hoan thanh thuc te ("16/05/2011 15:00")
    base_project_cost NUMERIC(15, 2) NOT NULL,  -- Chi phi thi cong goc
    penalty_cost NUMERIC(15, 2) DEFAULT 0.00,   -- Tien phat tre
    bonus_amount NUMERIC(15, 2) DEFAULT 0.00,   -- Tien thuong lam som
    total_cost NUMERIC(15, 2) NOT NULL,         -- Chi phi Rong (Net Cost)
    risk_pct NUMERIC(5, 2) NOT NULL,            -- Ty le rui ro tre %
    tasks_schedule JSONB NOT NULL DEFAULT '{}'::jsonb, -- Bang ke hoach chi tiet tung task (Gantt Chart Data)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- INDEXES FOR MAXIMUM QUERY PERFORMANCE (TỐI ƯU TỐC ĐỘ TRUY VẤN)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_projects_name ON public.projects(project_name);
CREATE INDEX idx_tasks_project ON public.tasks(project_id, task_id);
CREATE INDEX idx_resources_project ON public.resources(project_id, resource_id);
CREATE INDEX idx_logic_project ON public.task_logic(project_id, predecessor_id, successor_id);
CREATE INDEX idx_task_resources_project ON public.task_resources(project_id, task_id, resource_id);
CREATE INDEX idx_pipeline_runs_project ON public.ai_pipeline_runs(project_id, status);
CREATE INDEX idx_pareto_solutions_run ON public.pareto_solutions(run_id, option_index);
