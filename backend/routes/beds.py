from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User, Bed, Patient
from backend.schemas.bed import BedCreate, BedUpdate, BedResponse, BedStatusUpdate, BedTransferRequest
from backend.services import bed_service
from backend.auth.dependencies import get_optional_current_user
from backend.realtime.connection_manager import connection_manager
from backend.realtime.events import EventType
from backend.services.audit_service import log_audit

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

@router.get("/{bed_id}", response_model=BedResponse, summary="Get bed by ID")
def read_bed(bed_id: str, db: Session = Depends(get_db)):
    """Retrieve specific bed details."""
    bed = bed_service.get_bed_by_id(db, bed_id)
    if not bed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bed '{bed_id}' not found.")
    return bed

@router.put("/{bed_id}/status", response_model=BedResponse, summary="Update bed status/allocation")
def update_bed_status(
    bed_id: str,
    status_in: BedStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Nurse/Admin update bed status (available, occupied, maintenance, reserved) and patient."""
    bed = bed_service.get_bed_by_id(db, bed_id)
    if not bed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bed '{bed_id}' not found.")

    if status_in.patient_id:
        pat = db.query(Patient).filter(Patient.patient_id == status_in.patient_id).first()
        if not pat:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Patient '{status_in.patient_id}' not found.")

    bed.status = status_in.status
    bed.patient_id = status_in.patient_id if status_in.status in ["occupied", "reserved"] else None
    db.commit()
    db.refresh(bed)

    connection_manager.broadcast_sync(
        event_type=EventType.BED_STATUS_CHANGED,
        payload={
            "bed_id": bed.bed_id,
            "status": bed.status,
            "ward": bed.ward,
            "bed_type": bed.bed_type,
            "patient_id": bed.patient_id
        }
    )
    log_audit(
        db,
        user=current_user,
        action="UPDATE_BED_STATUS",
        entity_type="Bed",
        entity_id=bed.bed_id,
        meta_data={"new_status": bed.status, "patient_id": bed.patient_id}
    )
    return bed

@router.post("/transfer", summary="Transfer patient between beds")
def transfer_patient(
    transfer_in: BedTransferRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Transfer an admitted patient from one bed to another."""
    from_bed = bed_service.get_bed_by_id(db, transfer_in.from_bed_id)
    to_bed = bed_service.get_bed_by_id(db, transfer_in.to_bed_id)

    if not from_bed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source bed '{transfer_in.from_bed_id}' not found.")
    if not to_bed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Destination bed '{transfer_in.to_bed_id}' not found.")

    if to_bed.status == "occupied" and to_bed.patient_id != transfer_in.patient_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Destination bed '{to_bed.bed_id}' is already occupied.")

    # Execute transfer
    from_bed.status = "available"
    from_bed.patient_id = None
    to_bed.status = "occupied"
    to_bed.patient_id = transfer_in.patient_id

    db.commit()
    db.refresh(from_bed)
    db.refresh(to_bed)

    connection_manager.broadcast_sync(
        event_type=EventType.BED_TRANSFERRED,
        payload={
            "patient_id": transfer_in.patient_id,
            "from_bed_id": from_bed.bed_id,
            "to_bed_id": to_bed.bed_id,
            "reason": transfer_in.reason
        }
    )
    log_audit(
        db,
        user=current_user,
        action="TRANSFER_BED",
        entity_type="Bed",
        entity_id=to_bed.bed_id,
        meta_data={
            "patient_id": transfer_in.patient_id,
            "from_bed_id": from_bed.bed_id,
            "to_bed_id": to_bed.bed_id,
            "reason": transfer_in.reason
        }
    )
    return {
        "status": "success",
        "message": f"Patient {transfer_in.patient_id} successfully transferred from {from_bed.bed_id} to {to_bed.bed_id}.",
        "from_bed": {"bed_id": from_bed.bed_id, "status": from_bed.status},
        "to_bed": {"bed_id": to_bed.bed_id, "status": to_bed.status, "patient_id": to_bed.patient_id}
    }

@router.put("/{bed_id}", response_model=BedResponse, summary="Update bed status/allocation")
def update_bed(
    bed_id: str,
    bed_in: BedUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Update bed status (available, occupied, maintenance) or assign a patient."""
    try:
        updated = bed_service.update_bed(db, bed_id, bed_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bed with ID '{bed_id}' not found."
            )
        connection_manager.broadcast_sync(
            event_type=EventType.BED_STATUS_CHANGED,
            payload={
                "bed_id": updated.bed_id,
                "status": updated.status,
                "ward": updated.ward,
                "bed_type": updated.bed_type,
                "patient_id": updated.patient_id
            }
        )
        log_audit(
            db,
            user=current_user,
            action="UPDATE_BED",
            entity_type="Bed",
            entity_id=updated.bed_id
        )
        return updated
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
