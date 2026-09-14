from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.services import appointment_service, doctor_service, patient_service
from backend.schemas.workflow import WorkflowParseResult

class AppointmentAgent:
    """Agent responsible for checking appointment slots and scheduling consultations."""

    def __init__(self, name: str = "Appointment Agent"):
        self.name = name

    def process(self, db: Session, parsed_req: WorkflowParseResult) -> Dict[str, Any]:
        steps: List[str] = ["Appointment Agent initialized."]

        # Check if mandatory department or doctor is missing
        if parsed_req.clarification_needed:
            steps.append("Clarification required before proceeding with appointment lookup.")
            return {
                "agent": self.name,
                "status": "clarification_required",
                "recommendation": parsed_req.clarification_prompt or "More information is required: Which department or doctor would you like to book an appointment with?",
                "data": {
                    "missing_fields": parsed_req.missing_info
                },
                "steps": steps
            }

        dept = parsed_req.department or parsed_req.specialization
        doctor_id = parsed_req.doctor_id
        patient_id = parsed_req.patient_id

        steps.append(f"Analyzing appointment request (Department: '{dept}', Doctor: '{doctor_id}', Patient: '{patient_id}')...")

        # Step 1: Find appropriate doctor
        target_doctor = None
        if doctor_id:
            steps.append(f"Searching for Doctor '{doctor_id}'...")
            target_doctor = doctor_service.get_doctor_by_id(db, doctor_id)
        elif dept:
            steps.append(f"Searching for available doctors in '{dept}'...")
            avail_docs = [d for d in doctor_service.get_doctors_by_specialization(db, dept) if d.availability]
            if avail_docs:
                target_doctor = avail_docs[0]
                steps.append(f"Selected available doctor '{target_doctor.name}' ({target_doctor.doctor_id}) in {dept}.")
            else:
                steps.append(f"No available doctors currently found in department '{dept}'.")

        if not target_doctor:
            steps.append("No matching available doctor found for this appointment request.")
            return {
                "agent": self.name,
                "status": "warning",
                "recommendation": f"No available doctor was found in department '{dept or 'requested'}'. Please try another department or schedule for later.",
                "data": {
                    "department": dept,
                    "available_doctors": []
                },
                "steps": steps
            }

        # Step 2: Propose appointment slot based on doctor's shift
        date_str = parsed_req.date or "tomorrow"
        suggested_time = "10:30 AM" if "09:00" in target_doctor.shift else "02:30 PM"
        steps.append(f"Calculated available slot for {target_doctor.name}: Date: '{date_str}', Time: '{suggested_time}'.")

        # Step 3: Check patient if patient_id was specified
        patient_info = None
        if patient_id:
            patient = patient_service.get_patient_by_id(db, patient_id)
            if patient:
                patient_info = {"patient_id": patient.patient_id, "name": patient.name}
                steps.append(f"Validated patient record for {patient.name} ({patient.patient_id}).")
            else:
                steps.append(f"Patient '{patient_id}' not found in database.")

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
