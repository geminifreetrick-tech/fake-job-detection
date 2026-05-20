from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common.logging import configure_logging  # noqa: E402

from .config import settings
from .routes import router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    configure_logging()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="filesystem-mcp", version="0.1.0", lifespan=_lifespan)
app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "service": "filesystem-mcp"}
