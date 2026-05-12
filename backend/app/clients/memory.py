from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import ServiceClient


class MemoryClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(settings.memory_mcp_url)

    async def upsert(self, collection: str, items: list[dict[str, Any]]) -> None:
        await self.post_json(f"/collections/{collection}/upsert", json={"items": items})

    async def context(self, user_id: str, limit: int = 5, query_text: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if query_text:
            params["query_text"] = query_text
        return await self.get_json(f"/context/{user_id}", params=params)
