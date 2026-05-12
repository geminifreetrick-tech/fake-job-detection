import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_create_job_and_prediction(client):
    job_body = {
        "user_id": "user-1",
        "raw_text": "We are hiring remote bitcoin agents!",
        "source_type": "text",
        "sha256": "deadbeef" * 8,
    }
    r = await client.post("/jobs", json=job_body)
    assert r.status_code == 201, r.text
    job = r.json()

    pred_body = {
        "job_id": job["id"],
        "label": "fraud",
        "score": 0.93,
        "explanation": {"top": [{"feature": "salary_unrealistic", "weight": 0.4}]},
        "model_version": "v1",
    }
    r2 = await client.post("/predictions", json=pred_body)
    assert r2.status_code == 201
    assert r2.json()["label"] == "fraud"


@pytest.mark.asyncio
async def test_idempotent_job_insert(client):
    body = {
        "user_id": "u1",
        "raw_text": "x",
        "source_type": "text",
        "sha256": "a" * 64,
    }
    r1 = await client.post("/jobs", json=body)
    r2 = await client.post("/jobs", json=body)
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.asyncio
async def test_requires_service_token(tmp_path, monkeypatch):
    import os
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT.parent))

    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app import db as db_mod
    from app import main as main_mod

    db_path = tmp_path / "x.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    SL = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db_mod, "engine", engine, raising=False)
    monkeypatch.setattr(db_mod, "SessionLocal", SL, raising=False)

    async def _gs():
        async with SL() as s:
            yield s

    main_mod.app.dependency_overrides[db_mod.get_session] = _gs
    async with engine.begin() as conn:
        await conn.run_sync(db_mod.Base.metadata.create_all)

    transport = ASGITransport(app=main_mod.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/jobs",
            json={"user_id": "u", "raw_text": "x", "source_type": "text", "sha256": "a" * 64},
        )
    assert r.status_code == 401
    main_mod.app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_list_user_jobs(client):
    for i in range(3):
        await client.post(
            "/jobs",
            json={
                "user_id": "u-list",
                "raw_text": f"posting {i}",
                "source_type": "text",
                "sha256": f"{i:064d}",
            },
        )
    r = await client.get("/users/u-list/jobs?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 3
    assert body[0]["job"]["user_id"] == "u-list"
