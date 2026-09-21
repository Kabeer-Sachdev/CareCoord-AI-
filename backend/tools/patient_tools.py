from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.services import patient_service, appointment_service

def find_patient(db: Session, patient_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Retrieve patient details by patient_id from SQLite database."""
    patient = patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        return None
    return {
        "patient_id": patient.patient_id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "phone": patient.phone,
        "department": patient.department,
        "blood_group": patient.blood_group,
        "existing_conditions": patient.existing_conditions or [],
        "created_at": str(patient.created_at)
    }

def find_patient_by_name(db: Session, name: str) -> List[Dict[str, Any]]:
    """Tool: Retrieve patients matching name pattern."""
    all_patients = patient_service.get_all_patients(db)
    matched = [p for p in all_patients if name.lower() in p.name.lower()]
    return [
        {
            "patient_id": p.patient_id,
            "name": p.name,
            "age": p.age,
            "department": p.department,
            "blood_group": p.blood_group
        }
        for p in matched
    ]

def get_patient_appointments(db: Session, patient_id: str) -> List[Dict[str, Any]]:
    """Tool: Retrieve all past/upcoming appointments for a patient."""
    appts = appointment_service.get_patient_appointments(db, patient_id)
    return [
        {
            "appointment_id": a.appointment_id,
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor.name if a.doctor else "Unknown",
            "appointment_date": a.appointment_date,
            "appointment_time": a.appointment_time,
            "department": a.department,
            "status": a.status,
            "reason": a.reason
        }
        for a in appts
    ]
