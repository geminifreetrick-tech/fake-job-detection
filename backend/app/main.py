from __future__ import annotations

import logging
import sys
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# `_common` is shipped from mcp-servers; in Docker it's copied to /app/_common.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from _common.logging import configure_logging  # type: ignore
except Exception:  # pragma: no cover
    def configure_logging() -> None:
        logging.basicConfig(level=logging.INFO)

from .api import auth as auth_router
from .api import jobs as jobs_router
from .api import me as me_router
from .core.config import settings
from .ws.routes import router as ws_router


configure_logging()

app = FastAPI(title="fjd-backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(auth_router.router, prefix=PREFIX)
app.include_router(jobs_router.router, prefix=PREFIX)
app.include_router(me_router.router, prefix=PREFIX)
app.include_router(ws_router)  # WS lives at /ws (no prefix)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "service": "backend"}


@app.get(f"{PREFIX}/healthz")
async def healthz_v1() -> dict:
    """Aggregated health: pings downstream services with a short timeout."""
    targets = {
        "auth-mcp": f"{settings.auth_mcp_url}/healthz",
        "db-mcp": f"{settings.db_mcp_url}/healthz",
        "ml-engine": f"{settings.ml_engine_url}/healthz",
        "memory-mcp": f"{settings.memory_mcp_url}/healthz",
    }
    results: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in targets.items():
            try:
                r = await client.get(url)
                results[name] = "ok" if r.status_code == 200 else f"unhealthy:{r.status_code}"
            except Exception as exc:  # pragma: no cover
                results[name] = f"unreachable:{type(exc).__name__}"
    ok = all(v == "ok" for v in results.values())
    return {"status": "ok" if ok else "degraded", "dependencies": results}
