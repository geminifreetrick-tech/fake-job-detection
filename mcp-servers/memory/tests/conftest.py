import os
import sys
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("SERVICE_TOKEN", "test-service-token")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))


@pytest_asyncio.fixture
async def client(monkeypatch):
    # Replace the Chroma HTTP client with an in-memory EphemeralClient for tests.
    import chromadb

    from app import store as store_mod

    fake = chromadb.EphemeralClient()
    store_mod.set_client(fake)

    from app import main as main_mod

    transport = ASGITransport(app=main_mod.app)
    headers = {"X-Service-Token": os.environ["SERVICE_TOKEN"]}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac
