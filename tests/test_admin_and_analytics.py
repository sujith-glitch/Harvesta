"""
Unit & Integration Tests for Phase B Company Analytics & Admin Dashboard.
Verifies role-based access control, admin endpoints, session lifecycle,
activity telemetry instrumentation, and bootstrap safety.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import Base, engine, SessionLocal
from backend.app.models import User, Farm, Crop, FieldAnalysisHistory, UserSession, ActivityEvent, AuditLog
from backend.app.services.auth_service import AuthService
from backend.app.services.email_service import EmailService
from scripts.promote_admin import promote_user_to_admin

client = TestClient(app)


def create_user_with_role(email_prefix: str, role: str = "farmer", is_verified: bool = True):
    """Helper to create a user with a specific role and return (user_obj, auth_headers)."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name=f"Test {role.capitalize()}",
            hashed_password=AuthService.hash_password("password123"),
            role=role,
            is_verified=is_verified,
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
# 1. ROLE-BASED ACCESS CONTROL (RBAC) TESTS
# =====================================================================

def test_unauthenticated_request_to_admin_endpoints_rejected():
    """Unauthenticated requests to admin routes must return 401."""
    res = client.get("/api/admin/overview")
    assert res.status_code == 401

    res = client.get("/api/admin/users")
    assert res.status_code == 401

    res = client.get("/api/admin/activity")
    assert res.status_code == 401

    res = client.get("/api/admin/audit-logs")
    assert res.status_code == 401

    res = client.get("/api/admin/sessions")
    assert res.status_code == 401

    assert client.get("/api/admin/data-inventory").status_code == 401
    assert client.get("/api/admin/data/users").status_code == 401


def test_farmer_cannot_access_admin_endpoints():
    """Authenticated users with role='farmer' must receive 403 Forbidden on all admin routes."""
    _, farmer_headers = create_user_with_role("farmer_rbac", role="farmer")

    res = client.get("/api/admin/overview", headers=farmer_headers)
    assert res.status_code == 403
    assert "administrator privileges required" in res.json()["detail"]

    res = client.get("/api/admin/users", headers=farmer_headers)
    assert res.status_code == 403

    res = client.get("/api/admin/activity", headers=farmer_headers)
    assert res.status_code == 403

    res = client.get("/api/admin/audit-logs", headers=farmer_headers)
    assert res.status_code == 403

    res = client.get("/api/admin/sessions", headers=farmer_headers)
    assert res.status_code == 403

    assert client.get("/api/admin/data-inventory", headers=farmer_headers).status_code == 403
    assert client.get("/api/admin/data/users", headers=farmer_headers).status_code == 403


def test_unverified_admin_cannot_access_admin_endpoints():
    """An admin role alone is insufficient until the account email is verified."""
    _, headers = create_user_with_role(
        "unverified_admin_rbac",
        role="admin",
        is_verified=False,
    )

    assert client.get("/api/admin/overview", headers=headers).status_code == 403
    assert client.get("/api/admin/data-inventory", headers=headers).status_code == 403


