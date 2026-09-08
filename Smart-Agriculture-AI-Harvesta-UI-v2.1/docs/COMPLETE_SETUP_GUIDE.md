# Harvesta Complete Setup Guide

This guide is written for the project owner. Follow it in order; do not paste any secret key into the frontend or commit `.env` files.

## What is already implemented

- Original Harvesta v2.1 UI/UX preserved.
- Signup, Gmail email verification, password setup/reset, verified-only login, and per-login security email.
- Supabase PostgreSQL support with local SQLite fallback.
- Private Supabase Storage support for disease-scan photos with secure local fallback.
- Farmer farms, crops, field-analysis history, weather history, notifications, chat history, image scans, sessions, device/platform, usage events, and audit logs.
- Company Admin dashboard with users, login/session duration, feature telemetry, audit logs, and a secret-safe Stored Data browser.
- Local Ollama chat plus a smaller no-network agricultural fallback.
- Crop image screening with ownership checks, private image access, uncertainty handling, and history.
- PWA installation and a generated Capacitor Android project in `frontend/android`.
- Sensor registration, one-time device keys, readings history, dashboard NPK/moisture integration, and a development simulator.

## 1. Start the project locally

Open two PowerShell windows in the project root.

Backend:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`. API documentation is at `http://127.0.0.1:8000/docs`.

## 2. Supabase database and private image storage

1. Create a Supabase project.
2. Copy its PostgreSQL pooler connection string into `backend/.env` as `DATABASE_URL`. Add `?sslmode=require` when it is not already present.
3. In Supabase Storage, create a **private** bucket named `crop-disease-scans`.
4. Add these backend-only values:

```dotenv
SUPABASE_STORAGE_ENABLED=true
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SECRET_KEY=YOUR_BACKEND_ONLY_SB_SECRET_KEY
SUPABASE_STORAGE_BUCKET=crop-disease-scans
SUPABASE_STORAGE_REQUIRED=true
```

5. Restart the backend. New database tables are created automatically and uploaded images are stored under `users/{user_id}/disease-scans/`.

The service-role key must never use a `VITE_` prefix and must never appear in an Android or browser build.

## 3. Gmail verification and login notifications

1. Enable two-step verification on the sender Google account.
2. Create a Google App Password for Mail.
3. Put the following only in `backend/.env`:

```dotenv
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_DELIVERY_ENABLED=true
SMTP_USERNAME=your-address@gmail.com
SMTP_PASSWORD=your-16-character-app-password
SMTP_FROM_EMAIL=your-address@gmail.com
FRONTEND_URL=http://localhost:5173
```

For production, replace `FRONTEND_URL` with the public HTTPS web-app URL. Signup verification, password reset, important farm alerts, disease alerts above the confidence threshold, and every successful login can then send email according to the farmer's notification preferences.

## 4. Unlimited local chat with Ollama

Install Ollama on the machine that runs the backend, then run:

```powershell
ollama pull gemma3:4b
ollama serve
```

Backend configuration:

```dotenv
LOCAL_AI_MODE=auto
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT_SECONDS=90
```

Ollama has no per-message API fee. Actual capacity is limited by the computer's RAM/CPU/GPU and storage. If Ollama is stopped, Harvesta automatically uses its smaller offline rules-based assistant so the chat bar still answers basic questions.

For a public Android app, Ollama must run beside the public backend on a private server/VPN; `127.0.0.1` on a phone means the phone itself, not the developer PC.

## 5. Create the company administrator

The detailed permission list and owner verification checklist are in `docs/ADMIN_ACCESS_GUIDE.md`.

1. Sign up normally and verify the owner's email.
2. From the project root, run:

```powershell
.\backend\.venv\Scripts\python.exe scripts\promote_admin.py owner@example.com
```

3. Log out and log in again. Open **Admin Portal**, then **Stored Data**.

The dashboard never displays password hashes, verification/reset tokens, JWTs, SMTP/Supabase credentials, or raw IP addresses.

## 6. Disease image screening: important truth

The current included model is a 10-class software prototype trained on 1,200 synthetic development images. Its synthetic held-out score is not real-field accuracy. It currently covers selected Tomato, Potato, Corn, and Bell Pepper classes only.

Harvesta now marks low-confidence results as `review_required`, blocks automatic disease alerts for those results, and tells the farmer to retake the photo or obtain human review. Do not use the current model to select chemicals or claim a confirmed diagnosis.

A true production model requires:

1. Downloading the licensed official PlantVillage images or another documented regional field dataset.
2. Training a modern image model on the real photographs.
3. Testing on independent field photos from the intended region, phones, lighting, growth stages, and disease severities.
4. Expert agronomist review and a documented acceptance threshold.
5. Replacing the `.joblib` artifact only after those tests pass.

The official PlantVillage repository documents 54,306 images across 14 crop species and 26 diseases: `https://github.com/spMohanty/PlantVillage-Dataset`.

## 7. Test sensor data before buying hardware

Register a device in Swagger:

1. Open `http://127.0.0.1:8000/docs`.
2. Authorize with a farmer JWT.
3. Call `POST /api/sensors/devices` with the farmer's farm ID.
4. Save the returned `device_uid` and one-time `device_key`.
5. Send one synthetic test reading:

```powershell
.\backend\.venv\Scripts\python.exe scripts\simulate_sensor.py --device-uid YOUR_UID --device-key YOUR_KEY --once
```

The dashboard's NPK and soil-moisture cards will use this test reading. Delete test records before real deployment if they should not be mixed with physical readings.

## 8. Android and Play Store

The Capacitor Android project is already generated under `frontend/android`. This computer currently has Java but no configured Android SDK, so install Android Studio and its Android SDK before producing an APK/AAB.

For a production build:

1. Deploy the FastAPI backend at a public HTTPS URL.
2. Set `frontend/.env.production`:

```dotenv
VITE_API_BASE_URL=https://api.your-domain.com
VITE_ENABLE_DEMO_MODE=false
```

3. Run:

```powershell
cd frontend
npm run android:sync
npm run android:open
```

4. In Android Studio, set the app icon/splash assets, increment the version, generate a private signing key, and choose **Build > Generate Signed Bundle / APK > Android App Bundle**.
5. Upload the `.aab` to Play Console. Complete Data Safety using the data inventory below and provide the privacy policy/deletion process required for the final company operation.

## 9. What the database stores

| Dataset | Purpose |
|---|---|
| users | Account email/name, verification state, role, and secure password/token hashes |
| farms, crops | Farmer-owned farm and crop details |
| field_analysis_history | Soil/weather inputs and recommendation history |
| user_sessions | Login, last activity, logout, duration, device/platform, hashed network identifier |
| activity_events | Feature usage telemetry without raw passwords or JWTs |
| notifications, notification_preferences | Alerts, delivery state, read state, and user choices |
| ai_chat_conversations, ai_chat_messages | Farmer's persistent chat history and local model name |
| crop_disease_scans | Private image key, candidate class, confidence, and guidance |
| weather_snapshots | Historical weather values and source |
| sensor_devices, sensor_readings | Registered hardware and timestamped soil/climate/NPK values |
| audit_logs | Security and important administrative actions |

No automatic retention/deletion schedule is enabled yet. Before public launch, the company must choose retention periods, publish a privacy policy, and implement account/data deletion according to the launch country.

## 10. Final verification commands

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
npm run android:sync
```

Never use demo mode for production and never ship `backend/.env` inside the Android app.
