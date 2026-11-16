from typing import List, Dict, Any, Set
from backend.optimization.engine.optimization_engine import ConstraintCheckResult

class BedConstraintValidator:
    """
    Validates operational bed allocation recommendations:
    1. Only AVAILABLE beds can be allocated.
    2. Single patient per bed (no multiple assignments to the same bed).
    3. Category / Ward matching (e.g. ICU requests assigned to ICU beds).
    4. Occupied or cleaning beds strictly excluded.
    """

    @staticmethod
    def validate(
        allocations: List[Dict[str, Any]],
        beds_map: Dict[str, Dict[str, Any]],
        requests_map: Dict[str, Dict[str, Any]]
    ) -> ConstraintCheckResult:
        violations = []
        warnings = []
        assigned_beds: Set[str] = set()

        for alloc in allocations:
            if alloc.get("allocation_status") != "ALLOCATED":
                continue

            r_id = alloc.get("request_id")
            b_id = alloc.get("bed_id")

            bed_info = beds_map.get(b_id)
            req_info = requests_map.get(r_id, {})

            if not bed_info:
                violations.append(f"Request {r_id}: Allocated non-existent bed ID '{b_id}'.")
                continue

            # Check if bed is currently AVAILABLE
            if bed_info.get("status") != "AVAILABLE" or bed_info.get("is_occupied", False):
                violations.append(
                    f"Request {r_id}: Bed {b_id} is '{bed_info.get('status')}' (Occupied: {bed_info.get('is_occupied')}). Only AVAILABLE beds permitted."
                )

            # Check for double-allocation of the same bed
            if b_id in assigned_beds:
                violations.append(f"Request {r_id}: Bed {b_id} allocated to multiple patients simultaneously.")
            else:
                assigned_beds.add(b_id)

            # Category / Ward matching check
            req_ward = req_info.get("required_ward")
            bed_ward = bed_info.get("ward")
            if req_ward and bed_ward and req_ward.lower() != bed_ward.lower():
                if req_ward.lower() == "icu":
                    violations.append(f"Request {r_id}: Critical ICU patient assigned to non-ICU ward '{bed_ward}'.")
                else:
                    warnings.append(f"Request {r_id}: Requested ward '{req_ward}' matched to alternate ward '{bed_ward}'.")

        is_valid = len(violations) == 0
        return ConstraintCheckResult(is_valid=is_valid, violations=violations, warnings=warnings)
