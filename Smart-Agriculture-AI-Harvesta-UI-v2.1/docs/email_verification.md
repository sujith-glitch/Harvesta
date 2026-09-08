# Gmail Real Email Verification Setup Guide ✉️🔐

This document provides step-by-step instructions for configuring **Gmail SMTP** in the **Smart Agriculture AI Platform** to send real HTML verification emails to newly registered farmers.

---

## 1. Gmail SMTP Setup Instructions

### Step 1: Create or Select a Gmail Account
Use a dedicated Gmail address for sending automated platform notifications (e.g. `smart.agriculture.ai@gmail.com`).

### Step 2: Enable 2-Step Verification
1. Sign in to your Google Account at [myaccount.google.com](https://myaccount.google.com).
2. On the left navigation panel, select **Security**.
3. Under **How you sign in to Google**, select **2-Step Verification**.
4. Follow the on-screen steps to turn on 2-Step Verification for your account.

### Step 3: Generate a Gmail App Password
> [!IMPORTANT]
> **NEVER** use your personal Gmail password in configuration files. Google blocks basic password authentication for SMTP. You **must** generate a dedicated 16-character **App Password**.

1. In your Google Account, navigate to **Security** -> **2-Step Verification**.
2. Scroll to the bottom of the page and select **App passwords**.
3. Enter an app name (e.g., `Smart Agriculture Platform`).
4. Click **Create**.
5. Google will generate a 16-character passcode (formatted like `abcd efgh ijkl mnop`). Copy this passcode.

---

## 2. Environment Configuration

### Step 4: Create Local `.env` File
Create a new file at `backend/.env` (based on `backend/.env.example`):

```ini
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail_address@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
SMTP_FROM_EMAIL=your_gmail_address@gmail.com
FRONTEND_URL=http://localhost:5173
JWT_SECRET_KEY=smart-agriculture-ai-secure-secret-key-2026
```

Replace `your_gmail_address@gmail.com` with your Gmail address and `abcd efgh ijkl mnop` with your 16-character App Password (spaces will be automatically handled).

---

## 3. Security Guidelines

> [!CAUTION]
> 1. **Never Commit Secrets**: `backend/.env` is excluded from git version control via `.gitignore`. Never commit real passwords, App Passwords, or JWT secret keys to public code repositories.
> 2. **Token Security**: Verification tokens are generated using cryptographically secure random bytes (`secrets.token_urlsafe(32)`). Only SHA-256 hashes of verification tokens are stored in the database (`verification_token_hash`).
> 3. **Token Expiry**: Verification links automatically expire 30 minutes after generation.
