import time
from typing import List, Dict, Any, Optional

from backend.optimization.engine.optimization_engine import BaseOptimizer, ConstraintCheckResult
from backend.optimization.engine.solver_factory import SolverFactory
from backend.optimization.beds.bed_constraints import BedConstraintValidator

class BedAllocator(BaseOptimizer):
    """
    Google OR-Tools MIP constraint-based operational bed allocation engine.
    Matches pending patient admission requests to available hospital beds,
    prioritizing acute/critical triage and respecting ward/category constraints.
    """

    def optimize(
        self,
        requests: List[Dict[str, Any]],
        beds: List[Dict[str, Any]],
        department: Optional[str] = None,
        predicted_occupancy: Optional[Dict[str, Any]] = None,
        target_date: Optional[str] = None,
        max_solve_time_seconds: float = 10.0
    ) -> Dict[str, Any]:
        start_time = time.time()

        # Filter strictly AVAILABLE beds
        available_beds = [
            b for b in beds
            if str(b.get("status", "")).upper() == "AVAILABLE" and not b.get("is_occupied", False)
        ]
        beds_map = {b["bed_id"]: b for b in beds}
        requests_map = {r["request_id"]: r for r in requests}

        if not requests:
            return {
                "solver_status": "OPTIMAL",
                "objective_value": 0.0,
                "execution_duration_ms": int((time.time() - start_time) * 1000),
                "recommended_allocations": [],
                "unallocated_requests": [],
                "constraint_validation": "PASSED"
            }

        if not available_beds:
            unallocated = [
                {
                    "request_id": r["request_id"],
                    "patient_id": r.get("patient_id"),
                    "patient_name": r.get("patient_name"),
                    "department": r.get("department", department),
                    "ward": r.get("required_ward"),
                    "allocation_status": "UNALLOCATED",
                    "reason": "Bed capacity exhausted: Zero beds currently marked AVAILABLE."
                }
                for r in requests
            ]
            return {
                "solver_status": "INFEASIBLE",
                "objective_value": 0.0,
                "execution_duration_ms": int((time.time() - start_time) * 1000),
                "recommended_allocations": [],
                "unallocated_requests": unallocated,
                "constraint_validation": "PASSED"
            }

        # Build OR-Tools MIP model
        solver = SolverFactory.create_mip_solver(max_time_seconds=max_solve_time_seconds)

        # Decision Variables:
        # z[r_idx, b_idx] in {0, 1}: True if request r assigned to available bed b
        # u[r_idx] in {0, 1}: True if request r unallocated
        z = {}
        u = {}

        for r_idx, req in enumerate(requests):
            u[r_idx] = solver.BoolVar(f"u_bed_r{r_idx}")
            req_ward = (req.get("required_ward") or "General").lower()

            for b_idx, bed in enumerate(available_beds):
                bed_ward = (bed.get("ward") or "General").lower()

                # Critical constraint: ICU admissions must go to ICU beds only
                if req_ward == "icu" and bed_ward != "icu":
                    continue
                # Conversely, non-ICU patients should not occupy scarce ICU beds unless urgent
                if req_ward != "icu" and bed_ward == "icu":
                    continue

                z[r_idx, b_idx] = solver.BoolVar(f"z_r{r_idx}_b{b_idx}")

        # Constraint 1: Each request is allocated to at most 1 bed, or marked unallocated
        for r_idx in range(len(requests)):
            possible_beds = [
                z[r_idx, b_idx]
                for b_idx in range(len(available_beds))
                if (r_idx, b_idx) in z
            ]
            solver.Add(sum(possible_beds) + u[r_idx] == 1)

        # Constraint 2: Each available bed can be assigned to at most 1 patient
        for b_idx in range(len(available_beds)):
            assigned_requests = [
                z[r_idx, b_idx]
                for r_idx in range(len(requests))
                if (r_idx, b_idx) in z
            ]
            if assigned_requests:
                solver.Add(sum(assigned_requests) <= 1)

        # Objective Function:
        # Prioritize high urgency requests (critical: 10,000, urgent: 5,000, standard: 2,000)
        # Penalize ward mismatch if not exact (e.g. general assigned to private or vice versa)
        objective_terms = []

        for r_idx, req in enumerate(requests):
            urgency = (req.get("urgency") or "standard").lower()
            unalloc_weight = 10000 if urgency == "critical" else (5000 if urgency == "urgent" else 2000)
            objective_terms.append(unalloc_weight * u[r_idx])

            req_ward = (req.get("required_ward") or "General").lower()
            req_dept = (req.get("department") or department or "").lower()

            for b_idx, bed in enumerate(available_beds):
                if (r_idx, b_idx) in z:
                    bed_ward = (bed.get("ward") or "General").lower()
                    bed_dept = (bed.get("department") or "").lower()

                    mismatch_cost = 0
                    if req_ward != bed_ward:
                        mismatch_cost += 100  # Slight penalty for alternate ward
                    if req_dept and bed_dept and req_dept != bed_dept:
                        mismatch_cost += 50   # Slight penalty for differing department ward

                    objective_terms.append(mismatch_cost * z[r_idx, b_idx])

        solver.Minimize(sum(objective_terms))

        solver_status_code = solver.Solve()
        status_str = SolverFactory.parse_solver_status(solver_status_code)
        elapsed_ms = int((time.time() - start_time) * 1000)

        recommended_allocations = []
        unallocated_requests = []

        if status_str in ["OPTIMAL", "FEASIBLE"]:
            for r_idx, req in enumerate(requests):
                if u[r_idx].solution_value() > 0.5:
                    unallocated_requests.append({
                        "request_id": req["request_id"],
                        "patient_id": req.get("patient_id"),
                        "patient_name": req.get("patient_name"),
                        "department": req.get("department", department),
                        "ward": req.get("required_ward"),
                        "allocation_status": "UNALLOCATED",
                        "reason": f"No available beds matching ward '{req.get('required_ward', 'General')}'."
                    })
                else:
                    assigned_bed = None
                    for b_idx, bed in enumerate(available_beds):
                        if (r_idx, b_idx) in z and z[r_idx, b_idx].solution_value() > 0.5:
                            assigned_bed = bed
                            break

                    if assigned_bed:
                        recommended_allocations.append({
                            "request_id": req["request_id"],
                            "patient_id": req.get("patient_id"),
                            "patient_name": req.get("patient_name"),
                            "bed_id": assigned_bed["bed_id"],
                            "ward": assigned_bed.get("ward"),
                            "department": assigned_bed.get("department"),
                            "allocation_status": "ALLOCATED",
                            "reason": f"Allocated bed {assigned_bed['bed_id']} ({assigned_bed['ward']} Ward, Room {assigned_bed.get('room_number')})."
                        })
        else:
            for req in requests:
                unallocated_requests.append({
                    "request_id": req["request_id"],
                    "patient_id": req.get("patient_id"),
                    "patient_name": req.get("patient_name"),
                    "department": req.get("department", department),
                    "ward": req.get("required_ward"),
                    "allocation_status": "UNALLOCATED",
                    "reason": f"Solver status '{status_str}': Could not determine feasible bed assignment."
                })

        validation_res = self.validate_constraints(
            recommended_allocations,
            beds_map=beds_map,
            requests_map=requests_map
        )

        return {
            "solver_status": status_str,
            "objective_value": float(solver.Objective().Value()) if status_str in ["OPTIMAL", "FEASIBLE"] else 0.0,
            "execution_duration_ms": elapsed_ms,
            "recommended_allocations": recommended_allocations,
            "unallocated_requests": unallocated_requests,
            "constraint_validation": validation_res.status,
            "validation_details": {
                "violations": validation_res.violations,
                "warnings": validation_res.warnings
            }
        }

    def validate_constraints(self, allocations: List[Dict[str, Any]], **kwargs) -> ConstraintCheckResult:
        return BedConstraintValidator.validate(
            allocations=allocations,
            beds_map=kwargs.get("beds_map", {}),
            requests_map=kwargs.get("requests_map", {})
        )
