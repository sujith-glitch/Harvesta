import os
import sys
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.weather_service import WeatherService
from backend.app.services.email_service import EmailService
from backend.app.database import SessionLocal
from backend.app.models import User, Notification

client = TestClient(app)

MOCK_WEATHER_DATA = {
    "temperature": 30.5,
    "humidity": 55.0,
    "precipitation": 0.0,
    "wind_speed": 10.0
}

def create_verified_user_and_get_headers(email_prefix: str = "verified_farmer"):
    """Helper to create a user, verify email and set password, and return Bearer auth headers."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"
    password = "password123"

    with patch.object(EmailService, 'send_verification_email') as mock_send:
        mock_send.return_value = True
        signup_res = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Farmer John"
        })
        assert signup_res.status_code == 201
        
        # Extract the raw token sent to the email service
        raw_token = mock_send.call_args[0][2]

    # Call verify email endpoint to set password and mark as verified
    verify_res = client.post("/api/auth/verify-email", json={"token": raw_token, "password": password})
    assert verify_res.status_code == 200

    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_signup_creates_unverified_user_and_sends_email():
    """Verify signup creates unverified user and triggers EmailService."""
    email = f"unverified_{uuid.uuid4().hex[:6]}@example.com"

    with patch.object(EmailService, 'send_verification_email') as mock_send:
        mock_send.return_value = True
        signup_res = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Unverified Farmer"
        })
        assert signup_res.status_code == 201
        data = signup_res.json()
        assert data["is_verified"] is False
        assert mock_send.called
        assert mock_send.call_args[0][0] == email
        verification_code = mock_send.call_args[0][2]
        assert len(verification_code) == 4
        assert verification_code.isdigit()


def test_verification_email_uses_plain_text_html_and_standard_headers():
    """Verification mail should be readable without HTML and include standard delivery headers."""
    config = {
        "host": "smtp.test",
        "port": 587,
        "username": "sender@example.com",
        "password": "test-only",
        "from_email": "sender@example.com",
        "from_name": "Harvesta",
        "frontend_url": "http://localhost:5173",
    }
    message = EmailService._build_message(
        config=config,
        to_email="farmer@example.com",
        subject="Verify your email for Harvesta",
        plain_text="Your verification code is 1234.",
        html_content="<p>Your verification code is 1234.</p>",
    )

    assert message["From"] == "Harvesta <sender@example.com>"
    assert message["Reply-To"] == "sender@example.com"
    assert message["Date"]
    assert message["Message-ID"]
    assert [part.get_content_type() for part in message.get_payload()] == ["text/plain", "text/html"]


def test_unverified_user_cannot_login():
    """Verify unverified users are directed back to Gmail verification."""
    email = f"blocked_{uuid.uuid4().hex[:6]}@example.com"
    password = "password123"

    with patch.object(EmailService, 'send_verification_email', return_value=True):
        client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Blocked Farmer"
        })

    # The account state is checked before its temporary random password so the
    # farmer receives the correct next step instead of a misleading password error.
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 403
    assert "not verified" in login_res.json()["detail"].lower()


def test_repeated_signup_recovers_an_unverified_account():
    """Repeating signup must return the farmer to verification, not trap the account."""
    email = f"retry_signup_{uuid.uuid4().hex[:6]}@example.com"
    with patch.object(EmailService, "send_verification_email", return_value=True) as mock_send:
        first = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Retry Farmer",
        })
        second = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Retry Farmer",
        })

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["is_verified"] is False
    assert "waiting for email verification" in second.json()["message"].lower()
    # The second request occurs inside the cooldown and must not send duplicate mail.
    assert mock_send.call_count == 1


def test_email_verification_with_valid_token():
    """Verify valid token marks user verified, sets password and allows login."""
    email = f"verify_me_{uuid.uuid4().hex[:6]}@example.com"
    password = "newpassword123"

    with patch.object(EmailService, 'send_verification_email') as mock_send:
        mock_send.return_value = True
        client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Verify Me"
        })
        raw_token = mock_send.call_args[0][2]

    # Call verify email endpoint to set password
    verify_res = client.post("/api/auth/verify-email", json={"token": raw_token, "password": password})
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "success"

    # User can now login successfully and receives a security email notice.
    with patch.object(EmailService, "send_alert_email", return_value=True) as login_email:
        login_res = client.post("/api/auth/login", json={
            "email": email,
            "password": password
        }, headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0)"})
    assert login_res.status_code == 200
    assert login_res.json()["user"]["is_verified"] is True
    login_email.assert_called_once()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        notice = (
            db.query(Notification)
            .filter(Notification.user_id == user.id, Notification.title == "New login to your Harvesta account")
            .first()
        )
        assert notice is not None
        assert notice.delivery_channel == "BOTH"
        assert "Windows" in notice.message
    finally:
        db.close()


def test_phone_verification_then_original_browser_creates_password():
    """Phone verifies Gmail; only the browser that began signup may create the password."""
    email = f"two_device_{uuid.uuid4().hex[:6]}@example.com"
    password = "newpassword123"

    with patch.object(EmailService, "send_verification_email") as mock_send:
        mock_send.return_value = True
        signup_res = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Two Device Farmer",
        })
        raw_email_token = mock_send.call_args[0][2]

    assert signup_res.status_code == 201
    setup_token = signup_res.json()["setup_token"]
    waiting = client.post("/api/auth/registration-status", json={"setup_token": setup_token})
    assert waiting.status_code == 200
    assert waiting.json()["status"] == "waiting_for_otp"

    # This is the request made by the Gmail link on the phone. It contains no password.
    phone_verify = client.post("/api/auth/verify-email", json={"token": raw_email_token})
    assert phone_verify.status_code == 200
    assert phone_verify.json()["status"] == "email_verified"

    ready = client.post("/api/auth/registration-status", json={"setup_token": setup_token})
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready_for_password"

    # The account cannot log in while password setup is incomplete.
    premature_login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert premature_login.status_code == 403
    assert "create your password" in premature_login.json()["detail"].lower()

    invalid_setup = client.post("/api/auth/complete-registration", json={
        "setup_token": "not-a-valid-registration-token",
        "password": password,
    })
    assert invalid_setup.status_code in {400, 422}

    completed = client.post("/api/auth/complete-registration", json={
        "setup_token": setup_token,
        "password": password,
    })
    assert completed.status_code == 200
    assert completed.json()["status"] == "success"

    complete_status = client.post("/api/auth/registration-status", json={"setup_token": setup_token})
    assert complete_status.status_code == 200
    assert complete_status.json()["status"] == "complete"

    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200


def test_four_digit_otp_then_password_opens_account():
    """The current registration flow verifies an emailed OTP before password creation."""
    email = f"otp_farmer_{uuid.uuid4().hex[:6]}@example.com"
    password = "newpassword123"

    with patch.object(EmailService, "send_verification_email", return_value=True) as mock_send:
        signup_res = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "OTP Farmer",
        })
        verification_code = mock_send.call_args[0][2]

    setup_token = signup_res.json()["setup_token"]
    wrong_code = f"{(int(verification_code) + 1) % 10_000:04d}"
    wrong = client.post("/api/auth/verify-registration-otp", json={
        "setup_token": setup_token,
        "code": wrong_code,
    })
    assert wrong.status_code == 400
    assert "4 attempts remaining" in wrong.json()["detail"]

    verified = client.post("/api/auth/verify-registration-otp", json={
        "setup_token": setup_token,
        "code": verification_code,
    })
    assert verified.status_code == 200
    assert verified.json()["status"] == "ready_for_password"

    completed = client.post("/api/auth/complete-registration", json={
        "setup_token": setup_token,
        "password": password,
    })
    assert completed.status_code == 200

    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200


def test_invalid_and_expired_token_rejection():
    """Verify invalid or expired tokens return HTTP 400 Bad Request."""
    # Invalid token
    res1 = client.post("/api/auth/verify-email", json={"token": "invalid_token_123456", "password": "password123"})
    assert res1.status_code == 400

    # Expired token
    email = f"expired_{uuid.uuid4().hex[:6]}@example.com"
    with patch.object(EmailService, 'send_verification_email', return_value=True):
        client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Expired User"
        })

    raw_token = "expired_token_abc"
    hashed_token = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    user.verification_token_hash = hashed_token
    user.verification_token_expires_at = datetime.utcnow() - timedelta(minutes=10) # Expired 10m ago
    db.commit()
    db.close()

    res2 = client.post("/api/auth/verify-email", json={"token": raw_token, "password": "password123"})
    assert res2.status_code == 400
    assert "expired" in res2.json()["detail"].lower()


def test_resend_verification_and_rate_limiting():
    """Verify resend verification endpoint dispatches email and rate limits requests within 60s."""
    email = f"resend_{uuid.uuid4().hex[:6]}@example.com"
    with patch.object(EmailService, 'send_verification_email', return_value=True):
        client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Resend User"
        })

    with patch.object(EmailService, 'send_verification_email') as mock_send:
        mock_send.return_value = True
        
        # Second immediate request should hit 429 rate limit
        res_limit = client.post("/api/auth/resend-verification", json={"email": email})
        assert res_limit.status_code == 429
        assert "wait" in res_limit.json()["detail"].lower()


def test_unauthenticated_request_rejected():
    """Verify unauthenticated history and dashboard endpoints return 401 Unauthorized."""
    assert client.get("/api/history/field-analysis").status_code == 401
    assert client.get("/api/dashboard/summary").status_code == 401
    assert client.post("/api/history/field-analysis", json={}).status_code == 401
    assert client.delete("/api/history/field-analysis/1").status_code == 401


def test_authenticated_user_can_create_and_retrieve_history():
    """Verify verified authenticated user can save field analysis and retrieve their history."""
    headers = create_verified_user_and_get_headers("history_user1")

    payload = {
        "crop_type": "Tomato",
        "location": {"location_text": "Salem, Tamil Nadu"},
        "weather": {"temperature": 32.0, "humidity": 60.0, "precipitation": 0.0, "wind_speed": 12.0},
        "soil": {"current_soil_moisture": 35.0, "soil_ph": 6.5, "soil_temperature": 30.0},
        "analysis": {
            "status": "IRRIGATION_REQUIRED",
            "priority": "HIGH",
            "reason": "Moisture is low.",
            "factors": ["Low soil moisture.", "High temperature."]
        }
    }

    create_res = client.post("/api/history/field-analysis", json=payload, headers=headers)
    assert create_res.status_code == 201
    history_id = create_res.json()["id"]

    # Retrieve history list
    list_res = client.get("/api/history/field-analysis", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert items[0]["id"] == history_id

    # Retrieve single item by ID
    single_res = client.get(f"/api/history/field-analysis/{history_id}", headers=headers)
    assert single_res.status_code == 200
    assert single_res.json()["id"] == history_id


def test_user_cannot_access_or_delete_another_users_analysis():
    """Verify User A cannot access or delete User B's analysis record (returns 404)."""
    headers_user_a = create_verified_user_and_get_headers("user_a")
    headers_user_b = create_verified_user_and_get_headers("user_b")

    payload = {
        "crop_type": "Rice",
        "location": {"location_text": "Chennai, Tamil Nadu"},
        "weather": {"temperature": 28.0, "humidity": 75.0, "precipitation": 5.0, "wind_speed": 8.0},
        "soil": {"current_soil_moisture": 50.0, "soil_ph": 6.8, "soil_temperature": 26.0},
        "analysis": {
            "status": "NO_IRRIGATION_NEEDED",
            "priority": "LOW",
            "reason": "Recent rain.",
            "factors": ["Rainfall received."]
        }
    }

    # User A creates record
    create_res = client.post("/api/history/field-analysis", json=payload, headers=headers_user_a)
    assert create_res.status_code == 201
    record_id_a = create_res.json()["id"]

    # User B tries to view User A's record -> should fail (404)
    get_b_res = client.get(f"/api/history/field-analysis/{record_id_a}", headers=headers_user_b)
    assert get_b_res.status_code == 404

    # User B tries to delete User A's record -> should fail (404)
    del_b_res = client.delete(f"/api/history/field-analysis/{record_id_a}", headers=headers_user_b)
    assert del_b_res.status_code == 404

    # User A can delete own record successfully -> 200 OK
    del_a_res = client.delete(f"/api/history/field-analysis/{record_id_a}", headers=headers_user_a)
    assert del_a_res.status_code == 200


