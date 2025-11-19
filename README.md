
Intelligent Radiology Work Allocation System

A Modular Monolithic Agent-Based Workflow Engine

This project implements an AI-powered radiology work allocation system that intelligently assigns imaging cases (MRI, CT, X-Ray, Ultrasound, Mammography) to the most suitable radiologist based on specialty, skill level, workload, experience, availability, and case priority.
The system uses a deterministic agent pipeline, a transparent scoring engine, and an LLM-driven explanation generator to produce professional, auditable assignment decisions.

Table of Contents

Project Overview

Architecture Overview

Monolithic Modular Project Structure

End-to-End System Workflow

Five Agents

Timestamp-Driven Availability Logic

Scoring Model

Database Schema & Indexing

Database Repositories

LLM Integration

Utility Modules

FastAPI Interface

End-to-End Pipeline Walkthrough

Key Features & Optimizations

Setup Instructions

Run Instructions

API Endpoints

Required Test Scenarios

Image & Diagram Placeholders

Project Overview

Radiology workflows require balancing specialty, availability, experience, and urgency. This system automates the process using a rule-based + AI-enhanced pipeline.

Core capabilities:

Intelligent assignment based on multiple weighted factors

Strict validation of scheduled timestamps

Specialty-based matching (with fallback logic)

Availability-window filtering

Detailed scoring breakdown

LLM-generated professional explanation

Flexible DB backend (MySQL / SQLite)

Modular monolithic architecture for scalability and clarity

Architecture Overview

The system is implemented using a modular monolithic architecture, providing the deployment simplicity of a single backend with the structural clarity of isolated modules.

Key Architectural Characteristics

Single Deployable Backend
All agents, repositories, controllers, utilities, and routes run as one cohesive service.

Modular Code Organization
Clearly separated modules (agents/, db/, routes/, utils/) ensure:

separation of concerns

low coupling

consistent debugging

high maintainability

Agent-Oriented Processing Pipeline

AddWorkAgent
      ↓
WorkAnalyzerAgent
      ↓
ResourceFinderAgent
      ↓
AvailabilityCheckerAgent
      ↓
AssignmentAgent (LLM Explanation)


Centralized Relational Database
MySQL (preferred) or SQLite with automatic fallback initialization.

FastAPI REST Interface
Clean API for UI integration, testing, and evaluation.

Mandatory LLM Explanation Generation
Agent 5 always produces a human-readable justification using either:

HuggingFace generation, or

Template fallback

Designed for testability, extensibility, and performance

Monolithic Modular Project Structure
services/
  api/
    app/
      agents/
        add_work_agent.py
        work_analyzer_agent.py
        resource_finder_agent.py
        availability_checker_agent.py
        assignment_agent.py
        base_agent.py
        llm_client.py
      db/
        repositories.py
        mysql.py
      routes/
        work_routes.py
        resource_routes.py
      utils/
        scoring.py
        time_utils.py
      static/
        index.html
      config.py
      main.py
infra/
  mysql_init/
    schema.sql
    resources.csv
    resource_calendar.csv
    specialty_mapping.csv
    work_requests.csv

End-to-End System Workflow

User submits new work request

Pipeline orchestrates all five agents

Each agent enriches the context

Scoring engine evaluates all possible radiologists

AssignmentAgent updates DB + generates LLM explanation

API returns full ranked list + explanation

Five Agents

Below are the five core agents with code-referenced responsibilities.

1. AddWorkAgent

Path: agents/add_work_agent.py

Responsibilities:

Validate user input

Combine scheduled_date + scheduled_time into scheduled_timestamp

Insert request into database

Create deterministic work_id

Key Logic Example:
work_id = f"W{int(time.time() * 1000)}"
scheduled_timestamp = self._compose_timestamp(...)
WorkRequestsRepo.create_work_request(record)

2. WorkAnalyzerAgent

Path: agents/work_analyzer_agent.py

Responsibilities:

Retrieve work request

Identify specialty via:

specialty_mapping table

fallback mappings

Always ensures valid required_specialty and alternate_specialty

Fallback Example:
MRI_Brain → Neurologist
CT_Scan_Chest → General_Radiologist
X_Ray_Bone → Musculoskeletal_Specialist

3. ResourceFinderAgent

Path: agents/resource_finder_agent.py

Responsibilities:

Fetch radiologists based on specialties

Optional FAISS-based semantic expansion

Merge semantic candidates with DB candidates

