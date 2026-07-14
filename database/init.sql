--
-- PostgreSQL database dump
--

-- \restrict 5N81jXheozMCPBQV7LMkOjedHsN2V8V4mS6OcrXRssUWN4nHeg4aVQzldZeznOK

-- Dumped from database version 15.18
-- Dumped by pg_dump version 15.18

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.tasks DROP CONSTRAINT IF EXISTS tasks_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.task_resources DROP CONSTRAINT IF EXISTS task_resources_task_id_fkey;
ALTER TABLE IF EXISTS ONLY public.task_resources DROP CONSTRAINT IF EXISTS task_resources_resource_id_fkey;
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_constraint_time DROP CONSTRAINT IF EXISTS project_constraint_time_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_constraint_resource DROP CONSTRAINT IF EXISTS project_constraint_resource_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_constraint_logic DROP CONSTRAINT IF EXISTS project_constraint_logic_successor_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_constraint_logic DROP CONSTRAINT IF EXISTS project_constraint_logic_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_constraint_logic DROP CONSTRAINT IF EXISTS project_constraint_logic_predecessor_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_baselines DROP CONSTRAINT IF EXISTS project_baselines_simulation_run_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_baselines DROP CONSTRAINT IF EXISTS project_baselines_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ai_simulation_runs DROP CONSTRAINT IF EXISTS ai_simulation_runs_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.ai_recommendations DROP CONSTRAINT IF EXISTS ai_recommendations_simulation_run_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_username_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE IF EXISTS ONLY public.tasks DROP CONSTRAINT IF EXISTS tasks_pkey;
ALTER TABLE IF EXISTS ONLY public.task_resources DROP CONSTRAINT IF EXISTS task_resources_pkey;
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_pkey;
ALTER TABLE IF EXISTS ONLY public.project_constraint_time DROP CONSTRAINT IF EXISTS project_constraint_time_project_id_key;
ALTER TABLE IF EXISTS ONLY public.project_constraint_time DROP CONSTRAINT IF EXISTS project_constraint_time_pkey;
ALTER TABLE IF EXISTS ONLY public.project_constraint_resource DROP CONSTRAINT IF EXISTS project_constraint_resource_pkey;
ALTER TABLE IF EXISTS ONLY public.project_constraint_logic DROP CONSTRAINT IF EXISTS project_constraint_logic_pkey;
ALTER TABLE IF EXISTS ONLY public.project_baselines DROP CONSTRAINT IF EXISTS project_baselines_pkey;
ALTER TABLE IF EXISTS ONLY public.ai_simulation_runs DROP CONSTRAINT IF EXISTS ai_simulation_runs_pkey;
ALTER TABLE IF EXISTS ONLY public.ai_recommendations DROP CONSTRAINT IF EXISTS ai_recommendations_pkey;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.projects ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_constraint_time ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_constraint_resource ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_baselines ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.ai_simulation_runs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.ai_recommendations ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.tasks;
DROP TABLE IF EXISTS public.task_resources;
DROP SEQUENCE IF EXISTS public.projects_id_seq;
DROP TABLE IF EXISTS public.projects;
DROP SEQUENCE IF EXISTS public.project_constraint_time_id_seq;
DROP TABLE IF EXISTS public.project_constraint_time;
DROP SEQUENCE IF EXISTS public.project_constraint_resource_id_seq;
DROP TABLE IF EXISTS public.project_constraint_resource;
DROP TABLE IF EXISTS public.project_constraint_logic;
DROP SEQUENCE IF EXISTS public.project_baselines_id_seq;
DROP TABLE IF EXISTS public.project_baselines;
DROP SEQUENCE IF EXISTS public.ai_simulation_runs_id_seq;
DROP TABLE IF EXISTS public.ai_simulation_runs;
DROP SEQUENCE IF EXISTS public.ai_recommendations_id_seq;
DROP TABLE IF EXISTS public.ai_recommendations;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_recommendations (
    id integer NOT NULL,
    simulation_run_id integer NOT NULL,
    option_name character varying(255),
    action_type jsonb NOT NULL,
    target_tasks jsonb NOT NULL,
    human_message text,
    modifications jsonb,
    impact jsonb,
    risk jsonb,
    is_applied boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: ai_recommendations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_recommendations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_recommendations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_recommendations_id_seq OWNED BY public.ai_recommendations.id;


--
-- Name: ai_simulation_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_simulation_runs (
    id integer NOT NULL,
    project_id integer NOT NULL,
    ai_weights jsonb DEFAULT '{"cost": 50, "time": 50}'::jsonb,
    status character varying(50) DEFAULT 'Running'::character varying,
    results_summary jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: ai_simulation_runs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_simulation_runs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_simulation_runs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_simulation_runs_id_seq OWNED BY public.ai_simulation_runs.id;


--
-- Name: project_baselines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_baselines (
    id integer NOT NULL,
    project_id integer NOT NULL,
    simulation_run_id integer,
    is_active boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: project_baselines_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_baselines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_baselines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_baselines_id_seq OWNED BY public.project_baselines.id;


--
-- Name: project_constraint_logic; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_constraint_logic (
    predecessor_id character varying(255) NOT NULL,
    successor_id character varying(255) NOT NULL,
    project_id integer NOT NULL,
    dependency_type character varying(50) DEFAULT 'FS'::character varying NOT NULL,
    lag_months numeric(15,2) DEFAULT 0,
    lag_weeks numeric(15,2) DEFAULT 0,
    lag_days numeric(15,2) DEFAULT 0,
    lag_hours numeric(15,2) DEFAULT 0
);


--
-- Name: project_constraint_resource; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_constraint_resource (
    id integer NOT NULL,
    project_id integer NOT NULL,
    resource_name character varying(100) NOT NULL,
    resource_type character varying(50) NOT NULL,
    max_availability numeric(10,2) NOT NULL,
    cost_per_use numeric(15,2) DEFAULT 0,
    cost_per_unit numeric(15,2) DEFAULT 0
);


--
-- Name: project_constraint_resource_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_constraint_resource_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_constraint_resource_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_constraint_resource_id_seq OWNED BY public.project_constraint_resource.id;


--
-- Name: project_constraint_time; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_constraint_time (
    id integer NOT NULL,
    project_id integer NOT NULL,
    weekly_schedule jsonb NOT NULL,
    holidays_list jsonb DEFAULT '[]'::jsonb,
    overtime_multiplier numeric(5,2) DEFAULT 1.50
);


--
-- Name: project_constraint_time_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_constraint_time_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_constraint_time_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_constraint_time_id_seq OWNED BY public.project_constraint_time.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    user_id integer,
    project_name character varying(255) NOT NULL,
    type character varying(50),
    status character varying(50) DEFAULT 'Planning'::character varying,
    base_cost numeric(15,2) DEFAULT 0.00,
    total_cost numeric(15,2) DEFAULT 0.00,
    target_deadline timestamp without time zone,
    penalty_per_day numeric(15,2),
    bonus_per_day numeric(15,2),
    search_vector tsvector,
    metadata_json jsonb DEFAULT '{}'::jsonb,
    num_tasks integer DEFAULT 0,
    num_edges integer DEFAULT 0,
    network_density numeric(5,4),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: task_resources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task_resources (
    task_id character varying(255) NOT NULL,
    resource_id integer NOT NULL,
    request_quantity numeric(15,2) NOT NULL,
    allocated_quantity numeric(15,2),
    labor_productivity numeric(15,2),
    equipment_utilization numeric(15,2),
    resource_substitutability integer
);


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasks (
    id character varying(255) NOT NULL,
    project_id integer NOT NULL,
    task_name character varying(255) NOT NULL,
    task_type character varying(100),
    status character varying(50) DEFAULT 'Pending'::character varying,
    baseline_start timestamp without time zone,
    type character varying(255),
    base_cost numeric(15,2) DEFAULT 0.00,
    total_cost numeric(15,2) DEFAULT 0.00,
    risk_factor numeric(10,4) DEFAULT 1.0000,
    duration_months numeric(15,2),
    duration_weeks numeric(15,2),
    duration_days numeric(15,2),
    duration_hours numeric(15,2),
    calendar_type character varying(50),
    internal_labor_cost numeric(15,2),
    overtime_cost numeric(15,2),
    equipment_fuel_cost numeric(15,2),
    qa_qc_cost numeric(15,2),
    material_cost numeric(15,2),
    outsourcing_cost numeric(15,2),
    training_cost numeric(15,2),
    facility_rent numeric(15,2),
    communication_cost numeric(15,2),
    utilities_cost numeric(15,2),
    insurance_cost numeric(15,2),
    licensing_cost numeric(15,2),
    warranty_cost numeric(15,2),
    complexity numeric(10,4),
    weather_contingency numeric(10,4),
    general_contingency numeric(10,4),
    rework_risk numeric(10,4),
    holding_cost numeric(15,2),
    international_freight numeric(15,2),
    handling_cost numeric(15,2),
    reverse_logistics numeric(15,2),
    defect_cost numeric(15,2),
    overtime_hours numeric(15,2),
    lag_time numeric(15,2),
    metadata_json jsonb
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: ai_recommendations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_recommendations ALTER COLUMN id SET DEFAULT nextval('public.ai_recommendations_id_seq'::regclass);


--
-- Name: ai_simulation_runs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_simulation_runs ALTER COLUMN id SET DEFAULT nextval('public.ai_simulation_runs_id_seq'::regclass);


--
-- Name: project_baselines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_baselines ALTER COLUMN id SET DEFAULT nextval('public.project_baselines_id_seq'::regclass);


--
-- Name: project_constraint_resource id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_resource ALTER COLUMN id SET DEFAULT nextval('public.project_constraint_resource_id_seq'::regclass);


--
-- Name: project_constraint_time id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_time ALTER COLUMN id SET DEFAULT nextval('public.project_constraint_time_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: ai_recommendations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ai_recommendations (id, simulation_run_id, option_name, action_type, target_tasks, human_message, modifications, impact, risk, is_applied, created_at) FROM stdin;
\.


--
-- Data for Name: ai_simulation_runs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ai_simulation_runs (id, project_id, ai_weights, status, results_summary, created_at) FROM stdin;
\.


--
-- Data for Name: project_baselines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_baselines (id, project_id, simulation_run_id, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: project_constraint_logic; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_constraint_logic (predecessor_id, successor_id, project_id, dependency_type, lag_months, lag_weeks, lag_days, lag_hours) FROM stdin;
15_1	15_2	15	FS	0.00	1.00	1.00	0.00
15_2	15_3	15	FS	0.00	7.00	0.00	2.00
15_3	15_4	15	FS	0.00	0.00	0.00	0.00
15_4	15_5	15	FS	0.00	0.00	0.00	2.00
15_5	15_6	15	FS	0.00	0.00	0.00	0.00
15_6	15_7	15	FS	0.00	2.00	0.00	0.00
15_7	15_8	15	FS	0.00	3.00	0.00	0.00
15_8	15_9	15	FS	0.00	0.00	0.00	0.00
15_9	15_10	15	FS	0.00	1.00	1.00	4.00
15_10	15_11	15	FS	0.00	2.00	0.00	0.00
15_11	15_12	15	FS	0.00	3.00	0.00	0.00
15_12	15_13	15	FS	0.00	4.00	0.00	0.00
15_13	15_14	15	FS	0.00	3.00	0.00	0.00
15_14	15_15	15	FS	0.00	6.00	0.00	0.00
15_15	15_16	15	FS	0.00	0.00	0.00	0.00
15_16	15_17	15	FS	0.00	7.00	3.00	4.00
15_17	15_18	15	FS	0.00	6.00	0.00	0.00
15_18	15_19	15	FS	0.00	0.00	0.00	0.00
15_8	15_20	15	FS	0.00	1.00	0.00	0.00
15_20	15_21	15	FS	0.00	1.00	2.00	0.00
15_21	15_22	15	FS	0.00	2.00	0.00	0.00
15_22	15_23	15	FS	0.00	1.00	0.00	0.00
15_23	15_24	15	FS	0.00	0.00	2.00	0.00
15_24	15_25	15	FS	0.00	0.00	1.00	6.00
15_25	15_26	15	FS	0.00	0.00	0.00	0.00
15_26	15_27	15	FS	0.00	8.00	0.00	0.00
15_19	15_27	15	FS	0.00	0.00	4.00	4.00
15_27	15_28	15	FS	0.00	0.00	0.00	4.00
15_28	15_29	15	FS	0.00	0.00	0.00	0.00
15_28	15_30	15	FS	0.00	0.00	0.00	0.00
15_28	15_31	15	FS	0.00	0.00	0.00	0.00
15_31	15_32	15	FS	0.00	0.00	0.00	0.00
15_46	15_33	15	FS	0.00	0.00	0.00	0.00
15_28	15_34	15	FS	0.00	0.00	0.00	0.00
15_34	15_35	15	FS	0.00	4.00	4.00	0.00
15_29	15_36	15	FS	0.00	0.00	0.00	0.00
15_31	15_36	15	FS	0.00	0.00	0.00	0.00
15_36	15_37	15	FS	0.00	3.00	2.00	0.00
15_35	15_37	15	FF	0.00	1.00	0.00	0.00
15_30	15_38	15	FS	0.00	0.00	0.00	0.00
15_32	15_38	15	FS	0.00	0.00	0.00	0.00
15_37	15_38	15	FS	0.00	0.00	0.00	0.00
15_38	15_39	15	FS	0.00	0.00	0.00	0.00
15_39	15_40	15	FS	0.00	0.00	0.00	0.00
15_40	15_41	15	FS	0.00	0.00	0.00	0.00
15_41	15_42	15	FS	0.00	0.00	0.00	0.00
15_42	15_43	15	FS	0.00	0.00	0.00	0.00
15_30	15_44	15	FS	0.00	0.00	0.00	0.00
15_32	15_44	15	FS	0.00	0.00	0.00	0.00
15_37	15_44	15	FS	0.00	0.00	0.00	0.00
15_44	15_45	15	FS	0.00	2.00	0.00	0.00
15_43	15_46	15	FS	0.00	0.00	0.00	0.00
15_45	15_46	15	FS	0.00	0.00	0.00	0.00
15_33	15_47	15	FS	0.00	0.00	0.00	0.00
15_47	15_48	15	FS	0.00	0.00	4.00	2.00
15_48	15_49	15	FS	0.00	0.00	0.00	0.00
16_1	16_2	16	FS	0.00	0.00	0.00	0.00
16_2	16_3	16	FS	0.00	0.00	0.00	0.00
16_3	16_4	16	FS	0.00	0.00	0.00	0.00
16_4	16_5	16	FS	0.00	0.00	0.00	0.00
16_5	16_6	16	FS	0.00	0.00	0.00	0.00
16_6	16_7	16	FS	0.00	0.00	0.00	0.00
16_7	16_8	16	FS	0.00	0.00	0.00	0.00
16_7	16_9	16	FS	0.00	0.00	0.00	0.00
16_9	16_14	16	FS	0.00	0.00	0.00	0.00
16_9	16_11	16	FS	0.00	0.00	0.00	0.00
16_11	16_12	16	FS	0.00	0.00	0.00	0.00
16_11	16_19	16	FS	0.00	0.00	0.00	0.00
16_19	16_20	16	FS	0.00	0.00	0.00	0.00
16_19	16_17	16	FS	0.00	0.00	0.00	0.00
16_17	16_22	16	FS	0.00	0.00	0.00	0.00
16_8	16_24	16	FS	0.00	0.00	0.00	0.00
16_12	16_24	16	FS	0.00	0.00	0.00	0.00
16_14	16_24	16	FS	0.00	0.00	0.00	0.00
16_20	16_24	16	FS	0.00	0.00	0.00	0.00
16_22	16_24	16	FS	0.00	0.00	0.00	0.00
16_24	16_25	16	FS	0.00	0.00	0.00	0.00
16_25	16_26	16	FS	0.00	0.00	0.00	0.00
16_26	16_27	16	FS	0.00	0.00	0.00	0.00
16_27	16_28	16	FS	0.00	0.00	0.00	0.00
16_28	16_29	16	FS	0.00	0.00	0.00	0.00
16_29	16_30	16	FS	0.00	0.00	0.00	0.00
16_30	16_31	16	FS	0.00	0.00	0.00	0.00
16_31	16_32	16	FS	0.00	0.00	0.00	0.00
16_32	16_33	16	FS	0.00	0.00	0.00	0.00
16_33	16_34	16	FS	0.00	0.00	0.00	0.00
16_34	16_35	16	FS	0.00	0.00	0.00	0.00
16_35	16_36	16	FS	0.00	0.00	0.00	0.00
16_8	16_41	16	FS	0.00	0.00	0.00	0.00
16_12	16_41	16	FS	0.00	0.00	0.00	0.00
16_14	16_41	16	FS	0.00	0.00	0.00	0.00
16_20	16_41	16	FS	0.00	0.00	0.00	0.00
16_22	16_41	16	FS	0.00	0.00	0.00	0.00
16_41	16_42	16	FS	0.00	0.00	0.00	0.00
16_42	16_38	16	FS	0.00	0.00	0.00	0.00
16_38	16_39	16	FS	0.00	0.00	0.00	0.00
16_41	16_63	16	FS	0.00	0.00	0.00	0.00
16_39	16_62	16	FS	0.00	0.00	0.00	0.00
16_62	16_66	16	FS	0.00	0.00	0.00	0.00
16_63	16_66	16	FS	0.00	0.00	0.00	0.00
16_66	16_67	16	FS	0.00	0.00	0.00	0.00
16_67	16_68	16	FS	0.00	0.00	0.00	0.00
16_68	16_69	16	FS	0.00	0.00	0.00	0.00
16_69	16_70	16	FS	0.00	0.00	0.00	0.00
16_70	16_82	16	FS	0.00	0.00	0.00	0.00
16_82	16_83	16	FS	0.00	0.00	0.00	0.00
16_83	16_75	16	FS	0.00	0.00	0.00	0.00
16_75	16_73	16	FS	0.00	0.00	0.00	0.00
16_73	16_72	16	FS	0.00	0.00	0.00	0.00
16_83	16_80	16	FS	0.00	0.00	0.00	0.00
16_75	16_78	16	FS	0.00	0.00	0.00	0.00
16_75	16_77	16	FS	0.00	0.00	0.00	0.00
16_72	16_48	16	FS	0.00	0.00	0.00	0.00
16_77	16_48	16	FS	0.00	0.00	0.00	0.00
16_78	16_48	16	FS	0.00	0.00	0.00	0.00
16_80	16_48	16	FS	0.00	0.00	0.00	0.00
16_48	16_49	16	FS	0.00	0.00	0.00	0.00
16_49	16_46	16	FS	0.00	0.00	0.00	0.00
16_46	16_44	16	FS	0.00	0.00	0.00	0.00
16_36	16_58	16	FS	0.00	0.00	0.00	0.00
16_44	16_58	16	FS	0.00	0.00	0.00	0.00
16_58	16_59	16	FS	0.00	0.00	0.00	0.00
16_59	16_52	16	FS	0.00	0.00	0.00	0.00
16_52	16_51	16	FS	0.00	0.00	0.00	0.00
16_51	16_55	16	FS	0.00	0.00	0.00	0.00
16_55	16_56	16	FS	0.00	0.00	0.00	0.00
16_56	16_85	16	FS	0.00	0.00	0.00	0.00
16_36	16_85	16	FS	0.00	0.00	0.00	0.00
16_85	16_86	16	FS	0.00	0.00	0.00	0.00
16_85	16_87	16	FS	0.00	0.00	0.00	0.00
16_87	16_88	16	FS	0.00	0.00	0.00	0.00
16_85	16_89	16	FS	0.00	0.00	0.00	0.00
16_86	16_91	16	FS	0.00	0.00	0.00	0.00
16_88	16_91	16	FS	0.00	0.00	0.00	0.00
16_89	16_91	16	FS	0.00	0.00	0.00	0.00
16_86	16_92	16	FS	0.00	0.00	0.00	0.00
16_88	16_92	16	FS	0.00	0.00	0.00	0.00
16_89	16_92	16	FS	0.00	0.00	0.00	0.00
16_92	16_93	16	FS	0.00	0.00	0.00	0.00
16_93	16_94	16	FS	0.00	0.00	0.00	0.00
17_1	17_2	17	FS	0.00	0.00	0.00	0.00
17_2	17_3	17	FS	0.00	0.00	0.00	0.00
17_551	17_11	17	SS	0.00	3.00	4.00	0.00
17_6	17_7	17	FS	0.00	0.00	0.00	0.00
17_3	17_526	17	FS	0.00	0.00	0.00	0.00
17_7	17_526	17	FS	0.00	0.00	0.00	0.00
17_11	17_526	17	SS	0.00	0.00	3.00	0.00
17_3	17_527	17	FS	0.00	0.00	0.00	0.00
17_7	17_527	17	FS	0.00	0.00	0.00	0.00
17_11	17_527	17	SS	0.00	0.00	3.00	0.00
17_3	17_528	17	FS	0.00	0.00	0.00	0.00
17_7	17_528	17	FS	0.00	0.00	0.00	0.00
17_11	17_528	17	SS	0.00	0.00	3.00	0.00
17_3	17_529	17	FS	0.00	0.00	0.00	0.00
17_7	17_529	17	FS	0.00	0.00	0.00	0.00
17_11	17_529	17	SS	0.00	0.00	3.00	0.00
17_3	17_530	17	FS	0.00	0.00	0.00	0.00
17_7	17_530	17	FS	0.00	0.00	0.00	0.00
17_11	17_530	17	SS	0.00	0.00	3.00	0.00
17_3	17_531	17	FS	0.00	0.00	0.00	0.00
17_7	17_531	17	FS	0.00	0.00	0.00	0.00
17_11	17_531	17	SS	0.00	0.00	3.00	0.00
17_3	17_532	17	FS	0.00	0.00	0.00	0.00
17_7	17_532	17	FS	0.00	0.00	0.00	0.00
17_11	17_532	17	SS	0.00	0.00	3.00	0.00
17_3	17_533	17	FS	0.00	0.00	0.00	0.00
17_7	17_533	17	FS	0.00	0.00	0.00	0.00
17_11	17_533	17	SS	0.00	0.00	3.00	0.00
17_3	17_534	17	FS	0.00	0.00	0.00	0.00
17_7	17_534	17	FS	0.00	0.00	0.00	0.00
17_11	17_534	17	SS	0.00	0.00	3.00	0.00
17_3	17_535	17	FS	0.00	0.00	0.00	0.00
17_7	17_535	17	FS	0.00	0.00	0.00	0.00
17_11	17_535	17	SS	0.00	0.00	3.00	0.00
17_3	17_536	17	FS	0.00	0.00	0.00	0.00
17_7	17_536	17	FS	0.00	0.00	0.00	0.00
17_11	17_536	17	SS	0.00	0.00	3.00	0.00
17_3	17_537	17	FS	0.00	0.00	0.00	0.00
17_7	17_537	17	FS	0.00	0.00	0.00	0.00
17_11	17_537	17	SS	0.00	0.00	3.00	0.00
17_3	17_538	17	FS	0.00	0.00	0.00	0.00
17_7	17_538	17	FS	0.00	0.00	0.00	0.00
17_11	17_538	17	SS	0.00	0.00	3.00	0.00
17_3	17_539	17	FS	0.00	0.00	0.00	0.00
17_7	17_539	17	FS	0.00	0.00	0.00	0.00
17_11	17_539	17	SS	0.00	0.00	3.00	0.00
17_3	17_540	17	FS	0.00	0.00	0.00	0.00
17_7	17_540	17	FS	0.00	0.00	0.00	0.00
17_11	17_540	17	SS	0.00	0.00	3.00	0.00
17_3	17_541	17	FS	0.00	0.00	0.00	0.00
17_7	17_541	17	FS	0.00	0.00	0.00	0.00
17_11	17_541	17	SS	0.00	0.00	3.00	0.00
17_3	17_542	17	FS	0.00	0.00	0.00	0.00
17_7	17_542	17	FS	0.00	0.00	0.00	0.00
17_11	17_542	17	SS	0.00	0.00	3.00	0.00
17_3	17_543	17	FS	0.00	0.00	0.00	0.00
17_7	17_543	17	FS	0.00	0.00	0.00	0.00
17_11	17_543	17	SS	0.00	0.00	3.00	0.00
17_3	17_544	17	FS	0.00	0.00	0.00	0.00
17_7	17_544	17	FS	0.00	0.00	0.00	0.00
17_11	17_544	17	SS	0.00	0.00	3.00	0.00
17_3	17_545	17	FS	0.00	0.00	0.00	0.00
17_7	17_545	17	FS	0.00	0.00	0.00	0.00
17_11	17_545	17	SS	0.00	0.00	3.00	0.00
17_3	17_546	17	FS	0.00	0.00	0.00	0.00
17_7	17_546	17	FS	0.00	0.00	0.00	0.00
17_11	17_546	17	SS	0.00	0.00	3.00	0.00
17_3	17_547	17	FS	0.00	0.00	0.00	0.00
17_7	17_547	17	FS	0.00	0.00	0.00	0.00
17_11	17_547	17	SS	0.00	0.00	3.00	0.00
17_3	17_548	17	FS	0.00	0.00	0.00	0.00
17_7	17_548	17	FS	0.00	0.00	0.00	0.00
17_11	17_548	17	SS	0.00	0.00	3.00	0.00
17_3	17_549	17	FS	0.00	0.00	0.00	0.00
17_7	17_549	17	FS	0.00	0.00	0.00	0.00
17_11	17_549	17	SS	0.00	0.00	3.00	0.00
17_3	17_550	17	FS	0.00	0.00	0.00	0.00
17_7	17_550	17	FS	0.00	0.00	0.00	0.00
17_11	17_550	17	SS	0.00	0.00	3.00	0.00
17_526	17_12	17	FS	0.00	0.00	0.00	0.00
17_527	17_13	17	FS	0.00	0.00	0.00	0.00
17_528	17_14	17	FS	0.00	0.00	0.00	0.00
17_529	17_196	17	FS	0.00	0.00	0.00	0.00
17_530	17_197	17	FS	0.00	0.00	0.00	0.00
17_531	17_198	17	FS	0.00	0.00	0.00	0.00
17_532	17_199	17	FS	0.00	0.00	0.00	0.00
17_533	17_200	17	FS	0.00	0.00	0.00	0.00
17_534	17_201	17	FS	0.00	0.00	0.00	0.00
17_535	17_202	17	FS	0.00	0.00	0.00	0.00
17_536	17_203	17	FS	0.00	0.00	0.00	0.00
17_537	17_204	17	FS	0.00	0.00	0.00	0.00
17_538	17_205	17	FS	0.00	0.00	0.00	0.00
17_539	17_206	17	FS	0.00	0.00	0.00	0.00
17_540	17_207	17	FS	0.00	0.00	0.00	0.00
17_541	17_208	17	FS	0.00	0.00	0.00	0.00
17_542	17_209	17	FS	0.00	0.00	0.00	0.00
17_543	17_210	17	FS	0.00	0.00	0.00	0.00
17_544	17_211	17	FS	0.00	0.00	0.00	0.00
17_545	17_212	17	FS	0.00	0.00	0.00	0.00
17_546	17_213	17	FS	0.00	0.00	0.00	0.00
17_547	17_214	17	FS	0.00	0.00	0.00	0.00
17_548	17_215	17	FS	0.00	0.00	0.00	0.00
17_549	17_216	17	FS	0.00	0.00	0.00	0.00
17_550	17_217	17	FS	0.00	0.00	0.00	0.00
17_12	17_16	17	FS	0.00	0.00	0.00	0.00
17_16	17_17	17	FS	0.00	0.00	0.00	0.00
17_13	17_162	17	FS	0.00	0.00	0.00	0.00
17_14	17_218	17	FS	0.00	0.00	0.00	0.00
17_196	17_219	17	FS	0.00	0.00	0.00	0.00
17_197	17_220	17	FS	0.00	0.00	0.00	0.00
17_198	17_221	17	FS	0.00	0.00	0.00	0.00
17_199	17_222	17	FS	0.00	0.00	0.00	0.00
17_200	17_223	17	FS	0.00	0.00	0.00	0.00
17_201	17_224	17	FS	0.00	0.00	0.00	0.00
17_202	17_225	17	FS	0.00	0.00	0.00	0.00
17_203	17_226	17	FS	0.00	0.00	0.00	0.00
17_204	17_227	17	FS	0.00	0.00	0.00	0.00
17_205	17_228	17	FS	0.00	0.00	0.00	0.00
17_206	17_229	17	FS	0.00	0.00	0.00	0.00
17_207	17_230	17	FS	0.00	0.00	0.00	0.00
17_208	17_231	17	FS	0.00	0.00	0.00	0.00
17_209	17_232	17	FS	0.00	0.00	0.00	0.00
17_210	17_233	17	FS	0.00	0.00	0.00	0.00
17_211	17_234	17	FS	0.00	0.00	0.00	0.00
17_212	17_235	17	FS	0.00	0.00	0.00	0.00
17_213	17_236	17	FS	0.00	0.00	0.00	0.00
17_214	17_237	17	FS	0.00	0.00	0.00	0.00
17_215	17_238	17	FS	0.00	0.00	0.00	0.00
17_216	17_239	17	FS	0.00	0.00	0.00	0.00
17_217	17_240	17	FS	0.00	0.00	0.00	0.00
17_162	17_241	17	FS	0.00	0.00	0.00	0.00
17_218	17_242	17	FS	0.00	0.00	0.00	0.00
17_219	17_243	17	FS	0.00	0.00	0.00	0.00
17_220	17_244	17	FS	0.00	0.00	0.00	0.00
17_221	17_245	17	FS	0.00	0.00	0.00	0.00
17_222	17_246	17	FS	0.00	0.00	0.00	0.00
17_223	17_247	17	FS	0.00	0.00	0.00	0.00
17_224	17_248	17	FS	0.00	0.00	0.00	0.00
17_225	17_249	17	FS	0.00	0.00	0.00	0.00
17_226	17_250	17	FS	0.00	0.00	0.00	0.00
17_227	17_251	17	FS	0.00	0.00	0.00	0.00
17_228	17_252	17	FS	0.00	0.00	0.00	0.00
17_229	17_253	17	FS	0.00	0.00	0.00	0.00
17_230	17_254	17	FS	0.00	0.00	0.00	0.00
17_231	17_255	17	FS	0.00	0.00	0.00	0.00
17_232	17_256	17	FS	0.00	0.00	0.00	0.00
17_233	17_257	17	FS	0.00	0.00	0.00	0.00
17_234	17_258	17	FS	0.00	0.00	0.00	0.00
17_235	17_259	17	FS	0.00	0.00	0.00	0.00
17_236	17_260	17	FS	0.00	0.00	0.00	0.00
17_237	17_261	17	FS	0.00	0.00	0.00	0.00
17_238	17_262	17	FS	0.00	0.00	0.00	0.00
17_239	17_263	17	FS	0.00	0.00	0.00	0.00
17_240	17_264	17	FS	0.00	0.00	0.00	0.00
17_21	17_25	17	SS	0.00	5.00	5.00	0.00
17_23	17_25	17	SS	0.00	5.00	5.00	0.00
17_25	17_337	17	FS	0.00	0.00	0.00	0.00
17_337	17_338	17	FS	0.00	0.00	0.00	0.00
17_338	17_339	17	FS	0.00	0.00	0.00	0.00
17_339	17_340	17	FS	0.00	0.00	0.00	0.00
17_340	17_341	17	FS	0.00	0.00	0.00	0.00
17_341	17_342	17	FS	0.00	0.00	0.00	0.00
17_342	17_343	17	FS	0.00	0.00	0.00	0.00
17_343	17_344	17	FS	0.00	0.00	0.00	0.00
17_344	17_345	17	FS	0.00	0.00	0.00	0.00
17_345	17_346	17	FS	0.00	0.00	0.00	0.00
17_346	17_347	17	FS	0.00	0.00	0.00	0.00
17_347	17_348	17	FS	0.00	0.00	0.00	0.00
17_348	17_349	17	FS	0.00	0.00	0.00	0.00
17_349	17_350	17	FS	0.00	0.00	0.00	0.00
17_350	17_351	17	FS	0.00	0.00	0.00	0.00
17_351	17_352	17	FS	0.00	0.00	0.00	0.00
17_352	17_353	17	FS	0.00	0.00	0.00	0.00
17_353	17_354	17	FS	0.00	0.00	0.00	0.00
17_354	17_355	17	FS	0.00	0.00	0.00	0.00
17_355	17_356	17	FS	0.00	0.00	0.00	0.00
17_356	17_357	17	FS	0.00	0.00	0.00	0.00
17_357	17_358	17	FS	0.00	0.00	0.00	0.00
17_358	17_359	17	FS	0.00	0.00	0.00	0.00
17_25	17_29	17	FS	0.00	0.00	0.00	0.00
17_27	17_29	17	SS	0.00	5.00	5.00	0.00
17_337	17_360	17	FS	0.00	0.00	0.00	0.00
17_27	17_360	17	SS	0.00	5.00	5.00	0.00
17_338	17_361	17	FS	0.00	0.00	0.00	0.00
17_27	17_361	17	SS	0.00	5.00	5.00	0.00
17_339	17_362	17	FS	0.00	0.00	0.00	0.00
17_27	17_362	17	SS	0.00	5.00	5.00	0.00
17_27	17_363	17	SS	0.00	5.00	5.00	0.00
17_341	17_364	17	FS	0.00	0.00	0.00	0.00
17_27	17_364	17	SS	0.00	5.00	5.00	0.00
17_342	17_365	17	FS	0.00	0.00	0.00	0.00
17_27	17_365	17	SS	0.00	5.00	5.00	0.00
17_343	17_366	17	FS	0.00	0.00	0.00	0.00
17_27	17_366	17	SS	0.00	5.00	5.00	0.00
17_344	17_367	17	FS	0.00	0.00	0.00	0.00
17_27	17_367	17	SS	0.00	5.00	5.00	0.00
17_345	17_368	17	FS	0.00	0.00	0.00	0.00
17_27	17_368	17	SS	0.00	5.00	5.00	0.00
17_346	17_369	17	FS	0.00	0.00	0.00	0.00
17_27	17_369	17	SS	0.00	5.00	5.00	0.00
17_347	17_370	17	FS	0.00	0.00	0.00	0.00
17_27	17_370	17	SS	0.00	5.00	5.00	0.00
17_348	17_371	17	FS	0.00	0.00	0.00	0.00
17_27	17_371	17	SS	0.00	5.00	5.00	0.00
17_349	17_372	17	FS	0.00	0.00	0.00	0.00
17_27	17_372	17	SS	0.00	5.00	5.00	0.00
17_350	17_373	17	FS	0.00	0.00	0.00	0.00
17_27	17_373	17	SS	0.00	5.00	5.00	0.00
17_351	17_374	17	FS	0.00	0.00	0.00	0.00
17_27	17_374	17	SS	0.00	5.00	5.00	0.00
17_352	17_375	17	FS	0.00	0.00	0.00	0.00
17_27	17_375	17	SS	0.00	5.00	5.00	0.00
17_353	17_376	17	FS	0.00	0.00	0.00	0.00
17_27	17_376	17	SS	0.00	5.00	5.00	0.00
17_354	17_377	17	FS	0.00	0.00	0.00	0.00
17_27	17_377	17	SS	0.00	5.00	5.00	0.00
17_355	17_378	17	FS	0.00	0.00	0.00	0.00
17_27	17_378	17	SS	0.00	5.00	5.00	0.00
17_356	17_379	17	FS	0.00	0.00	0.00	0.00
17_27	17_379	17	SS	0.00	5.00	5.00	0.00
17_357	17_380	17	FS	0.00	0.00	0.00	0.00
17_27	17_380	17	SS	0.00	5.00	5.00	0.00
17_358	17_381	17	FS	0.00	0.00	0.00	0.00
17_27	17_381	17	SS	0.00	5.00	5.00	0.00
17_359	17_382	17	FS	0.00	0.00	0.00	0.00
17_27	17_382	17	SS	0.00	5.00	5.00	0.00
17_29	17_31	17	FS	0.00	0.00	0.00	0.00
17_360	17_383	17	FS	0.00	0.00	0.00	0.00
17_361	17_384	17	FS	0.00	0.00	0.00	0.00
17_362	17_385	17	FS	0.00	0.00	0.00	0.00
17_363	17_386	17	FS	0.00	0.00	0.00	0.00
17_364	17_387	17	FS	0.00	0.00	0.00	0.00
17_365	17_388	17	FS	0.00	0.00	0.00	0.00
17_366	17_389	17	FS	0.00	0.00	0.00	0.00
17_367	17_390	17	FS	0.00	0.00	0.00	0.00
17_368	17_391	17	FS	0.00	0.00	0.00	0.00
17_369	17_392	17	FS	0.00	0.00	0.00	0.00
17_370	17_393	17	FS	0.00	0.00	0.00	0.00
17_371	17_394	17	FS	0.00	0.00	0.00	0.00
17_372	17_395	17	FS	0.00	0.00	0.00	0.00
17_373	17_396	17	FS	0.00	0.00	0.00	0.00
17_374	17_397	17	FS	0.00	0.00	0.00	0.00
17_375	17_398	17	FS	0.00	0.00	0.00	0.00
17_376	17_399	17	FS	0.00	0.00	0.00	0.00
17_377	17_400	17	FS	0.00	0.00	0.00	0.00
17_378	17_401	17	FS	0.00	0.00	0.00	0.00
17_379	17_402	17	FS	0.00	0.00	0.00	0.00
17_380	17_403	17	FS	0.00	0.00	0.00	0.00
17_381	17_404	17	FS	0.00	0.00	0.00	0.00
17_382	17_405	17	FS	0.00	0.00	0.00	0.00
17_31	17_313	17	FS	0.00	0.00	0.00	0.00
17_383	17_314	17	FS	0.00	0.00	0.00	0.00
17_384	17_315	17	FS	0.00	0.00	0.00	0.00
17_385	17_316	17	FS	0.00	0.00	0.00	0.00
17_386	17_317	17	FS	0.00	0.00	0.00	0.00
17_387	17_318	17	FS	0.00	0.00	0.00	0.00
17_388	17_319	17	FS	0.00	0.00	0.00	0.00
17_389	17_320	17	FS	0.00	0.00	0.00	0.00
17_390	17_321	17	FS	0.00	0.00	0.00	0.00
17_391	17_322	17	FS	0.00	0.00	0.00	0.00
17_392	17_323	17	FS	0.00	0.00	0.00	0.00
17_393	17_324	17	FS	0.00	0.00	0.00	0.00
17_394	17_325	17	FS	0.00	0.00	0.00	0.00
17_395	17_326	17	FS	0.00	0.00	0.00	0.00
17_396	17_327	17	FS	0.00	0.00	0.00	0.00
17_397	17_328	17	FS	0.00	0.00	0.00	0.00
17_398	17_329	17	FS	0.00	0.00	0.00	0.00
17_399	17_330	17	FS	0.00	0.00	0.00	0.00
17_400	17_331	17	FS	0.00	0.00	0.00	0.00
17_401	17_332	17	FS	0.00	0.00	0.00	0.00
17_402	17_333	17	FS	0.00	0.00	0.00	0.00
17_403	17_334	17	FS	0.00	0.00	0.00	0.00
17_404	17_335	17	FS	0.00	0.00	0.00	0.00
17_405	17_336	17	FS	0.00	0.00	0.00	0.00
17_313	17_289	17	FS	0.00	0.00	0.00	0.00
17_241	17_289	17	FS	0.00	2.00	1.00	0.00
17_314	17_290	17	FS	0.00	0.00	0.00	0.00
17_242	17_290	17	FS	0.00	2.00	1.00	0.00
17_315	17_291	17	FS	0.00	0.00	0.00	0.00
17_243	17_291	17	FS	0.00	2.00	1.00	0.00
17_316	17_292	17	FS	0.00	0.00	0.00	0.00
17_244	17_292	17	FS	0.00	2.00	1.00	0.00
17_317	17_293	17	FS	0.00	0.00	0.00	0.00
17_245	17_293	17	FS	0.00	2.00	1.00	0.00
17_318	17_294	17	FS	0.00	0.00	0.00	0.00
17_246	17_294	17	FS	0.00	2.00	1.00	0.00
17_319	17_295	17	FS	0.00	0.00	0.00	0.00
17_247	17_295	17	FS	0.00	2.00	1.00	0.00
17_320	17_296	17	FS	0.00	0.00	0.00	0.00
17_248	17_296	17	FS	0.00	2.00	1.00	0.00
17_321	17_297	17	FS	0.00	0.00	0.00	0.00
17_249	17_297	17	FS	0.00	2.00	1.00	0.00
17_322	17_298	17	FS	0.00	0.00	0.00	0.00
17_250	17_298	17	FS	0.00	2.00	1.00	0.00
17_323	17_299	17	FS	0.00	0.00	0.00	0.00
17_251	17_299	17	FS	0.00	2.00	1.00	0.00
17_324	17_300	17	FS	0.00	0.00	0.00	0.00
17_252	17_300	17	FS	0.00	2.00	1.00	0.00
17_325	17_301	17	FS	0.00	0.00	0.00	0.00
17_253	17_301	17	FS	0.00	2.00	1.00	0.00
17_326	17_302	17	FS	0.00	0.00	0.00	0.00
17_254	17_302	17	FS	0.00	2.00	1.00	0.00
17_327	17_303	17	FS	0.00	0.00	0.00	0.00
17_255	17_303	17	FS	0.00	2.00	1.00	0.00
17_328	17_304	17	FS	0.00	0.00	0.00	0.00
17_256	17_304	17	FS	0.00	2.00	1.00	0.00
17_329	17_305	17	FS	0.00	0.00	0.00	0.00
17_257	17_305	17	FS	0.00	2.00	1.00	0.00
17_330	17_306	17	FS	0.00	0.00	0.00	0.00
17_258	17_306	17	FS	0.00	2.00	1.00	0.00
17_331	17_307	17	FS	0.00	0.00	0.00	0.00
17_259	17_307	17	FS	0.00	2.00	1.00	0.00
17_332	17_308	17	FS	0.00	0.00	0.00	0.00
17_260	17_308	17	FS	0.00	2.00	1.00	0.00
17_333	17_309	17	FS	0.00	0.00	0.00	0.00
17_261	17_309	17	FS	0.00	2.00	1.00	0.00
17_334	17_310	17	FS	0.00	0.00	0.00	0.00
17_262	17_310	17	FS	0.00	2.00	1.00	0.00
17_335	17_311	17	FS	0.00	0.00	0.00	0.00
17_263	17_311	17	FS	0.00	2.00	1.00	0.00
17_336	17_312	17	FS	0.00	0.00	0.00	0.00
17_264	17_312	17	FS	0.00	2.00	1.00	0.00
17_289	17_265	17	FS	0.00	0.00	0.00	0.00
17_290	17_266	17	FS	0.00	0.00	0.00	0.00
17_291	17_267	17	FS	0.00	0.00	0.00	0.00
17_292	17_268	17	FS	0.00	0.00	0.00	0.00
17_293	17_269	17	FS	0.00	0.00	0.00	0.00
17_294	17_270	17	FS	0.00	0.00	0.00	0.00
17_295	17_271	17	FS	0.00	0.00	0.00	0.00
17_296	17_272	17	FS	0.00	0.00	0.00	0.00
17_297	17_273	17	FS	0.00	0.00	0.00	0.00
17_298	17_274	17	FS	0.00	0.00	0.00	0.00
17_299	17_275	17	FS	0.00	0.00	0.00	0.00
17_300	17_276	17	FS	0.00	0.00	0.00	0.00
17_301	17_277	17	FS	0.00	0.00	0.00	0.00
17_302	17_278	17	FS	0.00	0.00	0.00	0.00
17_303	17_279	17	FS	0.00	0.00	0.00	0.00
17_304	17_280	17	FS	0.00	0.00	0.00	0.00
17_305	17_281	17	FS	0.00	0.00	0.00	0.00
17_306	17_282	17	FS	0.00	0.00	0.00	0.00
17_307	17_283	17	FS	0.00	0.00	0.00	0.00
17_308	17_284	17	FS	0.00	0.00	0.00	0.00
17_309	17_285	17	FS	0.00	0.00	0.00	0.00
17_310	17_286	17	FS	0.00	0.00	0.00	0.00
17_311	17_287	17	FS	0.00	0.00	0.00	0.00
17_312	17_288	17	FS	0.00	0.00	0.00	0.00
17_46	17_53	17	SS	0.00	28.00	4.00	0.00
17_47	17_52	17	SS	0.00	28.00	4.00	0.00
17_48	17_51	17	SS	0.00	28.00	4.00	0.00
17_49	17_50	17	SS	0.00	28.00	4.00	0.00
17_51	17_57	17	FS	0.00	0.00	0.00	0.00
17_50	17_57	17	FS	0.00	0.00	0.00	0.00
17_56	17_57	17	FS	0.00	0.00	0.00	0.00
17_52	17_58	17	FS	0.00	0.00	0.00	0.00
17_56	17_58	17	FS	0.00	0.00	0.00	0.00
17_53	17_502	17	SS	0.00	2.00	6.00	0.00
17_57	17_502	17	SS	0.00	2.00	6.00	0.00
17_58	17_502	17	SS	0.00	2.00	6.00	0.00
17_53	17_503	17	SS	0.00	2.00	6.00	0.00
17_57	17_503	17	SS	0.00	2.00	6.00	0.00
17_58	17_503	17	SS	0.00	2.00	6.00	0.00
17_53	17_504	17	SS	0.00	2.00	6.00	0.00
17_57	17_504	17	SS	0.00	2.00	6.00	0.00
17_58	17_504	17	SS	0.00	2.00	6.00	0.00
17_53	17_505	17	SS	0.00	2.00	6.00	0.00
17_57	17_505	17	SS	0.00	2.00	6.00	0.00
17_58	17_505	17	SS	0.00	2.00	6.00	0.00
17_53	17_506	17	SS	0.00	2.00	6.00	0.00
17_57	17_506	17	SS	0.00	2.00	6.00	0.00
17_58	17_506	17	SS	0.00	2.00	6.00	0.00
17_53	17_507	17	SS	0.00	2.00	6.00	0.00
17_57	17_507	17	SS	0.00	2.00	6.00	0.00
17_58	17_507	17	SS	0.00	2.00	6.00	0.00
17_53	17_508	17	SS	0.00	2.00	6.00	0.00
17_57	17_508	17	SS	0.00	2.00	6.00	0.00
17_58	17_508	17	SS	0.00	2.00	6.00	0.00
17_53	17_509	17	SS	0.00	2.00	6.00	0.00
17_57	17_509	17	SS	0.00	2.00	6.00	0.00
17_58	17_509	17	SS	0.00	2.00	6.00	0.00
17_53	17_510	17	SS	0.00	2.00	6.00	0.00
17_57	17_510	17	SS	0.00	2.00	6.00	0.00
17_58	17_510	17	SS	0.00	2.00	6.00	0.00
17_53	17_511	17	SS	0.00	2.00	6.00	0.00
17_57	17_511	17	SS	0.00	2.00	6.00	0.00
17_58	17_511	17	SS	0.00	2.00	6.00	0.00
17_53	17_512	17	SS	0.00	2.00	6.00	0.00
17_57	17_512	17	SS	0.00	2.00	6.00	0.00
17_58	17_512	17	SS	0.00	2.00	6.00	0.00
17_53	17_513	17	SS	0.00	2.00	6.00	0.00
17_57	17_513	17	SS	0.00	2.00	6.00	0.00
17_58	17_513	17	SS	0.00	2.00	6.00	0.00
17_53	17_514	17	SS	0.00	2.00	6.00	0.00
17_57	17_514	17	SS	0.00	2.00	6.00	0.00
17_58	17_514	17	SS	0.00	2.00	6.00	0.00
17_53	17_515	17	SS	0.00	2.00	6.00	0.00
17_57	17_515	17	SS	0.00	2.00	6.00	0.00
17_58	17_515	17	SS	0.00	2.00	6.00	0.00
17_53	17_516	17	SS	0.00	2.00	6.00	0.00
17_57	17_516	17	SS	0.00	2.00	6.00	0.00
17_58	17_516	17	SS	0.00	2.00	6.00	0.00
17_53	17_517	17	SS	0.00	2.00	6.00	0.00
17_57	17_517	17	SS	0.00	2.00	6.00	0.00
17_58	17_517	17	SS	0.00	2.00	6.00	0.00
17_53	17_518	17	SS	0.00	2.00	6.00	0.00
17_57	17_518	17	SS	0.00	2.00	6.00	0.00
17_58	17_518	17	SS	0.00	2.00	6.00	0.00
17_53	17_519	17	SS	0.00	2.00	6.00	0.00
17_57	17_519	17	SS	0.00	2.00	6.00	0.00
17_58	17_519	17	SS	0.00	2.00	6.00	0.00
17_53	17_520	17	SS	0.00	2.00	6.00	0.00
17_57	17_520	17	SS	0.00	2.00	6.00	0.00
17_58	17_520	17	SS	0.00	2.00	6.00	0.00
17_53	17_521	17	SS	0.00	2.00	6.00	0.00
17_57	17_521	17	SS	0.00	2.00	6.00	0.00
17_58	17_521	17	SS	0.00	2.00	6.00	0.00
17_53	17_522	17	SS	0.00	2.00	6.00	0.00
17_57	17_522	17	SS	0.00	2.00	6.00	0.00
17_58	17_522	17	SS	0.00	2.00	6.00	0.00
17_53	17_523	17	SS	0.00	2.00	6.00	0.00
17_57	17_523	17	SS	0.00	2.00	6.00	0.00
17_58	17_523	17	SS	0.00	2.00	6.00	0.00
17_53	17_524	17	SS	0.00	2.00	6.00	0.00
17_57	17_524	17	SS	0.00	2.00	6.00	0.00
17_58	17_524	17	SS	0.00	2.00	6.00	0.00
17_53	17_525	17	SS	0.00	2.00	6.00	0.00
17_57	17_525	17	SS	0.00	2.00	6.00	0.00
17_58	17_525	17	SS	0.00	2.00	6.00	0.00
17_502	17_478	17	FS	0.00	0.00	0.00	0.00
17_265	17_478	17	FS	0.00	0.00	6.00	4.00
17_503	17_479	17	FS	0.00	0.00	0.00	0.00
17_266	17_479	17	FS	0.00	0.00	6.00	4.00
17_504	17_480	17	FS	0.00	0.00	0.00	0.00
17_267	17_480	17	FS	0.00	0.00	6.00	4.00
17_505	17_481	17	FS	0.00	0.00	0.00	0.00
17_268	17_481	17	FS	0.00	0.00	6.00	4.00
17_506	17_482	17	FS	0.00	0.00	0.00	0.00
17_269	17_482	17	FS	0.00	0.00	6.00	4.00
17_507	17_483	17	FS	0.00	0.00	0.00	0.00
17_270	17_483	17	FS	0.00	0.00	6.00	4.00
17_508	17_484	17	FS	0.00	0.00	0.00	0.00
17_271	17_484	17	FS	0.00	0.00	6.00	4.00
17_509	17_485	17	FS	0.00	0.00	0.00	0.00
17_272	17_485	17	FS	0.00	0.00	6.00	4.00
17_510	17_486	17	FS	0.00	0.00	0.00	0.00
17_273	17_486	17	FS	0.00	0.00	6.00	4.00
17_511	17_487	17	FS	0.00	0.00	0.00	0.00
17_274	17_487	17	FS	0.00	0.00	6.00	4.00
17_512	17_488	17	FS	0.00	0.00	0.00	0.00
17_275	17_488	17	FS	0.00	0.00	6.00	4.00
17_513	17_489	17	FS	0.00	0.00	0.00	0.00
17_276	17_489	17	FS	0.00	0.00	6.00	4.00
17_514	17_490	17	FS	0.00	0.00	0.00	0.00
17_277	17_490	17	FS	0.00	0.00	6.00	4.00
17_515	17_491	17	FS	0.00	0.00	0.00	0.00
17_278	17_491	17	FS	0.00	0.00	6.00	4.00
17_516	17_492	17	FS	0.00	0.00	0.00	0.00
17_279	17_492	17	FS	0.00	0.00	6.00	4.00
17_517	17_493	17	FS	0.00	0.00	0.00	0.00
17_280	17_493	17	FS	0.00	0.00	6.00	4.00
17_518	17_494	17	FS	0.00	0.00	0.00	0.00
17_281	17_494	17	FS	0.00	0.00	6.00	4.00
17_519	17_495	17	FS	0.00	0.00	0.00	0.00
17_282	17_495	17	FS	0.00	0.00	6.00	4.00
17_520	17_496	17	FS	0.00	0.00	0.00	0.00
17_283	17_496	17	FS	0.00	0.00	6.00	4.00
17_521	17_497	17	FS	0.00	0.00	0.00	0.00
17_284	17_497	17	FS	0.00	0.00	6.00	4.00
17_522	17_498	17	FS	0.00	0.00	0.00	0.00
17_285	17_498	17	FS	0.00	0.00	6.00	4.00
17_523	17_499	17	FS	0.00	0.00	0.00	0.00
17_286	17_499	17	FS	0.00	0.00	6.00	4.00
17_524	17_500	17	FS	0.00	0.00	0.00	0.00
17_287	17_500	17	FS	0.00	0.00	6.00	0.00
17_525	17_501	17	FS	0.00	0.00	0.00	0.00
17_288	17_501	17	FS	0.00	0.00	6.00	0.00
17_112	17_454	17	FS	0.00	0.00	0.00	0.00
17_478	17_454	17	SS	0.00	0.00	3.00	0.00
17_112	17_455	17	FS	0.00	0.00	0.00	0.00
17_479	17_455	17	SS	0.00	0.00	3.00	0.00
17_112	17_456	17	FS	0.00	0.00	0.00	0.00
17_480	17_456	17	SS	0.00	0.00	3.00	0.00
17_112	17_457	17	FS	0.00	0.00	0.00	0.00
17_481	17_457	17	SS	0.00	0.00	3.00	0.00
17_112	17_458	17	FS	0.00	0.00	0.00	0.00
17_482	17_458	17	SS	0.00	0.00	3.00	0.00
17_112	17_459	17	FS	0.00	0.00	0.00	0.00
17_483	17_459	17	SS	0.00	0.00	3.00	0.00
17_112	17_460	17	FS	0.00	0.00	0.00	0.00
17_484	17_460	17	FS	0.00	0.00	3.00	0.00
17_112	17_461	17	FS	0.00	0.00	0.00	0.00
17_485	17_461	17	SS	0.00	0.00	3.00	0.00
17_112	17_462	17	FS	0.00	0.00	0.00	0.00
17_486	17_462	17	SS	0.00	0.00	3.00	0.00
17_112	17_463	17	FS	0.00	0.00	0.00	0.00
17_487	17_463	17	SS	0.00	0.00	3.00	0.00
17_112	17_464	17	FS	0.00	0.00	0.00	0.00
17_488	17_464	17	SS	0.00	0.00	3.00	0.00
17_112	17_465	17	FS	0.00	0.00	0.00	0.00
17_489	17_465	17	SS	0.00	0.00	3.00	0.00
17_112	17_466	17	FS	0.00	0.00	0.00	0.00
17_490	17_466	17	SS	0.00	0.00	3.00	0.00
17_112	17_467	17	FS	0.00	0.00	0.00	0.00
17_491	17_467	17	SS	0.00	0.00	3.00	0.00
17_112	17_468	17	FS	0.00	0.00	0.00	0.00
17_492	17_468	17	SS	0.00	0.00	3.00	0.00
17_112	17_469	17	FS	0.00	0.00	0.00	0.00
17_493	17_469	17	SS	0.00	0.00	3.00	0.00
17_112	17_470	17	FS	0.00	0.00	0.00	0.00
17_494	17_470	17	SS	0.00	0.00	3.00	0.00
17_112	17_471	17	FS	0.00	0.00	0.00	0.00
17_495	17_471	17	SS	0.00	0.00	3.00	0.00
17_112	17_472	17	FS	0.00	0.00	0.00	0.00
17_496	17_472	17	SS	0.00	0.00	3.00	0.00
17_112	17_473	17	FS	0.00	0.00	0.00	0.00
17_497	17_473	17	SS	0.00	0.00	3.00	0.00
17_112	17_474	17	FS	0.00	0.00	0.00	0.00
17_498	17_474	17	SS	0.00	0.00	3.00	0.00
17_112	17_475	17	FS	0.00	0.00	0.00	0.00
17_499	17_475	17	SS	0.00	0.00	3.00	0.00
17_112	17_476	17	FS	0.00	0.00	0.00	0.00
17_500	17_476	17	SS	0.00	0.00	3.00	0.00
17_112	17_477	17	FS	0.00	0.00	0.00	0.00
17_501	17_477	17	SS	0.00	0.00	3.00	0.00
17_154	17_430	17	FS	0.00	0.00	0.00	0.00
17_454	17_430	17	FS	0.00	0.00	0.00	0.00
17_154	17_431	17	FS	0.00	0.00	0.00	0.00
17_455	17_431	17	FS	0.00	0.00	0.00	0.00
17_154	17_432	17	FS	0.00	0.00	0.00	0.00
17_456	17_432	17	FS	0.00	0.00	0.00	0.00
17_154	17_433	17	FS	0.00	0.00	0.00	0.00
17_457	17_433	17	FS	0.00	0.00	0.00	0.00
17_154	17_434	17	FS	0.00	0.00	0.00	0.00
17_458	17_434	17	FS	0.00	0.00	0.00	0.00
17_154	17_435	17	FS	0.00	0.00	0.00	0.00
17_459	17_435	17	FS	0.00	0.00	0.00	0.00
17_154	17_436	17	FS	0.00	0.00	0.00	0.00
17_460	17_436	17	FS	0.00	0.00	0.00	0.00
17_154	17_437	17	FS	0.00	0.00	0.00	0.00
17_461	17_437	17	FS	0.00	0.00	0.00	0.00
17_154	17_438	17	FS	0.00	0.00	0.00	0.00
17_462	17_438	17	FS	0.00	0.00	0.00	0.00
17_154	17_439	17	FS	0.00	0.00	0.00	0.00
17_463	17_439	17	FS	0.00	0.00	0.00	0.00
17_154	17_440	17	FS	0.00	0.00	0.00	0.00
17_464	17_440	17	FS	0.00	0.00	0.00	0.00
17_154	17_441	17	FS	0.00	0.00	0.00	0.00
17_465	17_441	17	FS	0.00	0.00	0.00	0.00
17_154	17_442	17	FS	0.00	0.00	0.00	0.00
17_466	17_442	17	FS	0.00	0.00	0.00	0.00
17_154	17_443	17	FS	0.00	0.00	0.00	0.00
17_467	17_443	17	FS	0.00	0.00	0.00	0.00
17_154	17_444	17	FS	0.00	0.00	0.00	0.00
17_468	17_444	17	FS	0.00	0.00	0.00	0.00
17_154	17_445	17	FS	0.00	0.00	0.00	0.00
17_469	17_445	17	FS	0.00	0.00	0.00	0.00
17_154	17_446	17	FS	0.00	0.00	0.00	0.00
17_470	17_446	17	FS	0.00	0.00	0.00	0.00
17_154	17_447	17	FS	0.00	0.00	0.00	0.00
17_471	17_447	17	FS	0.00	0.00	0.00	0.00
17_154	17_448	17	FS	0.00	0.00	0.00	0.00
17_472	17_448	17	FS	0.00	0.00	0.00	0.00
17_154	17_449	17	FS	0.00	0.00	0.00	0.00
17_473	17_449	17	FS	0.00	0.00	0.00	0.00
17_154	17_450	17	FS	0.00	0.00	0.00	0.00
17_474	17_450	17	FS	0.00	0.00	0.00	0.00
17_154	17_451	17	FS	0.00	0.00	0.00	0.00
17_475	17_451	17	FS	0.00	0.00	0.00	0.00
17_154	17_452	17	FS	0.00	0.00	0.00	0.00
17_476	17_452	17	FS	0.00	0.00	0.00	0.00
17_154	17_453	17	FS	0.00	0.00	0.00	0.00
17_477	17_453	17	FS	0.00	0.00	0.00	0.00
17_430	17_406	17	FS	0.00	0.00	0.00	0.00
17_431	17_407	17	FS	0.00	0.00	0.00	0.00
17_432	17_408	17	FS	0.00	0.00	0.00	0.00
17_433	17_409	17	FS	0.00	0.00	0.00	0.00
17_434	17_410	17	FS	0.00	0.00	0.00	0.00
17_435	17_411	17	FS	0.00	0.00	0.00	0.00
17_436	17_412	17	FS	0.00	0.00	0.00	0.00
17_437	17_413	17	FS	0.00	0.00	0.00	0.00
17_438	17_414	17	FS	0.00	0.00	0.00	0.00
17_439	17_415	17	FS	0.00	0.00	0.00	0.00
17_440	17_416	17	FS	0.00	0.00	0.00	0.00
17_441	17_417	17	FS	0.00	0.00	0.00	0.00
17_442	17_418	17	FS	0.00	0.00	0.00	0.00
17_443	17_419	17	FS	0.00	0.00	0.00	0.00
17_445	17_421	17	FS	0.00	0.00	0.00	0.00
17_444	17_420	17	FS	0.00	0.00	0.00	0.00
17_446	17_422	17	FS	0.00	0.00	0.00	0.00
17_447	17_423	17	FS	0.00	0.00	0.00	0.00
17_448	17_424	17	FS	0.00	0.00	0.00	0.00
17_449	17_425	17	FS	0.00	0.00	0.00	0.00
17_450	17_426	17	FS	0.00	0.00	0.00	0.00
17_451	17_427	17	FS	0.00	0.00	0.00	0.00
17_452	17_428	17	FS	0.00	0.00	0.00	0.00
17_453	17_429	17	FS	0.00	0.00	0.00	0.00
17_75	17_76	17	FS	0.00	0.00	0.00	0.00
17_76	17_77	17	FS	0.00	0.00	0.00	0.00
17_77	17_82	17	FS	0.00	0.00	0.00	0.00
17_17	17_82	17	FS	0.00	1.00	5.00	0.00
17_82	17_81	17	FS	0.00	0.00	0.00	0.00
17_84	17_85	17	SS	0.00	8.00	4.00	0.00
17_85	17_86	17	FS	0.00	0.00	0.00	0.00
17_86	17_87	17	FS	0.00	0.00	0.00	0.00
17_87	17_88	17	FS	0.00	0.00	0.00	0.00
17_88	17_89	17	FS	0.00	0.00	0.00	0.00
17_89	17_90	17	FS	0.00	0.00	0.00	0.00
17_90	17_91	17	FS	0.00	0.00	0.00	0.00
17_81	17_94	17	FS	0.00	0.00	0.00	0.00
17_91	17_94	17	FS	0.00	0.00	0.00	0.00
17_94	17_95	17	FS	0.00	0.00	0.00	0.00
17_95	17_100	17	FS	0.00	0.00	0.00	0.00
17_100	17_101	17	FS	0.00	0.00	0.00	0.00
17_101	17_102	17	FS	0.00	0.00	0.00	0.00
17_104	17_105	17	FS	0.00	0.00	0.00	0.00
17_105	17_106	17	FS	0.00	0.00	0.00	0.00
17_106	17_107	17	FS	0.00	0.00	0.00	0.00
17_102	17_108	17	FS	0.00	0.00	0.00	0.00
17_107	17_108	17	FS	0.00	0.00	0.00	0.00
17_265	17_108	17	FS	0.00	0.00	0.00	0.00
17_266	17_108	17	FS	0.00	0.00	0.00	0.00
17_267	17_108	17	FS	0.00	0.00	0.00	0.00
17_268	17_108	17	FS	0.00	0.00	0.00	0.00
17_269	17_108	17	FS	0.00	0.00	0.00	0.00
17_270	17_108	17	FS	0.00	0.00	0.00	0.00
17_271	17_108	17	FS	0.00	0.00	0.00	0.00
17_272	17_108	17	FS	0.00	0.00	0.00	0.00
17_273	17_108	17	FS	0.00	0.00	0.00	0.00
17_274	17_108	17	FS	0.00	0.00	0.00	0.00
17_275	17_108	17	FS	0.00	0.00	0.00	0.00
17_276	17_108	17	FS	0.00	0.00	0.00	0.00
17_277	17_108	17	FS	0.00	0.00	0.00	0.00
17_278	17_108	17	FS	0.00	0.00	0.00	0.00
17_279	17_108	17	FS	0.00	0.00	0.00	0.00
17_280	17_108	17	FS	0.00	0.00	0.00	0.00
17_281	17_108	17	FS	0.00	0.00	0.00	0.00
17_282	17_108	17	FS	0.00	0.00	0.00	0.00
17_283	17_108	17	FS	0.00	0.00	0.00	0.00
17_284	17_108	17	FS	0.00	0.00	0.00	0.00
17_285	17_108	17	FS	0.00	0.00	0.00	0.00
17_286	17_108	17	FS	0.00	0.00	0.00	0.00
17_287	17_108	17	FS	0.00	0.00	0.00	0.00
17_288	17_108	17	FS	0.00	0.00	0.00	0.00
17_108	17_109	17	SS	0.00	0.00	5.00	0.00
17_109	17_110	17	FS	0.00	0.00	0.00	0.00
17_110	17_111	17	FS	0.00	0.00	0.00	0.00
17_111	17_112	17	FS	0.00	0.00	0.00	0.00
17_128	17_129	17	SS	0.00	7.00	1.00	0.00
17_129	17_131	17	FS	0.00	0.00	0.00	0.00
17_130	17_131	17	FS	0.00	0.00	0.00	0.00
17_133	17_134	17	FS	0.00	0.00	0.00	0.00
17_136	17_193	17	FS	0.00	0.00	0.00	0.00
17_137	17_138	17	FS	0.00	0.00	0.00	0.00
17_193	17_138	17	FS	0.00	0.00	0.00	0.00
17_138	17_139	17	FS	0.00	0.00	0.00	0.00
17_139	17_140	17	FS	0.00	0.00	0.00	0.00
17_140	17_141	17	FS	0.00	0.00	0.00	0.00
17_141	17_194	17	FS	0.00	0.00	0.00	0.00
17_126	17_149	17	FS	0.00	0.00	0.00	0.00
17_131	17_149	17	FS	0.00	0.00	0.00	0.00
17_134	17_149	17	FS	0.00	0.00	0.00	0.00
17_149	17_150	17	SS	0.00	0.00	0.00	0.00
17_138	17_150	17	FS	0.00	0.00	0.00	0.00
17_150	17_195	17	FS	0.00	0.00	0.00	0.00
17_195	17_151	17	FS	0.00	0.00	0.00	0.00
17_95	17_152	17	FS	0.00	0.00	0.00	0.00
17_151	17_152	17	FS	0.00	0.00	0.00	0.00
17_152	17_153	17	FS	0.00	0.00	0.00	0.00
17_153	17_154	17	FS	0.00	0.00	0.00	0.00
17_194	17_154	17	FS	0.00	0.00	0.00	0.00
17_156	17_157	17	FS	0.00	0.00	0.00	0.00
17_151	17_157	17	FS	0.00	0.00	0.00	0.00
17_157	17_158	17	FS	0.00	0.00	0.00	0.00
18_3	18_4	18	FS	0.00	0.00	0.00	0.00
18_4	18_5	18	FS	0.00	0.00	0.00	0.00
18_5	18_6	18	FS	0.00	0.00	0.00	0.00
18_5	18_7	18	FS	0.00	0.00	0.00	0.00
18_5	18_8	18	FS	0.00	0.00	0.00	0.00
18_6	18_9	18	FS	0.00	0.00	0.00	0.00
18_8	18_9	18	FS	0.00	0.00	0.00	0.00
18_7	18_9	18	FS	0.00	0.00	0.00	0.00
18_9	18_10	18	FS	0.00	0.00	0.00	0.00
18_10	18_11	18	FS	0.00	0.00	0.00	0.00
18_11	18_13	18	FS	0.00	0.00	0.00	0.00
18_13	18_14	18	FS	0.00	0.00	0.00	0.00
18_13	18_15	18	FS	0.00	0.00	0.00	0.00
18_14	18_16	18	FS	0.00	0.00	0.00	0.00
18_16	18_17	18	FS	0.00	0.00	0.00	0.00
18_13	18_19	18	FS	0.00	0.00	0.00	0.00
18_19	18_20	18	FS	0.00	0.00	0.00	0.00
18_20	18_21	18	FS	0.00	0.00	0.00	0.00
18_21	18_22	18	FS	0.00	0.00	0.00	0.00
18_21	18_23	18	FS	0.00	0.00	0.00	0.00
18_15	18_25	18	FS	0.00	0.00	0.00	0.00
18_17	18_27	18	FS	0.00	0.00	0.00	0.00
18_27	18_28	18	FS	0.00	0.00	0.00	0.00
18_28	18_29	18	FS	0.00	0.00	0.00	0.00
18_28	18_30	18	FS	0.00	0.00	0.00	0.00
18_28	18_31	18	FS	0.00	0.00	0.00	0.00
18_29	18_32	18	FS	0.00	0.00	0.00	0.00
18_32	18_34	18	FS	0.00	0.00	0.00	0.00
18_30	18_34	18	FS	0.00	0.00	0.00	0.00
18_31	18_34	18	FS	0.00	0.00	0.00	0.00
18_15	18_34	18	FS	0.00	0.00	0.00	0.00
18_34	18_36	18	FS	0.00	0.00	0.00	0.00
18_36	18_37	18	FS	0.00	0.00	0.00	0.00
18_37	18_39	18	FS	0.00	0.00	0.00	0.00
18_23	18_41	18	FS	0.00	0.00	0.00	0.00
18_22	18_41	18	FS	0.00	0.00	0.00	0.00
18_28	18_42	18	FS	0.00	0.00	0.00	0.00
18_29	18_43	18	FS	0.00	0.00	0.00	0.00
18_30	18_44	18	FS	0.00	0.00	0.00	0.00
18_31	18_44	18	FS	0.00	0.00	0.00	0.00
18_27	18_45	18	FS	0.00	0.00	0.00	0.00
18_34	18_46	18	FS	0.00	0.00	0.00	0.00
18_41	18_48	18	FS	0.00	0.00	0.00	0.00
18_42	18_48	18	FS	0.00	0.00	0.00	0.00
18_43	18_48	18	FS	0.00	0.00	0.00	0.00
18_44	18_48	18	FS	0.00	0.00	0.00	0.00
18_45	18_48	18	FS	0.00	0.00	0.00	0.00
18_46	18_48	18	FS	0.00	0.00	0.00	0.00
19_1	19_2	19	FS	0.00	0.00	0.00	0.00
19_1	19_3	19	FS	0.00	0.00	0.00	0.00
19_1	19_4	19	FS	0.00	0.00	0.00	0.00
19_4	19_5	19	FS	0.00	0.00	0.00	0.00
19_5	19_6	19	FS	0.00	0.00	0.00	0.00
19_4	19_6	19	FS	0.00	0.00	0.00	0.00
19_6	19_7	19	FS	0.00	0.00	0.00	0.00
19_5	19_7	19	FS	0.00	0.00	0.00	0.00
19_7	19_30	19	FS	0.00	0.00	0.00	0.00
19_2	19_30	19	FS	0.00	0.00	0.00	0.00
19_3	19_30	19	FS	0.00	0.00	0.00	0.00
19_30	19_8	19	FS	0.00	0.00	0.00	0.00
19_8	19_9	19	FS	0.00	0.00	0.00	0.00
19_8	19_10	19	FS	0.00	0.00	0.00	0.00
19_10	19_11	19	FS	0.00	0.00	0.00	0.00
19_10	19_12	19	FS	0.00	0.00	0.00	0.00
19_11	19_13	19	FS	0.00	0.00	0.00	0.00
19_12	19_13	19	FS	0.00	0.00	0.00	0.00
19_9	19_14	19	FS	0.00	0.00	0.00	0.00
19_10	19_14	19	FS	0.00	0.00	0.00	0.00
19_13	19_15	19	FS	0.00	0.00	0.00	0.00
19_14	19_15	19	FS	0.00	0.00	0.00	0.00
19_15	19_16	19	FS	0.00	0.00	0.00	0.00
19_15	19_17	19	FS	0.00	0.00	0.00	0.00
19_15	19_18	19	FS	0.00	0.00	0.00	0.00
19_16	19_31	19	FS	0.00	0.00	0.00	0.00
19_17	19_31	19	FS	0.00	0.00	0.00	0.00
19_18	19_31	19	FS	0.00	0.00	0.00	0.00
19_31	19_19	19	FS	0.00	0.00	0.00	0.00
19_19	19_20	19	FS	0.00	0.00	0.00	0.00
19_20	19_21	19	FS	0.00	0.00	0.00	0.00
19_21	19_22	19	FS	0.00	0.00	0.00	0.00
19_21	19_23	19	FS	0.00	0.00	0.00	0.00
19_23	19_24	19	FS	0.00	0.00	0.00	0.00
19_21	19_25	19	FS	0.00	0.00	0.00	0.00
19_21	19_26	19	FS	0.00	0.00	0.00	0.00
19_22	19_32	19	FS	0.00	0.00	0.00	0.00
19_24	19_32	19	FS	0.00	0.00	0.00	0.00
19_25	19_32	19	FS	0.00	0.00	0.00	0.00
19_26	19_32	19	FS	0.00	0.00	0.00	0.00
19_32	19_27	19	FS	0.00	0.00	0.00	0.00
19_27	19_28	19	FS	0.00	0.00	0.00	0.00
19_28	19_29	19	FS	0.00	0.00	0.00	0.00
\.


--
-- Data for Name: project_constraint_resource; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_constraint_resource (id, project_id, resource_name, resource_type, max_availability, cost_per_use, cost_per_unit) FROM stdin;
168	15	Project Coordinator	Renewable	1.00	0.00	31.28
169	15	Headnurses	Renewable	65.00	0.00	31.28
170	15	ICT committee	Renewable	5.00	0.00	27.62
171	15	Board of directors	Renewable	7.00	0.00	62.10
172	15	Stretcher-bearer/logisticians	Renewable	24.00	0.00	22.31
173	16	Labourers	Renewable	10.00	0.00	60.00
174	16	Truck IVECO Trakker	Renewable	6.00	0.00	70.00
175	16	Bulldozer D8T	Renewable	1.00	0.00	75.00
176	16	Wheel Loader	Renewable	2.00	0.00	60.00
177	16	Sheepfoot rolles	Renewable	2.00	0.00	70.00
178	16	Smooth Roller	Renewable	2.00	0.00	60.00
179	16	Crawler Excavator	Renewable	2.00	0.00	98.00
180	16	Drilling Rid	Renewable	1.00	0.00	75.00
181	16	Concrete Mixer Truck	Renewable	1.00	0.00	95.00
182	16	Crane	Renewable	1.00	0.00	105.00
183	16	Paler	Renewable	1.00	0.00	65.00
184	16	Cold Milling Machine	Renewable	1.00	0.00	230.00
185	16	Pile Driver	Renewable	1.00	0.00	48.00
186	16	Pruning Machine	Renewable	1.00	0.00	40.00
187	16	Tank Truck	Renewable	1.00	0.00	78.00
188	16	Line Striper Machine	Renewable	1.00	0.00	30.00
189	16	Materials	Consumable	1.00	0.00	1.00
190	16	Paving Material	Consumable	1.00	0.00	1.00
191	17	Skipper	Renewable	4.00	0.00	60.00
192	17	Welder	Renewable	8.00	0.00	60.00
193	17	Engineer	Renewable	18.00	0.00	160.00
194	17	Special team	Renewable	2.00	0.00	800.00
195	17	Disconnecting team	Renewable	1.00	0.00	800.00
196	17	Commissioning team	Renewable	1.00	0.00	800.00
197	17	Testing team	Renewable	1.00	0.00	800.00
198	17	Diving team	Renewable	1.00	0.00	900.00
199	17	Crane	Renewable	3.00	0.00	200.00
200	17	Vessel Pompei	Renewable	1.00	0.00	3320.00
201	17	Vessel Neptune	Renewable	1.00	0.00	3750.00
202	17	Vessel Vagant	Renewable	1.00	0.00	3180.00
203	17	Vessel Sternat Spirit	Renewable	1.00	0.00	3250.00
204	17	Vessel Souverreign	Renewable	1.00	0.00	3250.00
205	17	Vessel Rambiz	Renewable	1.00	0.00	3620.00
206	17	Vessel Buzzard	Renewable	1.00	0.00	3200.00
207	17	Vessel Breydel	Renewable	2.00	0.00	3200.00
208	17	Vessel Breughel	Renewable	1.00	0.00	3200.00
209	17	Vessel Pearl River	Renewable	1.00	0.00	3250.00
210	17	Vessel Maersk	Renewable	1.00	0.00	800.00
211	17	Vessel Innovator	Renewable	1.00	0.00	3250.00
212	17	Pre-piling template	Renewable	1.00	0.00	200.00
213	17	Towning tugs	Renewable	2.00	0.00	450.00
214	17	Transport barges	Renewable	2.00	0.00	400.00
215	17	Drilling machine	Renewable	2.00	0.00	1200.00
216	17	Pulling machine	Renewable	1.00	0.00	1300.00
217	17	Laborer	Renewable	60.00	0.00	40.00
218	18	Project Leader	Renewable	1.00	0.00	30.00
219	18	Engineer	Renewable	3.00	0.00	50.00
220	18	Worker	Renewable	2.00	0.00	24.00
221	18	Marketeer	Renewable	1.00	0.00	28.00
222	18	Administrator	Renewable	1.00	0.00	30.00
223	19	Employees	Renewable	3.00	0.00	40.00
\.


--
-- Data for Name: project_constraint_time; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_constraint_time (id, project_id, weekly_schedule, holidays_list, overtime_multiplier) FROM stdin;
14	15	{"friday": ["08:00-12:00", "13:00-17:00"], "monday": ["08:00-12:00", "13:00-17:00"], "sunday": [], "tuesday": ["08:00-12:00", "13:00-17:00"], "saturday": [], "thursday": ["08:00-12:00", "13:00-17:00"], "wednesday": ["08:00-12:00", "13:00-17:00"]}	[]	1.50
15	16	{"friday": ["08:00-12:00", "13:00-17:00"], "monday": ["08:00-12:00", "13:00-17:00"], "sunday": [], "tuesday": ["08:00-12:00", "13:00-17:00"], "saturday": [], "thursday": ["08:00-12:00", "13:00-17:00"], "wednesday": ["08:00-12:00", "13:00-17:00"]}	[]	1.50
16	17	{"friday": ["08:00-12:00", "13:00-17:00"], "monday": ["08:00-12:00", "13:00-17:00"], "sunday": [], "tuesday": ["08:00-12:00", "13:00-17:00"], "saturday": [], "thursday": ["08:00-12:00", "13:00-17:00"], "wednesday": ["08:00-12:00", "13:00-17:00"]}	[]	1.50
17	18	{"friday": ["08:00-12:00", "13:00-17:00"], "monday": ["08:00-12:00", "13:00-17:00"], "sunday": [], "tuesday": ["08:00-12:00", "13:00-17:00"], "saturday": [], "thursday": ["08:00-12:00", "13:00-17:00"], "wednesday": ["08:00-12:00", "13:00-17:00"]}	[]	1.50
18	19	{"friday": ["08:00-12:00", "13:00-17:00"], "monday": ["08:00-12:00", "13:00-17:00"], "sunday": [], "tuesday": ["08:00-12:00", "13:00-17:00"], "saturday": [], "thursday": ["08:00-12:00", "13:00-17:00"], "wednesday": ["08:00-12:00", "13:00-17:00"]}	[]	1.50
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.projects (id, user_id, project_name, type, status, base_cost, total_cost, target_deadline, penalty_per_day, bonus_per_day, search_vector, metadata_json, num_tasks, num_edges, network_density, created_at, updated_at) FROM stdin;
18	\N	CarSharing platform	ITLG	Planning	439234.00	614927.60	\N	\N	\N	\N	{}	0	0	0.0000	2026-07-10 13:12:33.936334	2026-07-11 06:51:14.238584
15	\N	Patient Transport System	PRO	Planning	32159.12	44070.63	\N	\N	\N	\N	{}	0	0	0.0000	2026-07-10 13:12:29.76466	2026-07-11 03:58:01.053427
19	\N	Lock Ganzepoot Ypres	CON	Planning	170000.00	238000.00	\N	\N	\N	\N	{"simulation_results": {"budget": 246675.0, "deadline": 478.40000000000003, "project_id": "19", "monte_carlo": {"P90": 431.3509512037911, "on_time_prob": 1.0, "mean_makespan": 420.30888237315975, "criticality_indices": {"19_1": 1.0, "19_2": 0.0, "19_3": 0.0, "19_4": 1.0, "19_5": 1.0, "19_6": 1.0, "19_7": 1.0, "19_8": 1.0, "19_9": 0.0, "19_10": 1.0, "19_11": 0.497, "19_12": 0.503, "19_13": 1.0, "19_14": 0.0, "19_15": 1.0, "19_16": 0.0, "19_17": 1.0, "19_18": 0.0, "19_19": 1.0, "19_20": 1.0, "19_21": 1.0, "19_22": 0.0, "19_23": 1.0, "19_24": 1.0, "19_25": 0.0, "19_26": 0.0, "19_27": 1.0, "19_28": 1.0, "19_29": 1.0, "19_30": 1.0, "19_31": 1.0, "19_32": 1.0}}, "dependencies": [["19_1", "19_2", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_1", "19_3", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_1", "19_4", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_4", "19_5", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_5", "19_6", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_4", "19_6", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_6", "19_7", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_5", "19_7", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_7", "19_30", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_2", "19_30", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_3", "19_30", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_30", "19_8", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_8", "19_9", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_8", "19_10", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_10", "19_11", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_10", "19_12", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_11", "19_13", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_12", "19_13", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_9", "19_14", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_10", "19_14", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_13", "19_15", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_14", "19_15", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_15", "19_16", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_15", "19_17", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_15", "19_18", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_16", "19_31", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_17", "19_31", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_18", "19_31", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_31", "19_19", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_19", "19_20", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_20", "19_21", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_21", "19_22", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_21", "19_23", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_23", "19_24", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_21", "19_25", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_21", "19_26", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_22", "19_32", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_24", "19_32", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_25", "19_32", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_26", "19_32", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_32", "19_27", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_27", "19_28", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}], ["19_28", "19_29", {"lag_days": 0.0, "lag_hours": 0.0, "lag_weeks": 0.0, "lag_months": 0.0, "dependency_type": "FS"}]], "pareto_nsga2": {"options": [{"cost": 245882.0, "risk": 10.3, "modes": [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0], "makespan": 344.0}, {"cost": 245140.0, "risk": 10.500000000000002, "modes": [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0], "makespan": 348.79999999999995}, {"cost": 245140.0, "risk": 10.500000000000002, "modes": [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0], "makespan": 348.79999999999995}, {"cost": 243684.0, "risk": 10.4, "modes": [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0], "makespan": 348.8}], "selected": {"cost": 245882.0, "risk": 10.3, "modes": [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0], "makespan": 344.0}, "solutions_found": 12}, "ppo_schedule": {"tgc": 0.0, "modes": [1, 0, 1, 2, 1, 1, 2, 1, 1, 2, 0, 2, 0, 1, 0, 0, 1, 1, 1, 2, 2, 2, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2], "reward": -139.63431231667565, "makespan": 115.38220977783203}, "tasks_metadata": [{"id": "19_18", "name": "Reparing walls", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 6270.0, "normal_cost": 4180.0, "outsource_cost": 8680.0, "most_probable_duration": 32.0}, {"id": "19_1", "name": "Installation of power generators, lighting, toilets, fencing,  supply of concrete and wooden partition", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 5880.0, "normal_cost": 3920.0, "outsource_cost": 8160.0, "most_probable_duration": 32.0}, {"id": "19_10", "name": "Pumping lock chamber completely dry", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 3210.0, "normal_cost": 2140.0, "outsource_cost": 4440.0, "most_probable_duration": 16.0}, {"id": "19_11", "name": "Cleaning lock floor", "resources": [{"quantity": 1.0, "resource_id": "223"}], "crash_cost": 3930.0, "normal_cost": 2620.0, "outsource_cost": 5400.0, "most_probable_duration": 16.0}, {"id": "19_12", "name": "supply concrete blocks (to prevent the floor comes up)", "resources": [{"quantity": 1.0, "resource_id": "223"}], "crash_cost": 14580.0, "normal_cost": 9720.0, "outsource_cost": 19600.0, "most_probable_duration": 16.0}, {"id": "19_13", "name": "placing concrete blocks", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 4710.0, "normal_cost": 3140.0, "outsource_cost": 6440.0, "most_probable_duration": 16.0}, {"id": "19_14", "name": "Cleaning walls and threshold", "resources": [{"quantity": 1.0, "resource_id": "223"}], "crash_cost": 5775.0, "normal_cost": 3850.0, "outsource_cost": 7860.0, "most_probable_duration": 16.0}, {"id": "19_15", "name": "Installing stairs in lock chamber", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 6240.0, "normal_cost": 4160.0, "outsource_cost": 8480.0, "most_probable_duration": 16.0}, {"id": "19_16", "name": "Replacing hinges, pivot shoes and pivots", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 15540.0, "normal_cost": 10360.0, "outsource_cost": 20880.0, "most_probable_duration": 16.0}, {"id": "19_17", "name": "Cleaning lock head", "resources": [{"quantity": 1.0, "resource_id": "223"}], "crash_cost": 5940.0, "normal_cost": 3960.0, "outsource_cost": 8400.0, "most_probable_duration": 48.0}, {"id": "19_19", "name": "Transport of gates to the site", "resources": [{"quantity": 1.0, "resource_id": "223"}], "crash_cost": 480.0, "normal_cost": 320.0, "outsource_cost": 800.0, "most_probable_duration": 16.0}, {"id": "19_2", "name": "Remove railing and platforms", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 7170.0, "normal_cost": 4780.0, "outsource_cost": 9880.0, "most_probable_duration": 32.0}, {"id": "19_20", "name": "Put gates in place", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 37440.0, "normal_cost": 24960.0, "outsource_cost": 50080.0, "most_probable_duration": 16.0}, {"id": "19_21", "name": "Adjusting gates (Tightening hinges , front beams, sealing, anchorage points)", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 12960.0, "normal_cost": 8640.0, "outsource_cost": 17440.0, "most_probable_duration": 16.0}, {"id": "19_22", "name": "Installing railing", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 4260.0, "normal_cost": 2840.0, "outsource_cost": 5840.0, "most_probable_duration": 16.0}, {"id": "19_23", "name": "preliminary works at threshold", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 4710.0, "normal_cost": 3140.0, "outsource_cost": 6440.0, "most_probable_duration": 16.0}, {"id": "19_24", "name": "Repairing threshold", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 7830.0, "normal_cost": 5220.0, "outsource_cost": 10760.0, "most_probable_duration": 32.0}, {"id": "19_25", "name": "Install platforms", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 8220.0, "normal_cost": 5480.0, "outsource_cost": 11280.0, "most_probable_duration": 32.0}, {"id": "19_26", "name": "Installing ladder", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 9720.0, "normal_cost": 6480.0, "outsource_cost": 13280.0, "most_probable_duration": 32.0}, {"id": "19_27", "name": "Remove concrete blocks", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 5190.0, "normal_cost": 3460.0, "outsource_cost": 7080.0, "most_probable_duration": 16.0}, {"id": "19_28", "name": "Remove concrete and wooden partition", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 6840.0, "normal_cost": 4560.0, "outsource_cost": 9280.0, "most_probable_duration": 16.0}, {"id": "19_29", "name": "Cleaning site", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 6840.0, "normal_cost": 4560.0, "outsource_cost": 9280.0, "most_probable_duration": 16.0}, {"id": "19_3", "name": "preliminary works at gates (loosing hinges, disconnect hinges, hydraulics, anchorage points)", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 8190.0, "normal_cost": 5460.0, "outsource_cost": 11080.0, "most_probable_duration": 16.0}, {"id": "19_30", "name": "End Of Preparation/Start Restoration of lock head", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "19_31", "name": "End Restoration of lock head/Start Installing new gates", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "19_32", "name": "End Installing new gates/ Start Termination", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "19_4", "name": "Sealing canal lock gates at other side and overflow sewers", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 3960.0, "normal_cost": 2640.0, "outsource_cost": 5440.0, "most_probable_duration": 16.0}, {"id": "19_5", "name": "Placing of concrete partition + Placing of wooden partition", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 8640.0, "normal_cost": 5760.0, "outsource_cost": 11680.0, "most_probable_duration": 16.0}, {"id": "19_6", "name": "Installing pumps", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 4710.0, "normal_cost": 3140.0, "outsource_cost": 6440.0, "most_probable_duration": 16.0}, {"id": "19_7", "name": "Check safety wooden partition + Check safety concrete partition", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 3090.0, "normal_cost": 2060.0, "outsource_cost": 4280.0, "most_probable_duration": 16.0}, {"id": "19_8", "name": "Remove gates", "resources": [{"quantity": 2.0, "resource_id": "223"}], "crash_cost": 29910.0, "normal_cost": 19940.0, "outsource_cost": 40040.0, "most_probable_duration": 16.0}, {"id": "19_9", "name": "Remove hinges", "resources": [{"quantity": 3.0, "resource_id": "223"}], "crash_cost": 4440.0, "normal_cost": 2960.0, "outsource_cost": 6080.0, "most_probable_duration": 16.0}], "cp_sat_schedule": {"status": "INFEASIBLE", "makespan": 0, "schedule": {}}, "cpm_static_makespan": 368.0, "project_state_evolution": {"state_history": [{"makespan": 368.0, "state_id": 0, "timestamp": 1783779530.9884574, "total_cost": 0.0, "direct_cost": 119120.0, "monte_carlo": {"P90": 432.3749277003668, "on_time_prob": 1.0, "mean_makespan": 420.7492611613503}, "critical_path": [], "indirect_cost": 0.0, "action_applied": null, "resource_metrics": {"capacities": {"223": 1}, "total_demand": {"223": 65.0}, "utilization_rate": {"223": 65.0}}}, {"makespan": 344.3333333333333, "state_id": 1, "timestamp": 1783779531.1609, "total_cost": 0.0, "direct_cost": 122240.0, "monte_carlo": {"P90": 406.0524797687438, "on_time_prob": 1.0, "mean_makespan": 395.01425185656234}, "critical_path": ["19_1", "19_10", "19_11", "19_12", "19_13", "19_15", "19_17", "19_19", "19_20", "19_21", "19_23", "19_24", "19_27", "19_28", "19_29", "19_30", "19_31", "19_32", "19_4", "19_5", "19_6", "19_7", "19_8"], "indirect_cost": 0.0, "action_applied": {"priority": 1, "action_type": "Crash", "crash_level": 1.5, "custom_params": {"modes": [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0]}, "overlap_ratio": 0.3, "affected_tasks": ["19_1", "19_10", "19_30", "19_31", "19_32", "19_6", "19_7"], "resource_delta": {}, "outsource_level": 2.0, "expected_cost_delta": 245882.0, "expected_risk_delta": 10.3, "expected_duration_delta": 344.0}, "resource_metrics": {"capacities": {"223": 1}, "total_demand": {"223": 69.0}, "utilization_rate": {"223": 69.0}}}], "current_state_id": 1, "before_after_comparison": {"action_applied": {"priority": 1, "action_type": "Crash", "crash_level": 1.5, "custom_params": {"modes": [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0]}, "overlap_ratio": 0.3, "affected_tasks": ["19_1", "19_10", "19_30", "19_31", "19_32", "19_6", "19_7"], "resource_delta": {}, "outsource_level": 2.0, "expected_cost_delta": 245882.0, "expected_risk_delta": 10.3, "expected_duration_delta": 344.0}, "after_state_id": 1, "before_state_id": 0, "metrics_comparison": {"makespan": {"after": 344.3333333333333, "delta": -23.666666666666686, "before": 368.0, "percent_change": -6.43115942028986}, "total_cost": {"after": 0.0, "delta": 0.0, "before": 0.0, "percent_change": 0.0}, "P90_makespan": {"after": 406.0524797687438, "delta": -26.322447931623003, "before": 432.3749277003668}, "on_time_probability": {"after": 1.0, "delta": 0.0, "before": 1.0}}, "top_attention_shifts": [{"delta": -0.0936276912689209, "task_id": "19_11", "score_after": 0.5382981300354004, "score_before": 0.6319258213043213}, {"delta": -0.08708643913269043, "task_id": "19_13", "score_after": 0.5742287635803223, "score_before": 0.6613152027130127}, {"delta": -0.08608841896057129, "task_id": "19_12", "score_after": 0.5362979173660278, "score_before": 0.6223863363265991}, {"delta": -0.0830504298210144, "task_id": "19_10", "score_after": 0.5417836904525757, "score_before": 0.6248341202735901}, {"delta": -0.06356245279312134, "task_id": "19_8", "score_after": 0.5521371960639954, "score_before": 0.6156996488571167}], "critical_path_evolution": {"after_count": 23, "before_count": 0, "newly_critical_tasks": ["19_12", "19_4", "19_13", "19_20", "19_7", "19_28", "19_31", "19_5", "19_27", "19_10", "19_8", "19_32", "19_23", "19_30", "19_17", "19_1", "19_24", "19_29", "19_21", "19_15", "19_19", "19_11", "19_6"], "no_longer_critical_tasks": []}, "resource_utilization_evolution": {"after": {"capacities": {"223": 1}, "total_demand": {"223": 69.0}, "utilization_rate": {"223": 69.0}}, "before": {"capacities": {"223": 1}, "total_demand": {"223": 65.0}, "utilization_rate": {"223": 65.0}}}}}}, "simulation_progress": "🤖 [BƯỚC 6] PPO Agent Runtime Dynamic Control..."}	0	0	0.0000	2026-07-10 13:12:34.194659	2026-07-11 14:18:52.634348
16	\N	Asti-Cuneo Highway	CON	Planning	5216841.00	6521051.25	\N	\N	\N	\N	{"simulation_results": {"budget": 7825261.5, "deadline": 2828.8, "project_id": "16", "monte_carlo": {"P90": 2288.181625096491, "on_time_prob": 1.0, "mean_makespan": 2272.8388463852184, "criticality_indices": {"16_1": 1.0, "16_2": 1.0, "16_3": 1.0, "16_4": 1.0, "16_5": 1.0, "16_6": 1.0, "16_7": 1.0, "16_8": 0.0, "16_9": 1.0, "16_11": 1.0, "16_12": 0.0, "16_14": 0.0, "16_17": 1.0, "16_19": 1.0, "16_20": 0.0, "16_22": 1.0, "16_24": 0.0, "16_25": 0.0, "16_26": 0.0, "16_27": 0.0, "16_28": 0.0, "16_29": 0.0, "16_30": 0.0, "16_31": 0.0, "16_32": 0.0, "16_33": 0.0, "16_34": 0.0, "16_35": 0.0, "16_36": 0.0, "16_38": 1.0, "16_39": 1.0, "16_41": 1.0, "16_42": 1.0, "16_44": 1.0, "16_46": 1.0, "16_48": 1.0, "16_49": 1.0, "16_51": 1.0, "16_52": 1.0, "16_55": 1.0, "16_56": 1.0, "16_58": 1.0, "16_59": 1.0, "16_62": 1.0, "16_63": 0.0, "16_66": 1.0, "16_67": 1.0, "16_68": 1.0, "16_69": 1.0, "16_70": 1.0, "16_72": 0.736, "16_73": 0.736, "16_75": 1.0, "16_77": 0.264, "16_78": 0.0, "16_80": 0.0, "16_82": 1.0, "16_83": 1.0, "16_85": 1.0, "16_86": 1.0, "16_87": 0.0, "16_88": 0.0, "16_89": 0.0, "16_91": 0.0, "16_92": 1.0, "16_93": 1.0, "16_94": 1.0}}, "dependencies": [["16_1", "16_2"], ["16_2", "16_3"], ["16_3", "16_4"], ["16_4", "16_5"], ["16_5", "16_6"], ["16_6", "16_7"], ["16_7", "16_8"], ["16_7", "16_9"], ["16_9", "16_14"], ["16_9", "16_11"], ["16_11", "16_12"], ["16_11", "16_19"], ["16_19", "16_20"], ["16_19", "16_17"], ["16_17", "16_22"], ["16_8", "16_24"], ["16_12", "16_24"], ["16_14", "16_24"], ["16_20", "16_24"], ["16_22", "16_24"], ["16_24", "16_25"], ["16_25", "16_26"], ["16_26", "16_27"], ["16_27", "16_28"], ["16_28", "16_29"], ["16_29", "16_30"], ["16_30", "16_31"], ["16_31", "16_32"], ["16_32", "16_33"], ["16_33", "16_34"], ["16_34", "16_35"], ["16_35", "16_36"], ["16_8", "16_41"], ["16_12", "16_41"], ["16_14", "16_41"], ["16_20", "16_41"], ["16_22", "16_41"], ["16_41", "16_42"], ["16_42", "16_38"], ["16_38", "16_39"], ["16_41", "16_63"], ["16_39", "16_62"], ["16_62", "16_66"], ["16_63", "16_66"], ["16_66", "16_67"], ["16_67", "16_68"], ["16_68", "16_69"], ["16_69", "16_70"], ["16_70", "16_82"], ["16_82", "16_83"], ["16_83", "16_75"], ["16_75", "16_73"], ["16_73", "16_72"], ["16_83", "16_80"], ["16_75", "16_78"], ["16_75", "16_77"], ["16_72", "16_48"], ["16_77", "16_48"], ["16_78", "16_48"], ["16_80", "16_48"], ["16_48", "16_49"], ["16_49", "16_46"], ["16_46", "16_44"], ["16_36", "16_58"], ["16_44", "16_58"], ["16_58", "16_59"], ["16_59", "16_52"], ["16_52", "16_51"], ["16_51", "16_55"], ["16_55", "16_56"], ["16_56", "16_85"], ["16_36", "16_85"], ["16_85", "16_86"], ["16_85", "16_87"], ["16_87", "16_88"], ["16_85", "16_89"], ["16_86", "16_91"], ["16_88", "16_91"], ["16_89", "16_91"], ["16_86", "16_92"], ["16_88", "16_92"], ["16_89", "16_92"], ["16_92", "16_93"], ["16_93", "16_94"]], "pareto_nsga2": {"options": [{"cost": 7750157.5, "risk": 18.2944, "modes": [0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1], "makespan": 5138.400000000001}, {"cost": 7693638.75, "risk": 18.394399999999997, "modes": [0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1], "makespan": 5145.600000000001}, {"cost": 7680325.625, "risk": 18.568000000000005, "modes": [0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0], "makespan": 5174.400000000001}, {"cost": 7623219.375, "risk": 18.568, "modes": [1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0], "makespan": 5224.800000000001}], "selected": {"cost": 7750157.5, "risk": 18.2944, "modes": [0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1], "makespan": 5138.400000000001}, "solutions_found": 40}, "ppo_schedule": {"tgc": 0.0, "modes": [2, 2, 0, 2, 2, 2, 2, 2, 2, 2, 0, 2, 0, 2, 2, 0, 2, 0, 2, 2, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 2, 2, 2, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], "reward": -1208.6248722672462, "makespan": 281.7736511230469}, "tasks_metadata": [{"id": "16_14", "name": "Manhole covers", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 3000.0, "resource_id": "189"}], "crash_cost": 6862.5, "normal_cost": 4575.0, "outsource_cost": 9150.0, "most_probable_duration": 0.0}, {"id": "16_49", "name": "Topsoil removal and clearing subbase", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "175"}], "crash_cost": 8302.5, "normal_cost": 5535.0, "outsource_cost": 11070.0, "most_probable_duration": 0.0}, {"id": "16_12", "name": "Culverts concrete aging", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "16_17", "name": "Digging", "resources": [{"quantity": 9.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "179"}, {"quantity": 6.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "177"}], "crash_cost": 74088.0, "normal_cost": 49392.0, "outsource_cost": 98784.0, "most_probable_duration": 0.0}, {"id": "16_19", "name": "Road embankments", "resources": [{"quantity": 10.0, "resource_id": "173"}, {"quantity": 6.0, "resource_id": "174"}, {"quantity": 2.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "177"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 55000.0, "resource_id": "189"}], "crash_cost": 244297.5, "normal_cost": 162865.0, "outsource_cost": 325730.0, "most_probable_duration": 0.0}, {"id": "16_2", "name": "Clearing site", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 3.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "176"}], "crash_cost": 7290.0, "normal_cost": 4860.0, "outsource_cost": 9720.0, "most_probable_duration": 0.0}, {"id": "16_20", "name": "Sound barriers", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 23000.0, "resource_id": "189"}], "crash_cost": 39225.0, "normal_cost": 26150.0, "outsource_cost": 52300.0, "most_probable_duration": 0.0}, {"id": "16_22", "name": "Longitudinal drains (ditches)", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1500.0, "resource_id": "189"}], "crash_cost": 20677.5, "normal_cost": 13785.0, "outsource_cost": 27570.0, "most_probable_duration": 0.0}, {"id": "16_24", "name": "Plinths excavation", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 3.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 0.0, "resource_id": "189"}], "crash_cost": 4158.0, "normal_cost": 2772.0, "outsource_cost": 5544.0, "most_probable_duration": 0.0}, {"id": "16_25", "name": "Pouring piles frameworks and drilling", "resources": [{"quantity": 6.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "180"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 1.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 190000.0, "resource_id": "189"}], "crash_cost": 306870.0, "normal_cost": 204580.0, "outsource_cost": 409160.0, "most_probable_duration": 0.0}, {"id": "16_26", "name": "Piles concrete aging", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "16_27", "name": "Making of plinths (pouring frameworks and concrete casting)", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 100000.0, "resource_id": "189"}], "crash_cost": 157290.0, "normal_cost": 104860.0, "outsource_cost": 209720.0, "most_probable_duration": 0.0}, {"id": "16_28", "name": "Plinths concrete aging", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "16_29", "name": "Making of pylons (pouring frameworks and concrete casting)", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 11000.0, "resource_id": "189"}], "crash_cost": 20145.0, "normal_cost": 13430.0, "outsource_cost": 26860.0, "most_probable_duration": 0.0}, {"id": "16_3", "name": "Levelling ground", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "175"}, {"quantity": 1.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "174"}], "crash_cost": 2767.5, "normal_cost": 1845.0, "outsource_cost": 3690.0, "most_probable_duration": 0.0}, {"id": "16_30", "name": "Pylons concrete aging", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "16_31", "name": "Making of shoulders (pouring frameworks and concrete casting)", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 81000.0, "resource_id": "189"}], "crash_cost": 125145.0, "normal_cost": 83430.0, "outsource_cost": 166860.0, "most_probable_duration": 0.0}, {"id": "16_32", "name": "Shoulders concrete aging", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "16_33", "name": "Pouring prefabricated beam", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 52000.0, "resource_id": "189"}], "crash_cost": 80362.5, "normal_cost": 53575.0, "outsource_cost": 107150.0, "most_probable_duration": 0.0}, {"id": "16_34", "name": "Making of slab (pouring frameworks and concrete casting)", "resources": [{"quantity": 5.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 23500.0, "resource_id": "189"}], "crash_cost": 38895.0, "normal_cost": 25930.0, "outsource_cost": 51860.0, "most_probable_duration": 0.0}, {"id": "16_35", "name": "Slab's concrete aging", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "16_36", "name": "Making of embankments", "resources": [{"quantity": 5.0, "resource_id": "173"}, {"quantity": 3.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "177"}, {"quantity": 18000.0, "resource_id": "189"}], "crash_cost": 82080.0, "normal_cost": 54720.0, "outsource_cost": 109440.0, "most_probable_duration": 0.0}, {"id": "16_38", "name": "Embankments", "resources": [{"quantity": 10.0, "resource_id": "173"}, {"quantity": 6.0, "resource_id": "174"}, {"quantity": 2.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "177"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 68600.0, "resource_id": "189"}], "crash_cost": 283732.5, "normal_cost": 189155.0, "outsource_cost": 378310.0, "most_probable_duration": 0.0}, {"id": "16_39", "name": "Sound barriers", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 12600.0, "resource_id": "189"}], "crash_cost": 23625.0, "normal_cost": 15750.0, "outsource_cost": 31500.0, "most_probable_duration": 0.0}, {"id": "16_4", "name": "Containers placement", "resources": [{"quantity": 2.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}], "crash_cost": 2362.5, "normal_cost": 1575.0, "outsource_cost": 3150.0, "most_probable_duration": 0.0}, {"id": "16_41", "name": "Demolitions", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "184"}], "crash_cost": 4995.0, "normal_cost": 3330.0, "outsource_cost": 6660.0, "most_probable_duration": 0.0}, {"id": "16_42", "name": "Topsoil removal and clearing subbase", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "175"}], "crash_cost": 13837.5, "normal_cost": 9225.0, "outsource_cost": 18450.0, "most_probable_duration": 0.0}, {"id": "16_46", "name": "Embankments", "resources": [{"quantity": 10.0, "resource_id": "173"}, {"quantity": 6.0, "resource_id": "174"}, {"quantity": 2.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "177"}, {"quantity": 1.0, "resource_id": "187"}, {"quantity": 32000.0, "resource_id": "189"}], "crash_cost": 140880.0, "normal_cost": 93920.0, "outsource_cost": 187840.0, "most_probable_duration": 0.0}, {"id": "16_48", "name": "Demolitions", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "184"}], "crash_cost": 4995.0, "normal_cost": 3330.0, "outsource_cost": 6660.0, "most_probable_duration": 0.0}, {"id": "16_5", "name": "Connection to network service", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}], "crash_cost": 1890.0, "normal_cost": 1260.0, "outsource_cost": 2520.0, "most_probable_duration": 0.0}, {"id": "16_51", "name": "Carrying remaining soil", "resources": [{"quantity": 8.0, "resource_id": "173"}, {"quantity": 6.0, "resource_id": "174"}, {"quantity": 2.0, "resource_id": "179"}], "crash_cost": 66528.0, "normal_cost": 44352.0, "outsource_cost": 88704.0, "most_probable_duration": 0.0}, {"id": "16_52", "name": "Terracing", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1.0, "resource_id": "177"}, {"quantity": 1.0, "resource_id": "187"}, {"quantity": 15000.0, "resource_id": "189"}], "crash_cost": 42426.0, "normal_cost": 28284.0, "outsource_cost": 56568.0, "most_probable_duration": 0.0}, {"id": "16_55", "name": "Draining trenches", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 26000.0, "resource_id": "189"}], "crash_cost": 57427.5, "normal_cost": 38285.0, "outsource_cost": 76570.0, "most_probable_duration": 0.0}, {"id": "16_56", "name": "Catch water drains", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 10000.0, "resource_id": "189"}], "crash_cost": 52044.0, "normal_cost": 34696.0, "outsource_cost": 69392.0, "most_probable_duration": 0.0}, {"id": "16_58", "name": "Demolitions", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "184"}], "crash_cost": 4995.0, "normal_cost": 3330.0, "outsource_cost": 6660.0, "most_probable_duration": 0.0}, {"id": "16_59", "name": "Topsoil removal and clearing subbase", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "175"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "176"}], "crash_cost": 33412.5, "normal_cost": 22275.0, "outsource_cost": 44550.0, "most_probable_duration": 0.0}, {"id": "16_6", "name": "Pegging road", "resources": [{"quantity": 2.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 30000.0, "resource_id": "189"}], "crash_cost": 45945.0, "normal_cost": 30630.0, "outsource_cost": 61260.0, "most_probable_duration": 0.0}, {"id": "16_62", "name": "Catch water drains", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 15000.0, "resource_id": "189"}], "crash_cost": 36391.5, "normal_cost": 24261.0, "outsource_cost": 48522.0, "most_probable_duration": 0.0}, {"id": "16_63", "name": "Manhole covers", "resources": [{"quantity": 2.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 6000.0, "resource_id": "189"}], "crash_cost": 11362.5, "normal_cost": 7575.0, "outsource_cost": 15150.0, "most_probable_duration": 0.0}, {"id": "16_66", "name": "Retaining walls (frameworks and concrete casting)", "resources": [{"quantity": 5.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 88000.0, "resource_id": "189"}], "crash_cost": 135645.0, "normal_cost": 90430.0, "outsource_cost": 180860.0, "most_probable_duration": 0.0}, {"id": "16_67", "name": "Retaining walls concrete aging", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "16_68", "name": "Pouring prefabricated beams", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 50000.0, "resource_id": "189"}], "crash_cost": 77362.5, "normal_cost": 51575.0, "outsource_cost": 103150.0, "most_probable_duration": 0.0}, {"id": "16_69", "name": "Making of slabs (frameworks pouring and concrete casting)", "resources": [{"quantity": 5.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 8000.0, "resource_id": "189"}], "crash_cost": 14362.5, "normal_cost": 9575.0, "outsource_cost": 19150.0, "most_probable_duration": 0.0}, {"id": "16_7", "name": "Alternative road system", "resources": [{"quantity": 7.0, "resource_id": "173"}, {"quantity": 5.0, "resource_id": "174"}, {"quantity": 2.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "177"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 50000.0, "resource_id": "189"}], "crash_cost": 109290.0, "normal_cost": 72860.0, "outsource_cost": 145720.0, "most_probable_duration": 0.0}, {"id": "16_70", "name": "Slabs concrete aging", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 0.0, "most_probable_duration": 0.0}, {"id": "16_72", "name": "Carrying remaining soil", "resources": [{"quantity": 10.0, "resource_id": "173"}, {"quantity": 6.0, "resource_id": "174"}, {"quantity": 2.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "177"}, {"quantity": 1.0, "resource_id": "187"}], "crash_cost": 9288.0, "normal_cost": 6192.0, "outsource_cost": 12384.0, "most_probable_duration": 0.0}, {"id": "16_73", "name": "Terracing", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1.0, "resource_id": "177"}, {"quantity": 1.0, "resource_id": "187"}, {"quantity": 1800.0, "resource_id": "189"}], "crash_cost": 6021.0, "normal_cost": 4014.0, "outsource_cost": 8028.0, "most_probable_duration": 0.0}, {"id": "16_75", "name": "Embankments", "resources": [{"quantity": 10.0, "resource_id": "173"}, {"quantity": 6.0, "resource_id": "174"}, {"quantity": 2.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "177"}, {"quantity": 1.0, "resource_id": "187"}, {"quantity": 140000.0, "resource_id": "189"}], "crash_cost": 600096.0, "normal_cost": 400064.0, "outsource_cost": 800128.0, "most_probable_duration": 0.0}, {"id": "16_77", "name": "Draining trenches", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 3600.0, "resource_id": "189"}], "crash_cost": 12771.0, "normal_cost": 8514.0, "outsource_cost": 17028.0, "most_probable_duration": 0.0}, {"id": "16_78", "name": "Catch water drains", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 20000.0, "resource_id": "189"}], "crash_cost": 34630.5, "normal_cost": 23087.0, "outsource_cost": 46174.0, "most_probable_duration": 0.0}, {"id": "16_8", "name": "Demolition", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1.0, "resource_id": "183"}], "crash_cost": 4090.5, "normal_cost": 2727.0, "outsource_cost": 5454.0, "most_probable_duration": 0.0}, {"id": "16_80", "name": "Culverts", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 7000.0, "resource_id": "189"}], "crash_cost": 15225.0, "normal_cost": 10150.0, "outsource_cost": 20300.0, "most_probable_duration": 0.0}, {"id": "16_82", "name": "Demolitions", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "184"}], "crash_cost": 4995.0, "normal_cost": 3330.0, "outsource_cost": 6660.0, "most_probable_duration": 0.0}, {"id": "16_83", "name": "Topsoil removal and subbase clearing", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "175"}, {"quantity": 1.0, "resource_id": "176"}], "crash_cost": 44550.0, "normal_cost": 29700.0, "outsource_cost": 59400.0, "most_probable_duration": 0.0}, {"id": "16_85", "name": "Paving", "resources": [{"quantity": 7.0, "resource_id": "173"}, {"quantity": 5.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "183"}, {"quantity": 1.0, "resource_id": "178"}, {"quantity": 2500000.0, "resource_id": "190"}], "crash_cost": 3942375.0, "normal_cost": 2628250.0, "outsource_cost": 5256500.0, "most_probable_duration": 0.0}, {"id": "16_86", "name": "Guardrails pouring", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "185"}, {"quantity": 300000.0, "resource_id": "189"}], "crash_cost": 493011.0, "normal_cost": 328674.0, "outsource_cost": 657348.0, "most_probable_duration": 0.0}, {"id": "16_87", "name": "Coverage and shaping slopes", "resources": [{"quantity": 5.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 2.0, "resource_id": "176"}, {"quantity": 1.0, "resource_id": "186"}, {"quantity": 15000.0, "resource_id": "189"}], "crash_cost": 58950.0, "normal_cost": 39300.0, "outsource_cost": 78600.0, "most_probable_duration": 0.0}, {"id": "16_88", "name": "Cascades pouring", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 16500.0, "resource_id": "189"}], "crash_cost": 28530.0, "normal_cost": 19020.0, "outsource_cost": 38040.0, "most_probable_duration": 0.0}, {"id": "16_89", "name": "Road signals pouring", "resources": [{"quantity": 2.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "188"}, {"quantity": 80000.0, "resource_id": "189"}], "crash_cost": 122700.0, "normal_cost": 81800.0, "outsource_cost": 163600.0, "most_probable_duration": 0.0}, {"id": "16_9", "name": "Clearing subbase and topsoil removal", "resources": [{"quantity": 3.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "175"}, {"quantity": 1.0, "resource_id": "176"}], "crash_cost": 11070.0, "normal_cost": 7380.0, "outsource_cost": 14760.0, "most_probable_duration": 0.0}, {"id": "16_91", "name": "Network connections removal", "resources": [{"quantity": 2.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}], "crash_cost": 945.0, "normal_cost": 630.0, "outsource_cost": 1260.0, "most_probable_duration": 0.0}, {"id": "16_92", "name": "Containers removal", "resources": [{"quantity": 2.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "182"}], "crash_cost": 2362.5, "normal_cost": 1575.0, "outsource_cost": 3150.0, "most_probable_duration": 0.0}, {"id": "16_93", "name": "Rubbles removal", "resources": [{"quantity": 2.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "176"}], "crash_cost": 7020.0, "normal_cost": 4680.0, "outsource_cost": 9360.0, "most_probable_duration": 0.0}, {"id": "16_94", "name": "Fences removal", "resources": [{"quantity": 2.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}], "crash_cost": 945.0, "normal_cost": 630.0, "outsource_cost": 1260.0, "most_probable_duration": 0.0}, {"id": "16_1", "name": "Pegging and fence", "resources": [{"quantity": 2.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 10000.0, "resource_id": "189"}], "crash_cost": 15945.0, "normal_cost": 10630.0, "outsource_cost": 21260.0, "most_probable_duration": 0.0}, {"id": "16_11", "name": "Placement formworks and concrete casting", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 1.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "181"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 3000.0, "resource_id": "189"}], "crash_cost": 8145.0, "normal_cost": 5430.0, "outsource_cost": 10860.0, "most_probable_duration": 0.0}, {"id": "16_44", "name": "Catch water drains", "resources": [{"quantity": 4.0, "resource_id": "173"}, {"quantity": 2.0, "resource_id": "174"}, {"quantity": 1.0, "resource_id": "179"}, {"quantity": 1.0, "resource_id": "182"}, {"quantity": 10000.0, "resource_id": "189"}], "crash_cost": 19630.5, "normal_cost": 13087.0, "outsource_cost": 26174.0, "most_probable_duration": 0.0}], "cp_sat_schedule": {"status": "INFEASIBLE", "makespan": 0, "schedule": {}}, "cpm_static_makespan": 2176.0, "project_state_evolution": {"state_history": [{"makespan": 2176.0, "state_id": 0, "timestamp": 1783743939.0769362, "total_cost": 4076100.0, "direct_cost": 4076100.0, "monte_carlo": {"P90": 2288.9628607599425, "on_time_prob": 1.0, "mean_makespan": 2272.3533471054247}, "critical_path": [], "indirect_cost": 0.0, "action_applied": null, "resource_metrics": {"capacities": {"173": 1, "174": 1, "175": 1, "176": 1, "177": 1, "178": 1, "179": 1, "180": 1, "181": 1, "182": 1, "183": 1, "184": 1, "185": 1, "186": 1, "187": 1, "188": 1, "189": 1, "190": 1}, "total_demand": {"173": 254.0, "174": 118.0, "175": 6.0, "176": 24.0, "177": 10.0, "178": 1.0, "179": 15.0, "180": 1.0, "181": 10.0, "182": 24.0, "183": 2.0, "184": 4.0, "185": 1.0, "186": 1.0, "187": 5.0, "188": 1.0, "189": 1576100.0, "190": 2500000.0}, "utilization_rate": {"173": 254.0, "174": 118.0, "175": 6.0, "176": 24.0, "177": 10.0, "178": 1.0, "179": 15.0, "180": 1.0, "181": 10.0, "182": 24.0, "183": 2.0, "184": 4.0, "185": 1.0, "186": 1.0, "187": 5.0, "188": 1.0, "189": 1576100.0, "190": 2500000.0}}}, {"makespan": 26.0, "state_id": 1, "timestamp": 1783743939.324735, "total_cost": 4076100.0, "direct_cost": 4076100.0, "monte_carlo": {"P90": 946.8006607865492, "on_time_prob": 1.0, "mean_makespan": 931.9997090388786}, "critical_path": ["16_49", "16_17", "16_19", "16_2", "16_22", "16_3", "16_38", "16_39", "16_4", "16_41", "16_42", "16_46", "16_48", "16_5", "16_51", "16_52", "16_55", "16_56", "16_58", "16_59", "16_6", "16_62", "16_66", "16_67", "16_68", "16_69", "16_7", "16_70", "16_72", "16_73", "16_75", "16_78", "16_82", "16_83", "16_85", "16_86", "16_89", "16_9", "16_91", "16_92", "16_93", "16_94", "16_1", "16_11", "16_44"], "indirect_cost": 0.0, "action_applied": {"priority": 1, "action_type": "Crash", "crash_level": 1.5, "custom_params": {"modes": [0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1]}, "overlap_ratio": 0.3, "affected_tasks": ["16_17", "16_19", "16_20", "16_22", "16_26", "16_28", "16_3", "16_30", "16_31", "16_32", "16_36", "16_38", "16_39", "16_4", "16_41", "16_46", "16_48", "16_51", "16_52", "16_55", "16_56", "16_66", "16_67", "16_68", "16_69", "16_7", "16_73", "16_75", "16_78", "16_80", "16_83", "16_86", "16_89", "16_91", "16_94", "16_11", "16_44"], "resource_delta": {}, "outsource_level": 2.0, "expected_cost_delta": 7750157.5, "expected_risk_delta": 18.2944, "expected_duration_delta": 5138.400000000001}, "resource_metrics": {"capacities": {"173": 1, "174": 1, "175": 1, "176": 1, "177": 1, "178": 1, "179": 1, "180": 1, "181": 1, "182": 1, "183": 1, "184": 1, "185": 1, "186": 1, "187": 1, "188": 1, "189": 1, "190": 1}, "total_demand": {"173": 328.0, "174": 162.0, "175": 8.0, "176": 32.0, "177": 19.0, "178": 1.0, "179": 24.0, "180": 1.0, "181": 16.0, "182": 38.0, "183": 2.0, "184": 6.0, "185": 2.0, "186": 1.0, "187": 9.0, "188": 2.0, "189": 2126350.0, "190": 2500000.0}, "utilization_rate": {"173": 328.0, "174": 162.0, "175": 8.0, "176": 32.0, "177": 19.0, "178": 1.0, "179": 24.0, "180": 1.0, "181": 16.0, "182": 38.0, "183": 2.0, "184": 6.0, "185": 2.0, "186": 1.0, "187": 9.0, "188": 2.0, "189": 2126350.0, "190": 2500000.0}}}], "current_state_id": 1, "before_after_comparison": {"action_applied": {"priority": 1, "action_type": "Crash", "crash_level": 1.5, "custom_params": {"modes": [0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1]}, "overlap_ratio": 0.3, "affected_tasks": ["16_17", "16_19", "16_20", "16_22", "16_26", "16_28", "16_3", "16_30", "16_31", "16_32", "16_36", "16_38", "16_39", "16_4", "16_41", "16_46", "16_48", "16_51", "16_52", "16_55", "16_56", "16_66", "16_67", "16_68", "16_69", "16_7", "16_73", "16_75", "16_78", "16_80", "16_83", "16_86", "16_89", "16_91", "16_94", "16_11", "16_44"], "resource_delta": {}, "outsource_level": 2.0, "expected_cost_delta": 7750157.5, "expected_risk_delta": 18.2944, "expected_duration_delta": 5138.400000000001}, "after_state_id": 1, "before_state_id": 0, "metrics_comparison": {"makespan": {"after": 26.0, "delta": -2150.0, "before": 2176.0, "percent_change": -98.80514705882352}, "total_cost": {"after": 4076100.0, "delta": 0.0, "before": 4076100.0, "percent_change": 0.0}, "P90_makespan": {"after": 946.8006607865492, "delta": -1342.1621999733934, "before": 2288.9628607599425}, "on_time_probability": {"after": 1.0, "delta": 0.0, "before": 1.0}}, "top_attention_shifts": [{"delta": 0.16450399160385132, "task_id": "16_93", "score_after": 0.6208673119544983, "score_before": 0.456363320350647}, {"delta": 0.15724468231201172, "task_id": "16_92", "score_after": 0.6562235355377197, "score_before": 0.498978853225708}, {"delta": 0.155464768409729, "task_id": "16_91", "score_after": 0.6562840938568115, "score_before": 0.5008193254470825}, {"delta": 0.14744406938552856, "task_id": "16_89", "score_after": 0.5934039950370789, "score_before": 0.4459599256515503}, {"delta": 0.14395558834075928, "task_id": "16_86", "score_after": 0.5879831314086914, "score_before": 0.44402754306793213}], "critical_path_evolution": {"after_count": 45, "before_count": 0, "newly_critical_tasks": ["16_66", "16_72", "16_5", "16_93", "16_19", "16_38", "16_69", "16_48", "16_52", "16_42", "16_73", "16_83", "16_9", "16_55", "16_17", "16_2", "16_22", "16_1", "16_49", "16_4", "16_94", "16_75", "16_7", "16_92", "16_41", "16_6", "16_68", "16_11", "16_3", "16_91", "16_46", "16_62", "16_70", "16_44", "16_39", "16_89", "16_86", "16_58", "16_78", "16_51", "16_85", "16_82", "16_67", "16_59", "16_56"], "no_longer_critical_tasks": []}, "resource_utilization_evolution": {"after": {"capacities": {"173": 1, "174": 1, "175": 1, "176": 1, "177": 1, "178": 1, "179": 1, "180": 1, "181": 1, "182": 1, "183": 1, "184": 1, "185": 1, "186": 1, "187": 1, "188": 1, "189": 1, "190": 1}, "total_demand": {"173": 328.0, "174": 162.0, "175": 8.0, "176": 32.0, "177": 19.0, "178": 1.0, "179": 24.0, "180": 1.0, "181": 16.0, "182": 38.0, "183": 2.0, "184": 6.0, "185": 2.0, "186": 1.0, "187": 9.0, "188": 2.0, "189": 2126350.0, "190": 2500000.0}, "utilization_rate": {"173": 328.0, "174": 162.0, "175": 8.0, "176": 32.0, "177": 19.0, "178": 1.0, "179": 24.0, "180": 1.0, "181": 16.0, "182": 38.0, "183": 2.0, "184": 6.0, "185": 2.0, "186": 1.0, "187": 9.0, "188": 2.0, "189": 2126350.0, "190": 2500000.0}}, "before": {"capacities": {"173": 1, "174": 1, "175": 1, "176": 1, "177": 1, "178": 1, "179": 1, "180": 1, "181": 1, "182": 1, "183": 1, "184": 1, "185": 1, "186": 1, "187": 1, "188": 1, "189": 1, "190": 1}, "total_demand": {"173": 254.0, "174": 118.0, "175": 6.0, "176": 24.0, "177": 10.0, "178": 1.0, "179": 15.0, "180": 1.0, "181": 10.0, "182": 24.0, "183": 2.0, "184": 4.0, "185": 1.0, "186": 1.0, "187": 5.0, "188": 1.0, "189": 1576100.0, "190": 2500000.0}, "utilization_rate": {"173": 254.0, "174": 118.0, "175": 6.0, "176": 24.0, "177": 10.0, "178": 1.0, "179": 15.0, "180": 1.0, "181": 10.0, "182": 24.0, "183": 2.0, "184": 4.0, "185": 1.0, "186": 1.0, "187": 5.0, "188": 1.0, "189": 1576100.0, "190": 2500000.0}}}}}}}	0	0	0.0000	2026-07-10 13:12:30.468224	2026-07-11 04:25:41.60624
17	\N	Sea Electricity	CON	Planning	168643738.00	199129396.60	\N	\N	\N	\N	{"simulation_results": {"budget": 250274622.0, "deadline": 14788.800000000001, "project_id": "17", "monte_carlo": {"P90": 11492.707671066002, "on_time_prob": 1.0, "mean_makespan": 11477.425159274035, "criticality_indices": {"17_1": 0.0, "17_2": 0.0, "17_3": 0.0, "17_6": 0.0, "17_7": 0.0, "17_11": 0.0, "17_12": 0.0, "17_13": 0.0, "17_14": 0.0, "17_16": 0.0, "17_17": 0.0, "17_21": 0.513, "17_23": 0.487, "17_25": 1.0, "17_27": 0.0, "17_29": 0.0, "17_31": 0.0, "17_46": 0.0, "17_47": 0.0, "17_48": 0.0, "17_49": 0.0, "17_50": 0.0, "17_51": 0.0, "17_52": 0.0, "17_53": 0.0, "17_56": 0.0, "17_57": 0.0, "17_58": 0.0, "17_75": 0.0, "17_76": 0.0, "17_77": 0.0, "17_81": 0.0, "17_82": 0.0, "17_84": 0.0, "17_85": 0.0, "17_86": 0.0, "17_87": 0.0, "17_88": 0.0, "17_89": 0.0, "17_90": 0.0, "17_91": 0.0, "17_94": 0.0, "17_95": 0.0, "17_100": 0.0, "17_101": 0.0, "17_102": 0.0, "17_104": 0.0, "17_105": 0.0, "17_106": 0.0, "17_107": 0.0, "17_108": 1.0, "17_109": 1.0, "17_110": 1.0, "17_111": 1.0, "17_112": 1.0, "17_126": 0.0, "17_128": 0.0, "17_129": 0.0, "17_130": 0.0, "17_131": 0.0, "17_133": 0.0, "17_134": 0.0, "17_136": 0.0, "17_137": 0.0, "17_138": 0.0, "17_139": 0.0, "17_140": 0.0, "17_141": 0.0, "17_149": 0.0, "17_150": 0.0, "17_151": 0.0, "17_152": 0.0, "17_153": 0.0, "17_154": 0.0, "17_156": 0.0, "17_157": 0.0, "17_158": 0.0, "17_162": 0.0, "17_193": 0.0, "17_194": 0.0, "17_195": 0.0, "17_196": 0.0, "17_197": 0.0, "17_198": 0.0, "17_199": 0.0, "17_200": 0.0, "17_201": 0.0, "17_202": 0.0, "17_203": 0.0, "17_204": 0.0, "17_205": 0.0, "17_206": 0.0, "17_207": 0.0, "17_208": 0.0, "17_209": 0.0, "17_210": 0.0, "17_211": 0.0, "17_212": 0.0, "17_213": 0.0, "17_214": 0.0, "17_215": 0.0, "17_216": 0.0, "17_217": 0.0, "17_218": 0.0, "17_219": 0.0, "17_220": 0.0, "17_221": 0.0, "17_222": 0.0, "17_223": 0.0, "17_224": 0.0, "17_225": 0.0, "17_226": 0.0, "17_227": 0.0, "17_228": 0.0, "17_229": 0.0, "17_230": 0.0, "17_231": 0.0, "17_232": 0.0, "17_233": 0.0, "17_234": 0.0, "17_235": 0.0, "17_236": 0.0, "17_237": 0.0, "17_238": 0.0, "17_239": 0.0, "17_240": 0.0, "17_241": 0.0, "17_242": 0.0, "17_243": 0.0, "17_244": 0.0, "17_245": 0.0, "17_246": 0.0, "17_247": 0.0, "17_248": 0.0, "17_249": 0.0, "17_250": 0.0, "17_251": 0.0, "17_252": 0.0, "17_253": 0.0, "17_254": 0.0, "17_255": 0.0, "17_256": 0.0, "17_257": 0.0, "17_258": 0.0, "17_259": 0.0, "17_260": 0.0, "17_261": 0.0, "17_262": 0.0, "17_263": 0.0, "17_264": 0.0, "17_265": 0.0, "17_266": 0.0, "17_267": 0.0, "17_268": 0.0, "17_269": 0.0, "17_270": 0.0, "17_271": 0.0, "17_272": 0.0, "17_273": 0.0, "17_274": 0.0, "17_275": 0.0, "17_276": 0.0, "17_277": 0.0, "17_278": 0.0, "17_279": 0.0, "17_280": 0.0, "17_281": 0.0, "17_282": 0.0, "17_283": 0.0, "17_284": 0.0, "17_285": 0.0, "17_286": 0.0, "17_287": 0.0, "17_288": 1.0, "17_289": 0.0, "17_290": 0.0, "17_291": 0.0, "17_292": 0.0, "17_293": 0.0, "17_294": 0.0, "17_295": 0.0, "17_296": 0.0, "17_297": 0.0, "17_298": 0.0, "17_299": 0.0, "17_300": 0.0, "17_301": 0.0, "17_302": 0.0, "17_303": 0.0, "17_304": 0.0, "17_305": 0.0, "17_306": 0.0, "17_307": 0.0, "17_308": 0.0, "17_309": 0.0, "17_310": 0.0, "17_311": 0.0, "17_312": 1.0, "17_313": 0.0, "17_314": 0.0, "17_315": 0.0, "17_316": 0.0, "17_317": 0.0, "17_318": 0.0, "17_319": 0.0, "17_320": 0.0, "17_321": 0.0, "17_322": 0.0, "17_323": 0.0, "17_324": 0.0, "17_325": 0.0, "17_326": 0.0, "17_327": 0.0, "17_328": 0.0, "17_329": 0.0, "17_330": 0.0, "17_331": 0.0, "17_332": 0.0, "17_333": 0.0, "17_334": 0.0, "17_335": 0.0, "17_336": 1.0, "17_337": 1.0, "17_338": 1.0, "17_339": 1.0, "17_340": 1.0, "17_341": 1.0, "17_342": 1.0, "17_343": 1.0, "17_344": 1.0, "17_345": 1.0, "17_346": 1.0, "17_347": 1.0, "17_348": 1.0, "17_349": 1.0, "17_350": 1.0, "17_351": 1.0, "17_352": 1.0, "17_353": 1.0, "17_354": 1.0, "17_355": 1.0, "17_356": 1.0, "17_357": 1.0, "17_358": 1.0, "17_359": 1.0, "17_360": 0.0, "17_361": 0.0, "17_362": 0.0, "17_363": 0.0, "17_364": 0.0, "17_365": 0.0, "17_366": 0.0, "17_367": 0.0, "17_368": 0.0, "17_369": 0.0, "17_370": 0.0, "17_371": 0.0, "17_372": 0.0, "17_373": 0.0, "17_374": 0.0, "17_375": 0.0, "17_376": 0.0, "17_377": 0.0, "17_378": 0.0, "17_379": 0.0, "17_380": 0.0, "17_381": 0.0, "17_382": 1.0, "17_383": 0.0, "17_384": 0.0, "17_385": 0.0, "17_386": 0.0, "17_387": 0.0, "17_388": 0.0, "17_389": 0.0, "17_390": 0.0, "17_391": 0.0, "17_392": 0.0, "17_393": 0.0, "17_394": 0.0, "17_395": 0.0, "17_396": 0.0, "17_397": 0.0, "17_398": 0.0, "17_399": 0.0, "17_400": 0.0, "17_401": 0.0, "17_402": 0.0, "17_403": 0.0, "17_404": 0.0, "17_405": 1.0, "17_406": 0.038, "17_407": 0.033, "17_408": 0.044, "17_409": 0.054, "17_410": 0.043, "17_411": 0.043, "17_412": 0.044, "17_413": 0.034, "17_414": 0.039, "17_415": 0.057, "17_416": 0.04, "17_417": 0.049, "17_418": 0.036, "17_419": 0.056, "17_420": 0.051, "17_421": 0.034, "17_422": 0.045, "17_423": 0.034, "17_424": 0.042, "17_425": 0.034, "17_426": 0.038, "17_427": 0.036, "17_428": 0.039, "17_429": 0.037, "17_430": 0.038, "17_431": 0.033, "17_432": 0.044, "17_433": 0.054, "17_434": 0.043, "17_435": 0.043, "17_436": 0.044, "17_437": 0.034, "17_438": 0.039, "17_439": 0.057, "17_440": 0.04, "17_441": 0.049, "17_442": 0.036, "17_443": 0.056, "17_444": 0.051, "17_445": 0.034, "17_446": 0.045, "17_447": 0.034, "17_448": 0.042, "17_449": 0.034, "17_450": 0.038, "17_451": 0.036, "17_452": 0.039, "17_453": 0.037, "17_454": 0.038, "17_455": 0.033, "17_456": 0.044, "17_457": 0.054, "17_458": 0.043, "17_459": 0.043, "17_460": 0.044, "17_461": 0.034, "17_462": 0.039, "17_463": 0.057, "17_464": 0.04, "17_465": 0.049, "17_466": 0.036, "17_467": 0.056, "17_468": 0.051, "17_469": 0.034, "17_470": 0.045, "17_471": 0.034, "17_472": 0.042, "17_473": 0.034, "17_474": 0.038, "17_475": 0.036, "17_476": 0.039, "17_477": 0.037, "17_478": 0.0, "17_479": 0.0, "17_480": 0.0, "17_481": 0.0, "17_482": 0.0, "17_483": 0.0, "17_484": 0.0, "17_485": 0.0, "17_486": 0.0, "17_487": 0.0, "17_488": 0.0, "17_489": 0.0, "17_490": 0.0, "17_491": 0.0, "17_492": 0.0, "17_493": 0.0, "17_494": 0.0, "17_495": 0.0, "17_496": 0.0, "17_497": 0.0, "17_498": 0.0, "17_499": 0.0, "17_500": 0.0, "17_501": 0.0, "17_502": 0.0, "17_503": 0.0, "17_504": 0.0, "17_505": 0.0, "17_506": 0.0, "17_507": 0.0, "17_508": 0.0, "17_509": 0.0, "17_510": 0.0, "17_511": 0.0, "17_512": 0.0, "17_513": 0.0, "17_514": 0.0, "17_515": 0.0, "17_516": 0.0, "17_517": 0.0, "17_518": 0.0, "17_519": 0.0, "17_520": 0.0, "17_521": 0.0, "17_522": 0.0, "17_523": 0.0, "17_524": 0.0, "17_525": 0.0, "17_526": 0.0, "17_527": 0.0, "17_528": 0.0, "17_529": 0.0, "17_530": 0.0, "17_531": 0.0, "17_532": 0.0, "17_533": 0.0, "17_534": 0.0, "17_535": 0.0, "17_536": 0.0, "17_537": 0.0, "17_538": 0.0, "17_539": 0.0, "17_540": 0.0, "17_541": 0.0, "17_542": 0.0, "17_543": 0.0, "17_544": 0.0, "17_545": 0.0, "17_546": 0.0, "17_547": 0.0, "17_548": 0.0, "17_549": 0.0, "17_550": 0.0, "17_551": 0.0}}, "dependencies": [["17_1", "17_2"], ["17_2", "17_3"], ["17_551", "17_11"], ["17_6", "17_7"], ["17_3", "17_526"], ["17_7", "17_526"], ["17_11", "17_526"], ["17_3", "17_527"], ["17_7", "17_527"], ["17_11", "17_527"], ["17_3", "17_528"], ["17_7", "17_528"], ["17_11", "17_528"], ["17_3", "17_529"], ["17_7", "17_529"], ["17_11", "17_529"], ["17_3", "17_530"], ["17_7", "17_530"], ["17_11", "17_530"], ["17_3", "17_531"], ["17_7", "17_531"], ["17_11", "17_531"], ["17_3", "17_532"], ["17_7", "17_532"], ["17_11", "17_532"], ["17_3", "17_533"], ["17_7", "17_533"], ["17_11", "17_533"], ["17_3", "17_534"], ["17_7", "17_534"], ["17_11", "17_534"], ["17_3", "17_535"], ["17_7", "17_535"], ["17_11", "17_535"], ["17_3", "17_536"], ["17_7", "17_536"], ["17_11", "17_536"], ["17_3", "17_537"], ["17_7", "17_537"], ["17_11", "17_537"], ["17_3", "17_538"], ["17_7", "17_538"], ["17_11", "17_538"], ["17_3", "17_539"], ["17_7", "17_539"], ["17_11", "17_539"], ["17_3", "17_540"], ["17_7", "17_540"], ["17_11", "17_540"], ["17_3", "17_541"], ["17_7", "17_541"], ["17_11", "17_541"], ["17_3", "17_542"], ["17_7", "17_542"], ["17_11", "17_542"], ["17_3", "17_543"], ["17_7", "17_543"], ["17_11", "17_543"], ["17_3", "17_544"], ["17_7", "17_544"], ["17_11", "17_544"], ["17_3", "17_545"], ["17_7", "17_545"], ["17_11", "17_545"], ["17_3", "17_546"], ["17_7", "17_546"], ["17_11", "17_546"], ["17_3", "17_547"], ["17_7", "17_547"], ["17_11", "17_547"], ["17_3", "17_548"], ["17_7", "17_548"], ["17_11", "17_548"], ["17_3", "17_549"], ["17_7", "17_549"], ["17_11", "17_549"], ["17_3", "17_550"], ["17_7", "17_550"], ["17_11", "17_550"], ["17_526", "17_12"], ["17_527", "17_13"], ["17_528", "17_14"], ["17_529", "17_196"], ["17_530", "17_197"], ["17_531", "17_198"], ["17_532", "17_199"], ["17_533", "17_200"], ["17_534", "17_201"], ["17_535", "17_202"], ["17_536", "17_203"], ["17_537", "17_204"], ["17_538", "17_205"], ["17_539", "17_206"], ["17_540", "17_207"], ["17_541", "17_208"], ["17_542", "17_209"], ["17_543", "17_210"], ["17_544", "17_211"], ["17_545", "17_212"], ["17_546", "17_213"], ["17_547", "17_214"], ["17_548", "17_215"], ["17_549", "17_216"], ["17_550", "17_217"], ["17_12", "17_16"], ["17_16", "17_17"], ["17_13", "17_162"], ["17_14", "17_218"], ["17_196", "17_219"], ["17_197", "17_220"], ["17_198", "17_221"], ["17_199", "17_222"], ["17_200", "17_223"], ["17_201", "17_224"], ["17_202", "17_225"], ["17_203", "17_226"], ["17_204", "17_227"], ["17_205", "17_228"], ["17_206", "17_229"], ["17_207", "17_230"], ["17_208", "17_231"], ["17_209", "17_232"], ["17_210", "17_233"], ["17_211", "17_234"], ["17_212", "17_235"], ["17_213", "17_236"], ["17_214", "17_237"], ["17_215", "17_238"], ["17_216", "17_239"], ["17_217", "17_240"], ["17_162", "17_241"], ["17_218", "17_242"], ["17_219", "17_243"], ["17_220", "17_244"], ["17_221", "17_245"], ["17_222", "17_246"], ["17_223", "17_247"], ["17_224", "17_248"], ["17_225", "17_249"], ["17_226", "17_250"], ["17_227", "17_251"], ["17_228", "17_252"], ["17_229", "17_253"], ["17_230", "17_254"], ["17_231", "17_255"], ["17_232", "17_256"], ["17_233", "17_257"], ["17_234", "17_258"], ["17_235", "17_259"], ["17_236", "17_260"], ["17_237", "17_261"], ["17_238", "17_262"], ["17_239", "17_263"], ["17_240", "17_264"], ["17_21", "17_25"], ["17_23", "17_25"], ["17_25", "17_337"], ["17_337", "17_338"], ["17_338", "17_339"], ["17_339", "17_340"], ["17_340", "17_341"], ["17_341", "17_342"], ["17_342", "17_343"], ["17_343", "17_344"], ["17_344", "17_345"], ["17_345", "17_346"], ["17_346", "17_347"], ["17_347", "17_348"], ["17_348", "17_349"], ["17_349", "17_350"], ["17_350", "17_351"], ["17_351", "17_352"], ["17_352", "17_353"], ["17_353", "17_354"], ["17_354", "17_355"], ["17_355", "17_356"], ["17_356", "17_357"], ["17_357", "17_358"], ["17_358", "17_359"], ["17_25", "17_29"], ["17_27", "17_29"], ["17_337", "17_360"], ["17_27", "17_360"], ["17_338", "17_361"], ["17_27", "17_361"], ["17_339", "17_362"], ["17_27", "17_362"], ["17_27", "17_363"], ["17_341", "17_364"], ["17_27", "17_364"], ["17_342", "17_365"], ["17_27", "17_365"], ["17_343", "17_366"], ["17_27", "17_366"], ["17_344", "17_367"], ["17_27", "17_367"], ["17_345", "17_368"], ["17_27", "17_368"], ["17_346", "17_369"], ["17_27", "17_369"], ["17_347", "17_370"], ["17_27", "17_370"], ["17_348", "17_371"], ["17_27", "17_371"], ["17_349", "17_372"], ["17_27", "17_372"], ["17_350", "17_373"], ["17_27", "17_373"], ["17_351", "17_374"], ["17_27", "17_374"], ["17_352", "17_375"], ["17_27", "17_375"], ["17_353", "17_376"], ["17_27", "17_376"], ["17_354", "17_377"], ["17_27", "17_377"], ["17_355", "17_378"], ["17_27", "17_378"], ["17_356", "17_379"], ["17_27", "17_379"], ["17_357", "17_380"], ["17_27", "17_380"], ["17_358", "17_381"], ["17_27", "17_381"], ["17_359", "17_382"], ["17_27", "17_382"], ["17_29", "17_31"], ["17_360", "17_383"], ["17_361", "17_384"], ["17_362", "17_385"], ["17_363", "17_386"], ["17_364", "17_387"], ["17_365", "17_388"], ["17_366", "17_389"], ["17_367", "17_390"], ["17_368", "17_391"], ["17_369", "17_392"], ["17_370", "17_393"], ["17_371", "17_394"], ["17_372", "17_395"], ["17_373", "17_396"], ["17_374", "17_397"], ["17_375", "17_398"], ["17_376", "17_399"], ["17_377", "17_400"], ["17_378", "17_401"], ["17_379", "17_402"], ["17_380", "17_403"], ["17_381", "17_404"], ["17_382", "17_405"], ["17_31", "17_313"], ["17_383", "17_314"], ["17_384", "17_315"], ["17_385", "17_316"], ["17_386", "17_317"], ["17_387", "17_318"], ["17_388", "17_319"], ["17_389", "17_320"], ["17_390", "17_321"], ["17_391", "17_322"], ["17_392", "17_323"], ["17_393", "17_324"], ["17_394", "17_325"], ["17_395", "17_326"], ["17_396", "17_327"], ["17_397", "17_328"], ["17_398", "17_329"], ["17_399", "17_330"], ["17_400", "17_331"], ["17_401", "17_332"], ["17_402", "17_333"], ["17_403", "17_334"], ["17_404", "17_335"], ["17_405", "17_336"], ["17_313", "17_289"], ["17_241", "17_289"], ["17_314", "17_290"], ["17_242", "17_290"], ["17_315", "17_291"], ["17_243", "17_291"], ["17_316", "17_292"], ["17_244", "17_292"], ["17_317", "17_293"], ["17_245", "17_293"], ["17_318", "17_294"], ["17_246", "17_294"], ["17_319", "17_295"], ["17_247", "17_295"], ["17_320", "17_296"], ["17_248", "17_296"], ["17_321", "17_297"], ["17_249", "17_297"], ["17_322", "17_298"], ["17_250", "17_298"], ["17_323", "17_299"], ["17_251", "17_299"], ["17_324", "17_300"], ["17_252", "17_300"], ["17_325", "17_301"], ["17_253", "17_301"], ["17_326", "17_302"], ["17_254", "17_302"], ["17_327", "17_303"], ["17_255", "17_303"], ["17_328", "17_304"], ["17_256", "17_304"], ["17_329", "17_305"], ["17_257", "17_305"], ["17_330", "17_306"], ["17_258", "17_306"], ["17_331", "17_307"], ["17_259", "17_307"], ["17_332", "17_308"], ["17_260", "17_308"], ["17_333", "17_309"], ["17_261", "17_309"], ["17_334", "17_310"], ["17_262", "17_310"], ["17_335", "17_311"], ["17_263", "17_311"], ["17_336", "17_312"], ["17_264", "17_312"], ["17_289", "17_265"], ["17_290", "17_266"], ["17_291", "17_267"], ["17_292", "17_268"], ["17_293", "17_269"], ["17_294", "17_270"], ["17_295", "17_271"], ["17_296", "17_272"], ["17_297", "17_273"], ["17_298", "17_274"], ["17_299", "17_275"], ["17_300", "17_276"], ["17_301", "17_277"], ["17_302", "17_278"], ["17_303", "17_279"], ["17_304", "17_280"], ["17_305", "17_281"], ["17_306", "17_282"], ["17_307", "17_283"], ["17_308", "17_284"], ["17_309", "17_285"], ["17_310", "17_286"], ["17_311", "17_287"], ["17_312", "17_288"], ["17_46", "17_53"], ["17_47", "17_52"], ["17_48", "17_51"], ["17_49", "17_50"], ["17_51", "17_57"], ["17_50", "17_57"], ["17_56", "17_57"], ["17_52", "17_58"], ["17_56", "17_58"], ["17_53", "17_502"], ["17_57", "17_502"], ["17_58", "17_502"], ["17_53", "17_503"], ["17_57", "17_503"], ["17_58", "17_503"], ["17_53", "17_504"], ["17_57", "17_504"], ["17_58", "17_504"], ["17_53", "17_505"], ["17_57", "17_505"], ["17_58", "17_505"], ["17_53", "17_506"], ["17_57", "17_506"], ["17_58", "17_506"], ["17_53", "17_507"], ["17_57", "17_507"], ["17_58", "17_507"], ["17_53", "17_508"], ["17_57", "17_508"], ["17_58", "17_508"], ["17_53", "17_509"], ["17_57", "17_509"], ["17_58", "17_509"], ["17_53", "17_510"], ["17_57", "17_510"], ["17_58", "17_510"], ["17_53", "17_511"], ["17_57", "17_511"], ["17_58", "17_511"], ["17_53", "17_512"], ["17_57", "17_512"], ["17_58", "17_512"], ["17_53", "17_513"], ["17_57", "17_513"], ["17_58", "17_513"], ["17_53", "17_514"], ["17_57", "17_514"], ["17_58", "17_514"], ["17_53", "17_515"], ["17_57", "17_515"], ["17_58", "17_515"], ["17_53", "17_516"], ["17_57", "17_516"], ["17_58", "17_516"], ["17_53", "17_517"], ["17_57", "17_517"], ["17_58", "17_517"], ["17_53", "17_518"], ["17_57", "17_518"], ["17_58", "17_518"], ["17_53", "17_519"], ["17_57", "17_519"], ["17_58", "17_519"], ["17_53", "17_520"], ["17_57", "17_520"], ["17_58", "17_520"], ["17_53", "17_521"], ["17_57", "17_521"], ["17_58", "17_521"], ["17_53", "17_522"], ["17_57", "17_522"], ["17_58", "17_522"], ["17_53", "17_523"], ["17_57", "17_523"], ["17_58", "17_523"], ["17_53", "17_524"], ["17_57", "17_524"], ["17_58", "17_524"], ["17_53", "17_525"], ["17_57", "17_525"], ["17_58", "17_525"], ["17_502", "17_478"], ["17_265", "17_478"], ["17_503", "17_479"], ["17_266", "17_479"], ["17_504", "17_480"], ["17_267", "17_480"], ["17_505", "17_481"], ["17_268", "17_481"], ["17_506", "17_482"], ["17_269", "17_482"], ["17_507", "17_483"], ["17_270", "17_483"], ["17_508", "17_484"], ["17_271", "17_484"], ["17_509", "17_485"], ["17_272", "17_485"], ["17_510", "17_486"], ["17_273", "17_486"], ["17_511", "17_487"], ["17_274", "17_487"], ["17_512", "17_488"], ["17_275", "17_488"], ["17_513", "17_489"], ["17_276", "17_489"], ["17_514", "17_490"], ["17_277", "17_490"], ["17_515", "17_491"], ["17_278", "17_491"], ["17_516", "17_492"], ["17_279", "17_492"], ["17_517", "17_493"], ["17_280", "17_493"], ["17_518", "17_494"], ["17_281", "17_494"], ["17_519", "17_495"], ["17_282", "17_495"], ["17_520", "17_496"], ["17_283", "17_496"], ["17_521", "17_497"], ["17_284", "17_497"], ["17_522", "17_498"], ["17_285", "17_498"], ["17_523", "17_499"], ["17_286", "17_499"], ["17_524", "17_500"], ["17_287", "17_500"], ["17_525", "17_501"], ["17_288", "17_501"], ["17_112", "17_454"], ["17_478", "17_454"], ["17_112", "17_455"], ["17_479", "17_455"], ["17_112", "17_456"], ["17_480", "17_456"], ["17_112", "17_457"], ["17_481", "17_457"], ["17_112", "17_458"], ["17_482", "17_458"], ["17_112", "17_459"], ["17_483", "17_459"], ["17_112", "17_460"], ["17_484", "17_460"], ["17_112", "17_461"], ["17_485", "17_461"], ["17_112", "17_462"], ["17_486", "17_462"], ["17_112", "17_463"], ["17_487", "17_463"], ["17_112", "17_464"], ["17_488", "17_464"], ["17_112", "17_465"], ["17_489", "17_465"], ["17_112", "17_466"], ["17_490", "17_466"], ["17_112", "17_467"], ["17_491", "17_467"], ["17_112", "17_468"], ["17_492", "17_468"], ["17_112", "17_469"], ["17_493", "17_469"], ["17_112", "17_470"], ["17_494", "17_470"], ["17_112", "17_471"], ["17_495", "17_471"], ["17_112", "17_472"], ["17_496", "17_472"], ["17_112", "17_473"], ["17_497", "17_473"], ["17_112", "17_474"], ["17_498", "17_474"], ["17_112", "17_475"], ["17_499", "17_475"], ["17_112", "17_476"], ["17_500", "17_476"], ["17_112", "17_477"], ["17_501", "17_477"], ["17_154", "17_430"], ["17_454", "17_430"], ["17_154", "17_431"], ["17_455", "17_431"], ["17_154", "17_432"], ["17_456", "17_432"], ["17_154", "17_433"], ["17_457", "17_433"], ["17_154", "17_434"], ["17_458", "17_434"], ["17_154", "17_435"], ["17_459", "17_435"], ["17_154", "17_436"], ["17_460", "17_436"], ["17_154", "17_437"], ["17_461", "17_437"], ["17_154", "17_438"], ["17_462", "17_438"], ["17_154", "17_439"], ["17_463", "17_439"], ["17_154", "17_440"], ["17_464", "17_440"], ["17_154", "17_441"], ["17_465", "17_441"], ["17_154", "17_442"], ["17_466", "17_442"], ["17_154", "17_443"], ["17_467", "17_443"], ["17_154", "17_444"], ["17_468", "17_444"], ["17_154", "17_445"], ["17_469", "17_445"], ["17_154", "17_446"], ["17_470", "17_446"], ["17_154", "17_447"], ["17_471", "17_447"], ["17_154", "17_448"], ["17_472", "17_448"], ["17_154", "17_449"], ["17_473", "17_449"], ["17_154", "17_450"], ["17_474", "17_450"], ["17_154", "17_451"], ["17_475", "17_451"], ["17_154", "17_452"], ["17_476", "17_452"], ["17_154", "17_453"], ["17_477", "17_453"], ["17_430", "17_406"], ["17_431", "17_407"], ["17_432", "17_408"], ["17_433", "17_409"], ["17_434", "17_410"], ["17_435", "17_411"], ["17_436", "17_412"], ["17_437", "17_413"], ["17_438", "17_414"], ["17_439", "17_415"], ["17_440", "17_416"], ["17_441", "17_417"], ["17_442", "17_418"], ["17_443", "17_419"], ["17_445", "17_421"], ["17_444", "17_420"], ["17_446", "17_422"], ["17_447", "17_423"], ["17_448", "17_424"], ["17_449", "17_425"], ["17_450", "17_426"], ["17_451", "17_427"], ["17_452", "17_428"], ["17_453", "17_429"], ["17_75", "17_76"], ["17_76", "17_77"], ["17_77", "17_82"], ["17_17", "17_82"], ["17_82", "17_81"], ["17_84", "17_85"], ["17_85", "17_86"], ["17_86", "17_87"], ["17_87", "17_88"], ["17_88", "17_89"], ["17_89", "17_90"], ["17_90", "17_91"], ["17_81", "17_94"], ["17_91", "17_94"], ["17_94", "17_95"], ["17_95", "17_100"], ["17_100", "17_101"], ["17_101", "17_102"], ["17_104", "17_105"], ["17_105", "17_106"], ["17_106", "17_107"], ["17_102", "17_108"], ["17_107", "17_108"], ["17_265", "17_108"], ["17_266", "17_108"], ["17_267", "17_108"], ["17_268", "17_108"], ["17_269", "17_108"], ["17_270", "17_108"], ["17_271", "17_108"], ["17_272", "17_108"], ["17_273", "17_108"], ["17_274", "17_108"], ["17_275", "17_108"], ["17_276", "17_108"], ["17_277", "17_108"], ["17_278", "17_108"], ["17_279", "17_108"], ["17_280", "17_108"], ["17_281", "17_108"], ["17_282", "17_108"], ["17_283", "17_108"], ["17_284", "17_108"], ["17_285", "17_108"], ["17_286", "17_108"], ["17_287", "17_108"], ["17_288", "17_108"], ["17_108", "17_109"], ["17_109", "17_110"], ["17_110", "17_111"], ["17_111", "17_112"], ["17_128", "17_129"], ["17_129", "17_131"], ["17_130", "17_131"], ["17_133", "17_134"], ["17_136", "17_193"], ["17_137", "17_138"], ["17_193", "17_138"], ["17_138", "17_139"], ["17_139", "17_140"], ["17_140", "17_141"], ["17_141", "17_194"], ["17_126", "17_149"], ["17_131", "17_149"], ["17_134", "17_149"], ["17_149", "17_150"], ["17_138", "17_150"], ["17_150", "17_195"], ["17_195", "17_151"], ["17_95", "17_152"], ["17_151", "17_152"], ["17_152", "17_153"], ["17_153", "17_154"], ["17_194", "17_154"], ["17_156", "17_157"], ["17_151", "17_157"], ["17_157", "17_158"]], "pareto_nsga2": {"options": [{"cost": 214713039.6, "risk": 17.355099999999993, "modes": [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0], "makespan": 9151.199999999999}, {"cost": 222523581.35, "risk": 17.263299999999987, "modes": [0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 2, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 2, 1, 0, 1, 0, 1, 0, 0, 0, 0], "makespan": 9216.0}, {"cost": 217500305.35, "risk": 17.255999999999986, "modes": [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0], "makespan": 9230.4}, {"cost": 226085322.6, "risk": 17.20389999999999, "modes": [0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 2, 1, 0, 0, 1, 0, 0, 2, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 2, 1, 0, 0, 1, 0, 0, 0, 0, 0], "makespan": 9283.199999999999}], "selected": {"cost": 214713039.6, "risk": 17.355099999999993, "modes": [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0], "makespan": 9151.199999999999}, "solutions_found": 40}, "ppo_schedule": {"tgc": 0.0, "modes": [2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 1, 2, 0, 0, 2, 0, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 0, 2, 2, 1, 2, 2, 1, 2, 2, 2, 1, 1, 0, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 0, 0, 0, 1, 2, 2, 2, 2, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2], "reward": -25924.785785970475, "makespan": 686.057861328125}, "tasks_metadata": [{"id": "17_305", "name": "Installation of the jacket foundations 17", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_306", "name": "Installation of the jacket foundations 18", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_307", "name": "Installation of the jacket foundations 19", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_308", "name": "Installation of the jacket foundations 20", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_309", "name": "Installation of the jacket foundations 21", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_31", "name": "Transport (Hoboken to Vlissingen) 1", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_310", "name": "Installation of the jacket foundations 22", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_311", "name": "Installation of the jacket foundations 23", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_312", "name": "Installation of the jacket foundations 24", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_313", "name": "Transport of the jacket foundations 1", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_314", "name": "Transport of the jacket foundations 2", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_315", "name": "Transport of the jacket foundations 3", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_316", "name": "Transport of the jacket foundations 4", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_317", "name": "Transport of the jacket foundations 5", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_318", "name": "Transport of the jacket foundations 6", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_319", "name": "Transport of the jacket foundations 7", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_320", "name": "Transport of the jacket foundations 8", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_321", "name": "Transport of the jacket foundations 9", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_322", "name": "Transport of the jacket foundations 10", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_323", "name": "Transport of the jacket foundations 11", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_324", "name": "Transport of the jacket foundations 12", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_325", "name": "Transport of the jacket foundations 13", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_326", "name": "Transport of the jacket foundations 14", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_327", "name": "Transport of the jacket foundations 15", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_328", "name": "Transport of the jacket foundations 16", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_329", "name": "Transport of the jacket foundations 17", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_330", "name": "Transport of the jacket foundations 18", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_331", "name": "Transport of the jacket foundations 19", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_332", "name": "Transport of the jacket foundations 20", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_333", "name": "Transport of the jacket foundations 21", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_334", "name": "Transport of the jacket foundations 22", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_335", "name": "Transport of the jacket foundations 23", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_336", "name": "Transport of the jacket foundations 24", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 67200.0, "normal_cost": 44800.0, "outsource_cost": 89840.0, "most_probable_duration": 24.0}, {"id": "17_337", "name": "Assembly of midsection 2", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_1", "name": "Fabrication of pre-piling template", "resources": [], "crash_cost": 1566000.0, "normal_cost": 1044000.0, "outsource_cost": 2091600.0, "most_probable_duration": 360.0}, {"id": "17_100", "name": "Rock dumping as scour protection around the OTS foundation", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 361920.0, "normal_cost": 241280.0, "outsource_cost": 483040.0, "most_probable_duration": 48.0}, {"id": "17_101", "name": "GOSA mattresses installations above existing underground cables as protection", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 2171520.0, "normal_cost": 1447680.0, "outsource_cost": 2898240.0, "most_probable_duration": 288.0}, {"id": "17_102", "name": "Pre-grapnel run to remove obstacles from cable trajectories", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 3.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 354240.0, "normal_cost": 236160.0, "outsource_cost": 472800.0, "most_probable_duration": 48.0}, {"id": "17_105", "name": "Transport", "resources": [{"quantity": 10.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "204"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1073700.0, "normal_cost": 715800.0, "outsource_cost": 1432800.0, "most_probable_duration": 120.0}, {"id": "17_106", "name": "Pre-grapnel runs to remove obstacles", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 3.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 189600.0, "normal_cost": 126400.0, "outsource_cost": 253040.0, "most_probable_duration": 24.0}, {"id": "17_107", "name": "Wet trials", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "197"}], "crash_cost": 87120.0, "normal_cost": 58080.0, "outsource_cost": 116400.0, "most_probable_duration": 24.0}, {"id": "17_108", "name": "Cable laying works", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "211"}], "crash_cost": 8570880.0, "normal_cost": 5713920.0, "outsource_cost": 11439360.0, "most_probable_duration": 1152.0}, {"id": "17_109", "name": "Final hang off of the cables in the WTG foundations", "resources": [{"quantity": 2.0, "resource_id": "194"}], "crash_cost": 1843200.0, "normal_cost": 1228800.0, "outsource_cost": 2469120.0, "most_probable_duration": 1152.0}, {"id": "17_11", "name": "Continious delivery of pin-piles", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 6000.0, "most_probable_duration": 600.0}, {"id": "17_110", "name": "Burial of cables", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "211"}], "crash_cost": 1939200.0, "normal_cost": 1292800.0, "outsource_cost": 2588000.0, "most_probable_duration": 240.0}, {"id": "17_111", "name": "Survey of burial depths", "resources": [{"quantity": 4.0, "resource_id": "193"}], "crash_cost": 30720.0, "normal_cost": 20480.0, "outsource_cost": 41440.0, "most_probable_duration": 48.0}, {"id": "17_112", "name": "Second remedial burial pass if necessary", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "211"}], "crash_cost": 775680.0, "normal_cost": 517120.0, "outsource_cost": 1035200.0, "most_probable_duration": 96.0}, {"id": "17_12", "name": "OTS: drive 4 pin-piles for OTS foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_126", "name": "Pre-lay grapnel run on trajectory", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 3.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 354240.0, "normal_cost": 236160.0, "outsource_cost": 472800.0, "most_probable_duration": 48.0}, {"id": "17_128", "name": "Purchase of raw materials", "resources": [], "crash_cost": 2205000.0, "normal_cost": 1470000.0, "outsource_cost": 2956800.0, "most_probable_duration": 1680.0}, {"id": "17_129", "name": "Manufacturing in Karlskrona Sweden", "resources": [], "crash_cost": 938400.0, "normal_cost": 625600.0, "outsource_cost": 1260800.0, "most_probable_duration": 960.0}, {"id": "17_13", "name": "Turbine1: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_130", "name": "Mobilisation of Stemat Spirit", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "203"}], "crash_cost": 816000.0, "normal_cost": 544000.0, "outsource_cost": 1089200.0, "most_probable_duration": 120.0}, {"id": "17_131", "name": "Transport Sweden-Ostend", "resources": [{"quantity": 6.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "203"}, {"quantity": 2.0, "resource_id": "199"}], "crash_cost": 752790.0, "normal_cost": 501860.0, "outsource_cost": 1004680.0, "most_probable_duration": 96.0}, {"id": "17_133", "name": "Dredging to widen shipping lane Vaargeul1", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "208"}], "crash_cost": 938400.0, "normal_cost": 625600.0, "outsource_cost": 1252400.0, "most_probable_duration": 120.0}, {"id": "17_134", "name": "Prepare trench where export cable B (150kV) is crossing Vaargeul1", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "208"}], "crash_cost": 1266900.0, "normal_cost": 844600.0, "outsource_cost": 1690400.0, "most_probable_duration": 120.0}, {"id": "17_136", "name": "Delivery of pipes to be drilled", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 14400.0, "most_probable_duration": 1440.0}, {"id": "17_137", "name": "Directional drillings on land", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 2.0, "resource_id": "215"}], "crash_cost": 2523300.0, "normal_cost": 1682200.0, "outsource_cost": 3368000.0, "most_probable_duration": 360.0}, {"id": "17_138", "name": "Pulling welded pipe in through drilling hole", "resources": [{"quantity": 14.0, "resource_id": "217"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "216"}], "crash_cost": 273600.0, "normal_cost": 182400.0, "outsource_cost": 365520.0, "most_probable_duration": 72.0}, {"id": "17_139", "name": "Factory Acceptance Tests on land cables", "resources": [{"quantity": 1.0, "resource_id": "197"}], "crash_cost": 57150.0, "normal_cost": 38100.0, "outsource_cost": 76680.0, "most_probable_duration": 48.0}, {"id": "17_14", "name": "Turbine2: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_140", "name": "Cable laying onshore between export cable landing and Elia sub-station", "resources": [{"quantity": 13.0, "resource_id": "217"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "216"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 526500.0, "normal_cost": 351000.0, "outsource_cost": 703200.0, "most_probable_duration": 120.0}, {"id": "17_141", "name": "Connection of the cables into Elia sub-station", "resources": [{"quantity": 1.0, "resource_id": "195"}], "crash_cost": 120300.0, "normal_cost": 80200.0, "outsource_cost": 160880.0, "most_probable_duration": 48.0}, {"id": "17_149", "name": "Export cable laying on sea bed between coast and OTS", "resources": [{"quantity": 17.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "207"}], "crash_cost": 1867200.0, "normal_cost": 1244800.0, "outsource_cost": 2492000.0, "most_probable_duration": 240.0}, {"id": "17_150", "name": "Landfall cable pull", "resources": [{"quantity": 13.0, "resource_id": "217"}, {"quantity": 3.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "216"}], "crash_cost": 86400.0, "normal_cost": 57600.0, "outsource_cost": 115440.0, "most_probable_duration": 24.0}, {"id": "17_151", "name": "Backfilling of cable trench", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "209"}], "crash_cost": 721500.0, "normal_cost": 481000.0, "outsource_cost": 962720.0, "most_probable_duration": 72.0}, {"id": "17_152", "name": "Export cable pull in OTS", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 6.0, "resource_id": "193"}], "crash_cost": 60990.0, "normal_cost": 40660.0, "outsource_cost": 81560.0, "most_probable_duration": 24.0}, {"id": "17_153", "name": "Complete connection of cable conductors and fibre optics", "resources": [{"quantity": 1.0, "resource_id": "195"}], "crash_cost": 57150.0, "normal_cost": 38100.0, "outsource_cost": 76680.0, "most_probable_duration": 48.0}, {"id": "17_156", "name": "Delivery of rock on Halve Maan site", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 240.0, "most_probable_duration": 24.0}, {"id": "17_157", "name": "Mobilizing rock dumping vessel", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 165600.0, "normal_cost": 110400.0, "outsource_cost": 221040.0, "most_probable_duration": 24.0}, {"id": "17_158", "name": "Rock dumping on PEC crossing and Interconnector South", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 165600.0, "normal_cost": 110400.0, "outsource_cost": 221040.0, "most_probable_duration": 24.0}, {"id": "17_16", "name": "Dredging and cleaning of pin-piles", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 201120.0, "normal_cost": 134080.0, "outsource_cost": 268400.0, "most_probable_duration": 24.0}, {"id": "17_17", "name": "Install pin-pile covers on the piles", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 197280.0, "normal_cost": 131520.0, "outsource_cost": 263280.0, "most_probable_duration": 24.0}, {"id": "17_193", "name": "Welding pipes together", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 8.0, "resource_id": "192"}, {"quantity": 1.0, "resource_id": "199"}, {"quantity": 1.0, "resource_id": "193"}], "crash_cost": 389400.0, "normal_cost": 259600.0, "outsource_cost": 520400.0, "most_probable_duration": 120.0}, {"id": "17_194", "name": "Electrical commissioning tests on the onshore cable connections", "resources": [{"quantity": 1.0, "resource_id": "197"}], "crash_cost": 101100.0, "normal_cost": 67400.0, "outsource_cost": 135040.0, "most_probable_duration": 24.0}, {"id": "17_195", "name": "Making joint between sea cable and land cable", "resources": [{"quantity": 1.0, "resource_id": "195"}], "crash_cost": 37950.0, "normal_cost": 25300.0, "outsource_cost": 50840.0, "most_probable_duration": 24.0}, {"id": "17_196", "name": "Turbine3: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_197", "name": "Turbine4: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_198", "name": "Turbine5: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_199", "name": "Turbine6: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_2", "name": "Transportation of template and mounting on Jack Up Platform Buzzard", "resources": [], "crash_cost": 0.0, "normal_cost": 0.0, "outsource_cost": 2400.0, "most_probable_duration": 240.0}, {"id": "17_200", "name": "Turbine7: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_201", "name": "Turbine8: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_202", "name": "Turbine9: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_203", "name": "Turbine10: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_204", "name": "Turbine11: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_205", "name": "Turbine12: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_206", "name": "Turbine13: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_207", "name": "Turbine14: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_208", "name": "Turbine15: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_209", "name": "Turbine16: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_210", "name": "Turbine17: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_211", "name": "Turbine18: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_212", "name": "Turbine19: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_213", "name": "Turbine20: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_214", "name": "Turbine21: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_215", "name": "Turbine22: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_216", "name": "Turbine23: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_217", "name": "Turbine24: drive 4 pin-piles for jacket foundation into seabed", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 398400.0, "normal_cost": 265600.0, "outsource_cost": 531680.0, "most_probable_duration": 48.0}, {"id": "17_218", "name": "Dredging and cleaning of pin-piles 2", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_219", "name": "Dredging and cleaning of pin-piles 3", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_220", "name": "Dredging and cleaning of pin-piles 4", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_221", "name": "Dredging and cleaning of pin-piles 5", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_222", "name": "Dredging and cleaning of pin-piles 6", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_223", "name": "Dredging and cleaning of pin-piles 7", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_224", "name": "Dredging and cleaning of pin-piles 8", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_225", "name": "Dredging and cleaning of pin-piles 9", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_226", "name": "Dredging and cleaning of pin-piles 10", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_227", "name": "Dredging and cleaning of pin-piles 11", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_228", "name": "Dredging and cleaning of pin-piles 12", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_229", "name": "Dredging and cleaning of pin-piles 13", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_23", "name": "Purchase of castings and pile stoppers", "resources": [], "crash_cost": 225000.0, "normal_cost": 150000.0, "outsource_cost": 328800.0, "most_probable_duration": 2880.0}, {"id": "17_230", "name": "Dredging and cleaning of pin-piles 14", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_231", "name": "Dredging and cleaning of pin-piles 15", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_232", "name": "Dredging and cleaning of pin-piles 16", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_233", "name": "Dredging and cleaning of pin-piles 17", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_234", "name": "Dredging and cleaning of pin-piles 18", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_235", "name": "Dredging and cleaning of pin-piles 19", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_236", "name": "Dredging and cleaning of pin-piles 20", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_237", "name": "Dredging and cleaning of pin-piles 21", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_238", "name": "Dredging and cleaning of pin-piles 22", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_239", "name": "Dredging and cleaning of pin-piles 23", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_240", "name": "Dredging and cleaning of pin-piles 24", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_241", "name": "Install pin-pile covers on the piles 1", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_242", "name": "Install pin-pile covers on the piles 2", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_243", "name": "Install pin-pile covers on the piles 3", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_244", "name": "Install pin-pile covers on the piles 4", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_245", "name": "Install pin-pile covers on the piles 5", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_246", "name": "Install pin-pile covers on the piles 6", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_247", "name": "Install pin-pile covers on the piles 7", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_248", "name": "Install pin-pile covers on the piles 8", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_249", "name": "Install pin-pile covers on the piles 9", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_25", "name": "Assembly of midsection 1", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_250", "name": "Install pin-pile covers on the piles 10", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_251", "name": "Install pin-pile covers on the piles 11", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_252", "name": "Install pin-pile covers on the piles 12", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_253", "name": "Install pin-pile covers on the piles 13", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_254", "name": "Install pin-pile covers on the piles 14", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_255", "name": "Install pin-pile covers on the piles 15", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_256", "name": "Install pin-pile covers on the piles 16", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_257", "name": "Install pin-pile covers on the piles 17", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_258", "name": "Install pin-pile covers on the piles 18", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_259", "name": "Install pin-pile covers on the piles 19", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_260", "name": "Install pin-pile covers on the piles 20", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_261", "name": "Install pin-pile covers on the piles 21", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_262", "name": "Install pin-pile covers on the piles 22", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_263", "name": "Install pin-pile covers on the piles 23", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_264", "name": "Install pin-pile covers on the piles 24", "resources": [{"quantity": 20.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 276180.0, "normal_cost": 184120.0, "outsource_cost": 368480.0, "most_probable_duration": 24.0}, {"id": "17_266", "name": "Grouting of foundation to the pin-piles 2", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_267", "name": "Grouting of foundation to the pin-piles 3", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_268", "name": "Grouting of foundation to the pin-piles 4", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_269", "name": "Grouting of foundation to the pin-piles 5", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_270", "name": "Grouting of foundation to the pin-piles 6", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_271", "name": "Grouting of foundation to the pin-piles 7", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_272", "name": "Grouting of foundation to the pin-piles 8", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_273", "name": "Grouting of foundation to the pin-piles 9", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_274", "name": "Grouting of foundation to the pin-piles 10", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_275", "name": "Grouting of foundation to the pin-piles 11", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_276", "name": "Grouting of foundation to the pin-piles 12", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_277", "name": "Grouting of foundation to the pin-piles 13", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_278", "name": "Grouting of foundation to the pin-piles 14", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_279", "name": "Grouting of foundation to the pin-piles 15", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_281", "name": "Grouting of foundation to the pin-piles 17", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_282", "name": "Grouting of foundation to the pin-piles 18", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_283", "name": "Grouting of foundation to the pin-piles 19", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_284", "name": "Grouting of foundation to the pin-piles 20", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_285", "name": "Grouting of foundation to the pin-piles 21", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_286", "name": "Grouting of foundation to the pin-piles 22", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_287", "name": "Grouting of foundation to the pin-piles 23", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_288", "name": "Grouting of foundation to the pin-piles 24", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_29", "name": "Final jacket assembly 1", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_290", "name": "Installation of the jacket foundations 2", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_291", "name": "Installation of the jacket foundations 3", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_292", "name": "Installation of the jacket foundations 4", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_293", "name": "Installation of the jacket foundations 5", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_294", "name": "Installation of the jacket foundations 6", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_295", "name": "Installation of the jacket foundations 7", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_296", "name": "Installation of the jacket foundations 8", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_297", "name": "Installation of the jacket foundations 9", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_298", "name": "Installation of the jacket foundations 10", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_299", "name": "Installation of the jacket foundations 11", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_3", "name": "Mobilisation of Jack Up Platform Buzzard", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 3.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "206"}], "crash_cost": 171360.0, "normal_cost": 114240.0, "outsource_cost": 228720.0, "most_probable_duration": 24.0}, {"id": "17_300", "name": "Installation of the jacket foundations 12", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_301", "name": "Installation of the jacket foundations 13", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_542", "name": "Delivery of pin-piles 16", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_162", "name": "Dredging and cleaning of pin-piles 1", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 229470.0, "normal_cost": 152980.0, "outsource_cost": 306200.0, "most_probable_duration": 24.0}, {"id": "17_21", "name": "Purshase of tubulars", "resources": [], "crash_cost": 120000.0, "normal_cost": 80000.0, "outsource_cost": 188800.0, "most_probable_duration": 2880.0}, {"id": "17_27", "name": "Purchase of secondary steel items", "resources": [], "crash_cost": 525000.0, "normal_cost": 350000.0, "outsource_cost": 719200.0, "most_probable_duration": 1920.0}, {"id": "17_289", "name": "Installation of the jacket foundations 1", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_265", "name": "Grouting of foundation to the pin-piles 1", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_280", "name": "Grouting of foundation to the pin-piles 16", "resources": [{"quantity": 12.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "198"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 378360.0, "normal_cost": 252240.0, "outsource_cost": 504720.0, "most_probable_duration": 24.0}, {"id": "17_454", "name": "Terminations of infield cables 1", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_430", "name": "Commissioning of wind turbines 1", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_406", "name": "Reliability tests 1", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_104", "name": "Production in Karlskrona Sweden", "resources": [], "crash_cost": 3307500.0, "normal_cost": 2205000.0, "outsource_cost": 4438800.0, "most_probable_duration": 2880.0}, {"id": "17_154", "name": "Testing 24 hours connection of cable conductors and fibre optics", "resources": [{"quantity": 1.0, "resource_id": "197"}], "crash_cost": 71100.0, "normal_cost": 47400.0, "outsource_cost": 95040.0, "most_probable_duration": 24.0}, {"id": "17_302", "name": "Installation of the jacket foundations 14", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_303", "name": "Installation of the jacket foundations 15", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_304", "name": "Installation of the jacket foundations 16", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 219360.0, "normal_cost": 146240.0, "outsource_cost": 292720.0, "most_probable_duration": 24.0}, {"id": "17_338", "name": "Assembly of midsection 3", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_339", "name": "Assembly of midsection 4", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_340", "name": "Assembly of midsection 5", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_341", "name": "Assembly of midsection 6", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_342", "name": "Assembly of midsection 7", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_343", "name": "Assembly of midsection 8", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_344", "name": "Assembly of midsection 9", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_345", "name": "Assembly of midsection 10", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_346", "name": "Assembly of midsection 11", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_347", "name": "Assembly of midsection 12", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_348", "name": "Assembly of midsection 13", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_349", "name": "Assembly of midsection 14", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_350", "name": "Assembly of midsection 15", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_351", "name": "Assembly of midsection 16", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_352", "name": "Assembly of midsection 17", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_353", "name": "Assembly of midsection 18", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_354", "name": "Assembly of midsection 19", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_355", "name": "Assembly of midsection 20", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_356", "name": "Assembly of midsection 21", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_357", "name": "Assembly of midsection 22", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_358", "name": "Assembly of midsection 23", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_359", "name": "Assembly of midsection 24", "resources": [], "crash_cost": 82650.0, "normal_cost": 55100.0, "outsource_cost": 112360.0, "most_probable_duration": 216.0}, {"id": "17_360", "name": "Final jacket assembly 2", "resources": [], "crash_cost": 61116.0, "normal_cost": 40744.0, "outsource_cost": 83648.0, "most_probable_duration": 216.0}, {"id": "17_361", "name": "Final jacket assembly 3", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_362", "name": "Final jacket assembly 4", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_363", "name": "Final jacket assembly 5", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_364", "name": "Final jacket assembly 6", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_365", "name": "Final jacket assembly 7", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_366", "name": "Final jacket assembly 8", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_367", "name": "Final jacket assembly 9", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_368", "name": "Final jacket assembly 10", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_369", "name": "Final jacket assembly 11", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_370", "name": "Final jacket assembly 12", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_371", "name": "Final jacket assembly 13", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_372", "name": "Final jacket assembly 14", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_373", "name": "Final jacket assembly 15", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_374", "name": "Final jacket assembly 16", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_375", "name": "Final jacket assembly 17", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_376", "name": "Final jacket assembly 18", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_377", "name": "Final jacket assembly 19", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_378", "name": "Final jacket assembly 20", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_379", "name": "Final jacket assembly 21", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_380", "name": "Final jacket assembly 22", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_381", "name": "Final jacket assembly 23", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_382", "name": "Final jacket assembly 24", "resources": [], "crash_cost": 60900.0, "normal_cost": 40600.0, "outsource_cost": 83360.0, "most_probable_duration": 216.0}, {"id": "17_383", "name": "Transport (Hoboken to Vlissingen) 2", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_384", "name": "Transport (Hoboken to Vlissingen) 3", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_385", "name": "Transport (Hoboken to Vlissingen) 4", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_386", "name": "Transport (Hoboken to Vlissingen) 5", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_387", "name": "Transport (Hoboken to Vlissingen) 6", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_388", "name": "Transport (Hoboken to Vlissingen) 7", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_389", "name": "Transport (Hoboken to Vlissingen) 8", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_390", "name": "Transport (Hoboken to Vlissingen) 9", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_391", "name": "Transport (Hoboken to Vlissingen) 10", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_392", "name": "Transport (Hoboken to Vlissingen) 11", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_393", "name": "Transport (Hoboken to Vlissingen) 12", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_394", "name": "Transport (Hoboken to Vlissingen) 13", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_395", "name": "Transport (Hoboken to Vlissingen) 14", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_396", "name": "Transport (Hoboken to Vlissingen) 15", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_397", "name": "Transport (Hoboken to Vlissingen) 16", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_398", "name": "Transport (Hoboken to Vlissingen) 17", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_399", "name": "Transport (Hoboken to Vlissingen) 18", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_400", "name": "Transport (Hoboken to Vlissingen) 19", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_401", "name": "Transport (Hoboken to Vlissingen) 20", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_402", "name": "Transport (Hoboken to Vlissingen) 21", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_403", "name": "Transport (Hoboken to Vlissingen) 22", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_404", "name": "Transport (Hoboken to Vlissingen) 23", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_405", "name": "Transport (Hoboken to Vlissingen) 24", "resources": [], "crash_cost": 21750.0, "normal_cost": 14500.0, "outsource_cost": 29240.0, "most_probable_duration": 24.0}, {"id": "17_407", "name": "Reliability tests 2", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_408", "name": "Reliability tests 3", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_409", "name": "Reliability tests 4", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_410", "name": "Reliability tests 5", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_411", "name": "Reliability tests 6", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_412", "name": "Reliability tests 7", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_413", "name": "Reliability tests 8", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_414", "name": "Reliability tests 9", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_415", "name": "Reliability tests 10", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_416", "name": "Reliability tests 11", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_417", "name": "Reliability tests 12", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_418", "name": "Reliability tests 13", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_419", "name": "Reliability tests 14", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_420", "name": "Reliability tests 16", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_421", "name": "Reliability tests 15", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_422", "name": "Reliability tests 17", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_423", "name": "Reliability tests 18", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_424", "name": "Reliability tests 19", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_425", "name": "Reliability tests 20", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_426", "name": "Reliability tests 21", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_427", "name": "Reliability tests 22", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_428", "name": "Reliability tests 23", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_429", "name": "Reliability tests 24", "resources": [{"quantity": 0.2, "resource_id": "197"}], "crash_cost": 19200.0, "normal_cost": 12800.0, "outsource_cost": 26800.0, "most_probable_duration": 120.0}, {"id": "17_431", "name": "Commissioning of wind turbines 2", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_432", "name": "Commissioning of wind turbines 3", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_433", "name": "Commissioning of wind turbines 4", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_434", "name": "Commissioning of wind turbines 5", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_435", "name": "Commissioning of wind turbines 6", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_436", "name": "Commissioning of wind turbines 7", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_437", "name": "Commissioning of wind turbines 8", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_438", "name": "Commissioning of wind turbines 9", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_439", "name": "Commissioning of wind turbines 10", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_440", "name": "Commissioning of wind turbines 11", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_441", "name": "Commissioning of wind turbines 12", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_442", "name": "Commissioning of wind turbines 13", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_443", "name": "Commissioning of wind turbines 14", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_444", "name": "Commissioning of wind turbines 15", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_445", "name": "Commissioning of wind turbines 16", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_446", "name": "Commissioning of wind turbines 17", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_447", "name": "Commissioning of wind turbines 18", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_448", "name": "Commissioning of wind turbines 19", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_449", "name": "Commissioning of wind turbines 20", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_450", "name": "Commissioning of wind turbines 21", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_451", "name": "Commissioning of wind turbines 22", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_452", "name": "Commissioning of wind turbines 23", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_453", "name": "Commissioning of wind turbines 24", "resources": [{"quantity": 1.0, "resource_id": "196"}], "crash_cost": 96000.0, "normal_cost": 64000.0, "outsource_cost": 129200.0, "most_probable_duration": 120.0}, {"id": "17_455", "name": "Terminations of infield cables 2", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_456", "name": "Terminations of infield cables 3", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_457", "name": "Terminations of infield cables 4", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_458", "name": "Terminations of infield cables 5", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_459", "name": "Terminations of infield cables 6", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_46", "name": "Towers by AMAU-Cuxhaven Germany", "resources": [], "crash_cost": 21600000.0, "normal_cost": 14400000.0, "outsource_cost": 28857600.0, "most_probable_duration": 5760.0}, {"id": "17_460", "name": "Terminations of infield cables 7", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_461", "name": "Terminations of infield cables 8", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_462", "name": "Terminations of infield cables 9", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_463", "name": "Terminations of infield cables 10", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_464", "name": "Terminations of infield cables 11", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_465", "name": "Terminations of infield cables 12", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_466", "name": "Terminations of infield cables 13", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_467", "name": "Terminations of infield cables 14", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_468", "name": "Terminations of infield cables 15", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_469", "name": "Terminations of infield cables 16", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_47", "name": "Blades by LM Denmark", "resources": [], "crash_cost": 12960000.0, "normal_cost": 8640000.0, "outsource_cost": 17337600.0, "most_probable_duration": 5760.0}, {"id": "17_470", "name": "Terminations of infield cables 17", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_471", "name": "Terminations of infield cables 18", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_472", "name": "Terminations of infield cables 19", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_473", "name": "Terminations of infield cables 20", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_474", "name": "Terminations of infield cables 21", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_475", "name": "Terminations of infield cables 22", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_476", "name": "Terminations of infield cables 23", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_477", "name": "Terminations of infield cables 24", "resources": [{"quantity": 1.0, "resource_id": "194"}], "crash_cost": 57600.0, "normal_cost": 38400.0, "outsource_cost": 77520.0, "most_probable_duration": 72.0}, {"id": "17_478", "name": "Offshore assembly of wind turbines 1", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 698976.0, "normal_cost": 465984.0, "outsource_cost": 932208.0, "most_probable_duration": 24.0}, {"id": "17_479", "name": "Offshore assembly of wind turbines 2", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_48", "name": "Generators by VEM Germany", "resources": [], "crash_cost": 18144000.0, "normal_cost": 12096000.0, "outsource_cost": 24249600.0, "most_probable_duration": 5760.0}, {"id": "17_480", "name": "Offshore assembly of wind turbines 3", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_481", "name": "Offshore assembly of wind turbines 4", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_482", "name": "Offshore assembly of wind turbines 5", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_483", "name": "Offshore assembly of wind turbines 6", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_484", "name": "Offshore assembly of wind turbines 7", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_485", "name": "Offshore assembly of wind turbines 8", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_486", "name": "Offshore assembly of wind turbines 9", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_487", "name": "Offshore assembly of wind turbines 10", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_488", "name": "Offshore assembly of wind turbines 11", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_489", "name": "Offshore assembly of wind turbines 12", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_49", "name": "Gearboxes by WINERGY-Vörde Germany and Hansen Belgium", "resources": [], "crash_cost": 33696000.0, "normal_cost": 22464000.0, "outsource_cost": 44985600.0, "most_probable_duration": 5760.0}, {"id": "17_490", "name": "Offshore assembly of wind turbines 13", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_491", "name": "Offshore assembly of wind turbines 14", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_492", "name": "Offshore assembly of wind turbines 15", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_493", "name": "Offshore assembly of wind turbines 16", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_494", "name": "Offshore assembly of wind turbines 17", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_495", "name": "Offshore assembly of wind turbines 18", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_496", "name": "Offshore assembly of wind turbines 19", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_497", "name": "Offshore assembly of wind turbines 20", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_498", "name": "Offshore assembly of wind turbines 21", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_499", "name": "Offshore assembly of wind turbines 22", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_50", "name": "Gearboxes Germany-Ostend/Antwerp-Ostend", "resources": [], "crash_cost": 1540500.0, "normal_cost": 1027000.0, "outsource_cost": 2065520.0, "most_probable_duration": 1152.0}, {"id": "17_500", "name": "Offshore assembly of wind turbines 23", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_501", "name": "Offshore assembly of wind turbines 24", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}], "crash_cost": 381600.0, "normal_cost": 254400.0, "outsource_cost": 509040.0, "most_probable_duration": 24.0}, {"id": "17_502", "name": "Loading jack up transport and installation platform 1", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 2125800.0, "normal_cost": 1417200.0, "outsource_cost": 2835120.0, "most_probable_duration": 72.0}, {"id": "17_503", "name": "Loading jack up transport and installation platform 2", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_504", "name": "Loading jack up transport and installation platform 3", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_505", "name": "Loading jack up transport and installation platform 4", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_506", "name": "Loading jack up transport and installation platform 5", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_507", "name": "Loading jack up transport and installation platform 6", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_508", "name": "Loading jack up transport and installation platform 7", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_509", "name": "Loading jack up transport and installation platform 8", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_51", "name": "Generators Germany-Ostend", "resources": [], "crash_cost": 1540500.0, "normal_cost": 1027000.0, "outsource_cost": 2065520.0, "most_probable_duration": 1152.0}, {"id": "17_510", "name": "Loading jack up transport and installation platform 9", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_544", "name": "Delivery of pin-piles 18", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_511", "name": "Loading jack up transport and installation platform 10", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_512", "name": "Loading jack up transport and installation platform 11", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_513", "name": "Loading jack up transport and installation platform 12", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_514", "name": "Loading jack up transport and installation platform 13", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_515", "name": "Loading jack up transport and installation platform 14", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_516", "name": "Loading jack up transport and installation platform 15", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_517", "name": "Loading jack up transport and installation platform 16", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_518", "name": "Loading jack up transport and installation platform 17", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_519", "name": "Loading jack up transport and installation platform 18", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_52", "name": "Blades Denmark-Ostend", "resources": [], "crash_cost": 936000.0, "normal_cost": 624000.0, "outsource_cost": 1257410.0, "most_probable_duration": 941.0}, {"id": "17_520", "name": "Loading jack up transport and installation platform 19", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_521", "name": "Loading jack up transport and installation platform 20", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_522", "name": "Loading jack up transport and installation platform 21", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_523", "name": "Loading jack up transport and installation platform 22", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_524", "name": "Loading jack up transport and installation platform 23", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_525", "name": "Loading jack up transport and installation platform 24", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 2.0, "resource_id": "191"}, {"quantity": 8.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "201"}, {"quantity": 1.0, "resource_id": "202"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1173600.0, "normal_cost": 782400.0, "outsource_cost": 1565520.0, "most_probable_duration": 72.0}, {"id": "17_526", "name": "Delivery of pin-piles OTS", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_527", "name": "Delivery of pin-piles 1", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_528", "name": "Delivery of pin-piles 2", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_529", "name": "Delivery of pin-piles 3", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_53", "name": "Towers Germany-Ostend", "resources": [], "crash_cost": 936000.0, "normal_cost": 624000.0, "outsource_cost": 1259520.0, "most_probable_duration": 1152.0}, {"id": "17_530", "name": "Delivery of pin-piles 4", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_531", "name": "Delivery of pin-piles 5", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_532", "name": "Delivery of pin-piles 6", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_533", "name": "Delivery of pin-piles 7", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_534", "name": "Delivery of pin-piles 8", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_535", "name": "Delivery of pin-piles 9", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_536", "name": "Delivery of pin-piles 10", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_537", "name": "Delivery of pin-piles 11", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_538", "name": "Delivery of pin-piles 12", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_539", "name": "Delivery of pin-piles 13", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_540", "name": "Delivery of pin-piles 14", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_541", "name": "Delivery of pin-piles 15", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_543", "name": "Delivery of pin-piles 17", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_545", "name": "Delivery of pin-piles 19", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_546", "name": "Delivery of pin-piles 20", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_547", "name": "Delivery of pin-piles 21", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_548", "name": "Delivery of pin-piles 22", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_549", "name": "Delivery of pin-piles 23", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_550", "name": "Delivery of pin-piles 24", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 0.5, "resource_id": "191"}, {"quantity": 0.5, "resource_id": "210"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 34320.0, "normal_cost": 22880.0, "outsource_cost": 46000.0, "most_probable_duration": 24.0}, {"id": "17_551", "name": "Purchasing of pin-piles", "resources": [], "crash_cost": 9396000.0, "normal_cost": 6264000.0, "outsource_cost": 12540000.0, "most_probable_duration": 1200.0}, {"id": "17_56", "name": "Preparation of the onshore site", "resources": [{"quantity": 32.0, "resource_id": "217"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 3.0, "resource_id": "199"}], "crash_cost": 2476800.0, "normal_cost": 1651200.0, "outsource_cost": 3309600.0, "most_probable_duration": 720.0}, {"id": "17_57", "name": "Assembly of gearbox and generator", "resources": [{"quantity": 16.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "192"}, {"quantity": 3.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1820160.0, "normal_cost": 1213440.0, "outsource_cost": 2438400.0, "most_probable_duration": 1152.0}, {"id": "17_58", "name": "Assembly of blades", "resources": [{"quantity": 19.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "192"}, {"quantity": 3.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 1958400.0, "normal_cost": 1305600.0, "outsource_cost": 2622720.0, "most_probable_duration": 1152.0}, {"id": "17_6", "name": "Mobilisation of vessels", "resources": [{"quantity": 5.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 2484000.0, "normal_cost": 1656000.0, "outsource_cost": 3315600.0, "most_probable_duration": 360.0}, {"id": "17_7", "name": "Seabed preparations", "resources": [{"quantity": 22.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "200"}], "crash_cost": 5124000.0, "normal_cost": 3416000.0, "outsource_cost": 6838000.0, "most_probable_duration": 600.0}, {"id": "17_75", "name": "Purchase of base materials", "resources": [], "crash_cost": 264000.0, "normal_cost": 176000.0, "outsource_cost": 361600.0, "most_probable_duration": 960.0}, {"id": "17_76", "name": "Construction of jacket foundation for OTS", "resources": [], "crash_cost": 417000.0, "normal_cost": 278000.0, "outsource_cost": 558400.0, "most_probable_duration": 240.0}, {"id": "17_77", "name": "Transport of jacket foundation to Ostend", "resources": [{"quantity": 8.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 119040.0, "normal_cost": 79360.0, "outsource_cost": 159200.0, "most_probable_duration": 48.0}, {"id": "17_81", "name": "Installation of jacket foundation of OTS", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 215520.0, "normal_cost": 143680.0, "outsource_cost": 287600.0, "most_probable_duration": 24.0}, {"id": "17_82", "name": "Transport of jacket foundation in sea", "resources": [{"quantity": 8.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 4.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 74880.0, "normal_cost": 49920.0, "outsource_cost": 100080.0, "most_probable_duration": 24.0}, {"id": "17_84", "name": "Purchase of base materials", "resources": [], "crash_cost": 4567500.0, "normal_cost": 3045000.0, "outsource_cost": 6126000.0, "most_probable_duration": 3600.0}, {"id": "17_85", "name": "Erection of 1st main deck section", "resources": [], "crash_cost": 1044000.0, "normal_cost": 696000.0, "outsource_cost": 1399200.0, "most_probable_duration": 720.0}, {"id": "17_86", "name": "Erection of 2st main deck section", "resources": [], "crash_cost": 1044000.0, "normal_cost": 696000.0, "outsource_cost": 1399200.0, "most_probable_duration": 720.0}, {"id": "17_87", "name": "Erection of mezzanine deck", "resources": [], "crash_cost": 981000.0, "normal_cost": 654000.0, "outsource_cost": 1311840.0, "most_probable_duration": 384.0}, {"id": "17_88", "name": "Construction of roof deck", "resources": [], "crash_cost": 1044000.0, "normal_cost": 696000.0, "outsource_cost": 1395840.0, "most_probable_duration": 384.0}, {"id": "17_89", "name": "Internal finishings", "resources": [], "crash_cost": 307500.0, "normal_cost": 205000.0, "outsource_cost": 410490.0, "most_probable_duration": 49.0}, {"id": "17_90", "name": "Installation of transformer equipment", "resources": [], "crash_cost": 1296000.0, "normal_cost": 864000.0, "outsource_cost": 1742400.0, "most_probable_duration": 1440.0}, {"id": "17_91", "name": "Preparation for upcoming transport", "resources": [], "crash_cost": 184500.0, "normal_cost": 123000.0, "outsource_cost": 248400.0, "most_probable_duration": 240.0}, {"id": "17_94", "name": "Transport of OTS", "resources": [{"quantity": 4.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 1.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "213"}, {"quantity": 1.0, "resource_id": "214"}, {"quantity": 1.0, "resource_id": "199"}], "crash_cost": 59520.0, "normal_cost": 39680.0, "outsource_cost": 79600.0, "most_probable_duration": 24.0}, {"id": "17_95", "name": "Installation of OTS foundation", "resources": [{"quantity": 18.0, "resource_id": "217"}, {"quantity": 1.0, "resource_id": "191"}, {"quantity": 6.0, "resource_id": "193"}, {"quantity": 1.0, "resource_id": "205"}], "crash_cost": 215520.0, "normal_cost": 143680.0, "outsource_cost": 287600.0, "most_probable_duration": 24.0}], "cp_sat_schedule": {"status": "INFEASIBLE", "makespan": 0, "schedule": {}}, "cpm_static_makespan": 11376.0, "project_state_evolution": {"state_history": [{"makespan": 11376.0, "state_id": 0, "timestamp": 1783755319.4944549, "total_cost": 133404804.0, "direct_cost": 133087404.0, "monte_carlo": {"P90": 11496.031837984181, "on_time_prob": 1.0, "mean_makespan": 11478.011236687526}, "critical_path": [], "indirect_cost": 317400.0, "action_applied": null, "resource_metrics": {"capacities": {"191": 1, "192": 1, "193": 1, "194": 1, "195": 1, "196": 1, "197": 1, "198": 1, "199": 1, "200": 1, "201": 1, "202": 1, "203": 1, "204": 1, "205": 1, "206": 1, "207": 1, "208": 1, "209": 1, "210": 1, "211": 1, "212": 1, "213": 1, "214": 1, "215": 1, "216": 1, "217": 1}, "total_demand": {"191": 268.0, "192": 10.0, "193": 1229.0, "194": 26.0, "195": 3.0, "196": 24.0, "197": 4.0, "198": 24.0, "199": 110.0, "200": 34.0, "201": 48.0, "202": 48.0, "203": 2.0, "204": 1.0, "205": 50.0, "206": 51.0, "207": 1.0, "208": 2.0, "209": 1.0, "210": 0.0, "211": 3.0, "213": 27.0, "214": 27.0, "215": 2.0, "216": 3.0, "217": 3809.0}, "utilization_rate": {"191": 268.0, "192": 10.0, "193": 1229.0, "194": 26.0, "195": 3.0, "196": 24.0, "197": 4.0, "198": 24.0, "199": 110.0, "200": 34.0, "201": 48.0, "202": 48.0, "203": 2.0, "204": 1.0, "205": 50.0, "206": 51.0, "207": 1.0, "208": 2.0, "209": 1.0, "210": 0.0, "211": 3.0, "212": 0.0, "213": 27.0, "214": 27.0, "215": 2.0, "216": 3.0, "217": 3809.0}}}, {"makespan": 8904.0, "state_id": 1, "timestamp": 1783755321.5081964, "total_cost": 142379604.0, "direct_cost": 142062204.0, "monte_carlo": {"P90": 9020.096546126637, "on_time_prob": 1.0, "mean_makespan": 9002.83749562166}, "critical_path": ["17_312", "17_336", "17_337", "17_108", "17_109", "17_110", "17_111", "17_112", "17_23", "17_25", "17_288", "17_21", "17_338", "17_339", "17_340", "17_341", "17_342", "17_343", "17_344", "17_345", "17_346", "17_347", "17_348", "17_349", "17_350", "17_351", "17_352", "17_353", "17_354", "17_355", "17_356", "17_357", "17_358", "17_359", "17_382", "17_405", "17_408", "17_410", "17_412", "17_413", "17_415", "17_417", "17_418", "17_420", "17_422", "17_425", "17_426", "17_428", "17_429", "17_432", "17_434", "17_436", "17_437", "17_439", "17_441", "17_442", "17_444", "17_446", "17_449", "17_450", "17_452", "17_453", "17_456", "17_458", "17_460", "17_461", "17_463", "17_465", "17_466", "17_468", "17_470", "17_473", "17_474", "17_476", "17_477"], "indirect_cost": 317400.0, "action_applied": {"priority": 1, "action_type": "Crash", "crash_level": 1.5, "custom_params": {"modes": [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0]}, "overlap_ratio": 0.3, "affected_tasks": ["17_306", "17_309", "17_312", "17_319", "17_323", "17_330", "17_333", "17_336", "17_108", "17_109", "17_13", "17_131", "17_136", "17_138", "17_139", "17_141", "17_157", "17_16", "17_200", "17_203", "17_214", "17_220", "17_227", "17_23", "17_235", "17_242", "17_25", "17_251", "17_259", "17_261", "17_278", "17_281", "17_288", "17_29", "17_291", "17_292", "17_294", "17_296", "17_298", "17_299", "17_21", "17_280", "17_454", "17_338", "17_342", "17_343", "17_347", "17_348", "17_351", "17_353", "17_356", "17_359", "17_361", "17_368", "17_369", "17_370", "17_373", "17_378", "17_380", "17_385", "17_394", "17_397", "17_400", "17_402", "17_404", "17_407", "17_419", "17_421", "17_433", "17_435", "17_438", "17_448", "17_451", "17_464", "17_471", "17_484", "17_496", "17_514", "17_517", "17_521", "17_526", "17_528", "17_529", "17_531", "17_533", "17_536", "17_539", "17_540", "17_546", "17_547", "17_56", "17_6", "17_84", "17_87"], "resource_delta": {}, "outsource_level": 2.0, "expected_cost_delta": 214713039.6, "expected_risk_delta": 17.355099999999993, "expected_duration_delta": 9151.199999999999}, "resource_metrics": {"capacities": {"191": 1, "192": 1, "193": 1, "194": 1, "195": 1, "196": 1, "197": 1, "198": 1, "199": 1, "200": 1, "201": 1, "202": 1, "203": 1, "204": 1, "205": 1, "206": 1, "207": 1, "208": 1, "209": 1, "210": 1, "211": 1, "212": 1, "213": 1, "214": 1, "215": 1, "216": 1, "217": 1}, "total_demand": {"191": 307.0, "192": 10.0, "193": 1329.0, "194": 30.0, "195": 4.0, "196": 29.0, "197": 5.0, "198": 28.0, "199": 130.0, "200": 40.0, "201": 53.0, "202": 53.0, "203": 3.0, "204": 1.0, "205": 63.0, "206": 59.0, "207": 1.0, "208": 2.0, "209": 1.0, "210": 0.0, "211": 4.0, "213": 32.0, "214": 32.0, "215": 2.0, "216": 4.0, "217": 4180.0}, "utilization_rate": {"191": 307.0, "192": 10.0, "193": 1329.0, "194": 30.0, "195": 4.0, "196": 29.0, "197": 5.0, "198": 28.0, "199": 130.0, "200": 40.0, "201": 53.0, "202": 53.0, "203": 3.0, "204": 1.0, "205": 63.0, "206": 59.0, "207": 1.0, "208": 2.0, "209": 1.0, "210": 0.0, "211": 4.0, "212": 0.0, "213": 32.0, "214": 32.0, "215": 2.0, "216": 4.0, "217": 4180.0}}}], "current_state_id": 1, "before_after_comparison": {"action_applied": {"priority": 1, "action_type": "Crash", "crash_level": 1.5, "custom_params": {"modes": [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0]}, "overlap_ratio": 0.3, "affected_tasks": ["17_306", "17_309", "17_312", "17_319", "17_323", "17_330", "17_333", "17_336", "17_108", "17_109", "17_13", "17_131", "17_136", "17_138", "17_139", "17_141", "17_157", "17_16", "17_200", "17_203", "17_214", "17_220", "17_227", "17_23", "17_235", "17_242", "17_25", "17_251", "17_259", "17_261", "17_278", "17_281", "17_288", "17_29", "17_291", "17_292", "17_294", "17_296", "17_298", "17_299", "17_21", "17_280", "17_454", "17_338", "17_342", "17_343", "17_347", "17_348", "17_351", "17_353", "17_356", "17_359", "17_361", "17_368", "17_369", "17_370", "17_373", "17_378", "17_380", "17_385", "17_394", "17_397", "17_400", "17_402", "17_404", "17_407", "17_419", "17_421", "17_433", "17_435", "17_438", "17_448", "17_451", "17_464", "17_471", "17_484", "17_496", "17_514", "17_517", "17_521", "17_526", "17_528", "17_529", "17_531", "17_533", "17_536", "17_539", "17_540", "17_546", "17_547", "17_56", "17_6", "17_84", "17_87"], "resource_delta": {}, "outsource_level": 2.0, "expected_cost_delta": 214713039.6, "expected_risk_delta": 17.355099999999993, "expected_duration_delta": 9151.199999999999}, "after_state_id": 1, "before_state_id": 0, "metrics_comparison": {"makespan": {"after": 8904.0, "delta": -2472.0, "before": 11376.0, "percent_change": -21.729957805907173}, "total_cost": {"after": 142379604.0, "delta": 8974800.0, "before": 133404804.0, "percent_change": 6.7274938614654385}, "P90_makespan": {"after": 9020.096546126637, "delta": -2475.935291857544, "before": 11496.031837984181}, "on_time_probability": {"after": 1.0, "delta": 0.0, "before": 1.0}}, "top_attention_shifts": [{"delta": -0.07073467969894409, "task_id": "17_11", "score_after": 0.5229721665382385, "score_before": 0.5937068462371826}, {"delta": -0.06001734733581543, "task_id": "17_131", "score_after": 0.5827372074127197, "score_before": 0.6427545547485352}, {"delta": -0.053799211978912354, "task_id": "17_105", "score_after": 0.5253602862358093, "score_before": 0.5791594982147217}, {"delta": 0.044888854026794434, "task_id": "17_108", "score_after": 0.5741064548492432, "score_before": 0.5292176008224487}, {"delta": 0.03443032503128052, "task_id": "17_382", "score_after": 0.6278803944587708, "score_before": 0.5934500694274902}], "critical_path_evolution": {"after_count": 75, "before_count": 0, "newly_critical_tasks": ["17_417", "17_426", "17_453", "17_452", "17_21", "17_348", "17_449", "17_413", "17_429", "17_460", "17_339", "17_337", "17_109", "17_353", "17_444", "17_340", "17_343", "17_351", "17_425", "17_441", "17_422", "17_474", "17_382", "17_112", "17_442", "17_439", "17_456", "17_352", "17_477", "17_357", "17_415", "17_418", "17_461", "17_345", "17_354", "17_312", "17_346", "17_470", "17_428", "17_466", "17_458", "17_108", "17_350", "17_410", "17_465", "17_23", "17_463", "17_355", "17_338", "17_405", "17_432", "17_408", "17_344", "17_468", "17_358", "17_359", "17_436", "17_349", "17_434", "17_446", "17_341", "17_25", "17_412", "17_476", "17_110", "17_356", "17_111", "17_336", "17_288", "17_342", "17_437", "17_473", "17_420", "17_450", "17_347"], "no_longer_critical_tasks": []}, "resource_utilization_evolution": {"after": {"capacities": {"191": 1, "192": 1, "193": 1, "194": 1, "195": 1, "196": 1, "197": 1, "198": 1, "199": 1, "200": 1, "201": 1, "202": 1, "203": 1, "204": 1, "205": 1, "206": 1, "207": 1, "208": 1, "209": 1, "210": 1, "211": 1, "212": 1, "213": 1, "214": 1, "215": 1, "216": 1, "217": 1}, "total_demand": {"191": 307.0, "192": 10.0, "193": 1329.0, "194": 30.0, "195": 4.0, "196": 29.0, "197": 5.0, "198": 28.0, "199": 130.0, "200": 40.0, "201": 53.0, "202": 53.0, "203": 3.0, "204": 1.0, "205": 63.0, "206": 59.0, "207": 1.0, "208": 2.0, "209": 1.0, "210": 0.0, "211": 4.0, "213": 32.0, "214": 32.0, "215": 2.0, "216": 4.0, "217": 4180.0}, "utilization_rate": {"191": 307.0, "192": 10.0, "193": 1329.0, "194": 30.0, "195": 4.0, "196": 29.0, "197": 5.0, "198": 28.0, "199": 130.0, "200": 40.0, "201": 53.0, "202": 53.0, "203": 3.0, "204": 1.0, "205": 63.0, "206": 59.0, "207": 1.0, "208": 2.0, "209": 1.0, "210": 0.0, "211": 4.0, "212": 0.0, "213": 32.0, "214": 32.0, "215": 2.0, "216": 4.0, "217": 4180.0}}, "before": {"capacities": {"191": 1, "192": 1, "193": 1, "194": 1, "195": 1, "196": 1, "197": 1, "198": 1, "199": 1, "200": 1, "201": 1, "202": 1, "203": 1, "204": 1, "205": 1, "206": 1, "207": 1, "208": 1, "209": 1, "210": 1, "211": 1, "212": 1, "213": 1, "214": 1, "215": 1, "216": 1, "217": 1}, "total_demand": {"191": 268.0, "192": 10.0, "193": 1229.0, "194": 26.0, "195": 3.0, "196": 24.0, "197": 4.0, "198": 24.0, "199": 110.0, "200": 34.0, "201": 48.0, "202": 48.0, "203": 2.0, "204": 1.0, "205": 50.0, "206": 51.0, "207": 1.0, "208": 2.0, "209": 1.0, "210": 0.0, "211": 3.0, "213": 27.0, "214": 27.0, "215": 2.0, "216": 3.0, "217": 3809.0}, "utilization_rate": {"191": 268.0, "192": 10.0, "193": 1229.0, "194": 26.0, "195": 3.0, "196": 24.0, "197": 4.0, "198": 24.0, "199": 110.0, "200": 34.0, "201": 48.0, "202": 48.0, "203": 2.0, "204": 1.0, "205": 50.0, "206": 51.0, "207": 1.0, "208": 2.0, "209": 1.0, "210": 0.0, "211": 3.0, "212": 0.0, "213": 27.0, "214": 27.0, "215": 2.0, "216": 3.0, "217": 3809.0}}}}}}, "simulation_progress": "🎲 [BƯỚC 3] Monte Carlo Level 2 Simulation..."}	0	0	0.0000	2026-07-10 13:12:33.132678	2026-07-11 13:41:27.462687
\.


--
-- Data for Name: task_resources; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.task_resources (task_id, resource_id, request_quantity, allocated_quantity, labor_productivity, equipment_utilization, resource_substitutability) FROM stdin;
15_1	168	1.00	\N	\N	\N	\N
15_2	169	65.00	\N	\N	\N	\N
15_2	172	24.00	\N	\N	\N	\N
15_3	168	1.00	\N	\N	\N	\N
15_4	168	1.00	\N	\N	\N	\N
15_4	170	5.00	\N	\N	\N	\N
15_4	171	7.00	\N	\N	\N	\N
15_5	168	1.00	\N	\N	\N	\N
15_6	168	1.00	\N	\N	\N	\N
15_6	170	1.00	\N	\N	\N	\N
15_7	168	1.00	\N	\N	\N	\N
15_8	168	1.00	\N	\N	\N	\N
15_9	168	1.00	\N	\N	\N	\N
15_10	168	1.00	\N	\N	\N	\N
15_10	171	7.00	\N	\N	\N	\N
15_10	170	1.00	\N	\N	\N	\N
15_11	168	1.00	\N	\N	\N	\N
15_12	168	1.00	\N	\N	\N	\N
15_13	168	1.00	\N	\N	\N	\N
15_13	171	7.00	\N	\N	\N	\N
15_13	170	5.00	\N	\N	\N	\N
15_14	168	1.00	\N	\N	\N	\N
15_15	168	1.00	\N	\N	\N	\N
15_16	168	1.00	\N	\N	\N	\N
15_17	168	1.00	\N	\N	\N	\N
15_17	171	7.00	\N	\N	\N	\N
15_18	168	1.00	\N	\N	\N	\N
15_19	168	1.00	\N	\N	\N	\N
15_19	171	1.00	\N	\N	\N	\N
15_20	168	1.00	\N	\N	\N	\N
15_20	170	5.00	\N	\N	\N	\N
15_21	168	1.00	\N	\N	\N	\N
15_22	168	1.00	\N	\N	\N	\N
15_23	168	1.00	\N	\N	\N	\N
15_23	171	7.00	\N	\N	\N	\N
15_24	168	1.00	\N	\N	\N	\N
15_24	170	5.00	\N	\N	\N	\N
15_25	168	1.00	\N	\N	\N	\N
15_26	168	1.00	\N	\N	\N	\N
15_26	171	1.00	\N	\N	\N	\N
15_27	168	1.00	\N	\N	\N	\N
15_27	171	7.00	\N	\N	\N	\N
15_27	170	5.00	\N	\N	\N	\N
15_28	168	1.00	\N	\N	\N	\N
15_28	172	24.00	\N	\N	\N	\N
15_28	169	65.00	\N	\N	\N	\N
15_29	170	2.00	\N	\N	\N	\N
15_30	170	2.00	\N	\N	\N	\N
15_31	168	1.00	\N	\N	\N	\N
15_32	168	1.00	\N	\N	\N	\N
15_33	168	1.00	\N	\N	\N	\N
15_34	168	1.00	\N	\N	\N	\N
15_34	172	24.00	\N	\N	\N	\N
15_35	168	1.00	\N	\N	\N	\N
15_35	170	1.00	\N	\N	\N	\N
15_36	168	1.00	\N	\N	\N	\N
15_37	168	1.00	\N	\N	\N	\N
15_38	168	1.00	\N	\N	\N	\N
15_38	172	12.00	\N	\N	\N	\N
15_39	168	1.00	\N	\N	\N	\N
15_39	172	12.00	\N	\N	\N	\N
15_40	168	1.00	\N	\N	\N	\N
15_40	169	17.00	\N	\N	\N	\N
15_41	168	1.00	\N	\N	\N	\N
15_41	169	16.00	\N	\N	\N	\N
15_42	168	1.00	\N	\N	\N	\N
15_42	169	16.00	\N	\N	\N	\N
15_43	168	1.00	\N	\N	\N	\N
15_43	169	16.00	\N	\N	\N	\N
15_44	168	1.00	\N	\N	\N	\N
15_45	170	5.00	\N	\N	\N	\N
15_47	168	1.00	\N	\N	\N	\N
15_47	171	7.00	\N	\N	\N	\N
15_48	168	1.00	\N	\N	\N	\N
15_48	169	65.00	\N	\N	\N	\N
15_49	168	1.00	\N	\N	\N	\N
16_1	173	2.00	\N	\N	\N	\N
16_1	174	1.00	\N	\N	\N	\N
16_1	189	10000.00	\N	\N	\N	\N
16_2	173	4.00	\N	\N	\N	\N
16_2	174	3.00	\N	\N	\N	\N
16_2	176	1.00	\N	\N	\N	\N
16_3	173	3.00	\N	\N	\N	\N
16_3	175	1.00	\N	\N	\N	\N
16_3	176	1.00	\N	\N	\N	\N
16_3	174	1.00	\N	\N	\N	\N
16_4	173	2.00	\N	\N	\N	\N
16_4	174	1.00	\N	\N	\N	\N
16_4	182	1.00	\N	\N	\N	\N
16_5	173	3.00	\N	\N	\N	\N
16_5	174	1.00	\N	\N	\N	\N
16_6	173	2.00	\N	\N	\N	\N
16_6	174	1.00	\N	\N	\N	\N
16_6	189	30000.00	\N	\N	\N	\N
16_7	173	7.00	\N	\N	\N	\N
16_7	174	5.00	\N	\N	\N	\N
16_7	176	2.00	\N	\N	\N	\N
16_7	177	1.00	\N	\N	\N	\N
16_7	181	1.00	\N	\N	\N	\N
16_7	189	50000.00	\N	\N	\N	\N
16_8	173	4.00	\N	\N	\N	\N
16_8	174	2.00	\N	\N	\N	\N
16_8	179	1.00	\N	\N	\N	\N
16_8	183	1.00	\N	\N	\N	\N
16_9	173	3.00	\N	\N	\N	\N
16_9	174	1.00	\N	\N	\N	\N
16_9	175	1.00	\N	\N	\N	\N
16_9	176	1.00	\N	\N	\N	\N
16_14	173	3.00	\N	\N	\N	\N
16_14	174	1.00	\N	\N	\N	\N
16_14	182	1.00	\N	\N	\N	\N
16_14	189	3000.00	\N	\N	\N	\N
16_11	173	4.00	\N	\N	\N	\N
16_11	174	1.00	\N	\N	\N	\N
16_11	181	1.00	\N	\N	\N	\N
16_11	182	1.00	\N	\N	\N	\N
16_11	189	3000.00	\N	\N	\N	\N
16_19	173	10.00	\N	\N	\N	\N
16_19	174	6.00	\N	\N	\N	\N
16_19	176	2.00	\N	\N	\N	\N
16_19	177	1.00	\N	\N	\N	\N
16_19	181	1.00	\N	\N	\N	\N
16_19	189	55000.00	\N	\N	\N	\N
16_20	173	4.00	\N	\N	\N	\N
16_20	174	1.00	\N	\N	\N	\N
16_20	182	1.00	\N	\N	\N	\N
16_20	189	23000.00	\N	\N	\N	\N
16_17	173	9.00	\N	\N	\N	\N
16_17	179	2.00	\N	\N	\N	\N
16_17	174	6.00	\N	\N	\N	\N
16_17	177	1.00	\N	\N	\N	\N
16_22	173	4.00	\N	\N	\N	\N
16_22	174	1.00	\N	\N	\N	\N
16_22	182	1.00	\N	\N	\N	\N
16_22	179	1.00	\N	\N	\N	\N
16_22	189	1500.00	\N	\N	\N	\N
16_24	173	4.00	\N	\N	\N	\N
16_24	174	3.00	\N	\N	\N	\N
16_24	179	1.00	\N	\N	\N	\N
16_24	189	0.00	\N	\N	\N	\N
16_25	173	6.00	\N	\N	\N	\N
16_25	174	1.00	\N	\N	\N	\N
16_25	180	1.00	\N	\N	\N	\N
16_25	182	1.00	\N	\N	\N	\N
16_25	176	1.00	\N	\N	\N	\N
16_25	181	1.00	\N	\N	\N	\N
16_25	189	190000.00	\N	\N	\N	\N
16_27	173	4.00	\N	\N	\N	\N
16_27	174	1.00	\N	\N	\N	\N
16_27	181	1.00	\N	\N	\N	\N
16_27	182	1.00	\N	\N	\N	\N
16_27	189	100000.00	\N	\N	\N	\N
16_29	173	4.00	\N	\N	\N	\N
16_29	174	1.00	\N	\N	\N	\N
16_29	181	1.00	\N	\N	\N	\N
16_29	182	1.00	\N	\N	\N	\N
16_29	189	11000.00	\N	\N	\N	\N
16_31	173	4.00	\N	\N	\N	\N
16_31	174	1.00	\N	\N	\N	\N
16_31	181	1.00	\N	\N	\N	\N
16_31	182	1.00	\N	\N	\N	\N
16_31	189	81000.00	\N	\N	\N	\N
16_33	173	4.00	\N	\N	\N	\N
16_33	174	1.00	\N	\N	\N	\N
16_33	182	1.00	\N	\N	\N	\N
16_33	189	52000.00	\N	\N	\N	\N
16_34	173	5.00	\N	\N	\N	\N
16_34	174	1.00	\N	\N	\N	\N
16_34	181	1.00	\N	\N	\N	\N
16_34	182	1.00	\N	\N	\N	\N
16_34	189	23500.00	\N	\N	\N	\N
16_36	173	5.00	\N	\N	\N	\N
16_36	174	3.00	\N	\N	\N	\N
16_36	176	1.00	\N	\N	\N	\N
16_36	177	1.00	\N	\N	\N	\N
16_36	189	18000.00	\N	\N	\N	\N
16_41	173	3.00	\N	\N	\N	\N
16_41	174	2.00	\N	\N	\N	\N
16_41	184	1.00	\N	\N	\N	\N
16_42	173	3.00	\N	\N	\N	\N
16_42	174	1.00	\N	\N	\N	\N
16_42	176	1.00	\N	\N	\N	\N
16_42	175	1.00	\N	\N	\N	\N
16_38	173	10.00	\N	\N	\N	\N
16_38	174	6.00	\N	\N	\N	\N
16_38	176	2.00	\N	\N	\N	\N
16_38	177	1.00	\N	\N	\N	\N
16_38	181	1.00	\N	\N	\N	\N
16_38	189	68600.00	\N	\N	\N	\N
16_39	173	4.00	\N	\N	\N	\N
16_39	174	1.00	\N	\N	\N	\N
16_39	182	1.00	\N	\N	\N	\N
16_39	189	12600.00	\N	\N	\N	\N
16_63	173	2.00	\N	\N	\N	\N
16_63	174	1.00	\N	\N	\N	\N
16_63	182	1.00	\N	\N	\N	\N
16_63	189	6000.00	\N	\N	\N	\N
16_62	173	4.00	\N	\N	\N	\N
16_62	174	2.00	\N	\N	\N	\N
16_62	179	1.00	\N	\N	\N	\N
16_62	182	1.00	\N	\N	\N	\N
16_62	189	15000.00	\N	\N	\N	\N
16_66	173	5.00	\N	\N	\N	\N
16_66	182	1.00	\N	\N	\N	\N
16_66	174	1.00	\N	\N	\N	\N
16_66	181	1.00	\N	\N	\N	\N
16_66	189	88000.00	\N	\N	\N	\N
16_68	173	4.00	\N	\N	\N	\N
16_68	174	1.00	\N	\N	\N	\N
16_68	182	1.00	\N	\N	\N	\N
16_68	189	50000.00	\N	\N	\N	\N
16_69	173	5.00	\N	\N	\N	\N
16_69	174	1.00	\N	\N	\N	\N
16_69	182	1.00	\N	\N	\N	\N
16_69	189	8000.00	\N	\N	\N	\N
16_82	173	3.00	\N	\N	\N	\N
16_82	174	2.00	\N	\N	\N	\N
16_82	184	1.00	\N	\N	\N	\N
16_83	173	4.00	\N	\N	\N	\N
16_83	174	2.00	\N	\N	\N	\N
16_83	175	1.00	\N	\N	\N	\N
16_83	176	1.00	\N	\N	\N	\N
16_75	173	10.00	\N	\N	\N	\N
16_75	174	6.00	\N	\N	\N	\N
16_75	176	2.00	\N	\N	\N	\N
16_75	177	1.00	\N	\N	\N	\N
16_75	187	1.00	\N	\N	\N	\N
16_75	189	140000.00	\N	\N	\N	\N
16_73	173	3.00	\N	\N	\N	\N
16_73	179	1.00	\N	\N	\N	\N
16_73	177	1.00	\N	\N	\N	\N
16_73	187	1.00	\N	\N	\N	\N
16_73	189	1800.00	\N	\N	\N	\N
16_72	173	10.00	\N	\N	\N	\N
16_72	174	6.00	\N	\N	\N	\N
16_72	176	2.00	\N	\N	\N	\N
16_72	177	1.00	\N	\N	\N	\N
16_72	187	1.00	\N	\N	\N	\N
16_80	173	3.00	\N	\N	\N	\N
16_80	182	1.00	\N	\N	\N	\N
16_80	174	1.00	\N	\N	\N	\N
16_80	189	7000.00	\N	\N	\N	\N
16_78	173	4.00	\N	\N	\N	\N
16_78	174	2.00	\N	\N	\N	\N
16_78	179	1.00	\N	\N	\N	\N
16_78	182	1.00	\N	\N	\N	\N
16_78	189	20000.00	\N	\N	\N	\N
16_77	173	3.00	\N	\N	\N	\N
16_77	174	1.00	\N	\N	\N	\N
16_77	179	1.00	\N	\N	\N	\N
16_77	182	1.00	\N	\N	\N	\N
16_77	189	3600.00	\N	\N	\N	\N
16_48	173	3.00	\N	\N	\N	\N
16_48	174	2.00	\N	\N	\N	\N
16_48	184	1.00	\N	\N	\N	\N
16_49	173	3.00	\N	\N	\N	\N
16_49	174	1.00	\N	\N	\N	\N
16_49	176	1.00	\N	\N	\N	\N
16_49	175	1.00	\N	\N	\N	\N
16_46	173	10.00	\N	\N	\N	\N
16_46	174	6.00	\N	\N	\N	\N
16_46	176	2.00	\N	\N	\N	\N
16_46	177	1.00	\N	\N	\N	\N
16_46	187	1.00	\N	\N	\N	\N
16_46	189	32000.00	\N	\N	\N	\N
16_44	173	4.00	\N	\N	\N	\N
16_44	174	2.00	\N	\N	\N	\N
16_44	179	1.00	\N	\N	\N	\N
16_44	182	1.00	\N	\N	\N	\N
16_44	189	10000.00	\N	\N	\N	\N
16_58	173	3.00	\N	\N	\N	\N
16_58	174	2.00	\N	\N	\N	\N
16_58	184	1.00	\N	\N	\N	\N
16_59	173	4.00	\N	\N	\N	\N
16_59	175	1.00	\N	\N	\N	\N
16_59	174	2.00	\N	\N	\N	\N
16_59	176	1.00	\N	\N	\N	\N
16_52	173	3.00	\N	\N	\N	\N
16_52	179	1.00	\N	\N	\N	\N
16_52	177	1.00	\N	\N	\N	\N
16_52	187	1.00	\N	\N	\N	\N
16_52	189	15000.00	\N	\N	\N	\N
16_51	173	8.00	\N	\N	\N	\N
16_51	174	6.00	\N	\N	\N	\N
16_51	179	2.00	\N	\N	\N	\N
16_55	173	3.00	\N	\N	\N	\N
16_55	179	1.00	\N	\N	\N	\N
16_55	174	1.00	\N	\N	\N	\N
16_55	182	1.00	\N	\N	\N	\N
16_55	189	26000.00	\N	\N	\N	\N
16_56	173	4.00	\N	\N	\N	\N
16_56	174	2.00	\N	\N	\N	\N
16_56	179	1.00	\N	\N	\N	\N
16_56	182	1.00	\N	\N	\N	\N
16_56	189	10000.00	\N	\N	\N	\N
16_85	173	7.00	\N	\N	\N	\N
16_85	174	5.00	\N	\N	\N	\N
16_85	183	1.00	\N	\N	\N	\N
16_85	178	1.00	\N	\N	\N	\N
16_85	190	2500000.00	\N	\N	\N	\N
16_86	173	4.00	\N	\N	\N	\N
16_86	174	1.00	\N	\N	\N	\N
16_86	185	1.00	\N	\N	\N	\N
16_86	189	300000.00	\N	\N	\N	\N
16_87	173	5.00	\N	\N	\N	\N
16_87	174	2.00	\N	\N	\N	\N
16_87	176	2.00	\N	\N	\N	\N
16_87	186	1.00	\N	\N	\N	\N
16_87	189	15000.00	\N	\N	\N	\N
16_88	173	3.00	\N	\N	\N	\N
16_88	174	1.00	\N	\N	\N	\N
16_88	189	16500.00	\N	\N	\N	\N
16_89	173	2.00	\N	\N	\N	\N
16_89	174	1.00	\N	\N	\N	\N
16_89	188	1.00	\N	\N	\N	\N
16_89	189	80000.00	\N	\N	\N	\N
16_91	173	2.00	\N	\N	\N	\N
16_91	174	1.00	\N	\N	\N	\N
16_92	173	2.00	\N	\N	\N	\N
16_92	174	1.00	\N	\N	\N	\N
16_92	182	1.00	\N	\N	\N	\N
16_93	173	2.00	\N	\N	\N	\N
16_93	174	1.00	\N	\N	\N	\N
16_93	176	1.00	\N	\N	\N	\N
16_94	173	2.00	\N	\N	\N	\N
16_94	174	1.00	\N	\N	\N	\N
17_3	217	5.00	\N	\N	\N	\N
17_3	191	1.00	\N	\N	\N	\N
17_3	193	3.00	\N	\N	\N	\N
17_3	206	1.00	\N	\N	\N	\N
17_6	217	5.00	\N	\N	\N	\N
17_6	191	1.00	\N	\N	\N	\N
17_6	200	1.00	\N	\N	\N	\N
17_7	217	22.00	\N	\N	\N	\N
17_7	191	1.00	\N	\N	\N	\N
17_7	193	6.00	\N	\N	\N	\N
17_7	200	1.00	\N	\N	\N	\N
17_526	217	5.00	\N	\N	\N	\N
17_526	191	0.50	\N	\N	\N	\N
17_526	210	0.50	\N	\N	\N	\N
17_526	199	1.00	\N	\N	\N	\N
17_527	217	5.00	\N	\N	\N	\N
17_527	191	0.50	\N	\N	\N	\N
17_527	210	0.50	\N	\N	\N	\N
17_527	199	1.00	\N	\N	\N	\N
17_528	217	5.00	\N	\N	\N	\N
17_528	191	0.50	\N	\N	\N	\N
17_528	210	0.50	\N	\N	\N	\N
17_528	199	1.00	\N	\N	\N	\N
17_529	217	5.00	\N	\N	\N	\N
17_529	191	0.50	\N	\N	\N	\N
17_529	210	0.50	\N	\N	\N	\N
17_529	199	1.00	\N	\N	\N	\N
17_530	217	5.00	\N	\N	\N	\N
17_530	191	0.50	\N	\N	\N	\N
17_530	210	0.50	\N	\N	\N	\N
17_530	199	1.00	\N	\N	\N	\N
17_531	217	5.00	\N	\N	\N	\N
17_531	191	0.50	\N	\N	\N	\N
17_531	210	0.50	\N	\N	\N	\N
17_531	199	1.00	\N	\N	\N	\N
17_532	217	5.00	\N	\N	\N	\N
17_532	191	0.50	\N	\N	\N	\N
17_532	210	0.50	\N	\N	\N	\N
17_532	199	1.00	\N	\N	\N	\N
17_533	217	5.00	\N	\N	\N	\N
17_533	191	0.50	\N	\N	\N	\N
17_533	210	0.50	\N	\N	\N	\N
17_533	199	1.00	\N	\N	\N	\N
17_534	217	5.00	\N	\N	\N	\N
17_534	191	0.50	\N	\N	\N	\N
17_534	210	0.50	\N	\N	\N	\N
17_534	199	1.00	\N	\N	\N	\N
17_535	217	5.00	\N	\N	\N	\N
17_535	191	0.50	\N	\N	\N	\N
17_535	210	0.50	\N	\N	\N	\N
17_535	199	1.00	\N	\N	\N	\N
17_536	217	5.00	\N	\N	\N	\N
17_536	191	0.50	\N	\N	\N	\N
17_536	210	0.50	\N	\N	\N	\N
17_536	199	1.00	\N	\N	\N	\N
17_537	217	5.00	\N	\N	\N	\N
17_537	191	0.50	\N	\N	\N	\N
17_537	210	0.50	\N	\N	\N	\N
17_537	199	1.00	\N	\N	\N	\N
17_538	217	5.00	\N	\N	\N	\N
17_538	191	0.50	\N	\N	\N	\N
17_538	210	0.50	\N	\N	\N	\N
17_538	199	1.00	\N	\N	\N	\N
17_539	217	5.00	\N	\N	\N	\N
17_539	191	0.50	\N	\N	\N	\N
17_539	210	0.50	\N	\N	\N	\N
17_539	199	1.00	\N	\N	\N	\N
17_540	217	5.00	\N	\N	\N	\N
17_540	191	0.50	\N	\N	\N	\N
17_540	210	0.50	\N	\N	\N	\N
17_540	199	1.00	\N	\N	\N	\N
17_541	217	5.00	\N	\N	\N	\N
17_541	191	0.50	\N	\N	\N	\N
17_541	210	0.50	\N	\N	\N	\N
17_541	199	1.00	\N	\N	\N	\N
17_542	217	5.00	\N	\N	\N	\N
17_542	191	0.50	\N	\N	\N	\N
17_542	210	0.50	\N	\N	\N	\N
17_542	199	1.00	\N	\N	\N	\N
17_543	217	5.00	\N	\N	\N	\N
17_543	191	0.50	\N	\N	\N	\N
17_543	210	0.50	\N	\N	\N	\N
17_543	199	1.00	\N	\N	\N	\N
17_544	217	5.00	\N	\N	\N	\N
17_544	191	0.50	\N	\N	\N	\N
17_544	210	0.50	\N	\N	\N	\N
17_544	199	1.00	\N	\N	\N	\N
17_545	217	5.00	\N	\N	\N	\N
17_545	191	0.50	\N	\N	\N	\N
17_545	210	0.50	\N	\N	\N	\N
17_545	199	1.00	\N	\N	\N	\N
17_546	217	5.00	\N	\N	\N	\N
17_546	191	0.50	\N	\N	\N	\N
17_546	210	0.50	\N	\N	\N	\N
17_546	199	1.00	\N	\N	\N	\N
17_547	217	5.00	\N	\N	\N	\N
17_547	191	0.50	\N	\N	\N	\N
17_547	210	0.50	\N	\N	\N	\N
17_547	199	1.00	\N	\N	\N	\N
17_548	217	5.00	\N	\N	\N	\N
17_548	191	0.50	\N	\N	\N	\N
17_548	210	0.50	\N	\N	\N	\N
17_548	199	1.00	\N	\N	\N	\N
17_549	217	5.00	\N	\N	\N	\N
17_549	191	0.50	\N	\N	\N	\N
17_549	210	0.50	\N	\N	\N	\N
17_549	199	1.00	\N	\N	\N	\N
17_550	217	5.00	\N	\N	\N	\N
17_550	191	0.50	\N	\N	\N	\N
17_550	210	0.50	\N	\N	\N	\N
17_550	199	1.00	\N	\N	\N	\N
17_12	217	22.00	\N	\N	\N	\N
17_12	191	1.00	\N	\N	\N	\N
17_12	193	6.00	\N	\N	\N	\N
17_12	206	1.00	\N	\N	\N	\N
17_13	217	22.00	\N	\N	\N	\N
17_13	191	1.00	\N	\N	\N	\N
17_13	193	6.00	\N	\N	\N	\N
17_13	206	1.00	\N	\N	\N	\N
17_14	217	22.00	\N	\N	\N	\N
17_14	191	1.00	\N	\N	\N	\N
17_14	193	6.00	\N	\N	\N	\N
17_14	206	1.00	\N	\N	\N	\N
17_196	217	22.00	\N	\N	\N	\N
17_196	191	1.00	\N	\N	\N	\N
17_196	193	6.00	\N	\N	\N	\N
17_196	206	1.00	\N	\N	\N	\N
17_197	217	22.00	\N	\N	\N	\N
17_197	191	1.00	\N	\N	\N	\N
17_197	193	6.00	\N	\N	\N	\N
17_197	206	1.00	\N	\N	\N	\N
17_198	217	22.00	\N	\N	\N	\N
17_198	191	1.00	\N	\N	\N	\N
17_198	193	6.00	\N	\N	\N	\N
17_198	206	1.00	\N	\N	\N	\N
17_199	217	22.00	\N	\N	\N	\N
17_199	191	1.00	\N	\N	\N	\N
17_199	193	6.00	\N	\N	\N	\N
17_199	206	1.00	\N	\N	\N	\N
17_200	217	22.00	\N	\N	\N	\N
17_200	191	1.00	\N	\N	\N	\N
17_200	193	6.00	\N	\N	\N	\N
17_200	206	1.00	\N	\N	\N	\N
17_201	217	22.00	\N	\N	\N	\N
17_201	191	1.00	\N	\N	\N	\N
17_201	193	6.00	\N	\N	\N	\N
17_201	206	1.00	\N	\N	\N	\N
17_202	217	22.00	\N	\N	\N	\N
17_202	191	1.00	\N	\N	\N	\N
17_202	193	6.00	\N	\N	\N	\N
17_202	206	1.00	\N	\N	\N	\N
17_203	217	22.00	\N	\N	\N	\N
17_203	191	1.00	\N	\N	\N	\N
17_203	193	6.00	\N	\N	\N	\N
17_203	206	1.00	\N	\N	\N	\N
17_204	217	22.00	\N	\N	\N	\N
17_204	191	1.00	\N	\N	\N	\N
17_204	193	6.00	\N	\N	\N	\N
17_204	206	1.00	\N	\N	\N	\N
17_205	217	22.00	\N	\N	\N	\N
17_205	191	1.00	\N	\N	\N	\N
17_205	193	6.00	\N	\N	\N	\N
17_205	206	1.00	\N	\N	\N	\N
17_206	217	22.00	\N	\N	\N	\N
17_206	191	1.00	\N	\N	\N	\N
17_206	193	6.00	\N	\N	\N	\N
17_206	206	1.00	\N	\N	\N	\N
17_207	217	22.00	\N	\N	\N	\N
17_207	191	1.00	\N	\N	\N	\N
17_207	193	6.00	\N	\N	\N	\N
17_207	206	1.00	\N	\N	\N	\N
17_208	217	22.00	\N	\N	\N	\N
17_208	191	1.00	\N	\N	\N	\N
17_208	193	6.00	\N	\N	\N	\N
17_208	206	1.00	\N	\N	\N	\N
17_209	217	22.00	\N	\N	\N	\N
17_209	191	1.00	\N	\N	\N	\N
17_209	193	6.00	\N	\N	\N	\N
17_209	206	1.00	\N	\N	\N	\N
17_210	217	22.00	\N	\N	\N	\N
17_210	191	1.00	\N	\N	\N	\N
17_210	193	6.00	\N	\N	\N	\N
17_210	206	1.00	\N	\N	\N	\N
17_211	217	22.00	\N	\N	\N	\N
17_211	191	1.00	\N	\N	\N	\N
17_211	193	6.00	\N	\N	\N	\N
17_211	206	1.00	\N	\N	\N	\N
17_212	217	22.00	\N	\N	\N	\N
17_212	191	1.00	\N	\N	\N	\N
17_212	193	6.00	\N	\N	\N	\N
17_212	206	1.00	\N	\N	\N	\N
17_213	217	22.00	\N	\N	\N	\N
17_213	191	1.00	\N	\N	\N	\N
17_213	193	6.00	\N	\N	\N	\N
17_213	206	1.00	\N	\N	\N	\N
17_214	217	22.00	\N	\N	\N	\N
17_214	191	1.00	\N	\N	\N	\N
17_214	193	6.00	\N	\N	\N	\N
17_214	206	1.00	\N	\N	\N	\N
17_215	217	22.00	\N	\N	\N	\N
17_215	191	1.00	\N	\N	\N	\N
17_215	193	6.00	\N	\N	\N	\N
17_215	206	1.00	\N	\N	\N	\N
17_216	217	22.00	\N	\N	\N	\N
17_216	191	1.00	\N	\N	\N	\N
17_216	193	6.00	\N	\N	\N	\N
17_216	206	1.00	\N	\N	\N	\N
17_217	217	22.00	\N	\N	\N	\N
17_217	191	1.00	\N	\N	\N	\N
17_217	193	6.00	\N	\N	\N	\N
17_217	206	1.00	\N	\N	\N	\N
17_16	217	18.00	\N	\N	\N	\N
17_16	191	1.00	\N	\N	\N	\N
17_16	193	6.00	\N	\N	\N	\N
17_16	200	1.00	\N	\N	\N	\N
17_17	217	20.00	\N	\N	\N	\N
17_17	191	1.00	\N	\N	\N	\N
17_17	193	6.00	\N	\N	\N	\N
17_17	206	1.00	\N	\N	\N	\N
17_162	217	18.00	\N	\N	\N	\N
17_162	191	1.00	\N	\N	\N	\N
17_162	193	6.00	\N	\N	\N	\N
17_162	200	1.00	\N	\N	\N	\N
17_218	217	18.00	\N	\N	\N	\N
17_218	191	1.00	\N	\N	\N	\N
17_218	193	6.00	\N	\N	\N	\N
17_218	200	1.00	\N	\N	\N	\N
17_219	217	18.00	\N	\N	\N	\N
17_219	191	1.00	\N	\N	\N	\N
17_219	193	6.00	\N	\N	\N	\N
17_219	200	1.00	\N	\N	\N	\N
17_220	217	18.00	\N	\N	\N	\N
17_220	191	1.00	\N	\N	\N	\N
17_220	193	6.00	\N	\N	\N	\N
17_220	200	1.00	\N	\N	\N	\N
17_221	217	18.00	\N	\N	\N	\N
17_221	191	1.00	\N	\N	\N	\N
17_221	193	6.00	\N	\N	\N	\N
17_221	200	1.00	\N	\N	\N	\N
17_222	217	18.00	\N	\N	\N	\N
17_222	191	1.00	\N	\N	\N	\N
17_222	193	6.00	\N	\N	\N	\N
17_222	200	1.00	\N	\N	\N	\N
17_223	217	18.00	\N	\N	\N	\N
17_223	191	1.00	\N	\N	\N	\N
17_223	193	6.00	\N	\N	\N	\N
17_223	200	1.00	\N	\N	\N	\N
17_224	217	18.00	\N	\N	\N	\N
17_224	191	1.00	\N	\N	\N	\N
17_224	193	6.00	\N	\N	\N	\N
17_224	200	1.00	\N	\N	\N	\N
17_225	217	18.00	\N	\N	\N	\N
17_225	191	1.00	\N	\N	\N	\N
17_225	193	6.00	\N	\N	\N	\N
17_225	200	1.00	\N	\N	\N	\N
17_226	217	18.00	\N	\N	\N	\N
17_226	191	1.00	\N	\N	\N	\N
17_226	193	6.00	\N	\N	\N	\N
17_226	200	1.00	\N	\N	\N	\N
17_227	217	18.00	\N	\N	\N	\N
17_227	191	1.00	\N	\N	\N	\N
17_227	193	6.00	\N	\N	\N	\N
17_227	200	1.00	\N	\N	\N	\N
17_228	217	18.00	\N	\N	\N	\N
17_228	191	1.00	\N	\N	\N	\N
17_228	193	6.00	\N	\N	\N	\N
17_228	200	1.00	\N	\N	\N	\N
17_229	217	18.00	\N	\N	\N	\N
17_229	191	1.00	\N	\N	\N	\N
17_229	193	6.00	\N	\N	\N	\N
17_229	200	1.00	\N	\N	\N	\N
17_230	217	18.00	\N	\N	\N	\N
17_230	191	1.00	\N	\N	\N	\N
17_230	193	6.00	\N	\N	\N	\N
17_230	200	1.00	\N	\N	\N	\N
17_231	217	18.00	\N	\N	\N	\N
17_231	191	1.00	\N	\N	\N	\N
17_231	193	6.00	\N	\N	\N	\N
17_231	200	1.00	\N	\N	\N	\N
17_232	217	18.00	\N	\N	\N	\N
17_232	191	1.00	\N	\N	\N	\N
17_232	193	6.00	\N	\N	\N	\N
17_232	200	1.00	\N	\N	\N	\N
17_233	217	18.00	\N	\N	\N	\N
17_233	191	1.00	\N	\N	\N	\N
17_233	193	6.00	\N	\N	\N	\N
17_233	200	1.00	\N	\N	\N	\N
17_234	217	18.00	\N	\N	\N	\N
17_234	191	1.00	\N	\N	\N	\N
17_234	193	6.00	\N	\N	\N	\N
17_234	200	1.00	\N	\N	\N	\N
17_235	217	18.00	\N	\N	\N	\N
17_235	191	1.00	\N	\N	\N	\N
17_235	193	6.00	\N	\N	\N	\N
17_235	200	1.00	\N	\N	\N	\N
17_236	217	18.00	\N	\N	\N	\N
17_236	191	1.00	\N	\N	\N	\N
17_236	193	6.00	\N	\N	\N	\N
17_236	200	1.00	\N	\N	\N	\N
17_237	217	18.00	\N	\N	\N	\N
17_237	191	1.00	\N	\N	\N	\N
17_237	193	6.00	\N	\N	\N	\N
17_237	200	1.00	\N	\N	\N	\N
17_238	217	18.00	\N	\N	\N	\N
17_238	191	1.00	\N	\N	\N	\N
17_238	193	6.00	\N	\N	\N	\N
17_238	200	1.00	\N	\N	\N	\N
17_239	217	18.00	\N	\N	\N	\N
17_239	191	1.00	\N	\N	\N	\N
17_239	193	6.00	\N	\N	\N	\N
17_239	200	1.00	\N	\N	\N	\N
17_240	217	18.00	\N	\N	\N	\N
17_240	191	1.00	\N	\N	\N	\N
17_240	193	6.00	\N	\N	\N	\N
17_240	200	1.00	\N	\N	\N	\N
17_241	217	20.00	\N	\N	\N	\N
17_241	191	1.00	\N	\N	\N	\N
17_241	193	6.00	\N	\N	\N	\N
17_241	206	1.00	\N	\N	\N	\N
17_242	217	20.00	\N	\N	\N	\N
17_242	191	1.00	\N	\N	\N	\N
17_242	193	6.00	\N	\N	\N	\N
17_242	206	1.00	\N	\N	\N	\N
17_243	217	20.00	\N	\N	\N	\N
17_243	191	1.00	\N	\N	\N	\N
17_243	193	6.00	\N	\N	\N	\N
17_243	206	1.00	\N	\N	\N	\N
17_244	217	20.00	\N	\N	\N	\N
17_244	191	1.00	\N	\N	\N	\N
17_244	193	6.00	\N	\N	\N	\N
17_244	206	1.00	\N	\N	\N	\N
17_245	217	20.00	\N	\N	\N	\N
17_245	191	1.00	\N	\N	\N	\N
17_245	193	6.00	\N	\N	\N	\N
17_245	206	1.00	\N	\N	\N	\N
17_246	217	20.00	\N	\N	\N	\N
17_246	191	1.00	\N	\N	\N	\N
17_246	193	6.00	\N	\N	\N	\N
17_246	206	1.00	\N	\N	\N	\N
17_247	217	20.00	\N	\N	\N	\N
17_247	191	1.00	\N	\N	\N	\N
17_247	193	6.00	\N	\N	\N	\N
17_247	206	1.00	\N	\N	\N	\N
17_248	217	20.00	\N	\N	\N	\N
17_248	191	1.00	\N	\N	\N	\N
17_248	193	6.00	\N	\N	\N	\N
17_248	206	1.00	\N	\N	\N	\N
17_249	217	20.00	\N	\N	\N	\N
17_249	191	1.00	\N	\N	\N	\N
17_249	193	6.00	\N	\N	\N	\N
17_249	206	1.00	\N	\N	\N	\N
17_250	217	20.00	\N	\N	\N	\N
17_250	191	1.00	\N	\N	\N	\N
17_250	193	6.00	\N	\N	\N	\N
17_250	206	1.00	\N	\N	\N	\N
17_251	217	20.00	\N	\N	\N	\N
17_251	191	1.00	\N	\N	\N	\N
17_251	193	6.00	\N	\N	\N	\N
17_251	206	1.00	\N	\N	\N	\N
17_252	217	20.00	\N	\N	\N	\N
17_252	191	1.00	\N	\N	\N	\N
17_252	193	6.00	\N	\N	\N	\N
17_252	206	1.00	\N	\N	\N	\N
17_253	217	20.00	\N	\N	\N	\N
17_253	191	1.00	\N	\N	\N	\N
17_253	193	6.00	\N	\N	\N	\N
17_253	206	1.00	\N	\N	\N	\N
17_254	217	20.00	\N	\N	\N	\N
17_254	191	1.00	\N	\N	\N	\N
17_254	193	6.00	\N	\N	\N	\N
17_254	206	1.00	\N	\N	\N	\N
17_255	217	20.00	\N	\N	\N	\N
17_255	191	1.00	\N	\N	\N	\N
17_255	193	6.00	\N	\N	\N	\N
17_255	206	1.00	\N	\N	\N	\N
17_256	217	20.00	\N	\N	\N	\N
17_256	191	1.00	\N	\N	\N	\N
17_256	193	6.00	\N	\N	\N	\N
17_256	206	1.00	\N	\N	\N	\N
17_257	217	20.00	\N	\N	\N	\N
17_257	191	1.00	\N	\N	\N	\N
17_257	193	6.00	\N	\N	\N	\N
17_257	206	1.00	\N	\N	\N	\N
17_258	217	20.00	\N	\N	\N	\N
17_258	191	1.00	\N	\N	\N	\N
17_258	193	6.00	\N	\N	\N	\N
17_258	206	1.00	\N	\N	\N	\N
17_259	217	20.00	\N	\N	\N	\N
17_259	191	1.00	\N	\N	\N	\N
17_259	193	6.00	\N	\N	\N	\N
17_259	206	1.00	\N	\N	\N	\N
17_260	217	20.00	\N	\N	\N	\N
17_260	191	1.00	\N	\N	\N	\N
17_260	193	6.00	\N	\N	\N	\N
17_260	206	1.00	\N	\N	\N	\N
17_261	217	20.00	\N	\N	\N	\N
17_261	191	1.00	\N	\N	\N	\N
17_261	193	6.00	\N	\N	\N	\N
17_261	206	1.00	\N	\N	\N	\N
17_262	217	20.00	\N	\N	\N	\N
17_262	191	1.00	\N	\N	\N	\N
17_262	193	6.00	\N	\N	\N	\N
17_262	206	1.00	\N	\N	\N	\N
17_263	217	20.00	\N	\N	\N	\N
17_263	191	1.00	\N	\N	\N	\N
17_263	193	6.00	\N	\N	\N	\N
17_263	206	1.00	\N	\N	\N	\N
17_264	217	20.00	\N	\N	\N	\N
17_264	191	1.00	\N	\N	\N	\N
17_264	193	6.00	\N	\N	\N	\N
17_264	206	1.00	\N	\N	\N	\N
17_313	217	6.00	\N	\N	\N	\N
17_313	191	1.00	\N	\N	\N	\N
17_313	213	1.00	\N	\N	\N	\N
17_313	214	1.00	\N	\N	\N	\N
17_313	199	2.00	\N	\N	\N	\N
17_314	217	6.00	\N	\N	\N	\N
17_314	191	1.00	\N	\N	\N	\N
17_314	213	1.00	\N	\N	\N	\N
17_314	214	1.00	\N	\N	\N	\N
17_314	199	2.00	\N	\N	\N	\N
17_315	217	6.00	\N	\N	\N	\N
17_315	191	1.00	\N	\N	\N	\N
17_315	213	1.00	\N	\N	\N	\N
17_315	214	1.00	\N	\N	\N	\N
17_315	199	2.00	\N	\N	\N	\N
17_316	217	6.00	\N	\N	\N	\N
17_316	191	1.00	\N	\N	\N	\N
17_316	213	1.00	\N	\N	\N	\N
17_316	214	1.00	\N	\N	\N	\N
17_316	199	2.00	\N	\N	\N	\N
17_317	217	6.00	\N	\N	\N	\N
17_317	191	1.00	\N	\N	\N	\N
17_317	213	1.00	\N	\N	\N	\N
17_317	214	1.00	\N	\N	\N	\N
17_317	199	2.00	\N	\N	\N	\N
17_318	217	6.00	\N	\N	\N	\N
17_318	191	1.00	\N	\N	\N	\N
17_318	213	1.00	\N	\N	\N	\N
17_318	214	1.00	\N	\N	\N	\N
17_318	199	2.00	\N	\N	\N	\N
17_319	217	6.00	\N	\N	\N	\N
17_319	191	1.00	\N	\N	\N	\N
17_319	213	1.00	\N	\N	\N	\N
17_319	214	1.00	\N	\N	\N	\N
17_319	199	2.00	\N	\N	\N	\N
17_320	217	6.00	\N	\N	\N	\N
17_320	191	1.00	\N	\N	\N	\N
17_320	213	1.00	\N	\N	\N	\N
17_320	214	1.00	\N	\N	\N	\N
17_320	199	2.00	\N	\N	\N	\N
17_321	217	6.00	\N	\N	\N	\N
17_321	191	1.00	\N	\N	\N	\N
17_321	213	1.00	\N	\N	\N	\N
17_321	214	1.00	\N	\N	\N	\N
17_321	199	2.00	\N	\N	\N	\N
17_322	217	6.00	\N	\N	\N	\N
17_322	191	1.00	\N	\N	\N	\N
17_322	213	1.00	\N	\N	\N	\N
17_322	214	1.00	\N	\N	\N	\N
17_322	199	2.00	\N	\N	\N	\N
17_323	217	6.00	\N	\N	\N	\N
17_323	191	1.00	\N	\N	\N	\N
17_323	213	1.00	\N	\N	\N	\N
17_323	214	1.00	\N	\N	\N	\N
17_323	199	2.00	\N	\N	\N	\N
17_324	217	6.00	\N	\N	\N	\N
17_324	191	1.00	\N	\N	\N	\N
17_324	213	1.00	\N	\N	\N	\N
17_324	214	1.00	\N	\N	\N	\N
17_324	199	2.00	\N	\N	\N	\N
17_325	217	6.00	\N	\N	\N	\N
17_325	191	1.00	\N	\N	\N	\N
17_325	213	1.00	\N	\N	\N	\N
17_325	214	1.00	\N	\N	\N	\N
17_325	199	2.00	\N	\N	\N	\N
17_326	217	6.00	\N	\N	\N	\N
17_326	191	1.00	\N	\N	\N	\N
17_326	213	1.00	\N	\N	\N	\N
17_326	214	1.00	\N	\N	\N	\N
17_326	199	2.00	\N	\N	\N	\N
17_327	217	6.00	\N	\N	\N	\N
17_327	191	1.00	\N	\N	\N	\N
17_327	213	1.00	\N	\N	\N	\N
17_327	214	1.00	\N	\N	\N	\N
17_327	199	2.00	\N	\N	\N	\N
17_328	217	6.00	\N	\N	\N	\N
17_328	191	1.00	\N	\N	\N	\N
17_328	213	1.00	\N	\N	\N	\N
17_328	214	1.00	\N	\N	\N	\N
17_328	199	2.00	\N	\N	\N	\N
17_329	217	6.00	\N	\N	\N	\N
17_329	191	1.00	\N	\N	\N	\N
17_329	213	1.00	\N	\N	\N	\N
17_329	214	1.00	\N	\N	\N	\N
17_329	199	2.00	\N	\N	\N	\N
17_330	217	6.00	\N	\N	\N	\N
17_330	191	1.00	\N	\N	\N	\N
17_330	213	1.00	\N	\N	\N	\N
17_330	214	1.00	\N	\N	\N	\N
17_330	199	2.00	\N	\N	\N	\N
17_331	217	6.00	\N	\N	\N	\N
17_331	191	1.00	\N	\N	\N	\N
17_331	213	1.00	\N	\N	\N	\N
17_331	214	1.00	\N	\N	\N	\N
17_331	199	2.00	\N	\N	\N	\N
17_332	217	6.00	\N	\N	\N	\N
17_332	191	1.00	\N	\N	\N	\N
17_332	213	1.00	\N	\N	\N	\N
17_332	214	1.00	\N	\N	\N	\N
17_332	199	2.00	\N	\N	\N	\N
17_333	217	6.00	\N	\N	\N	\N
17_333	191	1.00	\N	\N	\N	\N
17_333	213	1.00	\N	\N	\N	\N
17_333	214	1.00	\N	\N	\N	\N
17_333	199	2.00	\N	\N	\N	\N
17_334	217	6.00	\N	\N	\N	\N
17_334	191	1.00	\N	\N	\N	\N
17_334	213	1.00	\N	\N	\N	\N
17_334	214	1.00	\N	\N	\N	\N
17_334	199	2.00	\N	\N	\N	\N
17_335	217	6.00	\N	\N	\N	\N
17_335	191	1.00	\N	\N	\N	\N
17_335	213	1.00	\N	\N	\N	\N
17_335	214	1.00	\N	\N	\N	\N
17_335	199	2.00	\N	\N	\N	\N
17_336	217	6.00	\N	\N	\N	\N
17_336	191	1.00	\N	\N	\N	\N
17_336	213	1.00	\N	\N	\N	\N
17_336	214	1.00	\N	\N	\N	\N
17_336	199	2.00	\N	\N	\N	\N
17_289	217	22.00	\N	\N	\N	\N
17_289	191	1.00	\N	\N	\N	\N
17_289	193	6.00	\N	\N	\N	\N
17_289	205	1.00	\N	\N	\N	\N
17_290	217	22.00	\N	\N	\N	\N
17_290	191	1.00	\N	\N	\N	\N
17_290	193	6.00	\N	\N	\N	\N
17_290	205	1.00	\N	\N	\N	\N
17_291	217	22.00	\N	\N	\N	\N
17_291	191	1.00	\N	\N	\N	\N
17_291	193	6.00	\N	\N	\N	\N
17_291	205	1.00	\N	\N	\N	\N
17_292	217	22.00	\N	\N	\N	\N
17_292	191	1.00	\N	\N	\N	\N
17_292	193	6.00	\N	\N	\N	\N
17_292	205	1.00	\N	\N	\N	\N
17_293	217	22.00	\N	\N	\N	\N
17_293	191	1.00	\N	\N	\N	\N
17_293	193	6.00	\N	\N	\N	\N
17_293	205	1.00	\N	\N	\N	\N
17_294	217	22.00	\N	\N	\N	\N
17_294	191	1.00	\N	\N	\N	\N
17_294	193	6.00	\N	\N	\N	\N
17_294	205	1.00	\N	\N	\N	\N
17_295	217	22.00	\N	\N	\N	\N
17_295	191	1.00	\N	\N	\N	\N
17_295	193	6.00	\N	\N	\N	\N
17_295	205	1.00	\N	\N	\N	\N
17_296	217	22.00	\N	\N	\N	\N
17_296	191	1.00	\N	\N	\N	\N
17_296	193	6.00	\N	\N	\N	\N
17_296	205	1.00	\N	\N	\N	\N
17_297	217	22.00	\N	\N	\N	\N
17_297	191	1.00	\N	\N	\N	\N
17_297	193	6.00	\N	\N	\N	\N
17_297	205	1.00	\N	\N	\N	\N
17_298	217	22.00	\N	\N	\N	\N
17_298	191	1.00	\N	\N	\N	\N
17_298	193	6.00	\N	\N	\N	\N
17_298	205	1.00	\N	\N	\N	\N
17_299	217	22.00	\N	\N	\N	\N
17_299	191	1.00	\N	\N	\N	\N
17_299	193	6.00	\N	\N	\N	\N
17_299	205	1.00	\N	\N	\N	\N
17_300	217	22.00	\N	\N	\N	\N
17_300	191	1.00	\N	\N	\N	\N
17_300	193	6.00	\N	\N	\N	\N
17_300	205	1.00	\N	\N	\N	\N
17_301	217	22.00	\N	\N	\N	\N
17_301	191	1.00	\N	\N	\N	\N
17_301	193	6.00	\N	\N	\N	\N
17_301	205	1.00	\N	\N	\N	\N
17_302	217	22.00	\N	\N	\N	\N
17_302	191	1.00	\N	\N	\N	\N
17_302	193	6.00	\N	\N	\N	\N
17_302	205	1.00	\N	\N	\N	\N
17_303	217	22.00	\N	\N	\N	\N
17_303	191	1.00	\N	\N	\N	\N
17_303	193	6.00	\N	\N	\N	\N
17_303	205	1.00	\N	\N	\N	\N
17_304	217	22.00	\N	\N	\N	\N
17_304	191	1.00	\N	\N	\N	\N
17_304	193	6.00	\N	\N	\N	\N
17_304	205	1.00	\N	\N	\N	\N
17_305	217	22.00	\N	\N	\N	\N
17_305	191	1.00	\N	\N	\N	\N
17_305	193	6.00	\N	\N	\N	\N
17_305	205	1.00	\N	\N	\N	\N
17_306	217	22.00	\N	\N	\N	\N
17_306	191	1.00	\N	\N	\N	\N
17_306	193	6.00	\N	\N	\N	\N
17_306	205	1.00	\N	\N	\N	\N
17_307	217	22.00	\N	\N	\N	\N
17_307	191	1.00	\N	\N	\N	\N
17_307	193	6.00	\N	\N	\N	\N
17_307	205	1.00	\N	\N	\N	\N
17_308	217	22.00	\N	\N	\N	\N
17_308	191	1.00	\N	\N	\N	\N
17_308	193	6.00	\N	\N	\N	\N
17_308	205	1.00	\N	\N	\N	\N
17_309	217	22.00	\N	\N	\N	\N
17_309	191	1.00	\N	\N	\N	\N
17_309	193	6.00	\N	\N	\N	\N
17_309	205	1.00	\N	\N	\N	\N
17_310	217	22.00	\N	\N	\N	\N
17_310	191	1.00	\N	\N	\N	\N
17_310	193	6.00	\N	\N	\N	\N
17_310	205	1.00	\N	\N	\N	\N
17_311	217	22.00	\N	\N	\N	\N
17_311	191	1.00	\N	\N	\N	\N
17_311	193	6.00	\N	\N	\N	\N
17_311	205	1.00	\N	\N	\N	\N
17_312	217	22.00	\N	\N	\N	\N
17_312	191	1.00	\N	\N	\N	\N
17_312	193	6.00	\N	\N	\N	\N
17_312	205	1.00	\N	\N	\N	\N
17_265	217	12.00	\N	\N	\N	\N
17_265	191	1.00	\N	\N	\N	\N
17_265	193	6.00	\N	\N	\N	\N
17_265	198	1.00	\N	\N	\N	\N
17_265	205	1.00	\N	\N	\N	\N
17_266	217	12.00	\N	\N	\N	\N
17_266	191	1.00	\N	\N	\N	\N
17_266	193	6.00	\N	\N	\N	\N
17_266	198	1.00	\N	\N	\N	\N
17_266	205	1.00	\N	\N	\N	\N
17_267	217	12.00	\N	\N	\N	\N
17_267	191	1.00	\N	\N	\N	\N
17_267	193	6.00	\N	\N	\N	\N
17_267	198	1.00	\N	\N	\N	\N
17_267	205	1.00	\N	\N	\N	\N
17_268	217	12.00	\N	\N	\N	\N
17_268	191	1.00	\N	\N	\N	\N
17_268	193	6.00	\N	\N	\N	\N
17_268	198	1.00	\N	\N	\N	\N
17_268	205	1.00	\N	\N	\N	\N
17_269	217	12.00	\N	\N	\N	\N
17_269	191	1.00	\N	\N	\N	\N
17_269	193	6.00	\N	\N	\N	\N
17_269	198	1.00	\N	\N	\N	\N
17_269	205	1.00	\N	\N	\N	\N
17_270	217	12.00	\N	\N	\N	\N
17_270	191	1.00	\N	\N	\N	\N
17_270	193	6.00	\N	\N	\N	\N
17_270	198	1.00	\N	\N	\N	\N
17_270	205	1.00	\N	\N	\N	\N
17_271	217	12.00	\N	\N	\N	\N
17_271	191	1.00	\N	\N	\N	\N
17_271	193	6.00	\N	\N	\N	\N
17_271	198	1.00	\N	\N	\N	\N
17_271	205	1.00	\N	\N	\N	\N
17_272	217	12.00	\N	\N	\N	\N
17_272	191	1.00	\N	\N	\N	\N
17_272	193	6.00	\N	\N	\N	\N
17_272	198	1.00	\N	\N	\N	\N
17_272	205	1.00	\N	\N	\N	\N
17_273	217	12.00	\N	\N	\N	\N
17_273	191	1.00	\N	\N	\N	\N
17_273	193	6.00	\N	\N	\N	\N
17_273	198	1.00	\N	\N	\N	\N
17_273	205	1.00	\N	\N	\N	\N
17_274	217	12.00	\N	\N	\N	\N
17_274	191	1.00	\N	\N	\N	\N
17_274	193	6.00	\N	\N	\N	\N
17_274	198	1.00	\N	\N	\N	\N
17_274	205	1.00	\N	\N	\N	\N
17_275	217	12.00	\N	\N	\N	\N
17_275	191	1.00	\N	\N	\N	\N
17_275	193	6.00	\N	\N	\N	\N
17_275	198	1.00	\N	\N	\N	\N
17_275	205	1.00	\N	\N	\N	\N
17_276	217	12.00	\N	\N	\N	\N
17_276	191	1.00	\N	\N	\N	\N
17_276	193	6.00	\N	\N	\N	\N
17_276	198	1.00	\N	\N	\N	\N
17_276	205	1.00	\N	\N	\N	\N
17_277	217	12.00	\N	\N	\N	\N
17_277	191	1.00	\N	\N	\N	\N
17_277	193	6.00	\N	\N	\N	\N
17_277	198	1.00	\N	\N	\N	\N
17_277	205	1.00	\N	\N	\N	\N
17_278	217	12.00	\N	\N	\N	\N
17_278	191	1.00	\N	\N	\N	\N
17_278	193	6.00	\N	\N	\N	\N
17_278	198	1.00	\N	\N	\N	\N
17_278	205	1.00	\N	\N	\N	\N
17_279	217	12.00	\N	\N	\N	\N
17_279	191	1.00	\N	\N	\N	\N
17_279	193	6.00	\N	\N	\N	\N
17_279	198	1.00	\N	\N	\N	\N
17_279	205	1.00	\N	\N	\N	\N
17_280	217	12.00	\N	\N	\N	\N
17_280	191	1.00	\N	\N	\N	\N
17_280	193	6.00	\N	\N	\N	\N
17_280	198	1.00	\N	\N	\N	\N
17_280	205	1.00	\N	\N	\N	\N
17_281	217	12.00	\N	\N	\N	\N
17_281	191	1.00	\N	\N	\N	\N
17_281	193	6.00	\N	\N	\N	\N
17_281	198	1.00	\N	\N	\N	\N
17_281	205	1.00	\N	\N	\N	\N
17_282	217	12.00	\N	\N	\N	\N
17_282	191	1.00	\N	\N	\N	\N
17_282	193	6.00	\N	\N	\N	\N
17_282	198	1.00	\N	\N	\N	\N
17_282	205	1.00	\N	\N	\N	\N
17_283	217	12.00	\N	\N	\N	\N
17_283	191	1.00	\N	\N	\N	\N
17_283	193	6.00	\N	\N	\N	\N
17_283	198	1.00	\N	\N	\N	\N
17_283	205	1.00	\N	\N	\N	\N
17_284	217	12.00	\N	\N	\N	\N
17_284	191	1.00	\N	\N	\N	\N
17_284	193	6.00	\N	\N	\N	\N
17_284	198	1.00	\N	\N	\N	\N
17_284	205	1.00	\N	\N	\N	\N
17_285	217	12.00	\N	\N	\N	\N
17_285	191	1.00	\N	\N	\N	\N
17_285	193	6.00	\N	\N	\N	\N
17_285	198	1.00	\N	\N	\N	\N
17_285	205	1.00	\N	\N	\N	\N
17_286	217	12.00	\N	\N	\N	\N
17_286	191	1.00	\N	\N	\N	\N
17_286	193	6.00	\N	\N	\N	\N
17_286	198	1.00	\N	\N	\N	\N
17_286	205	1.00	\N	\N	\N	\N
17_287	217	12.00	\N	\N	\N	\N
17_287	191	1.00	\N	\N	\N	\N
17_287	193	6.00	\N	\N	\N	\N
17_287	198	1.00	\N	\N	\N	\N
17_287	205	1.00	\N	\N	\N	\N
17_288	217	12.00	\N	\N	\N	\N
17_288	191	1.00	\N	\N	\N	\N
17_288	193	6.00	\N	\N	\N	\N
17_288	198	1.00	\N	\N	\N	\N
17_288	205	1.00	\N	\N	\N	\N
17_56	217	32.00	\N	\N	\N	\N
17_56	193	6.00	\N	\N	\N	\N
17_56	199	3.00	\N	\N	\N	\N
17_57	217	16.00	\N	\N	\N	\N
17_57	192	1.00	\N	\N	\N	\N
17_57	193	3.00	\N	\N	\N	\N
17_57	199	1.00	\N	\N	\N	\N
17_58	217	19.00	\N	\N	\N	\N
17_58	192	1.00	\N	\N	\N	\N
17_58	193	3.00	\N	\N	\N	\N
17_58	199	1.00	\N	\N	\N	\N
17_502	217	16.00	\N	\N	\N	\N
17_502	191	2.00	\N	\N	\N	\N
17_502	193	8.00	\N	\N	\N	\N
17_502	201	1.00	\N	\N	\N	\N
17_502	202	1.00	\N	\N	\N	\N
17_502	199	1.00	\N	\N	\N	\N
17_503	217	16.00	\N	\N	\N	\N
17_503	191	2.00	\N	\N	\N	\N
17_503	193	8.00	\N	\N	\N	\N
17_503	201	1.00	\N	\N	\N	\N
17_503	202	1.00	\N	\N	\N	\N
17_503	199	1.00	\N	\N	\N	\N
17_504	217	16.00	\N	\N	\N	\N
17_504	191	2.00	\N	\N	\N	\N
17_504	193	8.00	\N	\N	\N	\N
17_504	201	1.00	\N	\N	\N	\N
17_504	202	1.00	\N	\N	\N	\N
17_504	199	1.00	\N	\N	\N	\N
17_505	217	16.00	\N	\N	\N	\N
17_505	191	2.00	\N	\N	\N	\N
17_505	193	8.00	\N	\N	\N	\N
17_505	201	1.00	\N	\N	\N	\N
17_505	202	1.00	\N	\N	\N	\N
17_505	199	1.00	\N	\N	\N	\N
17_506	217	16.00	\N	\N	\N	\N
17_506	191	2.00	\N	\N	\N	\N
17_506	193	8.00	\N	\N	\N	\N
17_506	201	1.00	\N	\N	\N	\N
17_506	202	1.00	\N	\N	\N	\N
17_506	199	1.00	\N	\N	\N	\N
17_507	217	16.00	\N	\N	\N	\N
17_507	191	2.00	\N	\N	\N	\N
17_507	193	8.00	\N	\N	\N	\N
17_507	201	1.00	\N	\N	\N	\N
17_507	202	1.00	\N	\N	\N	\N
17_507	199	1.00	\N	\N	\N	\N
17_508	217	16.00	\N	\N	\N	\N
17_508	191	2.00	\N	\N	\N	\N
17_508	193	8.00	\N	\N	\N	\N
17_508	201	1.00	\N	\N	\N	\N
17_508	202	1.00	\N	\N	\N	\N
17_508	199	1.00	\N	\N	\N	\N
17_509	217	16.00	\N	\N	\N	\N
17_509	191	2.00	\N	\N	\N	\N
17_509	193	8.00	\N	\N	\N	\N
17_509	201	1.00	\N	\N	\N	\N
17_509	202	1.00	\N	\N	\N	\N
17_509	199	1.00	\N	\N	\N	\N
17_510	217	16.00	\N	\N	\N	\N
17_510	191	2.00	\N	\N	\N	\N
17_510	193	8.00	\N	\N	\N	\N
17_510	201	1.00	\N	\N	\N	\N
17_510	202	1.00	\N	\N	\N	\N
17_510	199	1.00	\N	\N	\N	\N
17_511	217	16.00	\N	\N	\N	\N
17_511	191	2.00	\N	\N	\N	\N
17_511	193	8.00	\N	\N	\N	\N
17_511	201	1.00	\N	\N	\N	\N
17_511	202	1.00	\N	\N	\N	\N
17_511	199	1.00	\N	\N	\N	\N
17_512	217	16.00	\N	\N	\N	\N
17_512	191	2.00	\N	\N	\N	\N
17_512	193	8.00	\N	\N	\N	\N
17_512	201	1.00	\N	\N	\N	\N
17_512	202	1.00	\N	\N	\N	\N
17_512	199	1.00	\N	\N	\N	\N
17_513	217	16.00	\N	\N	\N	\N
17_513	191	2.00	\N	\N	\N	\N
17_513	193	8.00	\N	\N	\N	\N
17_513	201	1.00	\N	\N	\N	\N
17_513	202	1.00	\N	\N	\N	\N
17_513	199	1.00	\N	\N	\N	\N
17_514	217	16.00	\N	\N	\N	\N
17_514	191	2.00	\N	\N	\N	\N
17_514	193	8.00	\N	\N	\N	\N
17_514	201	1.00	\N	\N	\N	\N
17_514	202	1.00	\N	\N	\N	\N
17_514	199	1.00	\N	\N	\N	\N
17_515	217	16.00	\N	\N	\N	\N
17_515	191	2.00	\N	\N	\N	\N
17_515	193	8.00	\N	\N	\N	\N
17_515	201	1.00	\N	\N	\N	\N
17_515	202	1.00	\N	\N	\N	\N
17_515	199	1.00	\N	\N	\N	\N
17_516	217	16.00	\N	\N	\N	\N
17_516	191	2.00	\N	\N	\N	\N
17_516	193	8.00	\N	\N	\N	\N
17_516	201	1.00	\N	\N	\N	\N
17_516	202	1.00	\N	\N	\N	\N
17_516	199	1.00	\N	\N	\N	\N
17_517	217	16.00	\N	\N	\N	\N
17_517	191	2.00	\N	\N	\N	\N
17_517	193	8.00	\N	\N	\N	\N
17_517	201	1.00	\N	\N	\N	\N
17_517	202	1.00	\N	\N	\N	\N
17_517	199	1.00	\N	\N	\N	\N
17_518	217	16.00	\N	\N	\N	\N
17_518	191	2.00	\N	\N	\N	\N
17_518	193	8.00	\N	\N	\N	\N
17_518	201	1.00	\N	\N	\N	\N
17_518	202	1.00	\N	\N	\N	\N
17_518	199	1.00	\N	\N	\N	\N
17_519	217	16.00	\N	\N	\N	\N
17_519	191	2.00	\N	\N	\N	\N
17_519	193	8.00	\N	\N	\N	\N
17_519	201	1.00	\N	\N	\N	\N
17_519	202	1.00	\N	\N	\N	\N
17_519	199	1.00	\N	\N	\N	\N
17_520	217	16.00	\N	\N	\N	\N
17_520	191	2.00	\N	\N	\N	\N
17_520	193	8.00	\N	\N	\N	\N
17_520	201	1.00	\N	\N	\N	\N
17_520	202	1.00	\N	\N	\N	\N
17_520	199	1.00	\N	\N	\N	\N
17_521	217	16.00	\N	\N	\N	\N
17_521	191	2.00	\N	\N	\N	\N
17_521	193	8.00	\N	\N	\N	\N
17_521	201	1.00	\N	\N	\N	\N
17_521	202	1.00	\N	\N	\N	\N
17_521	199	1.00	\N	\N	\N	\N
17_522	217	16.00	\N	\N	\N	\N
17_522	191	2.00	\N	\N	\N	\N
17_522	193	8.00	\N	\N	\N	\N
17_522	201	1.00	\N	\N	\N	\N
17_522	202	1.00	\N	\N	\N	\N
17_522	199	1.00	\N	\N	\N	\N
17_523	217	16.00	\N	\N	\N	\N
17_523	191	2.00	\N	\N	\N	\N
17_523	193	8.00	\N	\N	\N	\N
17_523	201	1.00	\N	\N	\N	\N
17_523	202	1.00	\N	\N	\N	\N
17_523	199	1.00	\N	\N	\N	\N
17_524	217	16.00	\N	\N	\N	\N
17_524	191	2.00	\N	\N	\N	\N
17_524	193	8.00	\N	\N	\N	\N
17_524	201	1.00	\N	\N	\N	\N
17_524	202	1.00	\N	\N	\N	\N
17_524	199	1.00	\N	\N	\N	\N
17_525	217	16.00	\N	\N	\N	\N
17_525	191	2.00	\N	\N	\N	\N
17_525	193	8.00	\N	\N	\N	\N
17_525	201	1.00	\N	\N	\N	\N
17_525	202	1.00	\N	\N	\N	\N
17_525	199	1.00	\N	\N	\N	\N
17_478	217	16.00	\N	\N	\N	\N
17_478	191	2.00	\N	\N	\N	\N
17_478	193	8.00	\N	\N	\N	\N
17_478	201	1.00	\N	\N	\N	\N
17_478	202	1.00	\N	\N	\N	\N
17_479	217	16.00	\N	\N	\N	\N
17_479	191	2.00	\N	\N	\N	\N
17_479	193	8.00	\N	\N	\N	\N
17_479	201	1.00	\N	\N	\N	\N
17_479	202	1.00	\N	\N	\N	\N
17_480	217	16.00	\N	\N	\N	\N
17_480	191	2.00	\N	\N	\N	\N
17_480	193	8.00	\N	\N	\N	\N
17_480	201	1.00	\N	\N	\N	\N
17_480	202	1.00	\N	\N	\N	\N
17_481	217	16.00	\N	\N	\N	\N
17_481	191	2.00	\N	\N	\N	\N
17_481	193	8.00	\N	\N	\N	\N
17_481	201	1.00	\N	\N	\N	\N
17_481	202	1.00	\N	\N	\N	\N
17_482	217	16.00	\N	\N	\N	\N
17_482	191	2.00	\N	\N	\N	\N
17_482	193	8.00	\N	\N	\N	\N
17_482	201	1.00	\N	\N	\N	\N
17_482	202	1.00	\N	\N	\N	\N
17_483	217	16.00	\N	\N	\N	\N
17_483	191	2.00	\N	\N	\N	\N
17_483	193	8.00	\N	\N	\N	\N
17_483	201	1.00	\N	\N	\N	\N
17_483	202	1.00	\N	\N	\N	\N
17_484	217	16.00	\N	\N	\N	\N
17_484	191	2.00	\N	\N	\N	\N
17_484	193	8.00	\N	\N	\N	\N
17_484	201	1.00	\N	\N	\N	\N
17_484	202	1.00	\N	\N	\N	\N
17_485	217	16.00	\N	\N	\N	\N
17_485	191	2.00	\N	\N	\N	\N
17_485	193	8.00	\N	\N	\N	\N
17_485	201	1.00	\N	\N	\N	\N
17_485	202	1.00	\N	\N	\N	\N
17_486	217	16.00	\N	\N	\N	\N
17_486	191	2.00	\N	\N	\N	\N
17_486	193	8.00	\N	\N	\N	\N
17_486	201	1.00	\N	\N	\N	\N
17_486	202	1.00	\N	\N	\N	\N
17_487	217	16.00	\N	\N	\N	\N
17_487	191	2.00	\N	\N	\N	\N
17_487	193	8.00	\N	\N	\N	\N
17_487	201	1.00	\N	\N	\N	\N
17_487	202	1.00	\N	\N	\N	\N
17_488	217	16.00	\N	\N	\N	\N
17_488	191	2.00	\N	\N	\N	\N
17_488	193	8.00	\N	\N	\N	\N
17_488	201	1.00	\N	\N	\N	\N
17_488	202	1.00	\N	\N	\N	\N
17_489	217	16.00	\N	\N	\N	\N
17_489	191	2.00	\N	\N	\N	\N
17_489	193	8.00	\N	\N	\N	\N
17_489	201	1.00	\N	\N	\N	\N
17_489	202	1.00	\N	\N	\N	\N
17_490	217	16.00	\N	\N	\N	\N
17_490	191	2.00	\N	\N	\N	\N
17_490	193	8.00	\N	\N	\N	\N
17_490	201	1.00	\N	\N	\N	\N
17_490	202	1.00	\N	\N	\N	\N
17_491	217	16.00	\N	\N	\N	\N
17_491	191	2.00	\N	\N	\N	\N
17_491	193	8.00	\N	\N	\N	\N
17_491	201	1.00	\N	\N	\N	\N
17_491	202	1.00	\N	\N	\N	\N
17_492	217	16.00	\N	\N	\N	\N
17_492	191	2.00	\N	\N	\N	\N
17_492	193	8.00	\N	\N	\N	\N
17_492	201	1.00	\N	\N	\N	\N
17_492	202	1.00	\N	\N	\N	\N
17_493	217	16.00	\N	\N	\N	\N
17_493	191	2.00	\N	\N	\N	\N
17_493	193	8.00	\N	\N	\N	\N
17_493	201	1.00	\N	\N	\N	\N
17_493	202	1.00	\N	\N	\N	\N
17_494	217	16.00	\N	\N	\N	\N
17_494	191	2.00	\N	\N	\N	\N
17_494	193	8.00	\N	\N	\N	\N
17_494	201	1.00	\N	\N	\N	\N
17_494	202	1.00	\N	\N	\N	\N
17_495	217	16.00	\N	\N	\N	\N
17_495	191	2.00	\N	\N	\N	\N
17_495	193	8.00	\N	\N	\N	\N
17_495	201	1.00	\N	\N	\N	\N
17_495	202	1.00	\N	\N	\N	\N
17_496	217	16.00	\N	\N	\N	\N
17_496	191	2.00	\N	\N	\N	\N
17_496	193	8.00	\N	\N	\N	\N
17_496	201	1.00	\N	\N	\N	\N
17_496	202	1.00	\N	\N	\N	\N
17_497	217	16.00	\N	\N	\N	\N
17_497	191	2.00	\N	\N	\N	\N
17_497	193	8.00	\N	\N	\N	\N
17_497	201	1.00	\N	\N	\N	\N
17_497	202	1.00	\N	\N	\N	\N
17_498	217	16.00	\N	\N	\N	\N
17_498	191	2.00	\N	\N	\N	\N
17_498	193	8.00	\N	\N	\N	\N
17_498	201	1.00	\N	\N	\N	\N
17_498	202	1.00	\N	\N	\N	\N
17_499	217	16.00	\N	\N	\N	\N
17_499	191	2.00	\N	\N	\N	\N
17_499	193	8.00	\N	\N	\N	\N
17_499	201	1.00	\N	\N	\N	\N
17_499	202	1.00	\N	\N	\N	\N
17_500	217	16.00	\N	\N	\N	\N
17_500	191	2.00	\N	\N	\N	\N
17_500	193	8.00	\N	\N	\N	\N
17_500	201	1.00	\N	\N	\N	\N
17_500	202	1.00	\N	\N	\N	\N
17_501	217	16.00	\N	\N	\N	\N
17_501	191	2.00	\N	\N	\N	\N
17_501	193	8.00	\N	\N	\N	\N
17_501	201	1.00	\N	\N	\N	\N
17_501	202	1.00	\N	\N	\N	\N
17_454	194	1.00	\N	\N	\N	\N
17_455	194	1.00	\N	\N	\N	\N
17_456	194	1.00	\N	\N	\N	\N
17_457	194	1.00	\N	\N	\N	\N
17_458	194	1.00	\N	\N	\N	\N
17_459	194	1.00	\N	\N	\N	\N
17_460	194	1.00	\N	\N	\N	\N
17_461	194	1.00	\N	\N	\N	\N
17_462	194	1.00	\N	\N	\N	\N
17_463	194	1.00	\N	\N	\N	\N
17_464	194	1.00	\N	\N	\N	\N
17_465	194	1.00	\N	\N	\N	\N
17_466	194	1.00	\N	\N	\N	\N
17_467	194	1.00	\N	\N	\N	\N
17_468	194	1.00	\N	\N	\N	\N
17_469	194	1.00	\N	\N	\N	\N
17_470	194	1.00	\N	\N	\N	\N
17_471	194	1.00	\N	\N	\N	\N
17_472	194	1.00	\N	\N	\N	\N
17_473	194	1.00	\N	\N	\N	\N
17_474	194	1.00	\N	\N	\N	\N
17_475	194	1.00	\N	\N	\N	\N
17_476	194	1.00	\N	\N	\N	\N
17_477	194	1.00	\N	\N	\N	\N
17_430	196	1.00	\N	\N	\N	\N
17_431	196	1.00	\N	\N	\N	\N
17_432	196	1.00	\N	\N	\N	\N
17_433	196	1.00	\N	\N	\N	\N
17_434	196	1.00	\N	\N	\N	\N
17_435	196	1.00	\N	\N	\N	\N
17_436	196	1.00	\N	\N	\N	\N
17_437	196	1.00	\N	\N	\N	\N
17_438	196	1.00	\N	\N	\N	\N
17_439	196	1.00	\N	\N	\N	\N
17_440	196	1.00	\N	\N	\N	\N
17_441	196	1.00	\N	\N	\N	\N
17_442	196	1.00	\N	\N	\N	\N
17_443	196	1.00	\N	\N	\N	\N
17_444	196	1.00	\N	\N	\N	\N
17_445	196	1.00	\N	\N	\N	\N
17_446	196	1.00	\N	\N	\N	\N
17_447	196	1.00	\N	\N	\N	\N
17_448	196	1.00	\N	\N	\N	\N
17_449	196	1.00	\N	\N	\N	\N
17_450	196	1.00	\N	\N	\N	\N
17_451	196	1.00	\N	\N	\N	\N
17_452	196	1.00	\N	\N	\N	\N
17_453	196	1.00	\N	\N	\N	\N
17_406	197	0.20	\N	\N	\N	\N
17_407	197	0.20	\N	\N	\N	\N
17_408	197	0.20	\N	\N	\N	\N
17_409	197	0.20	\N	\N	\N	\N
17_410	197	0.20	\N	\N	\N	\N
17_411	197	0.20	\N	\N	\N	\N
17_412	197	0.20	\N	\N	\N	\N
17_413	197	0.20	\N	\N	\N	\N
17_414	197	0.20	\N	\N	\N	\N
17_415	197	0.20	\N	\N	\N	\N
17_416	197	0.20	\N	\N	\N	\N
17_417	197	0.20	\N	\N	\N	\N
17_418	197	0.20	\N	\N	\N	\N
17_419	197	0.20	\N	\N	\N	\N
17_421	197	0.20	\N	\N	\N	\N
17_420	197	0.20	\N	\N	\N	\N
17_422	197	0.20	\N	\N	\N	\N
17_423	197	0.20	\N	\N	\N	\N
17_424	197	0.20	\N	\N	\N	\N
17_425	197	0.20	\N	\N	\N	\N
17_426	197	0.20	\N	\N	\N	\N
17_427	197	0.20	\N	\N	\N	\N
17_428	197	0.20	\N	\N	\N	\N
17_429	197	0.20	\N	\N	\N	\N
17_77	217	8.00	\N	\N	\N	\N
17_77	191	1.00	\N	\N	\N	\N
17_77	213	1.00	\N	\N	\N	\N
17_77	214	1.00	\N	\N	\N	\N
17_77	199	1.00	\N	\N	\N	\N
17_82	217	8.00	\N	\N	\N	\N
17_82	191	1.00	\N	\N	\N	\N
17_82	193	4.00	\N	\N	\N	\N
17_82	213	1.00	\N	\N	\N	\N
17_82	214	1.00	\N	\N	\N	\N
17_82	199	1.00	\N	\N	\N	\N
17_81	217	18.00	\N	\N	\N	\N
17_81	191	1.00	\N	\N	\N	\N
17_81	193	6.00	\N	\N	\N	\N
17_81	205	1.00	\N	\N	\N	\N
17_94	217	4.00	\N	\N	\N	\N
17_94	191	1.00	\N	\N	\N	\N
17_94	193	1.00	\N	\N	\N	\N
17_94	213	1.00	\N	\N	\N	\N
17_94	214	1.00	\N	\N	\N	\N
17_94	199	1.00	\N	\N	\N	\N
17_95	217	18.00	\N	\N	\N	\N
17_95	191	1.00	\N	\N	\N	\N
17_95	193	6.00	\N	\N	\N	\N
17_95	205	1.00	\N	\N	\N	\N
17_100	217	5.00	\N	\N	\N	\N
17_100	191	1.00	\N	\N	\N	\N
17_100	193	4.00	\N	\N	\N	\N
17_100	200	1.00	\N	\N	\N	\N
17_101	217	5.00	\N	\N	\N	\N
17_101	191	1.00	\N	\N	\N	\N
17_101	193	4.00	\N	\N	\N	\N
17_101	200	1.00	\N	\N	\N	\N
17_102	217	5.00	\N	\N	\N	\N
17_102	191	1.00	\N	\N	\N	\N
17_102	193	3.00	\N	\N	\N	\N
17_102	200	1.00	\N	\N	\N	\N
17_105	217	10.00	\N	\N	\N	\N
17_105	191	1.00	\N	\N	\N	\N
17_105	204	1.00	\N	\N	\N	\N
17_105	199	1.00	\N	\N	\N	\N
17_106	217	18.00	\N	\N	\N	\N
17_106	191	1.00	\N	\N	\N	\N
17_106	193	3.00	\N	\N	\N	\N
17_106	200	1.00	\N	\N	\N	\N
17_107	217	12.00	\N	\N	\N	\N
17_107	197	1.00	\N	\N	\N	\N
17_108	217	22.00	\N	\N	\N	\N
17_108	191	1.00	\N	\N	\N	\N
17_108	211	1.00	\N	\N	\N	\N
17_109	194	2.00	\N	\N	\N	\N
17_110	217	22.00	\N	\N	\N	\N
17_110	191	1.00	\N	\N	\N	\N
17_110	193	4.00	\N	\N	\N	\N
17_110	211	1.00	\N	\N	\N	\N
17_111	193	4.00	\N	\N	\N	\N
17_112	217	22.00	\N	\N	\N	\N
17_112	191	1.00	\N	\N	\N	\N
17_112	193	4.00	\N	\N	\N	\N
17_112	211	1.00	\N	\N	\N	\N
17_126	217	5.00	\N	\N	\N	\N
17_126	191	1.00	\N	\N	\N	\N
17_126	193	3.00	\N	\N	\N	\N
17_126	200	1.00	\N	\N	\N	\N
17_130	217	6.00	\N	\N	\N	\N
17_130	191	1.00	\N	\N	\N	\N
17_130	203	1.00	\N	\N	\N	\N
17_131	217	6.00	\N	\N	\N	\N
17_131	191	1.00	\N	\N	\N	\N
17_131	203	1.00	\N	\N	\N	\N
17_131	199	2.00	\N	\N	\N	\N
17_133	217	18.00	\N	\N	\N	\N
17_133	191	1.00	\N	\N	\N	\N
17_133	193	4.00	\N	\N	\N	\N
17_133	208	1.00	\N	\N	\N	\N
17_134	217	18.00	\N	\N	\N	\N
17_134	191	1.00	\N	\N	\N	\N
17_134	193	4.00	\N	\N	\N	\N
17_134	208	1.00	\N	\N	\N	\N
17_193	217	12.00	\N	\N	\N	\N
17_193	192	8.00	\N	\N	\N	\N
17_193	199	1.00	\N	\N	\N	\N
17_193	193	1.00	\N	\N	\N	\N
17_137	217	16.00	\N	\N	\N	\N
17_137	193	4.00	\N	\N	\N	\N
17_137	215	2.00	\N	\N	\N	\N
17_138	217	14.00	\N	\N	\N	\N
17_138	193	4.00	\N	\N	\N	\N
17_138	216	1.00	\N	\N	\N	\N
17_139	197	1.00	\N	\N	\N	\N
17_140	217	13.00	\N	\N	\N	\N
17_140	193	4.00	\N	\N	\N	\N
17_140	216	1.00	\N	\N	\N	\N
17_140	199	1.00	\N	\N	\N	\N
17_141	195	1.00	\N	\N	\N	\N
17_194	197	1.00	\N	\N	\N	\N
17_149	217	17.00	\N	\N	\N	\N
17_149	191	1.00	\N	\N	\N	\N
17_149	193	4.00	\N	\N	\N	\N
17_149	207	1.00	\N	\N	\N	\N
17_150	217	13.00	\N	\N	\N	\N
17_150	193	3.00	\N	\N	\N	\N
17_150	216	1.00	\N	\N	\N	\N
17_195	195	1.00	\N	\N	\N	\N
17_151	217	12.00	\N	\N	\N	\N
17_151	191	1.00	\N	\N	\N	\N
17_151	193	6.00	\N	\N	\N	\N
17_151	209	1.00	\N	\N	\N	\N
17_152	217	20.00	\N	\N	\N	\N
17_152	193	6.00	\N	\N	\N	\N
17_153	195	1.00	\N	\N	\N	\N
17_154	197	1.00	\N	\N	\N	\N
17_157	217	5.00	\N	\N	\N	\N
17_157	191	1.00	\N	\N	\N	\N
17_157	200	1.00	\N	\N	\N	\N
17_158	217	5.00	\N	\N	\N	\N
17_158	191	1.00	\N	\N	\N	\N
17_158	200	1.00	\N	\N	\N	\N
18_3	218	1.00	\N	\N	\N	\N
18_4	219	1.00	\N	\N	\N	\N
18_5	219	1.00	\N	\N	\N	\N
18_6	219	1.00	\N	\N	\N	\N
18_7	219	1.00	\N	\N	\N	\N
18_8	219	1.00	\N	\N	\N	\N
18_9	219	1.00	\N	\N	\N	\N
18_10	219	1.00	\N	\N	\N	\N
18_11	218	1.00	\N	\N	\N	\N
18_13	218	1.00	\N	\N	\N	\N
18_14	218	1.00	\N	\N	\N	\N
18_15	218	1.00	\N	\N	\N	\N
18_16	218	1.00	\N	\N	\N	\N
18_17	218	1.00	\N	\N	\N	\N
18_19	218	1.00	\N	\N	\N	\N
18_25	218	1.00	\N	\N	\N	\N
18_36	220	1.00	\N	\N	\N	\N
18_37	219	1.00	\N	\N	\N	\N
18_39	221	1.00	\N	\N	\N	\N
18_41	222	1.00	\N	\N	\N	\N
18_42	222	1.00	\N	\N	\N	\N
18_43	222	1.00	\N	\N	\N	\N
18_44	222	1.00	\N	\N	\N	\N
18_45	222	1.00	\N	\N	\N	\N
18_46	222	1.00	\N	\N	\N	\N
19_1	223	3.00	\N	\N	\N	\N
19_2	223	2.00	\N	\N	\N	\N
19_3	223	3.00	\N	\N	\N	\N
19_4	223	2.00	\N	\N	\N	\N
19_5	223	3.00	\N	\N	\N	\N
19_6	223	2.00	\N	\N	\N	\N
19_7	223	3.00	\N	\N	\N	\N
19_8	223	2.00	\N	\N	\N	\N
19_9	223	3.00	\N	\N	\N	\N
19_10	223	2.00	\N	\N	\N	\N
19_11	223	1.00	\N	\N	\N	\N
19_12	223	1.00	\N	\N	\N	\N
19_13	223	2.00	\N	\N	\N	\N
19_14	223	1.00	\N	\N	\N	\N
19_15	223	3.00	\N	\N	\N	\N
19_16	223	3.00	\N	\N	\N	\N
19_17	223	1.00	\N	\N	\N	\N
19_18	223	2.00	\N	\N	\N	\N
19_19	223	1.00	\N	\N	\N	\N
19_20	223	3.00	\N	\N	\N	\N
19_21	223	2.00	\N	\N	\N	\N
19_22	223	2.00	\N	\N	\N	\N
19_23	223	2.00	\N	\N	\N	\N
19_24	223	3.00	\N	\N	\N	\N
19_25	223	2.00	\N	\N	\N	\N
19_26	223	2.00	\N	\N	\N	\N
19_27	223	3.00	\N	\N	\N	\N
19_28	223	3.00	\N	\N	\N	\N
19_29	223	3.00	\N	\N	\N	\N
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tasks (id, project_id, task_name, task_type, status, baseline_start, type, base_cost, total_cost, risk_factor, duration_months, duration_weeks, duration_days, duration_hours, calendar_type, internal_labor_cost, overtime_cost, equipment_fuel_cost, qa_qc_cost, material_cost, outsourcing_cost, training_cost, facility_rent, communication_cost, utilities_cost, insurance_cost, licensing_cost, warranty_cost, complexity, weather_contingency, general_contingency, rework_risk, holding_cost, international_freight, handling_cost, reverse_logistics, defect_cost, overtime_hours, lag_time, metadata_json) FROM stdin;
15_18	15	Final agreement with supplier	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_305	17	Installation of the jacket foundations 17	\N	Pending	2013-08-27 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_306	17	Installation of the jacket foundations 18	\N	Pending	2013-09-05 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_307	17	Installation of the jacket foundations 19	\N	Pending	2013-09-14 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_308	17	Installation of the jacket foundations 20	\N	Pending	2013-09-23 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_309	17	Installation of the jacket foundations 21	\N	Pending	2013-10-02 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_31	17	Transport (Hoboken to Vlissingen) 1	\N	Pending	2013-04-03 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_310	17	Installation of the jacket foundations 22	\N	Pending	2013-10-11 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_311	17	Installation of the jacket foundations 23	\N	Pending	2013-10-20 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_312	17	Installation of the jacket foundations 24	\N	Pending	2013-10-29 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_313	17	Transport of the jacket foundations 1	\N	Pending	2013-05-04 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_314	17	Transport of the jacket foundations 2	\N	Pending	2013-05-03 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_315	17	Transport of the jacket foundations 3	\N	Pending	2013-04-29 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_316	17	Transport of the jacket foundations 4	\N	Pending	2013-05-02 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_317	17	Transport of the jacket foundations 5	\N	Pending	2013-05-14 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_318	17	Transport of the jacket foundations 6	\N	Pending	2013-05-19 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_319	17	Transport of the jacket foundations 7	\N	Pending	2013-05-28 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_320	17	Transport of the jacket foundations 8	\N	Pending	2013-06-06 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_321	17	Transport of the jacket foundations 9	\N	Pending	2013-06-15 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_322	17	Transport of the jacket foundations 10	\N	Pending	2013-06-24 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_323	17	Transport of the jacket foundations 11	\N	Pending	2013-07-03 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_324	17	Transport of the jacket foundations 12	\N	Pending	2013-07-12 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_325	17	Transport of the jacket foundations 13	\N	Pending	2013-07-21 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_326	17	Transport of the jacket foundations 14	\N	Pending	2013-07-30 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_327	17	Transport of the jacket foundations 15	\N	Pending	2013-08-08 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_328	17	Transport of the jacket foundations 16	\N	Pending	2013-08-17 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_329	17	Transport of the jacket foundations 17	\N	Pending	2013-08-26 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_330	17	Transport of the jacket foundations 18	\N	Pending	2013-09-04 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_331	17	Transport of the jacket foundations 19	\N	Pending	2013-09-13 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_332	17	Transport of the jacket foundations 20	\N	Pending	2013-09-22 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_333	17	Transport of the jacket foundations 21	\N	Pending	2013-10-01 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_334	17	Transport of the jacket foundations 22	\N	Pending	2013-10-10 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_335	17	Transport of the jacket foundations 23	\N	Pending	2013-10-19 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_336	17	Transport of the jacket foundations 24	\N	Pending	2013-10-28 06:00:00	\N	44800.00	56000.00	1.2500	0.00	0.00	1.00	16.00	\N	24800.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_14	16	Manhole covers	\N	Pending	2012-05-04 07:00:00	\N	4575.00	5718.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	1575.00	0.00	3000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_49	16	Topsoil removal and clearing subbase	\N	Pending	2012-11-20 07:00:00	\N	5535.00	6918.75	1.2500	0.00	0.00	3.00	0.00	\N	0.00	0.00	5535.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_12	16	Culverts concrete aging	\N	Pending	2012-05-07 07:00:00	\N	0.00	0.00	1.2500	0.00	0.00	10.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_17	16	Digging	\N	Pending	2012-05-30 07:00:00	\N	49392.00	61740.00	1.2500	0.00	0.00	8.00	0.00	\N	0.00	0.00	49392.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_19	16	Road embankments	\N	Pending	2012-05-07 07:00:00	\N	162865.00	203581.25	1.2500	0.00	0.00	17.00	0.00	\N	0.00	0.00	107865.00	0.00	55000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_2	16	Clearing site	\N	Pending	2012-04-13 07:00:00	\N	4860.00	6075.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	4860.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_20	16	Sound barriers	\N	Pending	2012-05-30 07:00:00	\N	26150.00	32687.50	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	3150.00	0.00	23000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_22	16	Longitudinal drains (ditches)	\N	Pending	2012-06-11 07:00:00	\N	13785.00	17231.25	1.2500	0.00	0.00	5.00	0.00	\N	0.00	0.00	12285.00	0.00	1500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_24	16	Plinths excavation	\N	Pending	2012-06-18 07:00:00	\N	2772.00	3465.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	2772.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_25	16	Pouring piles frameworks and drilling	\N	Pending	2012-06-19 07:00:00	\N	204580.00	255725.00	1.2500	0.00	0.00	4.00	0.00	\N	0.00	0.00	14580.00	0.00	190000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_26	16	Piles concrete aging	\N	Pending	2012-06-25 07:00:00	\N	0.00	0.00	1.2500	0.00	0.00	10.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_27	16	Making of plinths (pouring frameworks and concrete casting)	\N	Pending	2012-07-09 07:00:00	\N	104860.00	131075.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	4860.00	0.00	100000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_28	16	Plinths concrete aging	\N	Pending	2012-07-11 07:00:00	\N	0.00	0.00	1.2500	0.00	0.00	10.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_29	16	Making of pylons (pouring frameworks and concrete casting)	\N	Pending	2012-07-25 07:00:00	\N	13430.00	16787.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	2430.00	0.00	11000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_3	16	Levelling ground	\N	Pending	2012-04-17 07:00:00	\N	1845.00	2306.25	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	1845.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_30	16	Pylons concrete aging	\N	Pending	2012-07-26 07:00:00	\N	0.00	0.00	1.2500	0.00	0.00	10.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_31	16	Making of shoulders (pouring frameworks and concrete casting)	\N	Pending	2012-08-09 07:00:00	\N	83430.00	104287.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	2430.00	0.00	81000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_32	16	Shoulders concrete aging	\N	Pending	2012-08-10 07:00:00	\N	0.00	0.00	1.2500	0.00	0.00	10.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_33	16	Pouring prefabricated beam	\N	Pending	2012-08-24 07:00:00	\N	53575.00	66968.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	1575.00	0.00	52000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_34	16	Making of slab (pouring frameworks and concrete casting)	\N	Pending	2012-08-27 07:00:00	\N	25930.00	32412.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	2430.00	0.00	23500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_35	16	Slab's concrete aging	\N	Pending	2012-08-28 07:00:00	\N	0.00	0.00	1.2500	0.00	0.00	10.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_36	16	Making of embankments	\N	Pending	2012-09-11 07:00:00	\N	54720.00	68400.00	1.2500	0.00	0.00	12.00	0.00	\N	0.00	0.00	36720.00	0.00	18000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_38	16	Embankments	\N	Pending	2012-06-26 07:00:00	\N	189155.00	236443.75	1.2500	0.00	0.00	19.00	0.00	\N	0.00	0.00	120555.00	0.00	68600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_39	16	Sound barriers	\N	Pending	2012-07-23 07:00:00	\N	15750.00	19687.50	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	3150.00	0.00	12600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_4	16	Containers placement	\N	Pending	2012-04-18 07:00:00	\N	1575.00	1968.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	1575.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_41	16	Demolitions	\N	Pending	2012-06-18 07:00:00	\N	3330.00	4162.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	3330.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_42	16	Topsoil removal and clearing subbase	\N	Pending	2012-06-19 07:00:00	\N	9225.00	11531.25	1.2500	0.00	0.00	5.00	0.00	\N	0.00	0.00	9225.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_46	16	Embankments	\N	Pending	2012-11-23 07:00:00	\N	93920.00	117400.00	1.2500	0.00	0.00	10.00	0.00	\N	0.00	0.00	61920.00	0.00	32000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_48	16	Demolitions	\N	Pending	2012-11-19 07:00:00	\N	3330.00	4162.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	3330.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_5	16	Connection to network service	\N	Pending	2012-04-19 07:00:00	\N	1260.00	1575.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	1260.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_51	16	Carrying remaining soil	\N	Pending	2013-01-01 07:00:00	\N	44352.00	55440.00	1.2500	0.00	0.00	8.00	0.00	\N	0.00	0.00	44352.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_52	16	Terracing	\N	Pending	2012-12-24 07:00:00	\N	28284.00	35355.00	1.2500	0.00	0.00	6.00	0.00	\N	0.00	0.00	13284.00	0.00	15000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_55	16	Draining trenches	\N	Pending	2013-01-11 07:00:00	\N	38285.00	47856.25	1.2500	0.00	0.00	5.00	0.00	\N	0.00	0.00	12285.00	0.00	26000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_56	16	Catch water drains	\N	Pending	2013-01-18 07:00:00	\N	34696.00	43370.00	1.2500	0.00	0.00	8.00	0.00	\N	0.00	0.00	24696.00	0.00	10000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_58	16	Demolitions	\N	Pending	2012-12-10 07:00:00	\N	3330.00	4162.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	3330.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_59	16	Topsoil removal and clearing subbase	\N	Pending	2012-12-11 07:00:00	\N	22275.00	27843.75	1.2500	0.00	0.00	9.00	0.00	\N	0.00	0.00	22275.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_6	16	Pegging road	\N	Pending	2012-04-23 07:00:00	\N	30630.00	38287.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	630.00	0.00	30000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_62	16	Catch water drains	\N	Pending	2012-07-25 07:00:00	\N	24261.00	30326.25	1.2500	0.00	0.00	3.00	0.00	\N	0.00	0.00	9261.00	0.00	15000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_63	16	Manhole covers	\N	Pending	2012-06-19 07:00:00	\N	7575.00	9468.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	1575.00	0.00	6000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_337	17	Assembly of midsection 2	\N	Pending	2013-03-25 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_66	16	Retaining walls (frameworks and concrete casting)	\N	Pending	2012-07-30 07:00:00	\N	90430.00	113037.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	2430.00	0.00	88000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_67	16	Retaining walls concrete aging	\N	Pending	2012-07-31 07:00:00	\N	0.00	0.00	1.2500	0.00	0.00	10.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_68	16	Pouring prefabricated beams	\N	Pending	2012-08-14 07:00:00	\N	51575.00	64468.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	1575.00	0.00	50000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_69	16	Making of slabs (frameworks pouring and concrete casting)	\N	Pending	2012-08-15 07:00:00	\N	9575.00	11968.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	1575.00	0.00	8000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_7	16	Alternative road system	\N	Pending	2012-04-24 07:00:00	\N	72860.00	91075.00	1.2500	0.00	0.00	4.00	0.00	\N	0.00	0.00	22860.00	0.00	50000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_70	16	Slabs concrete aging	\N	Pending	2012-08-16 07:00:00	\N	0.00	0.00	1.2500	0.00	0.00	10.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_72	16	Carrying remaining soil	\N	Pending	2012-11-16 07:00:00	\N	6192.00	7740.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	6192.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_73	16	Terracing	\N	Pending	2012-11-15 07:00:00	\N	4014.00	5017.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	2214.00	0.00	1800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_75	16	Embankments	\N	Pending	2012-09-18 07:00:00	\N	400064.00	500080.00	1.2500	0.00	0.00	42.00	0.00	\N	0.00	0.00	260064.00	0.00	140000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_77	16	Draining trenches	\N	Pending	2012-11-15 07:00:00	\N	8514.00	10642.50	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	4914.00	0.00	3600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_78	16	Catch water drains	\N	Pending	2012-11-15 07:00:00	\N	23087.00	28858.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	3087.00	0.00	20000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_8	16	Demolition	\N	Pending	2012-04-30 07:00:00	\N	2727.00	3408.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	2727.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_80	16	Culverts	\N	Pending	2012-09-18 07:00:00	\N	10150.00	12687.50	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	3150.00	0.00	7000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_82	16	Demolitions	\N	Pending	2012-08-30 07:00:00	\N	3330.00	4162.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	3330.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_83	16	Topsoil removal and subbase clearing	\N	Pending	2012-08-31 07:00:00	\N	29700.00	37125.00	1.2500	0.00	0.00	12.00	0.00	\N	0.00	0.00	29700.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_85	16	Paving	\N	Pending	2013-01-30 07:00:00	\N	2628250.00	3285312.50	1.2500	0.00	0.00	30.00	0.00	\N	0.00	0.00	128250.00	0.00	2500000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_86	16	Guardrails pouring	\N	Pending	2013-03-13 07:00:00	\N	328674.00	410842.50	1.2500	0.00	0.00	27.00	0.00	\N	0.00	0.00	28674.00	0.00	300000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_87	16	Coverage and shaping slopes	\N	Pending	2013-03-13 07:00:00	\N	39300.00	49125.00	1.2500	0.00	0.00	9.00	0.00	\N	0.00	0.00	24300.00	0.00	15000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_88	16	Cascades pouring	\N	Pending	2013-03-26 07:00:00	\N	19020.00	23775.00	1.2500	0.00	0.00	4.00	0.00	\N	0.00	0.00	2520.00	0.00	16500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_89	16	Road signals pouring	\N	Pending	2013-03-13 07:00:00	\N	81800.00	102250.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	1800.00	0.00	80000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_9	16	Clearing subbase and topsoil removal	\N	Pending	2012-04-30 07:00:00	\N	7380.00	9225.00	1.2500	0.00	0.00	4.00	0.00	\N	0.00	0.00	7380.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_91	16	Network connections removal	\N	Pending	2013-04-19 07:00:00	\N	630.00	787.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	630.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_92	16	Containers removal	\N	Pending	2013-04-19 07:00:00	\N	1575.00	1968.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	1575.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_93	16	Rubbles removal	\N	Pending	2013-04-22 07:00:00	\N	4680.00	5850.00	1.2500	0.00	0.00	4.00	0.00	\N	0.00	0.00	4680.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_94	16	Fences removal	\N	Pending	2013-04-26 07:00:00	\N	630.00	787.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	630.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_1	17	Fabrication of pre-piling template	\N	Pending	2013-04-20 06:00:00	\N	1044000.00	1305000.00	1.2500	0.00	0.00	15.00	240.00	\N	0.00	0.00	0.00	0.00	626400.00	417600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_100	17	Rock dumping as scour protection around the OTS foundation	\N	Pending	2013-09-18 07:00:00	\N	241280.00	301600.00	1.2500	0.00	0.00	2.00	32.00	\N	135040.00	0.00	106240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_101	17	GOSA mattresses installations above existing underground cables as protection	\N	Pending	2013-09-20 07:00:00	\N	1447680.00	1809600.00	1.2500	0.00	0.00	12.00	192.00	\N	810240.00	0.00	637440.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_102	17	Pre-grapnel run to remove obstacles from cable trajectories	\N	Pending	2013-10-02 07:00:00	\N	236160.00	295200.00	1.2500	0.00	0.00	2.00	32.00	\N	129920.00	0.00	106240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_105	17	Transport	\N	Pending	2013-06-06 06:00:00	\N	715800.00	758748.00	1.0600	0.00	0.00	5.00	80.00	\N	312800.00	0.00	276000.00	0.00	127000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_106	17	Pre-grapnel runs to remove obstacles	\N	Pending	2013-06-11 06:00:00	\N	126400.00	158000.00	1.2500	0.00	0.00	1.00	16.00	\N	73280.00	0.00	53120.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_107	17	Wet trials	\N	Pending	2013-06-12 06:00:00	\N	58080.00	72600.00	1.2500	0.00	0.00	1.00	16.00	\N	20480.00	0.00	0.00	0.00	37600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_108	17	Cable laying works	\N	Pending	2013-10-31 06:00:00	\N	5713920.00	7142400.00	1.2500	0.00	0.00	48.00	768.00	\N	3217920.00	0.00	2496000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_109	17	Final hang off of the cables in the WTG foundations	\N	Pending	2013-11-05 06:00:00	\N	1228800.00	1536000.00	1.2500	0.00	0.00	48.00	768.00	\N	1228800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_11	17	Continious delivery of pin-piles	\N	Pending	2013-03-01 06:00:00	\N	19200.00	24000.00	1.2500	0.00	0.00	25.00	400.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	3840.00	15360.00	0.00	0.00	0.00	0.00	\N	{}
17_110	17	Burial of cables	\N	Pending	2013-12-23 06:00:00	\N	1292800.00	1616000.00	1.2500	0.00	0.00	10.00	160.00	\N	772800.00	0.00	520000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_111	17	Survey of burial depths	\N	Pending	2014-01-02 06:00:00	\N	20480.00	27648.00	1.3500	0.00	0.00	2.00	32.00	\N	20480.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_112	17	Second remedial burial pass if necessary	\N	Pending	2014-01-04 06:00:00	\N	517120.00	672256.00	1.3000	0.00	0.00	4.00	64.00	\N	309120.00	0.00	208000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.1000	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_12	17	OTS: drive 4 pin-piles for OTS foundation into seabed	\N	Pending	2013-05-17 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_126	17	Pre-lay grapnel run on trajectory	\N	Pending	2013-02-04 06:00:00	\N	236160.00	295200.00	1.2500	0.00	0.00	2.00	32.00	\N	129920.00	0.00	106240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_128	17	Purchase of raw materials	\N	Pending	2013-02-09 06:00:00	\N	1470000.00	1558200.00	1.0600	0.00	0.00	70.00	1120.00	\N	0.00	0.00	0.00	0.00	1470000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_129	17	Manufacturing in Karlskrona Sweden	\N	Pending	2013-03-31 06:00:00	\N	625600.00	663136.00	1.0600	0.00	0.00	40.00	640.00	\N	0.00	0.00	0.00	0.00	625600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_13	17	Turbine1: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-05-21 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_130	17	Mobilisation of Stemat Spirit	\N	Pending	2013-05-05 06:00:00	\N	560570.00	700712.50	1.2500	0.00	0.00	5.00	80.00	\N	284000.00	0.00	260000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	3314.00	13256.00	0.00	0.00	0.00	0.00	\N	{}
17_131	17	Transport Sweden-Ostend	\N	Pending	2013-05-10 06:00:00	\N	501860.00	627325.00	1.2500	0.00	0.00	4.00	64.00	\N	252800.00	0.00	233600.00	0.00	15460.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_133	17	Dredging to widen shipping lane Vaargeul1	\N	Pending	2013-05-04 06:00:00	\N	737600.00	922000.00	1.2500	0.00	0.00	5.00	80.00	\N	369600.00	0.00	256000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	22400.00	89600.00	0.00	0.00	0.00	0.00	\N	{}
17_134	17	Prepare trench where export cable B (150kV) is crossing Vaargeul1	\N	Pending	2013-05-09 06:00:00	\N	844600.00	1055750.00	1.2500	0.00	0.00	5.00	80.00	\N	369600.00	0.00	256000.00	0.00	219000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_136	17	Delivery of pipes to be drilled	\N	Pending	2013-02-18 06:00:00	\N	103570.00	134641.00	1.3000	0.00	0.00	60.00	960.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.1000	0.0000	20714.00	82856.00	0.00	0.00	0.00	0.00	\N	{}
17_137	17	Directional drillings on land	\N	Pending	2013-04-09 06:00:00	\N	1682200.00	2102750.00	1.2500	0.00	0.00	15.00	240.00	\N	883200.00	0.00	576000.00	0.00	223000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_138	17	Pulling welded pipe in through drilling hole	\N	Pending	2013-04-24 06:00:00	\N	182400.00	228000.00	1.2500	0.00	0.00	3.00	48.00	\N	120000.00	0.00	62400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_139	17	Factory Acceptance Tests on land cables	\N	Pending	2013-04-27 06:00:00	\N	38100.00	47625.00	1.2500	0.00	0.00	2.00	32.00	\N	25600.00	0.00	0.00	0.00	12500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_14	17	Turbine2: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-05-25 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_140	17	Cable laying onshore between export cable landing and Elia sub-station	\N	Pending	2013-05-12 06:00:00	\N	351000.00	438750.00	1.2500	0.00	0.00	5.00	80.00	\N	212800.00	0.00	120000.00	0.00	18200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_141	17	Connection of the cables into Elia sub-station	\N	Pending	2013-05-17 06:00:00	\N	80200.00	100250.00	1.2500	0.00	0.00	2.00	32.00	\N	25600.00	0.00	0.00	0.00	54600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_149	17	Export cable laying on sea bed between coast and OTS	\N	Pending	2013-05-14 06:00:00	\N	1244800.00	1556000.00	1.2500	0.00	0.00	10.00	160.00	\N	732800.00	0.00	512000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_150	17	Landfall cable pull	\N	Pending	2013-05-24 06:00:00	\N	57600.00	72000.00	1.2500	0.00	0.00	1.00	16.00	\N	36800.00	0.00	20800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_151	17	Backfilling of cable trench	\N	Pending	2013-05-26 06:00:00	\N	481000.00	601250.00	1.2500	0.00	0.00	3.00	48.00	\N	228000.00	0.00	156000.00	0.00	97000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_152	17	Export cable pull in OTS	\N	Pending	2013-09-18 07:00:00	\N	40660.00	50825.00	1.2500	0.00	0.00	1.00	16.00	\N	28160.00	0.00	0.00	0.00	12500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_153	17	Complete connection of cable conductors and fibre optics	\N	Pending	2013-09-19 07:00:00	\N	38100.00	47625.00	1.2500	0.00	0.00	2.00	32.00	\N	25600.00	0.00	0.00	0.00	12500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_156	17	Delivery of rock on Halve Maan site	\N	Pending	2013-05-28 06:00:00	\N	325000.00	344500.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	65000.00	260000.00	0.00	0.00	0.00	0.00	\N	{}
17_157	17	Mobilizing rock dumping vessel	\N	Pending	2013-05-29 06:00:00	\N	110400.00	138000.00	1.2500	0.00	0.00	1.00	16.00	\N	57280.00	0.00	53120.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_158	17	Rock dumping on PEC crossing and Interconnector South	\N	Pending	2013-05-30 06:00:00	\N	110400.00	138000.00	1.2500	0.00	0.00	1.00	16.00	\N	57280.00	0.00	53120.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_16	17	Dredging and cleaning of pin-piles	\N	Pending	2013-05-19 06:00:00	\N	134080.00	167600.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	53120.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_17	17	Install pin-pile covers on the piles	\N	Pending	2013-05-20 06:00:00	\N	131520.00	164400.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_193	17	Welding pipes together	\N	Pending	2013-04-19 06:00:00	\N	259600.00	275176.00	1.0600	0.00	0.00	5.00	80.00	\N	105600.00	0.00	16000.00	0.00	82800.00	55200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_194	17	Electrical commissioning tests on the onshore cable connections	\N	Pending	2013-05-19 06:00:00	\N	67400.00	90990.00	1.3500	0.00	0.00	1.00	16.00	\N	12800.00	0.00	0.00	54600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_195	17	Making joint between sea cable and land cable	\N	Pending	2013-05-25 06:00:00	\N	25300.00	31625.00	1.2500	0.00	0.00	1.00	16.00	\N	12800.00	0.00	0.00	0.00	12500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_196	17	Turbine3: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-05-29 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_197	17	Turbine4: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-06-02 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_198	17	Turbine5: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-06-06 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
19_18	19	Reparing walls	\N	Pending	2019-06-04 08:00:00	\N	4180.00	5852.00	1.4000	0.00	0.00	2.00	16.00	\N	1280.00	0.00	0.00	0.00	2900.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
17_199	17	Turbine6: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-06-11 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_2	17	Transportation of template and mounting on Jack Up Platform Buzzard	\N	Pending	2013-05-05 06:00:00	\N	58000.00	72500.00	1.2500	0.00	0.00	10.00	160.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	11600.00	46400.00	0.00	0.00	0.00	0.00	\N	{}
17_200	17	Turbine7: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-06-15 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_201	17	Turbine8: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-06-19 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_202	17	Turbine9: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-06-23 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_203	17	Turbine10: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-06-27 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_204	17	Turbine11: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-07-01 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_205	17	Turbine12: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-07-05 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_206	17	Turbine13: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-07-09 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_207	17	Turbine14: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-07-13 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_208	17	Turbine15: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-07-17 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_209	17	Turbine16: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-07-21 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_210	17	Turbine17: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-07-25 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_211	17	Turbine18: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-07-29 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_212	17	Turbine19: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-08-02 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_213	17	Turbine20: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-08-06 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_214	17	Turbine21: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-08-14 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_215	17	Turbine22: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-08-10 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_216	17	Turbine23: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-08-18 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_217	17	Turbine24: drive 4 pin-piles for jacket foundation into seabed	\N	Pending	2013-08-22 06:00:00	\N	265600.00	332000.00	1.2500	0.00	0.00	2.00	32.00	\N	163200.00	0.00	102400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_218	17	Dredging and cleaning of pin-piles 2	\N	Pending	2013-05-27 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_219	17	Dredging and cleaning of pin-piles 3	\N	Pending	2013-05-31 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_220	17	Dredging and cleaning of pin-piles 4	\N	Pending	2013-06-04 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_221	17	Dredging and cleaning of pin-piles 5	\N	Pending	2013-06-08 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_222	17	Dredging and cleaning of pin-piles 6	\N	Pending	2013-06-13 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_223	17	Dredging and cleaning of pin-piles 7	\N	Pending	2013-06-17 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_224	17	Dredging and cleaning of pin-piles 8	\N	Pending	2013-06-21 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_225	17	Dredging and cleaning of pin-piles 9	\N	Pending	2013-06-25 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_226	17	Dredging and cleaning of pin-piles 10	\N	Pending	2013-06-29 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_227	17	Dredging and cleaning of pin-piles 11	\N	Pending	2013-07-03 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_228	17	Dredging and cleaning of pin-piles 12	\N	Pending	2013-07-07 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_229	17	Dredging and cleaning of pin-piles 13	\N	Pending	2013-07-11 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_23	17	Purchase of castings and pile stoppers	\N	Pending	2013-02-04 06:00:00	\N	150000.00	159000.00	1.0600	0.00	0.00	120.00	1920.00	\N	0.00	0.00	0.00	0.00	90000.00	60000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_230	17	Dredging and cleaning of pin-piles 14	\N	Pending	2013-07-15 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_231	17	Dredging and cleaning of pin-piles 15	\N	Pending	2013-07-19 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_232	17	Dredging and cleaning of pin-piles 16	\N	Pending	2013-07-23 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_233	17	Dredging and cleaning of pin-piles 17	\N	Pending	2013-07-27 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_234	17	Dredging and cleaning of pin-piles 18	\N	Pending	2013-07-31 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_235	17	Dredging and cleaning of pin-piles 19	\N	Pending	2013-08-04 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_236	17	Dredging and cleaning of pin-piles 20	\N	Pending	2013-08-08 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_237	17	Dredging and cleaning of pin-piles 21	\N	Pending	2013-08-16 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_238	17	Dredging and cleaning of pin-piles 22	\N	Pending	2013-08-12 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_239	17	Dredging and cleaning of pin-piles 23	\N	Pending	2013-08-20 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_240	17	Dredging and cleaning of pin-piles 24	\N	Pending	2013-08-24 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_241	17	Install pin-pile covers on the piles 1	\N	Pending	2013-05-24 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_242	17	Install pin-pile covers on the piles 2	\N	Pending	2013-05-28 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_243	17	Install pin-pile covers on the piles 3	\N	Pending	2013-06-01 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_244	17	Install pin-pile covers on the piles 4	\N	Pending	2013-06-05 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_245	17	Install pin-pile covers on the piles 5	\N	Pending	2013-06-10 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_246	17	Install pin-pile covers on the piles 6	\N	Pending	2013-06-14 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_247	17	Install pin-pile covers on the piles 7	\N	Pending	2013-06-18 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_248	17	Install pin-pile covers on the piles 8	\N	Pending	2013-06-22 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_249	17	Install pin-pile covers on the piles 9	\N	Pending	2013-06-26 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_25	17	Assembly of midsection 1	\N	Pending	2013-03-16 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_250	17	Install pin-pile covers on the piles 10	\N	Pending	2013-06-30 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_251	17	Install pin-pile covers on the piles 11	\N	Pending	2013-07-04 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_252	17	Install pin-pile covers on the piles 12	\N	Pending	2013-07-08 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_253	17	Install pin-pile covers on the piles 13	\N	Pending	2013-07-12 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_254	17	Install pin-pile covers on the piles 14	\N	Pending	2013-07-16 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_255	17	Install pin-pile covers on the piles 15	\N	Pending	2013-07-20 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_256	17	Install pin-pile covers on the piles 16	\N	Pending	2013-07-24 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_257	17	Install pin-pile covers on the piles 17	\N	Pending	2013-07-28 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_258	17	Install pin-pile covers on the piles 18	\N	Pending	2013-08-01 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_259	17	Install pin-pile covers on the piles 19	\N	Pending	2013-08-05 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_260	17	Install pin-pile covers on the piles 20	\N	Pending	2013-08-09 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_261	17	Install pin-pile covers on the piles 21	\N	Pending	2013-08-17 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_262	17	Install pin-pile covers on the piles 22	\N	Pending	2013-08-13 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_263	17	Install pin-pile covers on the piles 23	\N	Pending	2013-08-21 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_264	17	Install pin-pile covers on the piles 24	\N	Pending	2013-08-25 06:00:00	\N	184120.00	230150.00	1.2500	0.00	0.00	1.00	16.00	\N	80320.00	0.00	51200.00	0.00	31560.00	21040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_266	17	Grouting of foundation to the pin-piles 2	\N	Pending	2013-06-14 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_267	17	Grouting of foundation to the pin-piles 3	\N	Pending	2013-06-18 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_268	17	Grouting of foundation to the pin-piles 4	\N	Pending	2013-06-22 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_269	17	Grouting of foundation to the pin-piles 5	\N	Pending	2013-06-27 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_270	17	Grouting of foundation to the pin-piles 6	\N	Pending	2013-07-01 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_271	17	Grouting of foundation to the pin-piles 7	\N	Pending	2013-07-05 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_272	17	Grouting of foundation to the pin-piles 8	\N	Pending	2013-07-09 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_273	17	Grouting of foundation to the pin-piles 9	\N	Pending	2013-07-13 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_274	17	Grouting of foundation to the pin-piles 10	\N	Pending	2013-07-17 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_275	17	Grouting of foundation to the pin-piles 11	\N	Pending	2013-07-21 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_276	17	Grouting of foundation to the pin-piles 12	\N	Pending	2013-07-25 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_277	17	Grouting of foundation to the pin-piles 13	\N	Pending	2013-07-29 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_278	17	Grouting of foundation to the pin-piles 14	\N	Pending	2013-08-02 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_279	17	Grouting of foundation to the pin-piles 15	\N	Pending	2013-08-10 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_281	17	Grouting of foundation to the pin-piles 17	\N	Pending	2013-08-28 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_282	17	Grouting of foundation to the pin-piles 18	\N	Pending	2013-09-06 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_283	17	Grouting of foundation to the pin-piles 19	\N	Pending	2013-09-15 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_284	17	Grouting of foundation to the pin-piles 20	\N	Pending	2013-09-24 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_285	17	Grouting of foundation to the pin-piles 21	\N	Pending	2013-10-03 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_286	17	Grouting of foundation to the pin-piles 22	\N	Pending	2013-10-12 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_287	17	Grouting of foundation to the pin-piles 23	\N	Pending	2013-10-21 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_288	17	Grouting of foundation to the pin-piles 24	\N	Pending	2013-10-30 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_29	17	Final jacket assembly 1	\N	Pending	2013-03-25 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_290	17	Installation of the jacket foundations 2	\N	Pending	2013-06-13 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_291	17	Installation of the jacket foundations 3	\N	Pending	2013-06-17 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_292	17	Installation of the jacket foundations 4	\N	Pending	2013-06-21 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_293	17	Installation of the jacket foundations 5	\N	Pending	2013-06-26 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_294	17	Installation of the jacket foundations 6	\N	Pending	2013-06-30 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_295	17	Installation of the jacket foundations 7	\N	Pending	2013-07-04 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_6	15	Registering the technical requirements	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_8	15	Putting together the formal document	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	3.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_9	15	Research suppliers transport systems	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	3.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_11	15	Contacting suppliers and sending proposal	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_12	15	Analyzing the received offers	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	3.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_13	15	Presentation to board & ICT staff	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_14	15	Collecting and registering comments on offers	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_15	15	Taking final decision and contacting supplier	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_16	15	Discussing project development with supplier	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	3.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_3	15	Collecting and analyzing the surveys	\N	Pending	\N	\N	0.00	0.00	1.4000	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.1500	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_4	15	Get-together PC, ICT committee & board	\N	Pending	\N	\N	2416.32	3020.40	1.2500	0.00	0.00	0.00	4.00	\N	2416.32	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_1	15	Compose survey for the staff	\N	Pending	\N	\N	125.12	175.17	1.4000	0.00	0.00	0.00	4.00	\N	125.12	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.1500	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_2	15	Brainstorming and filling in the survey	\N	Pending	\N	\N	5137.28	10274.56	2.0000	0.00	0.00	0.00	2.00	\N	5137.28	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.5000	0.0000	0.5000	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_5	15	Enrollment of the meeting	\N	Pending	\N	\N	62.56	78.20	1.2500	0.00	0.00	0.00	2.00	\N	62.56	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_7	15	Set-up a detailed budget study	\N	Pending	\N	\N	0.00	0.00	1.3500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_10	15	Meeting with board for final proposal	\N	Pending	\N	\N	1974.40	2468.00	1.2500	0.00	0.00	0.00	4.00	\N	1974.40	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_17	15	Discussing project development with board	\N	Pending	\N	\N	1863.92	2329.90	1.2500	0.00	0.00	0.00	4.00	\N	1863.92	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_296	17	Installation of the jacket foundations 8	\N	Pending	2013-07-08 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_297	17	Installation of the jacket foundations 9	\N	Pending	2013-07-12 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_298	17	Installation of the jacket foundations 10	\N	Pending	2013-07-16 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_299	17	Installation of the jacket foundations 11	\N	Pending	2013-07-20 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_3	17	Mobilisation of Jack Up Platform Buzzard	\N	Pending	2013-05-15 06:00:00	\N	114240.00	142800.00	1.2500	0.00	0.00	1.00	16.00	\N	63040.00	0.00	51200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_300	17	Installation of the jacket foundations 12	\N	Pending	2013-07-24 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_301	17	Installation of the jacket foundations 13	\N	Pending	2013-07-28 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_24	15	Discussing progress with ICT committee	\N	Pending	\N	\N	677.52	846.90	1.2500	0.00	0.00	0.00	4.00	\N	677.52	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_20	15	Meeting with ICT committee	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_21	15	Contacting Siemens and sending proposal	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	3.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_22	15	Discussing project development with supplier	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_25	15	Final agreement with supplier	\N	Pending	\N	\N	125.12	156.40	1.2500	0.00	0.00	0.00	4.00	\N	125.12	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_26	15	Signing contract	\N	Pending	\N	\N	373.52	466.90	1.2500	0.00	0.00	0.00	4.00	\N	373.52	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	9060.00	9060.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_27	15	Information session	\N	Pending	\N	\N	1208.16	1510.20	1.2500	0.00	0.00	0.00	2.00	\N	1208.16	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_28	15	Explanation project implementation to staff	\N	Pending	\N	\N	5199.84	6499.80	1.2500	0.00	0.00	0.00	2.00	\N	5199.84	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_34	15	Surveying the required functionalities	\N	Pending	\N	\N	0.00	0.00	1.4000	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.1500	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_23	15	Discussing progress with board	\N	Pending	\N	\N	931.96	1164.95	1.2500	0.00	0.00	0.00	2.00	\N	931.96	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_29	15	Installation transport system	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	6.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_30	15	Installation DACS	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	6.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_31	15	Training coordinator	\N	Pending	\N	\N	1000.00	1250.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	1000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_32	15	Train de trainer	\N	Pending	\N	\N	1000.00	1250.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	1000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_33	15	Training rapportage	\N	Pending	\N	\N	500.00	625.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_35	15	Creating codes	\N	Pending	\N	\N	0.00	0.00	1.3500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_47	15	Discussing project with board	\N	Pending	\N	\N	931.96	1164.95	1.2500	0.00	0.00	0.00	2.00	\N	931.96	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_36	15	Registration data about employees	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	4.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_37	15	Registration hospital data	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	6.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_38	15	Training team 1	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_39	15	Training team 2	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_40	15	Training team 3	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_41	15	Training team 4	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_42	15	Training team 5	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_43	15	Training team 6	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	2.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_44	15	Check-up by PC	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_45	15	Check-up by ICT committee	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_46	15	Live pilot period	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	71.00	0.00	\N	0.00	0.00	0.00	0.00	500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_48	15	Discussing project with head nurses	\N	Pending	\N	\N	8257.92	10322.40	1.2500	0.00	0.00	0.00	4.00	\N	8257.92	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_19	15	Signing contract	\N	Pending	\N	\N	373.52	466.90	1.2500	0.00	0.00	0.00	4.00	\N	373.52	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	27500.00	27500.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
15_49	15	Enrollment of the entire project	\N	Pending	\N	\N	0.00	0.00	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.2000	0.0000	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_1	16	Pegging and fence	\N	Pending	2012-04-12 07:00:00	\N	10630.00	13287.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	630.00	0.00	10000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_11	16	Placement formworks and concrete casting	\N	Pending	2012-05-04 07:00:00	\N	5430.00	6787.50	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	2430.00	0.00	3000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
16_44	16	Catch water drains	\N	Pending	2012-12-07 07:00:00	\N	13087.00	16358.75	1.2500	0.00	0.00	1.00	0.00	\N	0.00	0.00	3087.00	0.00	10000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0500	0.1500	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_542	17	Delivery of pin-piles 16	\N	Pending	2013-07-20 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_162	17	Dredging and cleaning of pin-piles 1	\N	Pending	2013-05-23 06:00:00	\N	197080.00	246350.00	1.2500	0.00	0.00	1.00	16.00	\N	80960.00	0.00	72020.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	44100.00	0.00	0.00	0.00	\N	{}
17_21	17	Purshase of tubulars	\N	Pending	2013-02-04 06:00:00	\N	80000.00	84800.00	1.0600	0.00	0.00	120.00	1920.00	\N	0.00	0.00	0.00	0.00	80000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_27	17	Purchase of secondary steel items	\N	Pending	2013-02-13 06:00:00	\N	350000.00	371000.00	1.0600	0.00	0.00	80.00	1280.00	\N	0.00	0.00	0.00	0.00	350000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_289	17	Installation of the jacket foundations 1	\N	Pending	2013-06-09 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_265	17	Grouting of foundation to the pin-piles 1	\N	Pending	2013-06-10 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_280	17	Grouting of foundation to the pin-piles 16	\N	Pending	2013-08-19 06:00:00	\N	252240.00	315300.00	1.2500	0.00	0.00	1.00	16.00	\N	96320.00	0.00	57920.00	0.00	58800.00	39200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_454	17	Terminations of infield cables 1	\N	Pending	2014-01-08 06:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_430	17	Commissioning of wind turbines 1	\N	Pending	2014-01-11 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_406	17	Reliability tests 1	\N	Pending	2014-01-16 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_104	17	Production in Karlskrona Sweden	\N	Pending	2013-02-04 06:00:00	\N	2205000.00	2337300.00	1.0600	0.00	0.00	120.00	1920.00	\N	0.00	0.00	0.00	0.00	2205000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_154	17	Testing 24 hours connection of cable conductors and fibre optics	\N	Pending	2013-09-21 07:00:00	\N	47400.00	63990.00	1.3500	0.00	0.00	1.00	16.00	\N	12800.00	0.00	0.00	34600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_302	17	Installation of the jacket foundations 14	\N	Pending	2013-08-01 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_303	17	Installation of the jacket foundations 15	\N	Pending	2013-08-09 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_304	17	Installation of the jacket foundations 16	\N	Pending	2013-08-18 06:00:00	\N	146240.00	182800.00	1.2500	0.00	0.00	1.00	16.00	\N	88320.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
18_45	18	35. Payment of the construction firm	\N	Pending	2019-07-12 08:00:00	\N	240.00	336.00	1.4000	0.00	0.00	1.00	8.00	\N	240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
17_338	17	Assembly of midsection 3	\N	Pending	2013-04-03 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_339	17	Assembly of midsection 4	\N	Pending	2013-04-12 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_340	17	Assembly of midsection 5	\N	Pending	2013-04-21 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_341	17	Assembly of midsection 6	\N	Pending	2013-04-30 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_342	17	Assembly of midsection 7	\N	Pending	2013-05-09 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_343	17	Assembly of midsection 8	\N	Pending	2013-05-18 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_344	17	Assembly of midsection 9	\N	Pending	2013-05-27 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_345	17	Assembly of midsection 10	\N	Pending	2013-06-05 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_346	17	Assembly of midsection 11	\N	Pending	2013-06-14 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_347	17	Assembly of midsection 12	\N	Pending	2013-06-23 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_348	17	Assembly of midsection 13	\N	Pending	2013-07-02 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_349	17	Assembly of midsection 14	\N	Pending	2013-07-11 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_350	17	Assembly of midsection 15	\N	Pending	2013-07-20 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_351	17	Assembly of midsection 16	\N	Pending	2013-07-29 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_352	17	Assembly of midsection 17	\N	Pending	2013-08-07 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_353	17	Assembly of midsection 18	\N	Pending	2013-08-16 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_354	17	Assembly of midsection 19	\N	Pending	2013-08-25 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_355	17	Assembly of midsection 20	\N	Pending	2013-09-03 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_356	17	Assembly of midsection 21	\N	Pending	2013-09-12 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_357	17	Assembly of midsection 22	\N	Pending	2013-09-21 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_358	17	Assembly of midsection 23	\N	Pending	2013-09-30 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_359	17	Assembly of midsection 24	\N	Pending	2013-10-09 06:00:00	\N	55100.00	68875.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	33060.00	22040.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_360	17	Final jacket assembly 2	\N	Pending	2013-04-03 06:00:00	\N	40744.00	50930.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24432.00	16312.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_361	17	Final jacket assembly 3	\N	Pending	2013-04-12 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_362	17	Final jacket assembly 4	\N	Pending	2013-04-21 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_363	17	Final jacket assembly 5	\N	Pending	2013-04-30 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_364	17	Final jacket assembly 6	\N	Pending	2013-05-09 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_365	17	Final jacket assembly 7	\N	Pending	2013-05-18 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_366	17	Final jacket assembly 8	\N	Pending	2013-05-27 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_367	17	Final jacket assembly 9	\N	Pending	2013-06-05 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_368	17	Final jacket assembly 10	\N	Pending	2013-06-14 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_369	17	Final jacket assembly 11	\N	Pending	2013-06-23 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_370	17	Final jacket assembly 12	\N	Pending	2013-07-02 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_371	17	Final jacket assembly 13	\N	Pending	2013-07-11 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_372	17	Final jacket assembly 14	\N	Pending	2013-07-20 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_373	17	Final jacket assembly 15	\N	Pending	2013-07-29 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_374	17	Final jacket assembly 16	\N	Pending	2013-08-07 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_375	17	Final jacket assembly 17	\N	Pending	2013-08-16 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_376	17	Final jacket assembly 18	\N	Pending	2013-08-25 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_377	17	Final jacket assembly 19	\N	Pending	2013-09-03 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_378	17	Final jacket assembly 20	\N	Pending	2013-09-12 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_379	17	Final jacket assembly 21	\N	Pending	2013-09-21 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_380	17	Final jacket assembly 22	\N	Pending	2013-09-30 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_381	17	Final jacket assembly 23	\N	Pending	2013-10-09 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_382	17	Final jacket assembly 24	\N	Pending	2013-10-18 06:00:00	\N	40600.00	50750.00	1.2500	0.00	0.00	9.00	144.00	\N	0.00	0.00	0.00	0.00	24360.00	16240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_383	17	Transport (Hoboken to Vlissingen) 2	\N	Pending	2013-04-12 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_384	17	Transport (Hoboken to Vlissingen) 3	\N	Pending	2013-04-21 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_385	17	Transport (Hoboken to Vlissingen) 4	\N	Pending	2013-04-30 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_386	17	Transport (Hoboken to Vlissingen) 5	\N	Pending	2013-05-09 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_387	17	Transport (Hoboken to Vlissingen) 6	\N	Pending	2013-05-18 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_388	17	Transport (Hoboken to Vlissingen) 7	\N	Pending	2013-05-27 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_389	17	Transport (Hoboken to Vlissingen) 8	\N	Pending	2013-06-05 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_390	17	Transport (Hoboken to Vlissingen) 9	\N	Pending	2013-06-14 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_391	17	Transport (Hoboken to Vlissingen) 10	\N	Pending	2013-06-23 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_392	17	Transport (Hoboken to Vlissingen) 11	\N	Pending	2013-07-02 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_393	17	Transport (Hoboken to Vlissingen) 12	\N	Pending	2013-07-11 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_394	17	Transport (Hoboken to Vlissingen) 13	\N	Pending	2013-07-20 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_395	17	Transport (Hoboken to Vlissingen) 14	\N	Pending	2013-07-29 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_396	17	Transport (Hoboken to Vlissingen) 15	\N	Pending	2013-08-07 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_397	17	Transport (Hoboken to Vlissingen) 16	\N	Pending	2013-08-16 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_398	17	Transport (Hoboken to Vlissingen) 17	\N	Pending	2013-08-25 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_399	17	Transport (Hoboken to Vlissingen) 18	\N	Pending	2013-09-03 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_400	17	Transport (Hoboken to Vlissingen) 19	\N	Pending	2013-09-12 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_401	17	Transport (Hoboken to Vlissingen) 20	\N	Pending	2013-09-21 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_402	17	Transport (Hoboken to Vlissingen) 21	\N	Pending	2013-09-30 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_403	17	Transport (Hoboken to Vlissingen) 22	\N	Pending	2013-10-09 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_404	17	Transport (Hoboken to Vlissingen) 23	\N	Pending	2013-10-18 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_405	17	Transport (Hoboken to Vlissingen) 24	\N	Pending	2013-10-27 06:00:00	\N	14500.00	15370.00	1.0600	0.00	0.00	1.00	16.00	\N	0.00	0.00	0.00	0.00	14500.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_407	17	Reliability tests 2	\N	Pending	2014-01-21 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_408	17	Reliability tests 3	\N	Pending	2014-01-26 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_409	17	Reliability tests 4	\N	Pending	2014-01-31 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_410	17	Reliability tests 5	\N	Pending	2014-02-05 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_411	17	Reliability tests 6	\N	Pending	2014-02-10 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_412	17	Reliability tests 7	\N	Pending	2014-02-15 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_413	17	Reliability tests 8	\N	Pending	2014-02-20 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_414	17	Reliability tests 9	\N	Pending	2014-02-25 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_415	17	Reliability tests 10	\N	Pending	2014-03-02 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_416	17	Reliability tests 11	\N	Pending	2014-03-07 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_417	17	Reliability tests 12	\N	Pending	2014-03-12 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_418	17	Reliability tests 13	\N	Pending	2014-03-17 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_419	17	Reliability tests 14	\N	Pending	2014-03-22 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_420	17	Reliability tests 16	\N	Pending	2014-03-27 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_421	17	Reliability tests 15	\N	Pending	2014-04-01 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_422	17	Reliability tests 17	\N	Pending	2014-04-06 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_423	17	Reliability tests 18	\N	Pending	2014-04-11 06:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_424	17	Reliability tests 19	\N	Pending	2014-04-23 07:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_425	17	Reliability tests 20	\N	Pending	2014-04-28 07:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_426	17	Reliability tests 21	\N	Pending	2014-05-03 07:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_427	17	Reliability tests 22	\N	Pending	2014-05-08 07:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_428	17	Reliability tests 23	\N	Pending	2014-05-13 07:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_429	17	Reliability tests 24	\N	Pending	2014-04-18 07:00:00	\N	12800.00	16000.00	1.2500	0.00	0.00	5.00	80.00	\N	12800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_431	17	Commissioning of wind turbines 2	\N	Pending	2014-01-16 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_432	17	Commissioning of wind turbines 3	\N	Pending	2014-01-21 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_433	17	Commissioning of wind turbines 4	\N	Pending	2014-01-26 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_434	17	Commissioning of wind turbines 5	\N	Pending	2014-01-31 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_435	17	Commissioning of wind turbines 6	\N	Pending	2014-02-05 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_436	17	Commissioning of wind turbines 7	\N	Pending	2014-02-10 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_437	17	Commissioning of wind turbines 8	\N	Pending	2014-02-15 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_438	17	Commissioning of wind turbines 9	\N	Pending	2014-02-20 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_439	17	Commissioning of wind turbines 10	\N	Pending	2014-02-25 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_440	17	Commissioning of wind turbines 11	\N	Pending	2014-03-02 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_441	17	Commissioning of wind turbines 12	\N	Pending	2014-03-07 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_442	17	Commissioning of wind turbines 13	\N	Pending	2014-03-12 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_443	17	Commissioning of wind turbines 14	\N	Pending	2014-03-17 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_444	17	Commissioning of wind turbines 15	\N	Pending	2014-03-22 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_445	17	Commissioning of wind turbines 16	\N	Pending	2014-03-27 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_446	17	Commissioning of wind turbines 17	\N	Pending	2014-04-01 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_447	17	Commissioning of wind turbines 18	\N	Pending	2014-04-06 06:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_448	17	Commissioning of wind turbines 19	\N	Pending	2014-04-18 07:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_449	17	Commissioning of wind turbines 20	\N	Pending	2014-04-23 07:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_450	17	Commissioning of wind turbines 21	\N	Pending	2014-04-28 07:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_451	17	Commissioning of wind turbines 22	\N	Pending	2014-05-03 07:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_452	17	Commissioning of wind turbines 23	\N	Pending	2014-05-08 07:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_453	17	Commissioning of wind turbines 24	\N	Pending	2014-04-13 07:00:00	\N	64000.00	86400.00	1.3500	0.00	0.00	5.00	80.00	\N	64000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.1000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_455	17	Terminations of infield cables 2	\N	Pending	2014-01-12 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_456	17	Terminations of infield cables 3	\N	Pending	2014-01-16 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_457	17	Terminations of infield cables 4	\N	Pending	2014-01-20 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_458	17	Terminations of infield cables 5	\N	Pending	2014-01-24 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_459	17	Terminations of infield cables 6	\N	Pending	2014-01-28 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_46	17	Towers by AMAU-Cuxhaven Germany	\N	Pending	2013-05-12 06:00:00	\N	14400000.00	15264000.00	1.0600	0.00	0.00	240.00	3840.00	\N	0.00	0.00	0.00	0.00	14400000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_460	17	Terminations of infield cables 7	\N	Pending	2014-02-02 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_461	17	Terminations of infield cables 8	\N	Pending	2014-02-05 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_462	17	Terminations of infield cables 9	\N	Pending	2014-02-09 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_463	17	Terminations of infield cables 10	\N	Pending	2014-02-13 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_464	17	Terminations of infield cables 11	\N	Pending	2014-02-17 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_465	17	Terminations of infield cables 12	\N	Pending	2014-02-21 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_466	17	Terminations of infield cables 13	\N	Pending	2014-02-25 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_467	17	Terminations of infield cables 14	\N	Pending	2014-03-01 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_468	17	Terminations of infield cables 15	\N	Pending	2014-03-05 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_469	17	Terminations of infield cables 16	\N	Pending	2014-03-09 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_47	17	Blades by LM Denmark	\N	Pending	2013-02-04 18:00:00	\N	8640000.00	9158400.00	1.0600	0.00	0.00	240.00	3840.00	\N	0.00	0.00	0.00	0.00	8640000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_470	17	Terminations of infield cables 17	\N	Pending	2014-03-13 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_471	17	Terminations of infield cables 18	\N	Pending	2014-03-17 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_472	17	Terminations of infield cables 19	\N	Pending	2014-03-21 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_473	17	Terminations of infield cables 20	\N	Pending	2014-03-25 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_474	17	Terminations of infield cables 21	\N	Pending	2014-03-29 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_475	17	Terminations of infield cables 22	\N	Pending	2014-04-02 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_476	17	Terminations of infield cables 23	\N	Pending	2014-04-06 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_477	17	Terminations of infield cables 24	\N	Pending	2014-04-10 07:00:00	\N	38400.00	48000.00	1.2500	0.00	0.00	3.00	48.00	\N	38400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_478	17	Offshore assembly of wind turbines 1	\N	Pending	2013-12-21 06:00:00	\N	465984.00	582480.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	105792.00	105792.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_479	17	Offshore assembly of wind turbines 2	\N	Pending	2014-01-09 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_48	17	Generators by VEM Germany	\N	Pending	2013-03-16 07:00:00	\N	12096000.00	12821760.00	1.0600	0.00	0.00	240.00	3840.00	\N	0.00	0.00	0.00	0.00	12096000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_480	17	Offshore assembly of wind turbines 3	\N	Pending	2014-01-13 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_481	17	Offshore assembly of wind turbines 4	\N	Pending	2014-01-17 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_482	17	Offshore assembly of wind turbines 5	\N	Pending	2014-01-21 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_483	17	Offshore assembly of wind turbines 6	\N	Pending	2014-01-25 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_484	17	Offshore assembly of wind turbines 7	\N	Pending	2014-01-29 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_485	17	Offshore assembly of wind turbines 8	\N	Pending	2014-02-02 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_486	17	Offshore assembly of wind turbines 9	\N	Pending	2014-02-06 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_487	17	Offshore assembly of wind turbines 10	\N	Pending	2014-02-10 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_488	17	Offshore assembly of wind turbines 11	\N	Pending	2014-02-14 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_489	17	Offshore assembly of wind turbines 12	\N	Pending	2014-02-18 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_49	17	Gearboxes by WINERGY-Vörde Germany and Hansen Belgium	\N	Pending	2013-03-16 07:00:00	\N	22464000.00	23811840.00	1.0600	0.00	0.00	240.00	3840.00	\N	0.00	0.00	0.00	0.00	22464000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_490	17	Offshore assembly of wind turbines 13	\N	Pending	2014-02-22 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_491	17	Offshore assembly of wind turbines 14	\N	Pending	2014-02-26 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_492	17	Offshore assembly of wind turbines 15	\N	Pending	2014-03-02 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_493	17	Offshore assembly of wind turbines 16	\N	Pending	2014-03-06 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_494	17	Offshore assembly of wind turbines 17	\N	Pending	2014-03-10 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_495	17	Offshore assembly of wind turbines 18	\N	Pending	2014-03-14 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_496	17	Offshore assembly of wind turbines 19	\N	Pending	2014-03-18 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_497	17	Offshore assembly of wind turbines 20	\N	Pending	2014-03-22 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_498	17	Offshore assembly of wind turbines 21	\N	Pending	2014-03-26 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_499	17	Offshore assembly of wind turbines 22	\N	Pending	2014-03-30 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_50	17	Gearboxes Germany-Ostend/Antwerp-Ostend	\N	Pending	2013-10-02 07:00:00	\N	1027000.00	1335100.00	1.3000	0.00	0.00	48.00	768.00	\N	0.00	0.00	0.00	0.00	1027000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.1000	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_500	17	Offshore assembly of wind turbines 23	\N	Pending	2014-04-03 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_501	17	Offshore assembly of wind turbines 24	\N	Pending	2014-04-07 07:00:00	\N	254400.00	318000.00	1.2500	0.00	0.00	1.00	16.00	\N	143520.00	0.00	110880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_502	17	Loading jack up transport and installation platform 1	\N	Pending	2013-12-18 06:00:00	\N	1417200.00	1771500.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	317400.00	0.00	317400.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_503	17	Loading jack up transport and installation platform 2	\N	Pending	2014-01-06 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_504	17	Loading jack up transport and installation platform 3	\N	Pending	2014-01-10 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_505	17	Loading jack up transport and installation platform 4	\N	Pending	2014-01-14 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_506	17	Loading jack up transport and installation platform 5	\N	Pending	2014-01-18 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_507	17	Loading jack up transport and installation platform 6	\N	Pending	2014-01-22 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_508	17	Loading jack up transport and installation platform 7	\N	Pending	2014-01-26 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_509	17	Loading jack up transport and installation platform 8	\N	Pending	2014-01-30 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_51	17	Generators Germany-Ostend	\N	Pending	2013-10-02 07:00:00	\N	1027000.00	1335100.00	1.3000	0.00	0.00	48.00	768.00	\N	0.00	0.00	0.00	0.00	1027000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.1000	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_510	17	Loading jack up transport and installation platform 9	\N	Pending	2014-02-03 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_544	17	Delivery of pin-piles 18	\N	Pending	2013-07-28 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_511	17	Loading jack up transport and installation platform 10	\N	Pending	2014-02-07 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_512	17	Loading jack up transport and installation platform 11	\N	Pending	2014-02-11 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_513	17	Loading jack up transport and installation platform 12	\N	Pending	2014-02-15 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_514	17	Loading jack up transport and installation platform 13	\N	Pending	2014-02-19 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_515	17	Loading jack up transport and installation platform 14	\N	Pending	2014-02-23 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_516	17	Loading jack up transport and installation platform 15	\N	Pending	2014-02-27 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_517	17	Loading jack up transport and installation platform 16	\N	Pending	2014-03-03 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_518	17	Loading jack up transport and installation platform 17	\N	Pending	2014-03-07 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_519	17	Loading jack up transport and installation platform 18	\N	Pending	2014-03-11 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_52	17	Blades Denmark-Ostend	\N	Pending	2013-08-23 18:00:00	\N	624000.00	811200.00	1.3000	0.00	0.00	39.00	629.00	\N	0.00	0.00	0.00	0.00	624000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.1000	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_520	17	Loading jack up transport and installation platform 19	\N	Pending	2014-03-15 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_521	17	Loading jack up transport and installation platform 20	\N	Pending	2014-03-19 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_522	17	Loading jack up transport and installation platform 21	\N	Pending	2014-03-23 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_523	17	Loading jack up transport and installation platform 22	\N	Pending	2014-03-27 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_524	17	Loading jack up transport and installation platform 23	\N	Pending	2014-03-31 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_525	17	Loading jack up transport and installation platform 24	\N	Pending	2014-04-04 07:00:00	\N	782400.00	978000.00	1.2500	0.00	0.00	3.00	48.00	\N	440160.00	0.00	342240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_526	17	Delivery of pin-piles OTS	\N	Pending	2013-05-16 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_527	17	Delivery of pin-piles 1	\N	Pending	2013-05-20 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_528	17	Delivery of pin-piles 2	\N	Pending	2013-05-24 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_529	17	Delivery of pin-piles 3	\N	Pending	2013-05-28 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_53	17	Towers Germany-Ostend	\N	Pending	2013-11-28 06:00:00	\N	624000.00	811200.00	1.3000	0.00	0.00	48.00	768.00	\N	0.00	0.00	0.00	0.00	624000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.1000	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_530	17	Delivery of pin-piles 4	\N	Pending	2013-06-01 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_531	17	Delivery of pin-piles 5	\N	Pending	2013-06-05 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_532	17	Delivery of pin-piles 6	\N	Pending	2013-06-10 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_533	17	Delivery of pin-piles 7	\N	Pending	2013-06-14 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_534	17	Delivery of pin-piles 8	\N	Pending	2013-06-18 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_535	17	Delivery of pin-piles 9	\N	Pending	2013-06-22 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_536	17	Delivery of pin-piles 10	\N	Pending	2013-06-26 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_537	17	Delivery of pin-piles 11	\N	Pending	2013-06-30 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_538	17	Delivery of pin-piles 12	\N	Pending	2013-07-04 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_539	17	Delivery of pin-piles 13	\N	Pending	2013-07-08 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_540	17	Delivery of pin-piles 14	\N	Pending	2013-07-12 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_541	17	Delivery of pin-piles 15	\N	Pending	2013-07-16 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_543	17	Delivery of pin-piles 17	\N	Pending	2013-07-24 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_545	17	Delivery of pin-piles 19	\N	Pending	2013-08-01 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_546	17	Delivery of pin-piles 20	\N	Pending	2013-08-05 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_547	17	Delivery of pin-piles 21	\N	Pending	2013-08-13 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_548	17	Delivery of pin-piles 22	\N	Pending	2013-08-09 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_549	17	Delivery of pin-piles 23	\N	Pending	2013-08-17 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_550	17	Delivery of pin-piles 24	\N	Pending	2013-08-21 06:00:00	\N	26930.00	33662.50	1.2500	0.00	0.00	1.00	16.00	\N	13280.00	0.00	9600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	810.00	3240.00	0.00	0.00	0.00	0.00	\N	{}
17_551	17	Purchasing of pin-piles	\N	Pending	2013-02-04 06:00:00	\N	6264000.00	7830000.00	1.2500	0.00	0.00	50.00	800.00	\N	0.00	0.00	0.00	0.00	6264000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_56	17	Preparation of the onshore site	\N	Pending	2013-03-18 06:00:00	\N	1651200.00	2064000.00	1.2500	0.00	0.00	30.00	480.00	\N	1363200.00	0.00	288000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_57	17	Assembly of gearbox and generator	\N	Pending	2013-11-19 07:00:00	\N	1213440.00	1516800.00	1.2500	0.00	0.00	48.00	768.00	\N	1059840.00	0.00	153600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_58	17	Assembly of blades	\N	Pending	2013-10-02 07:00:00	\N	1305600.00	1632000.00	1.2500	0.00	0.00	48.00	768.00	\N	1152000.00	0.00	153600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_6	17	Mobilisation of vessels	\N	Pending	2013-04-06 06:00:00	\N	1656000.00	2070000.00	1.2500	0.00	0.00	15.00	240.00	\N	859200.00	0.00	796800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_7	17	Seabed preparations	\N	Pending	2013-04-21 06:00:00	\N	3416000.00	4270000.00	1.2500	0.00	0.00	25.00	400.00	\N	2088000.00	0.00	1328000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_75	17	Purchase of base materials	\N	Pending	2013-02-04 06:00:00	\N	176000.00	228800.00	1.3000	0.00	0.00	40.00	640.00	\N	0.00	0.00	0.00	0.00	176000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.1000	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_76	17	Construction of jacket foundation for OTS	\N	Pending	2013-03-16 06:00:00	\N	278000.00	347500.00	1.2500	0.00	0.00	10.00	160.00	\N	0.00	0.00	0.00	0.00	278000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_77	17	Transport of jacket foundation to Ostend	\N	Pending	2013-05-31 06:00:00	\N	79360.00	84121.60	1.0600	0.00	0.00	2.00	32.00	\N	45760.00	0.00	33600.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0015	0.0085	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_81	17	Installation of jacket foundation of OTS	\N	Pending	2013-06-03 06:00:00	\N	143680.00	179600.00	1.2500	0.00	0.00	1.00	16.00	\N	85760.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_82	17	Transport of jacket foundation in sea	\N	Pending	2013-06-02 06:00:00	\N	49920.00	62400.00	1.2500	0.00	0.00	1.00	16.00	\N	33120.00	0.00	16800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_84	17	Purchase of base materials	\N	Pending	2013-02-04 06:00:00	\N	3045000.00	3958500.00	1.3000	0.00	0.00	150.00	2400.00	\N	0.00	0.00	0.00	0.00	3045000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.1000	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_85	17	Erection of 1st main deck section	\N	Pending	2013-04-05 06:00:00	\N	696000.00	870000.00	1.2500	0.00	0.00	30.00	480.00	\N	0.00	0.00	0.00	0.00	696000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_86	17	Erection of 2st main deck section	\N	Pending	2013-05-05 06:00:00	\N	696000.00	870000.00	1.2500	0.00	0.00	30.00	480.00	\N	0.00	0.00	0.00	0.00	696000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_87	17	Erection of mezzanine deck	\N	Pending	2013-06-04 06:00:00	\N	654000.00	817500.00	1.2500	0.00	0.00	16.00	256.00	\N	0.00	0.00	0.00	0.00	654000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_88	17	Construction of roof deck	\N	Pending	2013-06-20 06:00:00	\N	696000.00	870000.00	1.2500	0.00	0.00	16.00	256.00	\N	0.00	0.00	0.00	0.00	696000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_89	17	Internal finishings	\N	Pending	2013-07-06 06:00:00	\N	205000.00	256250.00	1.2500	0.00	0.00	2.00	33.00	\N	0.00	0.00	0.00	0.00	205000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_90	17	Installation of transformer equipment	\N	Pending	2013-07-08 07:00:00	\N	864000.00	1080000.00	1.2500	0.00	0.00	60.00	960.00	\N	0.00	0.00	0.00	0.00	864000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_91	17	Preparation for upcoming transport	\N	Pending	2013-09-06 07:00:00	\N	123000.00	153750.00	1.2500	0.00	0.00	10.00	160.00	\N	0.00	0.00	0.00	0.00	123000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_94	17	Transport of OTS	\N	Pending	2013-09-16 07:00:00	\N	39680.00	49600.00	1.2500	0.00	0.00	1.00	16.00	\N	22880.00	0.00	16800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
17_95	17	Installation of OTS foundation	\N	Pending	2013-09-17 07:00:00	\N	143680.00	179600.00	1.2500	0.00	0.00	1.00	16.00	\N	85760.00	0.00	57920.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.0300	0.1700	0.0500	0.0000	0.00	0.00	0.00	0.00	0.00	0.00	\N	{}
18_10	18	8. Feasibility study	\N	Pending	2019-02-07 08:00:00	\N	2800.00	3920.00	1.4000	0.00	0.00	7.00	56.00	\N	2800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_11	18	9. Search for funding (VC, Business angels, bankloan)	\N	Pending	2019-02-18 08:00:00	\N	2880.00	4032.00	1.4000	0.00	0.00	12.00	96.00	\N	2880.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_13	18	10. Contact city to get the approval	\N	Pending	2019-03-06 08:00:00	\N	4800.00	6720.00	1.4000	0.00	0.00	20.00	160.00	\N	4800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_14	18	11. Asking city for blue prints power network	\N	Pending	2019-04-10 08:00:00	\N	4800.00	6720.00	1.4000	0.00	0.00	20.00	160.00	\N	4800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_15	18	12. Meeting with car leasers + quotation	\N	Pending	2019-04-10 08:00:00	\N	6000.00	8400.00	1.4000	0.00	0.00	25.00	200.00	\N	6000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_16	18	13. Meeting with docking station suppliers	\N	Pending	2019-05-08 08:00:00	\N	6000.00	8400.00	1.4000	0.00	0.00	25.00	200.00	\N	6000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_17	18	14. Meeting with possible contractors	\N	Pending	2019-06-12 08:00:00	\N	2400.00	3360.00	1.4000	0.00	0.00	10.00	80.00	\N	2400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_19	18	15. Web/app developer search	\N	Pending	2019-04-03 08:00:00	\N	1200.00	1680.00	1.4000	0.00	0.00	5.00	40.00	\N	1200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_20	18	16. Developing website/app	\N	Pending	2019-04-10 08:00:00	\N	90000.00	126000.00	1.4000	0.00	0.00	70.00	560.00	\N	0.00	0.00	0.00	0.00	90000.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_21	18	17. Developing payment system	\N	Pending	2019-07-17 08:00:00	\N	20000.00	28000.00	1.4000	0.00	0.00	55.00	440.00	\N	0.00	0.00	0.00	0.00	20000.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_22	18	18. Testing & approving app	\N	Pending	2019-10-02 08:00:00	\N	4500.00	6300.00	1.4000	0.00	0.00	15.00	120.00	\N	0.00	0.00	0.00	4500.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_23	18	19. Testing & approving payment system	\N	Pending	2019-10-02 08:00:00	\N	1500.00	2100.00	1.4000	0.00	0.00	15.00	120.00	\N	0.00	0.00	0.00	1500.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_25	18	20. Negotiate maintenance contract with possible partners	\N	Pending	2019-06-19 08:00:00	\N	4800.00	6720.00	1.4000	0.00	0.00	20.00	160.00	\N	4800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_27	18	21. Drilling the holes where the charging blocks will be put by Eandis and where the traffic signs will be put	\N	Pending	2019-06-26 08:00:00	\N	10599.00	14838.60	1.4000	0.00	0.00	12.00	96.00	\N	0.00	0.00	0.00	0.00	0.00	10599.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_28	18	22. Delivery and placing of the charging blocks (UwLaadpunt)	\N	Pending	2019-07-12 08:00:00	\N	78715.00	110201.00	1.4000	0.00	0.00	12.00	96.00	\N	0.00	0.00	0.00	0.00	0.00	78715.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_29	18	23. Access power network: connecting charging blocks to power grid (Eandis)	\N	Pending	2019-07-30 08:00:00	\N	19500.00	27300.00	1.4000	0.00	0.00	12.00	96.00	\N	0.00	0.00	0.00	0.00	0.00	19500.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_3	18	1. Analysis of car usage in general, link to car sharing, environment, cost of parking	\N	Pending	2019-01-01 08:00:00	\N	2400.00	3360.00	1.4000	0.00	0.00	10.00	80.00	\N	2400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_30	18	24. Installation of visibility marks (Trafiroad)	\N	Pending	2019-07-30 08:00:00	\N	2480.00	3472.00	1.4000	0.00	0.00	6.00	48.00	\N	0.00	0.00	0.00	0.00	0.00	2480.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_31	18	25. Installation of trafic signs (Trafiroad)	\N	Pending	2019-07-30 08:00:00	\N	8500.00	11900.00	1.4000	0.00	0.00	6.00	48.00	\N	0.00	0.00	0.00	0.00	0.00	8500.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_32	18	26. Testing of the charging blocks	\N	Pending	2019-08-15 08:00:00	\N	0.00	0.00	1.4000	0.00	0.00	6.00	48.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_34	18	27. Delivery cars	\N	Pending	2019-08-23 08:00:00	\N	144000.00	201600.00	1.4000	0.00	0.00	6.00	48.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	144000.00	0.00	0.00	\N	0.00	\N	{}
18_36	18	28. Placing cars	\N	Pending	2019-09-02 08:00:00	\N	960.00	1344.00	1.4000	0.00	0.00	5.00	40.00	\N	960.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_37	18	29. Final testing of the finished system	\N	Pending	2019-09-09 08:00:00	\N	8000.00	11200.00	1.4000	0.00	0.00	20.00	160.00	\N	8000.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_39	18	30. Publicity campaign for our company	\N	Pending	2019-10-07 08:00:00	\N	3360.00	4704.00	1.4000	0.00	0.00	15.00	120.00	\N	3360.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_4	18	2. Type of cars	\N	Pending	2019-01-15 08:00:00	\N	2400.00	3360.00	1.4000	0.00	0.00	6.00	48.00	\N	2400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_41	18	31. Payment of Web/app developers	\N	Pending	2019-10-23 08:00:00	\N	240.00	336.00	1.4000	0.00	0.00	1.00	8.00	\N	240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_42	18	32. Payment 'UwLaadpunt'	\N	Pending	2019-07-30 08:00:00	\N	240.00	336.00	1.4000	0.00	0.00	1.00	8.00	\N	240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_43	18	33. Payment 'Eandis'	\N	Pending	2019-08-15 08:00:00	\N	240.00	336.00	1.4000	0.00	0.00	1.00	8.00	\N	240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_44	18	34. Payment 'Traffiroad'	\N	Pending	2019-08-07 08:00:00	\N	240.00	336.00	1.4000	0.00	0.00	1.00	8.00	\N	240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_46	18	36. Payment carleasing	\N	Pending	2019-09-02 08:00:00	\N	240.00	336.00	1.4000	0.00	0.00	1.00	8.00	\N	240.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_48	18	37. Launch	\N	Pending	2019-10-23 17:00:00	\N	0.00	0.00	1.4000	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_5	18	3. Determine amount of ars needed and parking place	\N	Pending	2019-01-23 08:00:00	\N	2400.00	3360.00	1.4000	0.00	0.00	6.00	48.00	\N	2400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_6	18	4. Research for charging stations (suppliers)	\N	Pending	2019-01-31 08:00:00	\N	800.00	1120.00	1.4000	0.00	0.00	2.00	16.00	\N	800.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_7	18	5. Research use of exsisting charging stations	\N	Pending	2019-01-31 08:00:00	\N	400.00	560.00	1.4000	0.00	0.00	1.00	8.00	\N	400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_8	18	6. Research for traffic sign supplier (Trafiroad)	\N	Pending	2019-01-31 08:00:00	\N	400.00	560.00	1.4000	0.00	0.00	1.00	8.00	\N	400.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
18_9	18	7. Research amount of staff needed (extra contractors)	\N	Pending	2019-02-04 08:00:00	\N	1200.00	1680.00	1.4000	0.00	0.00	3.00	24.00	\N	1200.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_1	19	Installation of power generators, lighting, toilets, fencing,  supply of concrete and wooden partition	\N	Pending	2019-05-20 08:00:00	\N	3920.00	5488.00	1.4000	0.00	0.00	2.00	16.00	\N	1920.00	0.00	0.00	0.00	0.00	0.00	0.00	2000.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_10	19	Pumping lock chamber completely dry	\N	Pending	2019-05-29 08:00:00	\N	2140.00	2996.00	1.4000	0.00	0.00	1.00	8.00	\N	640.00	0.00	0.00	0.00	1500.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_11	19	Cleaning lock floor	\N	Pending	2019-05-30 08:00:00	\N	2620.00	3668.00	1.4000	0.00	0.00	1.00	8.00	\N	320.00	0.00	0.00	0.00	0.00	2300.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_12	19	supply concrete blocks (to prevent the floor comes up)	\N	Pending	2019-05-30 08:00:00	\N	9720.00	13608.00	1.4000	0.00	0.00	1.00	8.00	\N	320.00	0.00	0.00	0.00	9400.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_13	19	placing concrete blocks	\N	Pending	2019-05-31 08:00:00	\N	3140.00	4396.00	1.4000	0.00	0.00	1.00	8.00	\N	640.00	0.00	0.00	0.00	2500.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.3000	0.0000	0.1000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_14	19	Cleaning walls and threshold	\N	Pending	2019-05-30 08:00:00	\N	3850.00	5390.00	1.4000	0.00	0.00	1.00	8.00	\N	320.00	0.00	0.00	0.00	0.00	3530.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_15	19	Installing stairs in lock chamber	\N	Pending	2019-06-03 08:00:00	\N	4160.00	5824.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	3200.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_16	19	Replacing hinges, pivot shoes and pivots	\N	Pending	2019-06-04 08:00:00	\N	10360.00	14504.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	9400.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.3000	0.0000	0.1000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_17	19	Cleaning lock head	\N	Pending	2019-06-04 08:00:00	\N	3960.00	5544.00	1.4000	0.00	0.00	3.00	24.00	\N	960.00	0.00	0.00	0.00	0.00	3000.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_19	19	Transport of gates to the site	\N	Pending	2019-06-07 08:00:00	\N	5870.00	8218.00	1.4000	0.00	0.00	1.00	8.00	\N	320.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.3000	0.0000	0.1000	0.0000	0.00	5550.00	0.00	0.00	\N	0.00	\N	{}
19_2	19	Remove railing and platforms	\N	Pending	2019-05-22 08:00:00	\N	4780.00	6692.00	1.4000	0.00	0.00	2.00	16.00	\N	1280.00	0.00	0.00	0.00	0.00	3500.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_20	19	Put gates in place	\N	Pending	2019-06-10 08:00:00	\N	24960.00	34944.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	24000.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.3000	0.0000	0.1000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_21	19	Adjusting gates (Tightening hinges , front beams, sealing, anchorage points)	\N	Pending	2019-06-11 08:00:00	\N	8640.00	12096.00	1.4000	0.00	0.00	1.00	8.00	\N	640.00	0.00	0.00	0.00	8000.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.3000	0.0000	0.1000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_22	19	Installing railing	\N	Pending	2019-06-12 08:00:00	\N	2840.00	3976.00	1.4000	0.00	0.00	1.00	8.00	\N	640.00	0.00	0.00	0.00	2200.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_23	19	preliminary works at threshold	\N	Pending	2019-06-12 08:00:00	\N	3140.00	4396.00	1.4000	0.00	0.00	1.00	8.00	\N	640.00	0.00	0.00	0.00	2500.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_24	19	Repairing threshold	\N	Pending	2019-06-13 08:00:00	\N	5220.00	7308.00	1.4000	0.00	0.00	2.00	16.00	\N	1920.00	0.00	0.00	0.00	3300.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_25	19	Install platforms	\N	Pending	2019-06-12 08:00:00	\N	5480.00	7672.00	1.4000	0.00	0.00	2.00	16.00	\N	1280.00	0.00	0.00	0.00	4200.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_26	19	Installing ladder	\N	Pending	2019-06-12 08:00:00	\N	6480.00	9072.00	1.4000	0.00	0.00	2.00	16.00	\N	1280.00	0.00	0.00	0.00	5200.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_27	19	Remove concrete blocks	\N	Pending	2019-06-17 08:00:00	\N	3460.00	4844.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	0.00	2500.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_28	19	Remove concrete and wooden partition	\N	Pending	2019-06-18 08:00:00	\N	4560.00	6384.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	0.00	3600.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_29	19	Cleaning site	\N	Pending	2019-06-19 08:00:00	\N	4560.00	6384.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	0.00	3600.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_3	19	preliminary works at gates (loosing hinges, disconnect hinges, hydraulics, anchorage points)	\N	Pending	2019-05-22 08:00:00	\N	5460.00	7644.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	4500.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.3000	0.0000	0.1000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_30	19	End Of Preparation/Start Restoration of lock head	\N	Pending	2019-05-27 17:00:00	\N	0.00	0.00	1.4000	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_31	19	End Restoration of lock head/Start Installing new gates	\N	Pending	2019-06-06 17:00:00	\N	0.00	0.00	1.4000	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_32	19	End Installing new gates/ Start Termination	\N	Pending	2019-06-14 17:00:00	\N	0.00	0.00	1.4000	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_4	19	Sealing canal lock gates at other side and overflow sewers	\N	Pending	2019-05-22 08:00:00	\N	2640.00	3696.00	1.4000	0.00	0.00	1.00	8.00	\N	640.00	0.00	0.00	0.00	2000.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_5	19	Placing of concrete partition + Placing of wooden partition	\N	Pending	2019-05-23 08:00:00	\N	5760.00	8064.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	4800.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.3000	0.0000	0.1000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_6	19	Installing pumps	\N	Pending	2019-05-24 08:00:00	\N	3140.00	4396.00	1.4000	0.00	0.00	1.00	8.00	\N	640.00	0.00	0.00	0.00	2500.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_7	19	Check safety wooden partition + Check safety concrete partition	\N	Pending	2019-05-27 08:00:00	\N	2060.00	2884.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	1100.00	0.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.2000	0.0000	0.2000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_8	19	Remove gates	\N	Pending	2019-05-28 08:00:00	\N	19940.00	27916.00	1.4000	0.00	0.00	1.00	8.00	\N	640.00	0.00	0.00	0.00	0.00	19300.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.3000	0.0000	0.1000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
19_9	19	Remove hinges	\N	Pending	2019-05-29 08:00:00	\N	2960.00	4144.00	1.4000	0.00	0.00	1.00	8.00	\N	960.00	0.00	0.00	0.00	0.00	2000.00	0.00	0.00	\N	0.00	0.00	0.00	0.00	0.3000	0.0000	0.1000	0.0000	0.00	0.00	0.00	0.00	\N	0.00	\N	{}
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, email, created_at) FROM stdin;
\.


--
-- Name: ai_recommendations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ai_recommendations_id_seq', 1, false);


--
-- Name: ai_simulation_runs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ai_simulation_runs_id_seq', 1, false);


--
-- Name: project_baselines_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_baselines_id_seq', 1, false);


--
-- Name: project_constraint_resource_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_constraint_resource_id_seq', 223, true);


--
-- Name: project_constraint_time_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_constraint_time_id_seq', 18, true);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.projects_id_seq', 19, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- Name: ai_recommendations ai_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_recommendations
    ADD CONSTRAINT ai_recommendations_pkey PRIMARY KEY (id);


--
-- Name: ai_simulation_runs ai_simulation_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_simulation_runs
    ADD CONSTRAINT ai_simulation_runs_pkey PRIMARY KEY (id);


--
-- Name: project_baselines project_baselines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_baselines
    ADD CONSTRAINT project_baselines_pkey PRIMARY KEY (id);


--
-- Name: project_constraint_logic project_constraint_logic_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_logic
    ADD CONSTRAINT project_constraint_logic_pkey PRIMARY KEY (predecessor_id, successor_id, project_id);


--
-- Name: project_constraint_resource project_constraint_resource_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_resource
    ADD CONSTRAINT project_constraint_resource_pkey PRIMARY KEY (id);


--
-- Name: project_constraint_time project_constraint_time_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_time
    ADD CONSTRAINT project_constraint_time_pkey PRIMARY KEY (id);


--
-- Name: project_constraint_time project_constraint_time_project_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_time
    ADD CONSTRAINT project_constraint_time_project_id_key UNIQUE (project_id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: task_resources task_resources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_resources
    ADD CONSTRAINT task_resources_pkey PRIMARY KEY (task_id, resource_id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: ai_recommendations ai_recommendations_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_recommendations
    ADD CONSTRAINT ai_recommendations_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.ai_simulation_runs(id) ON DELETE CASCADE;


--
-- Name: ai_simulation_runs ai_simulation_runs_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_simulation_runs
    ADD CONSTRAINT ai_simulation_runs_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_baselines project_baselines_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_baselines
    ADD CONSTRAINT project_baselines_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_baselines project_baselines_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_baselines
    ADD CONSTRAINT project_baselines_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.ai_simulation_runs(id) ON DELETE SET NULL;


--
-- Name: project_constraint_logic project_constraint_logic_predecessor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_logic
    ADD CONSTRAINT project_constraint_logic_predecessor_id_fkey FOREIGN KEY (predecessor_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: project_constraint_logic project_constraint_logic_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_logic
    ADD CONSTRAINT project_constraint_logic_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_constraint_logic project_constraint_logic_successor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_logic
    ADD CONSTRAINT project_constraint_logic_successor_id_fkey FOREIGN KEY (successor_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: project_constraint_resource project_constraint_resource_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_resource
    ADD CONSTRAINT project_constraint_resource_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_constraint_time project_constraint_time_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_constraint_time
    ADD CONSTRAINT project_constraint_time_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: projects projects_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: task_resources task_resources_resource_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_resources
    ADD CONSTRAINT task_resources_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES public.project_constraint_resource(id) ON DELETE CASCADE;


--
-- Name: task_resources task_resources_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_resources
    ADD CONSTRAINT task_resources_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

-- \unrestrict 5N81jXheozMCPBQV7LMkOjedHsN2V8V4mS6OcrXRssUWN4nHeg4aVQzldZeznOK

