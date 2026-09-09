"""
Safe Local SMTP Configuration Diagnostic Tool.
Verifies Gmail SMTP settings without revealing credentials or sending unauthorized emails.
"""

import os
import sys
import smtplib

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.app.services.email_service import EmailService

def verify_smtp_configuration():
    print("==================================================")
    print("   GMAIL SMTP CONFIGURATION DIAGNOSTIC CHECK")
    print("==================================================")
    
    backend_env = os.path.join(WORKSPACE_ROOT, "backend", ".env")
    env_exists = os.path.exists(backend_env)
    print(f"1. backend/.env file present: {env_exists}")
    
    config = EmailService.get_config()
    
    required_vars = [
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "FRONTEND_URL"
    ]
    
    print("\n2. Variable Presence Checks:")
    all_vars_present = True
    for var in required_vars:
        val = os.getenv(var)
        is_set = bool(val and val.strip())
        print(f"   - {var}: {'[SET]' if is_set else '[MISSING]'}")
        if not is_set:
            all_vars_present = False
            
    print(f"\n3. Loaded SMTP Settings (Safe View):")
    print(f"   - Host: {config['host']}")
    print(f"   - Port: {config['port']} (STARTTLS)")
    print(f"   - Username: {config['username'] if config['username'] else '[NOT SET]'}")
    print(f"   - From Email: {config['from_email']}")
    print(f"   - Frontend URL: {config['frontend_url']}")
    print(f"   - Password: {'[CONFIGURED (Hidden for Security)]' if config['password'] and config['password'] != 'your_gmail_app_password' else '[PLACEHOLDER / NOT SET]'}")
    
    # Check if using placeholders
    is_placeholder_user = config['username'] in ('', 'your_gmail_address@gmail.com', 'your_gmail_address@gmail.com')
    is_placeholder_pass = config['password'] in ('', 'your_gmail_app_password')
    
    if is_placeholder_user or is_placeholder_pass:
        print("\n==================================================")
        print("RESULT: PLACEHOLDER CREDENTIALS DETECTED")
        print("To send REAL emails via Gmail SMTP, edit 'backend/.env' and replace:")
        if is_placeholder_user:
            print("  - SMTP_USERNAME=your_real_gmail@gmail.com")
            print("  - SMTP_FROM_EMAIL=your_real_gmail@gmail.com")
        if is_placeholder_pass:
            print("  - SMTP_PASSWORD=your_16_character_gmail_app_password")
        print("==================================================")
        return False
        
    # Attempt dry-run TLS handshake with smtp.gmail.com:587
    print("\n4. Testing SMTP Server Connection (smtp.gmail.com:587 STARTTLS)...")
    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            print("   -> Connected to smtp.gmail.com and completed STARTTLS handshake.")
            try:
                server.login(config["username"], config["password"])
                print("   -> SMTP Authentication: SUCCESSFUL! Real Gmail credentials verified.")
                print("\n==================================================")
                print("RESULT: GMAIL SMTP CONFIGURATION IS 100% VALID & READY!")
                print("==================================================")
                return True
            except smtplib.SMTPAuthenticationError:
                print("   -> SMTP Authentication: FAILED (Invalid Username or App Password).")
                print("==================================================")
                print("RESULT: Invalid Gmail App Password or Username.")
                print("Please check 2-Step Verification & App Password in Google Account.")
                print("==================================================")
                return False
    except Exception as e:
        print(f"   -> Connection Error: {e}")
        return False

if __name__ == "__main__":
    verify_smtp_configuration()
