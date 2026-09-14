from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import Patient
from backend.schemas.patient import PatientCreate, PatientUpdate

def generate_patient_id(db: Session) -> str:
    """Generate next sequential patient_id like P001, P002..."""
    count = db.query(Patient).count()
    return f"P{count + 1:03d}"

def get_all_patients(db: Session) -> List[Patient]:
    """Retrieve all patients."""
    return db.query(Patient).order_by(Patient.id.asc()).all()

def get_patient_by_id(db: Session, patient_id: str) -> Optional[Patient]:
    """Retrieve patient by string patient_id."""
    return db.query(Patient).filter(Patient.patient_id == patient_id).first()

def create_patient(db: Session, patient_data: PatientCreate) -> Patient:
    """Create a new patient entry."""
    pid = patient_data.patient_id or generate_patient_id(db)
    
    existing = db.query(Patient).filter(Patient.patient_id == pid).first()
    if existing:
        raise ValueError(f"Patient with ID {pid} already exists.")
        
    patient_dict = patient_data.model_dump()
    patient_dict["patient_id"] = pid

    db_patient = Patient(**patient_dict)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def update_patient(db: Session, patient_id: str, patient_data: PatientUpdate) -> Optional[Patient]:
    """Update patient information."""
    db_patient = get_patient_by_id(db, patient_id)
    if not db_patient:
        return None

    update_data = patient_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_patient, field, value)

    db.commit()
    db.refresh(db_patient)
    return db_patient

def delete_patient(db: Session, patient_id: str) -> bool:
    """Delete a patient by ID."""
    db_patient = get_patient_by_id(db, patient_id)
    if not db_patient:
        return False

    db.delete(db_patient)
    db.commit()
    return True
