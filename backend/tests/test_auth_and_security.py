"""Security, RBAC, CSRF, production guards and token redaction tests."""
import pytest
from app.core.config import Settings
from app.services.llm_client import LLMClient


def test_unauthenticated_request_rejected(client):
    """Endpoints requiring authentication return 401 Unauthorized."""
    resp = client.get("/api/v1/audits/projects")
    assert resp.status_code == 401


def test_viewer_denied_analyst_actions(viewer_client):
    """Viewers are rejected with 403 Forbidden on analyst endpoints."""
    resp = viewer_client.post(
        "/api/v1/audits/projects",
        json={"name": "forbidden-project", "description": "test"}
    )
    assert resp.status_code == 403
    assert "analyst" in resp.json()["detail"].lower()


def test_csrf_protection_on_mutating_requests(client, db_session):
    """Mutating cookie-authenticated requests without valid CSRF header are rejected."""
    from app.core.security import create_session
    from app.core.config import settings

    session = create_session(db_session, "user-csrf", "user@test.local", ["analyst"])
    client.cookies.set(settings.OIDC_COOKIE_NAME, session.session_id)
    # Intentionally do not provide or provide wrong x-csrf-token
    resp = client.post(
        "/api/v1/audits/projects",
        json={"name": "csrf-test", "description": "test"},
        headers={"x-csrf-token": "invalid-token"}
    )
    assert resp.status_code == 403
    assert "csrf" in resp.json()["detail"].lower()


def test_production_guard_refuses_demo_mode():
    """System refuses to start with demo mode in production environment."""
    cfg = Settings(ENVIRONMENT="production", DEMO_MODE=True)
    with pytest.raises(RuntimeError) as exc_info:
        cfg.validate_production_guards()
    assert "DEMO_MODE cannot be enabled in production" in str(exc_info.value)


def test_credential_redaction_synthetic_token():
    """LLM client redacts keys from error messages using runtime synthetic values."""
    # Never hardcode token literals; generate purely synthetic zeros
    synthetic_key = "synthetic-provider-" + ("0" * 32)
    raw_error = f"HTTP 401 Unauthorized: Authorization failed for Bearer {synthetic_key} and key={synthetic_key}"
    
    redacted = LLMClient._redact_key(raw_error)
    assert synthetic_key not in redacted
    assert "[REDACTED" in redacted
