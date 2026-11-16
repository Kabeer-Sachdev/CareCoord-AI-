import numpy as np
from typing import List, Dict, Any
from backend.optimization.appointment.appointment_constraints import STANDARD_TIME_SLOTS

def calculate_appointment_metrics(
    allocations: List[Dict[str, Any]],
    total_requests: int,
    doctors_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes rigorous academic operational metrics for appointment scheduling:
    1. Allocation Rate (%)
    2. Average Waiting Time (measured in minutes from the start of the clinical shift at 09:00 AM)
    3. Doctor Workload Imbalance (Standard Deviation of assigned patients per doctor)
    4. Scheduling Conflicts (overlapping doctor or patient assignments)
    """
    allocated = [a for a in allocations if a.get("allocation_status") == "ALLOCATED"]
    unallocated = [a for a in allocations if a.get("allocation_status") == "UNALLOCATED"]

    # 1. Allocation Rate
    allocation_rate = round((len(allocated) / max(1, total_requests)) * 100, 2)

    # 2. Average Waiting Time Calculation
    # Slot 0 (09:00 AM) = 0 mins wait; Slot 1 (09:30 AM) = 30 mins wait; Slot k = k * 30 mins wait
    slot_to_wait_minutes = {slot: idx * 30 for idx, slot in enumerate(STANDARD_TIME_SLOTS)}
    wait_times = [
        slot_to_wait_minutes.get(a.get("allocated_time_slot"), 0)
        for a in allocated
        if a.get("allocated_time_slot") in slot_to_wait_minutes
    ]
    avg_wait_minutes = round(float(np.mean(wait_times)), 1) if wait_times else 0.0

    # 3. Doctor Workload Imbalance (Standard Deviation)
    doctor_ids = [d["doctor_id"] for d in doctors_list]
    doc_counts = {d_id: 0 for d_id in doctor_ids}
    for a in allocated:
        d_id = a.get("doctor_id")
        if d_id in doc_counts:
            doc_counts[d_id] += 1
        elif d_id:
            doc_counts[d_id] = 1

    counts_arr = list(doc_counts.values()) if doc_counts else [0]
    workload_imbalance_std = round(float(np.std(counts_arr)), 2)

    # 4. Scheduling Conflict Count
    doc_slot_pairs = set()
    pat_slot_pairs = set()
    conflicts = 0

    for a in allocated:
        d_id = a.get("doctor_id")
        p_id = a.get("patient_id")
        slot = a.get("allocated_time_slot")

        if d_id and slot:
            if (d_id, slot) in doc_slot_pairs:
                conflicts += 1
            doc_slot_pairs.add((d_id, slot))

        if p_id and slot:
            if (p_id, slot) in pat_slot_pairs:
                conflicts += 1
            pat_slot_pairs.add((p_id, slot))

    return {
        "total_requests": total_requests,
        "allocated_count": len(allocated),
        "unallocated_count": len(unallocated),
        "allocation_rate_percent": allocation_rate,
        "average_wait_minutes": avg_wait_minutes,
        "workload_imbalance_std": workload_imbalance_std,
        "scheduling_conflicts": conflicts
    }
