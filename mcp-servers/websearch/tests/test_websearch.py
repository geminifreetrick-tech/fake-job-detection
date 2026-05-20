import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_search_fallback_when_no_key(client):
    r = await client.post("/search", json={"query": "Acme Inc careers"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "fallback"
    assert body["results"] == []


@pytest.mark.asyncio
async def test_verify_company_uses_fallback_signals(client, monkeypatch):
    """No CSE key + whois likely fails in CI → fallback path returns a 0.4 baseline."""

    async def fake_whois(domain):
        return None

    from app import routes as routes_mod

    monkeypatch.setattr(routes_mod, "whois_lookup", fake_whois)

    r = await client.post("/verify-company", json={"name": "Acme Inc", "domain": "acme.com"})
    assert r.status_code == 200
    body = r.json()
    assert "legitimacy_score" in body
    assert body["provider"] == "fallback"
    assert body["search_results"] == []
    assert body["legitimacy_score"] >= 0.0


@pytest.mark.asyncio
async def test_verify_company_with_mocked_cse_and_whois(client, monkeypatch):
    from app import routes as routes_mod

    async def fake_search(query, num):
        return [
            {
                "title": "Acme Careers",
                "snippet": "Open roles at Acme",
                "url": "https://acme.com/careers",
                "display_link": "acme.com",
            },
            {
                "title": "Acme Inc – LinkedIn",
                "snippet": "Company page",
                "url": "https://www.linkedin.com/company/acme",
                "display_link": "linkedin.com",
            },
        ], "google_cse"

    async def fake_whois(domain):
        return {
            "domain_name": domain,
            "registrar": "RegRegRegistrar",
            "creation_date": "2005-04-12T00:00:00",
            "expiration_date": "2030-01-01T00:00:00",
            "name_servers": ["ns1.acme.com"],
            "country": "US",
            "org": "Acme Inc",
        }

    monkeypatch.setattr(routes_mod, "_do_search", fake_search)
    monkeypatch.setattr(routes_mod, "whois_lookup", fake_whois)

    r = await client.post("/verify-company", json={"name": "Acme Inc", "domain": "acme.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "google_cse"
    assert body["legitimacy_score"] > 0.7
    assert body["signals"]["whois_age_days"] > 1000
    assert body["signals"]["results_same_domain"] == 1
