import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_email_console_mode_logs(client, monkeypatch):
    """No SMTP_HOST => console mode; we just stub out the db-mcp log too."""
    async def noop(record):
        return None

    from app import routes as routes_mod

    monkeypatch.setattr(routes_mod, "log_notification", noop)

    body = {
        "user_id": "alice",
        "to": "alice@example.com",
        "template": "fraud_detected",
        "context": {
            "user": {"email": "alice@example.com"},
            "prediction": {"score": 0.97},
            "report_url": "http://example.com/r/abc",
            "explanations": [
                {"feature": "scam_marker_score", "label": "Scam markers", "contribution": 0.6}
            ],
        },
    }
    r = await client.post("/email", json=body)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_ws_push_uses_backend(client, monkeypatch):
    sent: list = []

    async def fake_push_ws(user_id, payload):
        sent.append((user_id, payload))
        return True

    async def noop(record):
        return None

    from app import routes as routes_mod

    monkeypatch.setattr(routes_mod, "push_ws", fake_push_ws)
    monkeypatch.setattr(routes_mod, "log_notification", noop)

    r = await client.post(
        "/ws",
        json={"user_id": "alice", "event": "fraud.detected", "payload": {"job_id": "j1"}},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "sent"
    assert sent and sent[0][0] == "alice"
    assert sent[0][1]["event"] == "fraud.detected"


@pytest.mark.asyncio
async def test_requires_service_token():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/email",
            json={"user_id": "x", "to": "x@y.z", "template": "fraud_detected"},
        )
    assert r.status_code == 401
