"""
Large Healthcare Dataset Loader (CareBridge Benchmark Loader)
Extracts real patient and doctor records from the cached CareBridge Synthetic Healthcare Dataset
(20,000 patients, 2,000 doctors) and loads a high-density operational subset into CareCoord's SQLite database.

Maintains non-destructive seeding: preserves all existing demo records and credentials.
"""

import os
import random
from datetime import date, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal, init_db
from backend.database.models import Patient, Doctor, Appointment, Bed, Emergency

CAREBRIDGE_CACHE_PATH = r"C:\Users\sachd\.cache\kagglehub\datasets\siddharth564\carebridge-synthetic-healthcare-dataset\versions\1"

DEPARTMENTS = [
    "Cardiology",
    "Neurology",
    "Orthopedics",
    "General Medicine",
    "Emergency Medicine",
    "Pediatrics",
    "Dermatology"
]

SPECIALIZATIONS = {
    "Cardiology": ["Cardiologist", "Interventional Cardiology", "Electrophysiologist"],
    "Neurology": ["Neurologist", "Neurosurgeon", "Epileptologist"],
    "Orthopedics": ["Orthopedic Surgeon", "Joint Replacement Specialist", "Sports Medicine"],
    "General Medicine": ["Internist", "Primary Care Physician", "Hospitalist"],
    "Emergency Medicine": ["Emergency Physician", "Trauma Specialist", "Critical Care"],
    "Pediatrics": ["Pediatrician", "Pediatric Intensivist", "Neonatologist"],
    "Dermatology": ["Dermatologist", "Dermatologic Surgeon"]
}

SHIFTS = ["08:00-16:00", "09:00-17:00", "12:00-20:00", "16:00-00:00", "00:00-08:00"]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]


