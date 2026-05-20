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

from .api import admin as admin_router
from .api import auth as auth_router
from .api import awareness as awareness_router
from .api import companies as companies_router
from .api import files as files_router
from .api import internal as internal_router
from .api import jobs as jobs_router
from .api import me as me_router
from .api import reports as reports_router
from .core.config import settings
from .ws.routes import router as ws_router


configure_logging()

app = FastAPI(title="fjd-backend", version="0.2.0")

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
app.include_router(reports_router.router, prefix=PREFIX)
app.include_router(awareness_router.router, prefix=PREFIX)
app.include_router(companies_router.router, prefix=PREFIX)
app.include_router(files_router.router, prefix=PREFIX)
app.include_router(admin_router.router, prefix=PREFIX)
app.include_router(internal_router.router)  # /internal/* (no /api/v1)
app.include_router(ws_router)  # WS at /ws (no prefix)


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
        "filesystem-mcp": f"{settings.filesystem_mcp_url}/healthz",
        "websearch-mcp": f"{settings.websearch_mcp_url}/healthz",
        "notification-mcp": f"{settings.notification_mcp_url}/healthz",
        "analytics-mcp": f"{settings.analytics_mcp_url}/healthz",
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
