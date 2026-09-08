"""
Unit & Integration Tests for Phase D Crop Disease Vision AI.
Covers image validation, ML diagnostic inference, database persistence,
user isolation, history endpoints, notification triggers, and security controls.
"""

import io
import os
import sys
import uuid
from datetime import datetime
from unittest.mock import patch
from PIL import Image

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, Farm, Crop, CropDiseaseScan, Notification, ActivityEvent, AuditLog
from backend.app.services.auth_service import AuthService
from backend.app.services.disease_service import DiseaseService
from backend.app.services.image_storage_service import ImageStorageService
from backend.app.services.notification_service import NotificationService
from ml.disease.prepare_dataset import generate_synthetic_leaf_sample
import numpy as np

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


def generate_test_image_bytes(class_name: str = "Tomato___Early_Blight", format: str = "JPEG") -> bytes:
    """Generates synthetic image bytes in memory for testing."""
    rng = np.random.RandomState(42)
    img = generate_synthetic_leaf_sample(class_name, rng)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


# =====================================================================
# 1. AUTHENTICATION & ACCESS CONTROL
# =====================================================================

def test_unauthenticated_disease_scan_rejected():
    """Unauthenticated requests to disease scan endpoints must return 401."""
    img_bytes = generate_test_image_bytes()
    files = {"file": ("leaf.jpg", img_bytes, "image/jpeg")}

    res = client.post("/api/ai/disease-scan", files=files)
    assert res.status_code == 401

    res = client.get("/api/disease-scans")
    assert res.status_code == 401

    res = client.get("/api/disease-scans/1")
    assert res.status_code == 401

    res = client.delete("/api/disease-scans/1")
    assert res.status_code == 401


# =====================================================================
# 2. IMAGE UPLOAD VALIDATION & SECURITY
# =====================================================================