def load_large_carebridge_dataset(
    target_patients: int = 200,
    target_doctors: int = 35,
    db: Session = None
) -> dict:
    """
    Loads CareBridge clinical records into SQLite.
    Returns summary statistics of the loaded dataset.
    """
    close_session = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_session = True

    try:
        patients_csv = os.path.join(CAREBRIDGE_CACHE_PATH, "patients.csv")
        doctors_csv = os.path.join(CAREBRIDGE_CACHE_PATH, "doctors.csv")

        if not os.path.exists(patients_csv) or not os.path.exists(doctors_csv):
            import kagglehub
            path = kagglehub.dataset_download("siddharth564/carebridge-synthetic-healthcare-dataset")
            patients_csv = os.path.join(path, "patients.csv")
            doctors_csv = os.path.join(path, "doctors.csv")

        p_df = pd.read_csv(patients_csv)
        d_df = pd.read_csv(doctors_csv)

        doctors_added = 0
        patients_added = 0
        appointments_added = 0
        beds_added = 0

        # 1. Seed Doctors across all 7 departments
        docs_subset = d_df.head(target_doctors)
        created_doctor_ids = []

        for idx, row in docs_subset.iterrows():
            did = f"DOC-CB-{idx+1:03d}"
            name = str(row.get("doctor_name", f"Dr. Specialist {idx+1}")).strip()
            if not name.startswith("Dr."):
                name = f"Dr. {name}"

            dept = DEPARTMENTS[idx % len(DEPARTMENTS)]
            spec_list = SPECIALIZATIONS.get(dept, ["Specialist"])
            spec = spec_list[idx % len(spec_list)]
            exp = int(row.get("experience_years", (idx % 15) + 3))
            shift = SHIFTS[idx % len(SHIFTS)]
            is_avail = (idx % 5 != 0)  # ~80% available

            existing = db.query(Doctor).filter(Doctor.doctor_id == did).first()
            if not existing:
                doc = Doctor(
                    doctor_id=did,
                    name=name,
                    specialization=spec,
                    department=dept,
                    experience_years=exp,
                    availability=is_avail,
                    availability_status="Available" if is_avail else "Busy",
                    shift=shift,
                    current_patients=random.randint(1, 6)
                )
                db.add(doc)
                doctors_added += 1
            created_doctor_ids.append(did)

        db.commit()

        # 2. Seed Patients
        patients_subset = p_df.head(target_patients)
        created_patient_ids = []

        for idx, row in patients_subset.iterrows():
            pid = f"PAT-CB-{idx+1:04d}"
            raw_name = str(row.get("patient_name", f"Patient {idx+1}")).strip()
            age = int(row.get("age", random.randint(18, 78)))
            gender = str(row.get("gender", "Female" if idx % 2 == 0 else "Male")).strip()
            city = str(row.get("city", "Metro Hospital Area")).strip()
            district = str(row.get("district", "Urban District")).strip()
            dept = DEPARTMENTS[idx % len(DEPARTMENTS)]
            bg = BLOOD_GROUPS[idx % len(BLOOD_GROUPS)]
            phone = f"+91-987{idx:07d}"

            medical_history = [
                f"Admitted via {district} triage",
                f"CareBridge Cohort 2026",
                f"Resides in {city}"
            ]
            if age > 50:
                medical_history.append("Hypertension monitoring")
            if idx % 7 == 0:
                medical_history.append("Type-2 Diabetes Mellitus")

            existing = db.query(Patient).filter(Patient.patient_id == pid).first()
            if not existing:
                pat = Patient(
                    patient_id=pid,
                    name=raw_name,
                    age=age,
                    gender=gender,
                    phone=phone,
                    department=dept,
                    blood_group=bg,
                    existing_conditions=medical_history
                )
                db.add(pat)
                patients_added += 1
            created_patient_ids.append(pid)

        db.commit()

        # 3. Seed Realistic Historical & Upcoming Appointments
        time_slots = ["09:00:00", "09:30:00", "10:00:00", "10:30:00", "11:00:00", "11:30:00", "14:00:00", "14:30:00", "15:00:00", "15:30:00"]
        today = date.today()

        for i in range(min(len(created_patient_ids), 80)):
            appt_id = f"APT-CB-{i+1:04d}"
            pid = created_patient_ids[i]
            did = created_doctor_ids[i % len(created_doctor_ids)]
            doc = db.query(Doctor).filter(Doctor.doctor_id == did).first()
            dept = doc.department if doc else "General Medicine"

            # Offset: past appointments, today, and future
            day_offset = (i % 15) - 5
            appt_date = today + timedelta(days=day_offset)
            appt_time = time_slots[i % len(time_slots)]

            if day_offset < 0:
                status = "Completed"
            elif day_offset == 0:
                status = "Scheduled"
            else:
                status = "Scheduled" if i % 6 != 0 else "Cancelled"

            existing = db.query(Appointment).filter(Appointment.appointment_id == appt_id).first()
            if not existing:
                appt = Appointment(
                    appointment_id=appt_id,
                    patient_id=pid,
                    doctor_id=did,
                    department=dept,
                    appointment_date=appt_date,
                    appointment_time=appt_time,
                    status=status,
                    reason=f"Clinical Consultation - {dept}"
                )
                db.add(appt)
                appointments_added += 1

        db.commit()

        # 4. Seed Ward Beds
        wards = [
            ("Cardiology", "ICU", "3rd Floor", 8),
            ("Emergency", "Emergency", "Ground Floor", 12),
            ("General Medicine", "General", "1st Floor", 16),
            ("Neurology", "Semi-Private", "2nd Floor", 6),
            ("Orthopedics", "Private", "4th Floor", 6),
            ("Pediatrics", "General", "2nd Floor", 6)
        ]

        bed_counter = 100
        for ward_name, bed_type, floor, count in wards:
            for b_idx in range(count):
                bed_id = f"BED-CB-{bed_counter}"
                bed_counter += 1
                status = "Occupied" if (b_idx % 3 == 0) else "Available"
                assigned_patient = created_patient_ids[b_idx % len(created_patient_ids)] if status == "Occupied" else None

                existing = db.query(Bed).filter(Bed.bed_id == bed_id).first()
                if not existing:
                    bed = Bed(
                        bed_id=bed_id,
                        ward=ward_name,
                        bed_type=bed_type,
                        status=status,
                        floor=floor,
                        patient_id=assigned_patient
                    )
                    db.add(bed)
                    beds_added += 1

        db.commit()

        total_patients = db.query(Patient).count()
        total_doctors = db.query(Doctor).count()
        total_appts = db.query(Appointment).count()
        total_beds = db.query(Bed).count()

        summary = {
            "status": "success",
            "source_dataset": "CareBridge Kaggle Dataset (siddharth564/carebridge-synthetic-healthcare-dataset)",
            "doctors_added": doctors_added,
            "total_doctors": total_doctors,
            "patients_added": patients_added,
            "total_patients": total_patients,
            "appointments_added": appointments_added,
            "total_appointments": total_appts,
            "beds_added": beds_added,
            "total_beds": total_beds
        }
        return summary
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    stats = load_large_carebridge_dataset(target_patients=200, target_doctors=35)
    print("\n==================================================")
    print("  CAREBRIDGE LARGE DATASET LOADED SUCCESSFULLY")
    print("==================================================")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("==================================================")
