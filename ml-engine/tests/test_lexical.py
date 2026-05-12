from app.pipeline import lexical


def test_marker_detected():
    feats = lexical.features("Work from home – make money fast! No experience needed.")
    assert feats["scam_marker_count"] >= 3
    assert feats["scam_marker_score"] > 0


def test_clean_text_no_markers():
    feats = lexical.features("We are seeking a software engineer with 5 years of experience.")
    assert feats["scam_marker_count"] == 0
    assert feats["scam_marker_score"] == 0


def test_payment_flag():
    feats = lexical.features("Pay a small registration fee of $49 to begin.")
    assert feats["asks_for_payment"] == 1.0
