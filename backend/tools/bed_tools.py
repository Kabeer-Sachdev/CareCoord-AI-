from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.services import bed_service

def get_available_beds(db: Session) -> List[Dict[str, Any]]:
    """Phase 4 Tool Stub: Retrieve all available hospital beds."""
    beds = bed_service.get_available_beds(db)
    return [
        {
            "bed_id": b.bed_id,
            "ward": b.ward,
            "bed_type": b.bed_type,
            "status": b.status,
            "floor": b.floor
        }
        for b in beds
    ]

def get_beds_by_type(db: Session, bed_type: str) -> List[Dict[str, Any]]:
    """Phase 4 Tool Stub: Retrieve beds filtered by type (e.g. ICU, General, Emergency)."""
    beds = bed_service.get_beds_by_type(db, bed_type)
    return [
        {
            "bed_id": b.bed_id,
            "ward": b.ward,
            "bed_type": b.bed_type,
            "status": b.status,
            "floor": b.floor
        }
        for b in beds
    ]
