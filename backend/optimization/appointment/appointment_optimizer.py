import time
from typing import List, Dict, Any, Optional

from backend.optimization.engine.optimization_engine import BaseOptimizer, ConstraintCheckResult
from backend.optimization.engine.solver_factory import SolverFactory
from backend.optimization.appointment.appointment_constraints import (
    STANDARD_TIME_SLOTS,
    AppointmentConstraintValidator
)

class AppointmentOptimizer(BaseOptimizer):
    """
    Google OR-Tools MIP constraint-based appointment scheduling optimizer.
    Finds globally optimal or high-quality feasible assignments of patient requests
    to eligible doctors and time slots while minimizing patient waiting time and doctor workload imbalance.
    """

    def optimize(
        self,
        requests: List[Dict[str, Any]],
        doctors: List[Dict[str, Any]],
        existing_appointments: Optional[List[Dict[str, Any]]] = None,
        department: str = "Cardiology",
        target_date: str = "2026-11-20",
        max_solve_time_seconds: float = 10.0
    ) -> Dict[str, Any]:
        start_time = time.time()
        if existing_appointments is None:
            existing_appointments = []

        # Filter eligible doctors
        eligible_doctors = [
            d for d in doctors
            if (not department or d.get("department") == department)
            and d.get("availability", True)
            and d.get("availability_status") not in ["On Leave", "Unavailable"]
        ]
        doctors_map = {d["doctor_id"]: d for d in doctors}

        # Build locked slot map from existing appointments
        locked_doctor_slots = {
            (apt.get("doctor_id"), apt.get("time_slot"))
            for apt in existing_appointments
            if apt.get("date") == target_date
        }
        locked_patient_slots = {
            (apt.get("patient_id"), apt.get("time_slot"))
            for apt in existing_appointments
            if apt.get("date") == target_date
        }

        # If no requests or no doctors available
        if not requests:
            return {
                "solver_status": "OPTIMAL",
                "objective_value": 0.0,
                "execution_duration_ms": int((time.time() - start_time) * 1000),
                "recommended_allocations": [],
                "unallocated_requests": [],
                "constraint_validation": "PASSED"
            }

        if not eligible_doctors:
            unallocated = [
                {
                    "request_id": r["request_id"],
                    "patient_id": r.get("patient_id"),
                    "patient_name": r.get("patient_name"),
                    "department": department,
                    "allocation_status": "UNALLOCATED",
                    "reason": f"No available doctors found in department '{department}'."
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

        # Initialize OR-Tools MIP solver
        solver = SolverFactory.create_mip_solver(max_time_seconds=max_solve_time_seconds)

        # Decision Variables:
        # x[r_idx, d_idx, s_idx] in {0, 1}: True if request r assigned to doctor d at slot s
        # u[r_idx] in {0, 1}: True if request r is unallocated
        x = {}
        u = {}

        for r_idx, req in enumerate(requests):
            u[r_idx] = solver.BoolVar(f"u_r{r_idx}")
            p_id = req.get("patient_id")

            for d_idx, doc in enumerate(eligible_doctors):
                d_id = doc["doctor_id"]

                for s_idx, slot in enumerate(STANDARD_TIME_SLOTS):
                    # Check if slot is locked by existing DB records
                    if (d_id, slot) in locked_doctor_slots or (p_id, slot) in locked_patient_slots:
                        continue  # Cannot assign into an already booked slot

                    x[r_idx, d_idx, s_idx] = solver.BoolVar(f"x_r{r_idx}_d{d_idx}_s{s_idx}")

        # Constraint 1: Every request is assigned to at most 1 (doctor, slot), or unallocated
        for r_idx in range(len(requests)):
            possible_vars = [
                x[r_idx, d_idx, s_idx]
                for d_idx in range(len(eligible_doctors))
                for s_idx in range(len(STANDARD_TIME_SLOTS))
                if (r_idx, d_idx, s_idx) in x
            ]
            solver.Add(sum(possible_vars) + u[r_idx] == 1)

        # Constraint 2: No doctor has overlapping appointments in the same slot
        for d_idx in range(len(eligible_doctors)):
            for s_idx in range(len(STANDARD_TIME_SLOTS)):
                assigned_to_slot = [
                    x[r_idx, d_idx, s_idx]
                    for r_idx in range(len(requests))
                    if (r_idx, d_idx, s_idx) in x
                ]
                if assigned_to_slot:
                    solver.Add(sum(assigned_to_slot) <= 1)

        # Constraint 3: No patient has double-booked appointments in the same slot
        patient_requests_map: Dict[str, List[int]] = {}
        for r_idx, req in enumerate(requests):
            p_id = req.get("patient_id")
            if p_id:
                patient_requests_map.setdefault(p_id, []).append(r_idx)

        for p_id, r_indices in patient_requests_map.items():
            if len(r_indices) > 1:
                for s_idx in range(len(STANDARD_TIME_SLOTS)):
                    patient_slot_vars = [
                        x[r_idx, d_idx, s_idx]
                        for r_idx in r_indices
                        for d_idx in range(len(eligible_doctors))
                        if (r_idx, d_idx, s_idx) in x
                    ]
                    if patient_slot_vars:
                        solver.Add(sum(patient_slot_vars) <= 1)

        # Workload balancing variables
        # w_max >= workload of doctor d
        max_workload = solver.IntVar(0, len(STANDARD_TIME_SLOTS), "max_workload")
        for d_idx in range(len(eligible_doctors)):
            doc_vars = [
                x[r_idx, d_idx, s_idx]
                for r_idx in range(len(requests))
                for s_idx in range(len(STANDARD_TIME_SLOTS))
                if (r_idx, d_idx, s_idx) in x
            ]
            solver.Add(max_workload >= sum(doc_vars))

        # Objective Function Formulation:
        # 1. Unallocated penalty (heavily penalize unmet requests; higher for urgent/emergency priority)
        # 2. Waiting time / slot order penalty (earlier slots preferred)
        # 3. Workload balance penalty (minimize max_workload)
        objective_terms = []

        for r_idx, req in enumerate(requests):
            priority = req.get("priority", "normal").lower()
            unalloc_penalty = 5000 if priority == "emergency" else (2500 if priority == "urgent" else 1000)
            objective_terms.append(unalloc_penalty * u[r_idx])

            preferred_slot = req.get("preferred_time_slot")

            for d_idx in range(len(eligible_doctors)):
                for s_idx, slot in enumerate(STANDARD_TIME_SLOTS):
                    if (r_idx, d_idx, s_idx) in x:
                        slot_cost = s_idx * 10
                        if preferred_slot and slot == preferred_slot:
                            slot_cost -= 20  # Reward matching patient's preferred slot
                        objective_terms.append(slot_cost * x[r_idx, d_idx, s_idx])

        # Workload imbalance penalty term
        objective_terms.append(50 * max_workload)

        solver.Minimize(sum(objective_terms))

        # Solve model
        solver_status_code = solver.Solve()
        status_str = SolverFactory.parse_solver_status(solver_status_code)
        elapsed_ms = int((time.time() - start_time) * 1000)

        recommended_allocations = []
        unallocated_requests = []

        if status_str in ["OPTIMAL", "FEASIBLE"]:
            for r_idx, req in enumerate(requests):
                is_unalloc = u[r_idx].solution_value() > 0.5
                if is_unalloc:
                    unallocated_requests.append({
                        "request_id": req["request_id"],
                        "patient_id": req.get("patient_id"),
                        "patient_name": req.get("patient_name"),
                        "department": department,
                        "allocation_status": "UNALLOCATED",
                        "reason": "Capacity deficit: all compatible doctor time slots are saturated."
                    })
                else:
                    assigned_doc = None
                    assigned_slot = None
                    for d_idx, doc in enumerate(eligible_doctors):
                        for s_idx, slot in enumerate(STANDARD_TIME_SLOTS):
                            if (r_idx, d_idx, s_idx) in x and x[r_idx, d_idx, s_idx].solution_value() > 0.5:
                                assigned_doc = doc
                                assigned_slot = slot
                                break
                        if assigned_doc:
                            break

                    if assigned_doc and assigned_slot:
                        recommended_allocations.append({
                            "request_id": req["request_id"],
                            "patient_id": req.get("patient_id"),
                            "patient_name": req.get("patient_name"),
                            "doctor_id": assigned_doc["doctor_id"],
                            "doctor_name": assigned_doc["name"],
                            "department": department,
                            "allocated_time_slot": assigned_slot,
                            "allocation_status": "ALLOCATED",
                            "reason": f"Optimal matching: Dr. {assigned_doc['name']} at {assigned_slot} (Min wait time & load balance)."
                        })
        else:
            for req in requests:
                unallocated_requests.append({
                    "request_id": req["request_id"],
                    "patient_id": req.get("patient_id"),
                    "patient_name": req.get("patient_name"),
                    "department": department,
                    "allocation_status": "UNALLOCATED",
                    "reason": f"Solver status '{status_str}': No mathematically valid schedule found satisfying all constraints."
                })

        validation_res = self.validate_constraints(
            recommended_allocations,
            existing_appointments=existing_appointments,
            doctors_map=doctors_map,
            department=department
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
        return AppointmentConstraintValidator.validate(
            allocations=allocations,
            existing_appointments=kwargs.get("existing_appointments", []),
            doctors_map=kwargs.get("doctors_map", {}),
            department=kwargs.get("department", "")
        )