Semantic Expansion Example:
if FAISS_AVAILABLE and len(candidates) < 3:
    sem = query_faiss_by_text(q, top_k=5)

4. AvailabilityCheckerAgent

Path: agents/availability_checker_agent.py

Responsibilities:

Fetch radiologist calendars for the scheduled date

Filter out radiologists not available during the timestamp

Score each candidate using utils/scoring.py

Sort by score descending

Calendar Matching Logic:
start, end = parse_time_window(entry['available_from'], entry['available_to'])
if start <= scheduled_time <= end:
    # candidate is valid

5. AssignmentAgent

Path: agents/assignment_agent.py

Responsibilities:

Select top-scoring radiologist

Update DB assignments and workloads

Increment resource case counters

Generate LLM explanation

Return structured final output

Key Logic:
WorkRequestsRepo.assign_work(work_id, resource_id)
LLMClient.generate_explanation(llm_input)

Timestamp-Driven Availability Logic

This system is centered around the scheduled timestamp.

Example:

scheduled_date = 2024-11-12
scheduled_time = 10:00
→ 2024-11-12 10:00:00

Radiologist Availability Example:
Radiologist	Availability	At 10:00?
R001	08:00–13:00	✔
R002	14:00–20:00	✘
R003	08:00–16:00	✔
R004	09:00–17:00	✔

Unavailable candidates are immediately removed.

Scoring Model

The scoring engine is transparent and weighted.

Weight Distribution:
Attribute	Weight
Role Match	0.25
Skill Level	0.20
Experience	0.20
Availability	0.20
Workload	0.15
Priority Bonus	+0.15 × (priority/5)
Code:
score = (
    0.25 * role +
    0.20 * skill +
    0.20 * experience +
    0.20 * availability +
    0.15 * workload +
    priority_bonus
)


Detailed breakdown is always returned.

Database Schema & Indexing
Core Tables

resources

resource_calendar

specialty_mapping

work_requests

Indexes:
CREATE INDEX idx_resource_calendar_resource_date
  ON resource_calendar (resource_id, date);

CREATE INDEX idx_work_requests_status
  ON work_requests (status);


These dramatically improve availability filtering and dashboard queries.

Database Repositories

Path: db/repositories.py

Features:

MySQL / SQLite compatible

Placeholder adaptation (%s → ? for SQLite)

Dictionary and row-based responses

Commit management

Encapsulated CRUD operations

LLM Integration

Path: agents/llm_client.py

Agent 5 always calls LLMClient

HuggingFace text generation is preferred

Template fallback ensures reliability

HF Example:
generator = pipeline("text-generation", model=_hf_model_name)

Template Fallback:
"{resource} was assigned... because of skill level, experience, availability..."

Utility Modules
scoring.py

Implements full scoring engine with role, experience, workload, and availability scoring.

time_utils.py

Standardizes parsing and timestamp construction.

FastAPI Interface

Path: main.py

Includes:

CORS

Static UI

Work routes

Resource routes

Health check

Visit:

/ui
/healthz
/work/create
/work/assign/{id}

End-to-End Pipeline Walkthrough
Scenario:
Work Type: CT_Scan_Chest
Priority: 4
Scheduled: 2024-11-12 10:00


Pipeline results in:

R002 eliminated (not available)

R004 highest score

Assignment written to DB

Explanation generated

Key Features & Optimizations

Modular monolithic architecture

Deterministic multi-agent pipeline

Priority-aware scoring

Availability-window filtering

FAISS semantic candidate expansion

Efficient SQL indexes

Template fallback for LLM

Auto-initializing SQLite DB

Clear debug logging

Full transparency via scoring breakdown

Setup Instructions
git clone <repo>
cd work-allocation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


Set .env:

DB_DIALECT=sqlite
HF_LLM_MODEL=distilgpt2


SQLite auto-initializes.

Run Instructions
uvicorn services.api.app.main:app --reload


Visit:

http://localhost:8000/ui

API Endpoints
Create Work
POST /work/create

Assign Work (full pipeline)
POST /work/assign/{work_id}

List Resources
GET /resources/list

List Work
GET /work/list

Required Test Scenarios
Scenario 1: Priority 5 – Urgent Case

Insert screenshots, logs, and scoring table here.

Scenario 2: Priority 2 – Routine Case

Insert screenshots, logs, and scoring table here.

Scenario 3: Priority 3 – Specialized Case

Insert screenshots, logs, and scoring table here.

Image & Diagram Placeholders
