from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User, Doctor
from backend.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse, DoctorStatusUpdate
from backend.services import doctor_service
from backend.auth.dependencies import get_optional_current_user
from backend.realtime.connection_manager import connection_manager
from backend.realtime.events import EventType
from backend.services.audit_service import log_audit

router = APIRouter(prefix="/doctors", tags=["Doctors"])

@router.get("", response_model=List[DoctorResponse], summary="Get all doctors")
def read_doctors(db: Session = Depends(get_db)):
    """Retrieve all doctor records."""
    return doctor_service.get_all_doctors(db)

@router.get("/available", response_model=List[DoctorResponse], summary="Get currently available doctors")
def read_available_doctors(db: Session = Depends(get_db)):
    """Return doctors who are currently marked as available."""
    return doctor_service.get_available_doctors(db)

@router.get("/specialization/{specialization}", response_model=List[DoctorResponse], summary="Get doctors by specialization")
def read_doctors_by_specialization(specialization: str, db: Session = Depends(get_db)):
    """Filter doctors by medical specialization (e.g. Cardiology, Neurology)."""
    return doctor_service.get_doctors_by_specialization(db, specialization)

@router.get("/{doctor_id}", response_model=DoctorResponse, summary="Get doctor by ID")
def read_doctor(doctor_id: str, db: Session = Depends(get_db)):
    """Retrieve doctor details by doctor ID."""
    doctor = doctor_service.get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{doctor_id}' not found."
        )
    return doctor

@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED, summary="Create a new doctor")
def create_doctor(
    doctor_in: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Register a new doctor in the hospital system."""
    try:
        doctor = doctor_service.create_doctor(db, doctor_in)
        log_audit(
            db,
            user=current_user,
            action="CREATE_DOCTOR",
            entity_type="Doctor",
            entity_id=doctor.doctor_id,
            meta_data={"name": doctor.name, "specialization": doctor.specialization}
        )
        return doctor
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.put("/{doctor_id}/status", response_model=DoctorResponse, summary="Update doctor availability status")
def update_doctor_status(
    doctor_id: str,
    status_in: DoctorStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Update doctor availability (Available, Busy, Unavailable, On Leave)."""
    if current_user and current_user.role == "DOCTOR":
        if current_user.doctor_id != doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctors may only update their own status."
            )

    doc = doctor_service.get_doctor_by_id(db, doctor_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{doctor_id}' not found."
        )

    is_avail = (status_in.availability_status.lower() == "available")
    doc.availability_status = status_in.availability_status
    doc.availability = is_avail
    db.commit()
    db.refresh(doc)

    connection_manager.broadcast_sync(
        event_type=EventType.DOCTOR_STATUS_CHANGED,
        payload={
            "doctor_id": doc.doctor_id,
            "name": doc.name,
            "availability_status": doc.availability_status,
            "availability": doc.availability
        }
    )
    log_audit(
        db,
        user=current_user,
        action="UPDATE_DOCTOR_STATUS",
        entity_type="Doctor",
        entity_id=doc.doctor_id,
        meta_data={"status": doc.availability_status}
    )
    return doc

@router.put("/{doctor_id}", response_model=DoctorResponse, summary="Update doctor information")
def update_doctor(
    doctor_id: str,
    doctor_in: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Update doctor shift, availability, or patient count."""
    try:
        updated = doctor_service.update_doctor(db, doctor_id, doctor_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID '{doctor_id}' not found."
            )
        connection_manager.broadcast_sync(
            event_type=EventType.DOCTOR_STATUS_CHANGED,
            payload={
                "doctor_id": updated.doctor_id,
                "name": updated.name,
                "availability": updated.availability
            }
        )
        log_audit(
            db,
            user=current_user,
            action="UPDATE_DOCTOR",
            entity_type="Doctor",
            entity_id=updated.doctor_id
        )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
