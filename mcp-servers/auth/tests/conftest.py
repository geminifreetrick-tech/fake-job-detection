import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("SERVICE_TOKEN", "test-service-token")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))  # for `_common`


@pytest_asyncio.fixture
async def client(tmp_path, monkeypatch):
    db_path = tmp_path / "auth.db"
    test_url = f"sqlite+aiosqlite:///{db_path}"

    # Recreate engine/session against the test sqlite DB
    from app import db as db_mod

    engine = create_async_engine(test_url, echo=False, future=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db_mod, "engine", engine, raising=False)
    monkeypatch.setattr(db_mod, "SessionLocal", SessionLocal, raising=False)

    async def _get_session():
        async with SessionLocal() as s:
            yield s

    from app import main as main_mod

    main_mod.app.dependency_overrides[db_mod.get_session] = _get_session

    async with engine.begin() as conn:
        await conn.run_sync(db_mod.Base.metadata.create_all)

    transport = ASGITransport(app=main_mod.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    main_mod.app.dependency_overrides.clear()
    await engine.dispose()
