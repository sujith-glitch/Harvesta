"""Integration coverage for profile, settings, inventory, reports, and language detection."""

import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models import User
from backend.app.services.auth_service import AuthService
from backend.app.services.local_ai_service import LocalAIService


client = TestClient(app)


def _farmer(prefix):
    db = SessionLocal()
    try:
        user = User(
            email=f"{prefix}_{uuid.uuid4().hex[:7]}@example.com",
            full_name="Test Farmer",
            hashed_password=AuthService.hash_password("password123"),
            role="farmer",
            is_verified=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = AuthService.create_access_token(user.id, user.email)
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


def test_profile_and_preferences_are_saved():
    headers = _farmer("profile")
    profile = client.put("/api/account/profile", headers=headers, json={
        "full_name": "Meena Farmer",
        "phone": "+91 9000000000",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "country": "India",
        "primary_crop": "Tomato",
        "experience_years": 8,
        "avatar_color": "#A6BC12",
    })
    assert profile.status_code == 200
    assert profile.json()["full_name"] == "Meena Farmer"
    assert profile.json()["primary_crop"] == "Tomato"

    preferences = client.put("/api/account/preferences", headers=headers, json={
        "language": "ta",
        "theme": "dark",
        "voice_enabled": True,
        "voice_auto_speak": True,
    })
    assert preferences.status_code == 200
    assert preferences.json()["language"] == "ta"
    assert client.get("/api/account/preferences", headers=headers).json()["theme"] == "dark"


def test_profile_colour_survives_reload_and_is_private():
    owner = _farmer("colour_owner")
    stranger = _farmer("colour_stranger")
    changed = client.put("/api/account/profile", headers=owner, json={
        "full_name": "Colour Farmer", "avatar_color": "#123456",
    })
    assert changed.status_code == 200
    reloaded = client.get("/api/account/profile", headers=owner)
    assert reloaded.status_code == 200
    assert reloaded.json()["avatar_color"] == "#123456"
    assert client.get("/api/account/profile", headers=stranger).json()["avatar_color"] == "#A6BC12"
    rejected = client.put("/api/account/profile", headers=owner, json={
        "full_name": "Colour Farmer", "avatar_color": "invalid-colour",
    })
    assert rejected.status_code == 422
    assert client.get("/api/account/profile", headers=owner).json()["avatar_color"] == "#123456"


def test_inventory_is_private_per_farmer_and_supports_crud():
    owner = _farmer("stock_owner")
    stranger = _farmer("stock_stranger")
    created = client.post("/api/inventory", headers=owner, json={
        "name": "Tomato seeds", "category": "Seeds", "quantity": 4,
        "unit": "packets", "low_stock_threshold": 5,
    })
    assert created.status_code == 201
    item = created.json()
    assert item["is_low_stock"] is True
    assert client.get("/api/inventory", headers=owner).json()["total"] == 1
    assert client.get("/api/inventory", headers=stranger).json()["total"] == 0
    assert client.delete(f"/api/inventory/{item['id']}", headers=stranger).status_code == 404
    assert client.delete(f"/api/inventory/{item['id']}", headers=owner).status_code == 200


def test_five_reports_can_be_viewed_and_downloaded():
    headers = _farmer("reports")
    listing = client.get("/api/reports", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()["reports"]) == 5

    detail = client.get("/api/reports/farm-overview", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["key"] == "farm-overview"

    pdf = client.get("/api/reports/farm-overview/download?format=pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")

    csv = client.get("/api/reports/activity-history/download?format=csv", headers=headers)
    assert csv.status_code == 200
    assert "text/csv" in csv.headers["content-type"]


def test_supported_language_detection_including_tanglish():
    assert LocalAIService.detect_language("என் தக்காளி இலைக்கு என்ன நோய்?") == "ta"
    assert LocalAIService.detect_language("ennaku mazhai epadi iruku nu sollu") == "ta"
    assert LocalAIService.detect_language("मेरी फसल को पानी चाहिए?") == "hi"
    assert LocalAIService.detect_language("నా పంటకు నీరు అవసరమా?") == "te"
