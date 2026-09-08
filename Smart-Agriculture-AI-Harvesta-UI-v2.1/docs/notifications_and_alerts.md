# Farmer Notification Center & Farm Alert System (Phase C)

## 1. Overview

The **Harvesta Notification Center & Farm Alert System** provides timely, actionable agronomic telemetry and security advisories to farmers both in-app and via email.

All notification records are strictly bound to authenticated user accounts, ensuring full multi-tenant isolation, granular preference controls, and non-blocking background notification dispatching.

---

## 2. Notification Architecture

```
[ Farm Events / Telemetry ]
   ├── AI Field Analysis ──> Irrigation Alert Trigger (threshold / dry soil)
   ├── Open-Meteo Weather ─> Microclimate Advisory (temp ≥38°C, precip ≥20mm, wind ≥35km/h with 6h cooldown)
   └── Auth Lifecycle ──────> Security Notice (email verified, password reset completed)
             │
             ▼
    [ NotificationService ]
             │
   ┌─────────┴─────────┐
   ▼                   ▼
[ In-App Database ]  [ EmailService (SMTP) ]
(notifications table) (if email_enabled & HIGH priority)
```

---

## 3. REST API Endpoints

All notification routes require `Bearer` token authentication via the `Authorization` header.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/notifications` | Returns paginated notifications for the authenticated farmer (`total`, `unread_count`, `notifications`). Supports `limit`, `offset`, and `unread_only`. |
| `GET` | `/api/notifications/unread-count` | Returns `{ "unread_count": <int> }` for responsive bell badge rendering. |
| `PATCH` | `/api/notifications/{id}/read` | Marks an individual notification as read. Returns `404` if the notification does not exist or belongs to another farmer. |
| `POST` | `/api/notifications/mark-all-read` | Marks all unread notifications belonging to the authenticated user as read. |
| `GET` | `/api/notifications/preferences` | Retrieves user notification preference flags (initializes defaults if not yet set). |
| `PUT` | `/api/notifications/preferences` | Updates notification preference toggles and creates an immutable audit record. |

---

## 4. Alert Categories & Triggers

| Category | Type Identifier | Description & Trigger Conditions | Default Channel |
| :--- | :--- | :--- | :--- |
| **Irrigation AI** | `IRRIGATION_ALERT` | Triggered when field analysis reports dry soil moisture or recommend irrigation. High priority alerts dispatch email if enabled. | In-App / Both |
| **Weather Advisory** | `WEATHER` | Triggered when live weather exceeds conservative thresholds (Temp $\ge 38^\circ\text{C}$, Precip $\ge 20\,\text{mm}$, Wind $\ge 35\,\text{km/h}$). Protected by a **6-hour cooldown** deduplication window. | In-App |
| **Account Security** | `SECURITY` | Triggered upon email verification, password reset, and administrator role assignment. Password reset notices dispatch email. | In-App / Both |
| **Crop Disease** | `DISEASE` | Reserved for visual plant diagnostic and pest anomaly scans. | In-App |

---

## 5. Notification Preferences Schema

Farmers can customize notification channels and alert categories at any time from the UI:

```json
{
  "email_enabled": true,
  "irrigation_alerts": true,
  "weather_alerts": true,
  "security_alerts": true,
  "disease_alerts": true
}
```

- Disabling a category completely suppresses new alert creation for that domain.
- Disabling `email_enabled` restricts delivery to in-app only while preserving in-app notifications.

---

## 6. Frontend UI Components

1. **`NotificationBell.jsx`**:
   - Integrated into the Dashboard topbar.
   - Dynamic unread count badge.
   - Interactive dropdown with unread filtering, individual "mark read" click actions, and "Mark all read" button.
2. **`Notifications.jsx`**:
   - Full-page notifications center with category filtering tabs.
3. **`NotificationSettings.jsx`**:
   - Dedicated preferences management page with instant saving and audit logging.
