from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class PatientBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Rahul Sharma")
    age: int = Field(..., ge=0, le=120, example=45)
    gender: str = Field(..., example="Male")
    phone: str = Field(..., min_length=7, max_length=20, example="9999999999")
    department: str = Field(..., example="Cardiology")
    blood_group: str = Field(..., example="B+")
    existing_conditions: Optional[List[str]] = Field(default_factory=list, example=["Hypertension"])

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        valid_genders = ["Male", "Female", "Other"]
        v_title = v.strip().capitalize()
        if v_title not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
        return v_title

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: str) -> str:
        valid_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        v_clean = v.strip().upper()
        if v_clean not in valid_groups:
            raise ValueError(f"Blood group must be one of: {', '.join(valid_groups)}")
        return v_clean


class PatientCreate(PatientBase):
    patient_id: Optional[str] = Field(None, example="P001")


class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = None
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    department: Optional[str] = None
    blood_group: Optional[str] = None
    existing_conditions: Optional[List[str]] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_genders = ["Male", "Female", "Other"]
        v_title = v.strip().capitalize()
        if v_title not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
        return v_title

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        v_clean = v.strip().upper()
        if v_clean not in valid_groups:
            raise ValueError(f"Blood group must be one of: {', '.join(valid_groups)}")
        return v_clean


class PatientResponse(PatientBase):
    id: int
    patient_id: str
    created_at: datetime

    class Config:
        from_attributes = True
