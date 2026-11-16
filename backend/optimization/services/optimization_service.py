import os
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

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
from backend.services.audit_service import log_audit
from backend.ml.prediction.prediction_service import prediction_service

class OptimizationService:
    def __init__(self):
        self.appointment_optimizer = AppointmentOptimizer()
        self.doctor_scheduler = DoctorScheduler()
        self.bed_allocator = BedAllocator()

    # -------------------------------------------------------------
    # 1. Appointment Scheduling Optimization
    # -------------------------------------------------------------
    def run_appointment_optimization(
        self,
        db: Session,
        department: str = "Cardiology",
        target_date: Optional[str] = None,
        custom_requests: Optional[List[Dict[str, Any]]] = None,
        max_solve_time_seconds: float = 10.0,
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        target_dt_str = target_date or (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

        # 1. Fetch Doctors from SQLite
        doctors_db = db.query(Doctor).filter(
            Doctor.department == department
        ).all()
        doctors_list = [
            {
                "doctor_id": d.doctor_id,
                "name": d.name,
                "department": d.department,
                "specialization": d.specialization,
                "availability": d.availability,
                "availability_status": d.availability_status or "Available"
            }
            for d in doctors_db
        ]

        # 2. Fetch Existing Confirmed Appointments from SQLite
        existing_appts_db = db.query(Appointment).filter(
            Appointment.appointment_date == target_dt_str,
            Appointment.status.in_(["scheduled", "Confirmed", "Scheduled"])
        ).all()
        existing_appts = [
            {
                "doctor_id": a.doctor_id,
                "date": a.appointment_date,
                "time_slot": a.appointment_time,
                "patient_id": a.patient_id
            }
            for a in existing_appts_db
        ]

        # 3. Consume Phase 6 ML Demand Prediction
        ml_prediction = {}
        try:
            ml_prediction = prediction_service.predict_appointment_demand(
                department=department,
                forecast_date=target_dt_str
            )
        except Exception:
            ml_prediction = {"predicted_value": 8, "data_type": "fallback_operational"}

        # 4. Formulate Requests: use custom if provided, otherwise sample patients
        requests_list = []
        if custom_requests:
            requests_list = custom_requests
        else:
            # Gather unallocated / requesting patients from SQLite
            patients = db.query(Patient).filter(Patient.department == department).limit(8).all()
            if not patients:
                patients = db.query(Patient).limit(6).all()

            for idx, p in enumerate(patients):
                requests_list.append({
                    "request_id": f"REQ-APT-{p.patient_id}-{idx+1}",
                    "patient_id": p.patient_id,
                    "patient_name": p.name,
                    "department": department,
                    "priority": "urgent" if idx == 0 else "normal",
                    "preferred_time_slot": "10:00 AM" if idx == 0 else None
                })

        # 5. Execute OR-Tools Optimizer
        opt_res = self.appointment_optimizer.optimize(
            requests=requests_list,
            doctors=doctors_list,
            existing_appointments=existing_appts,
            department=department,
            target_date=target_dt_str,
            max_solve_time_seconds=max_solve_time_seconds
        )

        # 6. Persist OptimizationRun & Allocations in SQLite
        opt_id = f"OPT-APT-{uuid.uuid4().hex[:8].upper()}"
        all_allocs = opt_res["recommended_allocations"] + opt_res["unallocated_requests"]

        opt_run = OptimizationRun(
            optimization_id=opt_id,
            optimization_type="APPOINTMENT_SCHEDULING",
            department=department,
            target_date=target_dt_str,
            solver_status=opt_res["solver_status"],
            objective_value=opt_res["objective_value"],
            execution_duration_ms=opt_res["execution_duration_ms"],
            constraint_validation=opt_res["constraint_validation"],
            total_requests=len(requests_list),
            allocated_count=len(opt_res["recommended_allocations"]),
            unallocated_count=len(opt_res["unallocated_requests"]),
            approval_status="PENDING_APPROVAL",
            requires_human_approval=True,
            ml_forecast_snapshot=ml_prediction,
            metrics_snapshot={
                "allocated_ratio": round(len(opt_res["recommended_allocations"]) / max(1, len(requests_list)), 2),
                "solver_duration_ms": opt_res["execution_duration_ms"]
            },
            parameters={
                "department": department,
                "target_date": target_dt_str,
                "max_solve_time_seconds": max_solve_time_seconds
            }
        )
        db.add(opt_run)
        db.flush()

        for alloc in all_allocs:
            db_alloc = OptimizationAllocation(
                optimization_id=opt_id,
                entity_type="APPOINTMENT",
                request_id=alloc["request_id"],
                patient_id=alloc.get("patient_id"),
                patient_name=alloc.get("patient_name"),
                doctor_id=alloc.get("doctor_id"),
                doctor_name=alloc.get("doctor_name"),
                department=alloc.get("department", department),
                allocated_time_slot=alloc.get("allocated_time_slot"),
                allocation_status=alloc["allocation_status"],
                reason=alloc.get("reason"),
                is_committed=False
            )
            db.add(db_alloc)

        db.commit()

        if current_user:
            log_audit(
                db=db,
                user=current_user,
                action="RUN_APPOINTMENT_OPTIMIZATION",
                entity_type="OPTIMIZATION_RUN",
                entity_id=opt_id,
                metadata={
                    "department": department,
                    "solver_status": opt_res["solver_status"],
                    "allocated": len(opt_res["recommended_allocations"]),
                    "unallocated": len(opt_res["unallocated_requests"])
                }
            )

        return self.get_optimization_run(db, opt_id)

    # -------------------------------------------------------------
    # 2. Doctor Scheduling Optimization
    # -------------------------------------------------------------
    def run_doctor_scheduling_optimization(
        self,
        db: Session,
        department: str = "Cardiology",
        target_date: Optional[str] = None,
        shifts: Optional[List[str]] = None,
        max_solve_time_seconds: float = 10.0,
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        target_dt_str = target_date or (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

        doctors_db = db.query(Doctor).filter(
            Doctor.department == department
        ).all()
        doctors_list = [
            {
                "doctor_id": d.doctor_id,
                "name": d.name,
                "department": d.department,
                "specialization": d.specialization,
                "availability": d.availability,
                "availability_status": d.availability_status or "Available",
                "shift": d.shift
            }
            for d in doctors_db
        ]

        # Consume Phase 6 Demand Prediction
        ml_prediction = {}
        try:
            arr_pred = prediction_service.predict_patient_arrivals(department, target_dt_str)
            er_pred = prediction_service.predict_emergency_demand(department, target_dt_str)
            ml_prediction = {
                "predicted_arrivals": arr_pred["predicted_value"],
                "predicted_emergencies": er_pred["predicted_value"]
            }
        except Exception:
            ml_prediction = {"predicted_arrivals": 25, "predicted_emergencies": 6}

        opt_res = self.doctor_scheduler.optimize(
            doctors=doctors_list,
            department=department,
            target_date=target_dt_str,
            predicted_demand=ml_prediction,
            shifts=shifts,
            max_solve_time_seconds=max_solve_time_seconds
        )

        opt_id = f"OPT-DOC-{uuid.uuid4().hex[:8].upper()}"
        all_allocs = opt_res["recommended_allocations"] + opt_res["unallocated_requests"]

        opt_run = OptimizationRun(
            optimization_id=opt_id,
            optimization_type="DOCTOR_SCHEDULING",
            department=department,
            target_date=target_dt_str,
            solver_status=opt_res["solver_status"],
            objective_value=opt_res["objective_value"],
            execution_duration_ms=opt_res["execution_duration_ms"],
            constraint_validation=opt_res["constraint_validation"],
            total_requests=len(doctors_list),
            allocated_count=len(opt_res["recommended_allocations"]),
            unallocated_count=len(opt_res["unallocated_requests"]),
            approval_status="PENDING_APPROVAL",
            requires_human_approval=True,
            ml_forecast_snapshot=ml_prediction,
            metrics_snapshot=opt_res.get("staffing_demand", {}),
            parameters={
                "department": department,
                "target_date": target_dt_str,
                "max_solve_time_seconds": max_solve_time_seconds
            }
        )
        db.add(opt_run)
        db.flush()

        for alloc in all_allocs:
            db_alloc = OptimizationAllocation(
                optimization_id=opt_id,
                entity_type="DOCTOR_SHIFT",
                request_id=alloc["request_id"],
                doctor_id=alloc.get("doctor_id"),
                doctor_name=alloc.get("doctor_name"),
                department=alloc.get("department", department),
                shift_name=alloc.get("shift_name"),
                allocation_status=alloc["allocation_status"],
                reason=alloc.get("reason"),
                is_committed=False
            )
            db.add(db_alloc)

        db.commit()

        if current_user:
            log_audit(
                db=db,
                user=current_user,
                action="RUN_DOCTOR_SCHEDULING_OPTIMIZATION",
                entity_type="OPTIMIZATION_RUN",
                entity_id=opt_id,
                metadata={"department": department, "status": opt_res["solver_status"]}
            )

        return self.get_optimization_run(db, opt_id)

    # -------------------------------------------------------------
    # 3. Bed Allocation Optimization
    # -------------------------------------------------------------
    def run_bed_allocation_optimization(
        self,
        db: Session,
        department: Optional[str] = "Cardiology",
        target_date: Optional[str] = None,
        custom_requests: Optional[List[Dict[str, Any]]] = None,
        max_solve_time_seconds: float = 10.0,
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        target_dt_str = target_date or (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Fetch Beds from SQLite
        query = db.query(Bed)
        beds_db = query.all()

        beds_list = [
            {
                "bed_id": b.bed_id,
                "ward": b.bed_type or b.ward,
                "department": department or "General",
                "status": "AVAILABLE" if str(b.status).lower() == "available" else "OCCUPIED",
                "is_occupied": str(b.status).lower() != "available",
                "room_number": f"Floor-{b.floor}"
            }
            for b in beds_db
        ]

        # Consume Phase 6 Bed Occupancy Prediction
        ml_prediction = {}
        try:
            ml_prediction = prediction_service.predict_bed_occupancy(
                department=department or "Cardiology",
                forecast_date=target_dt_str
            )
        except Exception:
            ml_prediction = {"predicted_occupied_beds": 8, "total_beds": 12, "occupancy_rate": 0.67}

        requests_list = []
        if custom_requests:
            requests_list = custom_requests
        else:
            # Sample pending admission patients
            patients = db.query(Patient).filter(Patient.department == (department or "Cardiology")).limit(5).all()
            for idx, p in enumerate(patients):
                requests_list.append({
                    "request_id": f"REQ-BED-{p.patient_id}-{idx+1}",
                    "patient_id": p.patient_id,
                    "patient_name": p.name,
                    "department": department or p.department,
                    "required_ward": "ICU" if idx == 0 else "General",
                    "urgency": "critical" if idx == 0 else "standard"
                })

        opt_res = self.bed_allocator.optimize(
            requests=requests_list,
            beds=beds_list,
            department=department,
            predicted_occupancy=ml_prediction,
            max_solve_time_seconds=max_solve_time_seconds
        )

        opt_id = f"OPT-BED-{uuid.uuid4().hex[:8].upper()}"
        all_allocs = opt_res["recommended_allocations"] + opt_res["unallocated_requests"]

        opt_run = OptimizationRun(
            optimization_id=opt_id,
            optimization_type="BED_ALLOCATION",
            department=department,
            target_date=target_dt_str,
            solver_status=opt_res["solver_status"],
            objective_value=opt_res["objective_value"],
            execution_duration_ms=opt_res["execution_duration_ms"],
            constraint_validation=opt_res["constraint_validation"],
            total_requests=len(requests_list),
            allocated_count=len(opt_res["recommended_allocations"]),
            unallocated_count=len(opt_res["unallocated_requests"]),
            approval_status="PENDING_APPROVAL",
            requires_human_approval=True,
            ml_forecast_snapshot=ml_prediction,
            metrics_snapshot={
                "allocated_beds": len(opt_res["recommended_allocations"]),
                "available_beds_pool": sum(1 for b in beds_list if b["status"] == "AVAILABLE")
            },
            parameters={
                "department": department,
                "target_date": target_dt_str,
                "max_solve_time_seconds": max_solve_time_seconds
            }
        )
        db.add(opt_run)
        db.flush()

        for alloc in all_allocs:
            db_alloc = OptimizationAllocation(
                optimization_id=opt_id,
                entity_type="BED_ASSIGNMENT",
                request_id=alloc["request_id"],
                patient_id=alloc.get("patient_id"),
                patient_name=alloc.get("patient_name"),
                bed_id=alloc.get("bed_id"),
                ward=alloc.get("ward"),
                department=alloc.get("department", department),
                allocation_status=alloc["allocation_status"],
                reason=alloc.get("reason"),
                is_committed=False
            )
            db.add(db_alloc)

        db.commit()

        if current_user:
            log_audit(
                db=db,
                user=current_user,
                action="RUN_BED_ALLOCATION_OPTIMIZATION",
                entity_type="OPTIMIZATION_RUN",
                entity_id=opt_id,
                metadata={"department": department, "status": opt_res["solver_status"]}
            )

        return self.get_optimization_run(db, opt_id)

    # -------------------------------------------------------------
    # 4. Results & Queries
    # -------------------------------------------------------------
    def get_optimization_results(
        self,
        db: Session,
        limit: int = 50,
        department: Optional[str] = None,
        optimization_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = db.query(OptimizationRun).order_by(OptimizationRun.created_at.desc())
        if department:
            query = query.filter(OptimizationRun.department == department)
        if optimization_type:
            query = query.filter(OptimizationRun.optimization_type == optimization_type)

        runs = query.limit(limit).all()
        return [self._format_run_summary(r) for r in runs]

    def get_optimization_run(self, db: Session, optimization_id: str) -> Dict[str, Any]:
        run = db.query(OptimizationRun).filter(OptimizationRun.optimization_id == optimization_id).first()
        if not run:
            raise HTTPException(status_code=404, detail=f"Optimization run '{optimization_id}' not found.")

        recommended = []
        unallocated = []

        for a in run.allocations:
            item = {
                "request_id": a.request_id,
                "patient_id": a.patient_id,
                "patient_name": a.patient_name,
                "doctor_id": a.doctor_id,
                "doctor_name": a.doctor_name,
                "bed_id": a.bed_id,
                "ward": a.ward,
                "department": a.department,
                "allocated_time_slot": a.allocated_time_slot,
                "shift_name": a.shift_name,
                "allocation_status": a.allocation_status,
                "reason": a.reason
            }
            if a.allocation_status == "ALLOCATED":
                recommended.append(item)
            else:
                unallocated.append(item)

        return {
            "optimization_id": run.optimization_id,
            "optimization_type": run.optimization_type,
            "department": run.department,
            "target_date": run.target_date,
            "solver_status": run.solver_status,
            "objective_value": run.objective_value,
            "execution_duration_ms": run.execution_duration_ms,
            "constraint_validation": run.constraint_validation,
            "total_requests": run.total_requests,
            "allocated_count": run.allocated_count,
            "unallocated_count": run.unallocated_count,
            "approval_status": run.approval_status,
            "requires_human_approval": run.requires_human_approval,
            "approved_by": run.approved_by,
            "approved_at": run.approved_at,
            "recommended_allocations": recommended,
            "unallocated_requests": unallocated,
            "ml_forecast_snapshot": run.ml_forecast_snapshot or {},
            "metrics_snapshot": run.metrics_snapshot or {},
            "created_at": run.created_at
        }

    # -------------------------------------------------------------
    # 5. Human-in-the-Loop Approval & Transactional Commits
    # -------------------------------------------------------------
    def approve_optimization_plan(
        self,
        db: Session,
        optimization_id: str,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Validates stale plan conditions, commits operational database updates inside an atomic transaction,
        and logs audit trail.
        """
        run = db.query(OptimizationRun).filter(OptimizationRun.optimization_id == optimization_id).first()
        if not run:
            raise HTTPException(status_code=404, detail=f"Optimization run '{optimization_id}' not found.")

        if run.approval_status == "APPROVED" or run.approval_status == "COMMITTED":
            raise HTTPException(status_code=400, detail=f"Plan '{optimization_id}' is already approved and committed.")

        if run.approval_status == "REJECTED":
            raise HTTPException(status_code=400, detail=f"Plan '{optimization_id}' was rejected. Please re-optimize.")

        committed_details = []

        try:
            # 1. Stale Plan Verification & Atomic Database Commits
            if run.optimization_type == "APPOINTMENT_SCHEDULING":
                for alloc in run.allocations:
                    if alloc.allocation_status != "ALLOCATED":
                        continue

                    # Check for conflicts that occurred after solver run
                    existing_conflict = db.query(Appointment).filter(
                        Appointment.doctor_id == alloc.doctor_id,
                        Appointment.appointment_date == run.target_date,
                        Appointment.appointment_time == alloc.allocated_time_slot,
                        Appointment.status.in_(["scheduled", "Confirmed", "Scheduled"])
                    ).first()

                    if existing_conflict:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Stale plan conflict: Doctor {alloc.doctor_id} was booked at {alloc.allocated_time_slot} before approval."
                        )

                    # Create actual Confirmed appointment
                    new_appt_id = f"APT-OPT-{uuid.uuid4().hex[:6].upper()}"
                    new_appt = Appointment(
                        appointment_id=new_appt_id,
                        patient_id=alloc.patient_id or "P001",
                        doctor_id=alloc.doctor_id,
                        appointment_date=run.target_date,
                        appointment_time=alloc.allocated_time_slot,
                        status="scheduled",
                        department=alloc.department,
                        reason="Allocated via Phase 7 OR-Tools Optimization Engine."
                    )
                    db.add(new_appt)
                    alloc.is_committed = True
                    committed_details.append(
                        f"Created Appointment {new_appt_id} for Patient {alloc.patient_id} with Dr. {alloc.doctor_name} at {alloc.allocated_time_slot}"
                    )

            elif run.optimization_type == "BED_ALLOCATION":
                for alloc in run.allocations:
                    if alloc.allocation_status != "ALLOCATED":
                        continue

                    bed = db.query(Bed).filter(Bed.bed_id == alloc.bed_id).first()
                    if not bed or str(bed.status).lower() != "available":
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Stale plan conflict: Bed {alloc.bed_id} is no longer available (Status: {bed.status if bed else 'Missing'})."
                        )

                    bed.status = "occupied"
                    bed.patient_id = alloc.patient_id
                    alloc.is_committed = True
                    committed_details.append(
                        f"Allocated Bed {alloc.bed_id} ({alloc.ward} Ward) to Patient {alloc.patient_id}"
                    )

            elif run.optimization_type == "DOCTOR_SCHEDULING":
                for alloc in run.allocations:
                    if alloc.allocation_status != "ALLOCATED":
                        continue
                    doc = db.query(Doctor).filter(Doctor.doctor_id == alloc.doctor_id).first()
                    if doc:
                        doc.shift = alloc.shift_name
                        alloc.is_committed = True
                        committed_details.append(
                            f"Assigned Dr. {doc.name} to {alloc.shift_name} on {run.target_date}"
                        )

            # Update Optimization Run Record
            run.approval_status = "APPROVED"
            run.approved_by = current_user.username or current_user.email
            run.approved_at = datetime.utcnow()

            db.commit()

            log_audit(
                db=db,
                user=current_user,
                action="APPROVE_OPTIMIZATION_PLAN",
                entity_type="OPTIMIZATION_RUN",
                entity_id=optimization_id,
                metadata={
                    "type": run.optimization_type,
                    "committed_count": len(committed_details),
                    "target_date": run.target_date
                }
            )

            return {
                "optimization_id": optimization_id,
                "approval_status": "APPROVED",
                "approved_by": run.approved_by,
                "approved_at": run.approved_at.isoformat(),
                "committed_changes_count": len(committed_details),
                "details": committed_details,
                "message": f"Optimization plan '{optimization_id}' approved and {len(committed_details)} change(s) committed successfully."
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transaction failed during plan execution: {str(exc)}"
            )

    def reject_optimization_plan(
        self,
        db: Session,
        optimization_id: str,
        current_user: User
    ) -> Dict[str, Any]:
        run = db.query(OptimizationRun).filter(OptimizationRun.optimization_id == optimization_id).first()
        if not run:
            raise HTTPException(status_code=404, detail=f"Optimization run '{optimization_id}' not found.")

        run.approval_status = "REJECTED"
        run.approved_by = current_user.username or current_user.email
        run.approved_at = datetime.utcnow()
        db.commit()

        log_audit(
            db=db,
            user=current_user,
            action="REJECT_OPTIMIZATION_PLAN",
            entity_type="OPTIMIZATION_RUN",
            entity_id=optimization_id,
            metadata={"status": "REJECTED"}
        )

        return {
            "optimization_id": optimization_id,
            "approval_status": "REJECTED",
            "message": f"Optimization plan '{optimization_id}' rejected by staff."
        }

    def reoptimize_plan(
        self,
        db: Session,
        optimization_id: str,
        current_user: User
    ) -> Dict[str, Any]:
        run = db.query(OptimizationRun).filter(OptimizationRun.optimization_id == optimization_id).first()
        if not run:
            raise HTTPException(status_code=404, detail=f"Optimization run '{optimization_id}' not found.")

        opt_type = run.optimization_type
        dept = run.department or "Cardiology"
        t_date = run.target_date

        if opt_type == "APPOINTMENT_SCHEDULING":
            return self.run_appointment_optimization(db, department=dept, target_date=t_date, current_user=current_user)
        elif opt_type == "DOCTOR_SCHEDULING":
            return self.run_doctor_scheduling_optimization(db, department=dept, target_date=t_date, current_user=current_user)
        elif opt_type == "BED_ALLOCATION":
            return self.run_bed_allocation_optimization(db, department=dept, target_date=t_date, current_user=current_user)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown optimization type '{opt_type}'.")

    # -------------------------------------------------------------
    # 6. Global Metrics & Benchmark
    # -------------------------------------------------------------
    def get_metrics_summary(self, db: Session) -> Dict[str, Any]:
        runs = db.query(OptimizationRun).all()
        total_runs = len(runs)
        successful_plans = sum(1 for r in runs if r.solver_status in ["OPTIMAL", "FEASIBLE"])
        pending_approvals = sum(1 for r in runs if r.approval_status == "PENDING_APPROVAL")
        total_allocations = sum(r.allocated_count for r in runs)
        total_unallocated = sum(r.unallocated_count for r in runs)
        total_reqs = total_allocations + total_unallocated
        allocation_rate = round((total_allocations / max(1, total_reqs)) * 100, 2)

        # Load benchmark report
        bench_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "artifacts",
            "optimization_benchmark.json"
        )
        bench_data = {}
        if os.path.exists(bench_path):
            with open(bench_path, "r", encoding="utf-8") as f:
                bench_data = json.load(f)
        else:
            bench_data = run_benchmark_comparison(save_report=True)

        return {
            "total_runs": total_runs,
            "successful_plans": successful_plans,
            "pending_approvals": pending_approvals,
            "total_allocations": total_allocations,
            "total_unallocated": total_unallocated,
            "overall_allocation_rate": allocation_rate,
            "baseline_comparison": bench_data
        }

    def approve_optimization_run(self, db: Session, run_id: str, approved_by: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        user = db.query(User).filter(User.username == approved_by).first() if approved_by else None
        if not user:
            user = User(id=1, username=approved_by or "admin", email=f"{approved_by or 'admin'}@hospital.org", role="ADMIN")
        return self.approve_optimization_plan(db, run_id, user)

    def reject_optimization_run(self, db: Session, run_id: str, rejected_by: Optional[str] = None, reason: Optional[str] = None) -> Dict[str, Any]:
        user = db.query(User).filter(User.username == rejected_by).first() if rejected_by else None
        if not user:
            user = User(id=1, username=rejected_by or "admin", email=f"{rejected_by or 'admin'}@hospital.org", role="ADMIN")
        return self.reject_optimization_plan(db, run_id, user)

    def reoptimize_run(self, db: Session, run_id: str, adjusted_parameters: Optional[Dict[str, Any]] = None, current_user: Optional[User] = None) -> Dict[str, Any]:
        if not current_user:
            current_user = User(id=1, username="admin", email="admin@hospital.org", role="ADMIN")
        return self.reoptimize_plan(db, run_id, current_user)

    def list_optimization_runs(self, db: Session, run_type: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        query = db.query(OptimizationRun).order_by(OptimizationRun.created_at.desc())
        if run_type and isinstance(run_type, str) and run_type.strip() and run_type != "None":
            query = query.filter(OptimizationRun.optimization_type == run_type)
        if status and isinstance(status, str) and status.strip() and status != "None":
            query = query.filter(OptimizationRun.approval_status == status)
        try:
            lim = int(limit)
        except Exception:
            lim = 50
        runs = query.limit(lim).all()
        return [self._format_run_summary(r) for r in runs]

    def get_optimization_metrics(self, db: Session) -> Dict[str, Any]:
        return self.get_metrics_summary(db)

    def _format_run_summary(self, run: OptimizationRun) -> Dict[str, Any]:
        return {
            "optimization_id": run.optimization_id,
            "optimization_type": run.optimization_type,
            "department": run.department,
            "target_date": run.target_date,
            "solver_status": run.solver_status,
            "objective_value": run.objective_value,
            "execution_duration_ms": run.execution_duration_ms,
            "constraint_validation": run.constraint_validation,
            "total_requests": run.total_requests,
            "allocated_count": run.allocated_count,
            "unallocated_count": run.unallocated_count,
            "approval_status": run.approval_status,
            "requires_human_approval": run.requires_human_approval,
            "approved_by": run.approved_by,
            "approved_at": run.approved_at,
            "created_at": run.created_at
        }

optimization_service = OptimizationService()
