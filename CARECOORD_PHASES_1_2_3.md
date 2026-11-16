# CareCoord – Comprehensive Phase 1, Phase 2 & Phase 3 Documentation

## Executive Overview
**CareCoord** is a stateful, multi-agent AI hospital workflow and resource coordination system. It automates and optimizes critical hospital operations—including patient record lookups, doctor schedule tracking, appointment booking, bed allocation management, emergency triage handling, and operational workflow history tracking.

> **Operational Safety Boundary**: CareCoord operates strictly as an **operational workflow and resource management system**. It does **NOT** provide clinical diagnosis or act as an AI doctor. Critical operational actions (such as finalizing appointment bookings or committing hospital resource alterations) require explicit **Human-in-the-Loop** authorization by hospital staff.

---

## 1. Phase 1: Backend Foundation & Core Data Architecture

### 1.1 Objective & Scope
Phase 1 established the core backend infrastructure required for real-time hospital resource tracking and data management. It features a clean, decoupled architecture using **FastAPI**, **SQLite**, **SQLAlchemy ORM 2.0+**, and **Pydantic v2** validation.

### 1.2 Technology & Data Models
- **Database Engine**: SQLite (`carecoord.db`) managed via SQLAlchemy ORM.
- **Data Validation**: Strict Pydantic schemas preventing invalid inputs (e.g. invalid age ranges, invalid blood groups, unformatted phone numbers).

#### Relational Entities
1. **Patient (`patients`)**: Stores patient demography, medical history summary, contact info, blood group, and current admission status.
2. **Doctor (`doctors`)**: Tracks doctor names, specializations (e.g., Cardiology, Neurology, Orthopedics), availability status, consultation hours, and assigned ward/room.
3. **Appointment (`appointments`)**: Manages scheduled consultations, linking patient ID, doctor ID, date, time slot, department, reason, and status (`scheduled`, `completed`, `cancelled`).
4. **Bed (`beds`)**: Tracks hospital bed inventory across departments (ICU, General Ward, Emergency, Pediatric), bed status (`available`, `occupied`, `maintenance`), and patient assignment.
5. **Emergency (`emergencies`)**: Handles high-priority emergency admissions, recording priority tier (`CRITICAL`, `HIGH`, `MEDIUM`), required department, assigned bed type, and handling doctor.

### 1.3 Synthetic Data Seeding (`backend/seed/seed_database.py`)
An idempotent database seeder populates realistic initial data:
- **20+ Patients** with diverse medical records and demographics.
- **10+ Doctors** across major hospital departments (Cardiology, Neurology, Orthopedics, Pediatrics, Emergency).
- **30+ Beds** categorized by ward type.
- **30+ Scheduled Appointments** and **10+ Active Emergency Triage Records**.

### 1.4 REST API Service Layer
Endpoints supporting standard CRUD operations:
- `GET /health` & `GET /health/database`: System health and table record count diagnostics.
- `GET /api/patients` & `GET /api/patients/{patient_id}`: Patient registry lookups.
- `GET /api/doctors/available` & `GET /api/doctors/specialization/{specialization}`: Real-time doctor query endpoints.
- `GET /api/beds/available` & `GET /api/beds/type/{bed_type}`: Bed availability lookups.
- `POST /api/appointments`: Appointment creation with validation.
- `POST /api/emergencies`: Emergency triage entry creation.

### 1.5 Automated Phase 1 Verification (`test_phase1.py`)
Executed via `python test_phase1.py`, covering 14 verification steps:
1. **Database Seeding**: Verified database setup and population.
2. **Health Check**: `GET /health` returning HTTP 200 `healthy`.
3. **Database Health Metrics**: Verification of count thresholds across all 5 tables.
4. **Patient Retrieval**: Bulk and single-record lookups (e.g. `P001`).
5. **Doctor Queries**: Filtering available doctors and specific specializations (e.g., Cardiology).
6. **Bed Queries**: Filtering available beds and ICU bed types.
7. **Appointment Creation**: Validating `POST /api/appointments` payload processing.
8. **Emergency Triage Creation**: Validating critical priority creation.
9. **Validation Handling**: Asserting HTTP 422 Unprocessable Entity on malformed payloads.
10. **Error Boundaries**: Asserting HTTP 404 Not Found on nonexistent IDs (`P99999`).
11. **Swagger OpenAPI Documentation**: Access verification for `/docs`.

---

