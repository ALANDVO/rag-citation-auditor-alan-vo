"""Export service for serializing audit findings to Markdown, CSV, and JSON formats."""
import io, csv, json
from typing import Dict, Any


class ExportService:
    @classmethod
    def to_json(cls, audit_data: Dict[str, Any]) -> str:
        return json.dumps(audit_data, indent=2, default=str)

    @classmethod
    def to_markdown(cls, d: Dict[str, Any]) -> str:
        md = [
            f"# RAG Citation Audit Report #{d.get('id', 'N/A')}\n",
            "## Summary\n",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Total Claims | {d.get('total_claims', 0)} |",
            f"| Faithfulness | {d.get('faithfulness_score', 0.0)*100:.1f}% |",
            f"| Citation Precision | {d.get('citation_precision', 0.0)*100:.1f}% |",
            f"| Citation Recall | {d.get('citation_recall', 0.0)*100:.1f}% |",
            f"| Numeric Accuracy | {d.get('numeric_accuracy', 0.0)*100:.1f}% |\n",
            "## Claims\n"
        ]
        for c in d.get("claims", []):
            md.append(f"### Claim {c.get('sentence_index', 0)+1} [{c.get('status')}]")
            md.append(f"- **Sentence**: {c.get('sentence_text')}")
            md.append(f"- **Citations**: `{', '.join(c.get('cited_passage_ids', [])) or 'None'}`")
            md.append(f"- **Review Status**: {c.get('review_status', 'PENDING')}")
            if c.get("auditor_notes"): md.append(f"- **Notes**: {c.get('auditor_notes')}")
            if c.get("match_details", {}).get("reason"): md.append(f"- **Rationale**: {c['match_details']['reason']}")
            md.append("")
        return "\n".join(md)

    @classmethod
    def to_csv(cls, d: Dict[str, Any]) -> str:
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["claim_id", "sentence_index", "status", "confidence_score", "citations", "clean_claim_text", "review_status", "auditor_notes", "reviewer"])
        for c in d.get("claims", []):
            w.writerow([
                c.get("id", ""), c.get("sentence_index", ""), c.get("status", ""),
                c.get("confidence_score", ""), ";".join(c.get("cited_passage_ids", [])),
                c.get("clean_claim_text", ""), c.get("review_status", "PENDING"),
                c.get("auditor_notes", ""), c.get("reviewer_user", "")
            ])
        return out.getvalue()
