from __future__ import annotations

import pytest
import respx
from httpx import Response

from .conftest import make_access_token


@pytest.mark.asyncio
@respx.mock
async def test_analyze_text_happy_path(client):
    ml_route = respx.post("http://ml-engine.test/predict").mock(
        return_value=Response(
            200,
            json={
                "label": "fraud",
                "score": 0.91,
                "explanations": [
                    {
                        "feature": "scam_marker_score",
                        "label": "Weighted score of scam-marker phrases",
                        "value": 5.4,
                        "contribution": 0.6,
                        "direction": "fraud",
                    }
                ],
                "features": {"scam_marker_score": 5.4},
                "model_version": "v1700000000",
                "source_type": "text",
                "text_excerpt": "Work from home make money fast",
            },
        )
    )
    db_jobs = respx.post("http://db-mcp.test/jobs").mock(
        return_value=Response(
            201,
            json={
                "id": "job-1",
                "user_id": "user-1",
                "raw_text": "Work from home",
                "source_type": "text",
                "source_uri": None,
                "sha256": "a" * 64,
                "created_at": "2024-01-01T00:00:00+00:00",
            },
        )
    )
    db_preds = respx.post("http://db-mcp.test/predictions").mock(
        return_value=Response(
            201,
            json={
                "id": "pred-1",
                "job_id": "job-1",
                "label": "fraud",
                "score": 0.91,
                "explanation": {},
                "model_version": "v1700000000",
                "created_at": "2024-01-01T00:00:00+00:00",
            },
        )
    )
    mem = respx.post(
        "http://memory-mcp.test/collections/user_context/upsert"
    ).mock(return_value=Response(204))

    token = make_access_token()
    r = await client.post(
        "/api/v1/jobs/analyze",
        json={"text": "Work from home – make money fast! Telegram @hire"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["label"] == "fraud"
    assert body["job_id"] == "job-1"
    assert body["prediction_id"] == "pred-1"
    assert ml_route.called
    assert db_jobs.called
    assert db_preds.called
    assert mem.called


@pytest.mark.asyncio
async def test_analyze_requires_auth(client):
    r = await client.post("/api/v1/jobs/analyze", json={"text": "hi"})
    assert r.status_code == 401


@pytest.mark.asyncio
@respx.mock
async def test_memory_failure_does_not_break_analysis(client):
    respx.post("http://ml-engine.test/predict").mock(
        return_value=Response(
            200,
            json={
                "label": "legit",
                "score": 0.1,
                "explanations": [],
                "features": {},
                "model_version": "v1",
                "source_type": "text",
                "text_excerpt": "ok",
            },
        )
    )
    respx.post("http://db-mcp.test/jobs").mock(
        return_value=Response(
            201,
            json={
                "id": "j",
                "user_id": "user-1",
                "raw_text": "x",
                "source_type": "text",
                "source_uri": None,
                "sha256": "a" * 64,
                "created_at": "2024-01-01T00:00:00+00:00",
            },
        )
    )
    respx.post("http://db-mcp.test/predictions").mock(
        return_value=Response(
            201,
            json={
                "id": "p",
                "job_id": "j",
                "label": "legit",
                "score": 0.1,
                "explanation": {},
                "model_version": "v1",
                "created_at": "2024-01-01T00:00:00+00:00",
            },
        )
    )
    respx.post("http://memory-mcp.test/collections/user_context/upsert").mock(
        return_value=Response(500)
    )

    token = make_access_token()
    r = await client.post(
        "/api/v1/jobs/analyze",
        json={"text": "An ordinary clean posting."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["label"] == "legit"


@pytest.mark.asyncio
@respx.mock
async def test_me_jobs_proxies_db(client):
    respx.get("http://db-mcp.test/users/user-1/jobs").mock(
        return_value=Response(200, json=[{"job": {"id": "j"}, "prediction": None}])
    )
    token = make_access_token()
    r = await client.get(
        "/api/v1/me/jobs", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert r.json() == [{"job": {"id": "j"}, "prediction": None}]


@pytest.mark.asyncio
@respx.mock
async def test_me_context(client):
    respx.get("http://memory-mcp.test/context/user-1").mock(
        return_value=Response(
            200,
            json={
                "recent": [{"id": "r1", "document": "d1", "metadata": {}, "distance": None}],
                "similar_scams": [],
            },
        )
    )
    token = make_access_token()
    r = await client.get(
        "/api/v1/me/context?limit=3", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert r.json()["recent"][0]["id"] == "r1"
