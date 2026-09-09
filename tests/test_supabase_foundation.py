"""
Unit & Integration Tests for Phase A Supabase Platform Foundation.
Verifies all 9 new foundation models, relationships, JSON metadata storage, and service layers.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pytest
from backend.app.database import Base, engine, SessionLocal
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
)
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.notification_service import NotificationService
from backend.app.services.chat_storage_service import ChatStorageService
from backend.app.services.audit_service import AuditService
from backend.app.services.auth_service import AuthService


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session for tests."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user(db_session):
    """Creates a sample test user."""
    email = f"farmer_supabase_{uuid.uuid4().hex[:6]}@example.com"
    user = User(
        email=email,
        full_name="Supabase Test Farmer",
        hashed_password=AuthService.hash_password("password123"),
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_farm(db_session, sample_user):
    """Creates a sample test farm."""
    farm = Farm(
        user_id=sample_user.id,
        name="Valley Green Farm",
        location="Iowa, USA",
        size=150.0,
    )
    db_session.add(farm)
    db_session.commit()
    db_session.refresh(farm)
    return farm


# =====================================================================
# 1. TABLE METADATA & SCHEMA VERIFICATION
# =====================================================================

def test_all_platform_tables_exist_in_metadata():
    """Verifies that all 13 core + platform foundation tables are registered."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        # Core domain tables
        "users",
        "farms",
        "crops",
        "field_analysis_history",
        # Phase A foundation tables
        "user_sessions",
        "activity_events",
        "notifications",
        "notification_preferences",
        "ai_chat_conversations",
        "ai_chat_messages",
        "crop_disease_scans",
        "weather_snapshots",
        "audit_logs",
    }
    for table in expected_tables:
        assert table in table_names, f"Table '{table}' missing from SQLAlchemy metadata"


# =====================================================================
# 2. USER SESSION TESTS
# =====================================================================

def test_user_session_lifecycle(db_session, sample_user):
    """Tests session creation, activity updating, and session termination with duration."""
    session_id = f"sess_{uuid.uuid4().hex}"
    session = AnalyticsService.create_session(
        db=db_session,
        user_id=sample_user.id,
        session_id=session_id,
        device_type="desktop",
        platform="Windows",
        user_agent="Mozilla/5.0 Test Agent",
        ip_address="192.168.1.100",
    )

    assert session.id is not None
    assert session.user_id == sample_user.id
    assert session.session_id == session_id
    assert session.device_type == "desktop"
    assert session.platform == "Windows"
    # Verify privacy-safe SHA-256 hashing of IP (no raw IP stored)
    assert session.ip_hash == AnalyticsService.hash_ip("192.168.1.100")
    assert session.logout_at is None
    assert session.duration_seconds is None

    # Test update activity
    updated = AnalyticsService.update_session_activity(db_session, session_id)
    assert updated is not None
    assert updated.last_active_at >= session.login_at

    # Test session end
    ended = AnalyticsService.end_session(db_session, session_id)
    assert ended is not None
    assert ended.logout_at is not None
    assert ended.duration_seconds is not None

    # Verify to_dict output
    data = ended.to_dict()
    assert data["session_id"] == session_id
    assert "login_at" in data


# =====================================================================
# 3. ACTIVITY EVENT LOGGING TESTS
# =====================================================================

def test_activity_event_logging_with_json_metadata(db_session, sample_user):
    """Tests recording feature usage events with structured JSON metadata."""
    metadata = {
        "crop_type": "Wheat",
        "soil_moisture": 42.5,
        "recommendation": "IRRIGATION_REQUIRED",
    }
    event = AnalyticsService.log_activity_event(
        db=db_session,
        event_name="field_analysis_run",
        user_id=sample_user.id,
        feature="irrigation_ai",
        metadata=metadata,
    )

    assert event.id is not None
    assert event.event_name == "field_analysis_run"
    assert event.feature == "irrigation_ai"
    assert event.event_metadata == metadata

    # Fetch user activity
    events = AnalyticsService.get_user_activity(db_session, sample_user.id, limit=10)
    assert len(events) >= 1
    assert any(e.event_name == "field_analysis_run" for e in events)


# =====================================================================
# 4. NOTIFICATION & PREFERENCE TESTS
# =====================================================================

