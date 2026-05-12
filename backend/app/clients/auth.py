from __future__ import annotations

from typing import Any

from ..core.config import settings
from .base import ServiceClient


class AuthClient(ServiceClient):
    def __init__(self) -> None:
        super().__init__(settings.auth_mcp_url)

    async def signup(self, email: str, password: str) -> dict[str, Any]:
        return await self.post_json("/signup", json={"email": email, "password": password})

    async def login(self, email: str, password: str) -> dict[str, Any]:
        return await self.post_json("/login", json={"email": email, "password": password})

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        return await self.post_json("/refresh", json={"refresh_token": refresh_token})
