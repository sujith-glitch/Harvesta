# Analytics & Privacy Architecture Guide

## 1. Overview

The **Smart Agriculture AI Platform (Harvesta v2.1)** incorporates platform telemetry and company analytics designed from the ground up around **data minimization, tenant isolation, and farmer privacy**.

Analytics data provides administrative visibility into feature adoption, system reliability, and active user engagement without monitoring intrusive farmer behaviors or logging sensitive credentials.

---

## 2. What Is Stored & Why

| Data Item | Storage Model | Business Purpose | Privacy Safeguard |
|---|---|---|---|
| **Session Timestamps** | `user_sessions.login_at`, `last_active_at`, `logout_at` | Active user tracking, concurrent session limits, platform KPIs | Stored only at minute resolution |
| **Session Duration** | `user_sessions.duration_seconds` | Aggregated engagement and platform usage statistics | Computed upon logout or session timeout |
| **Client Platform & Device** | `user_sessions.device_type`, `platform` | Optimizing mobile vs desktop UI performance | Coarse categories only (e.g. `desktop` / `mobile`, `Windows` / `iOS`) |
| **Network Identifier** | `user_sessions.ip_hash` | Security anomaly detection & abuse rate limiting | **One-way SHA-256 hash**; raw IP addresses are never persisted |
| **Feature Event Counts** | `activity_events.event_name`, `feature` | Understanding which features farmers use (e.g. Irrigation AI vs Farms) | Abstract event names only (`farm_created`, `analysis_run`) |
| **Audit Logs** | `audit_logs` | Accountability for security-critical actions (role promotions, deletions) | Strictly excludes passwords, tokens, and payloads |

---

## 3. What Is Explicitly Excluded (Never Stored)

The platform strictly prohibits collecting or storing:
1. ❌ **No Plaintext Passwords or Hashes in Analytics:** Password hashes reside strictly in `users.hashed_password` and are never queried or exported.
2. ❌ **No Plain JWT Tokens in Telemetry:** Access tokens are ephemeral bearer credentials passed via `Authorization` headers; they are never persisted in session or event tables.
3. ❌ **No Raw IP Addresses:** Network IDs are hashed immediately in memory with SHA-256 prior to database persistence.
4. ❌ **No Keystroke / Continuous Cursor Tracking:** No client-side keylogging, mouse tracking, or invasive DOM recordings.
5. ❌ **No Sensitive Form Bodies in Logs:** Payload bodies for personal notes, credentials, or custom inputs are never logged to `activity_events` or `audit_logs`.

---

## 4. Active Session Lifecycle & Thresholds

* **Active Session Threshold:** A session is classified as active if `logout_at IS NULL` and `last_active_at` was recorded within the last **30 minutes**.
* **Zero Aggressive Polling:** Heartbeats or activity timestamps update only on authenticated user interactions or sensible 10-minute intervals — never pinging every few seconds.

---

## 5. Data Retention & Compliance Recommendations

For production deployment (GDPR, CCPA, and agricultural data privacy compliance):
1. **Activity Events Retention:** Retain raw `activity_events` for 90 days, after which automated scheduled tasks aggregate them into anonymized monthly KPIs and purge individual records.
2. **User Session Retention:** Retain `user_sessions` for 180 days for security auditing, then delete records older than 6 months.
3. **Right to Erasure (Account Deletion):** Deleting a user account cleanly cascades through foreign keys:
   - Cascades and permanently removes all sessions, notifications, preferences, and chat threads.
   - Nullifies `user_id` on audit logs and historical weather snapshots (`ON DELETE SET NULL`) to maintain system audit continuity without retaining personal identity links.
