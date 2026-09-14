from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import Doctor
from backend.schemas.doctor import DoctorCreate, DoctorUpdate

def generate_doctor_id(db: Session) -> str:
    """Generate next doctor_id like D001, D002..."""
    count = db.query(Doctor).count()
    return f"D{count + 1:03d}"

def get_all_doctors(db: Session) -> List[Doctor]:
    """Retrieve all doctors."""
    return db.query(Doctor).order_by(Doctor.id.asc()).all()

def get_doctor_by_id(db: Session, doctor_id: str) -> Optional[Doctor]:
    """Retrieve doctor by doctor_id string."""
    return db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()

def get_available_doctors(db: Session) -> List[Doctor]:
    """Retrieve only doctors who are currently marked as available."""
    return db.query(Doctor).filter(Doctor.availability == True).order_by(Doctor.id.asc()).all()

def get_doctors_by_specialization(db: Session, specialization: str) -> List[Doctor]:
    """Retrieve doctors by specialization (case-insensitive partial/exact match)."""
    return db.query(Doctor).filter(
        Doctor.specialization.ilike(f"%{specialization}%")
    ).order_by(Doctor.id.asc()).all()

def create_doctor(db: Session, doctor_data: DoctorCreate) -> Doctor:
    """Create a new doctor entry."""
    did = doctor_data.doctor_id or generate_doctor_id(db)

    existing = db.query(Doctor).filter(Doctor.doctor_id == did).first()
    if existing:
        raise ValueError(f"Doctor with ID {did} already exists.")

    doctor_dict = doctor_data.model_dump()
    doctor_dict["doctor_id"] = did

    db_doctor = Doctor(**doctor_dict)
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

def update_doctor(db: Session, doctor_id: str, doctor_data: DoctorUpdate) -> Optional[Doctor]:
    """Update doctor information."""
    db_doctor = get_doctor_by_id(db, doctor_id)
    if not db_doctor:
        return None

    update_data = doctor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_doctor, field, value)

    db.commit()
    db.refresh(db_doctor)
    return db_doctor
