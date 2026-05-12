from __future__ import annotations

from typing import Any

import httpx

from ..core.config import settings


class ServiceClient:
    """httpx-backed async client with service-token injection."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"X-Service-Token": settings.service_token},
        )

    @property
    def http(self) -> httpx.AsyncClient:
        return self._client

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_json(self, path: str, **kw) -> Any:
        r = await self._client.get(path, **kw)
        r.raise_for_status()
        return r.json() if r.content else None

    async def post_json(self, path: str, **kw) -> Any:
        r = await self._client.post(path, **kw)
        r.raise_for_status()
        return r.json() if r.content else None
