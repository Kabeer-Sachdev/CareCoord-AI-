from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.database import get_db
from backend.database.models import Patient, Doctor, Appointment, Bed, Emergency

router = APIRouter(prefix="/dashboard", tags=["Dashboard Summary"])

@router.get("/summary", summary="Get aggregated hospital command center summary statistics")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Calculate live hospital metrics and resource utilization from SQLite database."""
    try:
        total_patients = db.query(Patient).count()
        total_doctors = db.query(Doctor).count()
        available_doctors = db.query(Doctor).filter(Doctor.availability == True).count()
        
        total_beds = db.query(Bed).count()
        available_beds = db.query(Bed).filter(Bed.status == "available").count()
        
        total_appts = db.query(Appointment).count()
        today_appts = db.query(Appointment).filter(Appointment.status.in_(["scheduled", "pending"])).count()
        
        active_emergencies = db.query(Emergency).filter(Emergency.status.in_(["waiting", "being_processed", "allocated"])).count()

        # Calculate Bed Utilization by Bed Type
        bed_types = ["ICU", "General", "Emergency", "Private"]
        utilization = {}
        for bt in bed_types:
            total_type = db.query(Bed).filter(Bed.bed_type == bt).count()
            occupied_type = db.query(Bed).filter(Bed.bed_type == bt, Bed.status == "occupied").count()
            pct = round((occupied_type / total_type * 100), 1) if total_type > 0 else 0.0
            utilization[bt] = {
                "total": total_type,
                "occupied": occupied_type,
                "available": total_type - occupied_type,
                "percentage": pct
            }

        # Calculate Doctor Availability by Department
        departments = db.query(Doctor.department).distinct().all()
        doc_availability_by_dept = []
        for (dept_name,) in departments:
            total_dept = db.query(Doctor).filter(Doctor.department == dept_name).count()
            avail_dept = db.query(Doctor).filter(Doctor.department == dept_name, Doctor.availability == True).count()
            doc_availability_by_dept.append({
                "department": dept_name,
                "available": avail_dept,
                "total": total_dept
            })

        # Fetch Recent Appointments (top 5)
        recent_appointments_raw = db.query(Appointment).order_by(Appointment.id.desc()).limit(5).all()
        recent_appointments = [
            {
                "appointment_id": a.appointment_id,
                "patient_id": a.patient_id,
                "doctor_id": a.doctor_id,
                "department": a.department,
                "date": a.appointment_date,
                "time": a.appointment_time,
                "status": a.status
            } for a in recent_appointments_raw
        ]

        # Fetch Active Emergencies (top 5)
        recent_emergencies_raw = db.query(Emergency).filter(
            Emergency.status.in_(["waiting", "being_processed", "allocated"])
        ).order_by(Emergency.id.desc()).limit(5).all()
        
        recent_emergencies = [
            {
                "emergency_id": e.emergency_id,
                "patient_id": e.patient_id,
                "priority": e.priority,
                "required_department": e.required_department,
                "required_bed_type": e.required_bed_type,
                "assigned_doctor_id": e.assigned_doctor_id,
                "status": e.status
            } for e in recent_emergencies_raw
        ]

        return {
            "status": "healthy",
            "kpis": {
                "total_patients": total_patients,
                "available_doctors": available_doctors,
                "total_doctors": total_doctors,
                "today_appointments": today_appts,
                "total_appointments": total_appts,
                "available_beds": available_beds,
                "total_beds": total_beds,
                "active_emergencies": active_emergencies
            },
            "resource_utilization": utilization,
            "doctor_availability": doc_availability_by_dept,
            "recent_appointments": recent_appointments,
            "recent_emergencies": recent_emergencies
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate dashboard summary: {str(exc)}"
        )
