from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os

from backend.app.database import Base, engine, sync_database_schema
from backend.app.routes.ai import router as ai_router
from backend.app.routes.weather import router as weather_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.history import router as history_router
from backend.app.routes.dashboard import router as dashboard_router
from backend.app.routes.farms import router as farms_router
from backend.app.routes.admin import router as admin_router
from backend.app.routes.notifications import router as notifications_router
from backend.app.routes.disease import router as disease_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.sensors import router as sensors_router
from backend.app.routes.account import router as account_router
from backend.app.routes.inventory import router as inventory_router
from backend.app.routes.reports import router as reports_router

# Safely migrate SQLite schema for existing database files
sync_database_schema()

# Create database tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Agriculture AI Platform API",
    description="Backend API for Smart Agriculture AI Platform providing weather, IoT, ML crop insights, authentication with email verification, and persistent field analysis history.",
    version="1.0.0"
)

# Configure CORS so the React frontend can communicate with the FastAPI backend.
# Local development origins are always allowed; production origins come from
# environment configuration (FRONTEND_URL + optional comma-separated extras).
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)

extra_origins = os.getenv("CORS_EXTRA_ORIGINS", "")
for extra in extra_origins.split(","):
    cleaned = extra.strip().rstrip("/")
    if cleaned and cleaned not in origins:
        origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # Permit only localhost and RFC1918 private-network browser origins for
    # phone testing. Public deployments still use FRONTEND_URL/CORS_EXTRA_ORIGINS.
    allow_origin_regex=(
        r"^https?://(localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|"
        r"192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})"
        r"(?::\d+)?$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(ai_router)
app.include_router(weather_router)
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(dashboard_router)
app.include_router(farms_router)
app.include_router(admin_router)
app.include_router(notifications_router)
app.include_router(disease_router)
app.include_router(chat_router)
app.include_router(sensors_router)
app.include_router(account_router)
app.include_router(inventory_router)
app.include_router(reports_router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Smart Agriculture AI Platform API",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
def get_health():
    return {
        "status": "ok",
        "service": "Smart Agriculture AI Platform"
    }
