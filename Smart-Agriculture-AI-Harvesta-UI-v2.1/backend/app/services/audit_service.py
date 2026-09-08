"""
Security and System Audit Logging Service.
Logs platform actions and lifecycle events without sensitive credentials or secrets.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models import AuditLog


class AuditService:
    @staticmethod
    def log_audit_event(
        db: Session,
        action: str,
        entity_type: str,
        user_id: Optional[int] = None,
        entity_id: Optional[int] = None,
        status: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Records an audit log entry.
        IMPORTANT: Never pass passwords, tokens, API keys, or raw SMTP secrets in metadata.
        """
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            audit_metadata=metadata,
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_audit_logs(
        db: Session,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditLog]:
        """
        Queries audit logs with optional filtering.
        """
        query = db.query(AuditLog)
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
