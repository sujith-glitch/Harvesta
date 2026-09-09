"""
Analytics and Session Storage Service.
Provides privacy-safe session recording and user activity event logging.
"""

import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models import UserSession, ActivityEvent


class AnalyticsService:
    @staticmethod
    def hash_ip(ip_address: Optional[str]) -> Optional[str]:
        """Generates a one-way privacy-safe SHA-256 hash of an IP address."""
        if not ip_address:
            return None
        return hashlib.sha256(ip_address.strip().encode("utf-8")).hexdigest()

    @classmethod
    def create_session(
        cls,
        db: Session,
        user_id: int,
        session_id: str,
        device_type: Optional[str] = None,
        platform: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> UserSession:
        """
        Creates a new user session record.
        """
        now = datetime.utcnow()
        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            login_at=now,
            last_active_at=now,
            device_type=device_type,
            platform=platform,
            user_agent=user_agent[:500] if user_agent else None,
            ip_hash=cls.hash_ip(ip_address),
            created_at=now,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def update_session_activity(db: Session, session_id: str) -> Optional[UserSession]:
        """
        Updates the last_active_at timestamp on an ongoing session.
        """
        session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        if session and not session.logout_at:
            session.last_active_at = datetime.utcnow()
            db.commit()
            db.refresh(session)
        return session

    @staticmethod
    def end_session(db: Session, session_id: str) -> Optional[UserSession]:
        """
        Marks a session as logged out and computes total duration in seconds.
        """
        session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        if session and not session.logout_at:
            now = datetime.utcnow()
            session.logout_at = now
            session.last_active_at = now
            if session.login_at:
                session.duration_seconds = int((now - session.login_at).total_seconds())
            db.commit()
            db.refresh(session)
        return session

    @staticmethod
    def log_activity_event(
        db: Session,
        event_name: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        feature: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        commit: bool = True,
    ) -> ActivityEvent:
        """
        Records an application usage analytics event with optional JSON metadata.
        """
        event = ActivityEvent(
            user_id=user_id,
            session_id=session_id,
            event_name=event_name,
            feature=feature,
            event_metadata=metadata,
            created_at=datetime.utcnow(),
        )
        db.add(event)
        if commit:
            db.commit()
            db.refresh(event)
        return event

    @staticmethod
    def get_user_activity(
        db: Session,
        user_id: int,
        limit: int = 50,
    ) -> List[ActivityEvent]:
        """
        Fetches the most recent activity events for a user.
        """
        return (
            db.query(ActivityEvent)
            .filter(ActivityEvent.user_id == user_id)
            .order_by(ActivityEvent.created_at.desc())
            .limit(limit)
            .all()
        )
