from typing import Dict, Any, List
import time
from sqlalchemy.orm import Session
from backend.services import doctor_service
from backend.schemas.workflow import WorkflowParseResult
from backend.agents.state import CareCoordState
from backend.tools import doctor_tools

class DoctorAgent:
    """Agent responsible for checking doctor availability, specializations, and schedules."""

    def __init__(self, name: str = "Doctor Agent"):
        self.name = name

    def process_node(self, state: CareCoordState) -> CareCoordState:
        """LangGraph node execution handler."""
        state["current_agent"] = self.name
        start_time = time.time()
        db = state.get("db_session")

        parsed = state.get("workflow_request", {})
        spec = parsed.get("specialization") or parsed.get("department")
        doctor_id = parsed.get("doctor_id")

        if doctor_id and db:
            docs = [doc for doc in [doctor_tools.get_doctor_schedule(db, doctor_id)] if doc]
        elif spec and db:
            docs = doctor_tools.get_doctors_by_specialization(db, spec)
        elif db:
            docs = doctor_tools.get_available_doctors(db)
        else:
            docs = []

        avail_docs = [d for d in docs if d.get("availability")]
        elapsed_ms = int((time.time() - start_time) * 1000)

        result_data = {
            "specialization": spec,
            "doctor_id": doctor_id,
            "total_found": len(docs),
            "available_count": len(avail_docs),
            "doctors": avail_docs if avail_docs else docs
        }

        state["doctor_result"] = {
            "agent": self.name,
            "status": "success" if avail_docs else "no_available_doctors",
            "data": result_data
        }

        if "Doctor Agent" not in state.get("executed_agents", []):
            state["executed_agents"].append("Doctor Agent")

        summary = f"Queried doctor tools: {len(avail_docs)} available doctor(s) found." if avail_docs else f"No available doctor found for {spec or 'requested criteria'}."

        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent_name": self.name,
            "node_name": "doctor_agent",
            "event_type": "tool_call",
            "tool_name": "get_doctors_by_specialization / get_available_doctors",
            "status": "success" if avail_docs else "warning",
            "execution_time_ms": elapsed_ms,
            "details": {
                "summary": summary,
                "data": result_data
            }
        }
        state["execution_log"].append(log_entry)
        return state

    def process(self, db: Session, parsed_req: WorkflowParseResult) -> Dict[str, Any]:
        """Legacy direct execution method for backwards compatibility."""
        steps: List[str] = ["Doctor Agent initialized."]
        spec = parsed_req.specialization or parsed_req.department
        doctor_id = parsed_req.doctor_id

        if doctor_id:
            doc = doctor_service.get_doctor_by_id(db, doctor_id)
            if not doc:
                return {
                    "agent": self.name,
                    "status": "error",
                    "recommendation": f"Doctor ID '{doctor_id}' was not found.",
                    "data": {"found": False},
                    "steps": steps
                }
            return {
                "agent": self.name,
                "status": "success",
                "recommendation": f"Doctor {doc.name} ({doc.specialization}) is currently {'Available' if doc.availability else 'Unavailable'} (Shift: {doc.shift}, Current Load: {doc.current_patients} patients).",
                "data": {
                    "doctor": {
                        "doctor_id": doc.doctor_id,
                        "name": doc.name,
                        "specialization": doc.specialization,
                        "department": doc.department,
                        "availability": doc.availability,
                        "shift": doc.shift,
                        "current_patients": doc.current_patients
                    }
                },
                "steps": steps
            }

        if spec:
            docs = doctor_service.get_doctors_by_specialization(db, spec)
            avail_docs = [d for d in docs if d.availability]
            rec = (
                f"Found {len(avail_docs)} available specialist(s) in {spec}: " +
                ", ".join([f"{d.name} ({d.doctor_id})" for d in avail_docs])
                if avail_docs else f"No available specialists currently found in {spec}."
            )
            return {
                "agent": self.name,
                "status": "success" if avail_docs else "warning",
                "recommendation": rec,
                "data": {
                    "specialization": spec,
                    "total_matching": len(docs),
                    "available_count": len(avail_docs),
                    "doctors": [
                        {
                            "doctor_id": d.doctor_id,
                            "name": d.name,
                            "specialization": d.specialization,
                            "availability": d.availability,
                            "shift": d.shift,
                            "current_patients": d.current_patients
                        } for d in docs
                    ]
                },
                "steps": steps
            }

        avail_docs = doctor_service.get_available_doctors(db)
        return {
            "agent": self.name,
            "status": "success",
            "recommendation": f"Currently {len(avail_docs)} doctor(s) are available on duty across all departments.",
            "data": {
                "available_count": len(avail_docs),
                "doctors": [
                    {
                        "doctor_id": d.doctor_id,
                        "name": d.name,
                        "specialization": d.specialization,
                        "department": d.department,
                        "shift": d.shift
                    } for d in avail_docs
                ]
            },
            "steps": steps
        }
