from __future__ import annotations

import time
from typing import Any

from .config import settings


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl = ttl_seconds
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        v = self._data.get(key)
        if not v:
            return None
        ts, val = v
        if time.time() - ts > self.ttl:
            self._data.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any) -> None:
        self._data[key] = (time.time(), value)


cache = TTLCache(settings.cache_ttl_seconds)
