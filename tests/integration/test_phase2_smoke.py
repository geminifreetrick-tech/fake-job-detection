"""End-to-end smoke test for Phase 2 features against the running stack.

Skipped automatically when the gateway is not reachable. Validates the full
user journey for reports, awareness, company verification, and PDF reports.
"""
from __future__ import annotations

import os
import time
import uuid

import httpx
import pytest

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")


def _reachable() -> bool:
    try:
        r = httpx.get(f"{BACKEND}/healthz", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _reachable(), reason=f"backend gateway not reachable at {BACKEND}"
)


def _wait_for_aggregated_health(timeout: float = 60.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BACKEND}/api/v1/healthz", timeout=2.0)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("aggregated /api/v1/healthz did not become ok in time")


def _signup() -> tuple[str, dict]:
    email = f"phase2-{uuid.uuid4().hex[:8]}@example.com"
    r = httpx.post(
        f"{BACKEND}/api/v1/auth/signup",
        json={"email": email, "password": "correct horse battery staple"},
        timeout=10.0,
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


def test_phase2_full_journey():
    _wait_for_aggregated_health()
    _, headers = _signup()

    me = httpx.get(f"{BACKEND}/api/v1/me", headers=headers, timeout=5.0).json()
    assert me["email"].endswith("@example.com")
    assert me["role"] == "user"

    fraud_text = (
        "URGENT!!! Work from home, earn $5000/week, Telegram @hire, "
        "send $49 registration fee."
    )
    analyse = httpx.post(
        f"{BACKEND}/api/v1/jobs/analyze",
        headers=headers,
        json={"text": fraud_text},
        timeout=30.0,
    ).json()
    job_id = analyse["job_id"]
    assert analyse["label"] == "fraud"

    pdf = httpx.post(
        f"{BACKEND}/api/v1/files/reports/{job_id}", headers=headers, timeout=10.0
    ).json()
    assert pdf["content_type"] == "application/pdf"
    assert len(pdf["sha256"]) == 64

    report = httpx.post(
        f"{BACKEND}/api/v1/reports",
        headers=headers,
        json={"title": "smoke report", "description": "smoke", "company": "Acme"},
        timeout=5.0,
    ).json()
    assert report["title"] == "smoke report"

    mine = httpx.get(f"{BACKEND}/api/v1/reports/mine", headers=headers, timeout=5.0).json()
    assert any(r["id"] == report["id"] for r in mine)

    articles = httpx.get(
        f"{BACKEND}/api/v1/awareness/articles", headers=headers, timeout=5.0
    ).json()
    assert len(articles) >= 3

    quizzes = httpx.get(
        f"{BACKEND}/api/v1/awareness/quizzes", headers=headers, timeout=5.0
    ).json()
    assert len(quizzes) >= 1
    quiz = quizzes[0]
    for q in quiz["questions"]:
        assert "correct_index" not in q

    sub = httpx.post(
        f"{BACKEND}/api/v1/awareness/quizzes/submit",
        headers=headers,
        json={"quiz_slug": quiz["slug"], "answers": [0] * len(quiz["questions"])},
        timeout=5.0,
    ).json()
    assert sub["total"] == len(quiz["questions"])

    vc = httpx.post(
        f"{BACKEND}/api/v1/companies/verify",
        headers=headers,
        json={"name": "Google", "domain": "google.com"},
        timeout=15.0,
    ).json()
    assert 0.0 <= vc["legitimacy_score"] <= 1.0

    # Admin route must reject normal users.
    forbidden = httpx.get(
        f"{BACKEND}/api/v1/admin/dashboard", headers=headers, timeout=5.0
    )
    assert forbidden.status_code == 403
