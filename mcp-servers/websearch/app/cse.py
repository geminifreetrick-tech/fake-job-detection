"""Google Custom Search Engine wrapper. Returns a normalized result list."""
from __future__ import annotations

import httpx

from .config import settings


class CseUnavailable(RuntimeError):
    pass


async def search(query: str, num: int = 5) -> list[dict]:
    if not settings.google_cse_api_key or not settings.google_cse_engine_id:
        raise CseUnavailable("google_cse_api_key/engine_id not configured")
    params = {
        "key": settings.google_cse_api_key,
        "cx": settings.google_cse_engine_id,
        "q": query,
        "num": max(1, min(num, 10)),
    }
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as ac:
        r = await ac.get("https://www.googleapis.com/customsearch/v1", params=params)
        r.raise_for_status()
        data = r.json()
    items: list[dict] = []
    for it in data.get("items", []):
        items.append(
            {
                "title": it.get("title", ""),
                "snippet": it.get("snippet", ""),
                "url": it.get("link", ""),
                "display_link": it.get("displayLink", ""),
            }
        )
    return items
