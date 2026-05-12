from app.pipeline import grammar


def test_caps_ratio_detected():
    feats = grammar.features("HIRE NOW URGENT IMMEDIATE START!!!!")
    assert feats["caps_ratio"] > 0.5
    assert feats["repeat_punct_ratio"] > 0


def test_clean_posting_low_ratios():
    feats = grammar.features("We are hiring a software engineer to join our growing team.")
    assert feats["caps_ratio"] < 0.05
    assert feats["repeat_punct_ratio"] == 0.0


def test_empty_text():
    feats = grammar.features("")
    assert feats["num_tokens"] == 0.0
