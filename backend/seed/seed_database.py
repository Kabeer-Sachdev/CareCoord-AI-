import sys
from pathlib import Path

# Add project root directory to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.database.database import SessionLocal, init_db
from backend.database.models import Patient, Doctor, Appointment, Bed, Emergency, User
from backend.auth.security import hash_password

def seed_patients(db):
    """Seed 20 realistic synthetic patient records."""
    patients_data = [
        {"patient_id": "P001", "name": "Rahul Sharma", "age": 45, "gender": "Male", "phone": "9876543210", "department": "Cardiology", "blood_group": "B+", "existing_conditions": ["Hypertension", "Diabetes Type 2"]},
        {"patient_id": "P002", "name": "Priya Patel", "age": 32, "gender": "Female", "phone": "9876543211", "department": "Neurology", "blood_group": "O+", "existing_conditions": ["Migraine"]},
        {"patient_id": "P003", "name": "Amitav Ghosh", "age": 58, "gender": "Male", "phone": "9876543212", "department": "Orthopedics", "blood_group": "A+", "existing_conditions": ["Osteoarthritis"]},
        {"patient_id": "P004", "name": "Sunita Verma", "age": 28, "gender": "Female", "phone": "9876543213", "department": "Dermatology", "blood_group": "AB+", "existing_conditions": ["Eczema"]},
        {"patient_id": "P005", "name": "Vikram Singh", "age": 62, "gender": "Male", "phone": "9876543214", "department": "General Medicine", "blood_group": "O-", "existing_conditions": ["Asthma", "Hypertension"]},
        {"patient_id": "P006", "name": "Ananya Roy", "age": 8, "gender": "Female", "phone": "9876543215", "department": "Pediatrics", "blood_group": "A+", "existing_conditions": ["Seasonal Allergy"]},
        {"patient_id": "P007", "name": "Rajesh Kumar", "age": 51, "gender": "Male", "phone": "9876543216", "department": "Emergency Medicine", "blood_group": "B-", "existing_conditions": ["Coronary Artery Disease"]},
        {"patient_id": "P008", "name": "Kavita Reddy", "age": 39, "gender": "Female", "phone": "9876543217", "department": "Cardiology", "blood_group": "O+", "existing_conditions": ["Arrhythmia"]},
        {"patient_id": "P009", "name": "Deepak Joshi", "age": 41, "gender": "Male", "phone": "9876543218", "department": "Neurology", "blood_group": "A-", "existing_conditions": ["Epilepsy"]},
        {"patient_id": "P010", "name": "Sneha Nair", "age": 25, "gender": "Female", "phone": "9876543219", "department": "Orthopedics", "blood_group": "B+", "existing_conditions": ["Ligament Tear"]},
        {"patient_id": "P011", "name": "Manish Gupta", "age": 49, "gender": "Male", "phone": "9876543220", "department": "General Medicine", "blood_group": "AB-", "existing_conditions": ["Hyperthyroidism"]},
        {"patient_id": "P012", "name": "Pooja Hegde", "age": 34, "gender": "Female", "phone": "9876543221", "department": "Dermatology", "blood_group": "O+", "existing_conditions": ["Psoriasis"]},
        {"patient_id": "P013", "name": "Siddharth Malhotra", "age": 12, "gender": "Male", "phone": "9876543222", "department": "Pediatrics", "blood_group": "A+", "existing_conditions": ["Juvenile Asthma"]},
        {"patient_id": "P014", "name": "Meenakshi Iyer", "age": 67, "gender": "Female", "phone": "9876543223", "department": "Emergency Medicine", "blood_group": "B+", "existing_conditions": ["Congestive Heart Failure", "Chronic Kidney Disease"]},
        {"patient_id": "P015", "name": "Rohan Das", "age": 29, "gender": "Male", "phone": "9876543224", "department": "Cardiology", "blood_group": "O-", "existing_conditions": []},
        {"patient_id": "P016", "name": "Shalini Mishra", "age": 44, "gender": "Female", "phone": "9876543225", "department": "Neurology", "blood_group": "AB+", "existing_conditions": ["Chronic Fatigue Syndrome"]},
        {"patient_id": "P017", "name": "Tarun Saxena", "age": 55, "gender": "Male", "phone": "9876543226", "department": "Orthopedics", "blood_group": "A+", "existing_conditions": ["Lumbar Spondylosis"]},
        {"patient_id": "P018", "name": "Divya Choudhary", "age": 31, "gender": "Female", "phone": "9876543227", "department": "General Medicine", "blood_group": "B+", "existing_conditions": ["Anemia"]},
        {"patient_id": "P019", "name": "Harish Bhatia", "age": 70, "gender": "Male", "phone": "9876543228", "department": "Emergency Medicine", "blood_group": "O+", "existing_conditions": ["COPD", "Hypertension"]},
        {"patient_id": "P020", "name": "Neha Kapoor", "age": 6, "gender": "Female", "phone": "9876543229", "department": "Pediatrics", "blood_group": "A-", "existing_conditions": ["Bronchitis"]}
    ]

    count = 0
    for p in patients_data:
        existing = db.query(Patient).filter(Patient.patient_id == p["patient_id"]).first()
        if not existing:
            db.add(Patient(**p))
            count += 1
    db.commit()
    return count


