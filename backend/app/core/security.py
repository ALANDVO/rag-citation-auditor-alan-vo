"""Authentication, Keycloak OIDC authorization-code flow, PKCE, CSRF and RBAC enforcement."""
import os
import secrets
import hashlib
import base64
import datetime
from typing import Dict, Any, List, Optional, Tuple
from fastapi import Request, HTTPException, status, Depends, Header
from sqlalchemy.orm import Session
import jwt
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import SessionRecord, AuditLog, utc_now


ROLE_HIERARCHY = {
    "viewer": 1,
    "analyst": 2,
    "admin": 3
}


def generate_pkce_pair() -> Tuple[str, str]:
    """Generates PKCE code_verifier and code_challenge using SHA256."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def create_session(
    db: Session,
    user_id: str,
    email: str,
    roles: List[str]
) -> SessionRecord:
    """Creates a server-side session record with associated CSRF token."""
    session_id = secrets.token_hex(32)
    csrf_token = secrets.token_hex(32)
    expires_at = utc_now() + datetime.timedelta(seconds=settings.SESSION_MAX_AGE_SECONDS)

    import json
    session = SessionRecord(
        session_id=session_id,
        user_id=user_id,
        email=email,
        roles=json.dumps(roles),
        csrf_token=csrf_token,
        created_at=utc_now(),
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """Retrieves authenticated session without raising exception if absent."""
    session_id = request.cookies.get(settings.OIDC_COOKIE_NAME)
    if not session_id:
        return None

    session = db.query(SessionRecord).filter(SessionRecord.session_id == session_id).first()
    if not session:
        return None

    # Check expiration (ensure timezone aware comparison)
    now = utc_now()
    exp = session.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=datetime.timezone.utc)
    if exp < now:
        db.delete(session)
        db.commit()
        return None

    import json
    try:
        roles = json.loads(session.roles)
    except Exception:
        roles = []

    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "email": session.email,
        "roles": roles,
        "csrf_token": session.csrf_token,
        "is_authenticated": True
    }


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Strict authentication dependency rejecting unauthenticated requests."""
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in via Keycloak OIDC or demo session.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # CSRF protection on mutating methods authenticated via cookie session
    if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
        csrf_header = request.headers.get("x-csrf-token")
        if not csrf_header or not secrets.compare_digest(csrf_header, user["csrf_token"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed: missing or invalid X-CSRF-Token header."
            )

    return user


def require_role(required_role: str):
    """Enforces minimum role privilege (viewer < analyst < admin)."""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_roles = user.get("roles", [])
        req_level = ROLE_HIERARCHY.get(required_role, 99)

        # Check if user has sufficient role level
        has_permission = any(ROLE_HIERARCHY.get(r, 0) >= req_level for r in user_roles)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: '{required_role}' privilege required."
            )
        return user
    return role_checker


def record_audit_log(
    db: Session,
    user: Dict[str, Any],
    action: str,
    entity_type: str,
    entity_id: str,
    details: Dict[str, Any]
) -> None:
    """Appends an immutable audit log record for security and regulatory compliance."""
    import json
    log = AuditLog(
        user_id=user.get("user_id", "anonymous"),
        user_email=user.get("email", "unknown"),
        user_role=",".join(user.get("roles", ["viewer"])),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        details=json.dumps(details)
    )
    db.add(log)
    db.commit()