def test_dashboard_summary_returns_correct_counts():
    """Verify GET /api/dashboard/summary calculates accurate counts for authenticated user."""
    headers = create_verified_user_and_get_headers("summary_user")

    p1 = {
        "crop_type": "Tomato",
        "location": {"location_text": "Coimbatore, Tamil Nadu"},
        "weather": {"temperature": 35.0, "humidity": 45.0, "precipitation": 0.0, "wind_speed": 15.0},
        "soil": {"current_soil_moisture": 25.0, "soil_ph": 6.5, "soil_temperature": 30.0},
        "analysis": {
            "status": "IRRIGATION_REQUIRED",
            "priority": "HIGH",
            "reason": "Low moisture",
            "factors": ["Dry soil"]
        }
    }
    client.post("/api/history/field-analysis", json=p1, headers=headers)

    summary_res = client.get("/api/dashboard/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_analyses"] >= 1
    assert summary["irrigation_required_count"] >= 1
    assert summary["high_priority_count"] >= 1
    assert summary["latest_analysis_timestamp"] is not None


def test_field_analysis_integration_auto_saves_history():
    """Verify POST /api/ai/field-analysis executes real weather analysis and saves history_id."""
    headers = create_verified_user_and_get_headers("field_auto_save")

    payload = {
        "crop_type": "Tomato",
        "current_soil_moisture": 35.0,
        "soil_ph": 6.5,
        "soil_temperature": 30.0
    }

    with patch.object(WeatherService, 'get_current_weather', return_value=MOCK_WEATHER_DATA):
        res = client.post("/api/ai/field-analysis", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "history_id" in data
        assert isinstance(data["history_id"], int)
        assert "prototype_notice" in data
