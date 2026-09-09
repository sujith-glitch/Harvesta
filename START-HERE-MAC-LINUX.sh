#!/bin/bash
# ============================================================
#   SMART AGRICULTURE AI - HARVESTA UI v2.1 - ONE CLICK START
#   This is the OFFICIAL Harvesta UI version.
#   If you see "Rajesh / Punjab / Good Evening" design,
#   you are running a DIFFERENT (old) folder!
# ============================================================

echo ""
echo "  ============================================================"
echo "    SMART AGRICULTURE AI - HARVESTA UI v2.1 (OFFICIAL)"
echo "  ============================================================"
echo ""
echo "  This version shows: light cream dashboard, 'Field 01' hero"
echo "  with aerial map, NPK Levels, Soil Moisture chart, sidebar"
echo "  with Dashboard/Fields/Equipment/Climate/Alerts/Inventory."
echo ""
echo "  VERIFICATION: look for the green 'v2.1' badge next to the"
echo "  Harvesta logo in the sidebar. No badge = wrong folder."
echo ""

# ---- Check Node.js ----
if ! command -v node &> /dev/null; then
    echo "  [ERROR] Node.js is not installed!"
    echo "  Install it from https://nodejs.org (LTS version), then run again."
    exit 1
fi
echo "  [OK] Node.js found: $(node --version)"

# ---- Go to frontend folder ----
cd "$(dirname "$0")/frontend" || exit 1
if [ ! -f package.json ]; then
    echo "  [ERROR] Cannot find frontend/package.json"
    echo "  Extract the FULL ZIP first, then run this script from inside the project."
    exit 1
fi

# ---- Install dependencies on first run ----
if [ ! -d node_modules ]; then
    echo ""
    echo "  [SETUP] First run - installing dependencies (2-5 minutes)..."
    echo ""
    npm install || { echo "  [ERROR] npm install failed. Check internet."; exit 1; }
fi

# ---- Start the app ----
echo ""
echo "  [START] Launching Harvesta UI v2.1 ..."
echo ""
echo "  Open in browser: http://localhost:5173"
echo "  Login page shows 'HARVESTA UI - v2.1 - OFFICIAL BUILD' text."
echo "  Click 'Test Login (no backend needed)' to see the dashboard."
echo ""
echo "  Keep this terminal OPEN. To stop: press Ctrl+C."
echo ""

# Try to open browser (best effort, works on mac and some linux)
( sleep 4 && (open "http://localhost:5173" 2>/dev/null || xdg-open "http://localhost:5173" 2>/dev/null) ) &

npm run dev