def seed_doctors(db):
    """Seed 10 realistic synthetic doctor records with mixed availability."""
    doctors_data = [
        {"doctor_id": "D001", "name": "Dr. Mehta", "specialization": "Cardiology", "department": "Cardiology", "experience_years": 15, "availability": True, "shift": "09:00-17:00", "current_patients": 4},
        {"doctor_id": "D002", "name": "Dr. Swati Sen", "specialization": "Neurology", "department": "Neurology", "experience_years": 12, "availability": True, "shift": "08:00-16:00", "current_patients": 3},
        {"doctor_id": "D003", "name": "Dr. Rajesh Khanna", "specialization": "Orthopedics", "department": "Orthopedics", "experience_years": 18, "availability": False, "shift": "12:00-20:00", "current_patients": 6},
        {"doctor_id": "D004", "name": "Dr. Alok Nath", "specialization": "Dermatology", "department": "Dermatology", "experience_years": 8, "availability": True, "shift": "09:00-17:00", "current_patients": 2},
        {"doctor_id": "D005", "name": "Dr. Sunita Rao", "specialization": "General Medicine", "department": "General Medicine", "experience_years": 14, "availability": True, "shift": "07:00-15:00", "current_patients": 5},
        {"doctor_id": "D006", "name": "Dr. Vivek Murthy", "specialization": "Pediatrics", "department": "Pediatrics", "experience_years": 10, "availability": True, "shift": "10:00-18:00", "current_patients": 3},
        {"doctor_id": "D007", "name": "Dr. Arjun Kapoor", "specialization": "Emergency Medicine", "department": "Emergency Medicine", "experience_years": 11, "availability": True, "shift": "00:00-08:00", "current_patients": 5},
        {"doctor_id": "D008", "name": "Dr. Neerja Bhanot", "specialization": "Cardiology", "department": "Cardiology", "experience_years": 9, "availability": False, "shift": "14:00-22:00", "current_patients": 4},
        {"doctor_id": "D009", "name": "Dr. Vikram Seth", "specialization": "Neurology", "department": "Neurology", "experience_years": 16, "availability": True, "shift": "09:00-17:00", "current_patients": 1},
        {"doctor_id": "D010", "name": "Dr. Ritu Karidhal", "specialization": "General Medicine", "department": "General Medicine", "experience_years": 7, "availability": False, "shift": "16:00-00:00", "current_patients": 2}
    ]

    count = 0
    for d in doctors_data:
        existing = db.query(Doctor).filter(Doctor.doctor_id == d["doctor_id"]).first()
        if not existing:
            db.add(Doctor(**d))
            count += 1
    db.commit()
    return count


def seed_beds(db):
    """Seed 30 realistic beds across various types and statuses."""
    beds_data = [
        # ICU Beds (Floor 3)
        {"bed_id": "B001", "ward": "ICU Ward 1", "bed_type": "ICU", "status": "occupied", "floor": 3, "patient_id": "P001"},
        {"bed_id": "B002", "ward": "ICU Ward 1", "bed_type": "ICU", "status": "available", "floor": 3, "patient_id": None},
        {"bed_id": "B003", "ward": "ICU Ward 1", "bed_type": "ICU", "status": "available", "floor": 3, "patient_id": None},
        {"bed_id": "B004", "ward": "ICU Ward 2", "bed_type": "ICU", "status": "occupied", "floor": 3, "patient_id": "P007"},
        {"bed_id": "B005", "ward": "ICU Ward 2", "bed_type": "ICU", "status": "maintenance", "floor": 3, "patient_id": None},

        # Emergency Beds (Floor 1)
        {"bed_id": "B006", "ward": "ER Bay A", "bed_type": "Emergency", "status": "occupied", "floor": 1, "patient_id": "P014"},
        {"bed_id": "B007", "ward": "ER Bay A", "bed_type": "Emergency", "status": "available", "floor": 1, "patient_id": None},
        {"bed_id": "B008", "ward": "ER Bay B", "bed_type": "Emergency", "status": "available", "floor": 1, "patient_id": None},
        {"bed_id": "B009", "ward": "ER Bay B", "bed_type": "Emergency", "status": "occupied", "floor": 1, "patient_id": "P019"},
        {"bed_id": "B010", "ward": "ER Bay C", "bed_type": "Emergency", "status": "available", "floor": 1, "patient_id": None},

        # General Beds (Floor 2 & 4)
        {"bed_id": "B011", "ward": "General Male Ward", "bed_type": "General", "status": "occupied", "floor": 2, "patient_id": "P003"},
        {"bed_id": "B012", "ward": "General Male Ward", "bed_type": "General", "status": "available", "floor": 2, "patient_id": None},
        {"bed_id": "B013", "ward": "General Male Ward", "bed_type": "General", "status": "available", "floor": 2, "patient_id": None},
        {"bed_id": "B014", "ward": "General Female Ward", "bed_type": "General", "status": "occupied", "floor": 2, "patient_id": "P002"},
        {"bed_id": "B015", "ward": "General Female Ward", "bed_type": "General", "status": "available", "floor": 2, "patient_id": None},
        {"bed_id": "B016", "ward": "General Female Ward", "bed_type": "General", "status": "maintenance", "floor": 2, "patient_id": None},
        {"bed_id": "B017", "ward": "Pediatric Ward", "bed_type": "General", "status": "occupied", "floor": 4, "patient_id": "P006"},
        {"bed_id": "B018", "ward": "Pediatric Ward", "bed_type": "General", "status": "available", "floor": 4, "patient_id": None},
        {"bed_id": "B019", "ward": "Pediatric Ward", "bed_type": "General", "status": "available", "floor": 4, "patient_id": None},
        {"bed_id": "B020", "ward": "General Stepdown", "bed_type": "General", "status": "available", "floor": 4, "patient_id": None},

        # Private Beds (Floor 5)
        {"bed_id": "B021", "ward": "Deluxe Suite Wing", "bed_type": "Private", "status": "occupied", "floor": 5, "patient_id": "P005"},
        {"bed_id": "B022", "ward": "Deluxe Suite Wing", "bed_type": "Private", "status": "available", "floor": 5, "patient_id": None},
        {"bed_id": "B023", "ward": "Super Deluxe Wing", "bed_type": "Private", "status": "available", "floor": 5, "patient_id": None},
        {"bed_id": "B024", "ward": "Super Deluxe Wing", "bed_type": "Private", "status": "maintenance", "floor": 5, "patient_id": None},
        {"bed_id": "B025", "ward": "Private Wing A", "bed_type": "Private", "status": "available", "floor": 5, "patient_id": None},
        {"bed_id": "B026", "ward": "Private Wing A", "bed_type": "Private", "status": "occupied", "floor": 5, "patient_id": "P008"},
        {"bed_id": "B027", "ward": "Private Wing B", "bed_type": "Private", "status": "available", "floor": 5, "patient_id": None},
        {"bed_id": "B028", "ward": "Private Wing B", "bed_type": "Private", "status": "available", "floor": 5, "patient_id": None},
        {"bed_id": "B029", "ward": "Isolation Suite", "bed_type": "Private", "status": "available", "floor": 5, "patient_id": None},
        {"bed_id": "B030", "ward": "Isolation Suite", "bed_type": "Private", "status": "available", "floor": 5, "patient_id": None}
    ]

    count = 0
    for b in beds_data:
        existing = db.query(Bed).filter(Bed.bed_id == b["bed_id"]).first()
        if not existing:
            db.add(Bed(**b))
            count += 1
    db.commit()
    return count


