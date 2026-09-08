# 🚀 HOW TO RUN — Smart Agriculture AI (Harvesta UI v2.1)

## ⚡ EASIEST WAY (One Click)

1. **Extract this entire ZIP** to a NEW empty folder (e.g., `C:\Harvesta-v21`)
   ⚠️ Do NOT extract into an existing project folder!
2. Open the extracted `Smart-Agriculture-AI` folder
3. **Windows:** Double-click **`START-HERE-WINDOWS.bat`**
   **Mac/Linux:** Run **`./START-HERE-MAC-LINUX.sh`** in terminal
4. Your browser opens at **http://localhost:5173** automatically
5. Click **"Test Login (no backend needed)"** → Dashboard appears!

## ✅ HOW TO KNOW YOU'RE RUNNING THE RIGHT VERSION

| Check | What you should see |
|-------|---------------------|
| Login page bottom | `HARVESTA UI · v2.1 · OFFICIAL BUILD` |
| Sidebar (after login) | Green `v2.1` badge next to Harvesta logo |
| Dashboard style | **Light cream** design, "Field 01" aerial map hero, NPK Levels card, Soil Moisture chart |

## ❌ IF YOU SEE THE WRONG DESIGN

If you see a **dark-green** design with "Good Evening, **Rajesh**", **Punjab, India** weather,
or FARMS/CROPS/ALERTS stat cards — you are running an **OLD/DIFFERENT project**, not this ZIP!

**Fix:** Close that terminal/browser tab. Extract THIS ZIP into a brand-new folder. Run the START script again.

## 🖥️ Run with FULL backend (optional — for AI analysis, signup, database)

```bash
# Terminal 1 — Backend (Python 3.10+ required)
cd Smart-Agriculture-AI
python -m venv venv
venv\Scripts\activate        # Windows (or: source venv/bin/activate on Mac/Linux)
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd Smart-Agriculture-AI/frontend
npm install
npm run dev
```

## 📋 Requirements

- **Node.js 18+** → https://nodejs.org (LTS version) — *required*
- **Python 3.10+** → only needed for the backend (optional for UI viewing)

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| `node: command not found` | Install Node.js from nodejs.org, then re-run START script |
| Page shows old design | You're in the wrong folder! Extract this ZIP fresh, run its START script |
| `npm install` fails | Check internet, delete `frontend/node_modules`, run START script again |
| Browser shows blank page | Hard-refresh with Ctrl+Shift+R (or Cmd+Shift+R on Mac) |
| Port 5173 busy | Close other Node windows, or run `npm run dev -- --port 5174` |
