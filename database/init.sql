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
    id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Planning',
    
    -- Contractual Project Constraints
    target_deadline TIMESTAMP,
    penalty_per_day NUMERIC(15,2),
    bonus_per_day NUMERIC(15,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. CONSTRAINT & RESOURCES LAYER
-- ------------------------------------------------------------------------------

CREATE TABLE project_constraint_agenda (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    weekly_schedule JSONB NOT NULL,
    holidays_list JSONB DEFAULT '[]'::jsonb
);

CREATE TABLE project_constraint_resources (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    resource_name VARCHAR(100) NOT NULL,
    capacity INTEGER NOT NULL,
    internal_cost NUMERIC(15,2) DEFAULT 0,
    external_cost NUMERIC(15,2) DEFAULT 0
);

-- ------------------------------------------------------------------------------
-- 3. AI PIPELINE & RESULTS
-- ------------------------------------------------------------------------------

CREATE TABLE ai_simulation_runs (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
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
    project_id VARCHAR(255) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    simulation_run_id INTEGER REFERENCES ai_simulation_runs(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 4. HUB TABLE (TASKS)
-- ------------------------------------------------------------------------------

CREATE TABLE tasks (
    id VARCHAR(255) PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    baseline_start TIMESTAMP,
    type VARCHAR(255),
    
    -- Extracted Time Components
    duration_months NUMERIC(15,2),
    duration_weeks NUMERIC(15,2),
    duration_days NUMERIC(15,2),
    duration_hours NUMERIC(15,2),
    
    -- Custom addition for heuristics
    calendar_type VARCHAR(50)
);

-- Logic Table (Edges between tasks)
CREATE TABLE project_constraint_logic (
    predecessor_task_id VARCHAR(255) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    successor_task_id VARCHAR(255) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    project_id VARCHAR(255) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'FS',
    
    lag_months NUMERIC(15,2) DEFAULT 0,
    lag_weeks NUMERIC(15,2) DEFAULT 0,
    lag_days NUMERIC(15,2) DEFAULT 0,
    lag_hours NUMERIC(15,2) DEFAULT 0,
    
    PRIMARY KEY (predecessor_task_id, successor_task_id, project_id)
);

-- ------------------------------------------------------------------------------
-- 5. SPOKE TABLES (USER INPUT FEATURES)
-- ------------------------------------------------------------------------------

CREATE TABLE task_g1_direct_costs (
    task_id VARCHAR(255) PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    internal_labor_cost NUMERIC(15,2),
    subcontracting_cost NUMERIC(15,2),
    overtime_crashing_cost NUMERIC(15,2),
    material_cost NUMERIC(15,2),
    equipment_cost NUMERIC(15,2), 
    direct_transportation NUMERIC(15,2),
    energy_fuel_cost NUMERIC(15,2),
    testing_and_inspection NUMERIC(15,2)
);

CREATE TABLE task_g2_indirect_costs (
    task_id VARCHAR(255) PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    pm_overhead NUMERIC(15,2),
    facility_rent NUMERIC(15,2),
    utilities NUMERIC(15,2),
    communication_cost NUMERIC(15,2),
    internal_training NUMERIC(15,2),
    quality_mgmt_overhead NUMERIC(15,2)
);

CREATE TABLE task_g4_contractual (
    task_id VARCHAR(255) PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    permits_and_licensing NUMERIC(15,2),
    project_insurance NUMERIC(15,2),
    warranty_and_after_sales NUMERIC(15,2),
    regulatory_compliance NUMERIC(15,2)
);

CREATE TABLE task_g5_logistics (
    task_id VARCHAR(255) PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    inventory_holding_cost NUMERIC(15,2),
    ordering_cost NUMERIC(15,2),
    shortage_stockout NUMERIC(15,2),
    obsolescence_cost NUMERIC(15,2),
    international_freight NUMERIC(15,2),
    packaging_and_handling NUMERIC(15,2),
    reverse_logistics NUMERIC(15,2)
);

CREATE TABLE task_g6_temporal (
    task_id VARCHAR(255) PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    wait_queue_time NUMERIC(15,2),
    setup_transition_time NUMERIC(15,2),
    induction_time NUMERIC(15,2),
    lead_time NUMERIC(15,2),
    pert_3_point_estimate NUMERIC(15,2)
);

CREATE TABLE task_g7_resources (
    task_id VARCHAR(255) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    resource_id INTEGER NOT NULL REFERENCES project_constraint_resources(id) ON DELETE CASCADE,
    request_quantity NUMERIC(15,2) NOT NULL,
    allocated_quantity NUMERIC(15,2),
    labor_productivity NUMERIC(15,2),
    equipment_utilization NUMERIC(15,2),
    resource_substitutability INTEGER,
    PRIMARY KEY (task_id, resource_id)
);

CREATE TABLE task_g9_risks (
    task_id VARCHAR(255) PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    technical_complexity NUMERIC(15,2),
    rework_probability NUMERIC(15,2),
    external_dependency_level NUMERIC(15,2),
    contingency_reserve NUMERIC(15,2),
    management_reserve NUMERIC(15,2),
    weather_seasonal_risk NUMERIC(15,2),
    technology_risk NUMERIC(15,2)
);

CREATE TABLE task_g11_human_org (
    task_id VARCHAR(255) PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    required_skill_level INTEGER,
    staff_experience NUMERIC(15,2),
    learning_curve_effect NUMERIC(15,2),
    hr_stability_risk NUMERIC(15,2), 
    cross_functional_coordination INTEGER,
    occupational_safety_risk INTEGER
);

CREATE TABLE task_g12_esg (
    task_id VARCHAR(255) PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    environmental_impact INTEGER,
    waste_disposal_cost NUMERIC(15,2),
    community_social_impact INTEGER,
    carbon_tax_credit NUMERIC(15,2),
    esg_compliance INTEGER
);
