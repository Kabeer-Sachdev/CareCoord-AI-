from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from backend.services import patient_service

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=List[PatientResponse], summary="Get all patients")
def read_patients(db: Session = Depends(get_db)):
    """Retrieve all patients registered in the system."""
    return patient_service.get_all_patients(db)

@router.get("/{patient_id}", response_model=PatientResponse, summary="Get patient by ID")
def read_patient(patient_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific patient by patient ID."""
    patient = patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )
    return patient

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED, summary="Create a new patient")
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)):
    """Register a new patient in the hospital database."""
    try:
        return patient_service.create_patient(db, patient_in)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.put("/{patient_id}", response_model=PatientResponse, summary="Update patient details")
def update_patient(patient_id: str, patient_in: PatientUpdate, db: Session = Depends(get_db)):
    """Update patient information for an existing patient."""
    try:
        updated = patient_service.update_patient(db, patient_id, patient_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{patient_id}' not found."
            )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.delete("/{patient_id}", summary="Delete a patient")
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    """Delete a patient record from the hospital database."""
    success = patient_service.delete_patient(db, patient_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )
    return {"message": f"Patient '{patient_id}' successfully deleted."}
