# Harvesta Development Handoff

Last updated: 2026-08-30.

## Non-negotiable project rule

Preserve the original Harvesta v2.1 UI/UX. The small white floating chat bar, light cream dashboard, navigation, layouts, color system, and existing page structure are the approved design. Add functionality within that design; do not redesign it.

## Current architecture

- React 19 + Vite frontend in `frontend/`.
- FastAPI + SQLAlchemy backend in `backend/`.
- Supabase PostgreSQL through backend-only `DATABASE_URL`; local SQLite fallback.
- Private Supabase Storage for disease photos when enabled; secure local fallback.
- JWT authentication; only verified accounts may log in.
- Gmail SMTP verification, password reset, alerts, and successful-login security email.
- Admin RBAC and company data visibility.
- Ollama local chat with deterministic offline fallback.
- Capacitor Android wrapper and PWA shell.
- Sensor device/reading backend and development simulator.

## Implemented data tables

`users`, `farms`, `crops`, `field_analysis_history`, `user_sessions`, `activity_events`, `notifications`, `notification_preferences`, `ai_chat_conversations`, `ai_chat_messages`, `crop_disease_scans`, `weather_snapshots`, `audit_logs`, `sensor_devices`, and `sensor_readings`.

Admin routes expose a secret-safe inventory and paginated dataset browser. Password hashes, token hashes, JWTs, SMTP/Supabase credentials, and raw IP addresses are never serialized to the frontend.

## Important operational facts

- Original ZIP remains unchanged one directory above the extracted working copy.
- Chat conversations and replies persist in the database.
- Preferred chat model is `gemma3:4b` through local Ollama. Basic rules-based chat remains available when Ollama is down.
- Session heartbeat runs every five minutes while the verified app is active; logout closes owned sessions.
- Supabase image storage is opt-in using backend-only service-role credentials.
- The Android project exists at `frontend/android`, but this workstation has no configured Android SDK, so an AAB has not been compiled here.

## Disease-model truth and safety

The included disease classifier is a 10-class prototype trained on 1,200 synthetic development images. It was not trained on the official PlantVillage photographs and must not be represented as a real-field diagnostic system. The API marks results below `DISEASE_MIN_ACTION_CONFIDENCE` as `review_required` and suppresses disease alerts for uncertain results.

Production disease work requires licensed real images, independent regional field testing, agronomist review, and measured acceptance thresholds. See `docs/COMPLETE_SETUP_GUIDE.md`.

## Sensor foundation

`POST /api/sensors/devices` registers a gateway and returns a raw key once. Only its SHA-256 hash is stored. `POST /api/sensors/ingest` accepts authenticated physical readings, and `GET /api/sensors/readings` is owner-scoped. The dashboard automatically incorporates physical NPK, humidity, and soil-moisture data. See `docs/SENSOR_HARDWARE_PLAN.md`.

## Validation

Run from the project root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
npm run android:sync
```

The full backend, frontend, and Capacitor sync should be rerun after every change. The production frontend build has a non-blocking large JavaScript bundle warning.

## Remaining launch responsibilities

1. Configure/verify the owner's Supabase database, private Storage bucket, and Gmail App Password without committing secrets.
2. Deploy the backend behind HTTPS. A generative local model requires a machine/VPS capable of running Ollama; Render's small/free service should use the offline fallback.
3. Install Android Studio/SDK, configure production API URL, signing, icon/splash, and generate an AAB.
4. Write the company privacy policy, retention schedule, account deletion process, and Play Console Data Safety answers.
5. Replace the synthetic disease prototype only after real-data training and validation.
6. Buy and calibrate sensors only after the simulator and one-device pilot pass.
