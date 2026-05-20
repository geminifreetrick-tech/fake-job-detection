from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common.logging import configure_logging  # noqa: E402

configure_logging()

from .routes import router  # noqa: E402

app = FastAPI(title="analytics-mcp", version="0.1.0")
app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "service": "analytics-mcp"}
