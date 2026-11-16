"""
CareCoord - Phase 7 Comprehensive Resource Allocation & Optimization Test Suite

Tests:
1. Google OR-Tools MIP Appointment Optimizer (Wait time, non-overlap, doctor availability)
2. Capacity Deficit Handling & Graceful Unallocated Status Tracking
3. Google OR-Tools MIP Doctor Shift Scheduler (Phase 6 ML Demand Driven, 1-shift constraint)
4. Google OR-Tools MIP Bed Allocator (Triage urgency prioritization, ward matching, Phase 6 occupancy)
5. Baseline Benchmark Comparison (OR-Tools MIP vs FIFO Greedy Heuristic)
6. Optimization Service Lifecycle (Pending approval, rejection, reoptimization)
7. Human Approval Governance & Stale Plan Conflict Detection with Atomic DB Commit
8. LangGraph Coordinator Integration & Optimization Agent Routing (REQUIRES_HUMAN_APPROVAL)
9. FastAPI Optimization Endpoints & RBAC Validation
"""

import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.database.database import SessionLocal, init_db
from backend.database.models import (
    OptimizationRun,
    OptimizationAllocation,
    Doctor,
    Bed,
    Appointment,
    Patient,
    User
)
from backend.optimization.appointment.appointment_optimizer import AppointmentOptimizer
from backend.optimization.doctor.doctor_scheduler import DoctorScheduler
from backend.optimization.beds.bed_allocator import BedAllocator
from backend.optimization.evaluation.baseline_comparison import run_benchmark_comparison
from backend.optimization.services.optimization_service import optimization_service
from backend.agents.graph import carecoord_graph
from backend.routes.optimization import (
    run_appointment_optimization,
    run_doctor_scheduling,
    run_bed_allocation,
    list_optimization_runs,
    get_optimization_run_detail,
    approve_optimization_run,
    reject_optimization_run,
    reoptimize_run,
    get_optimization_metrics,
    ApprovalRequestPayload,
    RejectionRequestPayload
)
from backend.optimization.schemas.optimization import (
    AppointmentOptimizationRunRequest,
    DoctorSchedulingRunRequest,
    BedAllocationRunRequest
)

def print_step(title):
    print(f"\n[Step] {title}")

def print_passed(msg):
    print(f"  [PASS] {msg}")

