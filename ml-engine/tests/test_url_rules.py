from app.pipeline import url_rules


def test_clean_corporate_link():
    feats = url_rules.features("Apply at https://careers.acme-corp.com/job/123")
    assert feats["num_urls"] == 1.0
    assert feats["url_suspicious_tld"] == 0.0
    assert feats["url_brand_lookalike"] == 0.0


def test_suspicious_tld():
    feats = url_rules.features("Apply at http://jobs.tk/start")
    assert feats["url_suspicious_tld"] == 1.0


def test_brand_lookalike():
    feats = url_rules.features("Apply at http://amazn-careers.xyz")
    assert feats["url_brand_lookalike"] == 1.0


def test_telegram_and_whatsapp():
    feats = url_rules.features("Reach us on Telegram @hire or WhatsApp +1 555 0100")
    assert feats["contact_telegram"] == 1.0
    assert feats["contact_whatsapp"] == 1.0


def test_free_email():
    feats = url_rules.features("Send your CV to hr.recruit@gmail.com")
    assert feats["contact_free_email"] == 1.0


def test_no_signals():
    feats = url_rules.features("Excellent benefits and competitive salary.")
    assert feats["num_urls"] == 0.0
    assert feats["contact_telegram"] == 0.0
    assert feats["contact_whatsapp"] == 0.0
    assert feats["contact_free_email"] == 0.0
