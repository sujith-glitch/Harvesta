"""
Admin Analytics & Platform Aggregation Service.
Computes platform-wide KPIs, engagement metrics, feature telemetry, and user management lists
without exposing sensitive secrets or credentials.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.models import (
    User,
    Farm,
    Crop,
    FieldAnalysisHistory,
    UserSession,
    ActivityEvent,
    Notification,
    NotificationPreference,
    AIChatConversation,
    AIChatMessage,
    CropDiseaseScan,
    WeatherSnapshot,
    AuditLog,
    SensorDevice,
    SensorReading,
)

ACTIVE_SESSION_THRESHOLD_MINUTES = 30

DATASET_CATALOG = {
    "users": (User, "Account directory", "Names, email addresses, roles, and verification state."),
    "farms": (Farm, "Farm profiles", "Farm ownership, location, size, soil, and farming method."),
    "crops": (Crop, "Crop records", "Crop varieties, dates, growth stage, health status, and notes."),
    "field_analyses": (FieldAnalysisHistory, "Field analysis history", "Soil inputs, weather snapshot, and irrigation recommendation history."),
    "sessions": (UserSession, "Login sessions", "Login time, activity duration, device/platform, and privacy-safe network hash."),
    "activity": (ActivityEvent, "Feature telemetry", "Feature usage events and non-secret metadata."),
    "notifications": (Notification, "Notifications", "In-app/email alert content and delivery state."),
    "notification_preferences": (NotificationPreference, "Notification preferences", "Per-user alert and email preference switches."),
    "chat_conversations": (AIChatConversation, "AI conversations", "Conversation ownership, farm link, title, and timestamps."),
    "chat_messages": (AIChatMessage, "AI messages", "Farmer and assistant message history and local model name."),
    "disease_scans": (CropDiseaseScan, "Disease scans", "Private image reference, screening output, confidence, and recommendation."),
    "weather_snapshots": (WeatherSnapshot, "Weather history", "Farm weather observations and their source."),
    "audit_logs": (AuditLog, "Security audit trail", "Account and administrative actions without passwords or tokens."),
    "sensor_devices": (SensorDevice, "Sensor gateways", "Registered farm hardware, firmware, status, and last-seen time."),
    "sensor_readings": (SensorReading, "Sensor readings", "Historical soil, climate, NPK, rainfall, and battery measurements."),
}


class AdminAnalyticsService:
    @staticmethod
    def _iso(value):
        return value.isoformat() if value else None

    @classmethod
    def _serialize_record(cls, dataset: str, record) -> Dict[str, Any]:
        """Explicit allowlist serializer so secrets can never leak through reflection."""
        if dataset == "users":
            return {
                "id": record.id,
                "email": record.email,
                "full_name": record.full_name,
                "role": record.role,
                "is_verified": record.is_verified,
                "created_at": cls._iso(record.created_at),
            }
        if dataset == "farms":
            return {
                "id": record.id,
                "user_id": record.user_id,
                "name": record.name,
                "location": record.location,
                "district": record.district,
                "state": record.state,
                "country": record.country,
                "size": record.size,
                "soil_type": record.soil_type,
                "farming_method": record.farming_method,
                "description": record.description,
                "created_at": cls._iso(record.created_at),
                "updated_at": cls._iso(record.updated_at),
            }
        if dataset == "crops":
            return {
                "id": record.id,
                "farm_id": record.farm_id,
                "name": record.name,
                "variety": record.variety,
                "planting_date": cls._iso(record.planting_date),
                "expected_harvest_date": cls._iso(record.expected_harvest_date),
                "growth_stage": record.growth_stage,
                "health_status": record.health_status,
                "notes": record.notes,
                "created_at": cls._iso(record.created_at),
                "updated_at": cls._iso(record.updated_at),
            }
        if dataset == "sessions":
            data = record.to_dict()
            data["user_agent"] = record.user_agent
            data["ip_hash"] = record.ip_hash
            return data
        return record.to_dict()

    @classmethod
    def get_data_inventory(cls, db: Session) -> Dict[str, Any]:
        datasets = []
        for key, (model, label, description) in DATASET_CATALOG.items():
            datasets.append({
                "key": key,
                "label": label,
                "description": description,
                "row_count": db.query(model).count(),
                "retention": "persistent_until_deleted",
                "admin_visible": True,
            })
        return {
            "datasets": datasets,
            "excluded_secrets": [
                "password hashes",
                "verification and password-reset tokens",
                "JWT access tokens",
                "SMTP and Supabase service credentials",
                "raw IP addresses",
            ],
        }

    @classmethod
    def get_dataset_records(
        cls,
        db: Session,
        dataset: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        config = DATASET_CATALOG.get(dataset)
        if not config:
            raise ValueError("Unknown admin dataset.")

        model, label, description = config
        query = db.query(model)
        total = query.count()
        created_column = getattr(model, "created_at", None)
        order_column = created_column if created_column is not None else getattr(model, "id")
        records = query.order_by(order_column.desc()).offset(offset).limit(limit).all()
        return {
            "dataset": dataset,
            "label": label,
            "description": description,
            "total": total,
            "limit": limit,
            "offset": offset,
            "records": [cls._serialize_record(dataset, item) for item in records],
        }

    @staticmethod
    def get_overview_metrics(db: Session) -> Dict[str, Any]:
        """
        Gathers aggregate overview metrics across users, sessions, platform domain objects, and telemetry.
        """
        now = datetime.utcnow()
        active_cutoff = now - timedelta(minutes=ACTIVE_SESSION_THRESHOLD_MINUTES)
        h24_cutoff = now - timedelta(hours=24)
        d7_cutoff = now - timedelta(days=7)

        # --- User Metrics ---
        total_users = db.query(User).count()
        verified_users = db.query(User).filter(User.is_verified == True).count()
        unverified_users = total_users - verified_users
        admin_users = db.query(User).filter(User.role == "admin").count()
        farmer_users = total_users - admin_users

        # --- Session & Login Metrics ---
        total_sessions = db.query(UserSession).count()
        active_sessions = (
            db.query(UserSession)
            .filter(
                UserSession.logout_at == None,
                UserSession.last_active_at >= active_cutoff,
            )
            .count()
        )
        avg_duration_res = (
            db.query(func.avg(UserSession.duration_seconds))
            .filter(UserSession.duration_seconds != None)
            .scalar()
        )
        avg_session_duration = round(float(avg_duration_res), 1) if avg_duration_res is not None else 0.0

        logins_24h = db.query(UserSession).filter(UserSession.login_at >= h24_cutoff).count()
        logins_7d = db.query(UserSession).filter(UserSession.login_at >= d7_cutoff).count()

        # --- Platform Data Totals ---
        total_farms = db.query(Farm).count()
        total_crops = db.query(Crop).count()
        total_field_analyses = db.query(FieldAnalysisHistory).count()
        total_notifications = db.query(Notification).count()
        total_conversations = db.query(AIChatConversation).count()
        total_messages = db.query(AIChatMessage).count()
        total_disease_scans = db.query(CropDiseaseScan).count()
        total_weather_snapshots = db.query(WeatherSnapshot).count()
        total_sensor_devices = db.query(SensorDevice).count()
        total_sensor_readings = db.query(SensorReading).count()

        # --- Feature Usage Aggregates ---
        feature_counts_raw = (
            db.query(ActivityEvent.feature, func.count(ActivityEvent.id))
            .filter(ActivityEvent.feature != None)
            .group_by(ActivityEvent.feature)
            .order_by(desc(func.count(ActivityEvent.id)))
            .all()
        )
        feature_usage = [{"feature": row[0], "count": row[1]} for row in feature_counts_raw]

        event_counts_raw = (
            db.query(ActivityEvent.event_name, func.count(ActivityEvent.id))
            .group_by(ActivityEvent.event_name)
            .order_by(desc(func.count(ActivityEvent.id)))
            .limit(10)
            .all()
        )
        event_usage = [{"event_name": row[0], "count": row[1]} for row in event_counts_raw]

        # --- Recent Feed Items ---
        recent_activity_records = (
            db.query(ActivityEvent)
            .order_by(ActivityEvent.created_at.desc())
            .limit(8)
            .all()
        )
        recent_audits_records = (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(8)
            .all()
        )

        return {
            "user_metrics": {
                "total_users": total_users,
                "verified_users": verified_users,
                "unverified_users": unverified_users,
                "admin_users": admin_users,
                "farmer_users": farmer_users,
            },
            "session_metrics": {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "active_threshold_minutes": ACTIVE_SESSION_THRESHOLD_MINUTES,
                "average_session_duration_seconds": avg_session_duration,
                "logins_24h": logins_24h,
                "logins_7d": logins_7d,
            },
            "platform_totals": {
                "total_farms": total_farms,
                "total_crops": total_crops,
                "total_field_analyses": total_field_analyses,
                "total_notifications": total_notifications,
                "total_ai_chat_conversations": total_conversations,
                "total_ai_chat_messages": total_messages,
                "total_crop_disease_scans": total_disease_scans,
                "total_weather_snapshots": total_weather_snapshots,
                "total_sensor_devices": total_sensor_devices,
                "total_sensor_readings": total_sensor_readings,
            },
            "feature_usage": feature_usage,
            "event_usage": event_usage,
            "recent_activity": [e.to_dict() for e in recent_activity_records],
            "recent_audits": [a.to_dict() for a in recent_audits_records],
        }

    @staticmethod
    def get_users_list(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns a paginated list of registered users.
        Strictly excludes passwords, verification tokens, and reset token hashes.
        """
        query = db.query(User)

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                (func.lower(User.email).like(term)) | (func.lower(User.full_name).like(term))
            )

        if role and role.strip():
            query = query.filter(User.role == role.strip().lower())

        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

        user_list = []
        for u in users:
            # Fetch last active session timestamp if available
            last_session = (
                db.query(UserSession)
                .filter(UserSession.user_id == u.id)
                .order_by(UserSession.login_at.desc())
                .first()
            )
            farms_count = db.query(Farm).filter(Farm.user_id == u.id).count()
            analyses_count = db.query(FieldAnalysisHistory).filter(FieldAnalysisHistory.user_id == u.id).count()

            user_list.append({
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": getattr(u, "role", "farmer"),
                "is_verified": u.is_verified,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "farms_count": farms_count,
                "analyses_count": analyses_count,
                "last_active_at": last_session.last_active_at.isoformat() if last_session and last_session.last_active_at else None,
                "last_login_at": last_session.login_at.isoformat() if last_session and last_session.login_at else None,
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "users": user_list,
        }

    @staticmethod
    def get_activity_events(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        feature: Optional[str] = None,
        event_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns paginated activity events telemetry.
        """
        query = db.query(ActivityEvent)
        if feature:
            query = query.filter(ActivityEvent.feature == feature)
        if event_name:
            query = query.filter(ActivityEvent.event_name == event_name)

        total = query.count()
        events = query.order_by(ActivityEvent.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "events": [e.to_dict() for e in events],
        }

    @staticmethod
    def get_audit_logs(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns paginated audit logs.
        """
        query = db.query(AuditLog)
        if action:
            query = query.filter(AuditLog.action == action)

        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "logs": [l.to_dict() for l in logs],
        }

    @staticmethod
    def get_sessions(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Returns paginated session telemetry records.
        """
        query = db.query(UserSession)
        if active_only:
            cutoff = datetime.utcnow() - timedelta(minutes=ACTIVE_SESSION_THRESHOLD_MINUTES)
            query = query.filter(UserSession.logout_at == None, UserSession.last_active_at >= cutoff)

        total = query.count()
        sessions = query.order_by(UserSession.login_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "sessions": [s.to_dict() for s in sessions],
        }
