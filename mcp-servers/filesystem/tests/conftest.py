import os
import sys
import tempfile
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("SERVICE_TOKEN", "test-service-token")
_TMP = tempfile.mkdtemp(prefix="fjd-fs-test-")
os.environ["UPLOAD_DIR"] = str(Path(_TMP) / "uploads")
os.environ["REPORTS_DIR"] = str(Path(_TMP) / "reports")

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