def seed_appointments(db):
    """Seed 30 realistic appointments across statuses."""
    appts_data = [
        {"appointment_id": "A001", "patient_id": "P001", "doctor_id": "D001", "appointment_date": "2026-10-01", "appointment_time": "10:00", "department": "Cardiology", "status": "completed", "reason": "Follow-up post ECG"},
        {"appointment_id": "A002", "patient_id": "P002", "doctor_id": "D002", "appointment_date": "2026-10-02", "appointment_time": "11:30", "department": "Neurology", "status": "completed", "reason": "Severe headache evaluation"},
        {"appointment_id": "A003", "patient_id": "P003", "doctor_id": "D003", "appointment_date": "2026-10-03", "appointment_time": "14:00", "department": "Orthopedics", "status": "scheduled", "reason": "Knee pain consultation"},
        {"appointment_id": "A004", "patient_id": "P004", "doctor_id": "D004", "appointment_date": "2026-10-04", "appointment_time": "09:30", "department": "Dermatology", "status": "scheduled", "reason": "Skin rash examination"},
        {"appointment_id": "A005", "patient_id": "P005", "doctor_id": "D005", "appointment_date": "2026-10-05", "appointment_time": "10:15", "department": "General Medicine", "status": "scheduled", "reason": "Routine annual health checkup"},
        {"appointment_id": "A006", "patient_id": "P006", "doctor_id": "D006", "appointment_date": "2026-10-06", "appointment_time": "11:00", "department": "Pediatrics", "status": "completed", "reason": "Vaccination and growth checkup"},
        {"appointment_id": "A007", "patient_id": "P007", "doctor_id": "D007", "appointment_date": "2026-10-07", "appointment_time": "02:00", "department": "Emergency Medicine", "status": "completed", "reason": "Acute chest pain triage"},
        {"appointment_id": "A008", "patient_id": "P008", "doctor_id": "D008", "appointment_date": "2026-10-08", "appointment_time": "15:00", "department": "Cardiology", "status": "cancelled", "reason": "Patient requested rescheduling"},
        {"appointment_id": "A009", "patient_id": "P009", "doctor_id": "D009", "appointment_date": "2026-10-09", "appointment_time": "12:00", "department": "Neurology", "status": "pending", "reason": "MRI scan results review"},
        {"appointment_id": "A010", "patient_id": "P010", "doctor_id": "D003", "appointment_date": "2026-10-10", "appointment_time": "13:30", "department": "Orthopedics", "status": "scheduled", "reason": "Ankle sprain follow-up"},
        {"appointment_id": "A011", "patient_id": "P011", "doctor_id": "D005", "appointment_date": "2026-10-11", "appointment_time": "08:30", "department": "General Medicine", "status": "pending", "reason": "Thyroid profile review"},
        {"appointment_id": "A012", "patient_id": "P012", "doctor_id": "D004", "appointment_date": "2026-10-12", "appointment_time": "10:45", "department": "Dermatology", "status": "completed", "reason": "Allergy patch testing"},
        {"appointment_id": "A013", "patient_id": "P013", "doctor_id": "D006", "appointment_date": "2026-10-13", "appointment_time": "14:30", "department": "Pediatrics", "status": "scheduled", "reason": "Asthma inhaler technique check"},
        {"appointment_id": "A014", "patient_id": "P014", "doctor_id": "D007", "appointment_date": "2026-10-14", "appointment_time": "04:15", "department": "Emergency Medicine", "status": "completed", "reason": "Shortness of breath admission"},
        {"appointment_id": "A015", "patient_id": "P015", "doctor_id": "D001", "appointment_date": "2026-10-15", "appointment_time": "11:15", "department": "Cardiology", "status": "scheduled", "reason": "Pre-operative cardiac clearance"},
        {"appointment_id": "A016", "patient_id": "P016", "doctor_id": "D002", "appointment_date": "2026-10-16", "appointment_time": "09:00", "department": "Neurology", "status": "pending", "reason": "Nerve conduction velocity study"},
        {"appointment_id": "A017", "patient_id": "P017", "doctor_id": "D003", "appointment_date": "2026-10-17", "appointment_time": "16:00", "department": "Orthopedics", "status": "cancelled", "reason": "Doctor unavailable due to surgery"},
        {"appointment_id": "A018", "patient_id": "P018", "doctor_id": "D010", "appointment_date": "2026-10-18", "appointment_time": "17:30", "department": "General Medicine", "status": "scheduled", "reason": "Blood pressure monitoring"},
        {"appointment_id": "A019", "patient_id": "P019", "doctor_id": "D007", "appointment_date": "2026-10-19", "appointment_time": "01:45", "department": "Emergency Medicine", "status": "completed", "reason": "COPD exacerbation"},
        {"appointment_id": "A020", "patient_id": "P020", "doctor_id": "D006", "appointment_date": "2026-10-20", "appointment_time": "12:15", "department": "Pediatrics", "status": "scheduled", "reason": "Fever consultation"},
        {"appointment_id": "A021", "patient_id": "P001", "doctor_id": "D008", "appointment_date": "2026-10-21", "appointment_time": "15:30", "department": "Cardiology", "status": "scheduled", "reason": "Holter monitor installation"},
        {"appointment_id": "A022", "patient_id": "P002", "doctor_id": "D009", "appointment_date": "2026-10-22", "appointment_time": "10:00", "department": "Neurology", "status": "completed", "reason": "EEG review"},
        {"appointment_id": "A023", "patient_id": "P005", "doctor_id": "D010", "appointment_date": "2026-10-23", "appointment_time": "18:00", "department": "General Medicine", "status": "scheduled", "reason": "Diabetic prescription adjustment"},
        {"appointment_id": "A024", "patient_id": "P008", "doctor_id": "D001", "appointment_date": "2026-10-24", "appointment_time": "11:45", "department": "Cardiology", "status": "pending", "reason": "Echocardiogram examination"},
        {"appointment_id": "A025", "patient_id": "P010", "doctor_id": "D003", "appointment_date": "2026-10-25", "appointment_time": "14:15", "department": "Orthopedics", "status": "scheduled", "reason": "Physiotherapy progress check"},
        {"appointment_id": "A026", "patient_id": "P012", "doctor_id": "D004", "appointment_date": "2026-10-26", "appointment_time": "16:15", "department": "Dermatology", "status": "scheduled", "reason": "Mole bioscopy follow-up"},
        {"appointment_id": "A027", "patient_id": "P015", "doctor_id": "D008", "appointment_date": "2026-10-27", "appointment_time": "17:00", "department": "Cardiology", "status": "cancelled", "reason": "Duplicate booking"},
        {"appointment_id": "A028", "patient_id": "P016", "doctor_id": "D009", "appointment_date": "2026-10-28", "appointment_time": "13:00", "department": "Neurology", "status": "scheduled", "reason": "Sleep apnea consultation"},
        {"appointment_id": "A029", "patient_id": "P018", "doctor_id": "D005", "appointment_date": "2026-10-29", "appointment_time": "09:15", "department": "General Medicine", "status": "completed", "reason": "HbA1c test discussion"},
        {"appointment_id": "A030", "patient_id": "P020", "doctor_id": "D006", "appointment_date": "2026-10-30", "appointment_time": "10:30", "department": "Pediatrics", "status": "scheduled", "reason": "Weight and nutrition audit"}
    ]

    count = 0
    for a in appts_data:
        existing = db.query(Appointment).filter(Appointment.appointment_id == a["appointment_id"]).first()
        if not existing:
            db.add(Appointment(**a))
            count += 1
    db.commit()
    return count


