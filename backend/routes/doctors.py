from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse
from backend.services import doctor_service

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
def create_doctor(doctor_in: DoctorCreate, db: Session = Depends(get_db)):
    """Register a new doctor in the hospital system."""
    try:
        return doctor_service.create_doctor(db, doctor_in)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.put("/{doctor_id}", response_model=DoctorResponse, summary="Update doctor information")
def update_doctor(doctor_id: str, doctor_in: DoctorUpdate, db: Session = Depends(get_db)):
    """Update doctor shift, availability, or patient count."""
    try:
        updated = doctor_service.update_doctor(db, doctor_id, doctor_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID '{doctor_id}' not found."
            )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
