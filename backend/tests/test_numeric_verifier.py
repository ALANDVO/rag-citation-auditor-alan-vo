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


def test_extract_entities_handles_adjacent_entities():
    """Test that extract_entities correctly handles adjacent numeric entities.
    
    "85 out of 100" should produce both "85 out" and "100" as separate entities
    since their spans are adjacent (not overlapping), per the overlaps function logic.
    """
    text = "The project scored 85 out of 100"
    entities = NumericVerifier.extract_entities(text)
    raw_texts = [e.raw_text for e in entities]
    # Both "85 out" and "100" should be extracted
    assert "85 out" in raw_texts, f"Expected '85 out' in {raw_texts}"
    assert "100" in raw_texts, f"Expected '100' in {raw_texts}"
    # Should have at least 2 entities
    assert len(entities) >= 2


def test_extract_entities_priority_specific_patterns():
    """Test that specific patterns (currency, percent, scaled) take precedence over general pattern."""
    text = "$10M revenue with 50% margin and 2.5 billion valuation"
    entities = NumericVerifier.extract_entities(text)
    kinds = {e.kind for e in entities}
    # Should have currency, percentage, and scaled_number
    assert "currency" in kinds, f"Expected currency kind, got {kinds}"
    assert "percentage" in kinds, f"Expected percentage kind, got {kinds}"
    assert "scaled_number" in kinds, f"Expected scaled_number kind, got {kinds}"
    
    # Verify specific values
    curr = next(e for e in entities if e.kind == "currency")
    assert curr.raw_text == "$10M", f"Expected '$10M', got '{curr.raw_text}'"
    
    pct = next(e for e in entities if e.kind == "percentage")
    assert pct.raw_text == "50%", f"Expected '50%', got '{pct.raw_text}'"
    
    scaled = next(e for e in entities if e.kind == "scaled_number")
    assert scaled.raw_text == "2.5 billion", f"Expected '2.5 billion', got '{scaled.raw_text}'"


def test_currency_claim_not_supported_by_unitless_count():
    """A currency claim must not be treated as supported by a bare number.

    Regression: the unit-compatibility gate previously treated a passage entity
    with ``unit=None`` as a wildcard, so ``$5`` matched a bare count ``5``.
    """
    claim = "Revenue was $5 [p1]."
    passage = "The count was 5 items."
    res = NumericVerifier.verify_sentence_numbers(claim, [passage])
    assert res["all_supported"] is False
    assert len(res["discrepancies"]) == 1


def test_currency_claim_supported_by_matching_currency():
    claim = "Revenue was $5 [p1]."
    passage = "Revenue was $5 total."
    res = NumericVerifier.verify_sentence_numbers(claim, [passage])
    assert res["all_supported"] is True


def test_unitless_claim_matches_unit_bearing_passage():
    claim = "There were 5 [p1]."
    passage = "There were 5 items."
    res = NumericVerifier.verify_sentence_numbers(claim, [passage])
    assert res["all_supported"] is True
