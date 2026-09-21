from typing import Dict, Any, List
import time
from sqlalchemy.orm import Session
from backend.services import patient_service, appointment_service
from backend.schemas.workflow import WorkflowParseResult
from backend.agents.state import CareCoordState
from backend.tools import patient_tools

class PatientAgent:
    """Agent responsible for retrieving patient details and medical appointment histories."""

    def __init__(self, name: str = "Patient Agent"):
        self.name = name

    def process_node(self, state: CareCoordState) -> CareCoordState:
        """LangGraph node execution handler."""
        state["current_agent"] = self.name
        start_time = time.time()
        db = state.get("db_session")

        parsed = state.get("workflow_request", {})
        patient_id = parsed.get("patient_id")

        if not patient_id:
            all_pats = patient_tools.find_patient_by_name(db, "") if db else []
            patient_record = None
            appts = []
        else:
            patient_record = patient_tools.find_patient(db, patient_id) if db else None
            appts = patient_tools.get_patient_appointments(db, patient_id) if db else []

        elapsed_ms = int((time.time() - start_time) * 1000)

        result_data = {
            "patient_id": patient_id,
            "patient": patient_record,
            "appointments": appts
        }

        state["patient_result"] = {
            "agent": self.name,
            "status": "success" if patient_record else "warning",
            "data": result_data
        }

        if "Patient Agent" not in state.get("executed_agents", []):
            state["executed_agents"].append("Patient Agent")

        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent_name": self.name,
            "node_name": "patient_agent",
            "event_type": "tool_call",
            "tool_name": "find_patient / get_patient_appointments",
            "status": "success",
            "execution_time_ms": elapsed_ms,
            "details": {
                "summary": f"Retrieved record and {len(appts)} appointment(s) for patient {patient_id or 'all'}.",
                "data": result_data
            }
        }
        state["execution_log"].append(log_entry)
        return state

    def process(self, db: Session, parsed_req: WorkflowParseResult) -> Dict[str, Any]:
        """Legacy direct execution method for backwards compatibility."""
        steps: List[str] = ["Patient Agent initialized."]
        patient_id = parsed_req.patient_id

        if not patient_id:
            patients = patient_service.get_all_patients(db)
            return {
                "agent": self.name,
                "status": "success",
                "recommendation": f"Found {len(patients)} registered patients in the database.",
                "data": {
                    "count": len(patients),
                    "patients": [
                        {
                            "patient_id": p.patient_id,
                            "name": p.name,
                            "age": p.age,
                            "department": p.department,
                            "blood_group": p.blood_group
                        } for p in patients[:5]
                    ]
                },
                "steps": steps
            }

        patient = patient_service.get_patient_by_id(db, patient_id)
        if not patient:
            return {
                "agent": self.name,
                "status": "error",
                "recommendation": f"Patient ID '{patient_id}' was not found in the hospital records.",
                "data": {"patient_id": patient_id, "found": False},
                "steps": steps
            }

        appts = appointment_service.get_patient_appointments(db, patient_id)
        return {
            "agent": self.name,
            "status": "success",
            "recommendation": f"Retrieved record and {len(appts)} appointment(s) for patient {patient.name} ({patient.patient_id}).",
            "data": {
                "patient": {
                    "patient_id": patient.patient_id,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "phone": patient.phone,
                    "department": patient.department,
                    "blood_group": patient.blood_group,
                    "existing_conditions": patient.existing_conditions
                },
                "appointments_count": len(appts),
                "appointments": [
                    {
                        "appointment_id": a.appointment_id,
                        "doctor_id": a.doctor_id,
                        "date": a.appointment_date,
                        "time": a.appointment_time,
                        "status": a.status,
                        "reason": a.reason
                    } for a in appts
                ]
            },
            "steps": steps
        }
