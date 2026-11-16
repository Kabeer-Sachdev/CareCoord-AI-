from typing import Optional
from pydantic import BaseModel, Field

class DoctorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Dr. Mehta")
    specialization: str = Field(..., example="Cardiology")
    department: str = Field(..., example="Cardiology")
    experience_years: int = Field(..., ge=0, le=70, example=12)
    availability: bool = Field(default=True, example=True)
    availability_status: Optional[str] = Field(default="Available", example="Available")
    shift: str = Field(..., example="09:00-17:00")
    current_patients: int = Field(default=0, ge=0, example=4)


class DoctorCreate(DoctorBase):
    doctor_id: Optional[str] = Field(None, example="D001")


class DoctorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    specialization: Optional[str] = None
    department: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0, le=70)
    availability: Optional[bool] = None
    availability_status: Optional[str] = None
    shift: Optional[str] = None
    current_patients: Optional[int] = Field(None, ge=0)


class DoctorStatusUpdate(BaseModel):
    availability_status: str = Field(..., example="Available")  # Available, Busy, Unavailable, On Leave
    notes: Optional[str] = Field(None, example="In emergency surgery")


class DoctorResponse(DoctorBase):
    id: int
    doctor_id: str

    class Config:
        from_attributes = True
