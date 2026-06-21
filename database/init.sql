-- ==============================================================================
-- GLPO Database Initialization Script (PostgreSQL)
-- Architecture: Topic-based Snowflake Schema + Application Management Layer
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. APPLICATION MANAGEMENT LAYER (TẦNG PHẦN MỀM)
-- ------------------------------------------------------------------------------

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE app_projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    project_name VARCHAR(255) NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', project_name)) STORED,
    working_hours JSONB,
    working_days JSONB,
    num_tasks INTEGER DEFAULT 0,
    num_edges INTEGER DEFAULT 0,
    network_density NUMERIC(5,4) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'Planning', -- Planning, Executing, Closed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_project_search ON app_projects USING GIN(search_vector);

CREATE TABLE ai_simulation_runs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES app_projects(id) ON DELETE CASCADE,
    ai_weights JSONB DEFAULT '{"time": 50, "cost": 50}'::jsonb,
    status VARCHAR(50) DEFAULT 'Running', -- Pending, Running, Success, Failed
    results_summary JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE project_baselines (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES app_projects(id) ON DELETE CASCADE,
    simulation_run_id INTEGER REFERENCES ai_simulation_runs(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. DIMENSION TOPICS (NGĂN KÉO CHỦ ĐỀ CHO SNOWFLAKE SCHEMA)
-- ------------------------------------------------------------------------------

CREATE TABLE dim_topic_time (
    id SERIAL PRIMARY KEY,
    duration NUMERIC(10,3),
    baseline_start TIMESTAMP,
    baseline_end TIMESTAMP
);

CREATE TABLE dim_topic_cost (
    id SERIAL PRIMARY KEY,
    total_cost NUMERIC(15,2) DEFAULT 0
);

CREATE TABLE dim_topic_risk (
    id SERIAL PRIMARY KEY,
    optimistic_time NUMERIC(10,3),
    pessimistic_time NUMERIC(10,3),
    variance NUMERIC(10,2),
    criticality_index NUMERIC(5,2)
);

CREATE TABLE dim_topic_resources (
    id SERIAL PRIMARY KEY,
    resource_demand TEXT
);

-- ------------------------------------------------------------------------------
-- 3. CORE FACT & GRAPH TABLES (LÕI DỮ LIỆU)
-- ------------------------------------------------------------------------------

CREATE TABLE fact_tasks (
    task_id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES app_projects(id) ON DELETE CASCADE,
    task_label VARCHAR(50) NOT NULL,
    wbs VARCHAR(100),
    task_name VARCHAR(255),
    
    -- Topic Foreign Keys (Zero-or-One relationships - Nullable to control sparsity)
    topic_time_id INTEGER REFERENCES dim_topic_time(id) ON DELETE SET NULL,
    topic_cost_id INTEGER REFERENCES dim_topic_cost(id) ON DELETE SET NULL,
    topic_risk_id INTEGER REFERENCES dim_topic_risk(id) ON DELETE SET NULL,
    topic_resources_id INTEGER REFERENCES dim_topic_resources(id) ON DELETE SET NULL
);

-- Indexing for fast analytical queries
CREATE INDEX idx_fact_tasks_project ON fact_tasks(project_id);

-- GRAPH BRIDGE: Bảng phục vụ đệ quy CTE (Edges)
CREATE TABLE bridge_task_dependencies (
    project_id INTEGER REFERENCES app_projects(id) ON DELETE CASCADE,
    predecessor_id INTEGER REFERENCES fact_tasks(task_id) ON DELETE CASCADE,
    successor_id INTEGER REFERENCES fact_tasks(task_id) ON DELETE CASCADE,
    dependency_type VARCHAR(10) DEFAULT 'FS', -- Finish-to-Start, Start-to-Start
    lag_days INTEGER DEFAULT 0,
    PRIMARY KEY (predecessor_id, successor_id)
);

-- Indexing heavily optimized for graph traversal (CTE)
CREATE INDEX idx_bridge_project ON bridge_task_dependencies(project_id);
CREATE INDEX idx_bridge_predecessor ON bridge_task_dependencies(predecessor_id);
CREATE INDEX idx_bridge_successor ON bridge_task_dependencies(successor_id);
