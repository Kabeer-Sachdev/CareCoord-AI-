from typing import Dict, Any, Optional
from backend.ml.prediction.prediction_service import prediction_service

def predict_patient_arrivals(department: str = "Cardiology", forecast_date: Optional[str] = None) -> Dict[str, Any]:
    """Predicts future patient arrivals for a specific hospital department."""
    return prediction_service.predict_patient_arrivals(department=department, forecast_date=forecast_date)

def predict_emergency_demand(department: str = "Emergency Medicine", forecast_date: Optional[str] = None) -> Dict[str, Any]:
    """Predicts emergency request workload and checks for emergency surge warnings."""
    return prediction_service.predict_emergency_demand(department=department, forecast_date=forecast_date)

def predict_bed_occupancy(department: str = "Cardiology", forecast_date: Optional[str] = None) -> Dict[str, Any]:
    """Estimates future occupied beds, available beds, and bed utilization percentage."""
    return prediction_service.predict_bed_occupancy(department=department, forecast_date=forecast_date)

def predict_appointment_demand(department: str = "Cardiology", forecast_date: Optional[str] = None) -> Dict[str, Any]:
    """Estimates scheduled outpatient appointment demand."""
    return prediction_service.predict_appointment_demand(department=department, forecast_date=forecast_date)

def get_resource_forecast(department: Optional[str] = None, forecast_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns comprehensive resource forecast.
    If department is provided, returns department-specific predictions; otherwise hospital-wide overview.
    """
    if department and department.strip() and department.lower() != "all":
        arr = predict_patient_arrivals(department, forecast_date)
        er = predict_emergency_demand(department, forecast_date)
        bed = predict_bed_occupancy(department, forecast_date)
        appt = predict_appointment_demand(department, forecast_date)
        return {
            "forecast_date": arr["forecast_date"],
            "department": department,
            "predicted_arrivals": arr["predicted_value"],
            "predicted_emergencies": er["predicted_value"],
            "predicted_appointments": appt["predicted_value"],
            "predicted_occupied_beds": bed["predicted_occupied_beds"],
            "estimated_available_beds": bed["estimated_available_beds"],
            "occupancy_rate": bed["occupancy_rate"],
            "alerts": [a for a in [er.get("alert"), bed.get("alert")] if a],
            "models_used": [arr["model_name"], er["model_name"], bed["model_name"], appt["model_name"]]
        }
    return prediction_service.get_forecast_overview(forecast_date=forecast_date)
