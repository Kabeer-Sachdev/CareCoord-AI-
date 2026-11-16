from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.auth.security import decode_access_token

# Bearer token scheme with auto_error=False for flexible handling
security_bearer = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate request via JWT Bearer token and return active User instance.
    Raises 401 Unauthorized if token is missing, expired, or invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: Token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account matching token does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    
    return user

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Return User if valid token is provided, otherwise None."""
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        if not payload:
            return None
        username: str = payload.get("sub")
        if not username:
            return None
        return db.query(User).filter(User.username == username, User.is_active == True).first()
    except Exception:
        return None

def require_role(*allowed_roles: str):
    """
    Factory creating a FastAPI dependency enforcing that the current user possesses one of the allowed roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{current_user.role}' lacks permission for this resource. Required: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker

def enforce_patient_isolation(current_user: User, patient_id: str):
    """
    If current user is a patient, strictly restrict them to accessing only their own patient data.
    Staff roles (ADMIN, RECEPTIONIST, DOCTOR, NURSE) can access according to operational duties.
    """
    if current_user.role == "PATIENT":
        if current_user.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Patient Data Isolation: You are not authorized to view or modify records for patient '{patient_id}'."
            )

def enforce_doctor_isolation(current_user: User, doctor_id: str):
    """
    If current user is a doctor, verify they are only modifying their own availability or schedule.
    """
    if current_user.role == "DOCTOR":
        if current_user.doctor_id != doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Doctor Isolation: You are not authorized to modify schedule for doctor '{doctor_id}'."
            )

