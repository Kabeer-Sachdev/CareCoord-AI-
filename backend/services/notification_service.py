from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy.orm import Session

from backend.database.models import Notification, User, Appointment, Emergency
from backend.realtime.connection_manager import connection_manager
from backend.realtime.events import EventType

def create_notification(
    db: Session,
    user_id: int,
    type: str,
    title: str,
    message: str,
    priority: str = "NORMAL"
) -> Notification:
    """Create a persistent notification in SQLite and push live via WebSocket."""
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        priority=priority,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # Push to specific user via WebSocket
    payload = {
        "id": notif.id,
        "user_id": notif.user_id,
        "type": notif.type,
        "title": notif.title,
        "message": notif.message,
        "priority": notif.priority,
        "is_read": notif.is_read,
        "created_at": notif.created_at.isoformat()
    }
    connection_manager.send_personal_sync(user_id, EventType.NOTIFICATION_CREATED, payload)
    return notif

def get_user_notifications(db: Session, user_id: int, limit: int = 50) -> List[Notification]:
    """Retrieve recent notifications for a user ordered by timestamp."""
    return db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).limit(limit).all()

def get_unread_count(db: Session, user_id: int) -> int:
    """Return count of unread notifications for a user."""
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()

def mark_as_read(db: Session, notification_id: int, user_id: int) -> bool:
    """Mark a specific notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    if not notif:
        return False
    notif.is_read = True
    db.commit()
    return True

def mark_all_as_read(db: Session, user_id: int) -> int:
    """Mark all unread notifications for a user as read."""
    updated = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return updated

def notify_appointment_participants(
    db: Session,
    appointment: Appointment,
    action: str = "created",
    custom_message: Optional[str] = None
):
    """
    Generate notifications for relevant Doctor and Patient user accounts upon appointment event.
    """
    action_titles = {
        "created": ("New Appointment Scheduled", f"Appointment {appointment.appointment_id} scheduled for {appointment.appointment_date} at {appointment.appointment_time}."),
        "confirmed": ("Appointment Confirmed", f"Appointment {appointment.appointment_id} has been confirmed."),
        "cancelled": ("Appointment Cancelled", f"Appointment {appointment.appointment_id} has been cancelled."),
        "rescheduled": ("Appointment Rescheduled", f"Appointment {appointment.appointment_id} rescheduled to {appointment.appointment_date} at {appointment.appointment_time}."),
        "accepted": ("Doctor Accepted Appointment", f"Doctor accepted appointment {appointment.appointment_id}."),
        "rejected": ("Doctor Rejected Appointment", f"Doctor rejected appointment {appointment.appointment_id}.")
    }
    title, default_msg = action_titles.get(action.lower(), ("Appointment Update", f"Appointment {appointment.appointment_id} updated."))
    msg = custom_message or default_msg

    # Notify Doctor
    doc_user = db.query(User).filter(User.doctor_id == appointment.doctor_id).first()
    if doc_user:
        create_notification(
            db=db,
            user_id=doc_user.id,
            type=EventType.APPOINTMENT_UPDATED if action != "created" else EventType.APPOINTMENT_CREATED,
            title=f"Doctor Alert: {title}",
            message=f"{msg} (Patient: {appointment.patient_id})",
            priority="NORMAL"
        )

    # Notify Patient
    pat_user = db.query(User).filter(User.patient_id == appointment.patient_id).first()
    if pat_user:
        create_notification(
            db=db,
            user_id=pat_user.id,
            type=EventType.APPOINTMENT_UPDATED if action != "created" else EventType.APPOINTMENT_CREATED,
            title=f"Patient Notice: {title}",
            message=f"{msg} (Doctor: {appointment.doctor_id}, Dept: {appointment.department})",
            priority="NORMAL"
        )

def notify_emergency_escalation(db: Session, emergency: Emergency):
    """Notify on-duty nurses, assigned doctor, and administrators of an incoming emergency."""
    # Notify all Nurses and Admins
    staff_users = db.query(User).filter(User.role.in_(["NURSE", "ADMIN"])).all()
    for staff in staff_users:
        create_notification(
            db=db,
            user_id=staff.id,
            type=EventType.EMERGENCY_CREATED,
            title=f"Emergency Alert [{emergency.priority}]: {emergency.emergency_id}",
            message=f"Urgent case requiring {emergency.required_department} ({emergency.required_bed_type} bed).",
            priority="CRITICAL" if emergency.priority in ["CRITICAL", "HIGH"] else "HIGH"
        )

    # Notify assigned doctor if one exists
    if emergency.assigned_doctor_id:
        doc_user = db.query(User).filter(User.doctor_id == emergency.assigned_doctor_id).first()
        if doc_user:
            create_notification(
                db=db,
                user_id=doc_user.id,
                type=EventType.EMERGENCY_CREATED,
                title=f"Urgent Emergency Assigned: {emergency.emergency_id}",
                message=f"You are assigned to an emergency case ({emergency.priority}) for Patient {emergency.patient_id}.",
                priority="CRITICAL"
            )

def notify_workflow_approval_required(
    db: Session,
    workflow: Any,
    summary: Optional[str] = None
):
    """Notify receptionists and admins that an AI recommendation requires human sign-off."""
    if hasattr(workflow, "workflow_id"):
        wf_id = workflow.workflow_id
        wf_summary = summary or workflow.recommendation or workflow.original_request
    else:
        wf_id = str(workflow)
        wf_summary = summary or f"Workflow {wf_id} requires human approval."

    staff = db.query(User).filter(User.role.in_(["ADMIN", "RECEPTIONIST"])).all()
    for s in staff:
        create_notification(
            db=db,
            user_id=s.id,
            type="WORKFLOW_APPROVAL_REQUIRED",
            title=f"AI Workflow Approval Required: {wf_id}",
            message=wf_summary,
            priority="HIGH"
        )
