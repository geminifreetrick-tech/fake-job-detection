import os
import sys
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("SERVICE_TOKEN", "test-service-token")
os.environ.setdefault("AUTH_MCP_URL", "http://auth-mcp.test")
os.environ.setdefault("DB_MCP_URL", "http://db-mcp.test")
os.environ.setdefault("ML_ENGINE_URL", "http://ml-engine.test")
os.environ.setdefault("MEMORY_MCP_URL", "http://memory-mcp.test")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "mcp-servers"))


@pytest_asyncio.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_access_token(user_id: str = "user-1", role: str = "user") -> str:
    """Mint an access token compatible with the backend's local validation."""
    import time

    import jwt

    payload = {
        "sub": user_id,
        "role": role,
        "kind": "access",
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")
