"""Test fixtures and database setup using in-memory SQLite."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_session

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    settings.ENVIRONMENT = "test"
    settings.DEMO_MODE = True
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provides a transactional database session per test with rollback/clean state."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="http://127.0.0.1:8000") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def analyst_client(client, db_session):
    """Client authenticated as analyst with CSRF headers."""
    session = create_session(db_session, user_id="test-analyst", email="analyst@example.com", roles=["analyst"])
    client.cookies.set(settings.OIDC_COOKIE_NAME, session.session_id)
    client.headers.update({"x-csrf-token": session.csrf_token})
    return client


@pytest.fixture
def viewer_client(client, db_session):
    """Client authenticated as viewer."""
    session = create_session(db_session, user_id="test-viewer", email="viewer@example.com", roles=["viewer"])
    client.cookies.set(settings.OIDC_COOKIE_NAME, session.session_id)
    client.headers.update({"x-csrf-token": session.csrf_token})
    return client


@pytest.fixture
def admin_client(client, db_session):
    """Client authenticated as admin."""
    session = create_session(db_session, user_id="test-admin", email="admin@example.com", roles=["admin"])
    client.cookies.set(settings.OIDC_COOKIE_NAME, session.session_id)
    client.headers.update({"x-csrf-token": session.csrf_token})
    return client
