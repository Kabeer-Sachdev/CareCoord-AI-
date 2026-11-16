from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User
from backend.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentStatusUpdate,
)
from backend.services import appointment_service
from backend.auth.dependencies import get_optional_current_user
from backend.realtime.connection_manager import connection_manager
from backend.realtime.events import EventType
from backend.services.notification_service import notify_appointment_participants
from backend.services.audit_service import log_audit

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("", response_model=List[AppointmentResponse], summary="Get all appointments")
def read_appointments(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieve all appointment records (patients only see their own)."""
    if current_user and current_user.role == "PATIENT" and current_user.patient_id:
        return appointment_service.get_patient_appointments(db, current_user.patient_id)
    return appointment_service.get_appointments(db)

@router.get("/doctor/{doctor_id}", response_model=List[AppointmentResponse], summary="Get appointments for a doctor")
def read_doctor_appointments(
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Filter appointments assigned to a specific doctor."""
    if current_user and current_user.role == "DOCTOR" and current_user.doctor_id:
        if current_user.doctor_id != doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctors may only view their own appointments."
            )
    return appointment_service.get_doctor_appointments(db, doctor_id)

@router.get("/patient/{patient_id}", response_model=List[AppointmentResponse], summary="Get appointments for a patient")
def read_patient_appointments(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Filter appointments associated with a specific patient."""
    if current_user and current_user.role == "PATIENT":
        if current_user.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Patients may only access their own appointments."
            )
    return appointment_service.get_patient_appointments(db, patient_id)

@router.get("/{appointment_id}", response_model=AppointmentResponse, summary="Get appointment by ID")
def read_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieve a specific appointment record by appointment ID."""
    appt = appointment_service.get_appointment_by_id(db, appointment_id)
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID '{appointment_id}' not found."
        )
    if current_user and current_user.role == "PATIENT" and current_user.patient_id:
        if appt.patient_id != current_user.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to view this appointment."
            )
    return appt

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED, summary="Create an appointment")
def create_appointment(
    appointment_in: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Schedule a new appointment after validating patient and doctor references."""
    if current_user and current_user.role == "PATIENT" and current_user.patient_id:
        if appointment_in.patient_id != current_user.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients can only book appointments for themselves."
            )
    try:
        appt = appointment_service.create_appointment(db, appointment_in)
        
        # Real-time event and notification
        connection_manager.broadcast_sync(
            event_type=EventType.APPOINTMENT_CREATED,
            payload={
                "appointment_id": appt.appointment_id,
                "patient_id": appt.patient_id,
                "doctor_id": appt.doctor_id,
                "appointment_date": appt.appointment_date,
                "appointment_time": appt.appointment_time,
                "department": appt.department,
                "status": appt.status,
            }
        )
        notify_appointment_participants(db, appt, "created", f"Scheduled for {appt.appointment_date} at {appt.appointment_time}")
        log_audit(
            db,
            user=current_user,
            action="CREATE_APPOINTMENT",
            entity_type="Appointment",
            entity_id=appt.appointment_id,
            meta_data={"doctor_id": appt.doctor_id, "patient_id": appt.patient_id}
        )
        return appt
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.put("/{appointment_id}/status", response_model=AppointmentResponse, summary="Update appointment status (accept, reject, confirm, cancel)")
def update_appointment_status(
    appointment_id: str,
    status_in: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Doctor acceptance/rejection, receptionist confirmation, or patient cancellation."""
    appt = appointment_service.get_appointment_by_id(db, appointment_id)
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID '{appointment_id}' not found."
        )

    # Permission check
    if current_user:
        if current_user.role == "DOCTOR" and current_user.doctor_id:
            if appt.doctor_id != current_user.doctor_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor cannot modify another doctor's appointments.")
        elif current_user.role == "PATIENT" and current_user.patient_id:
            if appt.patient_id != current_user.patient_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient cannot modify another patient's appointments.")
            if status_in.status not in ["cancelled"]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients may only cancel their appointments.")

    updated = appointment_service.update_appointment(db, appointment_id, AppointmentUpdate(status=status_in.status))
    
    # Broadcast event
    evt = EventType.APPOINTMENT_CANCELLED if status_in.status in ["cancelled", "rejected"] else EventType.APPOINTMENT_UPDATED
    connection_manager.broadcast_sync(
        event_type=evt,
        payload={
            "appointment_id": updated.appointment_id,
            "patient_id": updated.patient_id,
            "doctor_id": updated.doctor_id,
            "status": updated.status,
            "notes": status_in.notes
        }
    )
    notify_appointment_participants(
        db,
        updated,
        f"status_{updated.status}",
        f"Status changed to {updated.status}. {status_in.notes or ''}".strip()
    )
    log_audit(
        db,
        user=current_user,
        action=f"UPDATE_APPOINTMENT_STATUS_{updated.status.upper()}",
        entity_type="Appointment",
        entity_id=updated.appointment_id,
        meta_data={"new_status": updated.status, "notes": status_in.notes}
    )
    return updated

@router.put("/{appointment_id}", response_model=AppointmentResponse, summary="Update an appointment")
def update_appointment(
    appointment_id: str,
    appointment_in: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Update appointment details or status (scheduled, completed, cancelled, pending)."""
    try:
        updated = appointment_service.update_appointment(db, appointment_id, appointment_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID '{appointment_id}' not found."
            )
        connection_manager.broadcast_sync(
            event_type=EventType.APPOINTMENT_UPDATED,
            payload={
                "appointment_id": updated.appointment_id,
                "patient_id": updated.patient_id,
                "doctor_id": updated.doctor_id,
                "status": updated.status
            }
        )
        log_audit(
            db,
            user=current_user,
            action="UPDATE_APPOINTMENT",
            entity_type="Appointment",
            entity_id=updated.appointment_id,
            meta_data={"status": updated.status}
        )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.delete("/{appointment_id}", summary="Delete an appointment")
def delete_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Delete an appointment record."""
    success = appointment_service.delete_appointment(db, appointment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID '{appointment_id}' not found."
        )
    connection_manager.broadcast_sync(
        event_type=EventType.APPOINTMENT_CANCELLED,
        payload={"appointment_id": appointment_id}
    )
    log_audit(
        db,
        user=current_user,
        action="DELETE_APPOINTMENT",
        entity_type="Appointment",
        entity_id=appointment_id
    )
    return {"message": f"Appointment '{appointment_id}' successfully deleted."}