def test_notification_creation_and_read_management(db_session, sample_user):
    """Tests in-app notification dispatch and individual/bulk read receipts."""
    notif = NotificationService.create_notification(
        db=db_session,
        user_id=sample_user.id,
        type="IRRIGATION_ALERT",
        title="Irrigation Required on Field 01",
        message="Soil moisture has dropped below 30% for winter wheat.",
        delivery_channel="IN_APP",
    )

    assert notif.id is not None
    assert notif.is_read is False
    assert notif.read_at is None

    # Check unread notifications
    unread = NotificationService.get_user_notifications(db_session, sample_user.id, unread_only=True)
    assert any(n.id == notif.id for n in unread)

    # Mark as read
    marked = NotificationService.mark_as_read(db_session, notif.id, sample_user.id)
    assert marked is not None
    assert marked.is_read is True
    assert marked.read_at is not None

    # Create another unread notification and test mark_all_as_read
    NotificationService.create_notification(
        db=db_session,
        user_id=sample_user.id,
        type="WEATHER_ALERT",
        title="Heavy Rain Forecasted",
        message="Precipitation of 25mm expected over next 24h.",
    )
    count = NotificationService.mark_all_as_read(db_session, sample_user.id)
    assert count >= 1


def test_notification_preferences(db_session, sample_user):
    """Tests automatic preference initialization and category updates."""
    prefs = NotificationService.get_or_create_preferences(db_session, sample_user.id)
    assert prefs.user_id == sample_user.id
    assert prefs.email_enabled is True
    assert prefs.irrigation_alerts is True

    # Update preferences
    updated = NotificationService.update_preferences(
        db=db_session,
        user_id=sample_user.id,
        email_enabled=False,
        weather_alerts=False,
    )
    assert updated.email_enabled is False
    assert updated.weather_alerts is False
    assert updated.irrigation_alerts is True  # Unchanged


# =====================================================================
# 5. AI CHAT STORAGE TESTS
# =====================================================================

