"""SMTP-or-console emitter. Falls back to console logging when SMTP is unset."""
from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from .config import settings

logger = logging.getLogger("notification-mcp.email")


def _send_sync(to: str, subject: str, body: str) -> tuple[bool, str | None]:
    if not settings.smtp_host:
        logger.info("[CONSOLE EMAIL] to=%s subject=%s\n%s", to, subject, body)
        return True, None

    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as s:
            if settings.smtp_use_tls:
                s.starttls()
            if settings.smtp_user and settings.smtp_password:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return True, None
    except Exception as exc:
        logger.warning("smtp send failed: %s", exc)
        return False, str(exc)


async def send(to: str, subject: str, body: str) -> tuple[bool, str | None]:
    return await asyncio.to_thread(_send_sync, to, subject, body)
