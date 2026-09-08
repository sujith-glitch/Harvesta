"""
Secure SMTP Email Service for dispatching HTML account verification emails.
Supports Gmail SMTP (smtp.gmail.com:587) with STARTTLS encryption.
"""

import os
import smtplib
import logging
from email.utils import formataddr, formatdate, make_msgid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict

try:
    from dotenv import load_dotenv
    # Load backend/.env or root .env
    backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
    if os.path.exists(root_env):
        load_dotenv(root_env)
except ImportError:
    pass

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def delivery_enabled() -> bool:
        """Allow automated tests and local-only installs to disable outbound SMTP."""
        return os.getenv("SMTP_DELIVERY_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}

    @classmethod
    def get_config(cls) -> Dict[str, str]:
        """
        Dynamically fetches current SMTP configuration from environment variables.
        """
        host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME", "").strip()
        password = os.getenv("SMTP_PASSWORD", "").strip()
        from_email = os.getenv("SMTP_FROM_EMAIL", username or "noreply@smartagriculture.ai").strip()
        from_name = os.getenv("SMTP_FROM_NAME", "Harvesta").strip() or "Harvesta"
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

        return {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "from_email": from_email,
            "from_name": from_name,
            "frontend_url": frontend_url
        }

    @staticmethod
    def _build_message(
        config: Dict[str, str],
        to_email: str,
        subject: str,
        plain_text: str,
        html_content: str,
    ) -> MIMEMultipart:
        """Build a standards-friendly multipart email with both text and HTML versions."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((config.get("from_name", "Harvesta"), config["from_email"]))
        msg["To"] = to_email
        msg["Reply-To"] = config["from_email"]
        msg["Date"] = formatdate(localtime=False)
        msg["Message-ID"] = make_msgid(domain=config["from_email"].partition("@")[2] or None)
        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        return msg

    @classmethod
    def build_password_reset_html(cls, to_email: str, full_name: str, raw_token: str) -> str:
        """
        Constructs the HTML body for a password reset email.

        Args:
            to_email: Registered farmer email address
            full_name: Farmer full name
            raw_token: Cryptographically secure password reset token

        Returns:
            str: Complete HTML email content.
        """
        config = cls.get_config()
        reset_link = f"{config['frontend_url']}/reset-password?token={raw_token}"
        display_name = full_name.strip() if full_name else "Farmer"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Outfit', 'Inter', Arial, sans-serif; background-color: #071910; color: #f0fdf4; margin: 0; padding: 20px; }}
                .container {{ max-width: 580px; margin: 0 auto; background: #102c1e; border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 16px; padding: 30px; }}
                .header {{ text-align: center; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 20px; margin-bottom: 20px; }}
                .logo-icon {{ font-size: 42px; display: block; margin-bottom: 10px; }}
                .title {{ font-size: 24px; font-weight: bold; color: #ffffff; margin: 0; }}
                .content {{ font-size: 16px; line-height: 1.6; color: #99f6e4; }}
                .btn-container {{ text-align: center; margin: 30px 0; }}
                .btn {{ background: linear-gradient(135deg, #10b981, #059669); color: #ffffff !important; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: bold; display: inline-block; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4); }}
                .link-text {{ font-size: 13px; color: #6ee7b7; word-break: break-all; margin-top: 15px; }}
                .expiry-notice {{ background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); padding: 12px; border-radius: 8px; font-size: 13px; color: #fde047; margin-top: 25px; }}
                .footer {{ text-align: center; font-size: 12px; color: #6ee7b7; margin-top: 30px; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="logo-icon">🔑</span>
                    <h1 class="title">Smart Agriculture AI Platform</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{display_name}</strong>,</p>
                    <p>We received a request to reset the password for your farmer account (<strong>{to_email}</strong>). Click the button below to choose a new password.</p>

                    <div class="btn-container">
                        <a href="{reset_link}" class="btn" target="_blank">Reset Password</a>
                    </div>

                    <p class="link-text">Or copy and paste this password reset link into your browser:<br>
                    <a href="{reset_link}" style="color: #34d399;">{reset_link}</a></p>

                    <div class="expiry-notice">
                        ⏱️ <strong>Expiry Notice:</strong> This password reset link will expire in <strong>30 minutes</strong> and can only be used once.<br><br>
                        🛡️ <strong>Security Note:</strong> If you did not request a password reset, you can safely ignore this email — your current password will remain unchanged.
                    </div>
                </div>
                <div class="footer">
                    Smart Agriculture AI Platform &copy; 2026 — Empowering Modern Smart Farming
                </div>
            </div>
        </body>
        </html>
        """

    @classmethod
    def send_password_reset_email(cls, to_email: str, full_name: str, raw_token: str) -> bool:
        """
        Constructs and dispatches an HTML password reset email via SMTP.

        Args:
            to_email: Registered farmer email address
            full_name: Farmer full name
            raw_token: Cryptographically secure password reset token

        Returns:
            bool: True if email dispatched successfully or handled safely.
        """
        config = cls.get_config()
        html_content = cls.build_password_reset_html(to_email, full_name, raw_token)

        subject = "Reset your Smart Agriculture AI Platform password"

        reset_link = f"{config['frontend_url']}/reset-password?token={raw_token}"
        plain_text = (
            f"Hello {full_name.strip() if full_name else 'Farmer'},\n\n"
            "Use the link below to reset your Harvesta password. The link expires in 30 minutes.\n\n"
            f"{reset_link}\n\n"
            "If you did not request this, you can ignore this email."
        )
        msg = cls._build_message(config, to_email, subject, plain_text, html_content)

        # Skip actual SMTP connection if username or password is not configured (offline / testing mode)
        if not cls.delivery_enabled() or not config["username"] or not config["password"]:
            logger.warning(f"[OFFLINE MODE] SMTP credentials not set in backend/.env. Simulated email to '{to_email}'. Password Reset Link requested.")
            return True

        try:
            with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(config["username"], config["password"])
                server.sendmail(config["from_email"], [to_email], msg.as_string())
                logger.info(f"Successfully dispatched password reset email to {to_email}")
                return True
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email} via SMTP: {e}")
            return False

    @classmethod
    def send_verification_email(cls, to_email: str, full_name: str, verification_code: str) -> bool:
        """Dispatch a four-digit registration code without including a verification link."""
        config = cls.get_config()
        display_name = full_name.strip() if full_name else "Farmer"
        subject = "Your Harvesta verification code"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Outfit', 'Inter', Arial, sans-serif; background-color: #f4f7ec; color: #202427; margin: 0; padding: 20px; }}
                .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border: 1px solid #e1e7d5; border-radius: 18px; padding: 32px; }}
                .header {{ text-align: center; padding-bottom: 18px; }}
                .logo-icon {{ font-size: 42px; display: block; margin-bottom: 10px; }}
                .title {{ font-size: 24px; font-weight: bold; color: #202427; margin: 0; }}
                .content {{ font-size: 16px; line-height: 1.6; color: #4f5965; }}
                .code {{ margin: 26px auto; padding: 18px 24px; max-width: 230px; border-radius: 14px; background: #dcea4e; color: #1d2419; text-align: center; font-size: 38px; font-weight: 800; letter-spacing: 12px; text-indent: 12px; }}
                .expiry-notice {{ background: #f4f7ec; border: 1px solid #dce5cf; padding: 13px; border-radius: 9px; font-size: 13px; color: #526046; margin-top: 24px; }}
                .footer {{ text-align: center; font-size: 12px; color: #74806a; margin-top: 28px; border-top: 1px solid #e7ebdf; padding-top: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="logo-icon">🌱</span>
                    <h1 class="title">Verify your Harvesta account</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{display_name}</strong>,</p>
                    <p>Enter this four-digit code on the Harvesta registration screen:</p>
                    <div class="code">{verification_code}</div>
                    <div class="expiry-notice">
                        This code expires in <strong>10 minutes</strong>. Do not share it with anyone. If you did not register, ignore this email.
                    </div>
                </div>
                <div class="footer">Harvesta &copy; 2026</div>
            </div>
        </body>
        </html>
        """

        plain_text = (
            f"Hello {display_name},\n\n"
            f"Your Harvesta verification code is: {verification_code}\n\n"
            "Enter this four-digit code on the Harvesta registration screen. "
            "It expires in 10 minutes. Do not share it with anyone."
        )
        msg = cls._build_message(config, to_email, subject, plain_text, html_content)

        # Skip actual SMTP connection if username or password is not configured (offline / testing mode)
        if not cls.delivery_enabled() or not config["username"] or not config["password"]:
            logger.warning(f"[OFFLINE MODE] SMTP credentials not set in backend/.env. Simulated verification-code email to '{to_email}'.")
            return True

        try:
            with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(config["username"], config["password"])
                server.sendmail(config["from_email"], [to_email], msg.as_string())
                logger.info(f"Successfully dispatched verification email to {to_email}")
                return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via SMTP: {e}")
            return False

    @classmethod
    def build_alert_email_html(cls, to_email: str, full_name: str, title: str, message: str, alert_type: str = "ALERT") -> str:
        """
        Constructs the HTML body for a notification/alert email.
        """
        config = cls.get_config()
        dashboard_link = f"{config['frontend_url']}"
        display_name = full_name.strip() if full_name else "Farmer"
        icon = "🌾" if "IRRIGATION" in alert_type.upper() else ("🌦️" if "WEATHER" in alert_type.upper() else "🛡️")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Outfit', 'Inter', Arial, sans-serif; background-color: #071910; color: #f0fdf4; margin: 0; padding: 20px; }}
                .container {{ max-width: 580px; margin: 0 auto; background: #102c1e; border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 16px; padding: 30px; }}
                .header {{ text-align: center; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 20px; margin-bottom: 20px; }}
                .logo-icon {{ font-size: 42px; display: block; margin-bottom: 10px; }}
                .title {{ font-size: 22px; font-weight: bold; color: #ffffff; margin: 0; }}
                .content {{ font-size: 15px; line-height: 1.6; color: #d1fae5; }}
                .alert-card {{ background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(52, 211, 153, 0.25); padding: 16px; border-radius: 10px; margin: 20px 0; }}
                .alert-title {{ font-size: 17px; font-weight: bold; color: #34d399; margin-bottom: 8px; }}
                .alert-body {{ font-size: 14px; color: #ecfdf5; margin: 0; }}
                .btn-container {{ text-align: center; margin: 25px 0; }}
                .btn {{ background: linear-gradient(135deg, #10b981, #059669); color: #ffffff !important; padding: 12px 24px; text-decoration: none; border-radius: 10px; font-weight: bold; display: inline-block; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4); }}
                .footer {{ text-align: center; font-size: 12px; color: #6ee7b7; margin-top: 30px; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="logo-icon">{icon}</span>
                    <h1 class="title">Smart Agriculture AI Harvesta</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{display_name}</strong>,</p>
                    <p>A new agricultural notification has been generated for your account:</p>

                    <div class="alert-card">
                        <div class="alert-title">{title}</div>
                        <p class="alert-body">{message}</p>
                    </div>

                    <div class="btn-container">
                        <a href="{dashboard_link}" class="btn" target="_blank">Open Harvesta Dashboard</a>
                    </div>
                </div>
                <div class="footer">
                    Smart Agriculture AI Platform &copy; 2026 — You received this alert according to your notification preferences.
                </div>
            </div>
        </body>
        </html>
        """

    @classmethod
    def send_alert_email(cls, to_email: str, full_name: str, title: str, message: str, alert_type: str = "ALERT") -> bool:
        """
        Dispatches an automated notification email via SMTP.
        Returns True if dispatched or safely simulated offline, False on error.
        """
        config = cls.get_config()
        html_content = cls.build_alert_email_html(to_email, full_name, title, message, alert_type)
        subject = f"[Harvesta Alert] {title}"

        plain_text = (
            f"Hello {full_name.strip() if full_name else 'Farmer'},\n\n"
            f"{title}\n\n{message}\n\n"
            f"Open Harvesta: {config['frontend_url']}"
        )
        msg = cls._build_message(config, to_email, subject, plain_text, html_content)

        if not cls.delivery_enabled() or not config["username"] or not config["password"]:
            logger.warning(f"[OFFLINE MODE] SMTP credentials not set in backend/.env. Simulated alert email to '{to_email}': {title}")
            return True

        try:
            with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(config["username"], config["password"])
                server.sendmail(config["from_email"], [to_email], msg.as_string())
                logger.info(f"Successfully dispatched alert email to {to_email}: {title}")
                return True
        except Exception as e:
            logger.error(f"Failed to send alert email to {to_email} via SMTP: {e}")
            return False
