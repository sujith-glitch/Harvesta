# Harvesta 3D Dashboard and Data Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add fast, accessible 3D-style dashboard motion and a documented, validated starter data pipeline for Harvesta’s agriculture models.

**Architecture:** Keep animation in a small reusable React component and CSS layer. Keep datasets versioned as manifests and compact samples, with Python validation/loaders producing model-ready files. Preserve existing backend fallbacks and expose provenance through existing service responses.

**Tech Stack:** React, Vite, CSS, FastAPI, Python, pandas, existing scikit-learn/joblib models, pytest.

**Spec:** `docs/superpowers/specs/2026-09-09-harvesta-3d-data-upgrade-design.md`

## Global Constraints

- Use CSS transforms, opacity, gradients, and existing icon assets; do not add a heavy WebGL runtime.
- Respect `prefers-reduced-motion` and keep mobile performance fast.
- Keep secrets and personal data out of datasets.
- Record source, license, retrieval date, and field definitions for every dataset.
- Preserve prototype disclaimers and deterministic fallbacks.

### Task 1: Add the accessible 3D-style motion layer

**Files:**
- Create: `frontend/src/components/DashboardMotionLayer.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/App.css`
- Test: `frontend/tests/dashboard-motion.test.jsx`

- [ ] Add a failing test that renders the motion layer and confirms its reduced-motion class/attributes.
- [ ] Implement decorative rings, floating particles, and a pointer-safe parallax wrapper using CSS only.
- [ ] Mount it behind dashboard content without changing navigation or card behavior.
- [ ] Add reduced-motion and small-screen CSS rules.
- [ ] Run the focused frontend test and production build.
- [ ] Commit: `feat: add accessible dashboard motion layer`

### Task 2: Create dataset manifests and compact starter samples

**Files:**
- Create: `data/manifests/datasets.json`
- Create: `data/sample/weather_history.csv`
- Create: `data/sample/soil_crop_suitability.csv`
- Create: `data/sample/pest_reference.csv`
- Create: `data/sample/fertilizer_reference.csv`
- Modify: `data/README.md`

- [ ] Define manifest fields for name, source, license, retrieval date, schema, and limitations.
- [ ] Add clean, clearly labelled starter rows suitable for development and demos.
- [ ] Document that disease image metadata and IoT samples are prototype data until licensed real data is imported.
- [ ] Validate CSV headers and UTF-8 parsing locally.
- [ ] Commit: `data: add documented agriculture starter datasets`

### Task 3: Add reusable validation and dataset loading

**Files:**
- Create: `ml/dataset_registry.py`
- Create: `tests/test_dataset_registry.py`
- Modify: `ml/data_validation.py`

- [ ] Write tests for required columns, numeric ranges, missing values, and manifest provenance.
- [ ] Implement `load_dataset(name: str) -> pandas.DataFrame` and `validate_dataset(name: str, frame: pandas.DataFrame) -> list[str]`.
- [ ] Ensure invalid data returns actionable errors without mutating source files.
- [ ] Run all dataset tests and existing ML tests.
- [ ] Commit: `ml: validate registered agriculture datasets`

### Task 4: Connect provenance and model metadata to the backend

**Files:**
- Modify: `backend/app/services/field_analysis_service.py`
- Modify: `backend/app/services/disease_service.py`
- Modify: `backend/app/main.py`
- Create: `tests/test_model_provenance.py`

- [ ] Add tests confirming responses include model/data version and fallback status.
- [ ] Add a small metadata reader that uses the registry manifest and existing joblib metadata.
- [ ] Include provenance in analysis responses while preserving existing response fields.
- [ ] Verify `/api/health` and relevant analysis endpoints with the backend test suite.
- [ ] Commit: `backend: expose model and dataset provenance`

### Task 5: Verify and prepare deployment

**Files:**
- Modify: `README.md`
- Modify: `DATA-STORAGE-GUIDE.md`
- Modify: `render.yaml` only if required by tests

- [ ] Run frontend tests/build and backend tests.
- [ ] Run a mobile-width smoke check and reduced-motion check.
- [ ] Confirm no secrets or large raw datasets are tracked.
- [ ] Document Render/Vercel environment requirements and redeploy checklist.
- [ ] Commit: `docs: document data upgrade and deployment verification`
