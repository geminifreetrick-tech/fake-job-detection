from app.pipeline import FEATURE_NAMES, FeaturePipeline


def test_vectorize_returns_fixed_size():
    p = FeaturePipeline()
    v = p.vectorize("Work from home!!! Earn $5000/week. Contact us on Telegram @hire.")
    assert v.shape == (len(FEATURE_NAMES),)


def test_extract_includes_all_features():
    p = FeaturePipeline()
    feats = p.extract("Software engineer in NYC. Salary $130,000/yr.")
    assert set(feats) == set(FEATURE_NAMES)


def test_fraud_features_higher_than_legit():
    p = FeaturePipeline()
    fraud = p.extract(
        "URGENT HIRING!!! Make money fast – earn $5000/week from home. "
        "Contact via Telegram @hire. Registration fee $49."
    )
    legit = p.extract(
        "Acme Inc is hiring a software engineer in NYC. "
        "Salary $130,000 per year. 401(k) and health benefits."
    )
    # At least the scam markers and payment flag should be larger on the fraud sample.
    assert fraud["scam_marker_score"] > legit["scam_marker_score"]
    assert fraud["asks_for_payment"] >= legit["asks_for_payment"]
    assert fraud["contact_telegram"] >= legit["contact_telegram"]