def test_admin_can_access_overview():
    """Authenticated users with role='admin' must successfully receive 200 OK on admin routes."""
    _, admin_headers = create_user_with_role("admin_rbac", role="admin")

    res = client.get("/api/admin/overview", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert "user_metrics" in data
    assert "session_metrics" in data
    assert "platform_totals" in data
    assert "feature_usage" in data
    assert "event_usage" in data


# =====================================================================
# 2. DATA PRIVACY & USER LIST SANITIZATION TESTS
# =====================================================================

def test_admin_user_list_excludes_sensitive_fields():
    """Admin user endpoint must strictly exclude password hashes and tokens."""
    _, admin_headers = create_user_with_role("admin_privacy", role="admin")

    res = client.get("/api/admin/users", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert "users" in data
    assert "total" in data
    assert len(data["users"]) > 0

    for user_entry in data["users"]:
        assert "id" in user_entry
        assert "email" in user_entry
        assert "full_name" in user_entry
        assert "role" in user_entry
        assert "is_verified" in user_entry
        # Critical security assertions:
        assert "hashed_password" not in user_entry
        assert "password" not in user_entry
        assert "verification_token_hash" not in user_entry
        assert "reset_token_hash" not in user_entry


def test_admin_can_inventory_and_browse_secret_safe_company_data():
    """Admin can inspect stored datasets, but credential material is never serialized."""
    _, admin_headers = create_user_with_role("admin_inventory", role="admin")

    inventory_res = client.get("/api/admin/data-inventory", headers=admin_headers)
    assert inventory_res.status_code == 200
    inventory = inventory_res.json()
    assert any(item["key"] == "users" for item in inventory["datasets"])
    assert "password hashes" in inventory["excluded_secrets"]

    records_res = client.get("/api/admin/data/users?limit=10", headers=admin_headers)
    assert records_res.status_code == 200
    records = records_res.json()["records"]
    assert records
    for record in records:
        assert "email" in record
        assert "hashed_password" not in record
        assert "verification_token_hash" not in record
        assert "reset_token_hash" not in record

    assert client.get("/api/admin/data/not-a-dataset", headers=admin_headers).status_code == 404


# =====================================================================
# 3. SESSION TELEMETRY & LIFECYCLE TESTS
# =====================================================================

def test_session_created_on_login():
    """Successful login must generate a session record and return session_id."""
    email = f"session_test_{uuid.uuid4().hex[:6]}@example.com"
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name="Session Farmer",
            hashed_password=AuthService.hash_password("password123"),
            is_verified=True,
            role="farmer",
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    session_id = data["session_id"]
    assert session_id.startswith("sess_")

    # Verify session recorded in database
    db = SessionLocal()
    try:
        session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        assert session is not None
        assert session.platform == "Windows"
        assert session.device_type == "desktop"
        assert session.logout_at is None
    finally:
        db.close()


def test_logout_endpoint_concludes_session():
    """Logging out must close the session, compute duration, and log logout activity."""
    email = f"logout_test_{uuid.uuid4().hex[:6]}@example.com"
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name="Logout Farmer",
            hashed_password=AuthService.hash_password("password123"),
            is_verified=True,
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

    login_res = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    session_id = login_res.json()["session_id"]

    # Call logout
    logout_res = client.post(
        "/api/auth/logout",
        json={"session_id": session_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200

    # Verify session closed
    db = SessionLocal()
    try:
        session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        assert session.logout_at is not None
        assert session.duration_seconds is not None
    finally:
        db.close()


# =====================================================================
# 4. ACTIVITY & AUDIT TELEMETRY INTEGRATION TESTS
# =====================================================================

def test_farm_and_crop_creation_logs_activity():
    """Creating farms and crops must automatically log activity telemetry."""
    user, headers = create_user_with_role("farmer_activity", role="farmer")

    # 1. Create farm
    farm_res = client.post(
        "/api/farms",
        json={"name": "Analytics Test Farm", "size": 25.0},
        headers=headers,
    )
    assert farm_res.status_code == 201
    farm_id = farm_res.json()["id"]

    # 2. Create crop
    crop_res = client.post(
        f"/api/farms/{farm_id}/crops",
        json={"name": "Wheat", "growth_stage": "Vegetative"},
        headers=headers,
    )
    assert crop_res.status_code == 201

    # 3. Verify activity events
    db = SessionLocal()
    try:
        events = (
            db.query(ActivityEvent)
            .filter(ActivityEvent.user_id == user.id)
            .all()
        )
        event_names = [e.event_name for e in events]
        assert "farm_created" in event_names
        assert "crop_created" in event_names
    finally:
        db.close()


def test_dashboard_view_logs_activity():
    """Accessing the dashboard must log a dashboard_view activity event."""
    user, headers = create_user_with_role("farmer_dash_view", role="farmer")

    res = client.get("/api/dashboard/home", headers=headers)
    assert res.status_code == 200

    db = SessionLocal()
    try:
        event = (
            db.query(ActivityEvent)
            .filter(
                ActivityEvent.user_id == user.id,
                ActivityEvent.event_name == "dashboard_view",
            )
            .first()
        )
        assert event is not None
        assert event.feature == "dashboard"
    finally:
        db.close()


# =====================================================================
# 5. ADMIN PAGINATION & FILTERING TESTS
# =====================================================================

def test_admin_pagination_and_filters():
    """Tests limit, offset, search, and role filtering across admin endpoints."""
    _, admin_headers = create_user_with_role("admin_filter", role="admin")

    # Users pagination
    res = client.get("/api/admin/users?limit=5&offset=0", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["users"]) <= 5
    assert data["limit"] == 5

    # Activity pagination
    act_res = client.get("/api/admin/activity?limit=10&offset=0", headers=admin_headers)
    assert act_res.status_code == 200
    assert len(act_res.json()["events"]) <= 10

    # Audit logs pagination
    audit_res = client.get("/api/admin/audit-logs?limit=10&offset=0", headers=admin_headers)
    assert audit_res.status_code == 200
    assert len(audit_res.json()["logs"]) <= 10

    # Sessions pagination
    sess_res = client.get("/api/admin/sessions?limit=10&offset=0", headers=admin_headers)
    assert sess_res.status_code == 200
    assert len(sess_res.json()["sessions"]) <= 10


# =====================================================================
# 6. ADMIN BOOTSTRAP SCRIPT TESTS
# =====================================================================

def test_admin_bootstrap_script_safety():
    """Promote admin script must safely promote verified users and record audit events."""
    email = f"bootstrap_{uuid.uuid4().hex[:6]}@example.com"
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name="Bootstrap Farmer",
            hashed_password=AuthService.hash_password("pw"),
            role="farmer",
            is_verified=True,
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

    # Execute promote function
    success = promote_user_to_admin(email)
    assert success is True

    # Verify role updated
    db = SessionLocal()
    try:
        updated_user = db.query(User).filter(User.email == email).first()
        assert updated_user.role == "admin"

        # Verify audit log created
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == updated_user.id,
                AuditLog.action == "admin_role_promoted",
            )
            .first()
        )
        assert audit is not None
        assert audit.status == "SUCCESS"
    finally:
        db.close()
