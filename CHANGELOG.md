# Changelog

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
