"""
email_sender.py — Sends cold emails via Gmail SMTP.
Uses your Gmail + App Password (no OAuth needed for sending).
"""

import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587


def extract_email_from_snippet(snippet: str, source_url: str) -> str | None:
    """
    Try to pull an email address from the snippet or source URL.
    Returns None if no email found — we'll skip those businesses.
    """
    # Search in snippet first, then source_url
    text = f"{snippet} {source_url}"
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if match:
        return match.group(0).lower()
    return None


def send_email(to_address: str, subject: str, body: str) -> bool:
    """
    Send a plain-text email via Gmail SMTP.
    Returns True on success, False on failure.
    """
    msg = MIMEMultipart()
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = to_address
    msg["Subject"] = subject

    # Plain text body
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_address, msg.as_string())

        print(f"[EMAIL] ✅ Sent to {to_address} — Subject: '{subject}'")
        return True

    except Exception as e:
        print(f"[EMAIL] ❌ Failed to send to {to_address}: {e}")
        return False