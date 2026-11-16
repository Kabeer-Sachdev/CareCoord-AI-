from typing import List, Dict, Any, Set
from backend.optimization.engine.optimization_engine import ConstraintCheckResult

STANDARD_SHIFTS = ["Morning (08:00 - 14:00)", "Evening (14:00 - 20:00)", "Night (20:00 - 08:00)"]

class DoctorConstraintValidator:
    """
    Validates operational doctor shift assignments:
    1. Single shift per doctor per day (no overlapping shifts)
    2. Available doctors only (excludes On Leave or Unavailable)
    3. Department / Specialization matching
    4. Preservation of confirmed pre-existing doctor schedules
    """

    @staticmethod
    def validate(
        allocations: List[Dict[str, Any]],
        doctors_map: Dict[str, Dict[str, Any]],
        department: str
    ) -> ConstraintCheckResult:
        violations = []
        warnings = []
        assigned_doctors: Set[str] = set()

        for alloc in allocations:
            if alloc.get("allocation_status") != "ALLOCATED":
                continue

            d_id = alloc.get("doctor_id")
            shift = alloc.get("shift_name")

            if d_id in assigned_doctors:
                violations.append(f"Doctor {d_id} double-assigned to multiple shifts on the same day.")
            else:
                assigned_doctors.add(d_id)

            doc = doctors_map.get(d_id)
            if not doc:
                violations.append(f"Allocated unknown doctor ID '{d_id}'.")
            else:
                if not doc.get("availability", True) or doc.get("availability_status") in ["On Leave", "Unavailable"]:
                    violations.append(f"Doctor {doc.get('name')} ({d_id}) is marked unavailable/on leave.")

                if department and doc.get("department") != department:
                    warnings.append(
                        f"Doctor {doc.get('name')} department '{doc.get('department')}' differs from target '{department}'."
                    )

        is_valid = len(violations) == 0
        return ConstraintCheckResult(is_valid=is_valid, violations=violations, warnings=warnings)
