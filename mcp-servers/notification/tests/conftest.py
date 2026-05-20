import os
import sys
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("SERVICE_TOKEN", "test-service-token")
os.environ.pop("SMTP_HOST", None)  # force console-email mode

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
