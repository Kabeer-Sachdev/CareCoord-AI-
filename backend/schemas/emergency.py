from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

EMERGENCY_PRIORITY_TYPES = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
EMERGENCY_STATUS_TYPES = Literal["waiting", "being_processed", "allocated", "completed"]

class EmergencyBase(BaseModel):
    patient_id: str = Field(..., example="P001")
    priority: EMERGENCY_PRIORITY_TYPES = Field(..., example="CRITICAL")
    required_department: str = Field(..., example="Cardiology")
    required_bed_type: str = Field(..., example="ICU")
    assigned_doctor_id: Optional[str] = Field(None, example="D001")
    status: EMERGENCY_STATUS_TYPES = Field(default="waiting", example="waiting")


class EmergencyCreate(EmergencyBase):
    emergency_id: Optional[str] = Field(None, example="E001")


class EmergencyUpdate(BaseModel):
    patient_id: Optional[str] = None
    priority: Optional[EMERGENCY_PRIORITY_TYPES] = None
    required_department: Optional[str] = None
    required_bed_type: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    status: Optional[EMERGENCY_STATUS_TYPES] = None


class EmergencyResponse(EmergencyBase):
    id: int
    emergency_id: str
    created_at: datetime

    class Config:
        from_attributes = True
