from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class AppointmentRequestItem(BaseModel):
    request_id: str = Field(..., example="REQ-APT-001")
    patient_id: str = Field(..., example="P001")
    patient_name: str = Field(..., example="Rahul Sharma")
    department: str = Field(..., example="Cardiology")
    priority: str = Field("normal", example="normal")  # normal, urgent, emergency
    preferred_time_slot: Optional[str] = Field(None, example="10:00 AM")

class BedAdmissionRequestItem(BaseModel):
    request_id: str = Field(..., example="REQ-BED-001")
    patient_id: str = Field(..., example="P002")
    patient_name: str = Field(..., example="Priya Patel")
    department: str = Field(..., example="Cardiology")
    required_ward: str = Field("General", example="General")  # ICU, Emergency, General, Private
    urgency: str = Field("urgent", example="urgent")  # critical, urgent, standard

class AppointmentOptimizationRunRequest(BaseModel):
    department: str = Field("Cardiology", example="Cardiology")
    target_date: Optional[str] = Field(None, example="2026-11-20")
    custom_requests: Optional[List[AppointmentRequestItem]] = None
    max_solve_time_seconds: Optional[int] = Field(10, example=10)

class DoctorSchedulingRunRequest(BaseModel):
    department: str = Field("Cardiology", example="Cardiology")
    target_date: Optional[str] = Field(None, example="2026-11-20")
    max_solve_time_seconds: Optional[int] = Field(10, example=10)

class BedAllocationRunRequest(BaseModel):
    department: Optional[str] = Field(None, example="Cardiology")
    target_date: Optional[str] = Field(None, example="2026-11-20")
    custom_requests: Optional[List[BedAdmissionRequestItem]] = None
    max_solve_time_seconds: Optional[int] = Field(10, example=10)

class AllocationResultItem(BaseModel):
    request_id: str
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    bed_id: Optional[str] = None
    ward: Optional[str] = None
    department: Optional[str] = None
    allocated_time_slot: Optional[str] = None
    shift_name: Optional[str] = None
    allocation_status: str  # ALLOCATED, UNALLOCATED
    reason: Optional[str] = None

class OptimizationRunResponse(BaseModel):
    optimization_id: str
    optimization_type: str
    department: Optional[str] = None
    target_date: str
    solver_status: str  # OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN, FAILED
    objective_value: float
    execution_duration_ms: float
    constraint_validation: str  # PASSED, WARNING, FAILED
    total_requests: int
    allocated_count: int
    unallocated_count: int
    approval_status: str  # PENDING_APPROVAL, APPROVED, REJECTED, COMMITTED
    requires_human_approval: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    recommended_allocations: List[AllocationResultItem] = []
    unallocated_requests: List[AllocationResultItem] = []
    ml_forecast_snapshot: Dict[str, Any] = {}
    metrics_snapshot: Dict[str, Any] = {}
    created_at: datetime

class OptimizationApproveResponse(BaseModel):
    optimization_id: str
    approval_status: str
    approved_by: str
    approved_at: str
    committed_changes_count: int
    details: List[str] = []
    message: str

class OptimizationMetricsResponse(BaseModel):
    total_runs: int
    successful_plans: int
    pending_approvals: int
    total_allocations: int
    total_unallocated: int
    overall_allocation_rate: float
    baseline_comparison: Dict[str, Any] = {}
