from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _common.security import require_service_token  # noqa: E402

from .cse import CseUnavailable, search as cse_search
from .scoring import compute
from .schemas import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    VerifyCompanyRequest,
    VerifyCompanyResponse,
)
from .whois_lookup import lookup as whois_lookup

logger = logging.getLogger("websearch-mcp")

router = APIRouter(dependencies=[Depends(require_service_token)])


async def _do_search(query: str, num: int) -> tuple[list[dict], str]:
    try:
        items = await cse_search(query, num=num)
        return items, "google_cse"
    except CseUnavailable:
        return [], "fallback"
    except Exception as exc:  # pragma: no cover - external API quirks
        logger.warning("CSE error: %s", exc)
        return [], "fallback"


@router.post("/search", response_model=SearchResponse)
async def search_endpoint(body: SearchRequest) -> SearchResponse:
    items, provider = await _do_search(body.query, body.num)
    return SearchResponse(
        results=[SearchResultItem(**i) for i in items],
        provider=provider,
    )


@router.post("/verify-company", response_model=VerifyCompanyResponse)
async def verify_company(body: VerifyCompanyRequest) -> VerifyCompanyResponse:
    query = f'"{body.name}" official site'
    if body.domain:
        query = f"{body.name} site:{body.domain}"
    items, provider = await _do_search(query, 7)

    whois_blob = None
    if body.domain:
        whois_blob = await whois_lookup(body.domain)

    scored = compute(body.name, body.domain, items, whois_blob)
    return VerifyCompanyResponse(
        name=body.name,
        domain=body.domain,
        legitimacy_score=scored["legitimacy_score"],
        signals=scored["signals"],
        whois=whois_blob,
        search_results=[SearchResultItem(**i) for i in items],
        provider=provider,
    )
