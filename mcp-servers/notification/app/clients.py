"""HTTP clients for downstream services (backend ws-push + db-mcp audit log)."""
from __future__ import annotations

import logging

import httpx

from .config import settings

logger = logging.getLogger("notification-mcp.clients")


async def push_ws(user_id: str, payload: dict) -> bool:
    headers = {"X-Service-Token": settings.service_token}
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as ac:
            r = await ac.post(
                f"{settings.backend_url}/internal/ws/push",
                headers=headers,
                json={"user_id": user_id, "payload": payload},
            )
            return r.status_code == 202
    except Exception as exc:
        logger.warning("ws push failed: %s", exc)
        return False


async def log_notification(record: dict) -> None:
    headers = {"X-Service-Token": settings.service_token}
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as ac:
            await ac.post(
                f"{settings.db_mcp_url}/notifications",
                headers=headers,
                json=record,
            )
    except Exception as exc:
        logger.warning("notification log failed: %s", exc)
