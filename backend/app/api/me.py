from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..clients import DbClient, MemoryClient
from ..core.security import CurrentUser, get_current_user
from ..deps import get_db_client, get_memory_client

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/jobs")
async def my_jobs(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[DbClient, Depends(get_db_client)],
    limit: int = Query(20, ge=1, le=100),
):
    try:
        return await db.list_user_jobs(user.user_id, limit=limit)
    finally:
        await db.aclose()


@router.get("/context")
async def my_context(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    memory: Annotated[MemoryClient, Depends(get_memory_client)],
    limit: int = Query(5, ge=1, le=20),
    query_text: str | None = Query(default=None),
):
    try:
        return await memory.context(user.user_id, limit=limit, query_text=query_text)
    finally:
        await memory.aclose()
