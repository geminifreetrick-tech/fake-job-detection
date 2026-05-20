import os
import sys
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("SERVICE_TOKEN", "test-service-token")
# Force fallback path so tests don't depend on real Google credentials.
os.environ.pop("GOOGLE_CSE_API_KEY", None)
os.environ.pop("GOOGLE_CSE_ENGINE_ID", None)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))


@pytest_asyncio.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    headers = {"X-Service-Token": os.environ["SERVICE_TOKEN"]}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac
