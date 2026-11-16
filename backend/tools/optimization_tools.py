from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.database.database import SessionLocal
from backend.optimization.services.optimization_service import optimization_service

def optimize_appointment_schedule(
    department: str = "Cardiology",
    target_date: Optional[str] = None,
    custom_requests: Optional[List[Dict[str, Any]]] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Controlled Optimization Tool:
    Optimizes patient appointment scheduling across available doctors and time slots using Google OR-Tools MIP.
    Minimizes patient waiting time and doctor workload imbalance while avoiding conflicts.
    Requires human approval before committing changes.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    try:
        return optimization_service.run_appointment_optimization(
            db=db,
            department=department,
            target_date=target_date,
            custom_requests=custom_requests
        )
    finally:
        if should_close:
            db.close()

def optimize_doctor_schedule(
    department: str = "Cardiology",
    target_date: Optional[str] = None,
    shifts: Optional[List[str]] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Controlled Optimization Tool:
    Distributes shifts across available doctors using Google OR-Tools MIP, incorporating
    Phase 6 ML predicted patient demand and emergency surges.
    Requires human approval before committing changes.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    try:
        return optimization_service.run_doctor_scheduling_optimization(
            db=db,
            department=department,
            target_date=target_date,
            shifts=shifts
        )
    finally:
        if should_close:
            db.close()

def recommend_bed_allocation(
    department: Optional[str] = "Cardiology",
    target_date: Optional[str] = None,
    custom_requests: Optional[List[Dict[str, Any]]] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Controlled Optimization Tool:
    Recommends optimal bed assignments for admission requests using Google OR-Tools MIP,
    prioritizing urgency tiers (critical/urgent/standard) and matching ward constraints,
    incorporating Phase 6 predicted bed occupancy.
    Requires human approval before committing changes.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    try:
        return optimization_service.run_bed_allocation_optimization(
            db=db,
            department=department,
            target_date=target_date,
            custom_requests=custom_requests
        )
    finally:
        if should_close:
            db.close()

def get_optimization_results(
    optimization_id: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Retrieves the optimization run details, solver status, constraint validation,
    and recommended allocations.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    try:
        return optimization_service.get_optimization_run(db=db, optimization_id=optimization_id)
    finally:
        if should_close:
            db.close()

def validate_allocation_plan(
    optimization_id: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Checks if an optimization plan has become stale or has conflicts against the current database state.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    try:
        run = optimization_service.get_optimization_run(db=db, optimization_id=optimization_id)
        return {
            "optimization_id": optimization_id,
            "status": run.get("approval_status"),
            "is_valid": run.get("solver_status") in ["OPTIMAL", "FEASIBLE"],
            "constraint_validation": run.get("constraint_validation"),
            "allocations_count": len(run.get("allocations", []))
        }
    finally:
        if should_close:
            db.close()

def get_optimization_metrics(
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Returns global optimization performance metrics and baseline comparison data (OR-Tools vs FIFO Greedy).
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    try:
        return optimization_service.get_optimization_metrics(db=db)
    finally:
        if should_close:
            db.close()
