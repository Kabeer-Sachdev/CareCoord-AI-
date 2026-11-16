"""
Hospital Information System (HIS) MCP Server.
Exposes standardized administrative and clinical resource query tools using the official MCP SDK.
"""

from typing import Optional, Dict, Any, List
from mcp.server.mcpserver import MCPServer

hospital_mcp_server = MCPServer(
    name="Hospital Information System (HIS)",
    version="1.0.0",
    instructions="Provides read-only operational queries for hospital patients, doctors, schedules, and bed utilization."
)

@hospital_mcp_server.tool(
    name="get_patient_record",
    description="Retrieve demographic and medical summary record for a registered patient by patient ID."
)
def get_patient_record(patient_id: str) -> Dict[str, Any]:
    from backend.database.database import SessionLocal
    from backend.database.models import Patient
    
    db = SessionLocal()
    try:
        p = db.query(Patient).filter(Patient.patient_id == patient_id.strip()).first()
        if not p:
            return {
                "found": False,
                "patient_id": patient_id,
                "message": f"Patient with ID '{patient_id}' not found in Hospital Information System."
            }
        return {
            "found": True,
            "patient_id": p.patient_id,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "phone": p.phone,
            "department": p.department,
            "blood_group": p.blood_group,
            "existing_conditions": p.existing_conditions or [],
            "source_system": "CareCoord Primary HIS Sandbox"
        }
    finally:
        db.close()


@hospital_mcp_server.tool(
    name="get_patient_appointments",
    description="Retrieve all scheduled, in-progress, or completed appointments for a given patient ID."
)
def get_patient_appointments(patient_id: str) -> Dict[str, Any]:
    from backend.database.database import SessionLocal
    from backend.database.models import Appointment, Doctor
    
    db = SessionLocal()
    try:
        appts = db.query(Appointment).filter(Appointment.patient_id == patient_id.strip()).all()
        results = []
        for a in appts:
            doc = db.query(Doctor).filter(Doctor.doctor_id == a.doctor_id).first()
            results.append({
                "appointment_id": a.appointment_id,
                "doctor_id": a.doctor_id,
                "doctor_name": doc.name if doc else "Unassigned",
                "department": a.department,
                "date": a.appointment_date,
                "time": a.appointment_time,
                "status": a.status,
                "reason": a.reason
            })
        return {
            "patient_id": patient_id,
            "appointment_count": len(results),
            "appointments": results,
            "source_system": "CareCoord Central Scheduling Service"
        }
    finally:
        db.close()


@hospital_mcp_server.tool(
    name="get_available_doctors",
    description="Query available medical doctors, optionally filtered by clinical department."
)
def get_available_doctors(department: Optional[str] = None) -> Dict[str, Any]:
    from backend.database.database import SessionLocal
    from backend.database.models import Doctor
    
    db = SessionLocal()
    try:
        q = db.query(Doctor).filter(Doctor.availability == True)
        if department and department.strip() and department.lower() != "all":
            q = q.filter(Doctor.department.ilike(f"%{department.strip()}%"))
        docs = q.all()
        return {
            "query_department": department or "All Departments",
            "available_count": len(docs),
            "doctors": [
                {
                    "doctor_id": d.doctor_id,
                    "name": d.name,
                    "department": d.department,
                    "specialization": d.specialization,
                    "shift": d.shift,
                    "current_patient_load": d.current_patients
                }
                for d in docs
            ]
        }
    finally:
        db.close()


@hospital_mcp_server.tool(
    name="get_doctor_schedule",
    description="Retrieve detailed shift schedule, specialization, and caseload for a specified doctor ID."
)
def get_doctor_schedule(doctor_id: str) -> Dict[str, Any]:
    from backend.database.database import SessionLocal
    from backend.database.models import Doctor, Appointment
    
    db = SessionLocal()
    try:
        d = db.query(Doctor).filter(Doctor.doctor_id == doctor_id.strip()).first()
        if not d:
            return {"found": False, "doctor_id": doctor_id, "message": f"Doctor '{doctor_id}' not found."}
        
        assigned_appts = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id.strip(),
            Appointment.status == "scheduled"
        ).count()

        return {
            "found": True,
            "doctor_id": d.doctor_id,
            "name": d.name,
            "specialization": d.specialization,
            "department": d.department,
            "experience_years": d.experience_years,
            "is_available": d.availability,
            "status_label": d.availability_status or "Available",
            "active_shift": d.shift,
            "assigned_active_appointments": assigned_appts,
            "current_ward_patients": d.current_patients
        }
    finally:
        db.close()


