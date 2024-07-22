from app import app
from core.database.models import User
from fastapi.testclient import TestClient
import middleware.authMiddleware as authMiddleware
import middleware.dbMiddleware as dbMiddleware
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Authorized users
test_user = User(
    "User",
    "user@test.com",
    "$2b$12$4kHVTQCMgWieAvSHUTWFVu11gAY0wXb1SDWtuAbiV2L9hITuxBQxy",
    "user"
)
test_admin = User(
    "Admin",
    "admin@test.com",
    "$2b$12$4kHVTQCMgWieAvSHUTWFVu11gAY0wXb1SDWtuAbiV2L9hITuxBQxy",
    "admin"
)


# Fake DB session, with a containerized test DB
# In local development: TEST_DB_URL = "postgresql+psycopg2://test:test@localhost:5000/cnc_db"
# In Docker: TEST_DB_URL = "postgresql+psycopg2://test:test@testdb:5432/cnc_db"
TEST_DB_URL = "postgresql+psycopg2://test:test@testdb:5432/cnc_db"
engine = create_engine(TEST_DB_URL)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def client() -> TestClient:
    # Mock user authentication and authorization
    def mock_auth_user():
        test_user.id = 1
        return test_user

    def mock_auth_admin():
        test_admin.id = 2
        return test_admin

    # Mock DB
    def get_test_db():
        database = TestingSession()
        database.expire_on_commit = False
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides.update({
        authMiddleware.auth_user: mock_auth_user,
        authMiddleware.auth_admin: mock_auth_admin,
        dbMiddleware.get_db: get_test_db
    })

    return TestClient(app=app)
