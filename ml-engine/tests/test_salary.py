from app.pipeline import salary


def test_extracts_basic_salary():
    mentions = salary.extract_mentions("Salary: $80,000 per year for a software engineer")
    assert mentions
    assert mentions[0].amount_annual == 80_000


def test_handles_k_suffix():
    mentions = salary.extract_mentions("$120k annually")
    assert mentions[0].amount_annual == 120_000


def test_weekly_converted_to_annual():
    mentions = salary.extract_mentions("Earn $3,000 per week!")
    assert mentions[0].amount_annual == 3_000 * 52


def test_unrealistic_data_entry():
    feats = salary.features("Data entry from home – earn $5,000 per week!")
    assert feats["salary_unrealistic_flag"] == 1.0
    assert feats["salary_z_score"] > 3.0


def test_realistic_software_engineer():
    feats = salary.features("Software engineer in NYC. Salary $130,000 / year.")
    assert feats["salary_unrealistic_flag"] == 0.0


def test_no_salary_returns_zero():
    feats = salary.features("We are hiring an analyst to join our team.")
    assert feats == {"salary_z_score": 0.0, "salary_unrealistic_flag": 0.0}


def test_high_unanchored_salary_flagged():
    feats = salary.features("Earn $500,000/year working from home.")
    # No specific role keyword; only "remote" matches loosely → either pathway should flag.
    assert feats["salary_unrealistic_flag"] == 1.0
