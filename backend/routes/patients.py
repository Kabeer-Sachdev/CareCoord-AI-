from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User
from backend.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from backend.services import patient_service
from backend.auth.dependencies import get_optional_current_user
from backend.services.audit_service import log_audit

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=List[PatientResponse], summary="Get all patients")
def read_patients(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieve all patients registered in the system (or only self if logged in as patient)."""
    if current_user and current_user.role == "PATIENT" and current_user.patient_id:
        p = patient_service.get_patient_by_id(db, current_user.patient_id)
        return [p] if p else []
    return patient_service.get_all_patients(db)

@router.get("/{patient_id}", response_model=PatientResponse, summary="Get patient by ID")
def read_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieve details of a specific patient by patient ID."""
    if current_user and current_user.role == "PATIENT":
        if current_user.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Patients may only access their own profile."
            )

    patient = patient_service.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )
    return patient

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED, summary="Create a new patient")
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Register a new patient in the hospital database."""
    try:
        patient = patient_service.create_patient(db, patient_in)
        log_audit(
            db,
            user=current_user,
            action="CREATE_PATIENT",
            entity_type="Patient",
            entity_id=patient.patient_id,
            meta_data={"name": patient.name, "department": patient.department}
        )
        return patient
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.put("/{patient_id}", response_model=PatientResponse, summary="Update patient details")
def update_patient(
    patient_id: str,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Update patient information for an existing patient."""
    if current_user and current_user.role == "PATIENT":
        if current_user.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Patients may only modify their own profile."
            )

    try:
        updated = patient_service.update_patient(db, patient_id, patient_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{patient_id}' not found."
            )
        log_audit(
            db,
            user=current_user,
            action="UPDATE_PATIENT",
            entity_type="Patient",
            entity_id=updated.patient_id
        )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.delete("/{patient_id}", summary="Delete a patient")
def delete_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Delete a patient record from the hospital database."""
    if current_user and current_user.role == "PATIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patients cannot delete patient records."
        )

    success = patient_service.delete_patient(db, patient_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )
    log_audit(
        db,
        user=current_user,
        action="DELETE_PATIENT",
        entity_type="Patient",
        entity_id=patient_id
    )
    return {"message": f"Patient '{patient_id}' successfully deleted."}
