-- ==============================================================================
-- GLPO Database Initialization Script (PostgreSQL)
-- Architecture: Hub-and-Spoke (12 Spokes based on ERD.drawio V3)
-- Updated: Synchronized with Draw.io changes (STRING IDs)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. MANAGEMENT LAYER
-- ------------------------------------------------------------------------------

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    project_name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Planning',
    base_cost NUMERIC(15,2) DEFAULT 0.00,
    total_cost NUMERIC(15,2) DEFAULT 0.00,
    
    -- Contractual Project Constraints
    target_deadline TIMESTAMP,
    penalty_per_day NUMERIC(15,2),
    bonus_per_day NUMERIC(15,2),
    
    -- Additional Model Fields
    search_vector TSVECTOR,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    num_tasks INTEGER DEFAULT 0,
    num_edges INTEGER DEFAULT 0,
    network_density NUMERIC(5,4),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. CONSTRAINT & RESOURCES LAYER
-- ------------------------------------------------------------------------------

CREATE TABLE project_constraint_time (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    weekly_schedule JSONB NOT NULL,
    holidays_list JSONB DEFAULT '[]'::jsonb,
    overtime_multiplier NUMERIC(5,2) DEFAULT 1.50
);

CREATE TABLE project_constraint_resource (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    resource_name VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    max_availability NUMERIC(10,2) NOT NULL,
    cost_per_use NUMERIC(15,2) DEFAULT 0,
    cost_per_unit NUMERIC(15,2) DEFAULT 0
);

-- ------------------------------------------------------------------------------
-- 3. AI PIPELINE & RESULTS
-- ------------------------------------------------------------------------------

CREATE TABLE ai_simulation_runs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ai_weights JSONB DEFAULT '{"time": 50, "cost": 50}'::jsonb,
    status VARCHAR(50) DEFAULT 'Running',
    results_summary JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ai_recommendations (
    id SERIAL PRIMARY KEY,
    simulation_run_id INTEGER NOT NULL REFERENCES ai_simulation_runs(id) ON DELETE CASCADE,
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

CREATE TABLE project_baselines (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    simulation_run_id INTEGER REFERENCES ai_simulation_runs(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 4. HUB TABLE (TASKS)
-- ------------------------------------------------------------------------------

CREATE TABLE tasks (
    id VARCHAR(255) PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    baseline_start TIMESTAMP,
    type VARCHAR(255),
    
    base_cost NUMERIC(15,2) DEFAULT 0.00,
    total_cost NUMERIC(15,2) DEFAULT 0.00,
    risk_factor NUMERIC(10,4) DEFAULT 1.0000,
    
    -- Extracted Time Components (Hub)
    duration_months NUMERIC(15,2),
    duration_weeks NUMERIC(15,2),
    duration_days NUMERIC(15,2),
    duration_hours NUMERIC(15,2),
    calendar_type VARCHAR(50),
    
    -- G1: Direct Costs
    internal_labor_cost NUMERIC(15,2),
    overtime_cost NUMERIC(15,2),
    equipment_fuel_cost NUMERIC(15,2),
    qa_qc_cost NUMERIC(15,2),
    material_cost NUMERIC(15,2),
    outsourcing_cost NUMERIC(15,2),
    
    -- G2: Indirect Costs
    training_cost NUMERIC(15,2),
    facility_rent NUMERIC(15,2),
    communication_cost NUMERIC(15,2),
    utilities_cost NUMERIC(15,2),
    
    -- G4: Contractual
    insurance_cost NUMERIC(15,2),
    licensing_cost NUMERIC(15,2),
    warranty_cost NUMERIC(15,2),
    
    -- G5: Risk Coefficients
    complexity NUMERIC(10,4),
    weather_contingency NUMERIC(10,4),
    general_contingency NUMERIC(10,4),
    rework_risk NUMERIC(10,4),
    
    -- G6: Logistics
    holding_cost NUMERIC(15,2),
    international_freight NUMERIC(15,2),
    handling_cost NUMERIC(15,2),
    reverse_logistics NUMERIC(15,2),
    defect_cost NUMERIC(15,2),
    
    -- G7: Time Components
    overtime_hours NUMERIC(15,2),
    lag_time NUMERIC(15,2),
    
    -- Metadata JSON cho AI Computed Data
    metadata_json JSONB
);

CREATE TABLE project_constraint_logic (
    predecessor_id VARCHAR(255) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    successor_id VARCHAR(255) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'FS',
    
    lag_months NUMERIC(15,2) DEFAULT 0,
    lag_weeks NUMERIC(15,2) DEFAULT 0,
    lag_days NUMERIC(15,2) DEFAULT 0,
    lag_hours NUMERIC(15,2) DEFAULT 0,
    
    PRIMARY KEY (predecessor_id, successor_id, project_id)
);

-- ------------------------------------------------------------------------------
-- 5. RESOURCE MAPPING (G7)
-- ------------------------------------------------------------------------------

CREATE TABLE task_resources (
    task_id VARCHAR(255) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    resource_id INTEGER NOT NULL REFERENCES project_constraint_resource(id) ON DELETE CASCADE,
    request_quantity NUMERIC(15,2) NOT NULL,
    allocated_quantity NUMERIC(15,2),
    labor_productivity NUMERIC(15,2),
    equipment_utilization NUMERIC(15,2),
    resource_substitutability INTEGER,
    PRIMARY KEY (task_id, resource_id)
);
