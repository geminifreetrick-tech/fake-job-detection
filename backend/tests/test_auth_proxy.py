import pytest
import respx
from httpx import Response


@pytest.mark.asyncio
@respx.mock
async def test_signup_proxies(client):
    respx.post("http://auth-mcp.test/signup").mock(
        return_value=Response(
            201,
            json={
                "access_token": "a",
                "refresh_token": "r",
                "token_type": "bearer",
            },
        )
    )
    r = await client.post(
        "/api/v1/auth/signup", json={"email": "a@b.com", "password": "s3cret123"}
    )
    assert r.status_code == 201
    assert r.json()["access_token"] == "a"


@pytest.mark.asyncio
@respx.mock
async def test_login_forwards_failure(client):
    respx.post("http://auth-mcp.test/login").mock(
        return_value=Response(401, json={"detail": "bad creds"})
    )
    r = await client.post(
        "/api/v1/auth/login", json={"email": "a@b.com", "password": "wrong"}
    )
    assert r.status_code == 401
    assert "bad creds" in r.json()["detail"]
