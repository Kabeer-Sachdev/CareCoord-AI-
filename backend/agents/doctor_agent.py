from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.services import doctor_service
from backend.schemas.workflow import WorkflowParseResult

class DoctorAgent:
    """Agent responsible for checking doctor availability, specializations, and schedules."""

    def __init__(self, name: str = "Doctor Agent"):
        self.name = name

    def process(self, db: Session, parsed_req: WorkflowParseResult) -> Dict[str, Any]:
        steps: List[str] = ["Doctor Agent initialized."]

        spec = parsed_req.specialization or parsed_req.department
        doctor_id = parsed_req.doctor_id

        if doctor_id:
            steps.append(f"Searching for Doctor ID '{doctor_id}'...")
            doc = doctor_service.get_doctor_by_id(db, doctor_id)
            if not doc:
                steps.append(f"Doctor ID '{doctor_id}' not found.")
                return {
                    "agent": self.name,
                    "status": "error",
                    "recommendation": f"Doctor ID '{doctor_id}' was not found.",
                    "data": {"found": False},
                    "steps": steps
                }
            steps.append(f"Found doctor {doc.name} ({doc.specialization}). Availability: {doc.availability}.")
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
            steps.append(f"Filtering doctors by specialization/department: '{spec}'...")
            docs = doctor_service.get_doctors_by_specialization(db, spec)
            steps.append(f"Retrieved {len(docs)} doctor(s) matching '{spec}'.")
            
            avail_docs = [d for d in docs if d.availability]
            steps.append(f"Found {len(avail_docs)} currently available doctor(s) in {spec}.")

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

        steps.append("Querying all available doctors in the hospital...")
        avail_docs = doctor_service.get_available_doctors(db)
        steps.append(f"Retrieved {len(avail_docs)} available doctor(s) across all departments.")

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
