import os
import sys
import uuid
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.auth_service import AuthService
from backend.app.services.email_service import EmailService
from backend.app.database import SessionLocal
from backend.app.models import User

client = TestClient(app)

GENERIC_MESSAGE = "If an account exists for this email, a password reset link has been sent."


def create_verified_user(email_prefix: str = "reset_farmer", password: str = "oldpassword123"):
    """Helper to create a verified user with a known password. Returns (email, password)."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"

    with patch.object(EmailService, 'send_verification_email') as mock_send:
        mock_send.return_value = True
        signup_res = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Reset Farmer"
        })
        assert signup_res.status_code == 201
        raw_token = mock_send.call_args[0][2]

    verify_res = client.post("/api/auth/verify-email", json={"token": raw_token, "password": password})
    assert verify_res.status_code == 200
    return email, password


def request_password_reset(email: str):
    """Helper to call forgot-password and return the raw reset token captured from EmailService."""
    with patch.object(EmailService, 'send_password_reset_email') as mock_send:
        mock_send.return_value = True
        res = client.post("/api/auth/forgot-password", json={"email": email})
        raw_token = mock_send.call_args[0][2] if mock_send.called else None
    return res, raw_token


def clear_reset_cooldown(email: str):
    """Bypass the 60-second forgot-password rate limit for a user (test convenience)."""
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.reset_sent_at = datetime.utcnow() - timedelta(seconds=RESET_COOLDOWN_BYPASS)
        db.commit()
    db.close()

RESET_COOLDOWN_BYPASS = 999


def test_forgot_password_existing_email_sends_generic_response():
    """Forgot password for a registered verified email returns generic success message."""
    email, _ = create_verified_user("forgot_existing")
    res, raw_token = request_password_reset(email)

    assert res.status_code == 200
    assert res.json()["message"] == GENERIC_MESSAGE
    # A reset email must actually have been dispatched with the user's email
    assert raw_token is not None


def test_forgot_password_unknown_email_generic_response():
    """Forgot password with unknown email must not reveal account existence."""
    unknown_email = f"ghost_{uuid.uuid4().hex[:6]}@example.com"
    with patch.object(EmailService, 'send_password_reset_email') as mock_send:
        res = client.post("/api/auth/forgot-password", json={"email": unknown_email})

    assert res.status_code == 200
    assert res.json()["message"] == GENERIC_MESSAGE
    assert not mock_send.called


def test_forgot_password_response_identical_for_existing_and_unknown():
    """Both known and unknown emails must produce byte-identical generic responses."""
    email, _ = create_verified_user("forgot_same")
    res_known = client.post("/api/auth/forgot-password", json={"email": email})
    res_unknown = client.post("/api/auth/forgot-password", json={
        "email": f"nobody_{uuid.uuid4().hex[:6]}@example.com"
    })

    assert res_known.json() == res_unknown.json()


def test_forgot_password_stores_hashed_token_not_raw():
    """Database must store only the SHA-256 hash of the reset token, never the raw token."""
    email, _ = create_verified_user("hashed_token")
    res, raw_token = request_password_reset(email)
    assert raw_token is not None

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    expected_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    assert user.reset_token_hash == expected_hash
    assert raw_token.encode('utf-8') not in (user.reset_token_hash or "").encode('utf-8')
    assert user.reset_token_expires_at is not None
    assert user.reset_token_expires_at > datetime.utcnow()
    db.close()


def test_reset_password_with_valid_token_changes_password():
    """Valid reset token updates the password; old fails, new works; token is consumed."""
    email, old_password = create_verified_user("valid_reset")
    res, raw_token = request_password_reset(email)
    assert raw_token is not None

    new_password = "brandnewpassword456"
    reset_res = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "new_password": new_password,
    })
    assert reset_res.status_code == 200
    body = reset_res.json()
    assert body["status"] == "success"
    # Password must never appear in the response
    assert new_password not in str(body)
    assert old_password not in str(body)

    # Old password no longer works
    old_login = client.post("/api/auth/login", json={"email": email, "password": old_password})
    assert old_login.status_code == 401

    # New password works
    new_login = client.post("/api/auth/login", json={"email": email, "password": new_password})
    assert new_login.status_code == 200
    assert new_login.json()["user"]["is_verified"] is True

    # Password was actually changed in DB using existing hashing implementation
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    assert user.hashed_password == AuthService.hash_password(new_password)
    assert user.hashed_password != AuthService.hash_password(old_password)
    db.close()


def test_password_reset_completes_phone_verified_pending_registration():
    """A reset-link password completes setup after Gmail verification on another device."""
    email = f"pending_reset_{uuid.uuid4().hex[:6]}@example.com"
    new_password = "completedthroughreset123"

    with patch.object(EmailService, "send_verification_email") as verification_email:
        verification_email.return_value = True
        signup_res = client.post("/api/auth/signup", json={
            "email": email,
            "full_name": "Pending Reset Farmer",
        })
        raw_verification_token = verification_email.call_args[0][2]
    assert signup_res.status_code == 201

    phone_verify = client.post("/api/auth/verify-email", json={"token": raw_verification_token})
    assert phone_verify.status_code == 200
    assert phone_verify.json()["status"] == "email_verified"

    with patch.object(EmailService, "send_password_reset_email") as reset_email:
        reset_email.return_value = True
        forgot_res = client.post("/api/auth/forgot-password", json={"email": email})
        raw_reset_token = reset_email.call_args[0][2]
    assert forgot_res.status_code == 200

    reset_res = client.post("/api/auth/reset-password", json={
        "token": raw_reset_token,
        "new_password": new_password,
    })
    assert reset_res.status_code == 200

    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": new_password,
    })
    assert login_res.status_code == 200


def test_reset_password_with_invalid_token_rejected():
    """Unknown/garbage tokens are rejected with HTTP 400."""
    create_verified_user("invalid_reset")
    res = client.post("/api/auth/reset-password", json={
        "token": "totally_invalid_token_123",
        "new_password": "somepassword789",
    })
    assert res.status_code == 400


def test_reset_password_with_expired_token_rejected():
    """Expired reset tokens are rejected and password remains unchanged."""
    email, old_password = create_verified_user("expired_reset")
    res, raw_token = request_password_reset(email)
    assert raw_token is not None

    # Force token into expired state
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    user.reset_token_expires_at = datetime.utcnow() - timedelta(minutes=5)
    db.commit()
    db.close()

    reset_res = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "new_password": "shouldnotapply123",
    })
    assert reset_res.status_code == 400
    assert "expired" in reset_res.json()["detail"].lower()

    # Old password still valid since nothing changed
    login_res = client.post("/api/auth/login", json={"email": email, "password": old_password})
    assert login_res.status_code == 200


def test_reset_password_token_cannot_be_reused():
    """A consumed reset token cannot be used a second time."""
    email, _ = create_verified_user("reuse_reset")
    res, raw_token = request_password_reset(email)
    assert raw_token is not None

    first_res = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "new_password": "firstnewpassword1",
    })
    assert first_res.status_code == 200

    second_res = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "new_password": "secondnewpassword2",
    })
    assert second_res.status_code == 400

    # The first new password still works, second was never applied
    login_res = client.post("/api/auth/login", json={"email": email, "password": "firstnewpassword1"})
    assert login_res.status_code == 200


def test_new_reset_request_invalidates_previous_token():
    """Requesting a new reset link invalidates any previously issued reset token."""
    email, _ = create_verified_user("supersede")
    _, first_token = request_password_reset(email)
    assert first_token is not None

    clear_reset_cooldown(email)
    _, second_token = request_password_reset(email)
    assert second_token is not None
    assert first_token != second_token

    # First token must no longer work
    stale_res = client.post("/api/auth/reset-password", json={
        "token": first_token,
        "new_password": "staleattempt123",
    })
    assert stale_res.status_code == 400

    # Second token works
    fresh_res = client.post("/api/auth/reset-password", json={
        "token": second_token,
        "new_password": "freshtokenpass99",
    })
    assert fresh_res.status_code == 200


@pytest.mark.parametrize("bad_password", ["", "abc12"])
def test_reset_password_enforces_password_policy(bad_password):
    """Passwords shorter than the existing policy (min 6 chars) are rejected."""
    email, old_password = create_verified_user("policy_reset")
    res, raw_token = request_password_reset(email)
    assert raw_token is not None

    policy_res = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "new_password": bad_password,
    })
    assert policy_res.status_code in (400, 422)

    # Original password unchanged
    login_res = client.post("/api/auth/login", json={"email": email, "password": old_password})
    assert login_res.status_code == 200


def test_password_never_returned_in_auth_responses():
    """No auth endpoint response ever contains the hashed or plain password."""
    email, password = create_verified_user("no_leak")
    res, raw_token = request_password_reset(email)
    assert raw_token is not None
    reset_res = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "new_password": "leakcheck12345",
    })
    assert reset_res.status_code == 200

    login_res = client.post("/api/auth/login", json={"email": email, "password": "leakcheck12345"})
    assert login_res.status_code == 200
    response_text = str(login_res.json())
    assert "hashed_password" not in response_text
    assert AuthService.hash_password("leakcheck12345") not in response_text
    assert "leakcheck12345" not in response_text

    me_res = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {login_res.json()['access_token']}"
    })
    assert me_res.status_code == 200
    me_text = str(me_res.json())
    assert "hashed_password" not in me_text
    assert "leakcheck12345" not in me_text


def test_reset_email_contains_required_content():
    """Reset email HTML includes link, expiry notice, and security ignore note."""
    with patch.object(EmailService, 'get_config', return_value={
        "host": "smtp.test", "port": 587, "username": "", "password": "",
        "from_email": "noreply@test.ai", "frontend_url": "http://localhost:5173",
    }):
        result = EmailService.send_password_reset_email(
            "farmer@example.com", "Test Farmer", "sampletoken123"
        )
    assert result is True

    # Inspect constructed HTML by calling internal build helper if exposed, else re-check via logger output
    html = EmailService.build_password_reset_html("farmer@example.com", "Test Farmer", "sampletoken123")
    assert "/reset-password?token=sampletoken123" in html
    assert "expire" in html.lower()
    assert "ignore" in html.lower()
