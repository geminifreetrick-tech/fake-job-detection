"""Tests for the Phase-2 db-mcp extensions: reports, articles, quizzes,
notifications, analytics, company verifications."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_create_and_update_report(client):
    body = {
        "user_id": "alice",
        "title": "Suspicious Telegram-only recruiter",
        "description": "Reached out on Telegram demanding $99 'training fee'.",
        "company": "Acme",
        "url": "https://amazn-careers.xyz",
    }
    r = await client.post("/reports", json=body)
    assert r.status_code == 201, r.text
    rep = r.json()
    assert rep["status"] == "open"

    # update
    r2 = await client.patch(
        f"/reports/{rep['id']}",
        json={"status": "confirmed", "admin_notes": "Verified — added to known scams."},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "confirmed"

    # list filtered
    r3 = await client.get("/reports?status=confirmed")
    assert r3.status_code == 200
    assert any(item["id"] == rep["id"] for item in r3.json())

    # list by user
    r4 = await client.get(f"/users/{body['user_id']}/reports")
    assert r4.status_code == 200
    assert len(r4.json()) >= 1


@pytest.mark.asyncio
async def test_article_upsert_and_get(client):
    body = {
        "slug": "spot-fakes",
        "title": "Spot fakes",
        "summary": "Quick guide",
        "body_md": "# spot fakes\nbody",
        "tags": ["basics"],
        "published": True,
    }
    r = await client.post("/articles", json=body)
    assert r.status_code == 201
    art_id = r.json()["id"]

    # idempotent upsert returns same id
    r2 = await client.post("/articles", json={**body, "title": "Spot fakes (v2)"})
    assert r2.json()["id"] == art_id
    assert r2.json()["title"] == "Spot fakes (v2)"

    r3 = await client.get("/articles/spot-fakes")
    assert r3.status_code == 200
    assert r3.json()["title"] == "Spot fakes (v2)"

    r4 = await client.get("/articles?tag=basics")
    assert any(a["slug"] == "spot-fakes" for a in r4.json())


@pytest.mark.asyncio
async def test_quiz_and_attempt(client):
    quiz_body = {
        "slug": "intro-quiz",
        "title": "Intro quiz",
        "description": "two-question intro",
        "questions": [
            {
                "id": "q1",
                "prompt": "Pay $99 to start work?",
                "choices": ["Yes", "No"],
                "correct_index": 1,
                "explanation": "Never pay to be hired.",
            },
            {
                "id": "q2",
                "prompt": "Telegram-only recruiter?",
                "choices": ["Legit", "Scam"],
                "correct_index": 1,
                "explanation": "No paper trail.",
            },
        ],
    }
    r = await client.post("/quizzes", json=quiz_body)
    assert r.status_code == 201, r.text
    quiz_id = r.json()["id"]

    r2 = await client.get("/quizzes/intro-quiz")
    assert r2.status_code == 200
    assert len(r2.json()["questions"]) == 2

    attempt = {
        "quiz_id": quiz_id,
        "user_id": "alice",
        "answers": [1, 1],
        "score": 1.0,
        "total": 2,
        "correct": 2,
    }
    r3 = await client.post("/quiz-attempts", json=attempt)
    assert r3.status_code == 201
    r4 = await client.get("/users/alice/quiz-attempts")
    assert r4.status_code == 200
    assert len(r4.json()) >= 1


@pytest.mark.asyncio
async def test_company_verification_cache(client):
    cached_until = datetime(2099, 1, 1, tzinfo=timezone.utc).isoformat()
    payload = {
        "name": "Acme Inc",
        "domain": "acme.com",
        "legitimacy_score": 0.92,
        "signals": {"whois_age_days": 4500, "results_count": 12},
        "search_results": [{"title": "Acme careers", "url": "https://acme.com/careers"}],
        "cached_until": cached_until,
    }
    r = await client.post("/company-verifications", json=payload)
    assert r.status_code == 201, r.text

    r2 = await client.get("/company-verifications?name=Acme%20Inc&domain=acme.com")
    assert r2.status_code == 200
    body = r2.json()
    assert body and body["domain"] == "acme.com"
    assert body["legitimacy_score"] == pytest.approx(0.92)


@pytest.mark.asyncio
async def test_analytics_summary_and_top_features(client):
    # seed two jobs + predictions
    for i, (label, score) in enumerate([("fraud", 0.9), ("legit", 0.1)]):
        j = await client.post(
            "/jobs",
            json={
                "user_id": "ana",
                "raw_text": f"posting {i}",
                "source_type": "text",
                "sha256": f"a{i:063d}",
            },
        )
        assert j.status_code == 201
        await client.post(
            "/predictions",
            json={
                "job_id": j.json()["id"],
                "label": label,
                "score": score,
                "explanation": {
                    "explanations": [
                        {"feature": "scam_marker_score", "direction": "fraud" if label == "fraud" else "legit"},
                        {"feature": "salary_unrealistic_flag", "direction": "fraud" if label == "fraud" else "legit"},
                    ]
                },
                "model_version": "v1",
            },
        )

    r = await client.get("/analytics/summary")
    assert r.status_code == 200
    summary = r.json()
    assert summary["total_fraud"] >= 1
    assert summary["total_legit"] >= 1
    assert 0.0 <= summary["fraud_rate"] <= 1.0

    r2 = await client.get("/analytics/top-scam-features?limit=5")
    assert r2.status_code == 200
    feats = r2.json()
    assert any(f["feature"] == "scam_marker_score" for f in feats)


@pytest.mark.asyncio
async def test_notifications(client):
    body = {
        "user_id": "alice",
        "channel": "email",
        "template": "fraud_detected",
        "payload": {"job_id": "j1", "score": 0.95},
    }
    r = await client.post("/notifications", json=body)
    assert r.status_code == 201
    r2 = await client.get("/users/alice/notifications")
    assert r2.status_code == 200
    assert any(n["template"] == "fraud_detected" for n in r2.json())


@pytest.mark.asyncio
async def test_analytics_event_recording(client):
    r = await client.post(
        "/analytics-events",
        json={"user_id": "alice", "name": "signup", "props": {"plan": "free"}},
    )
    assert r.status_code == 201
    assert r.json()["name"] == "signup"
