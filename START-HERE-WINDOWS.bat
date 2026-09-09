@echo off
REM ============================================================
REM   SMART AGRICULTURE AI - HARVESTA UI v2.1 - ONE CLICK START
REM   This is the OFFICIAL Harvesta UI version.
REM   If you see "Rajesh / Punjab / Good Evening" design,
REM   you are running a DIFFERENT (old) folder!
REM ============================================================
title Smart Agriculture AI - Harvesta UI v2.1
color 0A

echo.
echo  ============================================================
echo    SMART AGRICULTURE AI - HARVESTA UI v2.1 (OFFICIAL)
echo  ============================================================
echo.
echo  This version shows: light cream dashboard, "Field 01" hero
echo  with aerial map, NPK Levels, Soil Moisture chart, sidebar
echo  with Dashboard/Fields/Equipment/Climate/Alerts/Inventory.
echo.
echo  VERIFICATION: After the app opens, look for the green
echo  "v2.1" badge next to the Harvesta logo in the sidebar.
echo  No badge = wrong folder is running.
echo.

REM ---- Check Node.js ----
where node >nul 2>nul
if errorlevel 1 (
    color 0C
    echo  [ERROR] Node.js is not installed!
    echo  Download and install it from: https://nodejs.org
    echo  Choose the "LTS" version. Then run this file again.
    echo.
    pause
    exit /b 1
)
echo  [OK] Node.js found:
node --version

REM ---- Go to frontend folder ----
cd /d "%~dp0frontend"
if not exist package.json (
    color 0C
    echo  [ERROR] Cannot find frontend\package.json
    echo  Make sure you extracted the FULL ZIP first,
    echo  then run this file from inside the project folder.
    echo.
    pause
    exit /b 1
)

REM ---- Install dependencies on first run ----
if not exist node_modules (
    echo.
    echo  [SETUP] First run - installing dependencies...
    echo  This can take 2-5 minutes. Please wait...
    echo.
    call npm install
    if errorlevel 1 (
        color 0C
        echo  [ERROR] npm install failed. Check your internet connection.
        pause
        exit /b 1
    )
)

REM ---- Start the app ----
echo.
echo  [START] Launching Harvesta UI v2.1 ...
echo.
echo  The app will open in your browser at: http://localhost:5173
echo  Login page shows "HARVESTA UI - v2.1 - OFFICIAL BUILD" text.
echo.
echo  Click "Test Login (no backend needed)" to see the dashboard.
echo.
echo  Keep this window OPEN while using the app.
echo  To stop: close this window or press Ctrl+C.
echo.
start "" "http://localhost:5173"
call npm run dev
pause
