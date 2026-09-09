"""
Make one verified account the sole Harvesta administrator.

Usage:
    python scripts/set_single_admin.py harvesta444@gmail.com

Only users currently holding the admin role are changed to farmer; existing
farmer accounts and all of their data remain untouched.
"""

import os
import sys

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(WORKSPACE_ROOT, "backend", ".env"), override=False)
except ImportError:
    pass

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.services.audit_service import AuditService


def set_single_admin(email: str) -> bool:
    target_email = email.strip().lower()
    db = SessionLocal()
    try:
        target = db.query(User).filter(User.email == target_email).first()
        if not target:
            print(f"[ERROR] User with email '{target_email}' does not exist.")
            return False
        if not target.is_verified:
            print(f"[ERROR] User '{target_email}' has not verified their email.")
            return False

        other_admins = (
            db.query(User)
            .filter(User.role == "admin", User.email != target_email)
            .all()
        )
        for user in other_admins:
            user.role = "farmer"
            AuditService.log_audit_event(
                db=db,
                action="admin_role_demoted",
                entity_type="user",
                user_id=target.id,
                entity_id=user.id,
                status="SUCCESS",
                metadata={"demoted_email": user.email, "replacement_admin": target_email},
            )

        target.role = "admin"
        db.commit()
        db.refresh(target)

        AuditService.log_audit_event(
            db=db,
            action="admin_role_promoted",
            entity_type="user",
            user_id=target.id,
            entity_id=target.id,
            status="SUCCESS",
            metadata={"promoted_by": "single_admin_script", "target_email": target_email},
        )

        print(f"[SUCCESS] '{target_email}' is now the sole admin.")
        if other_admins:
            print("[INFO] Demoted: " + ", ".join(user.email for user in other_admins))
        return True
    except Exception as exc:
        db.rollback()
        print(f"[FATAL] Error updating roles: {exc}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/set_single_admin.py <verified_user_email>")
        sys.exit(1)
    sys.exit(0 if set_single_admin(sys.argv[1]) else 1)
