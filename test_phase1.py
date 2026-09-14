import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from backend.main import app
from backend.seed.seed_database import run_seed

client = TestClient(app)

def test_complete_phase1():
    print("==================================================")
    print("  RUNNING CARECOORD PHASE 1 BACKEND VERIFICATION  ")
    print("==================================================")

    # 1. Run seed script
    print("\n[Step 1] Running database seed script...")
    run_seed()

    # 2. Test basic health endpoint
    print("\n[Step 2] Testing GET /health...")
    res = client.get("/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert res.json()["status"] == "healthy"
    print("  -> PASSED:", res.json())

    # 3. Test database health endpoint
    print("\n[Step 3] Testing GET /health/database...")
    res = client.get("/health/database")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    db_info = res.json()
    assert db_info["status"] == "healthy"
    assert db_info["counts"]["patients"] >= 20
    assert db_info["counts"]["doctors"] >= 10
    assert db_info["counts"]["beds"] >= 30
    assert db_info["counts"]["appointments"] >= 30
    assert db_info["counts"]["emergencies"] >= 10
    print("  -> PASSED:", db_info["counts"])

    # 4. Test GET /api/patients
    print("\n[Step 4] Testing GET /api/patients...")
    res = client.get("/api/patients")
    assert res.status_code == 200
    patients = res.json()
    assert len(patients) >= 20
    print(f"  -> PASSED: Retrieved {len(patients)} patients. Sample:", patients[0]["name"])

    # 5. Test GET /api/patients/{patient_id}
    print("\n[Step 5] Testing GET /api/patients/P001...")
    res = client.get("/api/patients/P001")
    assert res.status_code == 200
    p001 = res.json()
    assert p001["patient_id"] == "P001"
    print("  -> PASSED: Patient P001 name:", p001["name"])

    # 6. Test GET /api/doctors/available
    print("\n[Step 6] Testing GET /api/doctors/available...")
    res = client.get("/api/doctors/available")
    assert res.status_code == 200
    avail_docs = res.json()
    assert len(avail_docs) > 0
    assert all(d["availability"] is True for d in avail_docs)
    print(f"  -> PASSED: Found {len(avail_docs)} available doctors.")

    # 7. Test GET /api/doctors/specialization/Cardiology
    print("\n[Step 7] Testing GET /api/doctors/specialization/Cardiology...")
    res = client.get("/api/doctors/specialization/Cardiology")
    assert res.status_code == 200
    cardio_docs = res.json()
    assert len(cardio_docs) >= 2
    print(f"  -> PASSED: Found {len(cardio_docs)} Cardiology specialists.")

    # 8. Test GET /api/beds/available
    print("\n[Step 8] Testing GET /api/beds/available...")
    res = client.get("/api/beds/available")
    assert res.status_code == 200
    avail_beds = res.json()
    assert len(avail_beds) > 0
    print(f"  -> PASSED: Found {len(avail_beds)} available beds.")

    # 9. Test GET /api/beds/type/ICU
    print("\n[Step 9] Testing GET /api/beds/type/ICU...")
    res = client.get("/api/beds/type/ICU")
    assert res.status_code == 200
    icu_beds = res.json()
    assert len(icu_beds) > 0
    print(f"  -> PASSED: Found {len(icu_beds)} available ICU beds.")

    # 10. Test POST /api/appointments
    print("\n[Step 10] Testing POST /api/appointments...")
    new_appt = {
        "patient_id": "P001",
        "doctor_id": "D001",
        "appointment_date": "2026-11-15",
        "appointment_time": "14:30",
        "department": "Cardiology",
        "status": "scheduled",
        "reason": "Test routine appointment creation"
    }
    res = client.post("/api/appointments", json=new_appt)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    created_appt = res.json()
    assert created_appt["patient_id"] == "P001"
    print("  -> PASSED: Created appointment ID:", created_appt["appointment_id"])

    # 11. Test POST /api/emergencies
    print("\n[Step 11] Testing POST /api/emergencies...")
    new_emg = {
        "patient_id": "P002",
        "priority": "CRITICAL",
        "required_department": "Neurology",
        "required_bed_type": "ICU",
        "assigned_doctor_id": "D002",
        "status": "waiting"
    }
    res = client.post("/api/emergencies", json=new_emg)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    created_emg = res.json()
    assert created_emg["priority"] == "CRITICAL"
    print("  -> PASSED: Created emergency ID:", created_emg["emergency_id"])

    # 12. Test Invalid Input (Validation error 422)
    print("\n[Step 12] Testing Invalid Input (Validation Error 422)...")
    invalid_patient = {
        "name": "X",
        "age": 250,  # Invalid age > 120
        "gender": "UnknownGender",  # Invalid gender
        "phone": "123",
        "department": "Cardiology",
        "blood_group": "XYZ"  # Invalid blood group
    }
    res = client.post("/api/patients", json=invalid_patient)
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"
    print("  -> PASSED: Correctly returned HTTP 422 Unprocessable Entity for invalid patient payload.")

    # 13. Test Nonexistent ID (404 Not Found)
    print("\n[Step 13] Testing Nonexistent ID (404 Not Found)...")
    res = client.get("/api/patients/P99999")
    assert res.status_code == 404, f"Expected 404, got {res.status_code}"
    print("  -> PASSED: Correctly returned HTTP 404 for non-existent patient ID 'P99999'.")

    # 14. Test Swagger OpenAPI Docs
    print("\n[Step 14] Testing Swagger /docs availability...")
    res = client.get("/docs")
    assert res.status_code == 200
    print("  -> PASSED: /docs accessible successfully.")

    print("\n==================================================")
    print("  ALL 14 VERIFICATION STEPS PASSED SUCCESSFULLY!  ")
    print("==================================================")

if __name__ == "__main__":
    test_complete_phase1()
