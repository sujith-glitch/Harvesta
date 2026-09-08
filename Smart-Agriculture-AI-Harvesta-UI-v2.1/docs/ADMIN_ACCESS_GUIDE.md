# Harvesta Owner-Admin Access Guide

Harvesta uses two roles:

| Role | What the account can do |
|---|---|
| Farmer | Use the dashboard, farms, crops, field analysis, disease screening, AI chat, notifications, weather, and sensors. A farmer can access only records owned by that farmer and cannot open company/database views. |
| Admin | Use every normal farmer feature and open the read-only Admin Portal for company-wide users, usage, sessions, audit history, and approved operational datasets. |

## Admin access is intentionally limited

The Admin Portal can view:

- Platform totals and feature usage.
- Registered farmer names, email addresses, verification state, and role.
- Login times, session activity, device/platform information, and duration.
- Farms, crops, field analyses, alerts, AI history, disease-screening records, weather history, and sensor history.
- Security and administrator audit events.

The Admin Portal cannot view:

- Passwords or password hashes.
- Verification or password-reset token hashes.
- Login JWTs, sensor device keys, Gmail passwords, Supabase service keys, or database credentials.
- Raw IP addresses.

The Admin Portal is read-only. It does not directly edit or delete database rows and cannot promote another account. This is deliberate least-privilege protection.

## Step-by-step: create the owner-admin

Do this only after `backend/.env` contains the correct `DATABASE_URL`. When Supabase is configured, the command below updates Supabase; otherwise it updates the local development database.

1. Start Harvesta normally.
2. Use **Sign up** to create your owner account.
3. Open the Gmail verification email and verify the account.
4. Log in once to confirm that the account works.
5. Open PowerShell in the project root.
6. Run the following command, replacing the example email with the exact verified owner email:

```powershell
.\backend\.venv\Scripts\python.exe scripts\promote_admin.py your-owner-email@gmail.com
```

7. Wait for the `[SUCCESS]` message.
8. Log out of Harvesta and log in again.
9. Open **Admin Portal** in the left navigation. On a phone, use the shield icon in the bottom navigation.
10. Open **Stored Data** to view the approved company-wide database records.

Run the promotion command only for the trusted company owner. Every public signup always starts as `farmer`; users cannot request or assign the admin role from the website or Android app.

## Step-by-step: confirm a normal farmer is blocked

1. Sign up with a second email address and verify it.
2. Log in using that second account.
3. Confirm that **Admin Portal** and the mobile shield icon are not shown.
4. Confirm that the farmer can still use farms, crops, analysis, AI, disease screening, alerts, and sensors.
5. Even if someone changes browser values or manually calls `/api/admin/...`, the server checks the role in the database and returns `403 Forbidden`.

## Important operating rules

- Keep only the company owner's account as admin unless another trusted administrator is genuinely required.
- Never change a role using frontend code or browser developer tools.
- Never place `DATABASE_URL`, `JWT_SECRET_KEY`, `SMTP_PASSWORD`, `SUPABASE_SECRET_KEY`, or the legacy `SUPABASE_SERVICE_ROLE_KEY` in the frontend.
- Review **Audit Logs** regularly for administrator and account-security events.
- Use separate accounts for administration and ordinary testing when the app goes live.
