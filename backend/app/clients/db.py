from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import ServiceClient


class DbClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(settings.db_mcp_url)

    async def create_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/jobs", json=payload)

    async def create_prediction(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/predictions", json=payload)

    async def list_user_jobs(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return await self.get_json(f"/users/{user_id}/jobs", params={"limit": limit})
