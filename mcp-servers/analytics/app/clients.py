from __future__ import annotations

import httpx

from .config import settings


def _headers() -> dict[str, str]:
    return {"X-Service-Token": settings.service_token}


async def get_summary() -> dict:
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as ac:
        r = await ac.get(f"{settings.db_mcp_url}/analytics/summary", headers=_headers())
        r.raise_for_status()
        return r.json()


async def get_fraud_over_time(days: int) -> dict:
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as ac:
        r = await ac.get(
            f"{settings.db_mcp_url}/analytics/fraud-over-time",
            params={"days": days},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


async def get_top_features(limit: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as ac:
        r = await ac.get(
            f"{settings.db_mcp_url}/analytics/top-scam-features",
            params={"limit": limit},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()
