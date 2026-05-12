import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["service"] == "auth-mcp"


@pytest.mark.asyncio
async def test_signup_login_me(client):
    creds = {"email": "alice@example.com", "password": "s3cretpw1!"}
    r = await client.post("/signup", json=creds)
    assert r.status_code == 201, r.text
    tokens = r.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    r2 = await client.post("/login", json=creds)
    assert r2.status_code == 200
    access = r2.json()["access_token"]

    r3 = await client.get("/me", headers={"Authorization": f"Bearer {access}"})
    assert r3.status_code == 200
    body = r3.json()
    assert body["email"] == creds["email"]
    assert body["role"] == "user"


@pytest.mark.asyncio
async def test_duplicate_signup_rejected(client):
    creds = {"email": "dup@example.com", "password": "s3cretpw1!"}
    assert (await client.post("/signup", json=creds)).status_code == 201
    r = await client.post("/signup", json=creds)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_bad_password_rejected(client):
    creds = {"email": "bob@example.com", "password": "s3cretpw1!"}
    assert (await client.post("/signup", json=creds)).status_code == 201
    r = await client.post("/login", json={"email": creds["email"], "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_flow(client):
    creds = {"email": "carol@example.com", "password": "s3cretpw1!"}
    r = await client.post("/signup", json=creds)
    refresh = r.json()["refresh_token"]
    r2 = await client.post("/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


@pytest.mark.asyncio
async def test_verify_returns_user(client):
    creds = {"email": "dave@example.com", "password": "s3cretpw1!"}
    r = await client.post("/signup", json=creds)
    access = r.json()["access_token"]
    r2 = await client.post("/verify", headers={"Authorization": f"Bearer {access}"})
    assert r2.status_code == 200
    assert r2.json()["email"] == creds["email"]
