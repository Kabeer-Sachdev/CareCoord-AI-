from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.database.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    phone = Column(String(20), nullable=False)
    department = Column(String(100), nullable=False)
    blood_group = Column(String(10), nullable=False)
    existing_conditions = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    beds = relationship("Bed", back_populates="patient")
    emergencies = relationship("Emergency", back_populates="patient", cascade="all, delete-orphan")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    doctor_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    specialization = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    experience_years = Column(Integer, nullable=False, default=0)
    availability = Column(Boolean, default=True, nullable=False)
    shift = Column(String(50), nullable=False)
    current_patients = Column(Integer, default=0, nullable=False)

    # Relationships
    appointments = relationship("Appointment", back_populates="doctor")
    assigned_emergencies = relationship("Emergency", back_populates="assigned_doctor")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    appointment_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False)
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id"), nullable=False)
    appointment_date = Column(String(20), nullable=False)
    appointment_time = Column(String(20), nullable=False)
    department = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="scheduled")  # scheduled, completed, cancelled, pending
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")


class Bed(Base):
    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bed_id = Column(String(50), unique=True, index=True, nullable=False)
    ward = Column(String(50), nullable=False)
    bed_type = Column(String(50), nullable=False)  # General, ICU, Emergency, Private
    status = Column(String(20), nullable=False, default="available")  # available, occupied, maintenance
    floor = Column(Integer, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="beds")


class Emergency(Base):
    __tablename__ = "emergencies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    emergency_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False)
    priority = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    required_department = Column(String(100), nullable=False)
    required_bed_type = Column(String(50), nullable=False)
    assigned_doctor_id = Column(String(50), ForeignKey("doctors.doctor_id"), nullable=True)
    status = Column(String(20), nullable=False, default="waiting")  # waiting, being_processed, allocated, completed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="emergencies")
    assigned_doctor = relationship("Doctor", back_populates="assigned_emergencies")
