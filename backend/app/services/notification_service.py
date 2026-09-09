"""
Notification and User Preference Management Service.
Handles in-app notification creation, read status tracking, notification preferences,
and domain-specific alert triggers (Irrigation AI, Weather advisories, Security events).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models import Notification, NotificationPreference, User
from backend.app.services.email_service import EmailService
from backend.app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

# Deduplication / cooldown window for weather advisories
WEATHER_ALERT_COOLDOWN_HOURS = 6


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        type: str,
        title: str,
        message: str,
        delivery_channel: str = "IN_APP",
        delivery_status: str = "DELIVERED",
    ) -> Notification:
        """
        Creates a new notification record for a user.
        """
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            is_read=False,
            delivery_channel=delivery_channel,
            delivery_status=delivery_status,
            created_at=datetime.utcnow(),
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """
        Returns the number of unread notifications for a user.
        """
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .count()
        )

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Fetches notification records for a user, sorted newest first.
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    @classmethod
    def get_paginated_notifications(
        cls,
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Fetches paginated notifications metadata and payload for the user API.
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)

        total = query.count()
        unread_count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .count()
        )
        items = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "unread_count": unread_count,
            "limit": limit,
            "offset": offset,
            "notifications": [n.to_dict() for n in items],
        }

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        """
        Marks a specific notification as read by the owner user.
        """
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """
        Marks all unread notifications for a user as read.
        Returns the number of notifications updated.
        """
        now = datetime.utcnow()
        count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({"is_read": True, "read_at": now}, synchronize_session="fetch")
        )
        db.commit()
        return count

    @staticmethod
    def get_or_create_preferences(db: Session, user_id: int) -> NotificationPreference:
        """
        Gets existing notification preferences or initializes default settings.
        """
        pref = (
            db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .first()
        )
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                email_enabled=True,
                irrigation_alerts=True,
                disease_alerts=True,
                security_alerts=True,
                weather_alerts=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @classmethod
    def update_preferences(
        cls,
        db: Session,
        user_id: int,
        email_enabled: Optional[bool] = None,
        irrigation_alerts: Optional[bool] = None,
        disease_alerts: Optional[bool] = None,
        security_alerts: Optional[bool] = None,
        weather_alerts: Optional[bool] = None,
    ) -> NotificationPreference:
        """
        Updates user notification preference flags and logs an audit event.
        """
        pref = cls.get_or_create_preferences(db, user_id)
        if email_enabled is not None:
            pref.email_enabled = email_enabled
        if irrigation_alerts is not None:
            pref.irrigation_alerts = irrigation_alerts
        if disease_alerts is not None:
            pref.disease_alerts = disease_alerts
        if security_alerts is not None:
            pref.security_alerts = security_alerts
        if weather_alerts is not None:
            pref.weather_alerts = weather_alerts

        pref.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(pref)

        AuditService.log_audit_event(
            db=db,
            action="notification_preferences_updated",
            entity_type="notification_preference",
            user_id=user_id,
            entity_id=pref.id,
            status="SUCCESS",
            metadata={
                "email_enabled": pref.email_enabled,
                "irrigation_alerts": pref.irrigation_alerts,
                "weather_alerts": pref.weather_alerts,
            },
        )

        return pref

    @classmethod
    def generate_irrigation_alert(
        cls,
        db: Session,
        user: User,
        crop_type: str,
        recommendation_status: str,
        priority: str,
        reason: str,
        farm_name: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Generates an irrigation alert if the farmer has enabled irrigation alerts.
        Dispatches an email if priority is HIGH and email_enabled is True.
        """
        prefs = cls.get_or_create_preferences(db, user.id)
        if not prefs.irrigation_alerts:
            return None

        is_high = priority.upper() == "HIGH"
        title = f"High-priority irrigation alert: {crop_type}" if is_high else f"Irrigation recommended: {crop_type}"
        
        farm_context = f" on {farm_name}" if farm_name else ""
        message = f"Field analysis for {crop_type}{farm_context} indicates {recommendation_status.lower().replace('_', ' ')}. {reason}"

        delivery_channel = "IN_APP"
        delivery_status = "DELIVERED"

        if is_high and prefs.email_enabled and user.email:
            delivery_channel = "BOTH"
            email_sent = EmailService.send_alert_email(
                to_email=user.email,
                full_name=user.full_name or "Farmer",
                title=title,
                message=message,
                alert_type="IRRIGATION_ALERT",
            )
            delivery_status = "EMAIL_SENT" if email_sent else "EMAIL_FAILED"

        notification = cls.create_notification(
            db=db,
            user_id=user.id,
            type="IRRIGATION_ALERT",
            title=title,
            message=message,
            delivery_channel=delivery_channel,
            delivery_status=delivery_status,
        )

        if is_high:
            AuditService.log_audit_event(
                db=db,
                action="high_priority_alert_created",
                entity_type="notification",
                user_id=user.id,
                entity_id=notification.id,
                status="SUCCESS",
                metadata={"crop_type": crop_type, "priority": priority, "channel": delivery_channel},
            )

        return notification

    @classmethod
    def generate_weather_advisory(
        cls,
        db: Session,
        user: User,
        weather_data: Dict[str, Any],
        farm_name: Optional[str] = None,
    ) -> List[Notification]:
        """
        Evaluates real weather metrics against conservative thresholds and creates
        farm weather advisories with a 6-hour deduplication / cooldown window.
        """
        prefs = cls.get_or_create_preferences(db, user.id)
        if not prefs.weather_alerts:
            return []

        temp = float(weather_data.get("temperature", 0))
        precip = float(weather_data.get("precipitation", 0))
        wind = float(weather_data.get("wind_speed", 0))

        advisories = []

        # Threshold 1: Extreme High Temperature (>= 38°C)
        if temp >= 38.0:
            advisories.append({
                "title": "Farm weather advisory: High temperature warning",
                "message": f"Current temperature of {temp}°C exceeds 38°C threshold. Monitor soil evapotranspiration and crop heat stress.",
            })

        # Threshold 2: Heavy Precipitation (>= 20mm)
        if precip >= 20.0:
            advisories.append({
                "title": "Farm weather advisory: Heavy precipitation warning",
                "message": f"Precipitation of {precip} mm recorded. Consider delaying scheduled irrigation and checking field drainage.",
            })

        # Threshold 3: Strong Wind (>= 35 km/h)
        if wind >= 35.0:
            advisories.append({
                "title": "Farm weather advisory: High wind advisory",
                "message": f"Wind speeds of {wind} km/h recorded. Exercise caution with high-clearance machinery and aerial crop spraying.",
            })

        created_notifications = []
        cooldown_cutoff = datetime.utcnow() - timedelta(hours=WEATHER_ALERT_COOLDOWN_HOURS)

        for adv in advisories:
            # Check for identical recent advisory for this user within cooldown window
            recent_duplicate = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user.id,
                    Notification.type == "WEATHER",
                    Notification.title == adv["title"],
                    Notification.created_at >= cooldown_cutoff,
                )
                .first()
            )

            if not recent_duplicate:
                n = cls.create_notification(
                    db=db,
                    user_id=user.id,
                    type="WEATHER",
                    title=adv["title"],
                    message=adv["message"],
                    delivery_channel="IN_APP",
                    delivery_status="DELIVERED",
                )
                created_notifications.append(n)

        return created_notifications

    @classmethod
    def generate_security_notification(
        cls,
        db: Session,
        user: User,
        event_type: str,
        details: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Generates security and account lifecycle in-app notifications.
        Dispatches email for password changes if email_enabled is True.
        """
        prefs = cls.get_or_create_preferences(db, user.id)
        if not prefs.security_alerts:
            return None

        title = "Security Alert"
        message = ""
        send_email = False

        if event_type == "login_success":
            title = "New login to your Harvesta account"
            message = details or "A successful login to your Harvesta account was recorded. If this was not you, reset your password immediately."
            send_email = True
        elif event_type == "email_verified":
            title = "Email address verified"
            message = "Your email address has been verified successfully. Your Harvesta farmer account is fully active."
        elif event_type == "password_reset_completed":
            title = "Password reset successful"
            message = "Your account password was updated successfully. If you did not initiate this change, contact support immediately."
            send_email = True
        elif event_type == "admin_role_promoted":
            title = "Administrator privileges granted"
            message = "Your account was granted administrator access. You can now access Company Analytics from the navigation menu."
        else:
            title = "Account security notice"
            message = details or "An account security event was recorded."

        delivery_channel = "IN_APP"
        delivery_status = "DELIVERED"

        if send_email and prefs.email_enabled and user.email:
            delivery_channel = "BOTH"
            email_sent = EmailService.send_alert_email(
                to_email=user.email,
                full_name=user.full_name or "Farmer",
                title=title,
                message=message,
                alert_type="SECURITY",
            )
            delivery_status = "EMAIL_SENT" if email_sent else "EMAIL_FAILED"

        return cls.create_notification(
            db=db,
            user_id=user.id,
            type="SECURITY",
            title=title,
            message=message,
            delivery_channel=delivery_channel,
            delivery_status=delivery_status,
        )

    @classmethod
    def generate_disease_alert(
        cls,
        db: Session,
        user: User,
        crop_name: str,
        disease_name: str,
        confidence: float,
        farm_name: Optional[str] = None,
        urgency: str = "MEDIUM",
    ) -> Optional[Notification]:
        """
        Generates a crop disease anomaly alert if disease_alerts is enabled in preferences.
        Dispatches email only for high-confidence (>= 0.85) findings if email_enabled is True.
        """
        prefs = cls.get_or_create_preferences(db, user.id)
        if not prefs.disease_alerts:
            return None

        # Do not alert for healthy leaf scans
        if disease_name.lower() == "healthy":
            return None

        conf_pct = int(round(confidence * 100))
        title = f"Possible crop disease detected: {crop_name}"
        farm_context = f" on {farm_name}" if farm_name else ""
        message = (
            f"Image screening on {crop_name}{farm_context} detected symptoms consistent with "
            f"{disease_name} ({conf_pct}% confidence). Inspect field canopy and review agronomic guidelines."
        )

        delivery_channel = "IN_APP"
        delivery_status = "DELIVERED"

        # Only email if high confidence (>= 0.85) and user enabled email
        is_high_conf = confidence >= 0.85
        if is_high_conf and prefs.email_enabled and user.email:
            delivery_channel = "BOTH"
            email_sent = EmailService.send_alert_email(
                to_email=user.email,
                full_name=user.full_name or "Farmer",
                title=title,
                message=message,
                alert_type="DISEASE_ALERT",
            )
            delivery_status = "EMAIL_SENT" if email_sent else "EMAIL_FAILED"

        notification = cls.create_notification(
            db=db,
            user_id=user.id,
            type="DISEASE_ALERT",
            title=title,
            message=message,
            delivery_channel=delivery_channel,
            delivery_status=delivery_status,
        )

        AuditService.log_audit_event(
            db=db,
            action="crop_disease_alert_created",
            entity_type="notification",
            user_id=user.id,
            entity_id=notification.id,
            status="SUCCESS",
            metadata={"crop": crop_name, "disease": disease_name, "confidence": confidence, "urgency": urgency},
        )

        return notification
