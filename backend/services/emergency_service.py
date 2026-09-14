from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import Emergency, Patient, Doctor
from backend.schemas.emergency import EmergencyCreate, EmergencyUpdate

def generate_emergency_id(db: Session) -> str:
    """Generate next emergency_id like E001, E002..."""
    count = db.query(Emergency).count()
    return f"E{count + 1:03d}"

def get_all_emergencies(db: Session) -> List[Emergency]:
    """Retrieve all emergency cases."""
    return db.query(Emergency).order_by(Emergency.id.asc()).all()

def get_emergency_by_id(db: Session, emergency_id: str) -> Optional[Emergency]:
    """Retrieve an emergency case by emergency_id."""
    return db.query(Emergency).filter(Emergency.emergency_id == emergency_id).first()

def get_emergencies_by_priority(db: Session, priority: str) -> List[Emergency]:
    """Retrieve emergencies by priority (LOW, MEDIUM, HIGH, CRITICAL)."""
    return db.query(Emergency).filter(
        Emergency.priority.ilike(priority)
    ).order_by(Emergency.id.asc()).all()

def create_emergency(db: Session, emergency_data: EmergencyCreate) -> Emergency:
    """Create an emergency record after validating referenced patient and doctor if assigned."""
    patient = db.query(Patient).filter(Patient.patient_id == emergency_data.patient_id).first()
    if not patient:
        raise ValueError(f"Patient with ID '{emergency_data.patient_id}' does not exist.")

    if emergency_data.assigned_doctor_id:
        doctor = db.query(Doctor).filter(Doctor.doctor_id == emergency_data.assigned_doctor_id).first()
        if not doctor:
            raise ValueError(f"Doctor with ID '{emergency_data.assigned_doctor_id}' does not exist.")

    eid = emergency_data.emergency_id or generate_emergency_id(db)
    existing = db.query(Emergency).filter(Emergency.emergency_id == eid).first()
    if existing:
        raise ValueError(f"Emergency record with ID '{eid}' already exists.")

    emg_dict = emergency_data.model_dump()
    emg_dict["emergency_id"] = eid

    db_emg = Emergency(**emg_dict)
    db.add(db_emg)
    db.commit()
    db.refresh(db_emg)
    return db_emg

def update_emergency(db: Session, emergency_id: str, emergency_data: EmergencyUpdate) -> Optional[Emergency]:
    """Update emergency status, priority, or assigned doctor."""
    db_emg = get_emergency_by_id(db, emergency_id)
    if not db_emg:
        return None

    update_data = emergency_data.model_dump(exclude_unset=True)

    if "patient_id" in update_data and update_data["patient_id"]:
        patient = db.query(Patient).filter(Patient.patient_id == update_data["patient_id"]).first()
        if not patient:
            raise ValueError(f"Patient with ID '{update_data['patient_id']}' does not exist.")

    if "assigned_doctor_id" in update_data and update_data["assigned_doctor_id"]:
        doctor = db.query(Doctor).filter(Doctor.doctor_id == update_data["assigned_doctor_id"]).first()
        if not doctor:
            raise ValueError(f"Doctor with ID '{update_data['assigned_doctor_id']}' does not exist.")

    for field, value in update_data.items():
        setattr(db_emg, field, value)

    db.commit()
    db.refresh(db_emg)
    return db_emg
