# CareCoord – PowerPoint Presentation Slide Deck & Speaker Notes

This document contains the complete 11-slide text outline, structure, and speaker notes for the **CareCoord Major Project Defense PowerPoint Presentation**. The corresponding `.pptx` file has been generated and saved to [`CareCoord_Major_Project_Presentation.pptx`](file:///c:/Users/sachd/OneDrive/Desktop/CareCoord%20Major/CareCoord_Major_Project_Presentation.pptx).

---

## Slide 1: Title Slide (Hero Slide)
* **Title**: **CareCoord: Agentic Healthcare Workflow System**
* **Subtitle**: Stateful Multi-Agent Orchestration with LangGraph & Human-in-the-Loop Safety Oversight
* **Category**: CSE Major Project Defense Presentation
* **Presenter Info**: Department of Computer Science & Engineering
* **Speaker Notes**:
  > *"Good morning/afternoon. Today I present CareCoord, a stateful multi-agent AI system designed to resolve critical hospital operational bottlenecks through automated resource coordination, appointment scheduling, bed management, and human-in-the-loop safety governance."*

---

## Slide 2: Project Overview & Problem Statement
* **Left Column — Problem Statement in Hospital Operations**:
  - **Fragmented Communication**: Hospital departments (Doctors, Beds, Admissions) operate in uncoordinated silos.
  - **Manual Bed & Slot Allocation**: Staff waste critical time checking spreadsheets and phone calls.
  - **Delayed Emergency Triage**: High-priority admissions experience bottlenecks due to lack of real-time resource tracking.
  - **Lack of Unified Auditability**: Operational history and decision steps are rarely logged with millisecond precision.
* **Right Column — CareCoord Multi-Agent Solution**:
  - **Stateful AI Multi-Agent System**: Autonomous agents orchestrating hospital workflows in real time.
  - **LangGraph Engine**: Structured execution graph with state persistence and conflict detection.
  - **Human-in-the-Loop Safety Boundary**: Strict requirement where AI suggests proposals, but human staff authorize database mutations.
  - **Non-Clinical Operational Scope**: Focuses purely on resource coordination, appointment scheduling, and bed tracking.

---

## Slide 3: Implementation Roadmap Across Phases
* **Phase 1: Backend Foundation**:
  - Clean FastAPI Architecture with Uvicorn server.
  - SQLite Database (`carecoord.db`) with SQLAlchemy 2.0 ORM.
  - 5 Relational Models: `Patient`, `Doctor`, `Appointment`, `Bed`, `Emergency`.
  - Pydantic v2 Schema Validation.
  - 14-Step Automated Verification Suite (`test_phase1.py`).
* **Phase 2: AI Foundation & UI V1**:
  - Natural Language Request Parser powered by Google Gemini API (`google-genai`).
  - Structured JSON Parse Result (`WorkflowParseResult`) & Intent Classification.
  - Early Single-Turn Agents (`PatientAgent`, `DoctorAgent`, `AppointmentAgent`).
  - Missing Parameter Clarification Prompts (`NEEDS_CLARIFICATION`).
  - React + Vite + Tailwind CSS Command Center V1.
* **Phase 3: LangGraph Architecture**:
  - LangGraph `StateGraph` Engine (`CareCoordState`).
  - Coordinator Agent & Specialized Tool Layer (`backend/tools/`).
  - Operational Validation Node & Rule Checker (`ValidationAgent`).
  - Human-in-the-Loop (HITL) Approval Boundary (`REQUIRES_HUMAN_APPROVAL`).
  - SQLite Audit Logging (`workflow_runs` & `workflow_events`).
  - Live Graph Visualizer & Audit History Page (`/workflows`).

---

## Slide 4: System Target Architecture & Data Flow
* **End-to-End Pipeline Steps**:
  1. **Command Center UI (React 18 + Vite)**: User submits natural language query via Workflow Terminal.
  2. **FastAPI REST Endpoint (`POST /api/workflows`)**: Receives request and initializes execution session.
  3. **LangGraph Request Parser (`parse_request` node)**: Invokes Gemini LLM to extract intent and entities.
  4. **Coordinator Agent (`coordinator` node)**: Calculates required agents, resolves slot conflicts, and routes state.
  5. **Specialized Tool Execution (`patient`, `doctor`, `appointment` nodes)**: Interacts directly with SQLite database services.
  6. **Validation Node & HITL Boundary**: Pauses mutation state at `REQUIRES_HUMAN_APPROVAL`.
  7. **Staff Authorization & Database Commit**: Staff approves via UI (`POST /api/workflows/{id}/approve`) to commit database record.

---

## Slide 5: LangGraph Stateful Engine & Execution Graph
* **Left Column — `CareCoordState` Schema**:
  - `workflow_id`: Unique string identifying the run.
  - `original_request`: Raw natural language prompt.
  - `workflow_request`: Structured JSON payload.
  - `required_agents` & `executed_agents`: Sequence & progress tracking lists.
  - `execution_log`: Step-by-step latency & tool event log.
  - `status`: `RUNNING`, `NEEDS_CLARIFICATION`, `REQUIRES_HUMAN_APPROVAL`, `COMPLETED`.
  - `iteration_count`: Safety depth cap (Max 10 iterations).
* **Right Column — Node Graph Execution Sequence**:
  - `parse_request`: Natural language parsing node.
  - `coordinator`: Central decision engine & router.
  - `doctor_agent`: Doctor schedule & availability lookup.
  - `patient_agent`: Patient history & record retrieval.
  - `appointment_agent`: Slot availability check & booking draft.
  - `validation`: Rules compliance & HITL flag trigger.
  - `final_response`: Formats operational output recommendation.

---

## Slide 6: Specialized AI Agents & Tool Layer
* **Coordinator Agent**: Acts as central orchestrator. Detects missing information (triggers clarification). Resolves schedule conflicts between doctors and patients.
* **Doctor Agent & `doctor_tools.py`**: Queries doctor availability status. Filters specialists by department (e.g. Cardiology). Checks shift times and active patient load.
* **Patient Agent & `patient_tools.py`**: Retrieves demographic details for patient IDs. Queries upcoming scheduled consultations. Fetches medical history summary.
* **Appointment Agent & `appointment_tools.py`**: Evaluates slot availability for target dates. Drafts appointment creation payloads. Hands off proposed booking to Validation Node.

---

## Slide 7: Human-in-the-Loop (HITL) Operational Safety Boundary
* **Operational Safety Mandate & Workflow Lifecycle**:
  - **Safety Core Rule**: AI agents are NEVER permitted to commit database mutations automatically.
  - **State Interception**: Operations involving resource allocation (creating appointments, assigning beds) halt execution at `REQUIRES_HUMAN_APPROVAL`.
  - **Staff Command Card (`HumanApprovalCard.jsx`)**: Displays proposed AI booking details, doctor info, slot time, and validation checks.
  - **Staff Review Actions**: Authorized hospital staff click *"Approve & Commit"* or *"Reject"* with optional review notes.
  - **Database Commit API (`POST /api/workflows/{id}/approve`)**: Commits the record to SQLite and updates status to `COMPLETED` upon explicit approval.

---

## Slide 8: CareCoord Command Center Dashboard V2
* **Left Column — Frontend UI Architecture**:
  - **Framework**: React 18 + Vite 5 + Tailwind CSS v3.
  - **KPI Cards**: Real-time count of total patients, available doctors, bed occupancy rate, and emergencies.
  - **Resource Utilization**: Visual progress bars tracking ICU, General Ward, and Emergency bed capacity.
  - **Workflow Terminal**: Prompts users with query samples and live status badges.
* **Right Column — Live Graph & Audit Components**:
  - `WorkflowGraphVisualizer.jsx`: Renders state graph nodes, highlighting current active agent and completed path.
  - `WorkflowDetailDrawer.jsx`: Slide-over inspection drawer detailing step execution latencies in ms and tool outputs.
  - **Workflow History (`/workflows`)**: Persistent table listing all previous workflow runs, statuses, and logs.

---

## Slide 9: Automated Verification & Test Suites
* **`test_phase1.py` (14 Steps)**: Database Seed Script Execution, `GET /health` Endpoint (200 OK), Database Table Count Metrics, Patient & Doctor Filter Queries, Bed Type Availability Queries, Appointment & Emergency POST, HTTP 422 Payload Validation, HTTP 404 Nonexistent ID Boundary.
* **`test_phase2.py` (6 Steps)**: `GET /api/dashboard/summary` KPI Assertions, Cardiologist Query $\rightarrow$ Appointment Agent, Neurologist Search $\rightarrow$ Doctor Agent, Patient P001 Query $\rightarrow$ Patient Agent, Incomplete Query $\rightarrow$ Clarification Required.
* **`test_phase3.py` (9 Steps)**: LangGraph `StateGraph` Execution, Primary Demo Query Halting at `REQUIRES_HUMAN_APPROVAL`, `GET /api/workflows/{id}/events` Log Retrieval, `POST /api/workflows/{id}/approve` Execution & DB Commit, Workflow Audit History Logging.

---

## Slide 10: Academic & Foundational References
1. **Topol et al.** (*Nature Medicine / PMC*): Multiagent AI Systems in Health Care: Envisioning Next-Generation Intelligence.
2. **Qian et al.** (*arXiv:2307.07924*): Communicative Agents for Software Development & Task Orchestration.
3. **Ben Ali et al.** (*Journal of Medical Systems*): Healthcare Decision Support Tool: Multi-Agent System for Bed Management.
4. **Yeoh et al.** (*IEEE Transactions / arXiv*): A Coordinated MDP Approach to Multi-Agent Resource Allocation.
5. **Amann et al.** (*BMC Medical Informatics*): Human-in-the-Loop AI Systems for Clinical Decision Support.
6. **Chase et al.** (*LangChain Technical Reports*): LangGraph Stateful Graph Execution Frameworks.

---

## Slide 11: Conclusion & Future Roadmap
* **Project Achievements**:
  - Successfully developed clean FastAPI + SQLite backend foundation.
  - Implemented structured Gemini LLM natural language parser.
  - Built stateful LangGraph multi-agent engine with 10-iteration loop safety cap.
  - Established strict Human-in-the-Loop safety boundary and audit logging.
  - Delivered Command Center UI V2 with live state visualizer and history.
* **Future Expansion Roadmap**:
  - **Phase 4**: Bed Allocation & Nurse Triage LangGraph Expansion.
  - **Phase 5**: RAG Policy Retrieval Agent (ChromaDB + Vector Index).
  - **Phase 6**: ML Resource Surge Prediction (XGBoost / Scikit-Learn).
  - **Phase 7**: OR-Tools Operations & Bed Transfer Optimization.
  - **Phase 8**: Production Cloud Deployment & Containerization.
