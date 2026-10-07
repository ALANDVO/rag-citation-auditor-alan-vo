"""Authentication API endpoints for Keycloak OIDC and guarded local demo mode."""
import secrets
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_session, generate_pkce_pair, get_current_user_optional, get_current_user, record_audit_log
from app.models.entities import SessionRecord
from app.models.schemas import UserProfile, DemoLoginRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])
PENDING_AUTH_STATES = {}


@router.get("/login")
def login(request: Request):
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    verifier, challenge = generate_pkce_pair()
    PENDING_AUTH_STATES[state] = {"verifier": verifier, "nonce": nonce}
    auth_url = (
        f"{settings.OIDC_ISSUER_URL}/protocol/openid-connect/auth?client_id={settings.OIDC_CLIENT_ID}"
        f"&response_type=code&scope=openid%20profile%20email&redirect_uri={settings.OIDC_REDIRECT_URI}"
        f"&state={state}&nonce={nonce}&code_challenge={challenge}&code_challenge_method=S256"
    )
    return {"auth_url": auth_url, "state": state}


@router.get("/callback")
async def oidc_callback(code: str, state: str, response: Response, db: Session = Depends(get_db)):
    stored = PENDING_AUTH_STATES.pop(state, None)
    if not stored:
        raise HTTPException(status_code=400, detail="Invalid or expired OIDC state parameter.")

    token_data = {
        "grant_type": "authorization_code", "client_id": settings.OIDC_CLIENT_ID,
        "client_secret": settings.OIDC_CLIENT_SECRET, "code": code,
        "redirect_uri": settings.OIDC_REDIRECT_URI, "code_verifier": stored["verifier"]
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{settings.OIDC_ISSUER_URL}/protocol/openid-connect/token", data=token_data)
            r.raise_for_status()
            tokens = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Keycloak communication failed: {str(e)}")

    import jwt
    try:
        payload = jwt.decode(tokens.get("id_token", tokens.get("access_token")), options={"verify_signature": False})
        uid = payload.get("sub", "keycloak-user")
        email = payload.get("email", f"{uid}@auth.local")
        roles = payload.get("realm_access", {}).get("roles", ["viewer"])
    except Exception:
        uid, email, roles = "oidc-user", "oidc-user@auth.local", ["analyst"]

    session = create_session(db, user_id=uid, email=email, roles=roles)
    response.set_cookie(key=settings.OIDC_COOKIE_NAME, value=session.session_id, max_age=settings.SESSION_MAX_AGE_SECONDS, httponly=True, samesite="lax", secure=False)
    record_audit_log(db, {"user_id": uid, "email": email, "roles": roles}, "OIDC_LOGIN_SUCCESS", "session", session.session_id, {"roles": roles})
    return {"status": "success", "user_id": uid, "email": email, "roles": roles, "csrf_token": session.csrf_token}


@router.post("/demo-login")
def demo_login(payload: DemoLoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    if settings.ENVIRONMENT.lower() == "production":
        raise HTTPException(status_code=403, detail="Demo mode is strictly prohibited in production environments.")
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Demo mode is disabled in system configuration.")

    client_host = request.client.host if request.client else "unknown"
    if client_host not in {"127.0.0.1", "localhost", "testclient"}:
        raise HTTPException(status_code=403, detail=f"Demo mode only permits connections from localhost. Received {client_host}.")

    uid, email, roles = f"demo-{payload.role}", f"demo-{payload.role}@demo.local", [payload.role]
    session = create_session(db, user_id=uid, email=email, roles=roles)
    response.set_cookie(key=settings.OIDC_COOKIE_NAME, value=session.session_id, max_age=settings.SESSION_MAX_AGE_SECONDS, httponly=True, samesite="lax", secure=False)
    record_audit_log(db, {"user_id": uid, "email": email, "roles": roles}, "DEMO_LOGIN_SUCCESS", "session", session.session_id, {"role": payload.role})
    return {"user_id": uid, "email": email, "roles": roles, "is_authenticated": True, "is_demo": True, "csrf_token": session.csrf_token}


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(user: Optional[dict] = Depends(get_current_user_optional)):
    if not user:
        return UserProfile(user_id="anonymous", email="", roles=[], is_authenticated=False, is_demo=False, csrf_token="")
    return UserProfile(user_id=user["user_id"], email=user["email"], roles=user["roles"], is_authenticated=True, is_demo=user["user_id"].startswith("demo-"), csrf_token=user["csrf_token"])


@router.post("/logout")
def logout(response: Response, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(SessionRecord).filter(SessionRecord.session_id == user["session_id"]).delete()
    db.commit()
    response.delete_cookie(settings.OIDC_COOKIE_NAME)
    record_audit_log(db, user, "LOGOUT_SUCCESS", "session", user["session_id"], {})
    return {"status": "logged_out"}
