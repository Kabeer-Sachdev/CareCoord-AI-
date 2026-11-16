from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

APPOINTMENT_STATUS_TYPES = Literal[
    "scheduled", "completed", "cancelled", "pending", "confirmed", "rejected", "accepted"
]

class AppointmentStatusUpdate(BaseModel):
    status: APPOINTMENT_STATUS_TYPES = Field(..., example="confirmed")
    notes: Optional[str] = Field(None, example="Accepted by doctor")

class AppointmentBase(BaseModel):
    patient_id: str = Field(..., example="P001")
    doctor_id: str = Field(..., example="D001")
    appointment_date: str = Field(..., example="2026-10-15")
    appointment_time: str = Field(..., example="10:30")
    department: str = Field(..., example="Cardiology")
    status: APPOINTMENT_STATUS_TYPES = Field(default="scheduled", example="scheduled")
    reason: Optional[str] = Field(None, example="Routine cardiology checkup")


class AppointmentCreate(AppointmentBase):
    appointment_id: Optional[str] = Field(None, example="A001")


class AppointmentUpdate(BaseModel):
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    department: Optional[str] = None
    status: Optional[APPOINTMENT_STATUS_TYPES] = None
    reason: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: int
    appointment_id: str
    created_at: datetime

    class Config:
        from_attributes = True
