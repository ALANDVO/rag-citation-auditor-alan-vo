"""Deterministic numeric and quantitative entity extractor and cross-passage verifier."""
import re
from typing import List, Dict, Any, Optional, Tuple


class NumericEntity:
    def __init__(self, raw_text: str, value: float, unit: Optional[str] = None, kind: str = "number", start_char: int = -1, end_char: int = -1):
        self.raw_text, self.value, self.unit, self.kind = raw_text, value, unit.lower() if unit else None, kind
        self.start_char, self.end_char = start_char, end_char

    def to_dict(self) -> Dict[str, Any]:
        return {"raw_text": self.raw_text, "value": self.value, "unit": self.unit, "kind": self.kind, "start_char": self.start_char, "end_char": self.end_char}


class NumericVerifier:
    SCALES = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "b": 1e9, "billion": 1e9, "t": 1e12, "trillion": 1e12}
    UNITS = {"%", "percent", "$", "usd", "dollar", "dollars", "€", "eur", "£", "gbp", "ms", "s", "min", "h", "day", "days", "month", "months", "year", "years", "kb", "mb", "gb", "tb", "m", "km", "kg", "g"}

    CURRENCY_PATTERN = re.compile(r'([$€£])\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s*(k|m|b|t|thousand|million|billion|trillion)?\b', re.IGNORECASE)
    PERCENT_PATTERN = re.compile(r'\b([0-9]+(?:\.[0-9]+)?)\s*(%|(?:percent(?:age)?\b))', re.IGNORECASE)
    SCALED_PATTERN = re.compile(r'\b([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s*(k|m|b|t|thousand|million|billion|trillion)\b', re.IGNORECASE)
    YEAR_PATTERN = re.compile(r'\b(in|by|since|during|year)\s+((?:19|20)[0-9]{2})\b', re.IGNORECASE)
    GENERAL_PATTERN = re.compile(r'\b([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z%]+)?\b')

    @classmethod
    def _parse_float(cls, s: str) -> Optional[float]:
        try: return float(s.replace(",", ""))
        except ValueError: return None

    @classmethod
    def extract_entities(cls, text: str) -> List[NumericEntity]:
        entities: List[NumericEntity] = []
        spans: List[Tuple[int, int]] = []

        def overlaps(st: int, en: int) -> bool:
            return any(s < en and en > s and not (en <= s or st >= e) for s, e in spans)

        for m in cls.CURRENCY_PATTERN.finditer(text):
            st, en = m.span()
            if overlaps(st, en): continue
            v = cls._parse_float(m.group(2))
            if v is not None:
                mult = cls.SCALES.get((m.group(3) or "").lower(), 1.0)
                u = "usd" if m.group(1) == "$" else ("eur" if m.group(1) == "€" else "gbp")
                entities.append(NumericEntity(m.group(0), v * mult, unit=u, kind="currency", start_char=st, end_char=en))
                spans.append((st, en))

        for m in cls.PERCENT_PATTERN.finditer(text):
            st, en = m.span()
            if overlaps(st, en): continue
            v = cls._parse_float(m.group(1))
            if v is not None:
                entities.append(NumericEntity(m.group(0), v, unit="percent", kind="percentage", start_char=st, end_char=en))
                spans.append((st, en))

        for m in cls.SCALED_PATTERN.finditer(text):
            st, en = m.span()
            if overlaps(st, en): continue
            v = cls._parse_float(m.group(1))
            if v is not None:
                entities.append(NumericEntity(m.group(0), v * cls.SCALES.get(m.group(2).lower(), 1.0), unit=None, kind="scaled_number", start_char=st, end_char=en))
                spans.append((st, en))

        for m in cls.YEAR_PATTERN.finditer(text):
            st, en = m.span(2)
            if overlaps(st, en): continue
            v = cls._parse_float(m.group(2))
            if v is not None:
                entities.append(NumericEntity(m.group(2), v, unit="year", kind="year", start_char=st, end_char=en))
                spans.append((st, en))

        for m in cls.GENERAL_PATTERN.finditer(text):
            st, en = m.span()
            if overlaps(st, en): continue
            v = cls._parse_float(m.group(1))
            if v is not None:
                ru = m.group(2)
                u = ru.lower() if (ru and ru.lower() in cls.UNITS) else None
                entities.append(NumericEntity(m.group(0).strip(), v, unit=u, kind="number", start_char=st, end_char=en))
                spans.append((st, en))

        return entities

    @classmethod
    def match_entity(cls, claim_ent: NumericEntity, passage_ents: List[NumericEntity], tol: float = 0.05) -> Tuple[bool, Optional[NumericEntity], str]:
        if not passage_ents:
            return False, None, "No numeric entities found in cited passage(s)."

        for pe in passage_ents:
            if abs(claim_ent.value - pe.value) < 1e-6:
                if claim_ent.unit == pe.unit or (claim_ent.unit is None or pe.unit is None):
                    return True, pe, f"Exact match found: {pe.raw_text}"

        if claim_ent.kind not in {"year"} and not (claim_ent.value.is_integer() and claim_ent.value > 100):
            for pe in passage_ents:
                if pe.kind == claim_ent.kind:
                    diff = abs(claim_ent.value - pe.value)
                    if diff / max(abs(claim_ent.value), 1e-9) <= tol:
                        if claim_ent.unit == pe.unit or (claim_ent.unit is None or pe.unit is None):
                            return True, pe, f"Approximate match within {tol*100:.1f}% tolerance: {pe.raw_text}"

        closest = min(passage_ents, key=lambda p: abs(claim_ent.value - p.value))
        return False, closest, f"Discrepancy: claim has {claim_ent.raw_text} but passage has {closest.raw_text}."

    @classmethod
    def verify_sentence_numbers(cls, claim_text: str, passage_texts: List[str]) -> Dict[str, Any]:
        claim_ents = cls.extract_entities(claim_text)
        if not claim_ents:
            return {"has_numeric_claims": False, "all_supported": True, "claim_entities": [], "discrepancies": [], "accuracy_ratio": 1.0}

        all_p_ents: List[NumericEntity] = []
        for pt in passage_texts:
            all_p_ents.extend(cls.extract_entities(pt))

        sup_cnt, discrepancies = 0, []
        for ent in claim_ents:
            matched, m_ref, reason = cls.match_entity(ent, all_p_ents)
            if matched: sup_cnt += 1
            else: discrepancies.append({"entity": ent.to_dict(), "reason": reason, "matched_reference": m_ref.to_dict() if m_ref else None})

        return {
            "has_numeric_claims": True, "all_supported": sup_cnt == len(claim_ents),
            "claim_entities": [e.to_dict() for e in claim_ents], "discrepancies": discrepancies,
            "accuracy_ratio": sup_cnt / len(claim_ents), "total_numeric_claims": len(claim_ents),
            "supported_numeric_claims": sup_cnt
        }
