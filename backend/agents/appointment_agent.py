from typing import Dict, Any, List
import time
from sqlalchemy.orm import Session
from backend.services import appointment_service, doctor_service, patient_service
from backend.schemas.workflow import WorkflowParseResult
from backend.agents.state import CareCoordState
from backend.tools import appointment_tools, doctor_tools

class AppointmentAgent:
    """Agent responsible for checking appointment slots and scheduling consultations."""

    def __init__(self, name: str = "Appointment Agent"):
        self.name = name

    def process_node(self, state: CareCoordState) -> CareCoordState:
        """LangGraph node execution handler."""
        state["current_agent"] = self.name
        start_time = time.time()
        db = state.get("db_session")

        parsed = state.get("workflow_request", {})
        doc_res = state.get("doctor_result") or {}
        doctors = doc_res.get("data", {}).get("doctors", [])

        target_doctor = doctors[0] if doctors else None
        date_str = parsed.get("date") or "tomorrow"

        if target_doctor and db:
            doctor_id = target_doctor["doctor_id"]
            suggested_time = "10:30 AM" if "09:00" in target_doctor.get("shift", "") else "02:30 PM"

            # Check exact slot availability using appointment tools
            slot_check = appointment_tools.check_slot_availability(db, doctor_id, date_str, suggested_time)
            available_slots = appointment_tools.get_available_slots(db, doctor_id, date_str)
        else:
            slot_check = {"available": False, "reason": "No target doctor identified."}
            available_slots = []

        elapsed_ms = int((time.time() - start_time) * 1000)

        result_data = {
            "doctor": target_doctor,
            "slot_check": slot_check,
            "available_slots": available_slots,
            "proposed_slot": {
                "date": date_str,
                "time": slot_check.get("time", "10:30 AM")
            }
        }

        state["appointment_result"] = {
            "agent": self.name,
            "status": "success" if slot_check.get("available") else "slot_conflict",
            "data": result_data
        }

        if "Appointment Agent" not in state.get("executed_agents", []):
            state["executed_agents"].append("Appointment Agent")

        summary = (
            f"Checked appointment slot availability for {target_doctor['name'] if target_doctor else 'Doctor'} on {date_str}: "
            f"{'Available at ' + slot_check.get('time', '') if slot_check.get('available') else 'Conflict detected'}"
        )

        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent_name": self.name,
            "node_name": "appointment_agent",
            "event_type": "tool_call",
            "tool_name": "check_slot_availability / get_available_slots",
            "status": "success" if slot_check.get("available") else "warning",
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
        steps: List[str] = ["Appointment Agent initialized."]

        if parsed_req.clarification_needed:
            return {
                "agent": self.name,
                "status": "clarification_required",
                "recommendation": parsed_req.clarification_prompt or "More information is required: Which department or doctor would you like to book an appointment with?",
                "data": {"missing_fields": parsed_req.missing_info},
                "steps": steps
            }

        dept = parsed_req.department or parsed_req.specialization
        doctor_id = parsed_req.doctor_id
        patient_id = parsed_req.patient_id

        target_doctor = None
        if doctor_id:
            target_doctor = doctor_service.get_doctor_by_id(db, doctor_id)
        elif dept:
            avail_docs = [d for d in doctor_service.get_doctors_by_specialization(db, dept) if d.availability]
            if avail_docs:
                target_doctor = avail_docs[0]

        if not target_doctor:
            return {
                "agent": self.name,
                "status": "warning",
                "recommendation": f"No available doctor was found in department '{dept or 'requested'}'. Please try another department or schedule for later.",
                "data": {"department": dept, "available_doctors": []},
                "steps": steps
            }

        date_str = parsed_req.date or "tomorrow"
        suggested_time = "10:30 AM" if "09:00" in target_doctor.shift else "02:30 PM"

        patient_info = None
        if patient_id:
            patient = patient_service.get_patient_by_id(db, patient_id)
            if patient:
                patient_info = {"patient_id": patient.patient_id, "name": patient.name}

        rec = (
            f"Recommended Appointment with {target_doctor.name} ({target_doctor.specialization}) "
            f"on {date_str} at {suggested_time} (Department: {target_doctor.department}, Doctor Shift: {target_doctor.shift})."
        )

        return {
            "agent": self.name,
            "status": "success",
            "recommendation": rec,
            "data": {
                "doctor": {
                    "doctor_id": target_doctor.doctor_id,
                    "name": target_doctor.name,
                    "specialization": target_doctor.specialization,
                    "department": target_doctor.department,
                    "shift": target_doctor.shift,
                    "availability": target_doctor.availability
                },
                "patient": patient_info,
                "proposed_slot": {
                    "date": date_str,
                    "time": suggested_time
                }
            },
            "steps": steps
        }