@hospital_mcp_server.tool(
    name="get_available_beds",
    description="Query currently vacant hospital beds, optionally filtered by department or bed type (General, ICU, Emergency)."
)
def get_available_beds(department: Optional[str] = None, bed_type: Optional[str] = None) -> Dict[str, Any]:
    from backend.database.database import SessionLocal
    from backend.database.models import Bed
    
    db = SessionLocal()
    try:
        q = db.query(Bed).filter(Bed.is_occupied == False)
        if department and department.strip() and department.lower() != "all":
            q = q.filter(Bed.department.ilike(f"%{department.strip()}%"))
        if bed_type and bed_type.strip() and bed_type.lower() != "all":
            q = q.filter(Bed.bed_type.ilike(f"%{bed_type.strip()}%"))
        vacant_beds = q.all()
        return {
            "filter_department": department or "All",
            "filter_bed_type": bed_type or "All",
            "available_bed_count": len(vacant_beds),
            "beds": [
                {
                    "bed_id": b.bed_id,
                    "bed_number": b.bed_number,
                    "department": b.department,
                    "bed_type": b.bed_type,
                    "ward": b.ward
                }
                for b in vacant_beds
            ]
        }
    finally:
        db.close()


@hospital_mcp_server.tool(
    name="get_department_information",
    description="Retrieve operational capacity, ward locations, and contact details for a hospital department."
)
def get_department_information(department: str) -> Dict[str, Any]:
    dept_lower = department.strip().lower()
    dept_info_directory = {
        "cardiology": {
            "department": "Cardiology",
            "head_of_department": "Dr. Mehta",
            "floor": "3rd Floor, West Wing",
            "stat_hotline": "+91-11-2659-4011",
            "icu_attached": True,
            "telemetry_supported": True,
            "hours": "24/7 Acute Cardiac Care"
        },
        "neurology": {
            "department": "Neurology",
            "head_of_department": "Dr. Swati Sen",
            "floor": "4th Floor, North Wing",
            "stat_hotline": "+91-11-2659-4012",
            "icu_attached": True,
            "telemetry_supported": True,
            "hours": "24/7 Stroke & Neuro Care"
        },
        "orthopedics": {
            "department": "Orthopedics",
            "head_of_department": "Dr. Rajesh Khanna",
            "floor": "2nd Floor, East Wing",
            "stat_hotline": "+91-11-2659-4013",
            "icu_attached": False,
            "telemetry_supported": False,
            "hours": "08:00 - 20:00 Routine / 24/7 Trauma"
        },
        "emergency medicine": {
            "department": "Emergency Medicine",
            "head_of_department": "Dr. Arjun Kapoor",
            "floor": "Ground Floor, Red Zone Entrance",
            "stat_hotline": "+91-11-2659-4000",
            "icu_attached": True,
            "telemetry_supported": True,
            "hours": "24/7 Unrestricted Level-1 Trauma"
        },
        "general medicine": {
            "department": "General Medicine",
            "head_of_department": "Dr. Sunita Rao",
            "floor": "1st Floor, Central Block",
            "stat_hotline": "+91-11-2659-4015",
            "icu_attached": False,
            "telemetry_supported": True,
            "hours": "24/7 Inpatient Acute"
        },
        "pediatrics": {
            "department": "Pediatrics",
            "head_of_department": "Dr. Vivek Murthy",
            "floor": "5th Floor, Child Health Pavilion",
            "stat_hotline": "+91-11-2659-4016",
            "icu_attached": True,
            "telemetry_supported": True,
            "hours": "24/7 Pediatric & NICU"
        }
    }
    
    info = dept_info_directory.get(dept_lower)
    if not info:
        # Fallback dynamic summary
        return {
            "department": department.title(),
            "head_of_department": "Senior Consulting Physician",
            "floor": "General Inpatient Complex",
            "stat_hotline": "+91-11-2659-4000",
            "icu_attached": False,
            "telemetry_supported": False,
            "hours": "09:00 - 18:00 Regular Operations",
            "note": "Standard clinical department operational parameters."
        }
    return info
