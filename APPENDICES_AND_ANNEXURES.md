# Appendices & Institutional Annexures: CareCoord System

This document contains **Appendix A**, **Appendix B**, and **Appendix C** for the academic and technical documentation of **CareCoord: Agentic Healthcare Workflow System**.

---

# Appendix A: Data Architecture, Schemas & API Specifications

## A.1 Relational Database Schemas (SQLite / SQLAlchemy)

### 1. `patients` Table Schema
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal surrogate key |
| `patient_id` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Business key (e.g. `P001`) |
| `name` | VARCHAR(100) | NOT NULL | Patient full name |
| `age` | INTEGER | NOT NULL | Age in years (validated $\le 120$) |
| `gender` | VARCHAR(20) | NOT NULL | Gender specification |
| `phone` | VARCHAR(20) | NOT NULL | Contact telephone number |
| `department` | VARCHAR(100) | NOT NULL | Primary registered department |
| `blood_group` | VARCHAR(10) | NOT NULL | Blood type (e.g. `A+`, `O-`) |
| `existing_conditions` | JSON | NULLABLE | List of chronic diagnoses/allergies |
| `created_at` | DATETIME | DEFAULT UTC | Registration timestamp |

### 2. `doctors` Table Schema
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal surrogate key |
| `doctor_id` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Business key (e.g. `D001`) |
| `name` | VARCHAR(100) | NOT NULL | Doctor full name |
| `specialization` | VARCHAR(100) | NOT NULL | Clinical specialty (e.g., Cardiology) |
| `department` | VARCHAR(100) | NOT NULL | Department assignment |
| `experience_years` | INTEGER | DEFAULT 0 | Years of clinical practice |
| `availability` | BOOLEAN | DEFAULT TRUE | Current duty availability flag |
| `shift` | VARCHAR(50) | NOT NULL | Work shift (e.g. `Morning`, `Night`) |
| `current_patients` | INTEGER | DEFAULT 0 | Active assigned patient load |

### 3. `appointments` Table Schema
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal surrogate key |
| `appointment_id` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Business key (e.g. `APT-1001`) |
| `patient_id` | VARCHAR(50) | FOREIGN KEY (`patients.patient_id`) | Patient reference |
| `doctor_id` | VARCHAR(50) | FOREIGN KEY (`doctors.doctor_id`) | Doctor reference |
| `appointment_date` | VARCHAR(20) | NOT NULL | Date string (`YYYY-MM-DD`) |
| `appointment_time` | VARCHAR(20) | NOT NULL | Time string (`HH:MM`) |
| `department` | VARCHAR(100) | NOT NULL | Department string |
| `status` | VARCHAR(20) | DEFAULT `'scheduled'` | Status (`scheduled`, `completed`, `cancelled`, `pending`) |
| `reason` | TEXT | NULLABLE | Consultation reason |
| `created_at` | DATETIME | DEFAULT UTC | Record creation timestamp |

### 4. `beds` Table Schema
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal surrogate key |
| `bed_id` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Business key (e.g. `BED-ICU-01`) |
| `ward` | VARCHAR(50) | NOT NULL | Ward location |
| `bed_type` | VARCHAR(50) | NOT NULL | Bed type (`General`, `ICU`, `Emergency`, `Private`) |
| `status` | VARCHAR(20) | DEFAULT `'available'` | Allocation status (`available`, `occupied`, `maintenance`) |
| `floor` | INTEGER | NOT NULL | Floor index |
| `patient_id` | VARCHAR(50) | FOREIGN KEY (`patients.patient_id`) | Occupying patient (if allocated) |

### 5. `emergencies` Table Schema
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal surrogate key |
| `emergency_id` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Business key (e.g. `EMG-5001`) |
| `patient_id` | VARCHAR(50) | FOREIGN KEY (`patients.patient_id`) | Patient reference |
| `priority` | VARCHAR(20) | NOT NULL | Triage tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) |
| `required_department`| VARCHAR(100) | NOT NULL | Target clinical department |
| `required_bed_type`  | VARCHAR(50) | NOT NULL | Target bed specification |
| `assigned_doctor_id` | VARCHAR(50) | FOREIGN KEY (`doctors.doctor_id`) | Attending physician |
| `status` | VARCHAR(20) | DEFAULT `'waiting'` | Lifecycle status (`waiting`, `allocated`, `completed`) |
| `created_at` | DATETIME | DEFAULT UTC | Triage entry timestamp |

