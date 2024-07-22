from app import app
from core.database.base import Base
from core.database.models import User
import datetime
from fastapi.testclient import TestClient
from jwt import ExpiredSignatureError, InvalidSignatureError
import middleware.dbMiddleware as dbMiddleware
from tests.conftest import engine, TestingSession


# Example users
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


# Override the default dependencies
def get_test_db():
    database = TestingSession()
    try:
        yield database
    finally:
        database.close()


app.dependency_overrides[dbMiddleware.get_db] = get_test_db


# Test HTTP client
client = TestClient(app)


class TestAuthMiddleware:
    def setup_class(self):
        # Creates tables in the test database
        Base.metadata.create_all(bind=engine)

        # Seeds the database with test data
        with TestingSession() as session:
            session.add(test_user)
            session.add(test_admin)
            session.commit()
            session.close()

    def teardown_class(self):
        Base.metadata.drop_all(bind=engine)

# --------------------------------------------------------------------- #
# -------------------------------- USER ------------------------------- #
# --------------------------------------------------------------------- #

    def test_auth_user_header(self, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock JWT validation
        mock_verify_token = mocker.patch(
            'authMiddleware.verify_token',
            return_value={
                'user_id': 1,
                'exp': datetime.datetime.now() + datetime.timedelta(1)
            },
        )

        # Query endpoint under test
        response = client.get("/tools/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert mock_verify_token.call_count == 1

    def test_auth_user_query(self, mocker):
        # Mock JWT validation
        mock_verify_token = mocker.patch(
            'authMiddleware.verify_token',
            return_value={
                'user_id': 1,
                'exp': datetime.datetime.now() + datetime.timedelta(1)
            },
        )

        # Query endpoint under test
        response = client.get("/tools?token=a-valid-token")

        # Assertions
        assert response.status_code == 200
        assert mock_verify_token.call_count == 1

    def test_error_token_missing(self):
        # Query endpoint under test
        response = client.get("/tools/")

        # Assertions
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized: Authentication Token is missing!"

    def test_error_expired_token(self, mocker):
        headers = {"Authorization": "Bearer an-expired-token"}

        # Mock JWT validation
        mock_verify_token = mocker.patch(
            'authMiddleware.verify_token',
            side_effect=ExpiredSignatureError(),
        )

        # Query endpoint under test
        response = client.get("/tools/", headers=headers)

        # Assertions
        assert mock_verify_token.call_count == 1
        assert response.status_code == 401
        assert response.json()["detail"] == "Expired token, please login to generate a new one"

    def test_error_invalid_token(self, mocker):
        headers = {"Authorization": "Bearer an-expired-token"}

        # Mock JWT validation
        mock_verify_token = mocker.patch(
            'authMiddleware.verify_token',
            side_effect=InvalidSignatureError(),
        )

        # Query endpoint under test
        response = client.get("/tools/", headers=headers)

        # Assertions
        assert mock_verify_token.call_count == 1
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token, please login to generate a new one"

    def test_error_user_not_found(self, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock JWT validation
        mock_verify_token = mocker.patch(
            'authMiddleware.verify_token',
            return_value={
                'user_id': 500,
                'exp': datetime.datetime.now() + datetime.timedelta(1)
            },
        )

        # Query endpoint under test
        response = client.get("/tools/", headers=headers)

        # Assertions
        assert mock_verify_token.call_count == 1
        assert response.status_code == 400
        assert response.json()["detail"] == "User with ID 500 was not found"

    def test_db_error(self, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock JWT validation
        mock_verify_token = mocker.patch(
            'authMiddleware.verify_token',
            return_value={
                'user_id': 1,
                'exp': datetime.datetime.now() + datetime.timedelta(1)
            },
        )
        # Mock DB method to simulate exception
        mock_get_user = mocker.patch(
            'authMiddleware.UserRepository.get_user_by_id',
            side_effect=Exception('There was an error')
        )

        # Query endpoint under test
        response = client.get("/tools/", headers=headers)

        # Assertions
        assert mock_verify_token.call_count == 1
        assert mock_get_user.call_count == 1
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

# --------------------------------------------------------------------- #
# ------------------------------- ADMIN ------------------------------- #
# --------------------------------------------------------------------- #

    def test_auth_admin_header(self, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock JWT validation
        mock_verify_token = mocker.patch(
            'authMiddleware.verify_token',
            return_value={
                'user_id': 2,
                'exp': datetime.datetime.now() + datetime.timedelta(1)
            },
        )

        # Query endpoint under test
        response = client.get("/users/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert mock_verify_token.call_count == 1

    def test_auth_admin_query(self, mocker):
        # Mock JWT validation
        mock_verify_token = mocker.patch(
            'authMiddleware.verify_token',
            return_value={
                'user_id': 2,
                'exp': datetime.datetime.now() + datetime.timedelta(1)
            },
        )

        # Query endpoint under test
        response = client.get("/users?token=a-valid-token")

        # Assertions
        assert response.status_code == 200
        assert mock_verify_token.call_count == 1

    def test_auth_admin_fails(self, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock JWT validation
        mock_verify_token = mocker.patch(
            'authMiddleware.verify_token',
            return_value={
                'user_id': 1,
                'exp': datetime.datetime.now() + datetime.timedelta(1)
            },
        )

        # Query endpoint under test
        response = client.get("/users/", headers=headers)

        # Assertions
        assert response.status_code == 401
        assert mock_verify_token.call_count == 1
        assert response.json()["detail"] == "Unauthorized: This endpoint requires admin permission"
