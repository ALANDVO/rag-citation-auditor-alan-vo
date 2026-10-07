"""End-to-end API workflows for passage ingestion, auditing, review queue and exports."""


def test_full_audit_workflow(analyst_client):
    # 1. Ingest Passage
    p_resp = analyst_client.post(
        "/api/v1/audits/passages",
        json={
            "passage_id": "doc_1",
            "title": "Quantum Benchmark",
            "content": "The quantum processor achieved 99.8% two-qubit gate fidelity across 64 qubits.",
            "url": "https://example.com/quantum"
        }
    )
    assert p_resp.status_code == 200
    passage_id = p_resp.json()["passage_id"]
    assert passage_id == "doc_1"

    # 2. Ingest Answer
    a_resp = analyst_client.post(
        "/api/v1/audits/answers",
        json={
            "query": "What was the gate fidelity of the quantum processor?",
            "generated_text": "The processor reached 99.8% fidelity across 64 qubits [doc_1]. Unrelated claim made here [doc_99].",
            "model_name": "qwen-3"
        }
    )
    assert a_resp.status_code == 200
    answer_id = a_resp.json()["id"]

    # 3. Trigger Audit
    audit_resp = analyst_client.post(f"/api/v1/audits/run?answer_id={answer_id}")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["total_claims"] == 2
    assert audit_data["supported_count"] == 1
    assert audit_data["unlinked_count"] == 1
    run_id = audit_data["id"]

    # 4. Inspect Review Queue
    q_resp = analyst_client.get("/api/v1/review/queue")
    assert q_resp.status_code == 200
    items = q_resp.json()
    assert len(items) >= 1
    unlinked_item = next(it for it in items if it["claim"]["status"] == "UNLINKED_CITATION")
    claim_id = unlinked_item["claim_id"]

    # 5. Resolve Human Review
    resolve_resp = analyst_client.post(
        "/api/v1/review/action",
        json={
            "claim_id": claim_id,
            "review_status": "CORRECTED",
            "auditor_notes": "Corrected citation link from non-existent doc_99 to doc_1.",
            "corrected_citation_ids": ["doc_1"]
        }
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["review_status"] == "CORRECTED"

    # 6. Export Reports
    md_export = analyst_client.get(f"/api/v1/audits/runs/{run_id}/export?format=markdown")
    assert md_export.status_code == 200
    assert "# RAG Citation Audit Report" in md_export.text

    csv_export = analyst_client.get(f"/api/v1/audits/runs/{run_id}/export?format=csv")
    assert csv_export.status_code == 200
    assert "claim_id,sentence_index" in csv_export.text

    json_export = analyst_client.get(f"/api/v1/audits/runs/{run_id}/export?format=json")
    assert json_export.status_code == 200
    assert json_export.json()["total_claims"] == 2


def test_evaluation_benchmark_endpoint(analyst_client):
    """Evaluation benchmark returns precision, recall, and numeric metrics."""
    resp = analyst_client.get("/api/v1/evaluation/benchmark")
    assert resp.status_code == 200
    data = resp.json()
    assert "precision" in data
    assert "recall" in data
    assert "f1" in data
    assert data["total_samples"] > 0


def test_audit_logs_denied_to_analyst(analyst_client):
    """Analysts cannot read audit logs; access is forbidden."""
    denied = analyst_client.get("/api/v1/review/audit-logs")
    assert denied.status_code == 403


def test_audit_logs_allowed_to_admin(admin_client):
    """Administrators have access to immutable audit logs."""
    allowed = admin_client.get("/api/v1/review/audit-logs")
    assert allowed.status_code == 200
    assert isinstance(allowed.json(), list)