def seed_emergencies(db):
    """Seed 10 emergency records with different priorities and statuses."""
    emergencies_data = [
        {"emergency_id": "E001", "patient_id": "P007", "priority": "CRITICAL", "required_department": "Emergency Medicine", "required_bed_type": "ICU", "assigned_doctor_id": "D007", "status": "allocated"},
        {"emergency_id": "E002", "patient_id": "P014", "priority": "HIGH", "required_department": "Cardiology", "required_bed_type": "Emergency", "assigned_doctor_id": "D001", "status": "being_processed"},
        {"emergency_id": "E003", "patient_id": "P019", "priority": "CRITICAL", "required_department": "General Medicine", "required_bed_type": "Emergency", "assigned_doctor_id": "D005", "status": "allocated"},
        {"emergency_id": "E004", "patient_id": "P001", "priority": "HIGH", "required_department": "Cardiology", "required_bed_type": "ICU", "assigned_doctor_id": "D008", "status": "waiting"},
        {"emergency_id": "E005", "patient_id": "P003", "priority": "MEDIUM", "required_department": "Orthopedics", "required_bed_type": "General", "assigned_doctor_id": "D003", "status": "completed"},
        {"emergency_id": "E006", "patient_id": "P009", "priority": "HIGH", "required_department": "Neurology", "required_bed_type": "ICU", "assigned_doctor_id": "D002", "status": "waiting"},
        {"emergency_id": "E007", "patient_id": "P002", "priority": "LOW", "required_department": "Neurology", "required_bed_type": "General", "assigned_doctor_id": "D009", "status": "completed"},
        {"emergency_id": "E008", "patient_id": "P011", "priority": "MEDIUM", "required_department": "General Medicine", "required_bed_type": "General", "assigned_doctor_id": "D010", "status": "being_processed"},
        {"emergency_id": "E009", "patient_id": "P017", "priority": "HIGH", "required_department": "Orthopedics", "required_bed_type": "Emergency", "assigned_doctor_id": "D003", "status": "waiting"},
        {"emergency_id": "E010", "patient_id": "P006", "priority": "CRITICAL", "required_department": "Pediatrics", "required_bed_type": "ICU", "assigned_doctor_id": "D006", "status": "allocated"}
    ]

    count = 0
    for e in emergencies_data:
        existing = db.query(Emergency).filter(Emergency.emergency_id == e["emergency_id"]).first()
        if not existing:
            db.add(Emergency(**e))
            count += 1
    db.commit()
    return count


