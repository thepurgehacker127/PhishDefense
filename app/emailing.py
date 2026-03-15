# app/emailing.py
import os
import smtplib
import secrets
from email.message import EmailMessage
from jinja2 import Template
from dotenv import load_dotenv

# Load .env
load_dotenv()

# SMTP / App settings
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER") or None
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or None
SMTP_FROM = os.getenv("SMTP_FROM", "Security Training <training@example.local>")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

def gen_token(length: int = 24) -> str:
    """Generate a URL-safe token for per-recipient tracking."""
    return secrets.token_urlsafe(length)

def render_email(subject: str, html_body: str, recipient_first_name: str | None, token: str):
    """
    Renders the HTML email by injecting the tracking pixel and unique link.
    Supports Jinja-like placeholders: {{ first_name }}, {{ unique_link }}, {{ open_pixel_url }}.
    """
    open_pixel_url = f"{BASE_URL}/t/{token}.png"
    unique_link = f"{BASE_URL}/o/{token}"

    html = Template(html_body).render(
        first_name=recipient_first_name or "there",
        unique_link=f'<a href="{unique_link}">',  # opener; template should close </a>
        open_pixel_url=f'<img src="{open_pixel_url}" width="1" height="1" style="display:none" alt="."/>'
    )
    return subject, html

def send_training_email(to_email: str, subject: str, html: str):
    """
    Sends the training email using SMTP. In dev, this should hit MailHog (localhost:1025).
    """
    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    # Mark for SOC/gateways that this is a simulation
    msg["X-Phish-Sim"] = "true"
    msg.add_header("List-Unsubscribe", "<mailto:security-training@example.local>")

    # Plaintext fallback + HTML alt
    msg.set_content("This message contains HTML content for security training.")
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        # Some dev SMTP servers (like MailHog) don't support TLS or auth; try and ignore failures.
        try:
            s.starttls()
        except Exception:
            pass
        if SMTP_USER and SMTP_PASSWORD:
            s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)