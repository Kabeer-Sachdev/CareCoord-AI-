# CareCoord – Agentic Healthcare Workflow System

## 1. Project Overview
**CareCoord** is a multi-agent AI hospital workflow and resource coordination system designed for CSE major projects. It coordinates critical hospital operational workflows including patient management, doctor availability tracking, appointment scheduling, bed allocation, emergency handling, nurse/lab coordination, hospital policy retrieval, and resource prediction through specialized AI agents.

> **Important Safety Boundary**: CareCoord is strictly an **operational workflow and resource coordination system**, NOT a medical diagnosis system or AI doctor. Final clinical and operational decisions remain under authorized human hospital staff.

---

## 2. Problem Statement
Hospitals face daily operational bottlenecks due to fragmented communication between departments, manual bed allocations, uncoordinated emergency room admissions, and inefficient doctor scheduling. CareCoord resolves these challenges by providing a stateful, tool-grounded multi-agent system that orchestrates hospital operations in real time with human oversight.

---

## 3. Implementation Status & Phase Roadmap

### Phase 1: Backend Foundation (Completed)
Established the clean hospital management backend (FastAPI + SQLite + SQLAlchemy + Pydantic) with synthetic hospital data and decoupled service layer. Verified via `test_phase1.py`.

### Phase 2: AI Foundation & CareCoord Dashboard V1 (Completed)
- Introduced natural-language request parsing via structured JSON schemas and safety system prompts.
- Built initial **Patient Agent**, **Doctor Agent**, and **Appointment Agent**.
- Built **CARECOORD DASHBOARD V1** using React, Vite, and Tailwind CSS. Verified via `test_phase2.py`.

### Phase 3: LangGraph Multi-Agent Architecture & Human Oversight (Completed)
- **LangGraph Stateful Engine**: State graph orchestrating node execution (`parse_request` $\rightarrow$ `coordinator` $\rightarrow$ specialized tool nodes $\rightarrow$ `validation` $\rightarrow$ `human_review` $\rightarrow$ `final_response`).
- **Coordinator Agent**: Operational decision engine selecting required agents, managing handoffs, detecting missing information (`NEEDS_CLARIFICATION`), resolving slot conflicts, and compiling recommendations.
- **Tool Architecture**: Specialized tool layer (`backend/tools/`) directly querying SQLite database services (`PatientService`, `DoctorService`, `AppointmentService`, `BedService`).
- **Human-in-the-Loop Boundary**: Operational database mutations (e.g. creating appointments) are **not** automatically committed upon AI recommendation. The system enters `REQUIRES_HUMAN_APPROVAL` until staff authorizes via UI or `POST /api/workflows/{workflow_id}/approve` API.
- **Database Audit Logging**: `workflow_runs` and `workflow_events` tables tracking granular execution logs, tool calls, and execution times in ms.
- **Upgraded Command Center Dashboard**: Integrated live **LangGraph State Visualizer**, interactive **Human Approval Card**, **Workflow Detail Drawer**, and **Workflow History** page (`/workflows`). Verified via `test_phase3.py`.

---

## 4. Technology Stack

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **Agent Orchestration**: LangGraph (`StateGraph`)
- **ASGI Server**: Uvicorn
- **Database**: SQLite (`carecoord.db`)
- **ORM Layer**: SQLAlchemy 2.0+
- **Data Validation**: Pydantic v2
- **LLM Integration**: Google Gemini API (`google-genai`) with fallback rule parser

### Frontend
- **Framework**: React 18 + Vite 5
- **Styling**: Tailwind CSS v3
- **Icons**: Lucide React
- **HTTP Client**: Native Fetch API service wrapper

---

## 5. Target Architecture

```text
                         CARECOORD COMMAND CENTER
                                    │
                                    ▼
                          React Dashboard (Vite)
                                    │
                                    ▼
                            FastAPI Backend
                                    │
                                    ▼
                            Coordinator Agent
                                    │
                                LangGraph
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       │                            │                            │
       ▼                            ▼                            ▼
 Patient Agent                Doctor Agent              Appointment Agent
       │                            │                            │
       ▼                            ▼                            ▼
 Patient Tools                Doctor Tools              Appointment Tools
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    │
                                    ▼
                              Validation Node
                                    │
                                    ▼
                              Service Layer
                                    │
                                    ▼
                             SQLite Database
```

---

