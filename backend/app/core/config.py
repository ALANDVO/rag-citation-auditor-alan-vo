"""Application configuration with validation and environment loading."""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration settings for RAG Citation Auditor."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "rag-citation-auditor-alan-vo"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./auditor.db"

    # Security & Sessions
    SECRET_KEY: str = "dev-secret-key-change-in-production-random-min32chars"
    SESSION_SECRET: str = "dev-session-secret-change-in-production-min32"
    SESSION_MAX_AGE_SECONDS: int = 86400  # 24 hours
    DEMO_MODE: bool = True
    ALLOWED_HOSTS: List[str] = ["127.0.0.1", "localhost", "testserver"]

    # Keycloak / OIDC Settings
    OIDC_ISSUER_URL: str = "http://127.0.0.1:8080/realms/rag-citation-auditor"
    OIDC_CLIENT_ID: str = "rag-auditor-backend"
    OIDC_CLIENT_SECRET: str = ""
    OIDC_REDIRECT_URI: str = "http://127.0.0.1:8000/api/v1/auth/callback"
    OIDC_COOKIE_NAME: str = "auditor_session"

    # LLM Settings (Server-side only, operator configurable, never request input)
    LLM_API_KEY: str = ""
    LLM_PROVIDER: str = "openai-compatible"
    LLM_MODEL: str = "qwen3.8-27b"
    LLM_BASE_URL: str = "https://llm.chris-vo.com/v1"
    LLM_TIMEOUT_SECONDS: float = 15.0

    def validate_production_guards(self) -> None:
        """Enforces that demo mode cannot run in a production environment."""
        if self.ENVIRONMENT.lower() == "production" and self.DEMO_MODE:
            raise RuntimeError(
                "Fatal configuration violation: DEMO_MODE cannot be enabled in production environment."
            )


settings = Settings()