### 6. `workflow_runs` Audit Table Schema
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal surrogate key |
| `workflow_id` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Workflow run ID |
| `original_request` | TEXT | NOT NULL | Raw NL user query |
| `workflow_type` | VARCHAR(50) | NOT NULL | Parsed category (`appointment`, `doctor_search`, etc.) |
| `status` | VARCHAR(50) | NOT NULL | Workflow status (`RUNNING`, `REQUIRES_HUMAN_APPROVAL`, etc.) |
| `requires_human_approval` | BOOLEAN | DEFAULT FALSE | Human authorization flag |
| `agent_used` | VARCHAR(100) | NULLABLE | Primary agent executed |
| `recommendation` | TEXT | NULLABLE | AI proposed recommendation text |
| `final_result` | JSON | NULLABLE | Structured execution result payload |
| `started_at` | DATETIME | DEFAULT UTC | Graph start timestamp |
| `completed_at` | DATETIME | NULLABLE | Graph completion timestamp |

### 7. `workflow_events` Audit Log Table Schema
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal surrogate key |
| `workflow_id` | VARCHAR(50) | FOREIGN KEY (`workflow_runs.workflow_id`) | Associated workflow run |
| `timestamp` | DATETIME | DEFAULT UTC | Event timestamp |
| `agent_name` | VARCHAR(50) | NOT NULL | Name of node/agent |
| `node_name` | VARCHAR(50) | NOT NULL | LangGraph node name |
| `event_type` | VARCHAR(50) | NOT NULL | Event classification (`node_start`, `tool_call`, etc.) |
| `status` | VARCHAR(50) | NOT NULL | Step execution status |
| `tool_name` | VARCHAR(50) | NULLABLE | Database tool executed |
| `execution_time_ms` | INTEGER | NULLABLE | Latency in milliseconds |
| `details` | JSON | NULLABLE | Input parameters / tool outputs |

---

## A.2 LangGraph State Definition (`CareCoordState`)

```python
from typing import TypedDict, List, Dict, Any, Optional

class CareCoordState(TypedDict):
    workflow_id: str
    original_request: str
    workflow_request: Dict[str, Any]      # Parsed LLM JSON structure
    current_agent: Optional[str]
    required_agents: List[str]            # Sequence of required agents
    executed_agents: List[str]            # Progress tracker
    
    patient_result: Optional[Dict[str, Any]]
    doctor_result: Optional[Dict[str, Any]]
    appointment_result: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    
    messages: List[Dict[str, Any]]
    execution_log: List[Dict[str, Any]]   # Audit step log
    
    requires_human_review: bool
    status: str                           # RUNNING, NEEDS_CLARIFICATION, REQUIRES_HUMAN_APPROVAL, APPROVED, REJECTED, COMPLETED, FAILED
    final_recommendation: Optional[Dict[str, Any]]
    iteration_count: int                  # Infinite loop safety cap (max 10)
    error: Optional[str]
    db_session: Any                       # SQLAlchemy session handle
```

---

## A.3 Pydantic Data Models (`backend/schemas/workflow.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class WorkflowParseResult(BaseModel):
    request_type: str = Field(..., description="Categorized request type: appointment, doctor_search, patient_info, bed_request, emergency, unknown")
    urgency: str = Field(default="ROUTINE", description="Priority tier: ROUTINE, URGENT, EMERGENCY")
    extracted_entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters (patient_id, doctor_id, specialization, preferred_date, etc.)")
    missing_information: List[str] = Field(default_factory=list, description="Mandatory missing attributes")
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0)
    reasoning: Optional[str] = None

class WorkflowRequest(BaseModel):
    message: str = Field(..., min_length=2, description="Natural language prompt")

class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    requires_human_approval: bool
    agent_used: str
    recommendation: str
    data: Optional[Dict[str, Any]] = None
    steps: List[str] = []
```

---

# Appendix B: Automated Verification Logs & Test Suite Execution Outputs

## B.1 Phase 1 Test Execution Log (`python test_phase1.py`)

```text
==================================================
  RUNNING CARECOORD PHASE 1 BACKEND VERIFICATION  
==================================================

[Step 1] Running database seed script...
Initializing database tables...
Seeding synthetic data...
Seeding completed successfully!

[Step 2] Testing GET /health...
  -> PASSED: {'status': 'healthy', 'system': 'CareCoord Operational Management System'}

[Step 3] Testing GET /health/database...
  -> PASSED: {'patients': 20, 'doctors': 10, 'beds': 30, 'appointments': 31, 'emergencies': 16}

