from typing import List, Dict, Any, Set
from backend.optimization.engine.optimization_engine import ConstraintCheckResult

STANDARD_TIME_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
    "11:00 AM", "11:30 AM", "02:00 PM", "02:30 PM",
    "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM"
]

class AppointmentConstraintValidator:
    """
    Verifies that generated appointment allocations strictly satisfy all hospital operational rules:
    1. Doctor non-overlap (no doctor has overlapping appointments)
    2. Patient non-overlap (no patient has double-booked appointments)
    3. Doctor availability (doctor is marked available)
    4. Specialization / Department matching
    5. Existing appointment preservation (no overwrite of confirmed DB appointments)
    """

    @staticmethod
    def validate(
        allocations: List[Dict[str, Any]],
        existing_appointments: List[Dict[str, Any]],
        doctors_map: Dict[str, Dict[str, Any]],
        department: str
    ) -> ConstraintCheckResult:
        violations = []
        warnings = []

        doctor_booked_slots: Dict[str, Set[str]] = {}
        patient_booked_slots: Dict[str, Set[str]] = {}

        # 1. Populate existing confirmed appointments
        for apt in existing_appointments:
            d_id = apt.get("doctor_id")
            slot = apt.get("time_slot")
            p_id = apt.get("patient_id")
            if d_id and slot:
                doctor_booked_slots.setdefault(d_id, set()).add(slot)
            if p_id and slot:
                patient_booked_slots.setdefault(p_id, set()).add(slot)

        # 2. Check each new recommended allocation
        for alloc in allocations:
            if alloc.get("allocation_status") != "ALLOCATED":
                continue

            r_id = alloc.get("request_id")
            d_id = alloc.get("doctor_id")
            p_id = alloc.get("patient_id")
            slot = alloc.get("allocated_time_slot")

            if not slot or slot not in STANDARD_TIME_SLOTS:
                violations.append(f"Request {r_id}: Invalid time slot '{slot}'.")

            # Doctor Availability & Department check
            doc_info = doctors_map.get(d_id)
            if not doc_info:
                violations.append(f"Request {r_id}: Assigned to non-existent doctor '{d_id}'.")
            else:
                if not doc_info.get("availability", True) or doc_info.get("availability_status") in ["On Leave", "Unavailable"]:
                    violations.append(f"Request {r_id}: Doctor {doc_info.get('name')} ({d_id}) is not available.")

                if department and doc_info.get("department") != department:
                    warnings.append(
                        f"Request {r_id}: Doctor department '{doc_info.get('department')}' differs from requested '{department}'."
                    )

            # Doctor Conflict check
            if d_id and slot:
                if slot in doctor_booked_slots.get(d_id, set()):
                    violations.append(
                        f"Request {r_id}: Doctor {d_id} double-booking conflict at slot '{slot}'."
                    )
                else:
                    doctor_booked_slots.setdefault(d_id, set()).add(slot)

            # Patient Conflict check
            if p_id and slot:
                if slot in patient_booked_slots.get(p_id, set()):
                    violations.append(
                        f"Request {r_id}: Patient {p_id} double-booking conflict at slot '{slot}'."
                    )
                else:
                    patient_booked_slots.setdefault(p_id, set()).add(slot)

        is_valid = len(violations) == 0
        return ConstraintCheckResult(is_valid=is_valid, violations=violations, warnings=warnings)
