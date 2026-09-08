"""
Authentication & User Security Service.
Handles password hashing, JWT token creation/verification, and user signup/login operations.
"""

import os
import hashlib
import hmac
import logging
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from dotenv import load_dotenv
    backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
    if os.path.exists(root_env):
        load_dotenv(root_env)
except ImportError:
    pass

from backend.app.database import get_db
from backend.app.models import User

logger = logging.getLogger(__name__)

_DEFAULT_DEV_SECRET = "smart-agriculture-ai-secure-secret-key-2026"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEFAULT_DEV_SECRET)

# Production safety guard: refuse to boot with the known development secret
# when a production database (DATABASE_URL) is configured.
if os.getenv("DATABASE_URL", "").strip() and SECRET_KEY == _DEFAULT_DEV_SECRET:
    raise RuntimeError(
        "Refusing to start: JWT_SECRET_KEY is using the insecure development "
        "default while DATABASE_URL is set. Configure a strong random "
        "JWT_SECRET_KEY before deploying to production."
    )
if SECRET_KEY == _DEFAULT_DEV_SECRET:
    logger.warning(
        "JWT_SECRET_KEY is using the development default. Set a strong random "
        "value via environment variable before deploying."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
REGISTRATION_SETUP_EXPIRE_MINUTES = 60

security = HTTPBearer(auto_error=False)

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes password securely using HMAC SHA-256 with secret salt."""
        salt = SECRET_KEY.encode('utf-8')
        return hmac.new(salt, password.encode('utf-8'), hashlib.sha256).hexdigest()

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verifies plain password matches stored hash."""
        return cls.hash_password(plain_password) == hashed_password

    @staticmethod
    def create_access_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
        """Generates a JWT access token for user."""
        expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
        payload = {
            "sub": str(user_id),
            "email": email,
            "exp": expire
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> Dict[str, Any]:
        """Decodes and validates JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again."
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token."
            )

    @staticmethod
    def create_registration_setup_token(user_id: int, email: str) -> str:
        """Create a short-lived token kept only by the browser that began signup."""
        payload = {
            "sub": str(user_id),
            "email": email,
            "purpose": "registration_setup",
            "exp": datetime.utcnow() + timedelta(minutes=REGISTRATION_SETUP_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_registration_setup_token(token: str) -> Dict[str, Any]:
        """Validate the browser-only registration token and its intended purpose."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("purpose") != "registration_setup" or not payload.get("sub"):
                raise jwt.InvalidTokenError("Unexpected token purpose")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration session expired. Please register again to receive a new email.",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid registration session. Please register again.",
            )


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to extract and authenticate the current user from HTTP Bearer token.
    Raises HTTP 401 if token is missing, invalid, or user does not exist.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided."
        )

    payload = AuthService.decode_access_token(auth.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload."
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists."
        )

    return user


def require_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency that ensures the authenticated user has the 'admin' role.
    Raises HTTP 403 Forbidden if user is not an administrator.
    """
    # The role is always read from the database on every request. A modified
    # browser value or stale client state therefore cannot grant access.
    if (
        getattr(current_user, "role", "farmer") != "admin"
        or not getattr(current_user, "is_verified", False)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified administrator privileges required."
        )
    return current_user
