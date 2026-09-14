from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import Bed, Patient
from backend.schemas.bed import BedCreate, BedUpdate

def generate_bed_id(db: Session) -> str:
    """Generate next bed_id like B001, B002..."""
    count = db.query(Bed).count()
    return f"B{count + 1:03d}"

def get_all_beds(db: Session) -> List[Bed]:
    """Retrieve all beds."""
    return db.query(Bed).order_by(Bed.id.asc()).all()

def get_bed_by_id(db: Session, bed_id: str) -> Optional[Bed]:
    """Retrieve bed by bed_id."""
    return db.query(Bed).filter(Bed.bed_id == bed_id).first()

def get_available_beds(db: Session) -> List[Bed]:
    """Retrieve all available beds."""
    return db.query(Bed).filter(Bed.status == "available").order_by(Bed.id.asc()).all()

def get_available_beds_by_type(db: Session, bed_type: str) -> List[Bed]:
    """Retrieve available beds of a specific bed type (General, ICU, Emergency, Private)."""
    return db.query(Bed).filter(
        Bed.status == "available",
        Bed.bed_type.ilike(bed_type)
    ).order_by(Bed.id.asc()).all()

def create_bed(db: Session, bed_data: BedCreate) -> Bed:
    """Create a new bed record."""
    bid = bed_data.bed_id or generate_bed_id(db)

    existing = db.query(Bed).filter(Bed.bed_id == bid).first()
    if existing:
        raise ValueError(f"Bed with ID '{bid}' already exists.")

    if bed_data.patient_id:
        patient = db.query(Patient).filter(Patient.patient_id == bed_data.patient_id).first()
        if not patient:
            raise ValueError(f"Patient with ID '{bed_data.patient_id}' does not exist.")

    bed_dict = bed_data.model_dump()
    bed_dict["bed_id"] = bid

    db_bed = Bed(**bed_dict)
    db.add(db_bed)
    db.commit()
    db.refresh(db_bed)
    return db_bed

def update_bed(db: Session, bed_id: str, bed_data: BedUpdate) -> Optional[Bed]:
    """Update bed status/allocation."""
    db_bed = get_bed_by_id(db, bed_id)
    if not db_bed:
        return None

    update_data = bed_data.model_dump(exclude_unset=True)

    if "patient_id" in update_data and update_data["patient_id"]:
        patient = db.query(Patient).filter(Patient.patient_id == update_data["patient_id"]).first()
        if not patient:
            raise ValueError(f"Patient with ID '{update_data['patient_id']}' does not exist.")

    for field, value in update_data.items():
        setattr(db_bed, field, value)

    db.commit()
    db.refresh(db_bed)
    return db_bed
