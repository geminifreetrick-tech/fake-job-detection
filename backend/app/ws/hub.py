"""Minimal in-process WebSocket pub/sub keyed by user_id.

This is intentionally simple for Phase 1; replace with Redis pub/sub if you
horizontally scale the gateway.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


_subscribers: dict[str, set[WebSocket]] = defaultdict(set)
_lock = asyncio.Lock()


async def subscribe(user_id: str, ws: WebSocket) -> None:
    async with _lock:
        _subscribers[user_id].add(ws)


async def unsubscribe(user_id: str, ws: WebSocket) -> None:
    async with _lock:
        _subscribers[user_id].discard(ws)
        if not _subscribers[user_id]:
            _subscribers.pop(user_id, None)


async def broadcast(user_id: str, payload: dict[str, Any]) -> int:
    async with _lock:
        subs = list(_subscribers.get(user_id, ()))
    sent = 0
    for ws in subs:
        try:
            await ws.send_json(payload)
            sent += 1
        except Exception:
            await unsubscribe(user_id, ws)
    return sent
