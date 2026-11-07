# Changelog

## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.3.1] - 2026-11-02

### Fixed
- Fixed frontend component test suite - all 32 tests now pass.
- Fixed EvaluationView component: added defensive null check for execution_time_ms.toFixed() call.
- Fixed AuditDetail tests: updated assertions to handle multiple identical metric values (Faithfulness and Precision both 67.0%) and multiple advisory buttons per claim.
- Fixed ImportWorkflow tests: added test auth provider wrapper to properly mock user roles for role-gated features.
- Fixed ReviewQueue test: updated to match actual component text content.

### Changed
- AuthContext now exports AuthContext for test mocking.
- Frontend test utilities improved with proper role-based auth mocking.



## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.1.1] - 2026-10-15

### Added
- Extended evaluation benchmark suite with 4 new edge-case samples (extreme paraphrasing, implicit unit conversion, partial numeric support, multi-citation with unlinked reference).
- Updated benchmark results: 12 samples, 100% precision/recall/F1 maintained, 0% false alarm rate.
- Documentation updates: README limitations section now reflects actual engine behavior for edge cases with concrete benchmark references.

### Fixed
- Version consistency: backend config.py VERSION now matches portfolio.json (1.1.0) and frontend package.json.
- Frontend footer version updated to 1.1.0.

## [1.1.0] - 2026-10-07

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-10-07

### Added
- Core deterministic RAG citation verification and attribution engine.
- Passage ingestion, chunk tracking, and bracketed citation tag parser.
- Entity extraction for numeric values, monetary quantities, percentages, and dates with cross-passage verification.
- Lexical overlap, n-gram containment, and attribution classification (SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, UNLINKED_CITATION, CONTRADICTION).
- Human evidence review queue with priority scoring, discrepancy inspection, and resolution audit log.
- Calibration and evaluation reporting module with benchmark metrics (precision, recall, numeric error detection rate).
- Provider-agnostic LLM advisory adapter (OpenAI-compatible, Anthropic, Gemini, Ollama) with strict grounded context.
- Secure Keycloak OIDC authentication with PKCE, state/nonce validation, SameSite HttpOnly cookies, CSRF protection, and role-based access control (viewer, analyst, admin).
- Local demo mode with strict production refusal guards.
- React + TypeScript dashboard with citation inspector, review workflow, and audit metrics.

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
