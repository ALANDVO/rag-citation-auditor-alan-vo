"""Tests for deterministic faithfulness and citation attribution engine."""
from app.services.citation_parser import CitationParser
from app.services.faithfulness_engine import FaithfulnessEngine


def test_audit_supported_sentence():
    claim = CitationParser.parse_answer("The algorithm reached 98% convergence [1].")[0]
    passages = {"1": "Our algorithm reached 98% convergence under standard conditions."}
    res = FaithfulnessEngine.audit_sentence(claim, passages)
    assert res["status"] == "SUPPORTED"
    assert res["review_priority"] == "LOW"


def test_audit_unlinked_citation():
    claim = CitationParser.parse_answer("Groundbreaking throughput was registered [doc_404].")[0]
    passages = {"doc_1": "Standard throughput recorded."}
    res = FaithfulnessEngine.audit_sentence(claim, passages)
    assert res["status"] == "UNLINKED_CITATION"
    assert res["review_priority"] == "HIGH"


def test_audit_numeric_mismatch():
    claim = CitationParser.parse_answer("Battery capacity increased by 80% [doc_1].")[0]
    passages = {"doc_1": "Battery capacity increased by 20% compared to previous cells."}
    res = FaithfulnessEngine.audit_sentence(claim, passages)
    assert res["status"] == "NUMERIC_MISMATCH"
    assert res["review_priority"] == "HIGH"


def test_audit_full_answer_metrics():
    answer = (
        "Project Orion commenced in 1958 [p1]. "
        "It consumed 450 megatons of fuel [p1]. "
        "The project finished in 1965 [p99]."
    )
    passages = [
        {"passage_id": "p1", "content": "Project Orion commenced in 1958 and consumed 45 megatons of fuel."}
    ]
    res = FaithfulnessEngine.audit_full_answer(answer, passages)
    assert res["total_claims"] == 3
    assert res["supported_count"] == 1
    assert res["numeric_mismatch_count"] == 1
    assert res["unlinked_count"] == 1
    assert res["faithfulness_score"] < 1.0
