"""
Unit & Integration Tests for Phase C Notifications & Farm Alert System.
Tests in-app notification center, read state management, user isolation,
notification preferences, and trigger integration with field analysis and security events.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, Notification, NotificationPreference, AuditLog
from backend.app.services.auth_service import AuthService
from backend.app.services.notification_service import NotificationService
from backend.app.services.email_service import EmailService
from backend.app.services.weather_service import WeatherService

client = TestClient(app)


def create_test_farmer(email_prefix: str = "farmer"):
    """Helper to create a verified user and return (user_obj, auth_headers)."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name=f"Farmer {email_prefix.capitalize()}",
            hashed_password=AuthService.hash_password("password123"),
            role="farmer",
            is_verified=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = AuthService.create_access_token(user.id, user.email)
        headers = {"Authorization": f"Bearer {token}"}
        return user, headers
    finally:
        db.close()


# =====================================================================
# 1. AUTHENTICATION & ACCESS CONTROL
# =====================================================================

def test_unauthenticated_notification_endpoints_rejected():
    """Unauthenticated requests to notification routes must return 401."""
    res = client.get("/api/notifications")
    assert res.status_code == 401

    res = client.get("/api/notifications/unread-count")
    assert res.status_code == 401

    res = client.patch("/api/notifications/1/read")
    assert res.status_code == 401

    res = client.post("/api/notifications/mark-all-read")
    assert res.status_code == 401

    res = client.get("/api/notifications/preferences")
    assert res.status_code == 401

    res = client.put("/api/notifications/preferences", json={"email_enabled": False})
    assert res.status_code == 401


# =====================================================================
# 2. NOTIFICATION RETRIEVAL & USER ISOLATION
# =====================================================================

