from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import ServiceClient


class FilesystemClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(settings.filesystem_mcp_url, timeout=60.0)

    async def upload(
        self, filename: str, content_type: str, data: bytes
    ) -> dict[str, Any]:
        files = {"file": (filename, data, content_type)}
        r = await self.http.post("/uploads", files=files)
        r.raise_for_status()
        return r.json()

    async def get_upload(self, sha: str) -> bytes | None:
        r = await self.http.get(f"/uploads/{sha}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content

    async def render_report(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/reports", json=body)

    async def fetch_report(self, sha: str, download: bool = False) -> bytes | None:
        r = await self.http.get(f"/reports/{sha}", params={"download": str(download).lower()})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content
