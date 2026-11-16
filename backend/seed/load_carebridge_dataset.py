import os
import pandas as pd
from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal, init_db
from backend.database.models import Patient, Doctor, Appointment, Bed, Emergency

DATASET_NAME = "siddharth564/carebridge-synthetic-healthcare-dataset"

def fetch_carebridge_dataset_path() -> str:
    """Download or retrieve path to CareBridge Synthetic Healthcare Dataset via kagglehub."""
    import kagglehub
    print(f"Fetching Kaggle dataset: '{DATASET_NAME}' via kagglehub...")
    path = kagglehub.dataset_download(DATASET_NAME)
    print(f"Dataset cached locally at: {path}")
    return path

def seed_carebridge_doctors(db: Session, docs_df: pd.DataFrame) -> int:
    """Load doctors from CareBridge dataset into SQLite doctors table."""
    count = 0
    dept_map = {
        "FAC0001": "Cardiology",
        "FAC0002": "Neurology",
        "FAC0003": "Orthopedics",
        "FAC0004": "General Medicine",
        "FAC0005": "Pediatrics",
        "FAC0006": "Dermatology",
        "FAC0007": "Emergency Medicine"
    }
    shifts = ["09:00-17:00", "08:00-16:00", "12:00-20:00", "00:00-08:00", "16:00-00:00"]

    for idx, row in docs_df.iterrows():
        did = str(row.get("doctor_id", f"D{idx+1:03d}"))
        name = str(row.get("doctor_name", f"Dr. Specialist {idx+1}"))
        spec = str(row.get("specialization", "General Medicine"))
        exp = int(row.get("experience_years", 5))
        fac = str(row.get("facility_id", "FAC0001"))
        status = str(row.get("availability_status", "Available"))

        dept = dept_map.get(fac, spec if spec and spec != "nan" else "General Medicine")
        shift = shifts[idx % len(shifts)]
        is_avail = (status.lower() in ["available", "on duty", "active"])

        existing = db.query(Doctor).filter(Doctor.doctor_id == did).first()
        if not existing:
            doc = Doctor(
                doctor_id=did,
                name=name,
                specialization=spec if spec and spec != "nan" else dept,
                department=dept,
                experience_years=exp,
                availability=is_avail,
                shift=shift,
                current_patients=(idx % 5) + 1
            )
            db.add(doc)
            count += 1

    db.commit()
    return count

def seed_carebridge_patients(db: Session, patients_df: pd.DataFrame) -> int:
    """Load patients from CareBridge dataset into SQLite patients table."""
    count = 0
    blood_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
    departments = ["Cardiology", "Neurology", "Orthopedics", "General Medicine", "Pediatrics", "Dermatology", "Emergency Medicine"]

    # Limit to top 50 patients for optimal database performance
    sample_patients = patients_df.head(50)

    for idx, row in sample_patients.iterrows():
        pid = str(row.get("patient_id", f"P{idx+1:03d}"))
        name = str(row.get("patient_name", f"Patient {idx+1}"))
        age = int(row.get("age", 35))
        gender = str(row.get("gender", "Male"))
        city = str(row.get("city", "Mumbai"))
        district = str(row.get("district", "Central"))

        dept = departments[idx % len(departments)]
        phone = f"98765{idx:05d}"
        bg = blood_groups[idx % len(blood_groups)]

        existing = db.query(Patient).filter(Patient.patient_id == pid).first()
        if not existing:
            pat = Patient(
                patient_id=pid,
                name=name,
                age=age,
                gender=gender,
                phone=phone,
                department=dept,
                blood_group=bg,
                existing_conditions=[f"Resident of {city}, {district}"]
            )
            db.add(pat)
            count += 1

    db.commit()
    return count

def run_carebridge_dataset_import():
    """Main execution function to download and seed CareBridge synthetic healthcare dataset."""
    init_db()
    path = fetch_carebridge_dataset_path()

    patients_csv = os.path.join(path, "patients.csv")
    doctors_csv = os.path.join(path, "doctors.csv")

    db = SessionLocal()
    try:
        doctors_added = 0
        patients_added = 0

        if os.path.exists(doctors_csv):
            docs_df = pd.read_csv(doctors_csv)
            doctors_added = seed_carebridge_doctors(db, docs_df)

        if os.path.exists(patients_csv):
            patients_df = pd.read_csv(patients_csv)
            patients_added = seed_carebridge_patients(db, patients_df)

        print("\n==================================================")
        print("  CAREBRIDGE KAGGLE DATASET IMPORTED SUCCESSFULLY ")
        print("==================================================")
        print(f"  Doctors imported:  {doctors_added} (Total in DB: {db.query(Doctor).count()})")
        print(f"  Patients imported: {patients_added} (Total in DB: {db.query(Patient).count()})")
        print("==================================================")
    except Exception as exc:
        db.rollback()
        print(f"Error importing CareBridge dataset: {exc}")
        raise exc
    finally:
        db.close()

if __name__ == "__main__":
    run_carebridge_dataset_import()
