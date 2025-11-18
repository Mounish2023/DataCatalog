# backend/app/audit.py
from app.models.models import AuditLog
from app.database import engine
from sqlmodel import Session

def record_audit(session: Session, user_id: str, action_type: str, target_type: str, target_id: str = None, before: str = None, after: str = None):
    log = AuditLog(user_id=user_id, action_type=action_type, target_type=target_type, target_id=target_id, before=before, after=after)
    session.add(log)
    session.commit()