def test_valid_image_scan_succeeds():
    """Uploading a valid JPEG leaf image returns 200 and diagnosis metadata."""
    user, headers = create_test_farmer("vision_valid")
    img_bytes = generate_test_image_bytes("Tomato___Early_Blight")
    files = {"file": ("tomato_leaf.jpg", img_bytes, "image/jpeg")}

    res = client.post("/api/ai/disease-scan", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "id" in data
    assert "predicted_crop" in data
    assert "predicted_disease" in data
    assert "confidence" in data
    assert data["confidence"] > 0.0
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0
    assert "disclaimer" in data
    assert "model_version" in data
    assert data["image_path"].startswith("uploads/disease_scans/")


def test_unsupported_file_format_rejected():
    """Uploading a non-image file (e.g. text/pdf) must return 400 Bad Request."""
    user, headers = create_test_farmer("vision_bad_mime")
    files = {"file": ("document.txt", b"Hello text content", "text/plain")}

    res = client.post("/api/ai/disease-scan", files=files, headers=headers)
    assert res.status_code == 400
    assert "Unsupported image" in res.json()["detail"] or "MIME" in res.json()["detail"]


def test_empty_image_upload_rejected():
    """Uploading an empty 0-byte file must return 400 Bad Request."""
    user, headers = create_test_farmer("vision_empty")
    files = {"file": ("empty.jpg", b"", "image/jpeg")}

    res = client.post("/api/ai/disease-scan", files=files, headers=headers)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_oversized_image_rejected():
    """Uploading an image exceeding 5MB must return 400 Bad Request."""
    user, headers = create_test_farmer("vision_oversize")
    large_bytes = b"0" * (6 * 1024 * 1024)  # 6 MB
    files = {"file": ("large.jpg", large_bytes, "image/jpeg")}

    res = client.post("/api/ai/disease-scan", files=files, headers=headers)
    assert res.status_code == 400
    assert "exceeds" in res.json()["detail"].lower() or "5.0 mb" in res.json()["detail"].lower()


def test_corrupted_image_rejected():
    """Uploading corrupted / invalid image bytes must return 400 Bad Request."""
    user, headers = create_test_farmer("vision_corrupt")
    corrupt_bytes = b"\xFF\xD8\xFF\xE0" + b"random_corrupted_garbage_bytes_12345"
    files = {"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}

    res = client.post("/api/ai/disease-scan", files=files, headers=headers)
    assert res.status_code == 400
    assert "corrupted" in res.json()["detail"].lower() or "unreadable" in res.json()["detail"].lower()


# =====================================================================
# 3. FARM & CROP OWNERSHIP VALIDATION
# =====================================================================

def test_invalid_farm_ownership_rejected():
    """Farmer cannot associate scan with another user's farm ID (returns 404)."""
    user1, _ = create_test_farmer("farm_owner")
    user2, headers2 = create_test_farmer("intruder_farm")

    db = SessionLocal()
    try:
        farm = Farm(user_id=user1.id, name="User1 Farm", size=10.0)
        db.add(farm)
        db.commit()
        farm_id = farm.id
    finally:
        db.close()

    img_bytes = generate_test_image_bytes()
    files = {"file": ("leaf.jpg", img_bytes, "image/jpeg")}
    data = {"farm_id": str(farm_id)}

    res = client.post("/api/ai/disease-scan", files=files, data=data, headers=headers2)
    assert res.status_code == 404
    assert "not found or does not belong" in res.json()["detail"]


def test_invalid_crop_ownership_rejected():
    """Farmer cannot associate scan with another user's crop ID (returns 404)."""
    user1, _ = create_test_farmer("crop_owner")
    user2, headers2 = create_test_farmer("intruder_crop")

    db = SessionLocal()
    try:
        farm = Farm(user_id=user1.id, name="User1 Farm", size=10.0)
        db.add(farm)
        db.commit()
        crop = Crop(farm_id=farm.id, name="Tomato")
        db.add(crop)
        db.commit()
        crop_id = crop.id
    finally:
        db.close()

    img_bytes = generate_test_image_bytes()
    files = {"file": ("leaf.jpg", img_bytes, "image/jpeg")}
    data = {"crop_id": str(crop_id)}

    res = client.post("/api/ai/disease-scan", files=files, data=data, headers=headers2)
    assert res.status_code == 404
    assert "not found or does not belong" in res.json()["detail"]


# =====================================================================
# 4. SCAN PERSISTENCE & HISTORY MANAGEMENT
# =====================================================================

def test_scan_history_pagination_and_isolation():
    """Farmer retrieves only their own scans in paginated order."""
    user1, headers1 = create_test_farmer("history_user1")
    user2, headers2 = create_test_farmer("history_user2")

    img_bytes = generate_test_image_bytes()

    # User 1 performs scan
    res1 = client.post(
        "/api/ai/disease-scan",
        files={"file": ("u1.jpg", img_bytes, "image/jpeg")},
        headers=headers1,
    )
    assert res1.status_code == 200
    scan1_id = res1.json()["id"]

    # User 2 performs scan
    res2 = client.post(
        "/api/ai/disease-scan",
        files={"file": ("u2.jpg", img_bytes, "image/jpeg")},
        headers=headers2,
    )
    assert res2.status_code == 200
    scan2_id = res2.json()["id"]

    # User 1 history query
    hist1 = client.get("/api/disease-scans", headers=headers1)
    assert hist1.status_code == 200
    scans1 = hist1.json()["scans"]
    ids1 = [s["id"] for s in scans1]
    assert scan1_id in ids1
    assert scan2_id not in ids1

    # User 2 history query
    hist2 = client.get("/api/disease-scans", headers=headers2)
    assert hist2.status_code == 200
    scans2 = hist2.json()["scans"]
    ids2 = [s["id"] for s in scans2]
    assert scan2_id in ids2
    assert scan1_id not in ids2


def test_single_scan_retrieval_and_cross_user_block():
    """Retrieving a single scan by ID enforces user isolation."""
    user1, headers1 = create_test_farmer("single_owner")
    user2, headers2 = create_test_farmer("single_intruder")

    img_bytes = generate_test_image_bytes()
    scan_res = client.post(
        "/api/ai/disease-scan",
        files={"file": ("scan.jpg", img_bytes, "image/jpeg")},
        headers=headers1,
    )
    scan_id = scan_res.json()["id"]

    # Owner can fetch
    get_res = client.get(f"/api/disease-scans/{scan_id}", headers=headers1)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == scan_id

    # Intruder is blocked (404)
    intruder_res = client.get(f"/api/disease-scans/{scan_id}", headers=headers2)
    assert intruder_res.status_code == 404


def test_delete_scan_and_image_file():
    """Deleting a scan removes database record and disk file."""
    user, headers = create_test_farmer("delete_scan_user")

    img_bytes = generate_test_image_bytes()
    scan_res = client.post(
        "/api/ai/disease-scan",
        files={"file": ("to_delete.jpg", img_bytes, "image/jpeg")},
        headers=headers,
    )
    scan_id = scan_res.json()["id"]
    image_key = scan_res.json()["image_path"]

    abs_path = ImageStorageService.get_absolute_image_path(image_key)
    assert abs_path is not None
    assert os.path.exists(abs_path)

    # Delete scan
    del_res = client.delete(f"/api/disease-scans/{scan_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Verify deleted from DB
    db = SessionLocal()
    try:
        assert db.query(CropDiseaseScan).filter(CropDiseaseScan.id == scan_id).first() is None
    finally:
        db.close()

    # Verify file removed from disk
    assert not os.path.exists(abs_path)


def test_cross_user_delete_blocked():
    """User B cannot delete User A's scan (returns 404)."""
    user1, headers1 = create_test_farmer("del_owner")
    user2, headers2 = create_test_farmer("del_intruder")

    img_bytes = generate_test_image_bytes()
    scan_res = client.post(
        "/api/ai/disease-scan",
        files={"file": ("owner_leaf.jpg", img_bytes, "image/jpeg")},
        headers=headers1,
    )
    scan_id = scan_res.json()["id"]

    # Intruder attempt
    del_res = client.delete(f"/api/disease-scans/{scan_id}", headers=headers2)
    assert del_res.status_code == 404


# =====================================================================
# 5. NOTIFICATION INTEGRATION & TELEMETRY
# =====================================================================

def test_disease_notification_triggered_on_anomaly():
    """Scanning diseased leaf triggers in-app notification when preference enabled."""
    user, headers = create_test_farmer("notif_disease_user")

    img_bytes = generate_test_image_bytes("Tomato___Late_Blight")
    scan_res = client.post(
        "/api/ai/disease-scan",
        files={"file": ("late_blight.jpg", img_bytes, "image/jpeg")},
        headers=headers,
    )
    assert scan_res.status_code == 200

    db = SessionLocal()
    try:
        notif = (
            db.query(Notification)
            .filter(
                Notification.user_id == user.id,
                Notification.type == "DISEASE_ALERT",
            )
            .first()
        )
        assert notif is not None
        assert "Possible crop disease detected:" in notif.title
        assert notif.is_read is False
    finally:
        db.close()


def test_uncertain_disease_screening_requires_review_without_alert():
    """Low-confidence screening is stored for review but must not create a disease alert."""
    user, headers = create_test_farmer("uncertain_disease_user")
    fake_prediction = {
        "class_key": "Tomato___Early_Blight",
        "display_name": "Possible Tomato Early Blight",
        "predicted_crop": "Tomato",
        "predicted_disease": "Early Blight",
        "is_healthy": False,
        "urgency": "REVIEW",
        "confidence": 0.31,
        "confidence_threshold": 0.65,
        "screening_status": "review_required",
        "description": "The image does not match one supported class with enough confidence.",
        "recommendations": ["Retake a clear photo.", "Ask a local agronomist."],
        "recommendation_summary": "Retake a clear photo. Ask a local agronomist.",
        "top_predictions": [],
        "model_version": "harvesta-disease-vision-v1.0",
        "disclaimer": "Prototype screening only.",
    }
    files = {"file": ("uncertain.jpg", generate_test_image_bytes(), "image/jpeg")}
    with patch.object(DiseaseService, "predict_image", return_value=fake_prediction):
        response = client.post("/api/ai/disease-scan", files=files, headers=headers)

    assert response.status_code == 200
    assert response.json()["screening_status"] == "review_required"
    db = SessionLocal()
    try:
        assert (
            db.query(Notification)
            .filter(Notification.user_id == user.id, Notification.type == "DISEASE_ALERT")
            .count()
            == 0
        )
    finally:
        db.close()


def test_disease_notification_suppressed_when_preference_disabled():
    """Disabling disease_alerts preference suppresses notification generation."""
    user, headers = create_test_farmer("suppressed_disease_user")

    # Disable disease alerts in preferences
    client.put("/api/notifications/preferences", json={"disease_alerts": False}, headers=headers)

    img_bytes = generate_test_image_bytes("Tomato___Early_Blight")
    scan_res = client.post(
        "/api/ai/disease-scan",
        files={"file": ("blight.jpg", img_bytes, "image/jpeg")},
        headers=headers,
    )
    assert scan_res.status_code == 200

    db = SessionLocal()
    try:
        notif = (
            db.query(Notification)
            .filter(
                Notification.user_id == user.id,
                Notification.type == "DISEASE_ALERT",
            )
            .first()
        )
        assert notif is None
    finally:
        db.close()


def test_disease_scan_logs_activity_event():
    """Disease scan creates an activity_event telemetry record."""
    user, headers = create_test_farmer("activity_disease_user")

    img_bytes = generate_test_image_bytes()
    scan_res = client.post(
        "/api/ai/disease-scan",
        files={"file": ("activity_leaf.jpg", img_bytes, "image/jpeg")},
        headers=headers,
    )
    assert scan_res.status_code == 200

    db = SessionLocal()
    try:
        act = (
            db.query(ActivityEvent)
            .filter(
                ActivityEvent.user_id == user.id,
                ActivityEvent.event_name == "disease_scan",
            )
            .first()
        )
        assert act is not None
        assert act.feature == "crop_disease_ai"
        assert act.event_metadata["scan_id"] is not None
    finally:
        db.close()


# =====================================================================
# 6. IMAGE STREAMING & TRAVERSAL SAFETY
# =====================================================================

def test_safe_image_stream_endpoint():
    """Owner can stream stored scan image."""
    user, headers = create_test_farmer("stream_owner")

    img_bytes = generate_test_image_bytes()
    scan_res = client.post(
        "/api/ai/disease-scan",
        files={"file": ("stream.jpg", img_bytes, "image/jpeg")},
        headers=headers,
    )
    scan_id = scan_res.json()["id"]

    stream_res = client.get(f"/api/disease-scans/{scan_id}/image", headers=headers)
    assert stream_res.status_code == 200
    assert stream_res.headers["content-type"] == "image/jpeg"
    assert len(stream_res.content) > 0


def test_image_storage_traversal_protection():
    """Path traversal attempt in storage key resolution is rejected."""
    bad_key = "uploads/disease_scans/../../../../etc/passwd"
    abs_path = ImageStorageService.get_absolute_image_path(bad_key)
    # Must either be None or safely sanitized to local upload dir
    if abs_path is not None:
        assert abs_path.startswith(os.path.abspath(ImageStorageService.ensure_upload_dir()))


# =====================================================================
# 7. SUPABASE SERVER-KEY COMPATIBILITY
# =====================================================================

def test_modern_supabase_secret_key_is_preferred_and_not_used_as_bearer(monkeypatch):
    """Current sb_secret keys use apikey and take precedence over legacy keys."""
    monkeypatch.setenv("SUPABASE_STORAGE_ENABLED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_current_test_key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "legacy.test.key")

    enabled, _, key, _ = ImageStorageService._cloud_config()
    headers = ImageStorageService._cloud_auth_headers(key)

    assert enabled is True
    assert key == "sb_secret_current_test_key"
    assert headers == {"apikey": "sb_secret_current_test_key"}


def test_legacy_supabase_service_role_key_remains_supported(monkeypatch):
    """Existing deployments can transition without breaking Storage access."""
    monkeypatch.setenv("SUPABASE_STORAGE_ENABLED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "legacy.test.key")

    enabled, _, key, _ = ImageStorageService._cloud_config()
    headers = ImageStorageService._cloud_auth_headers(key)

    assert enabled is True
    assert headers["apikey"] == "legacy.test.key"
    assert headers["Authorization"] == "Bearer legacy.test.key"
