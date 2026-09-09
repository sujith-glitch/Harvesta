"""
Database connection, session management, and startup schema migration helper.
Supports SQLite for local development (default) and PostgreSQL in production
via the DATABASE_URL environment variable.
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

try:
    from dotenv import load_dotenv

    # Load backend-only configuration before DATABASE_URL is read. Existing
    # process environment variables (tests and hosting dashboards) still win.
    _backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    _root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env, override=False)
    if os.path.exists(_root_env):
        load_dotenv(_root_env, override=False)
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Workspace root paths (used by the local SQLite fallback)
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Production deployments set DATABASE_URL (e.g. Render PostgreSQL).
# When unset or empty, fall back to the existing local SQLite file so
# local development keeps working exactly as before.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if SQLALCHEMY_DATABASE_URL:
    # Render/heroku style URLs may omit the driver scheme segment
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
            "postgres://", "postgresql://", 1
        )
    logger.info("Using external database from DATABASE_URL environment variable.")
else:
    DB_PATH = os.path.join(DATA_DIR, "smart_agriculture.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
    logger.info("DATABASE_URL not set - using local SQLite database.")

IS_SQLITE = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

# SQLite needs check_same_thread=False for FastAPI multithreading;
# PostgreSQL engines must not receive SQLite-specific connect args.
# SQLite needs check_same_thread=False for FastAPI multithreading;
# PostgreSQL engines must not receive SQLite-specific connect args.
if IS_SQLITE:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
else:
    # Supabase pooler connections can be closed while the app is idle. Recycle
    # them before the provider's idle timeout and ping them before each use.
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI Dependency yielding a SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _postgres_column_is_nullable(conn, table_name: str, column_name: str) -> bool:
    """Returns True if the column exists and is nullable on PostgreSQL."""
    result = conn.execute(
        text(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_name = :table_name AND column_name = :column_name"
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    row = result.fetchone()
    if row is None:
        return True  # Column/table does not exist yet; nothing to relax.
    return str(row[0]).lower() == "yes"


def sync_database_schema():
    """
    Safely inspects and migrates existing tables WITHOUT destroying any data.

    - SQLite (local dev): adds missing columns via PRAGMA inspection.
    - PostgreSQL (production): creates new tables happen via Base.metadata.create_all();
      this routine only relaxes constraints on EXISTING tables (e.g. makes legacy
      latitude/longitude columns nullable) using idempotent ALTER statements.

    Reproducible: safe to run on every startup; every statement is guarded by a
    check so it applies at most once per database state.
    """
    if not IS_SQLITE:
        # --- PostgreSQL / production migrations (idempotent, non-destructive) ---
        try:
            with engine.begin() as conn:
                # Phase 2A: latitude/longitude are no longer collected from farmers.
                # Existing production rows keep their stored values; new rows store NULL.
                for column in ("latitude", "longitude"):
                    if not _postgres_column_is_nullable(conn, "field_analysis_history", column):
                        conn.execute(
                            text(
                                f"ALTER TABLE field_analysis_history "
                                f"ALTER COLUMN {column} DROP NOT NULL"
                            )
                        )
                        logger.info(
                            "Migrated PostgreSQL table 'field_analysis_history': "
                            f"Made '{column}' nullable."
                        )
                # Phase B: Ensure role column exists on users table
                try:
                    conn.execute(
                        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'farmer' NOT NULL")
                    )
                    conn.execute(
                        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_attempts INTEGER DEFAULT 0 NOT NULL")
                    )
                except Exception as e:
                    logger.debug(f"PostgreSQL users column check: {e}")
        except Exception as e:
            logger.error(f"Error executing PostgreSQL schema migration: {e}")
        return

    try:
        with engine.begin() as conn:
            # --- users table migration ---
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]

            if columns:
                if "role" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'farmer'"))
                    logger.info("Migrated SQLite table 'users': Added 'role'.")
                if "verification_token_hash" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN verification_token_hash VARCHAR(255)"))
                    logger.info("Migrated SQLite table 'users': Added 'verification_token_hash'.")
                if "verification_token_expires_at" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN verification_token_expires_at DATETIME"))
                    logger.info("Migrated SQLite table 'users': Added 'verification_token_expires_at'.")
                if "verification_sent_at" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN verification_sent_at DATETIME"))
                    logger.info("Migrated SQLite table 'users': Added 'verification_sent_at'.")
                if "verification_attempts" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN verification_attempts INTEGER DEFAULT 0 NOT NULL"))
                    logger.info("Migrated SQLite table 'users': Added 'verification_attempts'.")
                if "reset_token_hash" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_hash VARCHAR(255)"))
                    logger.info("Migrated SQLite table 'users': Added 'reset_token_hash'.")
                if "reset_token_expires_at" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires_at DATETIME"))
                    logger.info("Migrated SQLite table 'users': Added 'reset_token_expires_at'.")
                if "reset_sent_at" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_sent_at DATETIME"))
                    logger.info("Migrated SQLite table 'users': Added 'reset_sent_at'.")

            # --- field_analysis_history table migration (SQLite batch-alter) ---
            _migrate_sqlite_field_analysis(conn)

    except Exception as e:
        logger.error(f"Error executing database schema migration: {e}")


_FAH_TABLE = "field_analysis_history"
_FAH_LEGACY = "field_analysis_history_legacy"


def _sqlite_table_exists(conn, table_name: str) -> bool:
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": table_name},
    ).fetchone()
    return row is not None


def _sqlite_columns(conn, table_name: str):
    """Returns [(name, notnull_flag), ...] for a SQLite table."""
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    # PRAGMA row shape: (cid, name, type, notnull, dflt_value, pk)
    return [(row[1], row[3]) for row in rows]


def _ensure_fah_indexes(conn) -> None:
    """Creates the model-declared indexes if missing (idempotent).

    Indexes are created separately from the table because a renamed legacy
    table temporarily holds the original index names.
    """
    from sqlalchemy.schema import CreateIndex

    from backend.app.models import FieldAnalysisHistory

    existing = {row[1] for row in conn.execute(text(f"PRAGMA index_list({_FAH_TABLE})")).fetchall()}
    for index in FieldAnalysisHistory.__table__.indexes:
        if index.name and index.name not in existing:
            ddl = str(CreateIndex(index).compile(bind=engine))
            # Make re-runnable even if a stale same-named index lingers.
            ddl = ddl.replace("CREATE UNIQUE INDEX", "CREATE UNIQUE INDEX IF NOT EXISTS")
            ddl = ddl.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS")
            conn.execute(text(ddl))
            logger.info(f"Migrated SQLite: ensured index '{index.name}'.")


def _migrate_sqlite_field_analysis(conn) -> None:
    """
    Relaxes legacy NOT NULL constraints on latitude/longitude WITHOUT losing
    any history rows.

    SQLite cannot ALTER COLUMN, so the standard batch-alter recipe is used:
    rename -> recreate per current model -> copy every row -> drop old table.

    NOTE on atomicity: Python's sqlite3 driver implicitly commits around DDL,
    so this routine is written to be *self-healing*: if an interrupted prior
    attempt leaves a *_legacy table behind, it is detected and finished (or
    rolled back to the original table) safely on the next startup.
    Idempotent: no-ops once columns are already nullable.
    """
    from sqlalchemy.schema import CreateTable

    from backend.app.models import FieldAnalysisHistory

    # --- Recovery pass: finish or undo an interrupted rebuild ---
    if _sqlite_table_exists(conn, _FAH_LEGACY):
        if _sqlite_table_exists(conn, _FAH_TABLE):
            logger.warning(
                f"Recovering interrupted migration: merging '{_FAH_LEGACY}' rows "
                f"back into '{_FAH_TABLE}'."
            )
            current_names = {name for name, _ in _sqlite_columns(conn, _FAH_TABLE)}
            common = [name for name, _ in _sqlite_columns(conn, _FAH_LEGACY) if name in current_names]
            collist = ", ".join(common)
            conn.execute(text(
                f"INSERT INTO {_FAH_TABLE} ({collist}) "
                f"SELECT {collist} FROM {_FAH_LEGACY} "
                f"WHERE id NOT IN (SELECT id FROM {_FAH_TABLE})"
            ))
            conn.execute(text(f"DROP TABLE {_FAH_LEGACY}"))
        else:
            # Interrupted before the new table was created: restore original.
            logger.warning(
                f"Recovering interrupted migration: restoring '{_FAH_LEGACY}' "
                f"as '{_FAH_TABLE}'."
            )
            conn.execute(text(f"ALTER TABLE {_FAH_LEGACY} RENAME TO {_FAH_TABLE}"))

    # --- Fresh migration check ---
    column_defs = _sqlite_columns(conn, _FAH_TABLE)
    if not column_defs:
        return  # Table does not exist yet; create_all() will handle it.

    needs_rebuild = any(
        name in ("latitude", "longitude") and notnull == 1
        for name, notnull in column_defs
    )
    if not needs_rebuild:
        _ensure_fah_indexes(conn)
        return

    logger.info(
        "Migrating SQLite table 'field_analysis_history': relaxing NOT NULL on "
        "latitude/longitude (all existing rows are preserved)."
    )
    collist = ", ".join(name for name, _ in column_defs)

    conn.execute(text(f"ALTER TABLE {_FAH_TABLE} RENAME TO {_FAH_LEGACY}"))
    # Table-only DDL (no indexes): the renamed legacy table still owns the
    # original index names until it is dropped below.
    table_ddl = str(CreateTable(FieldAnalysisHistory.__table__).compile(bind=engine))
    conn.execute(text(table_ddl))
    conn.execute(text(
        f"INSERT INTO {_FAH_TABLE} ({collist}) "
        f"SELECT {collist} FROM {_FAH_LEGACY}"
    ))
    copied = conn.execute(text(f"SELECT COUNT(*) FROM {_FAH_TABLE}")).scalar()
    conn.execute(text(f"DROP TABLE {_FAH_LEGACY}"))
    _ensure_fah_indexes(conn)

    logger.info(
        f"Migrated SQLite table 'field_analysis_history': {copied} existing "
        "rows preserved; latitude/longitude are now nullable."
    )
