@echo off
title Harvesta UI v2.1 - Quick Start
color 0A

echo ============================================================
echo   Starting Smart Agriculture AI (Harvesta UI v2.1)
echo ============================================================
echo.

set "BASE_DIR=%~dp0"
if exist "%BASE_DIR%Smart-Agriculture-AI-Harvesta-UI-v2.1\frontend" (
    set "PROJECT_DIR=%BASE_DIR%Smart-Agriculture-AI-Harvesta-UI-v2.1"
) else (
    set "PROJECT_DIR=%BASE_DIR%"
)

REM Start Backend in separate window if python venv exists
if exist "%PROJECT_DIR%\backend\.venv\Scripts\python.exe" (
    echo [OK] Starting FastAPI Backend on http://localhost:8000 ...
    start "Harvesta Backend" cmd /k "cd /d "%PROJECT_DIR%" && backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000"
)

REM Open browser
start "" "http://localhost:5173"

REM Start Frontend
echo [OK] Starting Frontend Vite Server on http://localhost:5173 ...
cd /d "%PROJECT_DIR%\frontend"
call npm run dev
