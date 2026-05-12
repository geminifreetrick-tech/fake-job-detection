from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _common.security import require_service_token  # noqa: E402

from .config import settings
from .schemas import (
    ContextResponse,
    DeleteRequest,
    QueryMatch,
    QueryRequest,
    QueryResponse,
    UpsertRequest,
)
from .store import get_or_create

router = APIRouter(dependencies=[Depends(require_service_token)])


def _matches_from_query(res: dict) -> list[QueryMatch]:
    matches: list[QueryMatch] = []
    ids = (res.get("ids") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    for i, doc, meta, dist in zip(ids, docs, metas, dists):
        matches.append(
            QueryMatch(id=str(i), document=doc or "", metadata=meta or {}, distance=float(dist))
        )
    return matches


def _matches_from_get(res: dict) -> list[QueryMatch]:
    matches: list[QueryMatch] = []
    ids = res.get("ids") or []
    docs = res.get("documents") or []
    metas = res.get("metadatas") or []
    for i, doc, meta in zip(ids, docs, metas):
        matches.append(QueryMatch(id=str(i), document=doc or "", metadata=meta or {}))
    return matches


@router.post("/collections/{name}/upsert", response_model=None)
async def upsert(name: str, body: UpsertRequest) -> Response:
    coll = get_or_create(name)
    coll.upsert(
        ids=[i.id for i in body.items],
        documents=[i.document for i in body.items],
        metadatas=[i.metadata or {"_": True} for i in body.items],
    )
    return Response(status_code=204)


@router.post("/collections/{name}/query", response_model=QueryResponse)
async def query(name: str, body: QueryRequest) -> QueryResponse:
    coll = get_or_create(name)
    res = coll.query(
        query_texts=body.query_texts,
        n_results=body.n_results,
        where=body.where,
    )
    return QueryResponse(matches=_matches_from_query(res))


@router.delete("/collections/{name}/items", response_model=None)
async def delete_items(name: str, body: DeleteRequest) -> Response:
    coll = get_or_create(name)
    coll.delete(ids=body.ids)
    return Response(status_code=204)


@router.get("/context/{user_id}", response_model=ContextResponse)
async def context(
    user_id: str,
    limit: int = Query(default=5, ge=1, le=50),
    query_text: str | None = Query(default=None),
) -> ContextResponse:
    user_coll = get_or_create(settings.collection_user_context)
    scams_coll = get_or_create(settings.collection_known_scams)
    recent_raw = user_coll.get(where={"user_id": user_id}, limit=limit)
    recent = _matches_from_get(recent_raw)
    similar: list[QueryMatch] = []
    if query_text:
        q = scams_coll.query(query_texts=[query_text], n_results=limit)
        similar = _matches_from_query(q)
    elif recent:
        # Use the most recent document as anchor.
        anchor = recent[0].document
        q = scams_coll.query(query_texts=[anchor], n_results=limit)
        similar = _matches_from_query(q)
    return ContextResponse(recent=recent, similar_scams=similar)


@router.post("/admin/seed-known-scams", status_code=200)
async def seed_known_scams_endpoint(body: dict) -> dict:
    """Seed the known_scams collection from a JSON body for admin/setup flows."""
    items = body.get("items")
    if not isinstance(items, list) or not items:
        raise HTTPException(400, "items[] required")
    from .store import seed_known_scams

    n = seed_known_scams(items)
    return {"seeded": n}
