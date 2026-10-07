"""Substantive domain engine for deterministic RAG citation verification and attribution."""
import re
from typing import List, Dict, Any, Set, Tuple
from app.services.citation_parser import CitationParser, ParsedClaim
from app.services.numeric_verifier import NumericVerifier


class TextMetrics:
    STOPWORDS: Set[str] = {
        "a", "about", "all", "an", "and", "any", "are", "as", "at", "be", "been", "by",
        "for", "from", "had", "has", "have", "he", "in", "is", "it", "its", "not", "of",
        "on", "or", "that", "the", "their", "this", "to", "was", "were", "with", "would"
    }

    @classmethod
    def stem(cls, word: str) -> str:
        w = word.lower()
        for suff in ("ing", "tion", "tions", "ies", "es", "ed", "s"):
            if w.endswith(suff) and len(w) > len(suff) + 2:
                return w[:-len(suff)]
        return w

    @classmethod
    def tokenize(cls, text: str, filter_stopwords: bool = True) -> List[str]:
        words = re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower())
        if filter_stopwords:
            return [cls.stem(w) for w in words if w not in cls.STOPWORDS and len(w) > 1]
        return [cls.stem(w) for w in words]

    @classmethod
    def get_ngrams(cls, tokens: List[str], n: int = 2) -> Set[Tuple[str, ...]]:
        if len(tokens) < n:
            return set()
        return set(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

    @classmethod
    def compute_overlap(cls, claim_text: str, passage_text: str) -> Dict[str, float]:
        claim_tokens = cls.tokenize(claim_text, filter_stopwords=True)
        passage_tokens = cls.tokenize(passage_text, filter_stopwords=True)

        if not claim_tokens:
            return {"containment": 1.0, "jaccard": 1.0, "bigram_overlap": 1.0, "composite_score": 1.0}
        if not passage_tokens:
            return {"containment": 0.0, "jaccard": 0.0, "bigram_overlap": 0.0, "composite_score": 0.0}

        claim_set, passage_set = set(claim_tokens), set(passage_tokens)
        intersection = claim_set.intersection(passage_set)
        containment = len(intersection) / len(claim_set)
        union = claim_set.union(passage_set)
        jaccard = len(intersection) / len(union) if union else 0.0

        claim_bigrams = cls.get_ngrams(cls.tokenize(claim_text, filter_stopwords=False), 2)
        passage_bigrams = cls.get_ngrams(cls.tokenize(passage_text, filter_stopwords=False), 2)
        bigram_overlap = len(claim_bigrams.intersection(passage_bigrams)) / len(claim_bigrams) if claim_bigrams else containment
        composite = (0.55 * containment) + (0.25 * bigram_overlap) + (0.20 * jaccard)

        return {
            "containment": round(containment, 4),
            "jaccard": round(jaccard, 4),
            "bigram_overlap": round(bigram_overlap, 4),
            "composite_score": round(composite, 4)
        }


class FaithfulnessEngine:
    @classmethod
    def audit_sentence(cls, parsed_claim: ParsedClaim, passages_map: Dict[str, str]) -> Dict[str, Any]:
        known_ids = set(passages_map.keys())
        valid_cites, unlinked_cites = CitationParser.validate_citation_linkage(parsed_claim.citations, known_ids)

        if unlinked_cites:
            return {
                "status": "UNLINKED_CITATION", "confidence_score": 0.95, "token_overlap_score": 0.0,
                "match_details": {"unlinked_citations": unlinked_cites, "valid_citations": valid_cites,
                                  "reason": f"Citation IDs {unlinked_cites} do not exist in the retrieved corpus."},
                "numeric_verification": {"has_numeric_claims": False, "discrepancies": []}, "review_priority": "HIGH"
            }

        if not parsed_claim.citations:
            num_check = NumericVerifier.extract_entities(parsed_claim.clean_text)
            has_facts = len(num_check) > 0 or len(parsed_claim.clean_text.split()) > 6
            return {
                "status": "UNSUPPORTED" if has_facts else "SUPPORTED",
                "confidence_score": 0.85 if has_facts else 0.5, "token_overlap_score": 0.0,
                "match_details": {"reason": "Factual assertion without citation attribution." if has_facts else "Transitional statement."},
                "numeric_verification": {"has_numeric_claims": len(num_check) > 0, "discrepancies": [{"entity": e.to_dict(), "reason": "No citation"} for e in num_check]},
                "review_priority": "HIGH" if has_facts else "LOW"
            }

        cited_texts = [passages_map[cid] for cid in valid_cites if cid in passages_map]
        num_verification = NumericVerifier.verify_sentence_numbers(parsed_claim.clean_text, cited_texts)

        if num_verification["has_numeric_claims"] and not num_verification["all_supported"]:
            return {
                "status": "NUMERIC_MISMATCH", "confidence_score": 0.92, "token_overlap_score": 0.0,
                "match_details": {"reason": "Numeric claims contradict or lack support in cited passage.", "discrepancies": num_verification["discrepancies"]},
                "numeric_verification": num_verification, "review_priority": "HIGH"
            }

        overlap = TextMetrics.compute_overlap(parsed_claim.clean_text, " ".join(cited_texts))
        comp, cont = overlap["composite_score"], overlap["containment"]
        has_verified_num = num_verification["has_numeric_claims"] and num_verification["all_supported"]

        if comp >= 0.45 or (cont >= 0.50 and (has_verified_num or comp >= 0.35)):
            status, priority, conf = "SUPPORTED", "LOW", min(0.99, 0.70 + (comp * 0.3))
        elif comp >= 0.22 or cont >= 0.30:
            status, priority, conf = "PARTIALLY_SUPPORTED", "MEDIUM", 0.75
        else:
            status, priority, conf = "UNSUPPORTED", "HIGH", 0.88

        return {
            "status": status, "confidence_score": round(conf, 4), "token_overlap_score": round(comp, 4),
            "match_details": {"overlap_metrics": overlap, "valid_citations": valid_cites, "reason": f"Overlap composite is {comp*100:.1f}%; status {status}."},
            "numeric_verification": num_verification, "review_priority": priority
        }

    @classmethod
    def audit_full_answer(cls, answer_text: str, passages: List[Dict[str, Any]]) -> Dict[str, Any]:
        passages_map = {p["passage_id"]: p["content"] for p in passages}
        claims = CitationParser.parse_answer(answer_text)
        claims_results = []
        counts = {"SUPPORTED": 0, "PARTIALLY_SUPPORTED": 0, "UNSUPPORTED": 0, "UNLINKED_CITATION": 0, "NUMERIC_MISMATCH": 0}
        total_num, supported_num = 0, 0
        total_cites, valid_cites_cnt = 0, 0

        for claim in claims:
            audit = cls.audit_sentence(claim, passages_map)
            st = audit["status"]
            counts[st] = counts.get(st, 0) + 1
            nv = audit.get("numeric_verification", {})
            if nv.get("has_numeric_claims"):
                total_num += nv.get("total_numeric_claims", 0)
                supported_num += nv.get("supported_numeric_claims", 0)

            total_cites += len(claim.citations)
            valid_cites_cnt += len(audit["match_details"].get("valid_citations", []))

            claims_results.append({
                "sentence_index": claim.sentence_index, "sentence_text": claim.raw_text,
                "clean_claim_text": claim.clean_text, "cited_passage_ids": claim.citations,
                "status": st, "confidence_score": audit["confidence_score"],
                "token_overlap_score": audit["token_overlap_score"],
                "numeric_entities": nv.get("claim_entities", []),
                "match_details": audit["match_details"], "review_priority": audit["review_priority"]
            })

        n = len(claims)
        faith = ((counts["SUPPORTED"] * 1.0) + (counts["PARTIALLY_SUPPORTED"] * 0.5)) / n if n else 1.0
        prec = valid_cites_cnt / total_cites if total_cites else 1.0
        needing_cites = [c for c in claims if len(c.clean_text.split()) > 5]
        rec = sum(1 for c in needing_cites if c.citations) / len(needing_cites) if needing_cites else 1.0
        num_acc = supported_num / total_num if total_num else 1.0

        return {
            "total_claims": n, "supported_count": counts["SUPPORTED"],
            "partially_supported_count": counts["PARTIALLY_SUPPORTED"],
            "unsupported_count": counts["UNSUPPORTED"], "unlinked_count": counts["UNLINKED_CITATION"],
            "numeric_mismatch_count": counts["NUMERIC_MISMATCH"], "faithfulness_score": round(faith, 4),
            "citation_precision": round(prec, 4), "citation_recall": round(rec, 4),
            "numeric_accuracy": round(num_acc, 4), "claims": claims_results
        }