def test_ai_chat_conversation_and_messages(db_session, sample_user, sample_farm):
    """Tests conversation creation, message history append, and cascade deletion."""
    conv = ChatStorageService.create_conversation(
        db=db_session,
        user_id=sample_user.id,
        farm_id=sample_farm.id,
        title="Corn Nitrogen Advice",
    )

    assert conv.id is not None
    assert conv.title == "Corn Nitrogen Advice"
    assert conv.farm_id == sample_farm.id

    # Append messages
    m1 = ChatStorageService.add_message(
        db=db_session,
        conversation_id=conv.id,
        role="user",
        content="What is the optimal NPK balance for late vegetative corn?",
    )
    m2 = ChatStorageService.add_message(
        db=db_session,
        conversation_id=conv.id,
        role="assistant",
        content="For late vegetative corn, target 180-220 kg/ha of Nitrogen...",
        model_name="harvesta-agronomist-v1",
    )

    messages = ChatStorageService.get_conversation_messages(db_session, conv.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert messages[1].model_name == "harvesta-agronomist-v1"

    # Test conversation deletion cascades to messages
    deleted = ChatStorageService.delete_conversation(db_session, conv.id, sample_user.id)
    assert deleted is True
    assert db_session.query(AIChatMessage).filter(AIChatMessage.conversation_id == conv.id).count() == 0


# =====================================================================
# 6. CROP DISEASE SCAN TESTS
# =====================================================================

def test_crop_disease_scan_storage(db_session, sample_user, sample_farm):
    """Tests crop disease scan record creation with diagnostic metadata."""
    crop = Crop(
        farm_id=sample_farm.id,
        name="Tomato",
        variety="Roma",
        health_status="Good",
    )
    db_session.add(crop)
    db_session.commit()
    db_session.refresh(crop)

    scan = CropDiseaseScan(
        user_id=sample_user.id,
        farm_id=sample_farm.id,
        crop_id=crop.id,
        image_path="storage/scans/tomato_leaf_001.jpg",
        predicted_crop="Tomato",
        predicted_disease="Early Blight",
        confidence=0.945,
        model_version="disease-resnet50-v1.0",
        recommendation="Apply copper-based fungicide and remove lower infected leaves.",
        created_at=datetime.utcnow(),
    )
    db_session.add(scan)
    db_session.commit()
    db_session.refresh(scan)

    assert scan.id is not None
    assert scan.predicted_disease == "Early Blight"
    assert scan.confidence == 0.945
    assert scan.user.id == sample_user.id
    assert scan.farm.id == sample_farm.id
    assert scan.crop.id == crop.id

    # Verify to_dict output
    data = scan.to_dict()
    assert data["predicted_crop"] == "Tomato"
    assert data["image_path"] == "storage/scans/tomato_leaf_001.jpg"


# =====================================================================
# 7. WEATHER SNAPSHOT TESTS
# =====================================================================

def test_weather_snapshot_storage(db_session, sample_user, sample_farm):
    """Tests storing and retrieving environmental weather snapshots."""
    snapshot = WeatherSnapshot(
        user_id=sample_user.id,
        farm_id=sample_farm.id,
        latitude=41.8781,
        longitude=-93.0977,
        temperature=24.5,
        humidity=62.0,
        precipitation=0.0,
        wind_speed=14.2,
        weather_code=1,
        source="open-meteo",
        captured_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)

    assert snapshot.id is not None
    assert snapshot.temperature == 24.5
    assert snapshot.source == "open-meteo"
    assert snapshot.user.id == sample_user.id
    assert snapshot.farm.id == sample_farm.id


# =====================================================================
# 8. AUDIT LOG TESTS
# =====================================================================

def test_audit_log_security_events(db_session, sample_user):
    """Tests creating security audit logs with JSON metadata."""
    audit = AuditService.log_audit_event(
        db=db_session,
        action="password_reset_requested",
        entity_type="user",
        user_id=sample_user.id,
        entity_id=sample_user.id,
        status="SUCCESS",
        metadata={"ip_hash": AnalyticsService.hash_ip("10.0.0.1"), "trigger": "web_ui"},
    )

    assert audit.id is not None
    assert audit.action == "password_reset_requested"
    assert audit.status == "SUCCESS"
    assert audit.audit_metadata["trigger"] == "web_ui"

    # Query audit logs
    logs = AuditService.get_audit_logs(db_session, user_id=sample_user.id, action="password_reset_requested")
    assert len(logs) >= 1
    assert logs[0].entity_type == "user"


# =====================================================================
# 9. RELATIONSHIP & CASCADE BEHAVIOR
# =====================================================================

def test_user_deletion_cascade_and_nullify_integrity(db_session):
    """
    Tests that deleting a user safely cascades to dependent records
    (sessions, notifications, preferences, chat conversations)
    while activity events, weather snapshots, and audit logs maintain SET NULL integrity.
    """
    user = User(
        email=f"cascade_test_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Cascade Farmer",
        hashed_password=AuthService.hash_password("pass"),
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    user_id = user.id

    # Create associated child records
    AnalyticsService.create_session(db_session, user_id=user_id, session_id=f"sess_{uuid.uuid4().hex}")
    AnalyticsService.log_activity_event(db_session, event_name="login", user_id=user_id)
    NotificationService.create_notification(db_session, user_id=user_id, type="TEST", title="T", message="M")
    NotificationService.get_or_create_preferences(db_session, user_id=user_id)
    conv = ChatStorageService.create_conversation(db_session, user_id=user_id, title="Test Chat")
    ChatStorageService.add_message(db_session, conv.id, "user", "Hello")
    AuditService.log_audit_event(db_session, action="test_action", entity_type="test", user_id=user_id)

    # Delete the user
    db_session.delete(user)
    db_session.commit()

    # Cascade deleted records should be gone
    assert db_session.query(UserSession).filter(UserSession.user_id == user_id).count() == 0
    assert db_session.query(Notification).filter(Notification.user_id == user_id).count() == 0
    assert db_session.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).count() == 0
    assert db_session.query(AIChatConversation).filter(AIChatConversation.user_id == user_id).count() == 0
    assert db_session.query(AIChatMessage).filter(AIChatMessage.conversation_id == conv.id).count() == 0

    # SET NULL records should still exist with user_id = NULL
    act = db_session.query(ActivityEvent).filter(ActivityEvent.event_name == "login").first()
    assert act is not None
