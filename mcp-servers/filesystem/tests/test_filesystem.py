import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_upload_and_retrieve(client):
    files = {"file": ("posting.txt", b"hello world", "text/plain")}
    r = await client.post("/uploads", files=files)
    assert r.status_code == 201, r.text
    sha = r.json()["sha256"]
    r2 = await client.get(f"/uploads/{sha}")
    assert r2.status_code == 200
    assert r2.content == b"hello world"


@pytest.mark.asyncio
async def test_reject_unsupported_mime(client):
    files = {"file": ("evil.bin", b"\x00\x01", "application/x-executable")}
    r = await client.post("/uploads", files=files)
    assert r.status_code == 415


@pytest.mark.asyncio
async def test_report_pdf_generation(client):
    body = {
        "user_email": "alice@example.com",
        "prediction": {"label": "fraud", "score": 0.97, "model_version": "v1700000000"},
        "text_excerpt": "Work from home – earn $5000/week. Telegram @hire. <script>",
        "source_type": "text",
        "explanations": [
            {
                "feature": "scam_marker_score",
                "label": "Weighted score of scam markers",
                "value": 4.1,
                "contribution": 0.62,
                "direction": "fraud",
            }
        ],
        "features": {"scam_marker_score": 4.1},
    }
    r = await client.post("/reports", json=body)
    assert r.status_code == 200, r.text
    sha = r.json()["sha256"]
    r2 = await client.get(f"/reports/{sha}?download=true")
    assert r2.status_code == 200
    assert r2.headers["content-type"].startswith("application/pdf")
    # Magic bytes of PDF
    assert r2.content[:4] == b"%PDF"
    assert "attachment" in r2.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_requires_service_token():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/uploads", files={"file": ("a.txt", b"hi", "text/plain")}
        )
    assert r.status_code == 401
