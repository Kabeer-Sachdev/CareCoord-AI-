import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from backend.main import app
from backend.seed.seed_database import run_seed
from backend.database.database import SessionLocal
from backend.database.models import Appointment, WorkflowRun, WorkflowEvent

client = TestClient(app)

def reset_test_db():
    run_seed()
    db = SessionLocal()
    try:
        # Remove any dynamic appointments created during previous test runs
        db.query(Appointment).filter(Appointment.id > 30).delete()
        db.commit()
    finally:
        db.close()

def test_phase3_backend():
    print("==================================================")
    print("  RUNNING CARECOORD PHASE 3 BACKEND VERIFICATION  ")
    print("==================================================")

    # 1. Reset database to initial seeded state
    reset_test_db()

    # 2. Test Workflow 1: Doctor Search via LangGraph
    print("\n[Step 1] Testing Workflow 1 (Doctor Search): 'Find me an available cardiologist'...")
    res = client.post("/api/workflows", json={"message": "Find me an available cardiologist."})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    wf1 = res.json()
    assert wf1["workflow_id"] is not None
    assert wf1["agent_used"] == "Doctor Agent"
    assert "Dr. Mehta" in wf1["recommendation"] or "Cardiology" in wf1["recommendation"]
    print(f"  -> PASSED: Workflow ID {wf1['workflow_id']} | Agent: {wf1['agent_used']}")
    print(f"  -> Recommendation: {wf1['recommendation']}")

    # 3. Test Workflow 2: Primary Demo (Appointment Request requiring Human Approval)
    print("\n[Step 2] Testing Workflow 2 (Primary Demo): 'I need an appointment with a cardiologist tomorrow.'...")
    res = client.post("/api/workflows", json={"message": "I need an appointment with a cardiologist tomorrow."})
    assert res.status_code == 200
    wf2 = res.json()
    wf2_id = wf2["workflow_id"]
    assert wf2["requires_human_approval"] is True, f"Expected requires_human_approval True, got {wf2}"
    assert wf2["agent_used"] == "Appointment Agent"
    print(f"  -> PASSED: Workflow ID {wf2_id} | Requires Human Approval: {wf2['requires_human_approval']}")
    print(f"  -> Recommendation: {wf2['recommendation']}")

    # 4. Test Workflow History & Detail API
    print(f"\n[Step 3] Testing GET /api/workflows/{wf2_id} and GET /api/workflows/{wf2_id}/events...")
    res_detail = client.get(f"/api/workflows/{wf2_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["status"] == "REQUIRES_HUMAN_APPROVAL"
    assert len(detail["events"]) >= 3
    print(f"  -> PASSED: Retrieved {len(detail['events'])} graph execution events for {wf2_id}.")

    # 5. Test Human Approval API (POST /api/workflows/{id}/approve)
    print(f"\n[Step 4] Testing Human Approval API: POST /api/workflows/{wf2_id}/approve...")
    res_app = client.post(f"/api/workflows/{wf2_id}/approve", json={"action": "approve", "notes": "Approved by supervisor"})
    assert res_app.status_code == 200
    app_res = res_app.json()
    assert app_res["status"] == "success"
    assert app_res["workflow_status"] == "COMPLETED"
    print(f"  -> PASSED: Workflow {wf2_id} status updated to COMPLETED after approval.")

    # 6. Test Workflow 3: Patient Information Lookup
    print("\n[Step 5] Testing Workflow 3 (Patient Info): 'Show appointments for patient P001.'...")
    res = client.post("/api/workflows", json={"message": "Show appointments for patient P001."})
    assert res.status_code == 200
    wf3 = res.json()
    assert wf3["agent_used"] == "Patient Agent"
    assert "Rahul Sharma" in wf3["recommendation"] or "P001" in wf3["recommendation"]
    print(f"  -> PASSED: Workflow ID {wf3['workflow_id']} | Agent: {wf3['agent_used']}")

    # 7. Test Workflow 4: Missing Information Clarification
    print("\n[Step 6] Testing Workflow 4 (Missing Info): 'Book an appointment.'...")
    res = client.post("/api/workflows", json={"message": "Book an appointment."})
    assert res.status_code == 200
    wf4 = res.json()
    assert wf4["status"] == "clarification_required"
    assert "Which department" in wf4["recommendation"] or "doctor" in wf4["recommendation"]
    print(f"  -> PASSED: Status '{wf4['status']}' | Prompt: {wf4['recommendation']}")

    # 8. Test Workflow 5: No Availability Scenario
    print("\n[Step 7] Testing Workflow 5 (No Availability Scenario): 'Find an available neurologist'...")
    res = client.post("/api/workflows", json={"message": "Find an available neurologist."})
    assert res.status_code == 200
    wf5 = res.json()
    assert wf5["status"] in ["success", "no_availability"]
    print(f"  -> PASSED: Handled specialization query cleanly.")

    # 9. Test GET /api/workflows history endpoint
    print("\n[Step 8] Testing GET /api/workflows...")
    res = client.get("/api/workflows")
    assert res.status_code == 200
    history = res.json()
    assert len(history) >= 4
    print(f"  -> PASSED: Retrieved {len(history)} workflow history records from SQLite.")

    print("\n==================================================")
    print("  ALL PHASE 3 BACKEND VERIFICATION STEPS PASSED!  ")
    print("==================================================")

if __name__ == "__main__":
    test_phase3_backend()