## 2. Phase 2: AI Foundation, Request Parsing & CareCoord Dashboard V1

### 2.1 Objective & Scope
Phase 2 introduced natural language processing capabilities to translate natural language user queries into structured operational requests, combined with an interactive web dashboard for real-time monitoring.

### 2.2 Natural Language Request Parser (`backend/services/llm_parser_service.py`)
- **LLM Integration**: Powered by Google Gemini API (`google-genai`), structured via JSON schemas.
- **Deterministic Rule Fallback**: Ensures resilience when offline or in test environments by extracting intent via keyword/pattern matching.
- **Structured Output Schema (`WorkflowParseResult`)**:
  - `request_type`: Categorized into `appointment`, `doctor_search`, `patient_info`, `bed_request`, `emergency`, `unknown`.
  - `urgency`: Priority tier (`ROUTINE`, `URGENT`, `EMERGENCY`).
  - `extracted_entities`: JSON object containing `patient_id`, `doctor_id`, `specialization`, `preferred_date`, `preferred_time`, `bed_type`, etc.
  - `missing_information`: Array of mandatory parameters missing from the user query.

### 2.3 Early Agent Architecture (V1)
- **Patient Agent V1**: Looked up medical history, current admissions, and upcoming consultations for a specific patient.
- **Doctor Agent V1**: Queried available specialists, schedules, and active duty status.
- **Appointment Agent V1**: Checked slot availability and drafted appointment bookings.
- **Clarification Trigger**: When mandatory entities were absent (e.g. query: *"Book an appointment"* without date or doctor), the system flagged `status = clarification_required` and listed missing parameters.

### 2.4 CareCoord Dashboard V1 (React + Vite + Tailwind CSS)
- **Real-Time KPI Cards**: Total Patients, Available Doctors, Bed Occupancy Rate, Active Emergencies.
- **Resource Utilization Bars**: Visual progress indicators for ICU, General Ward, and Emergency beds.
- **Doctor Status Overview**: Quick-glance cards showing doctor duty status and specializations.
- **Interactive Workflow Terminal V1**: Single-turn prompt terminal executing NL requests via `POST /api/workflow/request`.

### 2.5 Automated Phase 2 Verification (`test_phase2.py`)
Executed via `python test_phase2.py`, covering key query pathways:
1. `GET /api/dashboard/summary`: Summary metrics and KPI verification.
2. Query: *"I need an appointment with a cardiologist tomorrow."* $\rightarrow$ Routed to Appointment Agent.
3. Query: *"Find an available neurologist."* $\rightarrow$ Routed to Doctor Agent.
4. Query: *"Show appointments for patient P001."* $\rightarrow$ Routed to Patient Agent.
5. Query: *"Book an appointment."* $\rightarrow$ Triggers clarification response listing missing details.

---

## 3. Phase 3: LangGraph Multi-Agent Architecture & Human Oversight

### 3.1 Objective & Scope
Phase 3 upgraded CareCoord to a **stateful multi-agent system** powered by **LangGraph (`StateGraph`)**. It introduced graph-based state transitions, a central **Coordinator Agent**, specialized DB tools, an operational **Validation Node**, and a strict **Human-in-the-Loop (HITL)** approval boundary.

```mermaid
graph TD
    START([User Request]) --> PR[parse_request node]
    PR --> CA[coordinator node]
    
    CA -->|Route to Doctor Search| DA[doctor_agent node]
    CA -->|Route to Patient Lookup| PA[patient_agent node]
    CA -->|Route to Appointment Booking| AA[appointment_agent node]
    
    DA --> CA
    PA --> CA
    AA --> CA
    
    CA -->|Validate Appointment| VN[validation node]
    VN --> CA
    
    CA -->|Requires Human Staff Approval| HITL{Human Approval Required?}
    HITL -->|Yes| HA[REQUIRES_HUMAN_APPROVAL state]
    HITL -->|No / Completed| FR[final_response node]
    
    HA -->|Staff Approves via UI/API| APP[POST /api/workflows/{id}/approve]
    APP --> DB[(Commit to SQLite Database)]
    DB --> END([COMPLETED Workflow])
    
    FR --> END
```

### 3.2 LangGraph Stateful Engine (`backend/agents/`)

