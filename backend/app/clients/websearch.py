from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import ServiceClient


class WebSearchClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(settings.websearch_mcp_url, timeout=20.0)

    async def search(self, query: str, num: int = 5) -> dict[str, Any]:
        return await self.post_json("/search", json={"query": query, "num": num})

    async def verify_company(self, name: str, domain: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name}
        if domain:
            body["domain"] = domain
        return await self.post_json("/verify-company", json=body)
