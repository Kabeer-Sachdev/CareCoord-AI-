# CareCoord - Agentic Healthcare Workflow System

## 1. Project Overview
**CareCoord** is a multi-agent AI-based hospital workflow coordination system designed for CSE major projects. It coordinates critical hospital operational workflows such as patient management, doctor availability tracking, appointment scheduling, bed allocation, emergency handling, nurse/lab coordination, hospital policy retrieval, and resource prediction through specialized AI agents.

> **Important Note**: CareCoord is strictly intended for **workflow and resource coordination**, NOT medical diagnosis or autonomous clinical decision-making. Final operational decisions remain with authorized hospital staff.

---

## 2. Problem Statement
Hospitals daily face critical bottlenecks due to fragmented communication between departments, manual bed allocations, uncoordinated emergency room admissions, and inefficient doctor scheduling. CareCoord solves these challenges by providing a modular, tool-backed agentic framework that streamlines hospital operations in real time.

---

## 3. Phase Objectives

### Phase 1: Backend Foundation (Completed)
Established the clean hospital management backend (FastAPI + SQLite + SQLAlchemy + Pydantic) with synthetic hospital data and decoupled service layer.

### Phase 2: AI Foundation & CareCoord Dashboard V1 (Completed)
- Introduced natural-language operational request parsing using LLM SDK with structured JSON schemas and safety system prompts.
- Created **Patient Agent**, **Doctor Agent**, and **Appointment Agent** consuming Phase 1 service tools.
- Implemented deterministic request router (`WorkflowService`).
- Built **CARECOORD DASHBOARD V1** — a modern hospital operations command center UI using React, Vite, and Tailwind CSS.

---

## 4. Technology Stack

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Database**: SQLite (`carecoord.db`)
- **ORM Layer**: SQLAlchemy 2.0+
- **Data Validation**: Pydantic v2
- **Configuration**: python-dotenv

### Frontend & AI
- **Framework**: React 18 + Vite 5
- **Styling**: Tailwind CSS v3
- **Icons**: Lucide React
- **LLM Integration**: Google Gemini API / OpenAI SDK with fallback heuristic parser

---

## 5. Architecture
```
                         CARECOORD COMMAND CENTER
                                    │
                                    ▼
                         React Dashboard (Vite)
                                    │
                                    ▼
                            FastAPI Backend
                                    │
              ┌─────────────────────┴─────────────────────┐
              ▼                                           ▼
       Workflow Request                            Dashboard Summary
       (/api/workflow/request)                    (/api/dashboard/summary)
              │                                           │
              ▼                                           ▼
     LLM Parser / Fallback                           SQLite Database
              │                                      (carecoord.db)
              ▼
      Structured Request
              │
              ▼
       Deterministic Router
          /       |       \
         /        |        \
        ▼         ▼         ▼
     Patient    Doctor   Appointment
      Agent      Agent      Agent
        \         |         /
         \        |        /
          ▼       ▼       ▼
             Service Layer
                  │
                  ▼
         SQLite (carecoord.db)
```

---

## 6. Folder Structure
```
CareCoord/
│
├── backend/
│   ├── main.py                    # FastAPI app, lifespan, CORS & router registrations
│   ├── config/
│   │   └── settings.py            # System settings & DB URI
│   ├── database/
│   │   ├── database.py            # SQLite engine, SessionLocal, init_db()
│   │   └── models.py              # Patient, Doctor, Appointment, Bed, Emergency ORM models
│   ├── schemas/
│   │   ├── patient.py / doctor.py / appointment.py / bed.py / emergency.py
│   │   └── workflow.py            # WorkflowRequest, WorkflowParseResult, WorkflowResponse
│   ├── agents/
│   │   ├── patient_agent.py       # Patient Agent logic
│   │   ├── doctor_agent.py        # Doctor Agent logic
│   │   └── appointment_agent.py   # Appointment Agent logic
│   ├── routes/
│   │   ├── patients.py / doctors.py / appointments.py / beds.py / emergencies.py
│   │   ├── dashboard.py           # GET /api/dashboard/summary endpoint
│   │   └── workflow.py            # POST /api/workflow/request endpoint
│   ├── services/
│   │   ├── patient_service.py / doctor_service.py / appointment_service.py / bed_service.py / emergency_service.py
│   │   ├── llm_parser_service.py  # Structured LLM natural-language request parser
│   │   └── workflow_service.py   # Request router to specialized agents
│   └── seed/
│       └── seed_database.py       # Idempotent synthetic data population script
│
├── frontend/
│   ├── src/
│   │   ├── components/            # Sidebar, Topbar, KpiCard, ProgressBar, StatusBadge, DataTable, AgentStatusCard, ActivityTimeline
│   │   ├── pages/                 # Overview, Patients, Doctors, Appointments, AiAgents, WorkflowRequest
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
├── test_phase2.py                 # Automated test suite for Phase 2 AI & Dashboard
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

### 2. Frontend Setup
In a separate terminal, install npm packages and start Vite dev server:
```bash
cd frontend
npm install
npm run dev
```

Open your browser at [http://localhost:5173/](http://localhost:5173/) to access **CareCoord Dashboard V1**.

---

## 8. Sample Natural Language Workflow Queries

Try these queries in the **Workflow Terminal**:
1. `"I need an appointment with a cardiologist tomorrow."`
2. `"Find an available neurologist."`
3. `"Show appointments for patient P001."`
4. `"Find an available doctor."`
5. `"Book an appointment."` *(Triggers clarification prompt)*

---

## 9. Future Phases Roadmap
- **Phase 3**: Coordinator Agent + Specialized Agents (Doctor, Bed, Appointment, Emergency) using LangGraph
- **Phase 4**: RAG / Hospital Policy Retrieval Agent (ChromaDB + Vector Store)
- **Phase 5**: Nurse / Lab / Pharmacy Agent Integration
- **Phase 6**: Machine Learning Resource Prediction (XGBoost / Scikit-Learn)
- **Phase 7**: Operations & Bed Allocation Optimization (OR-Tools)
- **Phase 8**: Interactive Web Dashboard, Evaluation & Deployment
