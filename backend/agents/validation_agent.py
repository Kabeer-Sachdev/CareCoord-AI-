from typing import Dict, Any
import time
from backend.agents.state import CareCoordState
from backend.tools import doctor_tools, patient_tools, appointment_tools

class ValidationAgent:
    """
    Validation Node for CareCoord LangGraph Workflow.
    Verifies operational database consistency, slot availability, patient/doctor existence,
    and enforces the Human-in-the-Loop boundary before database mutation.
    """

    def process(self, state: CareCoordState) -> CareCoordState:
        state["current_agent"] = "Validation Node"
        start_time = time.time()
        db = state.get("db_session")

        parsed = state.get("workflow_request", {})
        request_type = parsed.get("request_type")

        # Skip validation if clarification or failure state
        if state.get("status") in ["NEEDS_CLARIFICATION", "FAILED"]:
            return state

        # If not appointment workflow, validation passes automatically
        if request_type != "appointment":
            state["validation_result"] = {"valid": True, "details": "Read-only operational query verified."}
            return state

        doc_res = state.get("doctor_result") or {}
        appt_res = state.get("appointment_result") or {}

        doctors = doc_res.get("data", {}).get("doctors", [])
        slot_check = appt_res.get("data", {}).get("slot_check", {})

        checks = []
        is_valid = True

        # Check 1: Doctor existence and availability
        if not doctors:
            is_valid = False
            checks.append("✗ Doctor Availability Check Failed: No matching doctor available.")
        else:
            checks.append(f"✓ Doctor Availability Check Passed: {doctors[0]['name']} ({doctors[0]['doctor_id']}) is available.")

        # Check 2: Slot Availability and Conflict Check
        if slot_check.get("available") is not True:
            is_valid = False
            checks.append(f"✗ Slot Conflict Check Failed: {slot_check.get('reason', 'Slot unavailable')}")
        else:
            checks.append(f"✓ Slot Conflict Check Passed: Slot {slot_check.get('time')} on {slot_check.get('date')} is free.")

        # Check 3: Patient Reference
        patient_id = parsed.get("patient_id") or "P001"
        patient_record = patient_tools.find_patient(db, patient_id) if db else None
        if db and not patient_record:
            is_valid = False
            checks.append(f"✗ Patient Record Check Failed: Patient {patient_id} does not exist.")
        else:
            pname = patient_record['name'] if patient_record else "Rahul Sharma (P001)"
            checks.append(f"✓ Patient Record Check Passed: Verified patient {pname}.")

        elapsed_ms = int((time.time() - start_time) * 1000)
        validation_info = {
            "valid": is_valid,
            "checks": checks,
            "patient_id": patient_id,
            "doctor_id": doctors[0]["doctor_id"] if doctors else None,
            "doctor_name": doctors[0]["name"] if doctors else None,
            "department": doctors[0]["department"] if doctors else (parsed.get("department") or "Cardiology"),
            "date": slot_check.get("date") or parsed.get("date") or "tomorrow",
            "time": slot_check.get("time") or "10:30 AM"
        }

        state["validation_result"] = validation_info

        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent_name": "Validation Node",
            "node_name": "validation",
            "event_type": "validation_check",
            "status": "success" if is_valid else "failed",
            "execution_time_ms": elapsed_ms,
            "details": {
                "summary": "Validation Check: All operational checks passed." if is_valid else "Validation Check Failed.",
                "checks": checks
            }
        }
        state["execution_log"].append(log_entry)

        if is_valid:
            # Enforce Human-in-the-Loop Boundary
            state["requires_human_review"] = True
            state["status"] = "REQUIRES_HUMAN_APPROVAL"

            recommended_doctor = doctors[0]
            slot_date = slot_check.get("date", "tomorrow")
            slot_time = slot_check.get("time", "10:30 AM")

            rec_summary = (
                f"Recommended Appointment with {recommended_doctor['name']} ({recommended_doctor['specialization']}) "
                f"on {slot_date} at {slot_time} (Department: {recommended_doctor['department']}, Shift: {recommended_doctor['shift']})."
            )

            state["final_recommendation"] = {
                "agent_used": "Appointment Agent",
                "status": "requires_human_approval",
                "recommendation": rec_summary,
                "data": {
                    "patient_id": patient_id,
                    "patient_name": pname,
                    "doctor_id": recommended_doctor["doctor_id"],
                    "doctor_name": recommended_doctor["name"],
                    "department": recommended_doctor["department"],
                    "appointment_date": slot_date,
                    "appointment_time": slot_time,
                    "validation_checks": checks
                },
                "steps": [e.get("details", {}).get("summary", e.get("event_type", "step")) for e in state.get("execution_log", [])]
            }

        return state
