"""Tests for numeric entity extraction and cross-passage verification."""
from app.services.numeric_verifier import NumericVerifier


def test_extract_numeric_entities():
    text = "In 2023, the startup raised $12.5M, reflecting 42% growth and 500 new hires."
    entities = NumericVerifier.extract_entities(text)
    kinds = {e.kind for e in entities}
    assert "currency" in kinds
    assert "percentage" in kinds
    assert "year" in kinds

    curr = next(e for e in entities if e.kind == "currency")
    assert curr.value == 12.5e6

    pct = next(e for e in entities if e.kind == "percentage")
    assert pct.value == 42.0


def test_verify_numeric_exact_match():
    claim = "The system achieved 94.5% precision."
    passage = "Model evaluations demonstrated 94.5% precision across benchmarks."
    res = NumericVerifier.verify_sentence_numbers(claim, [passage])
    assert res["has_numeric_claims"] is True
    assert res["all_supported"] is True
    assert len(res["discrepancies"]) == 0


def test_verify_numeric_discrepancy():
    claim = "Revenue totaled $5.2B in 2021."
    passage = "Annual financial reports confirmed revenue of $520M in 2021."
    res = NumericVerifier.verify_sentence_numbers(claim, [passage])
    assert res["has_numeric_claims"] is True
    assert res["all_supported"] is False
    assert len(res["discrepancies"]) > 0


def test_calendar_year_strict_matching():
    claim = "The treaty concluded in 2015."
    passage = "Historical records verify the treaty was signed in 1995."
    res = NumericVerifier.verify_sentence_numbers(claim, [passage])
    assert res["all_supported"] is False
    assert any("2015" in d["entity"]["raw_text"] for d in res["discrepancies"])