## 6. Folder Structure
```text
CareCoord/
│
├── backend/
│   ├── main.py                    # FastAPI app, lifespan, CORS & router registrations
│   ├── config/
│   │   └── settings.py            # System settings & DB URI
│   ├── database/
│   │   ├── database.py            # SQLite engine, SessionLocal, init_db()
│   │   └── models.py              # Patient, Doctor, Appointment, Bed, Emergency, WorkflowRun, WorkflowEvent ORM models
│   ├── schemas/
│   │   ├── patient.py / doctor.py / appointment.py / bed.py / emergency.py
│   │   └── workflow.py            # WorkflowRequest, WorkflowParseResult, WorkflowResponse, WorkflowRunResponse, WorkflowEventResponse
│   ├── agents/
│   │   ├── state.py               # CareCoordState TypedDict schema
│   │   ├── coordinator_agent.py   # Coordinator Agent decision engine
│   │   ├── patient_agent.py       # Patient Agent node handler
│   │   ├── doctor_agent.py        # Doctor Agent node handler
│   │   ├── appointment_agent.py   # Appointment Agent node handler
│   │   ├── validation_agent.py    # Operational Validation Node
│   │   └── graph.py               # LangGraph StateGraph engine & conditional routing
│   ├── tools/
│   │   ├── patient_tools.py       # DB tools for patient lookups
│   │   ├── doctor_tools.py        # DB tools for doctor availability & schedules
│   │   ├── appointment_tools.py   # DB tools for slot checking & appointment creation
│   │   └── bed_tools.py           # Phase 4 bed tools stubs
│   ├── routes/
│   │   ├── patients.py / doctors.py / appointments.py / beds.py / emergencies.py
│   │   ├── dashboard.py           # GET /api/dashboard/summary endpoint
│   │   └── workflow.py            # Phase 3 LangGraph & workflow history/approval API routes
│   ├── services/
│   │   ├── patient_service.py / doctor_service.py / appointment_service.py / bed_service.py / emergency_service.py
│   │   ├── llm_parser_service.py  # Structured LLM natural-language request parser
│   │   └── workflow_service.py   # Workflow execution service & SQLite audit logger
│   └── seed/
│       └── seed_database.py       # Idempotent synthetic data population script
│
├── frontend/
│   ├── src/
│   │   ├── components/            # Sidebar, Topbar, KpiCard, ProgressBar, StatusBadge, WorkflowGraphVisualizer, HumanApprovalCard, WorkflowDetailDrawer
│   │   ├── pages/                 # Overview, Patients, Doctors, Appointments, AiAgents, WorkflowRequest, WorkflowHistory
│   │   ├── services/
│   │   │   └── api.js             # API client service wrapper
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── carecoord.db                   # SQLite database (auto-created)
├── test_phase1.py                 # Automated test suite for Phase 1
├── test_phase2.py                 # Automated test suite for Phase 2
├── test_phase3.py                 # Automated test suite for Phase 3 LangGraph Multi-Agent Workflows
├── requirements.txt
└── README.md
```

---

## 7. How to Run

### 1. Backend Setup
Activate virtual environment and install dependencies:
```bash
python -m venv venv
# Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

Seed synthetic hospital data:
```bash
python -m backend.seed.seed_database
```

Run FastAPI backend server:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

- Backend Service Root: [http://localhost:8000/](http://localhost:8000/)
- Swagger API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup
In a separate terminal, install npm packages and start Vite dev server:
```bash
cd frontend
npm install
npm run dev
```

Open your browser at [http://localhost:5173/](http://localhost:5173/) to access **CareCoord Command Center**.

---

## 8. Automated Test Verification

Run automated test suites to verify system correctness across all phases:
```bash
python test_phase1.py   # Tests Phase 1 backend CRUD services
python test_phase2.py   # Tests Phase 2 request parsing & deterministic routing
python test_phase3.py   # Tests Phase 3 LangGraph multi-agent orchestration & human approval
```

---

## 9. Sample Multi-Agent Demonstration Queries

Try these queries in the **Workflow Command Terminal** (`/workflow`):
1. `"I need an appointment with a cardiologist tomorrow."` *(Primary Demo: Doctor Agent $\rightarrow$ Appointment Agent $\rightarrow$ Validation Node $\rightarrow$ Human Approval Card $\rightarrow$ Database Mutation)*
2. `"Find me an available cardiologist."` *(Doctor Search Workflow)*
3. `"Show appointments for patient P001."` *(Patient Information Workflow)*
4. `"Book an appointment."` *(Triggers NEEDS_CLARIFICATION prompt)*
5. `"Find an available neurologist."` *(Doctor Availability Lookup)*

---

## 10. Future Phases Roadmap
- **Phase 4**: Bed Allocation, Nurse Coordination & Emergency Triage Agents (LangGraph expansion)
- **Phase 5**: RAG Policy Retrieval Agent (ChromaDB + Vector Index)
- **Phase 6**: ML Resource Surge Prediction (XGBoost / Scikit-Learn)
- **Phase 7**: OR-Tools Operations & Bed Transfer Optimization
- **Phase 8**: System Evaluation & Production Deployment
