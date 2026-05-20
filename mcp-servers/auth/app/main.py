from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common.logging import configure_logging  # noqa: E402

from .db import init_db
from .routes import router
from .seed import seed_admin


@asynccontextmanager
async def _lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    try:
        await seed_admin()
    except Exception:
        pass
    yield


app = FastAPI(title="auth-mcp", version="0.1.0", lifespan=_lifespan)
app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "service": "auth-mcp"}
