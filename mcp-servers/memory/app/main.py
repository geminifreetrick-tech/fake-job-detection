from __future__ import annotations

import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common.logging import configure_logging  # noqa: E402

from .routes import router
from .store import bootstrap, seed_known_scams

logger = logging.getLogger("memory-mcp")
_SEED_PATH = Path(__file__).resolve().parent / "seed_known_scams.json"


@asynccontextmanager
async def _lifespan(app: FastAPI):
    configure_logging()
    try:
        bootstrap()
    except Exception as exc:  # pragma: no cover
        logger.warning("chroma bootstrap failed: %s", exc)
    if _SEED_PATH.exists():
        try:
            items = json.loads(_SEED_PATH.read_text())
            if isinstance(items, list) and items:
                n = seed_known_scams(items)
                logger.info("seeded %d known_scams from %s", n, _SEED_PATH)
        except Exception as exc:  # pragma: no cover
            logger.warning("seed failed: %s", exc)
    yield


app = FastAPI(title="memory-mcp", version="0.1.0", lifespan=_lifespan)
app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "service": "memory-mcp"}
