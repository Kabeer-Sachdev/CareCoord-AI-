import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from backend.main import app
from backend.seed.seed_database import run_seed

client = TestClient(app)

def test_phase2_backend():
    print("==================================================")
    print("  RUNNING CARECOORD PHASE 2 BACKEND VERIFICATION  ")
    print("==================================================")

    # 1. Run seed script
    run_seed()

    # 2. Test GET /api/dashboard/summary
    print("\n[Step 1] Testing GET /api/dashboard/summary...")
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    dash_data = res.json()
    assert dash_data["status"] == "healthy"
    assert "kpis" in dash_data
    assert "resource_utilization" in dash_data
    assert "doctor_availability" in dash_data
    print("  -> PASSED KPIs:", dash_data["kpis"])
    print("  -> PASSED Utilization:", dash_data["resource_utilization"])

    # 3. Test Workflow Request: Appointment with Cardiologist
    print("\n[Step 2] Testing Query 1: 'I need an appointment with a cardiologist tomorrow.'...")
    res = client.post("/api/workflow/request", json={"message": "I need an appointment with a cardiologist tomorrow."})
    assert res.status_code == 200
    wf_res = res.json()
    assert wf_res["agent_used"] == "Appointment Agent"
    assert wf_res["status"] == "success"
    print("  -> PASSED Agent:", wf_res["agent_used"])
    print("  -> Recommendation:", wf_res["recommendation"])

    # 4. Test Workflow Request: Find available neurologist
    print("\n[Step 3] Testing Query 2: 'Find an available neurologist.'...")
    res = client.post("/api/workflow/request", json={"message": "Find an available neurologist."})
    assert res.status_code == 200
    wf_res = res.json()
    assert wf_res["agent_used"] == "Doctor Agent"
    print("  -> PASSED Agent:", wf_res["agent_used"])
    print("  -> Recommendation:", wf_res["recommendation"])

    # 5. Test Workflow Request: Show appointments for patient P001
    print("\n[Step 4] Testing Query 3: 'Show appointments for patient P001.'...")
    res = client.post("/api/workflow/request", json={"message": "Show appointments for patient P001."})
    assert res.status_code == 200
    wf_res = res.json()
    assert wf_res["agent_used"] == "Patient Agent"
    print("  -> PASSED Agent:", wf_res["agent_used"])
    print("  -> Recommendation:", wf_res["recommendation"])

    # 6. Test Workflow Request: Find an available doctor
    print("\n[Step 5] Testing Query 4: 'Find an available doctor.'...")
    res = client.post("/api/workflow/request", json={"message": "Find an available doctor."})
    assert res.status_code == 200
    wf_res = res.json()
    assert wf_res["agent_used"] == "Doctor Agent"
    print("  -> PASSED Agent:", wf_res["agent_used"])
    print("  -> Recommendation:", wf_res["recommendation"])

    # 7. Test Workflow Request: Book an appointment (Clarification prompt check!)
    print("\n[Step 6] Testing Query 5: 'Book an appointment.' (Clarification Check)...")
    res = client.post("/api/workflow/request", json={"message": "Book an appointment."})
    assert res.status_code == 200
    wf_res = res.json()
    assert wf_res["status"] == "clarification_required"
    print("  -> PASSED Clarification Prompt:", wf_res["recommendation"])

    print("\n==================================================")
    print("  ALL PHASE 2 BACKEND VERIFICATION STEPS PASSED!  ")
    print("==================================================")

if __name__ == "__main__":
    test_phase2_backend()
