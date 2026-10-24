# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

frontend-test-expansion

## Roadmap

### core-verification-engine — Deterministic Citation & Faithfulness Verification Engine

Status: done

Acceptance:
- Sentence segmentation with abbreviation preservation
- Bracket citation extraction and linkage validation
- Numeric entity extraction (currency, percentages, years, scaled values)
- Cross-passage verification with attribution classification
- Composite metrics: faithfulness score, citation precision/recall, numeric accuracy

Implementation: `backend/app/services/faithfulness_engine.py`, `backend/app/services/citation_parser.py`, `backend/app/services/numeric_verifier.py`

Tests: `backend/tests/test_faithfulness_engine.py`, `backend/tests/test_domain_parser.py`, `backend/tests/test_numeric_verifier.py`

### ingestion-api — Passage & Answer Ingestion API with Structured Citations

Status: done

Acceptance:
- Project CRUD with analyst role requirement
- Passage ingestion with passage_id, title, content, URL, chunk_index
- Answer ingestion with query, generated_text, model_name
- Bracket citation markers parsed and validated on audit run

Implementation: `backend/app/api/audits.py`, `backend/app/services/audit_service.py`

Tests: `backend/tests/test_api_workflows.py::test_full_audit_workflow`

### human-review-queue — Human Evidence Review Queue & Dispute Resolution

Status: done

Acceptance:
- Automatic queue population from audit discrepancies (HIGH priority for numeric mismatch/unlinked)
- Side-by-side claim vs passage inspection
- Auditor verdict submission: VERIFIED_TRUE, FALSE_POSITIVE, HALLUCINATION_CONFIRMED, CORRECTED
- Required rationale notes, optional citation corrections
- Immutable audit log entries for all review actions

Implementation: `backend/app/api/review.py`, `backend/app/models/entities.py (ReviewQueueItem, AuditLog)`, `frontend/src/components/ReviewQueue.tsx`

Tests: `backend/tests/test_api_workflows.py::test_full_audit_workflow`, `frontend/src/tests/ReviewQueue.test.tsx`

### auth-rbac — Keycloak OIDC Authentication with PKCE, CSRF, and RBAC

Status: done

Acceptance:
- Authorization code flow with PKCE S256
- State + nonce validation, HttpOnly SameSite=Lax session cookie
- CSRF protection on all mutating cookie-authenticated requests
- Role hierarchy: viewer < analyst < admin with endpoint enforcement
- Demo mode with localhost binding and production startup refusal

Implementation: `backend/app/core/security.py`, `backend/app/api/auth.py`, `frontend/src/context/AuthContext.tsx`

Tests: `backend/tests/test_auth_and_security.py`, `frontend/src/tests/Navbar.test.tsx`

### llm-advisory — Provider-Agnostic LLM Advisory Adapter

Status: done

Acceptance:
- Supports OpenAI-compatible, Anthropic, Gemini, Ollama via config
- Bounded 15s timeout, credential redaction in errors
- Advisory responses clearly labeled, grounded in passages
- Graceful degradation when no API key configured

Implementation: `backend/app/services/llm_client.py`, `backend/app/api/audits.py (advisory endpoint)`

Tests: `backend/tests/test_auth_and_security.py::test_credential_redaction_synthetic_token`

### evaluation-benchmark — Reproducible AI/ML Evaluation Benchmark Suite

Status: done

Acceptance:
- 8 labeled RAG instances covering numeric, citation, and factual errors
- Metrics: precision, recall, F1, numeric error detection rate, false alarm rate
- Naive token-overlap baseline comparison
- CLI executable: PYTHONPATH=backend python -m app.services.evaluation_benchmark

Implementation: `backend/app/services/evaluation_benchmark.py`, `backend/app/api/evaluation.py`

Tests: `backend/tests/test_api_workflows.py::test_evaluation_benchmark_endpoint`

### frontend-dashboard — React TypeScript Dashboard with Three Workflows

Status: done

Acceptance:
- Audit Dashboard: history, metrics, navigation to detail
- Import Workflow: passage/answer ingestion with presets, audit trigger
- Evidence Review Queue: prioritized list, inspection panel, resolution form
- Evaluation View: benchmark metrics, dataset inspection, rerun
- Audit Logs (admin): immutable trail table

Implementation: `frontend/src/components/AuditDashboard.tsx`, `frontend/src/components/ImportWorkflow.tsx`, `frontend/src/components/ReviewQueue.tsx`, `frontend/src/components/EvaluationView.tsx`, `frontend/src/components/AuditDetail.tsx`, `frontend/src/components/AuditLogsView.tsx`

Tests: `frontend/src/tests/AuditDashboard.test.tsx`, `frontend/src/tests/ReviewQueue.test.tsx`, `frontend/src/tests/Navbar.test.tsx`

### benchmark-edge-cases — Extended Benchmark Dataset for Documented Edge Cases

Status: done

Acceptance:
- Add test cases for extreme paraphrasing (zero lexical overlap)
- Add test cases for implicit unit conversions
- Add test cases for partial numeric support (multiple numbers, some match)
- Document expected engine behavior in README limitations section

Implementation: `backend/app/services/evaluation_benchmark.py (BENCHMARK_DATASET)`, `README.md (limitations section)`

Tests: `backend/tests/test_faithfulness_engine.py (existing tests cover behavior)`, `backend/tests/test_api_workflows.py (benchmark endpoint still passes)`

### frontend-test-expansion — Expanded Frontend Component Test Coverage

Status: in_progress

Acceptance:
- Add ImportWorkflow test: preset loading, form submission flow
- Add AuditDetail test: claim rendering, export buttons, advisory request
- Add EvaluationView test: metric display, dataset rendering

Implementation: `frontend/src/tests/ImportWorkflow.test.tsx`, `frontend/src/tests/AuditDetail.test.tsx`, `frontend/src/tests/EvaluationView.test.tsx`

Tests: `frontend/src/tests/ImportWorkflow.test.tsx`, `frontend/src/tests/AuditDetail.test.tsx`, `frontend/src/tests/EvaluationView.test.tsx`

