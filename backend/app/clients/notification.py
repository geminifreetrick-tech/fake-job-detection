from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import ServiceClient


class NotificationClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(settings.notification_mcp_url, timeout=15.0)

    async def send_email(
        self, user_id: str, to: str, template: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.post_json(
            "/email",
            json={
                "user_id": user_id,
                "to": to,
                "template": template,
                "context": context,
            },
        )

    async def send_ws(
        self, user_id: str, event: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.post_json(
            "/ws",
            json={"user_id": user_id, "event": event, "payload": payload},
        )
