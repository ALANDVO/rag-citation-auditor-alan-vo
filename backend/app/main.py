"""Main FastAPI entrypoint for RAG Citation & Faithfulness Auditor."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.audits import router as audits_router
from app.api.review import router as review_router
from app.api.evaluation import router as eval_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation: verify production guards
    settings.validate_production_guards()
    # Initialize database tables
    init_db()
    yield


app = FastAPI(
    title="RAG Citation & Faithfulness Auditor",
    description="Deterministic verification engine for RAG citations, quantitative claims, and human review.",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration allowing local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforces baseline HTTP security headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Health check endpoints
@app.get("/healthz")
def healthz():
    """Liveness probe."""
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/health/ready")
def readiness():
    """Readiness probe checking database connectivity."""
    from app.core.database import SessionLocal
    from sqlalchemy import text
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready", "version": settings.VERSION}
    except Exception as e:
        return Response(content=f"Database error: {str(e)}", status_code=503)


# Mount API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(audits_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")
app.include_router(eval_router, prefix="/api/v1")
