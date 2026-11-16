import time
import math
from typing import List, Dict, Any, Optional

from backend.optimization.engine.optimization_engine import BaseOptimizer, ConstraintCheckResult
from backend.optimization.engine.solver_factory import SolverFactory
from backend.optimization.doctor.doctor_constraints import STANDARD_SHIFTS, DoctorConstraintValidator

class DoctorScheduler(BaseOptimizer):
    """
    Google OR-Tools MIP constraint-based doctor shift scheduler.
    Consumes Phase 6 predicted patient arrivals & emergency demand to calculate optimal
    doctor shift assignments while respecting non-overlap rules and availability constraints.
    """

    def optimize(
        self,
        doctors: List[Dict[str, Any]],
        department: str,
        target_date: str,
        predicted_demand: Optional[Dict[str, Any]] = None,
        shifts: Optional[List[str]] = None,
        max_solve_time_seconds: float = 10.0
    ) -> Dict[str, Any]:
        start_time = time.time()
        active_shifts = shifts if shifts else STANDARD_SHIFTS

        # Filter doctors belonging to the requested department
        dept_doctors = [
            d for d in doctors
            if (not department or d.get("department") == department)
        ]
        doctors_map = {d["doctor_id"]: d for d in dept_doctors}

        # Available doctors only
        available_doctors = [
            d for d in dept_doctors
            if d.get("availability", True) and d.get("availability_status") not in ["On Leave", "Unavailable"]
        ]

        # Calculate required shift staffing using Phase 6 predicted demand
        pred_arrivals = 20
        pred_emergencies = 4
        if predicted_demand:
            pred_arrivals = predicted_demand.get("predicted_arrivals", 20)
            pred_emergencies = predicted_demand.get("predicted_emergencies", 4)

        total_demand = pred_arrivals + pred_emergencies
        # Staffing distribution: Morning (50%), Evening (35%), Night (15%)
        # Standard: 1 doctor handles approx 8-10 patient visits per 6-hour shift
        pat_per_doc = 10
        req_morning = max(1, math.ceil((total_demand * 0.50) / pat_per_doc))
        req_evening = max(1, math.ceil((total_demand * 0.35) / pat_per_doc))
        req_night = max(1, math.ceil((total_demand * 0.15) / pat_per_doc))
        required_staffing = [req_morning, req_evening, req_night]

        if not available_doctors:
            return {
                "solver_status": "INFEASIBLE",
                "objective_value": 0.0,
                "execution_duration_ms": int((time.time() - start_time) * 1000),
                "recommended_allocations": [],
                "unallocated_requests": [
                    {
                        "request_id": f"SHIFT-DEFICIT-{s_name[:3].upper()}",
                        "department": department,
                        "shift_name": s_name,
                        "allocation_status": "UNALLOCATED",
                        "reason": f"Zero available doctors in department '{department}'."
                    }
                    for s_name in STANDARD_SHIFTS
                ],
                "constraint_validation": "PASSED",
                "staffing_demand": {
                    "total_patient_demand": total_demand,
                    "required_shifts": dict(zip(STANDARD_SHIFTS, required_staffing)),
                    "available_doctors": 0
                }
            }

        # Build OR-Tools MIP Model
        solver = SolverFactory.create_mip_solver(max_time_seconds=max_solve_time_seconds)

        # Decision Variables:
        # y[d_idx, s_idx] in {0, 1}: Doctor d_idx assigned to shift s_idx
        y = {}
        for d_idx, doc in enumerate(available_doctors):
            for s_idx in range(len(STANDARD_SHIFTS)):
                y[d_idx, s_idx] = solver.BoolVar(f"y_d{d_idx}_s{s_idx}")

        # Constraint 1: A doctor can work at most 1 shift per day (non-overlapping shifts)
        for d_idx in range(len(available_doctors)):
            solver.Add(sum(y[d_idx, s_idx] for s_idx in range(len(STANDARD_SHIFTS))) <= 1)

        # Shift coverage & demand deficit variables
        deficit = []
        surplus = []

        for s_idx, req_count in enumerate(required_staffing):
            coverage_s = sum(y[d_idx, s_idx] for d_idx in range(len(available_doctors)))

            def_var = solver.IntVar(0, len(available_doctors) + 10, f"deficit_s{s_idx}")
            sur_var = solver.IntVar(0, len(available_doctors) + 10, f"surplus_s{s_idx}")

            solver.Add(coverage_s + def_var - sur_var == req_count)

            deficit.append(def_var)
            surplus.append(sur_var)

        # Objective Function:
        # Heavily penalize staffing deficits below forecasted demand (penalty 500)
        # Lightly penalize overstaffing surplus (penalty 50)
        solver.Minimize(
            sum(500 * deficit[s] + 50 * surplus[s] for s in range(len(STANDARD_SHIFTS)))
        )

        solver_status_code = solver.Solve()
        status_str = SolverFactory.parse_solver_status(solver_status_code)
        elapsed_ms = int((time.time() - start_time) * 1000)

        recommended_allocations = []
        unallocated_shifts = []

        if status_str in ["OPTIMAL", "FEASIBLE"]:
            for d_idx, doc in enumerate(available_doctors):
                assigned_shift = None
                for s_idx, s_name in enumerate(STANDARD_SHIFTS):
                    if y[d_idx, s_idx].solution_value() > 0.5:
                        assigned_shift = s_name
                        break

                if assigned_shift:
                    recommended_allocations.append({
                        "request_id": f"SCHED-{doc['doctor_id']}-{target_date}",
                        "doctor_id": doc["doctor_id"],
                        "doctor_name": doc["name"],
                        "department": doc.get("department", department),
                        "shift_name": assigned_shift,
                        "allocation_status": "ALLOCATED",
                        "reason": f"Assigned to {assigned_shift} based on Phase 6 predicted workload ({total_demand} patients)."
                    })

            # Check if any shift had a staffing deficit
            for s_idx, s_name in enumerate(STANDARD_SHIFTS):
                def_count = int(round(deficit[s_idx].solution_value()))
                if def_count > 0:
                    unallocated_shifts.append({
                        "request_id": f"DEFICIT-{s_name[:3].upper()}-{target_date}",
                        "department": department,
                        "shift_name": s_name,
                        "allocation_status": "UNALLOCATED",
                        "reason": f"Understaffing: {def_count} additional doctor(s) required to meet predicted demand of {total_demand} patients."
                    })
        else:
            for s_name in STANDARD_SHIFTS:
                unallocated_shifts.append({
                    "request_id": f"FAILED-SHIFT-{s_name[:3].upper()}",
                    "department": department,
                    "shift_name": s_name,
                    "allocation_status": "UNALLOCATED",
                    "reason": f"Solver status '{status_str}': Could not find valid feasible shift schedule."
                })

        validation_res = self.validate_constraints(
            recommended_allocations,
            doctors_map=doctors_map,
            department=department
        )

        return {
            "solver_status": status_str,
            "objective_value": float(solver.Objective().Value()) if status_str in ["OPTIMAL", "FEASIBLE"] else 0.0,
            "execution_duration_ms": elapsed_ms,
            "recommended_allocations": recommended_allocations,
            "unallocated_requests": unallocated_shifts,
            "constraint_validation": validation_res.status,
            "staffing_demand": {
                "total_patient_demand": total_demand,
                "required_shifts": dict(zip(STANDARD_SHIFTS, required_staffing)),
                "scheduled_doctors": len(recommended_allocations),
                "total_available_doctors": len(available_doctors)
            },
            "validation_details": {
                "violations": validation_res.violations,
                "warnings": validation_res.warnings
            }
        }

    def validate_constraints(self, allocations: List[Dict[str, Any]], **kwargs) -> ConstraintCheckResult:
        return DoctorConstraintValidator.validate(
            allocations=allocations,
            doctors_map=kwargs.get("doctors_map", {}),
            department=kwargs.get("department", "")
        )
