import api.middleware.authMiddleware as authMiddleware
import api.middleware.dbMiddleware as dbMiddleware
import pytest
from api.main import app
from api_db import TestingSession, test_admin, test_user
from fastapi.testclient import TestClient


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

    app.dependency_overrides.update(
        {
            authMiddleware.auth_user: mock_auth_user,
            authMiddleware.auth_admin: mock_auth_admin,
            dbMiddleware.get_db: get_test_db,
        }
    )

    return TestClient(app=app)
