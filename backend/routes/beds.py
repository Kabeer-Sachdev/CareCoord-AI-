from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.bed import BedCreate, BedUpdate, BedResponse
from backend.services import bed_service

router = APIRouter(prefix="/beds", tags=["Beds"])

@router.get("", response_model=List[BedResponse], summary="Get all beds")
def read_beds(db: Session = Depends(get_db)):
    """Retrieve all hospital beds across all wards."""
    return bed_service.get_all_beds(db)

@router.get("/available", response_model=List[BedResponse], summary="Get all available beds")
def read_available_beds(db: Session = Depends(get_db)):
    """Retrieve all currently unallocated / available beds."""
    return bed_service.get_available_beds(db)

@router.get("/type/{bed_type}", response_model=List[BedResponse], summary="Get available beds of a specific type")
def read_available_beds_by_type(bed_type: str, db: Session = Depends(get_db)):
    """Retrieve available beds filtered by category (General, ICU, Emergency, Private)."""
    return bed_service.get_available_beds_by_type(db, bed_type)

@router.put("/{bed_id}", response_model=BedResponse, summary="Update bed status/allocation")
def update_bed(bed_id: str, bed_in: BedUpdate, db: Session = Depends(get_db)):
    """Update bed status (available, occupied, maintenance) or assign a patient."""
    try:
        updated = bed_service.update_bed(db, bed_id, bed_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bed with ID '{bed_id}' not found."
            )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
