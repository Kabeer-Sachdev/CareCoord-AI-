from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import Appointment, Patient, Doctor
from backend.schemas.appointment import AppointmentCreate, AppointmentUpdate

def generate_appointment_id(db: Session) -> str:
    """Generate next appointment_id like A001, A002..."""
    count = db.query(Appointment).count()
    return f"A{count + 1:03d}"

def get_appointments(db: Session) -> List[Appointment]:
    """Retrieve all appointments."""
    return db.query(Appointment).order_by(Appointment.id.asc()).all()

def get_appointment_by_id(db: Session, appointment_id: str) -> Optional[Appointment]:
    """Retrieve appointment by appointment_id."""
    return db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()

def get_doctor_appointments(db: Session, doctor_id: str) -> List[Appointment]:
    """Retrieve appointments for a specific doctor."""
    return db.query(Appointment).filter(Appointment.doctor_id == doctor_id).order_by(Appointment.id.asc()).all()

def get_patient_appointments(db: Session, patient_id: str) -> List[Appointment]:
    """Retrieve appointments for a specific patient."""
    return db.query(Appointment).filter(Appointment.patient_id == patient_id).order_by(Appointment.id.asc()).all()

def create_appointment(db: Session, appointment_data: AppointmentCreate) -> Appointment:
    """Create appointment after validating referenced patient and doctor exist."""
    patient = db.query(Patient).filter(Patient.patient_id == appointment_data.patient_id).first()
    if not patient:
        raise ValueError(f"Patient with ID '{appointment_data.patient_id}' does not exist.")

    doctor = db.query(Doctor).filter(Doctor.doctor_id == appointment_data.doctor_id).first()
    if not doctor:
        raise ValueError(f"Doctor with ID '{appointment_data.doctor_id}' does not exist.")

    aid = appointment_data.appointment_id or generate_appointment_id(db)
    existing = db.query(Appointment).filter(Appointment.appointment_id == aid).first()
    if existing:
        raise ValueError(f"Appointment with ID '{aid}' already exists.")

    appt_dict = appointment_data.model_dump()
    appt_dict["appointment_id"] = aid

    db_appt = Appointment(**appt_dict)
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    return db_appt

def update_appointment(db: Session, appointment_id: str, appointment_data: AppointmentUpdate) -> Optional[Appointment]:
    """Update an appointment."""
    db_appt = get_appointment_by_id(db, appointment_id)
    if not db_appt:
        return None

    update_data = appointment_data.model_dump(exclude_unset=True)

    if "patient_id" in update_data and update_data["patient_id"]:
        patient = db.query(Patient).filter(Patient.patient_id == update_data["patient_id"]).first()
        if not patient:
            raise ValueError(f"Patient with ID '{update_data['patient_id']}' does not exist.")

    if "doctor_id" in update_data and update_data["doctor_id"]:
        doctor = db.query(Doctor).filter(Doctor.doctor_id == update_data["doctor_id"]).first()
        if not doctor:
            raise ValueError(f"Doctor with ID '{update_data['doctor_id']}' does not exist.")

    for field, value in update_data.items():
        setattr(db_appt, field, value)

    db.commit()
    db.refresh(db_appt)
    return db_appt

def cancel_appointment(db: Session, appointment_id: str) -> Optional[Appointment]:
    """Convenience function to set status of appointment to cancelled."""
    db_appt = get_appointment_by_id(db, appointment_id)
    if not db_appt:
        return None

    db_appt.status = "cancelled"
    db.commit()
    db.refresh(db_appt)
    return db_appt

def delete_appointment(db: Session, appointment_id: str) -> bool:
    """Delete an appointment record."""
    db_appt = get_appointment_by_id(db, appointment_id)
    if not db_appt:
        return False

    db.delete(db_appt)
    db.commit()
    return True
