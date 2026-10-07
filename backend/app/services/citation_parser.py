"""Sentence segmentation and inline citation marker extraction."""
import re
from typing import List, Dict, Set, Tuple


class ParsedClaim:
    def __init__(self, sentence_index: int, raw_text: str, clean_text: str, citations: List[str]):
        self.sentence_index, self.raw_text, self.clean_text, self.citations = sentence_index, raw_text, clean_text, citations

    def to_dict(self) -> Dict:
        return {"sentence_index": self.sentence_index, "raw_text": self.raw_text, "clean_text": self.clean_text, "citations": self.citations}


class CitationParser:
    CITATION_PATTERN = re.compile(r'\[(?:cite:)?\s*([a-zA-Z0-9_\-]+(?:\s*[,;]\s*(?:cite:)?\s*[a-zA-Z0-9_\-]+)*)\s*\]')
    COMMON_ABBREVS = {"e.g.", "i.e.", "u.s.", "u.k.", "dr.", "mr.", "ms.", "prof.", "vs.", "fig.", "al."}

    @classmethod
    def segment_sentences(cls, text: str) -> List[str]:
        if not text or not text.strip(): return []
        raw = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9\[])', text.strip())
        merged: List[str] = []
        for s in raw:
            s_str = s.strip()
            if not s_str: continue
            if merged and any(merged[-1].lower().endswith(abbr) for abbr in cls.COMMON_ABBREVS):
                merged[-1] = f"{merged[-1]} {s_str}"
            else: merged.append(s_str)
        return merged

    @classmethod
    def extract_citations(cls, sentence: str) -> Tuple[str, List[str]]:
        citations: List[str] = []
        def repl(match):
            for p in re.split(r'[,;]\s*', match.group(1)):
                cid = re.sub(r'^(?:cite:)?\s*', '', p.strip())
                if cid and cid not in citations: citations.append(cid)
            return ""

        clean = cls.CITATION_PATTERN.sub(repl, sentence)
        clean = re.sub(r'\s+([,.;!?])', r'\1', clean)
        return re.sub(r'\s{2,}', ' ', clean).strip(), citations

    @classmethod
    def parse_answer(cls, answer_text: str) -> List[ParsedClaim]:
        return [
            ParsedClaim(idx, s, clean or s, cites)
            for idx, s in enumerate(cls.segment_sentences(answer_text))
            for clean, cites in [cls.extract_citations(s)]
        ]

    @classmethod
    def validate_citation_linkage(cls, citations: List[str], known_passage_ids: Set[str]) -> Tuple[List[str], List[str]]:
        valid = [c for c in citations if c in known_passage_ids]
        unlinked = [c for c in citations if c not in known_passage_ids]
        return valid, unlinked
