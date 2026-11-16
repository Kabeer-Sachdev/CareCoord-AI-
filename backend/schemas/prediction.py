from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PredictionRequest(BaseModel):
    department: str = Field(..., example="Cardiology")
    forecast_date: Optional[str] = Field(None, example="2026-11-16", description="Target forecast date (YYYY-MM-DD)")
    forecast_interval: Optional[str] = Field("daily", example="daily")

class PatientArrivalsResponse(BaseModel):
    prediction_type: str = "patient_arrivals"
    department: str
    forecast_date: str
    predicted_value: int
    interval_lower: int
    interval_upper: int
    unit: str = "patients"
    model_name: str
    model_version: str
    test_mae: float
    test_r2: float
    prediction_status: str = "available"
    data_type: str = "synthetic_operational"

class EmergencyDemandResponse(BaseModel):
    prediction_type: str = "emergency_demand"
    department: str
    forecast_date: str
    predicted_value: int
    interval_lower: int
    interval_upper: int
    unit: str = "emergency_cases"
    alert: Optional[str] = None
    model_name: str
    model_version: str
    test_mae: float
    test_r2: float
    prediction_status: str = "available"
    data_type: str = "synthetic_operational"

class BedOccupancyResponse(BaseModel):
    prediction_type: str = "bed_occupancy"
    department: str
    forecast_date: str
    predicted_occupied_beds: int
    estimated_available_beds: int
    total_beds: int
    occupancy_rate: float
    alert: Optional[str] = None
    model_name: str
    model_version: str
    test_mae: float
    test_r2: float
    prediction_status: str = "available"
    data_type: str = "synthetic_operational"

class AppointmentDemandResponse(BaseModel):
    prediction_type: str = "appointment_demand"
    department: str
    forecast_date: str
    predicted_value: int
    interval_lower: int
    interval_upper: int
    unit: str = "appointments"
    model_name: str
    model_version: str
    test_mae: float
    test_r2: float
    prediction_status: str = "available"
    data_type: str = "synthetic_operational"

class DepartmentForecastItem(BaseModel):
    department: str
    predicted_arrivals: int
    predicted_emergencies: int
    predicted_appointments: int
    predicted_occupied_beds: int
    estimated_available_beds: int
    total_beds: int
    occupancy_rate: float

class ForecastOverviewResponse(BaseModel):
    forecast_date: str
    total_predicted_arrivals: int
    total_predicted_emergencies: int
    total_predicted_appointments: int
    total_occupied_beds: int
    total_available_beds: int
    total_beds: int
    hospital_occupancy_rate: float
    operational_alerts: List[str]
    department_breakdown: List[DepartmentForecastItem]
    forecast_generated_at: str
    data_type: str = "synthetic_operational"
