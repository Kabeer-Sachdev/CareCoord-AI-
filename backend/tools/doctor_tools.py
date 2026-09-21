from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.services import doctor_service, appointment_service

def get_available_doctors(db: Session) -> List[Dict[str, Any]]:
    """Tool: Retrieve all doctors currently available on duty."""
    docs = doctor_service.get_available_doctors(db)
    return [
        {
            "doctor_id": d.doctor_id,
            "name": d.name,
            "specialization": d.specialization,
            "department": d.department,
            "availability": d.availability,
            "shift": d.shift,
            "current_patients": d.current_patients
        }
        for d in docs
    ]

def get_doctors_by_specialization(db: Session, specialization: str) -> List[Dict[str, Any]]:
    """Tool: Retrieve doctors filtered by specialization or department."""
    docs = doctor_service.get_doctors_by_specialization(db, specialization)
    return [
        {
            "doctor_id": d.doctor_id,
            "name": d.name,
            "specialization": d.specialization,
            "department": d.department,
            "availability": d.availability,
            "shift": d.shift,
            "current_patients": d.current_patients
        }
        for d in docs
    ]

def get_doctor_schedule(db: Session, doctor_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Retrieve doctor details along with scheduled shift hours."""
    doc = doctor_service.get_doctor_by_id(db, doctor_id)
    if not doc:
        return None
    return {
        "doctor_id": doc.doctor_id,
        "name": doc.name,
        "specialization": doc.specialization,
        "department": doc.department,
        "shift": doc.shift,
        "availability": doc.availability
    }

def get_doctor_workload(db: Session, doctor_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Calculate current workload and active appointment count for doctor."""
    doc = doctor_service.get_doctor_by_id(db, doctor_id)
    if not doc:
        return None
    appts = appointment_service.get_doctor_appointments(db, doctor_id)
    active_appts = [a for a in appts if a.status in ["scheduled", "pending"]]
    return {
        "doctor_id": doc.doctor_id,
        "name": doc.name,
        "current_patients": doc.current_patients,
        "scheduled_appointments_count": len(active_appts)
    }
