"""End-to-end smoke test against a running docker-compose stack.

Set BACKEND_URL to point at the running gateway (default: http://localhost:8000)
and run:

    docker compose up -d --build
    pytest -q tests/integration

The test is skipped automatically when the gateway is not reachable, so it
won't break local unit-test runs.
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


def test_e2e_signup_analyze_context():
    _wait_for_aggregated_health()
    email = f"e2e-{uuid.uuid4().hex[:8]}@example.com"
    password = "correct horse battery staple"

    r = httpx.post(
        f"{BACKEND}/api/v1/auth/signup",
        json={"email": email, "password": password},
        timeout=10.0,
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    fraud_text = (
        "URGENT!!! Work from home and make money fast. Earn $5000 per week. "
        "Send your CV to recruit@gmail.com or message us on Telegram @hire. "
        "Pay a small $49 registration fee."
    )
    r2 = httpx.post(
        f"{BACKEND}/api/v1/jobs/analyze",
        headers=headers,
        json={"text": fraud_text},
        timeout=30.0,
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["label"] == "fraud"
    assert body["score"] > 0.5
    assert len(body["explanations"]) == 5

    r3 = httpx.get(f"{BACKEND}/api/v1/me/context?limit=3", headers=headers, timeout=10.0)
    assert r3.status_code == 200
    ctx = r3.json()
    assert any("Telegram" in m["document"] or "work from home" in m["document"].lower() for m in ctx["recent"])
