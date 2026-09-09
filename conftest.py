"""
Pytest configuration.

Pins the test environment to an isolated temporary SQLite database so that a
production DATABASE_URL configured in backend/.env can never be reached by the
test suite, and so every test module sees an identical environment regardless
of collection order. load_dotenv() does not override variables already present
in os.environ, so these settings win over backend/.env.
"""

import os
import tempfile

# Every pytest process gets an isolated temporary database and upload directory.
# This prevents synthetic test accounts and images from entering local development data.
_TEST_TEMP_DIR = tempfile.TemporaryDirectory(prefix="harvesta_pytest_")
_TEST_DB_PATH = os.path.join(_TEST_TEMP_DIR.name, "harvesta_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ["DISEASE_UPLOAD_DIR"] = os.path.join(_TEST_TEMP_DIR.name, "disease_scans")
os.environ["SMTP_DELIVERY_ENABLED"] = "false"
os.environ["SUPABASE_STORAGE_ENABLED"] = "false"

# Ensure the auth service does not trip its production-safety guard while
# tests run without a real JWT secret configured.
os.environ.pop("JWT_SECRET_KEY", None)


def pytest_sessionfinish(session, exitstatus):
    """Release SQLite before removing the Windows temporary directory."""
    from backend.app.database import engine

    engine.dispose()
    _TEST_TEMP_DIR.cleanup()