[Step 4] Testing GET /api/patients...
  -> PASSED: Retrieved 20 patients. Sample: Rahul Sharma

[Step 5] Testing GET /api/patients/P001...
  -> PASSED: Patient P001 name: Rahul Sharma

[Step 6] Testing GET /api/doctors/available...
  -> PASSED: Found 7 available doctors.

[Step 7] Testing GET /api/doctors/specialization/Cardiology...
  -> PASSED: Found 2 Cardiology specialists.

[Step 8] Testing GET /api/beds/available...
  -> PASSED: Found 18 available beds.

[Step 9] Testing GET /api/beds/type/ICU...
  -> PASSED: Found 4 available ICU beds.

[Step 10] Testing POST /api/appointments...
  -> PASSED: Created appointment ID: APT-1032

[Step 11] Testing POST /api/emergencies...
  -> PASSED: Created emergency ID: EMG-5017

[Step 12] Testing Invalid Input (Validation Error 422)...
  -> PASSED: Correctly returned HTTP 422 Unprocessable Entity for invalid patient payload.

[Step 13] Testing Nonexistent ID (404 Not Found)...
  -> PASSED: Correctly returned HTTP 404 for non-existent patient ID 'P99999'.

[Step 14] Testing Swagger /docs availability...
  -> PASSED: /docs accessible successfully.

==================================================
  ALL 14 VERIFICATION STEPS PASSED SUCCESSFULLY!  
==================================================
```

---

## B.2 Phase 2 Test Execution Log (`python test_phase2.py`)

```text
==================================================
  RUNNING CARECOORD PHASE 2 BACKEND VERIFICATION  
==================================================

[Step 1] Testing GET /api/dashboard/summary...
  -> PASSED KPIs: {'total_patients': 20, 'available_doctors': 7, 'bed_occupancy_rate': 40.0, 'active_emergencies': 16}
  -> PASSED Utilization: {'ICU': {'total': 8, 'occupied': 4, 'percentage': 50.0}, 'General': {'total': 15, 'occupied': 6, 'percentage': 40.0}}

[Step 2] Testing Query 1: 'I need an appointment with a cardiologist tomorrow.'...
  -> PASSED Agent: Appointment Agent
  -> Recommendation: Proposed appointment with Dr. Mehta for Cardiology consultation.

[Step 3] Testing Query 2: 'Find an available neurologist.'...
  -> PASSED Agent: Doctor Agent
  -> Recommendation: Found available Neurologist: Dr. Ananya Iyer (Neurology).

[Step 4] Testing Query 3: 'Show appointments for patient P001.'...
  -> PASSED Agent: Patient Agent
  -> Recommendation: Retrieved appointments for patient P001 (Rahul Sharma).

[Step 5] Testing Query 4: 'Find an available doctor.'...
  -> PASSED Agent: Doctor Agent
  -> Recommendation: Retrieved 7 active available doctors across departments.

[Step 6] Testing Query 5: 'Book an appointment.' (Clarification Check)...
  -> PASSED Clarification Prompt: Please specify which department or doctor specialization you require.

==================================================
  ALL PHASE 2 BACKEND VERIFICATION STEPS PASSED!  
==================================================
```

---

## B.3 Phase 3 Test Execution Log (`python test_phase3.py`)

```text
==================================================
  RUNNING CARECOORD PHASE 3 BACKEND VERIFICATION  
==================================================

[Step 1] Testing Workflow 1 (Doctor Search): 'Find me an available cardiologist'...
  -> PASSED: Workflow ID wf-910283 | Agent: Doctor Agent
  -> Recommendation: Found available Cardiology specialists: Dr. Rajesh Mehta (Cardiology).

[Step 2] Testing Workflow 2 (Primary Demo): 'I need an appointment with a cardiologist tomorrow.'...
  -> PASSED: Workflow ID wf-482910 | Requires Human Approval: True
  -> Recommendation: Proposed Cardiology appointment on 2026-09-25 at 10:00 AM with Dr. Rajesh Mehta. Pending staff authorization.

[Step 3] Testing GET /api/workflows/wf-482910 and GET /api/workflows/wf-482910/events...
  -> PASSED: Retrieved 5 graph execution events for wf-482910.

[Step 4] Testing Human Approval API: POST /api/workflows/wf-482910/approve...
  -> PASSED: Workflow wf-482910 status updated to COMPLETED after approval.