def test_farmer_retrieves_own_notifications_only():
    """Farmers must only receive notifications belonging to their account."""
    user1, headers1 = create_test_farmer("user_one")
    user2, headers2 = create_test_farmer("user_two")

    db = SessionLocal()
    try:
        NotificationService.create_notification(
            db=db,
            user_id=user1.id,
            type="IRRIGATION_ALERT",
            title="User 1 Alert",
            message="Alert message for user 1",
        )
        NotificationService.create_notification(
            db=db,
            user_id=user2.id,
            type="WEATHER",
            title="User 2 Alert",
            message="Alert message for user 2",
        )
    finally:
        db.close()

    # User 1 fetches
    res1 = client.get("/api/notifications", headers=headers1)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] >= 1
    assert all(n["title"] == "User 1 Alert" or "User 2 Alert" not in n["title"] for n in data1["notifications"])

    # User 2 fetches
    res2 = client.get("/api/notifications", headers=headers2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total"] >= 1
    assert all(n["title"] == "User 2 Alert" or "User 1 Alert" not in n["title"] for n in data2["notifications"])


def test_unread_count_endpoint():
    """Unread count endpoint must return accurate counts."""
    user, headers = create_test_farmer("unread_counter")

    db = SessionLocal()
    try:
        NotificationService.create_notification(db, user.id, "TEST", "T1", "M1")
        NotificationService.create_notification(db, user.id, "TEST", "T2", "M2")
    finally:
        db.close()

    res = client.get("/api/notifications/unread-count", headers=headers)
    assert res.status_code == 200
    assert res.json()["unread_count"] >= 2


# =====================================================================
# 3. READ STATE MANAGEMENT & ISOLATION
# =====================================================================

def test_mark_single_notification_as_read():
    """Marking a notification as read updates is_read flag and read_at timestamp."""
    user, headers = create_test_farmer("mark_read")

    db = SessionLocal()
    try:
        notif = NotificationService.create_notification(db, user.id, "TEST", "Read Me", "Message")
        notif_id = notif.id
    finally:
        db.close()

    res = client.patch(f"/api/notifications/{notif_id}/read", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_read"] is True
    assert data["read_at"] is not None


def test_farmer_cannot_mark_other_farmers_notification():
    """Farmers cannot mark another user's notification as read (returns 404)."""
    user1, _ = create_test_farmer("owner_user")
    _, intruder_headers = create_test_farmer("intruder_user")

    db = SessionLocal()
    try:
        notif = NotificationService.create_notification(db, user1.id, "TEST", "Private Alert", "Secret")
        notif_id = notif.id
    finally:
        db.close()

    res = client.patch(f"/api/notifications/{notif_id}/read", headers=intruder_headers)
    assert res.status_code == 404


def test_mark_all_notifications_read():
    """Mark all endpoint updates all unread notifications for authenticated user."""
    user, headers = create_test_farmer("mark_all_read")

    db = SessionLocal()
    try:
        NotificationService.create_notification(db, user.id, "TEST", "A1", "M1")
        NotificationService.create_notification(db, user.id, "TEST", "A2", "M2")
        NotificationService.create_notification(db, user.id, "TEST", "A3", "M3")
    finally:
        db.close()

    res = client.post("/api/notifications/mark-all-read", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["updated_count"] >= 3

    # Check unread count is now 0
    count_res = client.get("/api/notifications/unread-count", headers=headers)
    assert count_res.json()["unread_count"] == 0


# =====================================================================
# 4. NOTIFICATION PREFERENCES
# =====================================================================

def test_notification_preferences_lifecycle():
    """Preferences are initialized with defaults and can be toggled via PUT."""
    user, headers = create_test_farmer("pref_user")

    # 1. Get default preferences
    res = client.get("/api/notifications/preferences", headers=headers)
    assert res.status_code == 200
    prefs = res.json()
    assert prefs["email_enabled"] is True
    assert prefs["irrigation_alerts"] is True
    assert prefs["weather_alerts"] is True
    assert prefs["security_alerts"] is True
    assert prefs["disease_alerts"] is True

    # 2. Update preferences
    update_res = client.put(
        "/api/notifications/preferences",
        json={"email_enabled": False, "weather_alerts": False},
        headers=headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["email_enabled"] is False
    assert updated["weather_alerts"] is False
    assert updated["irrigation_alerts"] is True  # preserved

    # 3. Verify audit log created
    db = SessionLocal()
    try:
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == user.id,
                AuditLog.action == "notification_preferences_updated",
            )
            .first()
        )
        assert audit is not None
        assert audit.status == "SUCCESS"
    finally:
        db.close()


# =====================================================================
# 5. DOMAIN ALERT TRIGGERS (IRRIGATION & WEATHER)
# =====================================================================

def test_field_analysis_triggers_irrigation_notification():
    """Running field analysis with dry soil triggers an irrigation notification."""
    user, headers = create_test_farmer("irrigation_trigger")

    payload = {
        "crop_type": "Tomato",
        "current_soil_moisture": 25.0,
        "soil_ph": 6.5,
        "soil_temperature": 26.0,
    }

    fake_weather = {
        "temperature": 32.0,
        "humidity": 60.0,
        "precipitation": 0.0,
        "wind_speed": 8.0,
    }
    with patch.object(WeatherService, "get_current_weather", return_value=fake_weather):
        res = client.post("/api/ai/field-analysis", json=payload, headers=headers)
    assert res.status_code == 200

    db = SessionLocal()
    try:
        notif = (
            db.query(Notification)
            .filter(
                Notification.user_id == user.id,
                Notification.type == "IRRIGATION_ALERT",
            )
            .first()
        )
        assert notif is not None
        assert "Tomato" in notif.title
        assert notif.is_read is False
    finally:
        db.close()


def test_disabled_irrigation_alerts_suppresses_notification():
    """If farmer disables irrigation_alerts in preferences, no alert is created."""
    user, headers = create_test_farmer("suppressed_user")

    # Disable irrigation alerts
    client.put("/api/notifications/preferences", json={"irrigation_alerts": False}, headers=headers)

    payload = {
        "crop_type": "Maize",
        "current_soil_moisture": 20.0,
        "soil_ph": 6.0,
        "soil_temperature": 25.0,
    }
    fake_weather = {
        "temperature": 32.0,
        "humidity": 60.0,
        "precipitation": 0.0,
        "wind_speed": 8.0,
    }
    with patch.object(WeatherService, "get_current_weather", return_value=fake_weather):
        res = client.post("/api/ai/field-analysis", json=payload, headers=headers)
    assert res.status_code == 200

    db = SessionLocal()
    try:
        notif = (
            db.query(Notification)
            .filter(
                Notification.user_id == user.id,
                Notification.type == "IRRIGATION_ALERT",
            )
            .first()
        )
        assert notif is None
    finally:
        db.close()


def test_weather_advisory_trigger_and_cooldown():
    """Weather advisory is generated for extreme conditions and cooldown window suppresses duplicate."""
    user, _ = create_test_farmer("weather_advisory_user")

    db = SessionLocal()
    try:
        # High temperature threshold test (>= 38°C)
        weather_extreme = {"temperature": 39.5, "precipitation": 0.0, "wind_speed": 10.0}
        advisories_1 = NotificationService.generate_weather_advisory(db, user, weather_extreme)
        assert len(advisories_1) == 1
        assert "High temperature warning" in advisories_1[0].title

        # Immediate repeat within cooldown window should be deduplicated
        advisories_2 = NotificationService.generate_weather_advisory(db, user, weather_extreme)
        assert len(advisories_2) == 0

        # Heavy precipitation threshold test (>= 20mm)
        weather_rain = {"temperature": 28.0, "precipitation": 25.0, "wind_speed": 15.0}
        advisories_3 = NotificationService.generate_weather_advisory(db, user, weather_rain)
        assert len(advisories_3) == 1
        assert "Heavy precipitation warning" in advisories_3[0].title
    finally:
        db.close()


# =====================================================================
# 6. HIGH-PRIORITY EMAIL DISPATCH INTEGRATION
# =====================================================================

def test_high_priority_alert_email_dispatch_with_preferences():
    """High-priority irrigation alerts dispatch email when email_enabled=True."""
    user, _ = create_test_farmer("email_dispatch_user")

    db = SessionLocal()
    try:
        with patch.object(EmailService, "send_alert_email", return_value=True) as mock_send:
            notif = NotificationService.generate_irrigation_alert(
                db=db,
                user=user,
                crop_type="Rice",
                recommendation_status="IRRIGATION_REQUIRED",
                priority="HIGH",
                reason="Severe drought stress detected.",
            )
            assert notif is not None
            assert notif.delivery_channel == "BOTH"
            assert notif.delivery_status == "EMAIL_SENT"
            mock_send.assert_called_once()
    finally:
        db.close()
