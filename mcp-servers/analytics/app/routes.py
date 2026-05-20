from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, Query

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _common.security import require_service_token  # noqa: E402

from .cache import cache
from .clients import get_fraud_over_time, get_summary, get_top_features

router = APIRouter(dependencies=[Depends(require_service_token)])


@router.get("/summary")
async def summary() -> dict:
    cached = cache.get("summary")
    if cached is not None:
        return cached
    data = await get_summary()
    cache.set("summary", data)
    return data


@router.get("/fraud-over-time")
async def fraud_over_time(days: int = Query(default=30, ge=1, le=365)) -> dict:
    key = f"fot:{days}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    data = await get_fraud_over_time(days)
    cache.set(key, data)
    return data


@router.get("/top-features")
async def top_features(limit: int = Query(default=10, ge=1, le=50)) -> list[dict]:
    key = f"feats:{limit}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    data = await get_top_features(limit)
    cache.set(key, data)
    return data


@router.get("/dashboard")
async def dashboard() -> dict:
    """Convenience composite for the admin dashboard."""
    cached = cache.get("dashboard")
    if cached is not None:
        return cached
    summary_data = await get_summary()
    fot = await get_fraud_over_time(30)
    feats = await get_top_features(8)
    data = {"summary": summary_data, "fraud_over_time": fot, "top_features": feats}
    cache.set("dashboard", data)
    return data
