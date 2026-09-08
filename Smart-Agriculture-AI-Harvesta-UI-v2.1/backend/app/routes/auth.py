"""
FastAPI Router for Farmer Authentication, Email Verification & Profile Management.
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from backend.app.database import get_db
from backend.app.models import User, UserSession
from backend.app.services.auth_service import AuthService, get_current_user
from backend.app.services.email_service import EmailService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.audit_service import AuditService
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/auth", tags=["Farmer Authentication"])

TOKEN_EXPIRY_MINUTES = 10
RESET_TOKEN_EXPIRY_MINUTES = 30
RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5
RESET_REQUEST_COOLDOWN_SECONDS = 60
FORGOT_PASSWORD_GENERIC_MESSAGE = (
    "If an account exists for this email, a password reset link has been sent."
)


def parse_client_device_and_platform(user_agent_str: Optional[str]):
    """Extracts high-level device type and OS platform from user-agent string."""
    if not user_agent_str:
        return "desktop", "Unknown"
    ua = user_agent_str.lower()
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device_type = "mobile"
    elif "tablet" in ua or "ipad" in ua:
        device_type = "tablet"
    else:
        device_type = "desktop"

    if "windows" in ua:
        platform = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        platform = "macOS"
    elif "android" in ua:
        platform = "Android"
    elif "iphone" in ua or "ipad" in ua or "ios" in ua:
        platform = "iOS"
    elif "linux" in ua:
        platform = "Linux"
    else:
        platform = "Unknown"
    return device_type, platform


# --- Request / Response Models ---

class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid farmer email address")
    full_name: str = Field(..., min_length=2, description="Farmer full name")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Farmer email address")
    password: str = Field(..., description="Account password")

class LogoutRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Optional active session ID to close")

class SessionHeartbeatRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=255)
    current_view: Optional[str] = Field(None, max_length=100)

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str = "farmer"
    is_verified: bool
    created_at: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    session_id: Optional[str] = None
    user: UserResponse

class SignupResponse(BaseModel):
    message: str
    email: str
    is_verified: bool = False
    setup_token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered farmer email address")

class VerifyAndSetPasswordRequest(BaseModel):
    token: str = Field(..., description="Cryptographic verification token")
    # Optional only for backward compatibility with links issued by v2.1.
    # The current UI verifies email first and creates the password on the
    # original registration device using a separate setup token.
    password: Optional[str] = Field(None, min_length=6)

class RegistrationSetupRequest(BaseModel):
    setup_token: str = Field(..., min_length=20, description="Browser-only registration setup token")

class VerifyRegistrationOtpRequest(RegistrationSetupRequest):
    code: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")

class CompleteRegistrationRequest(RegistrationSetupRequest):
    password: str = Field(..., min_length=6, description="New account password")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered farmer email address")

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token from the email link")
    new_password: str = Field(..., min_length=6, description="New account password (minimum 6 characters)")


def _registration_user_from_token(setup_token: str, db: Session) -> User:
    payload = AuthService.decode_registration_setup_token(setup_token.strip())
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid registration session. Please register again.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.email != payload.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid registration session. Please register again.",
        )
    return user


def _generate_verification_code() -> str:
    """Return a zero-padded four-digit code, including values such as 0042."""
    return f"{secrets.randbelow(10_000):04d}"


def _hash_verification_code(code: str) -> str:
    """Pepper the OTP so the readable four-digit code never reaches the database."""
    return AuthService.hash_password(f"email-verification:{code}")


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Farmer Account"
)
def signup(request_data: SignupRequest, db: Session = Depends(get_db)):
    email_clean = request_data.email.strip().lower()
    
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        if not existing_user.is_verified:
            # A farmer may return to the signup screen after missing the first
            # email. Keep signup recoverable instead of trapping the account in
            # an unfinished state. Respect the same resend cooldown used below.
            sent_recently = False
            if existing_user.verification_sent_at:
                elapsed = (datetime.utcnow() - existing_user.verification_sent_at).total_seconds()
                sent_recently = elapsed < RESEND_COOLDOWN_SECONDS

            if not sent_recently:
                verification_code = _generate_verification_code()
                existing_user.verification_token_hash = _hash_verification_code(verification_code)
                existing_user.verification_token_expires_at = (
                    datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
                )
                existing_user.verification_sent_at = datetime.utcnow()
                existing_user.verification_attempts = 0
                db.commit()
                EmailService.send_verification_email(
                    existing_user.email,
                    existing_user.full_name,
                    verification_code,
                )

            return {
                "message": (
                    "This registration is waiting for email verification. "
                    "Please enter the newest four-digit code sent by Harvesta."
                ),
                "email": existing_user.email,
                "is_verified": False,
                "setup_token": AuthService.create_registration_setup_token(
                    existing_user.id,
                    existing_user.email,
                ),
            }

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Temporary random password until the user verifies their email and sets a real one
    temp_random_pw = secrets.token_urlsafe(16)
    hashed_pw = AuthService.hash_password(temp_random_pw)
    
    # Generate a short user-facing code while storing only its peppered hash.
    verification_code = _generate_verification_code()
    token_hash = _hash_verification_code(verification_code)
    expires_at = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    now = datetime.utcnow()

    new_user = User(
        email=email_clean,
        full_name=request_data.full_name.strip(),
        hashed_password=hashed_pw,
        role="farmer",
        is_verified=False,
        verification_token_hash=token_hash,
        verification_token_expires_at=expires_at,
        verification_sent_at=now,
        verification_attempts=0,
        created_at=now
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Activity & Audit logging
    AnalyticsService.log_activity_event(
        db=db,
        event_name="account_created",
        user_id=new_user.id,
        feature="auth",
        metadata={"email": new_user.email},
    )
    AuditService.log_audit_event(
        db=db,
        action="account_created",
        entity_type="user",
        user_id=new_user.id,
        entity_id=new_user.id,
        status="SUCCESS",
    )

    # Trigger HTML verification-code email.
    EmailService.send_verification_email(new_user.email, new_user.full_name, verification_code)

    return {
        "message": "Account registered successfully. Enter the four-digit code sent to your email.",
        "email": new_user.email,
        "is_verified": False,
        "setup_token": AuthService.create_registration_setup_token(
            new_user.id,
            new_user.email,
        ),
    }


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate Farmer Account"
)
def login(
    request_data: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    email_clean = request_data.email.strip().lower()
    
    try:
        user = db.query(User).filter(User.email == email_clean).first()
    except OperationalError:
        # A remote pooler may close an idle connection between requests. Roll
        # back and retry once so a transient disconnect does not become a 500.
        db.rollback()
        user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Restrict unverified users from gaining access tokens
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not verified. Enter the four-digit code sent to your email."
        )

    # During the two-device signup flow, the verification hash is intentionally
    # retained until the original browser creates the password.
    if user.verification_token_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verified. Return to the device where registration was started and create your password.",
        )

    if not AuthService.verify_password(request_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = AuthService.create_access_token(user.id, user.email)

    # Session & Activity Telemetry
    user_agent = http_request.headers.get("user-agent", "")
    client_ip = http_request.headers.get("x-forwarded-for", http_request.client.host if http_request.client else None)
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    device_type, platform = parse_client_device_and_platform(user_agent)
    session_id = f"sess_{uuid.uuid4().hex}"

    try:
        AnalyticsService.create_session(
            db=db,
            user_id=user.id,
            session_id=session_id,
            device_type=device_type,
            platform=platform,
            user_agent=user_agent,
            ip_address=client_ip,
        )
        AnalyticsService.log_activity_event(
            db=db,
            event_name="login_success",
            user_id=user.id,
            session_id=session_id,
            feature="auth",
            metadata={"device_type": device_type, "platform": platform},
        )
    except Exception:
        pass

    # Notify the verified account owner about each successful login. Email failure
    # never blocks access; the in-app record and session telemetry remain available.
    try:
        login_details = (
            f"A successful login was recorded from {device_type or 'an unknown device'} "
            f"on {platform or 'an unknown platform'}. If this was not you, reset your password immediately."
        )
        NotificationService.generate_security_notification(
            db=db,
            user=user,
            event_type="login_success",
            details=login_details,
        )
    except Exception:
        pass

    return {
        "access_token": token,
        "token_type": "bearer",
        "session_id": session_id,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": getattr(user, "role", "farmer"),
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if isinstance(user.created_at, datetime) else str(user.created_at)
        }
    }


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Conclude Authenticated Session"
)
def logout(
    logout_data: Optional[LogoutRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_id = logout_data.session_id if logout_data else None
    if session_id:
        owned_session = (
            db.query(UserSession)
            .filter(UserSession.session_id == session_id, UserSession.user_id == current_user.id)
            .first()
        )
        if owned_session:
            AnalyticsService.end_session(db, session_id)
    AnalyticsService.log_activity_event(
        db=db,
        event_name="logout",
        user_id=current_user.id,
        session_id=session_id,
        feature="auth",
    )
    return {"status": "success", "message": "Logged out successfully."}


@router.post(
    "/session/heartbeat",
    status_code=status.HTTP_200_OK,
    summary="Update Authenticated Session Activity",
)
def session_heartbeat(
    payload: SessionHeartbeatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id == payload.session_id,
            UserSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    AnalyticsService.update_session_activity(db, session.session_id)
    return {
        "status": "ok",
        "session_id": session.session_id,
        "last_active_at": session.last_active_at.isoformat() if session.last_active_at else None,
        "current_view": payload.current_view,
    }


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify Email Token"
)
def verify_email(
    request_data: VerifyAndSetPasswordRequest,
    db: Session = Depends(get_db)
):
    token = request_data.token
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is required."
        )

    token_clean = token.strip()
    candidate_hashes = [
        _hash_verification_code(token_clean),
        # Backward compatibility for verification links issued before OTP registration.
        hashlib.sha256(token_clean.encode("utf-8")).hexdigest(),
    ]

    user = db.query(User).filter(User.verification_token_hash.in_(candidate_hashes)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized verification token."
        )

    # Check token expiration
    if not user.is_verified and user.verification_token_expires_at and datetime.utcnow() > user.verification_token_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please request a new verification email."
        )

    if not user.is_verified:
        # Keep the verification hash until password creation is completed on
        # the original browser. It acts as the server-side "setup incomplete"
        # marker and prevents login with the temporary random password.
        user.is_verified = True
        user.verification_attempts = 0
        db.commit()

        AnalyticsService.log_activity_event(
            db=db,
            event_name="email_verified",
            user_id=user.id,
            feature="auth",
        )
        AuditService.log_audit_event(
            db=db,
            action="email_verified",
            entity_type="user",
            user_id=user.id,
            entity_id=user.id,
            status="SUCCESS",
        )

        try:
            NotificationService.generate_security_notification(
                db=db,
                user=user,
                event_type="email_verified",
            )
        except Exception:
            pass

    # Backward compatibility for already-open v2.1 password pages. New pages
    # never send a password through this phone verification endpoint.
    if request_data.password:
        user.hashed_password = AuthService.hash_password(request_data.password)
        user.verification_token_hash = None
        user.verification_token_expires_at = None
        user.verification_sent_at = None
        user.verification_attempts = 0
        db.commit()
        return {
            "status": "success",
            "message": "Email verified and password created successfully. You can now log in.",
        }

    return {
        "status": "email_verified",
        "message": "Gmail verification successful. Return to the device where you registered to create your password."
    }


@router.post(
    "/verify-registration-otp",
    status_code=status.HTTP_200_OK,
    summary="Verify Four-Digit Registration Code",
)
def verify_registration_otp(
    request_data: VerifyRegistrationOtpRequest,
    db: Session = Depends(get_db),
):
    user = _registration_user_from_token(request_data.setup_token, db)

    if user.is_verified:
        return {
            "status": "complete" if not user.verification_token_hash else "ready_for_password",
            "message": "Email is already verified.",
        }

    if not user.verification_token_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification code. Please request a new code.",
        )

    if user.verification_token_expires_at and datetime.utcnow() > user.verification_token_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Please request a new code.",
        )

    attempts = int(user.verification_attempts or 0)
    if attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Please request a new code.",
        )

    provided_hash = _hash_verification_code(request_data.code)
    if not hmac.compare_digest(provided_hash, user.verification_token_hash):
        user.verification_attempts = attempts + 1
        db.commit()
        attempts_left = OTP_MAX_ATTEMPTS - user.verification_attempts
        if attempts_left <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many incorrect attempts. Please request a new code.",
            )
        suffix = "s" if attempts_left != 1 else ""
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect verification code. {attempts_left} attempt{suffix} remaining.",
        )

    # Keep the hash until password creation; it marks registration as incomplete
    # and prevents login with the temporary random password.
    user.is_verified = True
    user.verification_attempts = 0
    db.commit()

    AnalyticsService.log_activity_event(
        db=db,
        event_name="email_verified",
        user_id=user.id,
        feature="auth",
    )
    AuditService.log_audit_event(
        db=db,
        action="email_verified",
        entity_type="user",
        user_id=user.id,
        entity_id=user.id,
        status="SUCCESS",
    )
    try:
        NotificationService.generate_security_notification(
            db=db,
            user=user,
            event_type="email_verified",
        )
    except Exception:
        pass

    return {
        "status": "ready_for_password",
        "message": "Verification successful. Create your Harvesta password.",
    }


@router.post(
    "/registration-status",
    status_code=status.HTTP_200_OK,
    summary="Check Two-Device Registration Status",
)
def registration_status(
    request_data: RegistrationSetupRequest,
    db: Session = Depends(get_db),
):
    user = _registration_user_from_token(request_data.setup_token, db)
    if user.is_verified and not user.verification_token_hash:
        state = "complete"
    elif user.is_verified:
        state = "ready_for_password"
    elif user.verification_token_expires_at and datetime.utcnow() > user.verification_token_expires_at:
        state = "verification_expired"
    else:
        state = "waiting_for_otp"
    return {"status": state, "email": user.email}


@router.post(
    "/complete-registration",
    status_code=status.HTTP_200_OK,
    summary="Create Password on Original Registration Device",
)
def complete_registration(
    request_data: CompleteRegistrationRequest,
    db: Session = Depends(get_db),
):
    user = _registration_user_from_token(request_data.setup_token, db)
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Verify your Gmail address before creating a password.",
        )
    if not user.verification_token_hash:
        return {
            "status": "already_complete",
            "message": "Registration is already complete. You can log in.",
        }

    user.hashed_password = AuthService.hash_password(request_data.password)
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    user.verification_sent_at = None
    user.verification_attempts = 0
    db.commit()

    AnalyticsService.log_activity_event(
        db=db,
        event_name="registration_completed",
        user_id=user.id,
        feature="auth",
    )
    AuditService.log_audit_event(
        db=db,
        action="registration_completed",
        entity_type="user",
        user_id=user.id,
        entity_id=user.id,
        status="SUCCESS",
    )

    return {
        "status": "success",
        "message": "Password created successfully. You can now log in to Harvesta.",
    }


@router.post(
    "/resend-verification",
    status_code=status.HTTP_200_OK,
    summary="Resend Email Verification Code"
)
def resend_verification(request_data: ResendVerificationRequest, db: Session = Depends(get_db)):
    email_clean = request_data.email.strip().lower()

    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        # Prevent account enumeration
        return {
            "status": "success",
            "message": "If an account with this email exists, a verification code has been sent."
        }

    if user.is_verified:
        if user.verification_token_hash:
            return {
                "status": "email_verified",
                "message": "Gmail is verified. Return to the original registration screen to create your password."
            }
        return {
            "status": "already_verified",
            "message": "This account is already verified. You can proceed to log in."
        }

    # Apply 60-second cooldown rate limiting
    if user.verification_sent_at:
        elapsed = (datetime.utcnow() - user.verification_sent_at).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            remaining = int(RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting another verification email."
            )

    verification_code = _generate_verification_code()
    token_hash = _hash_verification_code(verification_code)
    expires_at = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    now = datetime.utcnow()

    user.verification_token_hash = token_hash
    user.verification_token_expires_at = expires_at
    user.verification_sent_at = now
    user.verification_attempts = 0
    db.commit()

    EmailService.send_verification_email(user.email, user.full_name, verification_code)

    return {
        "status": "success",
        "message": "A new four-digit verification code was sent. Please check your inbox."
    }


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset Link"
)
def forgot_password(request_data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email_clean = request_data.email.strip().lower()

    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not user.is_verified:
        return {
            "status": "success",
            "message": FORGOT_PASSWORD_GENERIC_MESSAGE
        }

    if user.reset_sent_at:
        elapsed = (datetime.utcnow() - user.reset_sent_at).total_seconds()
        if elapsed < RESET_REQUEST_COOLDOWN_SECONDS:
            remaining = int(RESET_REQUEST_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting another password reset email."
            )

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    expires_at = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)

    user.reset_token_hash = token_hash
    user.reset_token_expires_at = expires_at
    user.reset_sent_at = datetime.utcnow()
    db.commit()

    EmailService.send_password_reset_email(user.email, user.full_name, raw_token)

    return {
        "status": "success",
        "message": FORGOT_PASSWORD_GENERIC_MESSAGE
    }


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset Account Password with Token"
)
def reset_password(request_data: ResetPasswordRequest, db: Session = Depends(get_db)):
    token = request_data.token
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token is required."
        )

    token_hash = hashlib.sha256(token.strip().encode('utf-8')).hexdigest()

    user = db.query(User).filter(User.reset_token_hash == token_hash).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized password reset token."
        )

    if user.reset_token_expires_at and datetime.utcnow() > user.reset_token_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset link has expired. Please request a new one."
        )

    # Hash and save the new password
    user.hashed_password = AuthService.hash_password(request_data.new_password)

    # A successful reset link proves control of the verified Gmail account.
    # If registration was left between phone verification and password setup,
    # the new password safely completes that pending setup as well.
    if user.is_verified and user.verification_token_hash:
        user.verification_token_hash = None
        user.verification_token_expires_at = None
        user.verification_sent_at = None
        user.verification_attempts = 0

    # Consume token
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.commit()

    # Log telemetry & audit
    AnalyticsService.log_activity_event(
        db=db,
        event_name="password_reset_completed",
        user_id=user.id,
        feature="auth",
    )
    AuditService.log_audit_event(
        db=db,
        action="password_reset_completed",
        entity_type="user",
        user_id=user.id,
        entity_id=user.id,
        status="SUCCESS",
    )

    try:
        NotificationService.generate_security_notification(
            db=db,
            user=user,
            event_type="password_reset_completed",
        )
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Your password has been updated successfully. You can now log in with your new password."
    }


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User Profile"
)
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": getattr(current_user, "role", "farmer"),
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at.isoformat() if isinstance(current_user.created_at, datetime) else str(current_user.created_at)
    }
