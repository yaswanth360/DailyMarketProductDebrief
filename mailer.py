"""Email delivery. Resend if configured, otherwise SMTP."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

import requests

from .config import CONFIG


def send(subject: str, html_body: str, text_body: str) -> None:
    recipients = [r.strip() for r in (CONFIG.email_to or "").split(",") if r.strip()]
    if not recipients:
        raise SystemExit("EMAIL_TO is empty.")

    if CONFIG.resend_api_key:
        _send_resend(subject, html_body, text_body, recipients)
    else:
        _send_smtp(subject, html_body, text_body, recipients)


def _send_resend(subject: str, html_body: str, text_body: str, recipients: list[str]) -> None:
    sender = CONFIG.email_from or "onboarding@resend.dev"
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {CONFIG.resend_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": sender,
            "to": recipients,
            "subject": subject,
            "html": html_body,
            "text": text_body,
        },
        timeout=30,
    )
    if resp.status_code >= 300:
        raise RuntimeError(f"Resend failed [{resp.status_code}]: {resp.text}")
    print(f"  Email sent via Resend to {', '.join(recipients)}")


def _send_smtp(subject: str, html_body: str, text_body: str, recipients: list[str]) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = CONFIG.email_from or CONFIG.smtp_user
    msg["To"] = ", ".join(recipients)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(CONFIG.smtp_host, CONFIG.smtp_port, timeout=45) as server:
        server.starttls()
        server.login(CONFIG.smtp_user, CONFIG.smtp_password)
        server.send_message(msg)
    print(f"  Email sent via SMTP to {', '.join(recipients)}")
