from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.database.models import AuditLog, User

def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    user: Optional[User] = None,
    username: Optional[str] = None,
    user_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    meta_data: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """Log an operational action for governance and hospital compliance auditing."""
    final_user_id = user.id if user else user_id
    final_username = user.username if user else username
    final_metadata = meta_data if meta_data is not None else metadata

    entry = AuditLog(
        user_id=final_user_id,
        username=final_username,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        timestamp=datetime.utcnow(),
        meta_data=final_metadata
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_audit_logs(
    db: Session,
    limit: int = 100,
    entity_type: Optional[str] = None
) -> List[AuditLog]:
    """Retrieve audit history ordered by newest first."""
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
