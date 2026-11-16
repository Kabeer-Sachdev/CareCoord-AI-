from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User, Patient, Doctor
from backend.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    AuditLogResponse
)
from backend.auth.security import hash_password, verify_password, create_access_token
from backend.auth.dependencies import get_current_user, get_optional_current_user, require_role
from backend.services.audit_service import log_audit, get_audit_logs

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

@router.post("/register", response_model=TokenResponse, summary="Register a new user account")
def register_user(
    req: UserRegisterRequest,
    db: Session = Depends(get_db),
    caller: Optional[User] = Depends(get_optional_current_user)
):
    """
    Register a new user account.
    Self-registration as ADMIN is restricted: only an existing ADMIN can create ADMIN accounts.
    """
    # Restrict ADMIN creation
    if req.role == "ADMIN":
        total_admins = db.query(User).filter(User.role == "ADMIN").count()
        if total_admins > 0 and (not caller or caller.role != "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security policy: Self-registration as ADMIN is prohibited. Contact hospital administration."
            )

    # Check for duplicate username or email
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{req.username}' is already taken."
        )

    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email address '{req.email}' is already registered."
        )

    patient_id = req.patient_id
    doctor_id = req.doctor_id

    # Validate linked patient/doctor if supplied
    if patient_id:
        if not db.query(Patient).filter(Patient.patient_id == patient_id).first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Linked patient with ID '{patient_id}' does not exist."
            )
    elif req.role == "PATIENT":
        # Auto-create Patient record
        p_count = db.query(Patient).count()
        new_pid = f"P{p_count + 1:03d}"
        while db.query(Patient).filter(Patient.patient_id == new_pid).first():
            p_count += 1
            new_pid = f"P{p_count + 1:03d}"
        new_patient = Patient(
            patient_id=new_pid,
            name=req.full_name,
            age=req.age or 30,
            gender=req.gender or "Other",
            phone=req.phone or "9876543200",
            department=req.department or "General Medicine",
            blood_group=req.blood_group or "O+",
            existing_conditions=[]
        )
        db.add(new_patient)
        db.flush()
        patient_id = new_pid

    if doctor_id:
        if not db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Linked doctor with ID '{doctor_id}' does not exist."
            )
    elif req.role == "DOCTOR":
        # Auto-create Doctor record
        d_count = db.query(Doctor).count()
        new_did = f"D{d_count + 1:03d}"
        while db.query(Doctor).filter(Doctor.doctor_id == new_did).first():
            d_count += 1
            new_did = f"D{d_count + 1:03d}"
        new_doctor = Doctor(
            doctor_id=new_did,
            name=req.full_name,
            specialization=req.specialization or "General Medicine",
            department=req.department or "General Medicine",
            experience_years=req.experience_years or 5,
            availability=True,
            availability_status="Available",
            shift="09:00-17:00",
            current_patients=0
        )
        db.add(new_doctor)
        db.flush()
        doctor_id = new_did

    hashed_pw = hash_password(req.password)
    user = User(
        username=req.username,
        email=req.email,
        password_hash=hashed_pw,
        role=req.role,
        full_name=req.full_name,
        is_active=True,
        patient_id=patient_id,
        doctor_id=doctor_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(
        db=db,
        action="User registered",
        entity_type="user",
        entity_id=str(user.id),
        username=user.username,
        metadata={"role": user.role, "email": user.email}
    )

    # Generate token
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "patient_id": user.patient_id,
        "doctor_id": user.doctor_id
    }
    access_token = create_access_token(token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=TokenResponse, summary="Authenticate and acquire JWT access token")
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with username or email and password."""
    user = db.query(User).filter(
        (User.username == req.username_or_email) | (User.email == req.username_or_email)
    ).first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact the hospital administrator."
        )

    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "patient_id": user.patient_id,
        "doctor_id": user.doctor_id
    }
    access_token = create_access_token(token_data)

    log_audit(
        db=db,
        action="User logged in",
        entity_type="user",
        entity_id=str(user.id),
        username=user.username,
        metadata={"role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse, summary="Get details of currently authenticated user")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Return profile and role details of the logged in user."""
    return UserResponse.model_validate(current_user)

@router.get("/users", response_model=List[UserResponse], summary="List all hospital accounts (Admin Only)")
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("ADMIN"))
):
    """Admin-only list of system users."""
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/audit-logs", response_model=List[AuditLogResponse], summary="Retrieve system audit logs (Admin Only)")
def list_audit_logs(
    limit: int = 100,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("ADMIN"))
):
    """Admin-only system compliance audit trail."""
    logs = get_audit_logs(db, limit=limit, entity_type=entity_type)
    return [AuditLogResponse.model_validate(log) for log in logs]
