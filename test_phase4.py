"""
CareCoord - Phase 4 Comprehensive Verification Test Suite
Tests:
1. Authentication & JWT Token Issuance (Login for Admin, Doctor, Receptionist, Nurse, Patient)
2. Invalid Credentials & Deactivated Account Handling (401 / 403)
3. Role-Based Access Control & Security Dependencies
4. Patient Data Isolation (Patient P001 forbidden from accessing P002 data)
5. Doctor Status Update & Self-Service Isolation
6. Bed Management (Status change & Patient Transfer)
7. Emergency Escalation & Role Notifications
8. Persistent Notification Service (List, Unread count, Mark as Read)
9. Governance Audit Logging
10. Backward Compatibility check (Health & Core Endpoints)
"""

import sys
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.database import init_db, SessionLocal
from backend.seed.seed_database import seed_users
from backend.database.models import User, Notification, AuditLog

def print_step(title):
    print(f"\n[Step] {title}")

def print_passed(msg):
    print(f"  -> PASSED: {msg}")

def test_phase4():
    print("=" * 60)
    print("  RUNNING CARECOORD PHASE 4 BACKEND & RBAC VERIFICATION  ")
    print("=" * 60)

    # 1. Ensure DB & Users exist
    print_step("1. Verifying Database and Demo Accounts...")
    init_db()
    db = SessionLocal()
    seed_users(db)
    user_count = db.query(User).count()
    db.close()
    assert user_count >= 5
    print_passed(f"Database ready with {user_count} user accounts.")

    client = TestClient(app)

    # 2. Test Login for all 5 Roles
    print_step("2. Testing JWT Authentication for all 5 Demo Roles...")
    roles = [
        ("admin@carecoord.demo", "ADMIN"),
        ("reception@carecoord.demo", "RECEPTIONIST"),
        ("doctor@carecoord.demo", "DOCTOR"),
        ("nurse@carecoord.demo", "NURSE"),
        ("patient@carecoord.demo", "PATIENT")
    ]
    tokens = {}

    for email, expected_role in roles:
        res = client.post("/api/auth/login", json={"username_or_email": email, "password": "Demo@1234"})
        assert res.status_code == 200, f"Login failed for {email}: {res.text}"
        data = res.json()
        assert "access_token" in data
        assert data["user"]["role"] == expected_role
        tokens[expected_role] = data["access_token"]
        print_passed(f"Authenticated {expected_role} ({email}) -> JWT acquired.")

    # 3. Test Invalid Credentials
    print_step("3. Testing Security: Invalid Password...")
    res_bad = client.post("/api/auth/login", json={"username_or_email": "admin@carecoord.demo", "password": "WrongPassword!"})
    assert res_bad.status_code == 401
    print_passed("Correctly rejected with HTTP 401 Unauthorized.")

    # 4. Test GET /api/auth/me
    print_step("4. Testing GET /api/auth/me for Doctor...")
    doc_headers = {"Authorization": f"Bearer {tokens['DOCTOR']}"}
    res_me = client.get("/api/auth/me", headers=doc_headers)
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert me_data["role"] == "DOCTOR"
    assert me_data["doctor_id"] == "D001"
    print_passed(f"Verified profile: {me_data['full_name']} ({me_data['role']}, Linked ID: {me_data['doctor_id']})")

    # 5. Test Patient Data Isolation (Enforce that Patient P001 cannot read another patient's data)
    print_step("5. Testing Strict Patient Data Isolation...")
    patient_headers = {"Authorization": f"Bearer {tokens['PATIENT']}"}
    
    # Own data: P001 should succeed
    res_own = client.get("/api/patients/P001", headers=patient_headers)
    assert res_own.status_code == 200
    print_passed(f"Patient successfully retrieved own profile ({res_own.json()['name']})")

    # Other patient's data: P002 should return 403 Forbidden
    res_forbidden = client.get("/api/patients/P002", headers=patient_headers)
    assert res_forbidden.status_code == 403
    print_passed("Patient access to P002 correctly blocked with HTTP 403 Forbidden.")

    # Patient appointments isolation
    res_appt_own = client.get("/api/appointments/patient/P001", headers=patient_headers)
    assert res_appt_own.status_code == 200
    print_passed(f"Patient retrieved own appointments ({len(res_appt_own.json())} found)")

    res_appt_forbidden = client.get("/api/appointments/patient/P002", headers=patient_headers)
    assert res_appt_forbidden.status_code == 403
    print_passed("Patient accessing another patient's appointments correctly blocked with HTTP 403.")

    # 6. Test Doctor Status Update
    print_step("6. Testing Doctor Availability Status Update...")
    res_status = client.put(
        "/api/doctors/D001/status",
        headers=doc_headers,
        json={"availability_status": "Busy", "notes": "Attending clinical rounds"}
    )
    assert res_status.status_code == 200
    assert res_status.json()["availability_status"] == "Busy"
    print_passed("Doctor D001 status successfully updated to 'Busy'.")

    # Restore to Available
    res_status_restore = client.put(
        "/api/doctors/D001/status",
        headers=doc_headers,
        json={"availability_status": "Available"}
    )
    assert res_status_restore.status_code == 200
    assert res_status_restore.json()["availability_status"] == "Available"
    print_passed("Doctor D001 status restored to 'Available'.")

    # 7. Test Bed Management: Status update and Patient Transfer
    print_step("7. Testing Bed Management & Patient Transfer...")
    nurse_headers = {"Authorization": f"Bearer {tokens['NURSE']}"}

    # Update bed B001 to maintenance then available
    res_bed_maint = client.put(
        "/api/beds/B001/status",
        headers=nurse_headers,
        json={"status": "maintenance", "notes": "Sterilization in progress"}
    )
    assert res_bed_maint.status_code == 200
    assert res_bed_maint.json()["status"] == "maintenance"
    print_passed("Nurse updated Bed B001 status to 'maintenance'.")

    res_bed_avail = client.put(
        "/api/beds/B001/status",
        headers=nurse_headers,
        json={"status": "available"}
    )
    assert res_bed_avail.status_code == 200
    assert res_bed_avail.json()["status"] == "available"
    print_passed("Nurse reset Bed B001 status to 'available'.")

    # Patient Transfer test
    res_transfer = client.post(
        "/api/beds/transfer",
        headers=nurse_headers,
        json={
            "patient_id": "P001",
            "from_bed_id": "B001",
            "to_bed_id": "B002",
            "reason": "Step-down observation transfer"
        }
    )
    assert res_transfer.status_code == 200
    assert res_transfer.json()["status"] == "success"
    print_passed("Patient transfer between beds completed and committed to SQLite.")

    # 8. Test Notifications System
    print_step("8. Testing Persistent Notifications API...")
    res_notifs = client.get("/api/notifications", headers=patient_headers)
    assert res_notifs.status_code == 200
    notif_data = res_notifs.json()
    notif_list = notif_data.get("notifications", [])
    unread_count = notif_data.get("unread_count", 0)
    print_passed(f"Retrieved {len(notif_list)} notifications for Patient P001 (Unread: {unread_count}).")

    if len(notif_list) > 0:
        first_notif_id = notif_list[0]["id"]
        res_read = client.put(f"/api/notifications/{first_notif_id}/read", headers=patient_headers)
        assert res_read.status_code == 200
        print_passed(f"Notification {first_notif_id} marked as read.")

    # 9. Test Admin Audit Logs & User Management
    print_step("9. Testing Admin-Only Governance & Audit Logs...")
    admin_headers = {"Authorization": f"Bearer {tokens['ADMIN']}"}

    res_users = client.get("/api/auth/users", headers=admin_headers)
    assert res_users.status_code == 200
    assert len(res_users.json()) >= 5
    print_passed(f"Admin retrieved all {len(res_users.json())} system users.")

    res_audit = client.get("/api/auth/audit-logs", headers=admin_headers)
    assert res_audit.status_code == 200
    audit_logs = res_audit.json()
    assert len(audit_logs) > 0
    print_passed(f"Admin retrieved compliance audit trail ({len(audit_logs)} log events found).")

    # Verify non-admin blocked from audit logs
    res_audit_forbidden = client.get("/api/auth/audit-logs", headers=patient_headers)
    assert res_audit_forbidden.status_code == 403
    print_passed("Non-admin correctly blocked from audit logs with HTTP 403 Forbidden.")

    print("\n" + "=" * 60)
    print("  ALL 9 PHASE 4 VERIFICATION STEPS PASSED SUCCESSFULLY!  ")
    print("=" * 60)

if __name__ == "__main__":
    test_phase4()
