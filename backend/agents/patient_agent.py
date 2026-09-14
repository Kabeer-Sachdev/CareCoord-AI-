from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.services import patient_service, appointment_service
from backend.schemas.workflow import WorkflowParseResult

class PatientAgent:
    """Agent responsible for retrieving patient details and medical appointment histories."""

    def __init__(self, name: str = "Patient Agent"):
        self.name = name

    def process(self, db: Session, parsed_req: WorkflowParseResult) -> Dict[str, Any]:
        steps: List[str] = ["Patient Agent initialized."]

        patient_id = parsed_req.patient_id
        if not patient_id:
            steps.append("No patient ID provided in request. Fetching summary list.")
            patients = patient_service.get_all_patients(db)
            steps.append(f"Retrieved {len(patients)} patient records.")
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
                        } for p in patients[:5]  # return top 5 in data preview
                    ]
                },
                "steps": steps
            }

        steps.append(f"Searching for patient with ID '{patient_id}' in SQLite database...")
        patient = patient_service.get_patient_by_id(db, patient_id)

        if not patient:
            steps.append(f"Patient '{patient_id}' not found in database.")
            return {
                "agent": self.name,
                "status": "error",
                "recommendation": f"Patient ID '{patient_id}' was not found in the hospital records.",
                "data": {"patient_id": patient_id, "found": False},
                "steps": steps
            }

        steps.append(f"Patient '{patient.name}' found (Department: {patient.department}).")
        steps.append(f"Fetching appointments for patient '{patient_id}'...")

        appts = appointment_service.get_patient_appointments(db, patient_id)
        steps.append(f"Found {len(appts)} appointment(s) for patient '{patient.name}'.")

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
