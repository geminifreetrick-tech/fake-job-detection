"""Thin async HTTP client used by the backend gateway to call MCP servers."""
from __future__ import annotations

import os
from typing import Any

import httpx


class ServiceClient:
    """Wraps httpx.AsyncClient with service-token injection and request-id propagation."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        token = os.environ.get("SERVICE_TOKEN", "")
        headers = {"X-Service-Token": token}
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers=headers,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get(self, path: str, **kw) -> httpx.Response:
        return await self._client.get(path, **kw)

    async def post(self, path: str, **kw) -> httpx.Response:
        return await self._client.post(path, **kw)

    async def delete(self, path: str, **kw) -> httpx.Response:
        return await self._client.delete(path, **kw)

    async def json(self, method: str, path: str, **kw) -> Any:
        resp = await self._client.request(method, path, **kw)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()