[Step 5] Testing Workflow 3 (Patient Info): 'Show appointments for patient P001.'...
  -> PASSED: Workflow ID wf-719284 | Agent: Patient Agent

[Step 6] Testing Workflow 4 (Missing Info): 'Book an appointment.'...
  -> PASSED: Status 'NEEDS_CLARIFICATION' | Prompt: Which department or doctor specialization do you require?

[Step 7] Testing Workflow 5 (No Availability Scenario): 'Find an available neurologist'...
  -> PASSED: Handled specialization query cleanly.

[Step 8] Testing GET /api/workflows...
  -> PASSED: Retrieved 5 workflow history records from SQLite.

==================================================
  ALL PHASE 3 BACKEND VERIFICATION STEPS PASSED!  
==================================================
```

---

# Appendix C: Institutional Compliance, Ethics & Safety Annexures

## C.1 Operational Safety Policy & Non-Clinical Scope Declaration

### Institutional Mandate
CareCoord is deployed strictly as an **operational coordination and resource management system**. It does **NOT** perform medical diagnoses, prescribe treatment plans, assess drug interactions, or issue clinical triage orders without human staff validation.

```text
+-------------------------------------------------------------------------+
|                        SAFETY & SCOPE BOUNDARY                          |
|                                                                         |
|  CareCoord AI Agents are RESTRICTED to operational resource management: |
|  - Patient profile lookup                                              |
|  - Doctor availability querying                                         |
|  - Appointment slot proposal                                            |
|  - Bed status inventory tracking                                        |
|                                                                         |
|  AI Agents are STRICTLY PROHIBITED from:                                |
|  - Generating clinical diagnoses                                        |
|  - Altering medical prescriptions                                       |
|  - Auto-committing database mutations without human staff approval      |
+-------------------------------------------------------------------------+
```

---

## C.2 Human-in-the-Loop (HITL) Staff Authorization Protocol

1. **State Interception**: Any workflow intending to mutate database records (e.g., creating an appointment, allocating a bed, updating patient status) is intercepted by `ValidationAgent`.
2. **Flag Setting**: The state transitions to `status = REQUIRES_HUMAN_APPROVAL` and `requires_human_review = True`.
3. **UI Rendering**: The CareCoord Command Center renders an interactive **Human Approval Card** (`HumanApprovalCard.jsx`) detailing:
   - Proposed Action (e.g., Create Appointment for `P001` with `D001` at `10:00 AM`).
   - Agent Confidence & Validation Summary.
   - Authorizing Staff Input Notes.
4. **Execution Commitment**: Database mutations are written to disk **only** upon receiving a validated HTTP `POST /api/workflows/{workflow_id}/approve` request containing `action: "approve"`.

---

## C.3 Data Privacy, Anonymization & HIPAA Alignment Checklist

| Compliance Attribute | Standard Requirement | CareCoord Implementation |
| :--- | :--- | :--- |
| **Data Minimization** | Collect only necessary patient data | Only demographic & operational fields stored |
| **Data Encryption at Rest** | Encrypt database records | SQLite local storage with isolated database permissions |
| **Audit Logging** | Record all administrative & system actions | Granular logging in `workflow_runs` & `workflow_events` |
| **PII Protection** | Mask or restrict phone/address access | Internal business IDs (`P001`, `D001`) used in graph states |
| **Access Control** | Role-based authorization | Staff authorization required for database commit endpoints |

---

## C.4 Institutional Ethics & Project Sign-Off Certificate

```text
===========================================================================
               INSTITUTIONAL PROJECT COMPLETION CERTIFICATE
===========================================================================

Project Title : CareCoord – Agentic Healthcare Workflow System
Domain        : Artificial Intelligence / Multi-Agent Systems / Healthcare Management
Degree        : Bachelor of Technology (B.Tech) in Computer Science & Engineering

This is to certify that the project entitled "CareCoord – Agentic Healthcare
Workflow System" has been successfully designed, implemented, and verified
in accordance with institutional academic standards.

Key Milestones Verified:
  [X] Phase 1: Clean FastAPI Backend, SQLite Database & Pydantic Validation
  [X] Phase 2: Natural Language Processing & CareCoord Dashboard V1
  [X] Phase 3: LangGraph Multi-Agent Architecture & Human-in-the-Loop Oversight
  [X] Operational Safety Boundary & Audit Logging System Verified

Project Supervisor / Guide : ___________________________  Date: ____________
Head of Department (CSE)   : ___________________________  Date: ____________
External Examiner          : ___________________________  Date: ____________

===========================================================================
```
