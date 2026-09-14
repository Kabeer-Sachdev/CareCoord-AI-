from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from backend.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("", response_model=List[AppointmentResponse], summary="Get all appointments")
def read_appointments(db: Session = Depends(get_db)):
    """Retrieve all appointment records."""
    return appointment_service.get_appointments(db)

@router.get("/doctor/{doctor_id}", response_model=List[AppointmentResponse], summary="Get appointments for a doctor")
def read_doctor_appointments(doctor_id: str, db: Session = Depends(get_db)):
    """Filter appointments assigned to a specific doctor."""
    return appointment_service.get_doctor_appointments(db, doctor_id)

@router.get("/patient/{patient_id}", response_model=List[AppointmentResponse], summary="Get appointments for a patient")
def read_patient_appointments(patient_id: str, db: Session = Depends(get_db)):
    """Filter appointments associated with a specific patient."""
    return appointment_service.get_patient_appointments(db, patient_id)

@router.get("/{appointment_id}", response_model=AppointmentResponse, summary="Get appointment by ID")
def read_appointment(appointment_id: str, db: Session = Depends(get_db)):
    """Retrieve a specific appointment record by appointment ID."""
    appt = appointment_service.get_appointment_by_id(db, appointment_id)
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID '{appointment_id}' not found."
        )
    return appt

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED, summary="Create an appointment")
def create_appointment(appointment_in: AppointmentCreate, db: Session = Depends(get_db)):
    """Schedule a new appointment after validating patient and doctor references."""
    try:
        return appointment_service.create_appointment(db, appointment_in)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.put("/{appointment_id}", response_model=AppointmentResponse, summary="Update an appointment")
def update_appointment(appointment_id: str, appointment_in: AppointmentUpdate, db: Session = Depends(get_db)):
    """Update appointment details or status (scheduled, completed, cancelled, pending)."""
    try:
        updated = appointment_service.update_appointment(db, appointment_id, appointment_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID '{appointment_id}' not found."
            )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.delete("/{appointment_id}", summary="Delete an appointment")
def delete_appointment(appointment_id: str, db: Session = Depends(get_db)):
    """Delete an appointment record."""
    success = appointment_service.delete_appointment(db, appointment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID '{appointment_id}' not found."
        )
    return {"message": f"Appointment '{appointment_id}' successfully deleted."}
