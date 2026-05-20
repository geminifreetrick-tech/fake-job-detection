from __future__ import annotations

import os

import pytest
import respx
from httpx import Response

from .conftest import make_access_token


@pytest.mark.asyncio
@respx.mock
async def test_submit_report(client):
    db_create = respx.post("http://db-mcp.test/reports").mock(
        return_value=Response(
            201,
            json={
                "id": "rep-1",
                "user_id": "user-1",
                "title": "scam",
                "description": "asked $99 fee",
                "company": None,
                "url": None,
                "job_id": None,
                "status": "open",
                "admin_notes": None,
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00",
            },
        )
    )
    respx.post("http://notification-mcp.test/email").mock(
        return_value=Response(200, json={"status": "sent", "channel": "email"})
    )
    respx.post("http://db-mcp.test/analytics-events").mock(
        return_value=Response(201, json={"id": "e", "name": "report.submitted", "props": {}, "user_id": "user-1", "created_at": "2024-01-01T00:00:00+00:00"})
    )

    token = make_access_token(email="alice@example.com")
    r = await client.post(
        "/api/v1/reports",
        json={"title": "scam", "description": "asked $99 fee"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert db_create.called


@pytest.mark.asyncio
@respx.mock
async def test_my_reports_proxies_db(client):
    respx.get("http://db-mcp.test/users/user-1/reports").mock(
        return_value=Response(200, json=[{"id": "r1", "title": "scam"}])
    )
    token = make_access_token()
    r = await client.get(
        "/api/v1/reports/mine", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert r.json()[0]["id"] == "r1"


@pytest.mark.asyncio
@respx.mock
async def test_awareness_strips_answers(client):
    respx.get("http://db-mcp.test/quizzes/intro").mock(
        return_value=Response(
            200,
            json={
                "id": "q-1",
                "slug": "intro",
                "title": "Intro",
                "description": "x",
                "questions": [
                    {
                        "id": "q1",
                        "prompt": "Pay $99 to start?",
                        "choices": ["Yes", "No"],
                        "correct_index": 1,
                        "explanation": "Never pay to be hired.",
                    }
                ],
                "created_at": "2024-01-01T00:00:00+00:00",
            },
        )
    )
    token = make_access_token()
    r = await client.get(
        "/api/v1/awareness/quizzes/intro", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    body = r.json()
    # No 'correct_index' or 'explanation' leaked to client.
    q = body["questions"][0]
    assert "correct_index" not in q
    assert "explanation" not in q
    assert q["choices"] == ["Yes", "No"]


@pytest.mark.asyncio
@respx.mock
async def test_quiz_submission_scores_correctly(client):
    respx.get("http://db-mcp.test/quizzes/intro").mock(
        return_value=Response(
            200,
            json={
                "id": "q-1",
                "slug": "intro",
                "title": "Intro",
                "description": "x",
                "questions": [
                    {"id": "q1", "prompt": "?", "choices": ["a", "b"], "correct_index": 1, "explanation": "x"},
                    {"id": "q2", "prompt": "?", "choices": ["a", "b"], "correct_index": 0, "explanation": "x"},
                ],
                "created_at": "2024-01-01T00:00:00+00:00",
            },
        )
    )
    attempt = respx.post("http://db-mcp.test/quiz-attempts").mock(
        return_value=Response(201, json={"id": "att-1", "quiz_id": "q-1", "user_id": "user-1",
                                          "answers": [1, 1], "score": 0.5, "total": 2, "correct": 1,
                                          "created_at": "2024-01-01T00:00:00+00:00"})
    )
    respx.post("http://db-mcp.test/analytics-events").mock(
        return_value=Response(201, json={"id": "e", "name": "quiz.completed", "props": {}, "user_id": "user-1", "created_at": "2024-01-01T00:00:00+00:00"})
    )

    token = make_access_token()
    r = await client.post(
        "/api/v1/awareness/quizzes/submit",
        json={"quiz_slug": "intro", "answers": [1, 1]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["correct"] == 1
    assert body["total"] == 2
    assert body["score"] == pytest.approx(0.5)
    assert body["breakdown"][0]["is_correct"] is True
    assert body["breakdown"][1]["is_correct"] is False
    assert attempt.called


@pytest.mark.asyncio
@respx.mock
async def test_verify_company_calls_websearch_on_miss(client):
    respx.get("http://db-mcp.test/company-verifications").mock(
        return_value=Response(200, json=None)
    )
    respx.post("http://websearch-mcp.test/verify-company").mock(
        return_value=Response(
            200,
            json={
                "name": "Acme",
                "domain": "acme.com",
                "legitimacy_score": 0.87,
                "signals": {"whois_age_days": 1200},
                "whois": {"creation_date": "2015-01-01T00:00:00"},
                "search_results": [],
                "provider": "google_cse",
            },
        )
    )
    respx.post("http://db-mcp.test/company-verifications").mock(
        return_value=Response(201, json={"id": "cv-1", "name": "Acme", "domain": "acme.com",
                                          "legitimacy_score": 0.87, "signals": {}, "whois": None,
                                          "search_results": [], "cached_until": "2099-01-01T00:00:00+00:00",
                                          "created_at": "2024-01-01T00:00:00+00:00"})
    )
    respx.post("http://db-mcp.test/analytics-events").mock(return_value=Response(201, json={"id": "e", "name": "company.verified", "props": {}, "user_id": "user-1", "created_at": "2024-01-01T00:00:00+00:00"}))

    token = make_access_token()
    r = await client.post(
        "/api/v1/companies/verify",
        json={"name": "Acme", "domain": "acme.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["legitimacy_score"] == pytest.approx(0.87)
    assert body["from_cache"] is False


@pytest.mark.asyncio
async def test_admin_requires_admin_role(client):
    token = make_access_token(role="user")
    r = await client.get(
        "/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 403


@pytest.mark.asyncio
@respx.mock
async def test_admin_dashboard_proxies_analytics(client):
    respx.get("http://analytics-mcp.test/dashboard").mock(
        return_value=Response(200, json={"summary": {"total_jobs": 1}, "fraud_over_time": {}, "top_features": []})
    )
    token = make_access_token(role="admin")
    r = await client.get(
        "/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert r.json()["summary"]["total_jobs"] == 1


@pytest.mark.asyncio
async def test_internal_ws_push_requires_service_token(client):
    r = await client.post(
        "/internal/ws/push",
        json={"user_id": "u", "payload": {"event": "ping"}},
    )
    assert r.status_code == 401

    r2 = await client.post(
        "/internal/ws/push",
        json={"user_id": "u", "payload": {"event": "ping"}},
        headers={"X-Service-Token": os.environ["SERVICE_TOKEN"]},
    )
    assert r2.status_code == 202
    assert r2.json() == {"sent": 0}
