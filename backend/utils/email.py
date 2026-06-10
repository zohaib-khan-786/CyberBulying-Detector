"""
Email utility — sends password reset emails via SMTP.
Configured via environment variables (see .env.example).
"""

from __future__ import annotations

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def _get_smtp_config() -> dict | None:
    host = os.getenv("SMTP_HOST", "").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    if not host or not username:
        return None
    return {
        "host": host,
        "port": int(os.getenv("SMTP_PORT", "587")),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        "username": username,
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_addr": os.getenv("SMTP_FROM", "noreply@cyberguard.local").strip(),
        "from_name": os.getenv("APP_NAME", "AI-Powered Cyberbullying Detection"),
    }


def is_smtp_configured() -> bool:
    return _get_smtp_config() is not None


def send_password_reset_email(recipient: str, reset_token: str) -> bool:
    cfg = _get_smtp_config()
    if not cfg:
        logger.warning("SMTP not configured — cannot send email to %s", recipient)
        return False

    reset_url = os.getenv(
        "APP_URL",
        "http://localhost:8080",
    ).rstrip("/") + f"/reset-password?token={reset_token}"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 0; }}
    .container {{ max-width: 520px; margin: 40px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
    .header {{ background: linear-gradient(135deg, #3B82F6, #8B5CF6); padding: 28px 32px; text-align: center; }}
    .header h1 {{ color: #fff; font-size: 20px; margin: 0; font-weight: 700; }}
    .body {{ padding: 32px; }}
    .body p {{ font-size: 14px; color: #475569; line-height: 1.6; margin: 0 0 16px; }}
    .btn {{ display: inline-block; background: linear-gradient(135deg, #3B82F6, #8B5CF6); color: #fff !important; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-size: 14px; font-weight: 600; }}
    .footer {{ padding: 20px 32px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center; }}
    .code {{ font-family: 'Courier New', monospace; font-size: 13px; background: #f1f5f9; padding: 10px 14px; border-radius: 6px; word-break: break-all; color: #3B82F6; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Password Reset</h1>
    </div>
    <div class="body">
      <p>Hello,</p>
      <p>We received a request to reset the password for your account on <strong>{cfg['from_name']}</strong>.</p>
      <p style="text-align: center; margin: 24px 0;">
        <a class="btn" href="{reset_url}">Reset Password</a>
      </p>
      <p>Or copy this reset code into the app:</p>
      <div class="code">{reset_token}</div>
      <p style="margin-top: 20px; font-size: 13px; color: #94a3b8;">This code expires in 1 hour. If you did not request this, you can safely ignore this email.</p>
    </div>
    <div class="footer">
      &copy; {cfg['from_name']} &mdash; Automated message, do not reply.
    </div>
  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Password Reset — {cfg['from_name']}"
    msg["From"] = f"{cfg['from_name']} <{cfg['from_addr']}>"
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    try:
        if cfg["use_tls"]:
            server = smtplib.SMTP(cfg["host"], cfg["port"])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"])

        if cfg["username"] and cfg["password"]:
            server.login(cfg["username"], cfg["password"])

        server.sendmail(cfg["from_addr"], [recipient], msg.as_string())
        server.quit()
        logger.info("Password reset email sent to %s", recipient)
        return True
    except Exception as exc:
        logger.exception("Failed to send email to %s: %s", recipient, exc)
        return False
