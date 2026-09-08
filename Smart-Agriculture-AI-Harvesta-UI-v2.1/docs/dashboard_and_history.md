# Farmer Dashboard, Database Persistence & Analysis History Documentation 🌾📊

This document provides a detailed overview of the database architecture, authentication security, persistent field analysis history, and farmer dashboard implementation in the **Smart Agriculture AI Platform**.

---

## 1. Database Architecture & Schema

The application uses an embedded **SQLite** relational database (`data/smart_agriculture.db`) managed via **SQLAlchemy ORM**.

### 1.1 `users` Table Schema

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique user identifier |
| `email` | `VARCHAR(255)` | `UNIQUE, NOT NULL, INDEXED` | Farmer email address |
| `full_name` | `VARCHAR(255)` | `NOT NULL` | Farmer full display name |
| `hashed_password` | `VARCHAR(255)` | `NOT NULL` | Salted HMAC-SHA256 password hash |
| `is_verified` | `BOOLEAN` | `DEFAULT TRUE` | Email verification status |
| `created_at` | `DATETIME` | `NOT NULL` | UTC creation timestamp |

### 1.2 `field_analysis_history` Table Schema

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique history record ID |
| `user_id` | `INTEGER` | `FOREIGN KEY(users.id), INDEXED` | Owner user ID |
| `crop_type` | `VARCHAR(100)` | `NOT NULL` | Crop species |
| `latitude` | `FLOAT` | `NOT NULL` | Geographical latitude coordinate |
| `longitude` | `FLOAT` | `NOT NULL` | Geographical longitude coordinate |
| `current_soil_moisture`| `FLOAT` | `NOT NULL` | Soil moisture percentage |
| `soil_ph` | `FLOAT` | `NOT NULL` | Soil pH level |
| `soil_temperature` | `FLOAT` | `NOT NULL` | Soil temperature (°C) |
| `weather_temperature` | `FLOAT` | `NOT NULL` | Fetched air temperature (°C) |
| `weather_humidity` | `FLOAT` | `NOT NULL` | Fetched air humidity (%) |
| `weather_precipitation`| `FLOAT` | `NOT NULL` | Fetched precipitation depth (mm) |
| `weather_wind_speed` | `FLOAT` | `NOT NULL` | Fetched wind speed (km/h) |
| `recommendation_status`| `VARCHAR(100)`| `NOT NULL` | Recommendation action (`IRRIGATION_REQUIRED`, `MONITOR`, `NO_IRRIGATION_NEEDED`) |
| `priority` | `VARCHAR(50)` | `NOT NULL` | Priority level (`HIGH`, `MEDIUM`, `LOW`) |
| `reason` | `TEXT` | `NOT NULL` | Primary recommendation rationale |
| `factors` | `TEXT` | `NOT NULL` | JSON string array of key factors |
| `created_at` | `DATETIME` | `NOT NULL, INDEXED` | UTC timestamp (ordered newest first) |

---

## 2. Authentication & Data Security Architecture

### 2.1 Token Authorization
- Authentication relies on standard **JSON Web Tokens (JWT)** passed via HTTP headers (`Authorization: Bearer <token>`).
- Tokens expire after 7 days (`ACCESS_TOKEN_EXPIRE_DAYS = 7`).

### 2.2 Strict User Ownership Isolation
- **Server-Driven User Binding**: All history creation endpoints bind records to `current_user.id` derived directly from the verified JWT payload. Arbitrary `user_id` values passed in request payloads are ignored.
- **Access Control Enforcer**: Queries for individual history records (`GET /api/history/field-analysis/{id}`) or deletion (`DELETE /api/history/field-analysis/{id}`) explicitly enforce `FieldAnalysisHistory.user_id == current_user.id`.
- **Zero Information Leakage**: Attempting to access or delete another user's record returns `HTTP 404 Not Found` rather than revealing record existence to potential unauthorized users.

---

## 3. Backend API Specification

### Authentication Endpoints
- `POST /api/auth/signup`: Create farmer account. Returns JWT access token and user object.
- `POST /api/auth/login`: Authenticate email & password. Returns JWT access token.
- `GET /api/auth/me`: Get current authenticated user profile.
- `POST /api/auth/verify-email`: Email verification status endpoint.

### Field Analysis & History Endpoints
- `POST /api/ai/field-analysis`: Authenticated endpoint that fetches real-time weather, computes explainable recommendation, persists result to DB, and returns response containing `history_id`.
- `POST /api/history/field-analysis`: Save a field analysis manually.
- `GET /api/history/field-analysis`: Retrieve authenticated user's history list (newest first, supports pagination).
- `GET /api/history/field-analysis/{id}`: Retrieve single history item owned by current user.
- `DELETE /api/history/field-analysis/{id}`: Delete history item owned by current user.

### Dashboard Summary Endpoint
- `GET /api/dashboard/summary`: Computes farmer dashboard metrics:
  - `total_analyses`
  - `irrigation_required_count`
  - `monitor_count`
  - `no_irrigation_needed_count`
  - `high_priority_count`
  - `latest_analysis_timestamp`

---

## 4. Frontend Dashboard Flow

1. **Authentication Guard**:
   - On page load, `App.jsx` verifies token presence and backend health.
   - If unauthenticated, displays modern agricultural `Login` / `Signup` views.
2. **Authenticated Farmer Dashboard**:
   - Header shows platform title, active farmer email, and Logout button.
   - **Summary Cards Section**: Renders `DashboardSummary` component with live counts.
   - **Interactive Action Panels**: Allows switching between `AI Field Analysis (Real Weather)` and `Custom Parameter Recommendation`.
   - **Recent Field Analyses Section**: Renders `AnalysisHistory` list with interactive item details, recommendation status badges, and confirmation-based deletion.
