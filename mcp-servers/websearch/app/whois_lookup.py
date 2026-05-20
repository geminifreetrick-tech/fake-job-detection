"""Thin sync→async wrapper around python-whois with conservative error handling."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("websearch-mcp.whois")


def _normalize_date(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, list):
        v = v[0] if v else None
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, str):
        return v
    return None


def _sync_whois(domain: str) -> dict | None:
    try:
        import whois  # python-whois
    except Exception as exc:
        logger.warning("python-whois import failed: %s", exc)
        return None
    try:
        w = whois.whois(domain)
    except Exception as exc:
        logger.info("whois lookup failed for %s: %s", domain, exc)
        return None
    if not w or not getattr(w, "domain_name", None):
        return None
    return {
        "domain_name": (
            w.domain_name[0] if isinstance(w.domain_name, list) and w.domain_name else w.domain_name
        )
        if w.domain_name
        else domain,
        "registrar": getattr(w, "registrar", None),
        "creation_date": _normalize_date(getattr(w, "creation_date", None)),
        "expiration_date": _normalize_date(getattr(w, "expiration_date", None)),
        "name_servers": list({str(ns).lower() for ns in (getattr(w, "name_servers", None) or []) if ns}),
        "country": getattr(w, "country", None),
        "org": getattr(w, "org", None),
    }


async def lookup(domain: str) -> dict | None:
    return await asyncio.to_thread(_sync_whois, domain)


def age_days(whois_blob: dict | None) -> int | None:
    if not whois_blob or not whois_blob.get("creation_date"):
        return None
    try:
        created = datetime.fromisoformat(whois_blob["creation_date"].replace("Z", "+00:00"))
    except Exception:
        return None
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - created
    return max(0, delta.days)