#### State Schema (`CareCoordState`)
Defined in `backend/agents/state.py`:
```python
class CareCoordState(TypedDict):
    workflow_id: str
    original_request: str
    workflow_request: Dict[str, Any]      # Parsed JSON structure
    current_agent: Optional[str]
    required_agents: List[str]            # Calculated agent sequence
    executed_agents: List[str]            # Tracked execution progress
    patient_result: Optional[Dict[str, Any]]
    doctor_result: Optional[Dict[str, Any]]
    appointment_result: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    messages: List[Dict[str, Any]]
    execution_log: List[Dict[str, Any]]   # Audit step log with execution times in ms
    requires_human_review: bool
    status: str                           # RUNNING, NEEDS_CLARIFICATION, REQUIRES_HUMAN_APPROVAL, COMPLETED, FAILED
    final_recommendation: Optional[Dict[str, Any]]
    iteration_count: int                  # Safety depth cap (max 10 iterations)
    error: Optional[str]
    db_session: Any
```

#### Graph Nodes & Execution Pipeline
1. `parse_request`: Converts natural language query into structured parameters.
2. `coordinator`: Decision engine assessing missing parameters, calculating required agents, resolving schedule conflicts, and synthesizing findings.
3. `patient_agent`: Executes DB queries via `patient_tools.py` for patient lookups.
4. `doctor_agent`: Executes DB queries via `doctor_tools.py` to evaluate doctor schedules and availability.
5. `appointment_agent`: Executes DB queries via `appointment_tools.py` to inspect slot availability and construct proposed appointments.
6. `validation`: Operational validation node ensuring non-conflicting schedules, valid IDs, and compliance with hospital rules.
7. `final_response`: Formats operational recommendations and finalizes workflow state.

#### Dynamic Conditional Routing (`route_next_node`)
- **Safety Cap**: Iteration count limit of 10 prevents infinite loops.
- **Early Termination**: Immediately halts on `NEEDS_CLARIFICATION`, `FAILED`, or `REQUIRES_HUMAN_APPROVAL`.
- **Sequential Execution**: Ensures prerequisite nodes execute in order (e.g. `doctor_agent` before `appointment_agent`).

### 3.3 Specialized Tool Layer (`backend/tools/`)
Tools interface directly with SQLite database services:
- `patient_tools.py`: `get_patient_details()`, `get_patient_appointments()`.
- `doctor_tools.py`: `find_available_doctors()`, `get_doctor_schedule()`.
- `appointment_tools.py`: `check_slot_availability()`, `propose_appointment_booking()`.
- `bed_tools.py`: Bed status lookups and allocation stubs.

### 3.4 Human-in-the-Loop (HITL) Safety & Audit System
- **Safety Boundary**: AI agents generate recommendations and validation checks, but **never automatically commit database mutations** (e.g., creating appointments).
- **Approval State**: Workflows involving resource mutations pause at `status = REQUIRES_HUMAN_APPROVAL`.
- **Approval API (`POST /api/workflows/{workflow_id}/approve`)**:
  - Staff selects `action: "approve"` or `action: "reject"` along with optional notes.
  - Upon approval, the database mutation is formally committed, and workflow status transitions to `COMPLETED`.
- **Database Audit Logging**:
  - `workflow_runs`: Stores workflow ID, prompt, final status, agent used, execution duration, and human approval flag.
  - `workflow_events`: Stores granular node-by-node execution logs, timestamps, event types, and execution durations in ms.

### 3.5 Command Center Dashboard V2 Upgrades
- **LangGraph State Visualizer (`WorkflowGraphVisualizer.jsx`)**: Interactive visual graph displaying live step execution, current active node, and completed nodes.
- **Human Approval Card (`HumanApprovalCard.jsx`)**: Displays pending AI recommendations, conflict checks, and action buttons (*Approve & Commit*, *Reject*) directly within the UI.
- **Workflow Detail Drawer (`WorkflowDetailDrawer.jsx`)**: Slide-over drawer detailing step-by-step node execution, tool inputs/outputs, and latency metrics.
- **Workflow History View (`/workflows`)**: Complete audit table listing past workflow runs, statuses, execution durations, and detailed log inspection.

