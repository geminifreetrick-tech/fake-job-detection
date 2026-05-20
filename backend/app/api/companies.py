from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends

from ..clients import DbClient, WebSearchClient
from ..core.security import CurrentUser, get_current_user
from ..deps import get_db_client, get_websearch_client
from ..schemas.companies import VerifyCompanyRequest

router = APIRouter(prefix="/companies", tags=["companies"])

_CACHE_HOURS = 24


@router.post("/verify")
async def verify_company(
    body: VerifyCompanyRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[DbClient, Depends(get_db_client)],
    ws: Annotated[WebSearchClient, Depends(get_websearch_client)],
) -> dict:
    try:
        cached = await db.get_company_verification(body.name, body.domain)
        if cached:
            try:
                cu = datetime.fromisoformat(cached["cached_until"].replace("Z", "+00:00"))
            except Exception:
                cu = datetime.now(timezone.utc) - timedelta(days=1)
            if cu > datetime.now(timezone.utc):
                return {**cached, "from_cache": True}

        res = await ws.verify_company(body.name, body.domain)
        cached_until = datetime.now(timezone.utc) + timedelta(hours=_CACHE_HOURS)
        try:
            await db.save_company_verification(
                {
                    "name": body.name,
                    "domain": (body.domain or "").lower() or None,
                    "legitimacy_score": float(res.get("legitimacy_score", 0.0)),
                    "signals": res.get("signals", {}),
                    "whois": res.get("whois"),
                    "search_results": [r for r in res.get("search_results", [])],
                    "cached_until": cached_until.isoformat(),
                }
            )
        except Exception:
            pass
        try:
            await db.record_event(
                {
                    "user_id": user.user_id,
                    "name": "company.verified",
                    "props": {"name": body.name, "score": res.get("legitimacy_score")},
                }
            )
        except Exception:
            pass
        return {**res, "from_cache": False}
    finally:
        await db.aclose()
        await ws.aclose()
