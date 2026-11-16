from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.schemas.auth import NotificationResponse
from backend.auth.dependencies import get_current_user
from backend.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", summary="Get current user's notifications")
def get_my_notifications(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve notifications belonging to the authenticated user."""
    notifs = notification_service.get_user_notifications(db, current_user.id, limit=limit)
    unread_count = notification_service.get_unread_count(db, current_user.id)
    return {
        "unread_count": unread_count,
        "notifications": [NotificationResponse.model_validate(n) for n in notifs]
    }

@router.put("/{notification_id}/read", summary="Mark notification as read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    success = notification_service.mark_as_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notification_id}' not found for user."
        )
    return {"status": "success", "message": "Notification marked as read."}

@router.put("/read-all", summary="Mark all notifications as read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all unread notifications for current user as read."""
    count = notification_service.mark_all_as_read(db, current_user.id)
    return {"status": "success", "marked_count": count}

