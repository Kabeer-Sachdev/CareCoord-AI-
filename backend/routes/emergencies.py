from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.emergency import EmergencyCreate, EmergencyUpdate, EmergencyResponse
from backend.services import emergency_service

router = APIRouter(prefix="/emergencies", tags=["Emergencies"])

@router.get("", response_model=List[EmergencyResponse], summary="Get all emergency cases")
def read_emergencies(db: Session = Depends(get_db)):
    """Retrieve all emergency records."""
    return emergency_service.get_all_emergencies(db)

@router.get("/priority/{priority}", response_model=List[EmergencyResponse], summary="Get emergencies by priority")
def read_emergencies_by_priority(priority: str, db: Session = Depends(get_db)):
    """Filter emergency cases by priority level (LOW, MEDIUM, HIGH, CRITICAL)."""
    return emergency_service.get_emergencies_by_priority(db, priority)

@router.get("/{emergency_id}", response_model=EmergencyResponse, summary="Get emergency case by ID")
def read_emergency(emergency_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific emergency record."""
    emg = emergency_service.get_emergency_by_id(db, emergency_id)
    if not emg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency case with ID '{emergency_id}' not found."
        )
    return emg

@router.post("", response_model=EmergencyResponse, status_code=status.HTTP_201_CREATED, summary="Create an emergency case")
def create_emergency(emergency_in: EmergencyCreate, db: Session = Depends(get_db)):
    """Register a new emergency case requiring allocation."""
    try:
        return emergency_service.create_emergency(db, emergency_in)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

@router.put("/{emergency_id}", response_model=EmergencyResponse, summary="Update an emergency case")
def update_emergency(emergency_id: str, emergency_in: EmergencyUpdate, db: Session = Depends(get_db)):
    """Update emergency status, assigned doctor, or required resources."""
    try:
        updated = emergency_service.update_emergency(db, emergency_id, emergency_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Emergency case with ID '{emergency_id}' not found."
            )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
