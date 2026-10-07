"""Tests for sentence segmentation and citation marker extraction."""
from app.services.citation_parser import CitationParser


def test_segment_sentences_preserves_abbreviations():
    text = "U.S. researchers examined the enzyme e.g. at 25C. Results showed 99% efficacy [1]."
    sentences = CitationParser.segment_sentences(text)
    assert len(sentences) == 2
    assert "e.g." in sentences[0]
    assert "99% efficacy" in sentences[1]


def test_extract_citations_multiple_formats():
    s1 = "The revenue grew 14% [doc_1, doc_2]."
    clean, cites = CitationParser.extract_citations(s1)
    assert clean == "The revenue grew 14%."
    assert cites == ["doc_1", "doc_2"]

    s2 = "A subsequent phase completed [cite:4]."
    clean2, cites2 = CitationParser.extract_citations(s2)
    assert clean2 == "A subsequent phase completed."
    assert cites2 == ["4"]


def test_validate_citation_linkage():
    known = {"doc_1", "doc_2", "doc_3"}
    cites = ["doc_1", "doc_99", "doc_3"]
    valid, unlinked = CitationParser.validate_citation_linkage(cites, known)
    assert valid == ["doc_1", "doc_3"]
    assert unlinked == ["doc_99"]


def test_parse_answer_produces_structured_claims():
    answer = "First statement with evidence [p1]. Second statement extrapolating [p2, p3]."
    claims = CitationParser.parse_answer(answer)
    assert len(claims) == 2
    assert claims[0].sentence_index == 0
    assert claims[0].citations == ["p1"]
    assert claims[1].citations == ["p2", "p3"]
