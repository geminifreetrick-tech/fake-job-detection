import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_upsert_and_query(client):
    body = {
        "items": [
            {"id": "j1", "document": "work from home data entry $5000 week", "metadata": {"user_id": "u1"}},
            {"id": "j2", "document": "senior software engineer python fastapi", "metadata": {"user_id": "u1"}},
        ]
    }
    r = await client.post("/collections/user_context/upsert", json=body)
    assert r.status_code == 204

    q = {"query_texts": ["earn 5000 a week from home"], "n_results": 2}
    r2 = await client.post("/collections/user_context/query", json=q)
    assert r2.status_code == 200
    matches = r2.json()["matches"]
    assert matches
    assert matches[0]["id"] in {"j1", "j2"}


@pytest.mark.asyncio
async def test_context_returns_recent_and_scams(client):
    await client.post(
        "/admin/seed-known-scams",
        json={
            "items": [
                {"id": "s1", "document": "wire transfer crypto money mule"},
                {"id": "s2", "document": "package reshipping agent receive forward"},
            ]
        },
    )
    await client.post(
        "/collections/user_context/upsert",
        json={
            "items": [
                {"id": "u-job-1", "document": "send wire transfer to crypto wallet", "metadata": {"user_id": "alice"}},
            ]
        },
    )
    r = await client.get("/context/alice?limit=3")
    assert r.status_code == 200
    body = r.json()
    assert body["recent"]
    assert body["similar_scams"]


@pytest.mark.asyncio
async def test_delete_items(client):
    await client.post(
        "/collections/user_context/upsert",
        json={"items": [{"id": "del-me", "document": "to delete"}]},
    )
    r = await client.request(
        "DELETE", "/collections/user_context/items", json={"ids": ["del-me"]}
    )
    assert r.status_code == 204
