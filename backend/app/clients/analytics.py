from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import ServiceClient


class AnalyticsClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(settings.analytics_mcp_url, timeout=15.0)

    async def summary(self) -> dict[str, Any]:
        return await self.get_json("/summary")

    async def fraud_over_time(self, days: int = 30) -> dict[str, Any]:
        return await self.get_json("/fraud-over-time", params={"days": days})

    async def top_features(self, limit: int = 10) -> list[dict[str, Any]]:
        return await self.get_json("/top-features", params={"limit": limit})

    async def dashboard(self) -> dict[str, Any]:
        return await self.get_json("/dashboard")
