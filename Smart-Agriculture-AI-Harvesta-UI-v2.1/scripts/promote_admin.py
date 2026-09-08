"""
Administrative CLI Script: Promote Verified User to Admin Role.

Usage:
    python scripts/promote_admin.py farmer@example.com

Security Requirements:
- Must be executed directly on the host system or via secure SSH.
- The target user must already exist and have verified their email address.
- Logs an immutable security audit event upon successful promotion.
- No passwords or secrets are accepted, stored, or modified.
"""

import sys
import os

# Add workspace root to sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

# Load the same backend-only configuration used by the running application
# before importing the database module. This ensures the promotion is applied
# to Supabase in production and to SQLite during local development.
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(WORKSPACE_ROOT, "backend", ".env"), override=False)
except ImportError:
    pass

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.services.audit_service import AuditService


def promote_user_to_admin(email: str) -> bool:
    clean_email = email.strip().lower()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == clean_email).first()
        if not user:
            print(f"[ERROR] User with email '{clean_email}' does not exist.")
            return False

        if not user.is_verified:
            print(f"[ERROR] User '{clean_email}' has not verified their email. Only verified accounts may be promoted to admin.")
            return False

        if user.role == "admin":
            print(f"[INFO] User '{clean_email}' is already an admin.")
            return True

        # Update role to admin
        user.role = "admin"
        db.commit()
        db.refresh(user)

        # Record immutable audit event
        AuditService.log_audit_event(
            db=db,
            action="admin_role_promoted",
            entity_type="user",
            user_id=user.id,
            entity_id=user.id,
            status="SUCCESS",
            metadata={"promoted_by": "cli_script", "target_email": clean_email},
        )

        print(f"[SUCCESS] Successfully promoted '{user.full_name}' ({clean_email}) to role 'admin'.")
        return True

    except Exception as e:
        db.rollback()
        print(f"[FATAL] Error updating user role: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/promote_admin.py <verified_user_email>")
        sys.exit(1)

    target_email = sys.argv[1]
    success = promote_user_to_admin(target_email)
    sys.exit(0 if success else 1)