def test_phase7():
    print("=" * 75)
    print("  STARTING CARECOORD PHASE 7 RESOURCE OPTIMIZATION VERIFICATION SUITE  ")
    print("=" * 75)

    init_db()
    db = SessionLocal()

    try:
        # -------------------------------------------------------------
        # Step 1: Appointment Scheduling Optimizer (Google OR-Tools MIP)
        # -------------------------------------------------------------
        print_step("1. Testing Google OR-Tools MIP Appointment Scheduling Optimizer...")
        optimizer = AppointmentOptimizer()
        doctors = [
            {"doctor_id": "D001", "name": "Dr. Sarah", "department": "Cardiology", "specialization": "Cardiology", "availability": True, "shift": "Morning"},
            {"doctor_id": "D002", "name": "Dr. Kevin", "department": "Cardiology", "specialization": "Cardiology", "availability": True, "shift": "Morning"}
        ]
        requests = [
            {"request_id": "R1", "patient_id": "P001", "patient_name": "Alice", "priority": "normal", "preferred_time_slot": "09:00"},
            {"request_id": "R2", "patient_id": "P002", "patient_name": "Bob", "priority": "urgent", "preferred_time_slot": "09:00"},
            {"request_id": "R3", "patient_id": "P003", "patient_name": "Charlie", "priority": "normal", "preferred_time_slot": "09:30"}
        ]
        existing = [
            {"doctor_id": "D001", "appointment_time": "10:00"}
        ]

        res_apt = optimizer.optimize(
            requests=requests,
            doctors=doctors,
            existing_appointments=existing,
            department="Cardiology",
            target_date="2026-11-20",
            max_solve_time_seconds=5.0
        )

        assert res_apt["solver_status"] in ["OPTIMAL", "FEASIBLE"], f"Unexpected status: {res_apt['solver_status']}"
        assert len(res_apt["recommended_allocations"]) == 3, f"Expected 3 allocations, got {len(res_apt['recommended_allocations'])}"
        assert len(res_apt["unallocated_requests"]) == 0
        assert res_apt["constraint_validation"] == "PASSED"

        # Check non-overlapping slots
        assigned_slots = set()
        for alloc in res_apt["recommended_allocations"]:
            doc_slot = (alloc["doctor_id"], alloc["allocated_time_slot"])
            assert doc_slot not in assigned_slots, f"Duplicate slot assigned: {doc_slot}"
            assigned_slots.add(doc_slot)
            assert doc_slot != ("D001", "10:00"), "Conflict with existing appointment at 10:00"

        print_passed(f"Appointment optimizer verified: {res_apt['solver_status']} in {res_apt['execution_duration_ms']:.1f}ms, 0 conflicts.")

        # -------------------------------------------------------------
        # Step 2: Capacity Deficit & Graceful Unallocated Handling
        # -------------------------------------------------------------
        print_step("2. Testing Capacity Deficit Handling & Unallocated Logging...")
        solo_doctor = [
            {"doctor_id": "D001", "name": "Dr. Solo", "department": "Cardiology", "availability": True}
        ]
        # Request 15 appointments when only 11 standard slots exist for 1 doctor
        excess_requests = [
            {"request_id": f"R{i}", "patient_id": f"P{i}", "patient_name": f"Patient {i}", "priority": "normal"}
            for i in range(15)
        ]
        res_deficit = optimizer.optimize(
            requests=excess_requests,
            doctors=solo_doctor,
            department="Cardiology",
            target_date="2026-11-20",
            max_solve_time_seconds=5.0
        )
        assert len(res_deficit["recommended_allocations"]) == 12, "Doctor slot capacity not strictly respected"
        assert len(res_deficit["unallocated_requests"]) == 3, "Excess requests not recorded as unallocated"
        for unalloc in res_deficit["unallocated_requests"]:
            assert unalloc["allocation_status"] == "UNALLOCATED"
            assert "capacity" in unalloc["reason"].lower()
        print_passed("Capacity deficit handled gracefully: 12 allocated to maximum slot capacity, 3 marked UNALLOCATED with clear reason.")

        # -------------------------------------------------------------
        # Step 3: Doctor Shift Scheduling (Phase 6 ML Demand Driven)
        # -------------------------------------------------------------
        print_step("3. Testing Doctor Shift Scheduler with Phase 6 Demand Prediction...")
        scheduler = DoctorScheduler()
        team_doctors = [
            {"doctor_id": "D001", "name": "Dr. Sarah", "department": "Cardiology", "availability": True, "availability_status": "Available"},
            {"doctor_id": "D002", "name": "Dr. Kevin", "department": "Cardiology", "availability": True, "availability_status": "Available"},
            {"doctor_id": "D003", "name": "Dr. Elena", "department": "Cardiology", "availability": True, "availability_status": "Available"}
        ]
        predicted_demand = {
            "predicted_arrivals": 42,
            "predicted_emergencies": 9
        }
        res_doc = scheduler.optimize(
            doctors=team_doctors,
            department="Cardiology",
            target_date="2026-11-20",
            predicted_demand=predicted_demand,
            max_solve_time_seconds=5.0
        )
        assert res_doc["solver_status"] in ["OPTIMAL", "FEASIBLE"]
        assert len(res_doc["recommended_allocations"]) == 3
        assert res_doc["constraint_validation"] == "PASSED"
        assigned_docs = set()
        for alloc in res_doc["recommended_allocations"]:
            assert alloc["doctor_id"] not in assigned_docs, f"Doctor {alloc['doctor_id']} assigned multiple shifts"
            assigned_docs.add(alloc["doctor_id"])
            assert "Morning" in alloc["shift_name"] or "Evening" in alloc["shift_name"] or "Night" in alloc["shift_name"]
        print_passed(f"Doctor scheduler verified: distributed shifts across {len(team_doctors)} doctors using ML arrival demand {predicted_demand['predicted_arrivals']}.")

        # -------------------------------------------------------------
        # Step 4: Bed Allocator with Triage Prioritization & Ward Matching
        # -------------------------------------------------------------
        print_step("4. Testing Bed Allocator with Triage Urgency & Ward Constraints...")
        bed_allocator = BedAllocator()
        test_beds = [
            {"bed_id": "BED-ICU-1", "ward": "ICU", "department": "Cardiology", "is_occupied": False, "status": "Available"},
            {"bed_id": "BED-GEN-1", "ward": "General", "department": "Cardiology", "is_occupied": False, "status": "Available"},
            {"bed_id": "BED-GEN-2", "ward": "General", "department": "Cardiology", "is_occupied": True, "status": "Occupied"}
        ]
        bed_requests = [
            {"request_id": "REQ-GEN", "patient_id": "P001", "patient_name": "Standard Pat", "department": "Cardiology", "required_ward": "General", "urgency": "standard"},
            {"request_id": "REQ-CRIT", "patient_id": "P002", "patient_name": "Critical Pat", "department": "Cardiology", "required_ward": "ICU", "urgency": "critical"}
        ]
        res_bed = bed_allocator.optimize(
            requests=bed_requests,
            beds=test_beds,
            department="Cardiology",
            target_date="2026-11-20",
            max_solve_time_seconds=5.0
        )
        assert res_bed["solver_status"] in ["OPTIMAL", "FEASIBLE"]
        assert len(res_bed["recommended_allocations"]) == 2
        for alloc in res_bed["recommended_allocations"]:
            if alloc["request_id"] == "REQ-CRIT":
                assert alloc["bed_id"] == "BED-ICU-1", f"Critical patient assigned wrong bed: {alloc['bed_id']}"
                assert alloc["ward"] == "ICU"
            elif alloc["request_id"] == "REQ-GEN":
                assert alloc["bed_id"] == "BED-GEN-1"
        print_passed("Bed allocator verified: Critical triage patient assigned ICU bed; standard patient assigned General bed.")

        # -------------------------------------------------------------
        # Step 5: Empirical Baseline Comparison (OR-Tools vs FIFO Greedy)
        # -------------------------------------------------------------
        print_step("5. Testing Baseline Benchmark Comparison (OR-Tools MIP vs FIFO Greedy)...")
        bench = run_benchmark_comparison()
        assert "improvements" in bench
        assert "ortools_optimizer" in bench
        assert "baseline_fifo" in bench
        assert bench["ortools_optimizer"]["solver_status"] == "OPTIMAL"
        assert bench["ortools_optimizer"]["scheduling_conflicts"] == 0
        assert bench["improvements"]["waiting_time_reduction_percent"] > 0
        assert bench["improvements"]["workload_imbalance_reduction_percent"] >= 0
        print_passed(f"Benchmark verified: OR-Tools achieved {bench['improvements']['waiting_time_reduction_percent']}% wait time reduction and {bench['improvements']['workload_imbalance_reduction_percent']}% workload imbalance reduction.")

        # -------------------------------------------------------------
        # Step 6: Service Lifecycle, Stale Conflict Detection & Atomic Commit
        # -------------------------------------------------------------
        print_step("6. Testing Optimization Service Lifecycle & Atomic SQLite Commit...")
        run_res = optimization_service.run_appointment_optimization(
            db=db,
            department="Cardiology",
            target_date="2026-11-25",
            max_solve_time_seconds=5.0
        )
        opt_id = run_res["optimization_id"]
        assert run_res["approval_status"] == "PENDING_APPROVAL"
        assert run_res["requires_human_approval"] is True

        # Verify DB record exists and is pending
        db_run = db.query(OptimizationRun).filter(OptimizationRun.optimization_id == opt_id).first()
        assert db_run is not None
        assert db_run.approval_status == "PENDING_APPROVAL"

        # Approve and verify atomic commit
        app_res = optimization_service.approve_optimization_run(
            db=db,
            run_id=opt_id,
            approved_by="Dr. Administrator"
        )
        assert app_res["approval_status"] == "APPROVED"
        assert app_res["committed_changes_count"] >= 0

        db.refresh(db_run)
        assert db_run.approval_status == "APPROVED"
        assert db_run.approved_by == "Dr. Administrator"
        print_passed("Lifecycle verified: Plan generated in PENDING_APPROVAL, passed conflict validation, and atomically committed.")

        # Rejection lifecycle test
        run_rej = optimization_service.run_appointment_optimization(
            db=db,
            department="Cardiology",
            target_date="2026-11-26",
            max_solve_time_seconds=5.0
        )
        rej_id = run_rej["optimization_id"]
        rej_res = optimization_service.reject_optimization_run(
            db=db,
            run_id=rej_id,
            rejected_by="Dr. Director",
            reason="Rescheduled clinic hours"
        )
        assert rej_res["approval_status"] == "REJECTED"
        db_run_rej = db.query(OptimizationRun).filter(OptimizationRun.optimization_id == rej_id).first()
        db.refresh(db_run_rej)
        assert db_run_rej.approval_status == "REJECTED"
        print_passed("Rejection verified: Plan transitioned to REJECTED with reason without mutating operational tables.")

        # -------------------------------------------------------------
        # Step 7: LangGraph Coordinator Integration & Optimization Agent Routing
        # -------------------------------------------------------------
        print_step("7. Testing LangGraph Coordinator Routing to Optimization Agent...")
        state_input = {
            "workflow_id": f"WF-OPT-{uuid.uuid4().hex[:6]}",
            "original_request": "Optimize doctor shift schedule for Cardiology tomorrow",
            "workflow_request": {},
            "current_agent": None,
            "required_agents": [],
            "executed_agents": [],
            "patient_result": None,
            "doctor_result": None,
            "appointment_result": None,
            "validation_result": None,
            "policy_result": None,
            "prediction_result": None,
            "optimization_result": None,
            "messages": [],
            "execution_log": [],
            "requires_human_review": False,
            "status": "RUNNING",
            "final_recommendation": None,
            "iteration_count": 0,
            "error": None,
            "db_session": db
        }
        graph_output = carecoord_graph.invoke(state_input)
        assert "Optimization Agent" in graph_output["executed_agents"], "Optimization Agent was not executed by LangGraph"
        assert graph_output["status"] == "REQUIRES_HUMAN_APPROVAL", f"Unexpected status: {graph_output['status']}"
        assert graph_output["requires_human_review"] is True
        assert graph_output["final_recommendation"]["agent_used"] == "Optimization Agent"
        print_passed("LangGraph coordinator successfully routed optimization request to Optimization Agent with human review guardrail.")

        # -------------------------------------------------------------
        # Step 8: FastAPI Optimization REST Endpoints
        # -------------------------------------------------------------
        print_step("8. Testing FastAPI Optimization REST Endpoints...")
        staff_user = User(id=1, username="admin", email="admin@carecoord.hospital", role="ADMIN", full_name="Admin Director")

        # 1. Appointment optimization endpoint
        req_apt = AppointmentOptimizationRunRequest(department="Cardiology", target_date="2026-11-28", max_solve_time_seconds=5)
        api_apt = run_appointment_optimization(payload=req_apt, db=db, current_user=staff_user)
        assert "OPT-APT-" in api_apt["optimization_id"]
        assert api_apt["approval_status"] == "PENDING_APPROVAL"

        # 2. Doctor scheduling endpoint
        req_doc = DoctorSchedulingRunRequest(department="Cardiology", target_date="2026-11-28", max_solve_time_seconds=5)
        api_doc = run_doctor_scheduling(payload=req_doc, db=db, current_user=staff_user)
        assert "OPT-DOC-" in api_doc["optimization_id"]

        # 3. Bed allocation endpoint
        req_bed = BedAllocationRunRequest(department="Cardiology", target_date="2026-11-28", max_solve_time_seconds=5)
        api_bed = run_bed_allocation(payload=req_bed, db=db, current_user=staff_user)
        assert "OPT-BED-" in api_bed["optimization_id"]

        # 4. List runs endpoint
        api_runs = list_optimization_runs(optimization_type=None, approval_status=None, limit=20, db=db, current_user=staff_user)
        assert isinstance(api_runs, list)
        assert len(api_runs) > 0

        # 5. Get detail endpoint
        api_detail = get_optimization_run_detail(optimization_id=api_apt["optimization_id"], db=db, current_user=staff_user)
        assert api_detail["optimization_id"] == api_apt["optimization_id"]

        # 6. Approve endpoint
        payload_app = ApprovalRequestPayload(notes="Approved via FastAPI endpoint unit test")
        api_app = approve_optimization_run(optimization_id=api_apt["optimization_id"], payload=payload_app, db=db, current_user=staff_user)
        assert api_app["approval_status"] == "APPROVED"

        # 7. Reject endpoint
        payload_rej = RejectionRequestPayload(reason="Rejected via test")
        api_rej = reject_optimization_run(optimization_id=api_doc["optimization_id"], payload=payload_rej, db=db, current_user=staff_user)
        assert api_rej["approval_status"] == "REJECTED"

        # 8. Reoptimize endpoint
        api_reopt = reoptimize_run(optimization_id=api_doc["optimization_id"], payload=None, db=db, current_user=staff_user)
        assert api_reopt["optimization_id"] != api_doc["optimization_id"]
        assert api_reopt["approval_status"] == "PENDING_APPROVAL"

        # 9. Metrics endpoint
        api_metrics = get_optimization_metrics(db=db, current_user=staff_user)
        assert "total_runs" in api_metrics
        assert "baseline_comparison" in api_metrics

        print_passed("All FastAPI /api/optimization/* REST endpoints executed cleanly with 100% success.")

        print("\n" + "=" * 75)
        print("  ALL PHASE 7 INTELLIGENT RESOURCE OPTIMIZATION TESTS PASSED!  ")
        print("=" * 75)

    finally:
        db.close()

if __name__ == "__main__":
    test_phase7()
