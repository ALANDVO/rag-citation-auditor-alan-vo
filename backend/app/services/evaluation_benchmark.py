"""Evaluation benchmark suite measuring hallucination and citation detection accuracy."""
import time
from typing import List, Dict, Any
from app.services.faithfulness_engine import FaithfulnessEngine

BENCHMARK_DATASET: List[Dict[str, Any]] = [
    {
        "id": "sample-01", "description": "Accurately cited and grounded financial statement",
        "passages": [{"passage_id": "doc_1", "content": "Acme Corp reported Q3 revenue of $14.2M, reflecting an 8.5% year-over-year increase."}],
        "answer": "Acme Corp generated $14.2M in Q3 revenue [doc_1]. This represents an 8.5% year-over-year increase [doc_1].",
        "expected_statuses": ["SUPPORTED", "SUPPORTED"], "has_error": False
    },
    {
        "id": "sample-02", "description": "Numeric percentage hallucination despite valid citation",
        "passages": [{"passage_id": "doc_1", "content": "Global EV sales climbed by 18.2% in 2023 across North America and Europe."}],
        "answer": "Global EV sales experienced a massive 45.0% surge during 2023 [doc_1].",
        "expected_statuses": ["NUMERIC_MISMATCH"], "has_error": True
    },
    {
        "id": "sample-03", "description": "Unlinked hallucinated citation ID",
        "passages": [{"passage_id": "doc_1", "content": "The enzyme functions optimally at pH 7.4."}],
        "answer": "The optimal pH for enzymatic activity was measured at 7.4 [doc_99].",
        "expected_statuses": ["UNLINKED_CITATION"], "has_error": True
    },
    {
        "id": "sample-04", "description": "Currency magnitude error (millions vs billions)",
        "passages": [{"passage_id": "p1", "content": "The municipal green bond raised $250M for clean water transit projects."}],
        "answer": "The transit initiative secured $2.5B through municipal green bonds [p1].",
        "expected_statuses": ["NUMERIC_MISMATCH"], "has_error": True
    },
    {
        "id": "sample-05", "description": "Completely unsupported factual claim without citation",
        "passages": [{"passage_id": "doc_1", "content": "Solar efficiency reached 24.1% in controlled laboratory settings."}],
        "answer": "Solar panels now operate at 95% efficiency worldwide without any degradation.",
        "expected_statuses": ["UNSUPPORTED"], "has_error": True
    },
    {
        "id": "sample-06", "description": "Multi-passage valid synthesis",
        "passages": [
            {"passage_id": "p1", "content": "Project Apollo was initiated in 1961 with the goal of lunar exploration."},
            {"passage_id": "p2", "content": "Apollo 11 successfully completed the first crewed landing in 1969."}
        ],
        "answer": "Project Apollo began in 1961 [p1]. Crewed lunar landings were achieved in 1969 [p2].",
        "expected_statuses": ["SUPPORTED", "SUPPORTED"], "has_error": False
    },
    {
        "id": "sample-07", "description": "Date year contradiction",
        "passages": [{"passage_id": "doc_4", "content": "The treaty was ratified in 1994 following extensive multilateral negotiations."}],
        "answer": "Multilateral delegates ratified the treaty in 2014 [doc_4].",
        "expected_statuses": ["NUMERIC_MISMATCH"], "has_error": True
    },
    {
        "id": "sample-08", "description": "Correct multi-citation bracket",
        "passages": [
            {"passage_id": "1", "content": "Model latency decreased by 30ms after quantization."},
            {"passage_id": "2", "content": "Memory consumption dropped by 1.2 GB."}
        ],
        "answer": "Quantization reduced latency by 30ms and cut memory usage by 1.2 GB [1, 2].",
        "expected_statuses": ["SUPPORTED"], "has_error": False
    }
]


class EvaluationBenchmark:
    @classmethod
    def run_benchmark(cls) -> Dict[str, Any]:
        t0 = time.perf_counter()
        tp, fp, fn, tn = 0, 0, 0, 0
        num_exp, num_det = 0, 0
        base_tp, base_fp, base_fn, base_tn = 0, 0, 0, 0
        failure_cases = []

        for sample in BENCHMARK_DATASET:
            audit = FaithfulnessEngine.audit_full_answer(sample["answer"], sample["passages"])
            detected = any(c["status"] in {"UNSUPPORTED", "UNLINKED_CITATION", "NUMERIC_MISMATCH"} for c in audit["claims"])
            gt_err = sample["has_error"]

            if gt_err and detected: tp += 1
            elif not gt_err and not detected: tn += 1
            elif not gt_err and detected:
                fp += 1
                failure_cases.append({"sample_id": sample["id"], "kind": "False Positive", "answer": sample["answer"]})
            elif gt_err and not detected:
                fn += 1
                failure_cases.append({"sample_id": sample["id"], "kind": "False Negative", "answer": sample["answer"]})

            if any(st == "NUMERIC_MISMATCH" for st in sample["expected_statuses"]):
                num_exp += 1
                if any(c["status"] == "NUMERIC_MISMATCH" for c in audit["claims"]):
                    num_det += 1

            comb_p = " ".join(p["content"] for p in sample["passages"]).lower()
            a_words = [w for w in sample["answer"].lower().split() if len(w) > 3]
            base_flag = (sum(1 for w in a_words if w in comb_p) / max(len(a_words), 1)) < 0.60
            if gt_err and base_flag: base_tp += 1
            elif not gt_err and not base_flag: base_tn += 1
            elif not gt_err and base_flag: base_fp += 1
            elif gt_err and not base_flag: base_fn += 1

        elapsed = (time.perf_counter() - t0) * 1000
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) else 0.0

        b_prec = base_tp / (base_tp + base_fp) if (base_tp + base_fp) else 0.0
        b_rec = base_tp / (base_tp + base_fn) if (base_tp + base_fn) else 0.0
        b_f1 = (2 * b_prec * b_rec) / (b_prec + b_rec) if (b_prec + b_rec) else 0.0

        return {
            "total_samples": len(BENCHMARK_DATASET),
            "precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4),
            "numeric_error_detection_rate": round(num_det / num_exp if num_exp else 1.0, 4),
            "false_alarm_rate": round(fp / (fp + tn) if (fp + tn) else 0.0, 4),
            "baseline_overlap_f1": round(b_f1, 4), "execution_time_ms": round(elapsed, 2),
            "failure_cases": failure_cases
        }


if __name__ == "__main__":
    import json
    print(json.dumps(EvaluationBenchmark.run_benchmark(), indent=2))
