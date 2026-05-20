import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_composes_db_responses(client, monkeypatch):
    async def fake_summary():
        return {
            "total_jobs": 10,
            "total_fraud": 4,
            "total_legit": 6,
            "fraud_rate": 0.4,
            "users": 3,
            "reports_open": 1,
            "avg_fraud_score": 0.81,
        }

    async def fake_fot(days):
        return {"fraud": [], "legit": []}

    async def fake_feats(limit):
        return [{"feature": "scam_marker_score", "count": 7}]

    from app import routes as routes_mod

    monkeypatch.setattr(routes_mod, "get_summary", fake_summary)
    monkeypatch.setattr(routes_mod, "get_fraud_over_time", fake_fot)
    monkeypatch.setattr(routes_mod, "get_top_features", fake_feats)
    from app import cache as cache_mod

    cache_mod.cache._data.clear()

    r = await client.get("/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total_fraud"] == 4
    assert body["top_features"][0]["feature"] == "scam_marker_score"


@pytest.mark.asyncio
async def test_cache_returns_same_value(client, monkeypatch):
    calls = {"n": 0}

    async def fake_summary():
        calls["n"] += 1
        return {"total_jobs": calls["n"]}

    async def fake_fot(days):
        return {}

    async def fake_feats(limit):
        return []

    from app import cache as cache_mod
    from app import routes as routes_mod

    cache_mod.cache._data.clear()
    monkeypatch.setattr(routes_mod, "get_summary", fake_summary)
    monkeypatch.setattr(routes_mod, "get_fraud_over_time", fake_fot)
    monkeypatch.setattr(routes_mod, "get_top_features", fake_feats)

    r1 = await client.get("/summary")
    r2 = await client.get("/summary")
    assert r1.json() == r2.json()
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_requires_service_token():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/summary")
    assert r.status_code == 401
