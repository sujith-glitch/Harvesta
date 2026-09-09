# Smart Agriculture AI Platform 🌾🤖

**HARVESTA UI v2.1 — FULL-STACK WORKING COPY**

A full-stack web and Android-ready application for farmers providing agricultural insights, real-time weather field analysis, persistent history, irrigation decision support, and authenticated farmer dashboards — featuring the original **Harvesta UI design system**.

The original UI/UX is preserved. Backend additions include verified Gmail login flows, successful-login email alerts, Supabase database/private image storage support, admin data visibility, persistent local AI chat, disease-scan safety controls, PWA/Android packaging, and a secure sensor ingestion foundation.

Start with [`docs/COMPLETE_SETUP_GUIDE.md`](./docs/COMPLETE_SETUP_GUIDE.md). Future hardware is documented in [`docs/SENSOR_HARDWARE_PLAN.md`](./docs/SENSOR_HARDWARE_PLAN.md).

> Disease AI safety: the included 10-class image model is a synthetic-data software prototype, not a validated real-field diagnostic model. Low-confidence results require human review.

> **✅ HOW TO VERIFY YOU ARE RUNNING THIS VERSION (v2.1):**
> 1. The login page shows **"HARVESTA UI · v2.1 · OFFICIAL BUILD"** at the bottom of the login card.
> 2. After login, the sidebar shows a green **"v2.1" badge** next to the Harvesta logo.
> 3. The dashboard shows a **light cream design** with a "Field 01" aerial map hero, NPK Levels card, Lost Area donuts, and Soil Moisture chart.
>
> **❌ IF YOU INSTEAD SEE:** a dark-green design with "Good Evening, Rajesh", Punjab India weather, FARMS/CROPS/ALERTS stat cards → you are running an **OLD/DIFFERENT project folder**, NOT this ZIP. Close it, extract this ZIP fresh, and run `START-HERE-WINDOWS.bat` (or `START-HERE-MAC-LINUX.sh`).

> **➡️ AI assistants & new developers: read [`HANDOFF.md`](./HANDOFF.md) first.**
> It contains the full project status, what works, what's missing, and the development roadmap.

---

## 📁 Project Structure

```text
Smart-Agriculture-AI/
│
├── frontend/             # React.js web application (Vite)
│   ├── src/
│   │   ├── pages/        # Dashboard, Login, Signup, VerifyEmail
│   │   ├── components/   # AnalysisHistory, DashboardSummary, UserProfile, RealWeatherForm, etc.
│   │   └── services/     # API client & auth token management
├── backend/              # Python FastAPI backend server
│   ├── app/
│   │   ├── routes/       # Auth, AI, Weather, History, Dashboard routers
│   │   ├── services/     # WeatherService, FieldAnalysisService, AIService, AuthService
│   │   ├── database.py   # SQLite connection & SQLAlchemy engine
│   │   ├── models.py     # User & FieldAnalysisHistory ORM models
│   │   └── main.py       # FastAPI application entrypoint
│   ├── requirements.txt  # Backend dependencies
│   └── venv/             # Python virtual environment
├── ml/                   # Machine learning model scripts & artifacts
├── data/                 # SQLite database & synthetic sample datasets
├── docs/                 # Platform documentation
└── tests/                # Automated pytest test suite
```

---

## ⚡ Quick Start Guide (Local Setup)

### Prerequisites
- **Python**: Version 3.10+ (Tested on Python 3.13.5)
- **Node.js**: Version 18+ (Tested on Node 24.14.0)

---

### 1. Run the Backend (FastAPI)

1. Open a terminal and navigate to the backend folder:
   ```bash
   cd backend
   ```

2. Activate the Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

3. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. Verify the backend is running:
   - **Health Check Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
   - **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 2. Run the Frontend (React + Vite)

1. Open a **new** terminal window and navigate to the frontend folder:
   ```bash
   cd frontend
   ```

2. Install dependencies (if not already installed):
   ```bash
   npm install
   ```

3. Start the Vite React development server:
   ```bash
   npm run dev
   ```

4. Open your browser and visit:
   - **Frontend App**: [http://localhost:5173](http://localhost:5173)

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | No | System health check |
| `POST` | `/api/auth/signup` | No | Farmer account registration |
| `POST` | `/api/auth/login` | No | Authenticate user & issue JWT token |
| `GET` | `/api/auth/me` | Yes | Get authenticated farmer profile |
| `GET` | `/api/weather/current` | No | Get live weather metrics for lat/lon |
| `POST` | `/api/ai/irrigation-recommendation` | No | ML model recommendation (manual inputs) |
| `POST` | `/api/ai/field-analysis` | Yes | Real-weather analysis & automatic history save |
| `GET` | `/api/history/field-analysis` | Yes | Get farmer's analysis history |
| `GET` | `/api/history/field-analysis/{id}` | Yes | Get single history record details |
| `DELETE`| `/api/history/field-analysis/{id}` | Yes | Delete history record |
| `GET` | `/api/dashboard/summary` | Yes | Get farmer dashboard summary metrics |
| `POST` | `/api/farms` + `/api/farms/{id}/crops` | Yes | Farm & crop management CRUD |

---

## 🎨 UI Design System — "Harvesta"

The frontend uses the Harvesta design (light cream theme, sidebar navigation,
aerial map hero, NPK / Lost Area Index / Soil Moisture widget grid, floating
chat bar). Design tokens live in `frontend/tailwind.config.js` and
`frontend/src/index.css`. All 10 pages (auth + app) follow this system.

## 🤖 Demo Mode

No backend? Click **"Test Login (no backend needed)"** on the login page to
explore the full Harvesta dashboard with sample data (Aanya Sharma ·
Greenfield Acres · 4 crops).

---

## 🛠️ Technology Stack
- **Frontend**: React 19, Vite, Tailwind CSS (Harvesta design system)
- **Backend**: Python 3.13, FastAPI, Uvicorn, SQLAlchemy ORM, SQLite/PostgreSQL
- **Authentication**: JWT Tokens, HMAC-SHA256 Password Hashing, Email Verification
- **External Integration**: Open-Meteo REST Weather API
- **Testing**: Pytest & FastAPI TestClient
