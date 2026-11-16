import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database.database import get_db
from backend.database.models import User
from backend.auth.dependencies import get_current_user, require_role
from backend.optimization.services.optimization_service import optimization_service
from backend.optimization.schemas.optimization import (
    AppointmentOptimizationRunRequest,
    DoctorSchedulingRunRequest,
    BedAllocationRunRequest,
    OptimizationRunResponse,
    OptimizationApproveResponse,
    OptimizationMetricsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/optimization", tags=["Intelligent Hospital Resource Optimization"])

class ApprovalRequestPayload(BaseModel):
    notes: Optional[str] = None

class RejectionRequestPayload(BaseModel):
    reason: Optional[str] = "Rejected by hospital administrator"

class ReoptimizationRequestPayload(BaseModel):
    adjusted_parameters: Optional[Dict[str, Any]] = None

# ------------------------------------------------------------------
# 1. Appointment Scheduling Optimization
# ------------------------------------------------------------------
@router.post("/appointments/run", summary="Run OR-Tools Appointment Scheduling Optimization")
def run_appointment_optimization(
    payload: AppointmentOptimizationRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes Google OR-Tools Mixed Integer Linear Programming (MIP) to schedule appointments.
    Minimizes patient wait times, doctor workload imbalance, and prevents double bookings.
    Generates a proposed plan with status PENDING_APPROVAL.
    """
    try:
        custom_reqs = [r.model_dump() for r in payload.custom_requests] if payload.custom_requests else None
        res = optimization_service.run_appointment_optimization(
            db=db,
            department=payload.department,
            target_date=payload.target_date,
            custom_requests=custom_reqs,
            max_solve_time_seconds=float(payload.max_solve_time_seconds or 10.0),
            current_user=current_user
        )
        return res
    except Exception as exc:
        logger.error(f"Appointment optimization failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Appointment optimization failed: {str(exc)}"
        )

# ------------------------------------------------------------------
# 2. Doctor Shift Scheduling Optimization
# ------------------------------------------------------------------
@router.post("/doctors/run", summary="Run OR-Tools Doctor Shift Scheduling Optimization")
def run_doctor_scheduling(
    payload: DoctorSchedulingRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes Google OR-Tools MIP to allocate doctor shifts based on Phase 6 ML demand forecasts.
    Respects maximum shift limits, non-overlapping shifts, and department coverage.
    """
    try:
        res = optimization_service.run_doctor_scheduling_optimization(
            db=db,
            department=payload.department,
            target_date=payload.target_date,
            max_solve_time_seconds=float(payload.max_solve_time_seconds or 10.0),
            current_user=current_user
        )
        return res
    except Exception as exc:
        logger.error(f"Doctor scheduling optimization failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Doctor scheduling optimization failed: {str(exc)}"
        )

# ------------------------------------------------------------------
# 3. Bed Allocation Optimization
# ------------------------------------------------------------------
@router.post("/beds/run", summary="Run OR-Tools Bed Allocation Optimization")
def run_bed_allocation(
    payload: BedAllocationRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes Google OR-Tools MIP to allocate available beds to pending admission requests.
    Prioritizes critical/urgent triage tiers, enforces ward compatibility, and factors in
    Phase 6 ML predicted occupancy.
    """
    try:
        custom_reqs = [r.model_dump() for r in payload.custom_requests] if payload.custom_requests else None
        res = optimization_service.run_bed_allocation_optimization(
            db=db,
            department=payload.department,
            target_date=payload.target_date,
            custom_requests=custom_reqs,
            max_solve_time_seconds=float(payload.max_solve_time_seconds or 10.0),
            current_user=current_user
        )
        return res
    except Exception as exc:
        logger.error(f"Bed allocation optimization failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bed allocation optimization failed: {str(exc)}"
        )

# ------------------------------------------------------------------
# 4. Results & Management
# ------------------------------------------------------------------
@router.get("/results", summary="List Optimization Runs")
def list_optimization_runs(
    optimization_type: Optional[str] = None,
    approval_status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves chronological history of optimization runs and their approval states."""
    opt_type_str = str(optimization_type) if isinstance(optimization_type, str) else None
    status_str = str(approval_status) if isinstance(approval_status, str) else None
    try:
        limit_val = int(limit)
    except Exception:
        limit_val = 50

    return optimization_service.list_optimization_runs(
        db=db,
        run_type=opt_type_str,
        status=status_str,
        limit=limit_val
    )

@router.get("/results/{optimization_id}", summary="Get Detailed Optimization Run")
def get_optimization_run_detail(
    optimization_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves full details of an optimization run including all allocations, metrics, and snapshots."""
    return optimization_service.get_optimization_run(db=db, optimization_id=optimization_id)

@router.post("/results/{optimization_id}/approve", summary="Human Approval: Commit Allocations to Operational DB")
def approve_optimization_run(
    optimization_id: str,
    payload: Optional[ApprovalRequestPayload] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Human-in-the-loop approval:
    Verifies that the proposed plan has not become stale (checks for resource conflicts).
    If valid, commits all recommended allocations to SQLite in an atomic transaction:
    - Appointments: creates or updates booked appointments
    - Doctor Shifts: assigns working shifts
    - Beds: assigns patient to bed and marks occupied
    """
    notes = payload.notes if payload else None
    approver_username = current_user.username if current_user else "AdminStaff"
    return optimization_service.approve_optimization_run(
        db=db,
        run_id=optimization_id,
        approved_by=approver_username,
        notes=notes
    )

@router.post("/results/{optimization_id}/reject", summary="Human Rejection: Reject Proposed Plan")
def reject_optimization_run(
    optimization_id: str,
    payload: Optional[RejectionRequestPayload] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marks an optimization run as REJECTED without modifying operational database tables."""
    reason = payload.reason if payload else "Rejected by user"
    rejector_username = current_user.username if current_user else "AdminStaff"
    return optimization_service.reject_optimization_run(
        db=db,
        run_id=optimization_id,
        rejected_by=rejector_username,
        reason=reason
    )

@router.post("/results/{optimization_id}/reoptimize", summary="Re-run Optimization with Adjusted Parameters")
def reoptimize_run(
    optimization_id: str,
    payload: Optional[ReoptimizationRequestPayload] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates a new optimization run using refreshed database state or modified parameters."""
    adj = payload.adjusted_parameters if payload else None
    return optimization_service.reoptimize_run(
        db=db,
        run_id=optimization_id,
        adjusted_parameters=adj,
        current_user=current_user
    )

@router.get("/metrics", summary="Get Optimization Performance KPIs & Baseline Comparison")
def get_optimization_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns global optimization KPIs (total runs, allocation success rate, solver solve time)
    along with empirical baseline comparisons: OR-Tools MIP vs FIFO Greedy heuristic.
    """
    return optimization_service.get_optimization_metrics(db=db)