def seed_users(db):
    """Seed synthetic role-based user accounts for Phase 4 demonstration."""
    demo_pw_hash = hash_password("Demo@1234")
    users_data = [
        {
            "username": "admin",
            "email": "admin@carecoord.demo",
            "password_hash": demo_pw_hash,
            "role": "ADMIN",
            "full_name": "Hospital Administrator",
            "is_active": True,
            "patient_id": None,
            "doctor_id": None
        },
        {
            "username": "reception",
            "email": "reception@carecoord.demo",
            "password_hash": demo_pw_hash,
            "role": "RECEPTIONIST",
            "full_name": "Head Receptionist",
            "is_active": True,
            "patient_id": None,
            "doctor_id": None
        },
        {
            "username": "doctor",
            "email": "doctor@carecoord.demo",
            "password_hash": demo_pw_hash,
            "role": "DOCTOR",
            "full_name": "Dr. Mehta",
            "is_active": True,
            "patient_id": None,
            "doctor_id": "D001"
        },
        {
            "username": "nurse",
            "email": "nurse@carecoord.demo",
            "password_hash": demo_pw_hash,
            "role": "NURSE",
            "full_name": "Nurse Priya Nair",
            "is_active": True,
            "patient_id": None,
            "doctor_id": None
        },
        {
            "username": "patient",
            "email": "patient@carecoord.demo",
            "password_hash": demo_pw_hash,
            "role": "PATIENT",
            "full_name": "Rahul Sharma",
            "is_active": True,
            "patient_id": "P001",
            "doctor_id": None
        }
    ]

    count = 0
    for u in users_data:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if not existing:
            db.add(User(**u))
            count += 1
    db.commit()
    return count


def run_seed():
    """Run all seeding steps safely without duplicate key violations."""
    print("Initializing database tables...")
    init_db()

    db = SessionLocal()
    try:
        print("Seeding synthetic data...")
        p_added = seed_patients(db)
        d_added = seed_doctors(db)
        b_added = seed_beds(db)
        a_added = seed_appointments(db)
        e_added = seed_emergencies(db)
        u_added = seed_users(db)

        print(f"Seeding completed successfully!")
        print(f"  Patients added:     {p_added} (Total in DB: {db.query(Patient).count()})")
        print(f"  Doctors added:      {d_added} (Total in DB: {db.query(Doctor).count()})")
        print(f"  Beds added:         {b_added} (Total in DB: {db.query(Bed).count()})")
        print(f"  Appointments added: {a_added} (Total in DB: {db.query(Appointment).count()})")
        print(f"  Emergencies added:  {e_added} (Total in DB: {db.query(Emergency).count()})")
        print(f"  Users added:        {u_added} (Total in DB: {db.query(User).count()})")
    except Exception as exc:
        db.rollback()
        print(f"Error during seeding: {exc}")
        raise exc
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