### 3.6 Automated Phase 3 Verification (`test_phase3.py`)
Executed via `python test_phase3.py`, covering 9 verification steps:
1. **Database Reset**: Clean state initialization.
2. **Doctor Search Workflow**: Verified LangGraph execution of *"Find me an available cardiologist"*.
3. **Primary Demo (Human Approval Lifecycle)**: Verified query *"I need an appointment with a cardiologist tomorrow."* correctly halted at `REQUIRES_HUMAN_APPROVAL`.
4. **Workflow History & Detail API**: Validated `GET /api/workflows/{id}` and event log retrieval.
5. **Human Approval API Execution**: Executed `POST /api/workflows/{id}/approve`, verifying status transition to `COMPLETED` and DB record persistence.
6. **Patient Info Workflow**: Verified `Patient Agent` retrieval graph execution for patient `P001`.
7. **Missing Info Clarification**: Verified query *"Book an appointment"* resulted in `NEEDS_CLARIFICATION`.
8. **No Availability Handling**: Asserted clean response handling when target specialization slots are filled.
9. **Audit History Log Verification**: Confirmed SQLite retrieval of workflow runs and event logs.

---

## 4. Comprehensive REST API Reference Across All Completed Phases

| Phase | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Phase 1** | `/health` | GET | Returns overall service health status. |
| **Phase 1** | `/health/database` | GET | Returns SQLite connectivity status and table record counts. |
| **Phase 1** | `/api/patients` | GET | Retrieves list of all registered patients. |
| **Phase 1** | `/api/patients/{patient_id}` | GET | Retrieves detailed patient profile by ID. |
| **Phase 1** | `/api/doctors/available` | GET | Lists currently available doctors. |
| **Phase 1** | `/api/doctors/specialization/{spec}` | GET | Filters doctors by specialization (e.g. Cardiology). |
| **Phase 1** | `/api/beds/available` | GET | Lists all unallocated beds. |
| **Phase 1** | `/api/beds/type/{bed_type}` | GET | Filters available beds by type (e.g. ICU). |
| **Phase 1** | `/api/appointments` | POST | Creates a new appointment record (Direct Service API). |
| **Phase 1** | `/api/emergencies` | POST | Creates an emergency triage record. |
| **Phase 2** | `/api/dashboard/summary` | GET | Aggregates KPIs, bed utilization percentages, and doctor stats. |
| **Phase 2** | `/api/workflow/request` | POST | Single-turn NL workflow execution endpoint (V1). |
| **Phase 3** | `/api/workflows` | POST | Submits natural language request to LangGraph Multi-Agent Engine. |
| **Phase 3** | `/api/workflows` | GET | Retrieves historical workflow run logs. |
| **Phase 3** | `/api/workflows/{id}` | GET | Retrieves detailed workflow run state and event history. |
| **Phase 3** | `/api/workflows/{id}/events` | GET | Retrieves granular node execution events for a workflow. |
| **Phase 3** | `/api/workflows/{id}/approve` | POST | Submits human staff approval or rejection for a pending workflow. |

---

## 5. Comparative Summary Across Phases

| Feature Dimension | Phase 1: Backend Foundation | Phase 2: AI & Dashboard V1 | Phase 3: LangGraph Multi-Agent System |
| :--- | :--- | :--- | :--- |
| **Core Focus** | REST API & SQLite DB CRUD | NL Request Parsing & Basic Dashboard | LangGraph Orchestration & Human Approval |
| **Agent Engine** | None (Direct Service Layer) | Single-turn Deterministic Router | Stateful `StateGraph` Engine |
| **State Management** | Stateless | Stateless | Persistent `CareCoordState` |
| **Tool Execution** | Direct SQL ORM Calls | Service Wrapper Calls | Decoupled Tool Layer (`backend/tools/`) |
| **Safety Boundary** | Input Pydantic Schema | Input Validation | Human-in-the-Loop (`REQUIRES_HUMAN_APPROVAL`) |
| **Audit Logging** | Terminal / Console | Basic Response Payload | SQLite `WorkflowRun` & `WorkflowEvent` Tables |
| **Frontend UI** | None (Swagger Docs) | Dashboard V1 KPI Cards | Command Center V2 with Live Graph & HITL |
| **Automated Verification** | `test_phase1.py` (14 steps) | `test_phase2.py` (6 steps) | `test_phase3.py` (9 steps) |

---

## 6. How to Verify & Run Test Suites

To execute all phase test suites and verify complete system functionality, run the following commands from the project root:

```bash
# 1. Run Phase 1 Verification (Backend CRUD, DB Seeding, API Schemas)
python test_phase1.py

# 2. Run Phase 2 Verification (NL Parsing, Dashboard Summary, Single-turn Agents)
python test_phase2.py

# 3. Run Phase 3 Verification (LangGraph Workflows, Human Approval Lifecycle, Audit Logs)
python test_phase3.py
```
