# Supabase PostgreSQL Platform Foundation Guide

## 1. Overview & Architecture

The **Smart Agriculture AI Platform (Harvesta v2.1)** uses **PostgreSQL hosted on Supabase** as its primary production database, while maintaining full **SQLite compatibility** for zero-friction local development.

```
┌────────────────────────────────────────────────────────┐
│               Frontend (React / Vite)                  │
│       - Uses public REST API endpoints                 │
│       - Injects JWT Bearer token on requests           │
│       - NEVER receives database credentials / secrets  │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS (REST + JWT)
┌──────────────────────────▼─────────────────────────────┐
│             FastAPI Backend (Render Web Service)        │
│       - Verifies JWT authentication                    │
│       - Enforces tenant isolation & user ownership      │
│       - Connects to Supabase via SQLAlchemy ORM        │
└──────────────────────────┬─────────────────────────────┘
                           │ Encrypted SSL (Port 5432 / 6543)
┌──────────────────────────▼─────────────────────────────┐
│          Supabase Cloud Platform (PostgreSQL)          │
│       - Core tables: users, farms, crops, history      │
│       - Analytics: user_sessions, activity_events      │
│       - Features: notifications, chat, disease_scans   │
│       - Private crop-disease image Storage bucket      │
│       - Sensor gateways and time-series readings       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Why Supabase PostgreSQL?

1. **Managed Reliability & Scalability:** Fully managed PostgreSQL with automated daily backups, point-in-time recovery (PITR), and enterprise uptime.
2. **Built-in Connection Pooling (Supavisor):** High-throughput pooling on port `6543` prevents connection exhaustion across serverless and web instances.
3. **Future AI Extensions (`pgvector`):** Native vector embeddings support for future RAG-based conversational agronomist knowledge retrieval.
4. **Private Image Storage:** S3-compatible Supabase Storage stores farmer-uploaded crop leaf photos behind authenticated backend routes.
5. **Standard SQL & SQLAlchemy Compatible:** Standard PostgreSQL dialect (`psycopg2-binary`) with zero vendor lock-in; runs seamlessly alongside local SQLite.

---

## 3. Environment Variable Configuration

To connect the backend to Supabase in staging or production, provide the standard `DATABASE_URL` environment variable:

```bash
# Production Connection (Render / Production Server)
DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[YOUR_PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
```

### Connection String Guidelines
* **Session Pooler / Transaction Pooler (Recommended):** Port `6543` (e.g. `aws-0-[region].pooler.supabase.com:6543/postgres`).
* **Direct Connection:** Port `5432` (e.g. `db.[project-ref].supabase.co:5432/postgres`).
* **URL Scheme Normalisation:** The backend automatically normalises `postgres://` to `postgresql://` if provided by older deployment dashboards.
* **SSL Requirement:** Supabase connections require SSL (`sslmode=require`), which is enabled automatically by SQLAlchemy's `create_engine`.

---

## 4. Local SQLite Development Fallback

When `DATABASE_URL` is unset or empty:
* The backend automatically boots with **SQLite** at `data/smart_agriculture.db`.
* All database tables, relationships, and queries function identically across both environments.
* Local development and unit tests require zero external cloud setup or internet connectivity.

---

## 5. Security & Isolation Rules

1. **Backend-Only Access:** The frontend never connects directly to Supabase via database ports or client SDKs with service role privileges. All database transactions occur exclusively within the authenticated FastAPI backend.
2. **Secret Protection:** Never commit `.env` files or paste database connection strings with passwords in git repositories or client-side bundles.
3. **No Plaintext Passwords or Sensitive Tokens:** Password hashes use salt-keyed HMAC SHA-256; verification and password-reset tokens are stored as SHA-256 hashes; and analytics sessions record one-way hashed IP identifiers (`ip_hash`).
4. **Tenant Isolation:** All queries filter strictly by `user_id` extracted from verified JWT claims.

---

## 6. Supabase Database Schema Inventory (Phase A Foundation)

### Core Domain Tables
* `users` — Farmer account identities, password hashes, email verification flags, and password reset tokens.
* `farms` — Farm records (location, district, state, country, acreage size, soil type, farming method).
* `crops` — Crop entries linked to farms (variety, planting date, harvest date, growth stage, health status).
* `field_analysis_history` — Historical AI field analyses, weather conditions, soil moisture metrics, and recommendations.

### Supabase Platform Foundation Tables
* `user_sessions` — Login session lifecycle, active timestamps, duration, device type, platform, and privacy-safe network hash.
* `activity_events` — Application feature telemetry and event metadata stored as cross-platform JSON.
* `notifications` — In-app alerts, irrigation warnings, disease notifications, delivery channels, and read receipts.
* `notification_preferences` — User alert preferences per category (email, irrigation, disease, security, weather).
* `ai_chat_conversations` — Conversational AI threads linked to users and optional farm contexts.
* `ai_chat_messages` — Individual messages (`user`, `assistant`, `system`) with model metadata.
* `crop_disease_scans` — Image-based crop disease scan records, predicted pathogen classes, confidence scores, and storage keys.
* `weather_snapshots` — Historical weather logs for farm coordinates.
* `audit_logs` — Immutable audit trail for security-critical actions and administrative events.
* `sensor_devices` — Farmer-owned sensor gateway registrations and secure device-key hashes.
* `sensor_readings` — Time-series soil moisture, temperature, humidity, pH, NPK, rainfall, and battery readings.

### Private Storage Bucket

Create a private bucket named `crop-disease-scans` and configure `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_STORAGE_BUCKET`, and `SUPABASE_STORAGE_ENABLED=true` only on the backend. Older projects may temporarily use `SUPABASE_SERVICE_ROLE_KEY` as a fallback. The browser never receives either elevated key.

---

## 7. Future Schema Evolution & Migrations

For Phase A, table creation is managed automatically on application startup via `Base.metadata.create_all(bind=engine)` and idempotent startup schema checks in `sync_database_schema()`. When evolving the production schema in later phases (e.g. adding new columns to existing production tables), Alembic migrations or controlled SQL migration scripts should be applied.
