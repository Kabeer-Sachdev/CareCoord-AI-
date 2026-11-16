from datetime import datetime
from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel, EmailStr, Field

ROLE_TYPES = Literal["ADMIN", "RECEPTIONIST", "DOCTOR", "NURSE", "PATIENT"]

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: ROLE_TYPES = Field(default="PATIENT")
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    blood_group: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None

class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: str
    is_active: bool
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    priority: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    timestamp: datetime
    meta_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

