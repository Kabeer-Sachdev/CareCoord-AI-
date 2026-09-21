from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.services import appointment_service, doctor_service, patient_service
from backend.schemas.appointment import AppointmentCreate

STANDARD_SLOTS = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00"]

def get_patient_appointments(db: Session, patient_id: str) -> List[Dict[str, Any]]:
    """Tool: Retrieve appointments for a patient."""
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

def get_doctor_appointments(db: Session, doctor_id: str) -> List[Dict[str, Any]]:
    """Tool: Retrieve appointments booked for a specific doctor."""
    appts = appointment_service.get_doctor_appointments(db, doctor_id)
    return [
        {
            "appointment_id": a.appointment_id,
            "patient_id": a.patient_id,
            "patient_name": a.patient.name if a.patient else "Unknown",
            "appointment_date": a.appointment_date,
            "appointment_time": a.appointment_time,
            "department": a.department,
            "status": a.status,
            "reason": a.reason
        }
        for a in appts
    ]

def check_slot_availability(db: Session, doctor_id: str, date: str, time: str) -> Dict[str, Any]:
    """
    Tool: Verify whether a specific doctor is available at requested date/time slot.
    Checks doctor existence, availability on duty, and existing booked appointments.
    """
    doc = doctor_service.get_doctor_by_id(db, doctor_id)
    if not doc:
        return {"available": False, "reason": f"Doctor {doctor_id} not found."}
    if not doc.availability:
        return {"available": False, "reason": f"Doctor {doc.name} is currently not on active shift availability."}

    appts = appointment_service.get_doctor_appointments(db, doctor_id)
    conflicting = [
        a for a in appts
        if a.appointment_date == date and a.appointment_time == time and a.status != "cancelled"
    ]
    if conflicting:
        return {
            "available": False,
            "reason": f"Doctor {doc.name} already has a scheduled appointment at {time} on {date}."
        }

    return {
        "available": True,
        "doctor_id": doc.doctor_id,
        "doctor_name": doc.name,
        "department": doc.department,
        "shift": doc.shift,
        "date": date,
        "time": time
    }

def get_available_slots(db: Session, doctor_id: str, date: str) -> List[str]:
    """Tool: Returns list of unbooked time slots for a doctor on a given date."""
    doc = doctor_service.get_doctor_by_id(db, doctor_id)
    if not doc or not doc.availability:
        return []

    appts = appointment_service.get_doctor_appointments(db, doctor_id)
    booked_times = {
        a.appointment_time for a in appts
        if a.appointment_date == date and a.status != "cancelled"
    }

    return [slot for slot in STANDARD_SLOTS if slot not in booked_times]

def create_appointment_in_db(
    db: Session,
    patient_id: str,
    doctor_id: str,
    appointment_date: str,
    appointment_time: str,
    department: str,
    reason: str = "Scheduled appointment"
) -> Dict[str, Any]:
    """
    Tool: Creates appointment record in database after explicit Human Approval.
    """
    data = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        department=department,
        reason=reason,
        status="scheduled"
    )
    created = appointment_service.create_appointment(db, data)
    return {
        "appointment_id": created.appointment_id,
        "patient_id": created.patient_id,
        "doctor_id": created.doctor_id,
        "appointment_date": created.appointment_date,
        "appointment_time": created.appointment_time,
        "department": created.department,
        "status": created.status
    }
