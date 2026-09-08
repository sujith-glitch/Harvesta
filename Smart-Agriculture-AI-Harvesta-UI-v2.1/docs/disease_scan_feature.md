# Crop Disease Screening Feature Guide (Phase D)

This document provides a comprehensive guide to the **Crop Disease Vision Screening Feature** introduced in Harvesta v2.1.

---

## 1. Feature Summary

The Crop Disease Vision Screening feature allows farmers to upload or photograph crop foliage to receive immediate AI-powered symptom analysis, confidence ratings, and actionable agronomic management steps.

### Key Capabilities
- **Photo Upload & Camera Capture**: Drag-and-drop file upload and direct mobile camera capture (`accept="image/*"`, `capture="environment"`).
- **Security Hardened Uploads**: Multi-layer MIME verification, Pillow image integrity decoding, size limits (max 5 MB), and UUID file naming.
- **Persistent Scan History**: Full CRUD history stored in PostgreSQL/SQLite (`crop_disease_scans` table) with user data isolation.
- **Smart Notification System**: Generates in-app anomaly notices on disease detection (and optional email for high confidence findings $\ge 85\%$).
- **Integrated Farm/Crop Linking**: Scans can optionally be linked to specific farms and crops.
- **Activity Telemetry**: Scans log `disease_scan` events for platform analytics.

---

## 2. API Endpoints

### 1. `POST /api/ai/disease-scan`
Uploads leaf photograph for ML analysis.
- **Auth**: Bearer JWT (Required).
- **Body (`multipart/form-data`)**:
  - `file`: Image binary (JPEG, PNG, WebP $\le 5$ MB).
  - `farm_id` *(Optional)*: Integer.
  - `crop_id` *(Optional)*: Integer.
- **Response (200 OK)**:
```json
{
  "id": 42,
  "scan_id": 42,
  "predicted_crop": "Tomato",
  "predicted_disease": "Early Blight",
  "display_name": "Tomato Early Blight (Alternaria solani)",
  "confidence": 0.8842,
  "is_healthy": false,
  "urgency": "MEDIUM",
  "description": "Characterized by concentric ringed brown lesions...",
  "recommendations": [
    "Prune and safely destroy heavily infected lower leaves.",
    "Avoid overhead irrigation; water at soil level to minimize leaf wetness duration.",
    "Apply organic mulch around plant bases to prevent soil-to-leaf spore splash."
  ],
  "recommendation": "Prune and safely destroy heavily infected lower leaves...",
  "top_predictions": [
    { "class_key": "Tomato___Early_Blight", "label": "Tomato Early Blight (Alternaria solani)", "confidence": 0.8842 },
    { "class_key": "Tomato___Leaf_Mold", "label": "Tomato Leaf Mold (Passalora fulva)", "confidence": 0.0712 },
    { "class_key": "Tomato___Healthy", "label": "Healthy Tomato Leaf", "confidence": 0.0446 }
  ],
  "model_version": "harvesta-disease-vision-v1.0",
  "disclaimer": "Smart Agriculture AI Harvesta crop disease screening is an artificial intelligence assistance tool...",
  "image_path": "uploads/disease_scans/scan_abcdef1234567890.jpg",
  "created_at": "2026-08-30T13:30:00Z"
}
```

### 2. `GET /api/disease-scans`
Lists authenticated user's scan history (paginated, newest first).
- **Query Params**: `limit` (default 50), `offset` (default 0), `farm_id`, `crop_id`.

### 3. `GET /api/disease-scans/{id}`
Retrieves single scan details. Enforces user ownership.

### 4. `DELETE /api/disease-scans/{id}`
Deletes scan record and associated local disk image. Enforces user ownership.

### 5. `GET /api/disease-scans/{id}/image`
Streams stored scan image securely to authenticated owners.

---

## 3. Frontend UI Components

- **Page**: `frontend/src/pages/DiseaseScan.jsx`
- **Navigation**: "Disease Scan" added to `AppNav.jsx` and routed in `App.jsx`.
- **API Client**: `frontend/src/services/api.js` (`scanCropDisease`, `getDiseaseScans`, `getDiseaseScan`, `deleteDiseaseScan`).
- **Offline / Demo Mode**: Fully mockable with simulated predictions and demo storage keys.
