from database.base import Base
from conftest import engine, test_admin, test_user, TestingSession


class TestRoutes:
    def setup_class(self):
        # Creates tables in the test database
        Base.metadata.create_all(bind=engine)

        # Seeds the database with test data
        with TestingSession() as session:
            session.add(test_user)
            session.add(test_admin)
            session.commit()

    def teardown_class(self):
        Base.metadata.drop_all(bind=engine)

    def test_user_auth(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/users/auth", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {
            'message': 'Successfully authenticated',
            'data': {
                "id": 1,
                "name": "User",
                "email": "user@test.com",
                "role": "user"
            }
        }

    def test_login(self, client):
        data = {"email": "admin@test.com", "password": "password"}

        # Query endpoint under test
        response = client.post("/users/login", json=data)

        # Assertions
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully fetched auth token"

    def test_login_invalid_email(self, client):
        data = {"email": "invalid@test.com", "password": "password"}

        # Query endpoint under test
        response = client.post("/users/login", json=data)

        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "Unauthorized: Invalid email"

    def test_login_invalid_password(self, client):
        data = {"email": "admin@test.com", "password": "invalid-password"}

        # Query endpoint under test
        response = client.post("/users/login", json=data)

        # Assertions
        assert response.status_code == 404
        error_msg = response.json()["detail"]
        assert error_msg == "Unauthorized: Invalid combination of email and password"

    def test_login_db_error(self, client, mocker):
        data = {"email": "admin@test.com", "password": "password"}

        # Mock DB method to simulate exception
        mocker.patch(
            'routes.userRoutes.UserRepository.get_user_by_email',
            side_effect=Exception('There was an error looking for the user')
        )

        # Query endpoint under test
        response = client.post("/users/login", json=data)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error looking for the user"

    def test_login_token_error(self, client, mocker):
        data = {"email": "admin@test.com", "password": "password"}

        # Mock DB method to simulate exception
        mocker.patch(
            'routes.userRoutes.generate_token',
            side_effect=Exception('There was an error generating the token')
        )

        # Query endpoint under test
        response = client.post("/users/login", json=data)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error generating the token"

    def test_get_users(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/users/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {
                "name": "User",
                "email": "user@test.com",
                "role": "user"
            },
            {
                "name": "Admin",
                "email": "admin@test.com",
                "role": "admin"
            }
        ]

    def test_create_user(self, client):
        data = {
            "name": "testuser",
            "email": "testuser@nofoobar.com",
            "password": "aVerySecureP@ssw0rd",
            "role": "user"
        }
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.post("/users/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "testuser"
        assert response.json()["email"] == "testuser@nofoobar.com"
        assert response.json()["role"] == "user"

    def test_create_user_error(self, client, mocker):
        data = {
            "name": "testuser2",
            "email": "testuser2@nofoobar.com",
            "password": "aVerySecureP@ssw0rd",
            "role": "user"
        }
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            'routes.userRoutes.UserRepository.create_user',
            side_effect=Exception('There was an error')
        )

        # Query endpoint under test
        response = client.post("/users/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    def test_update_user(self, client):
        data = {
            "name": "testupdate",
            "email": "updateduser@nofoobar.com",
            "role": "user"
        }
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.put("/users/3", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "The user was successfully updated"}

    def test_update_user_error(self, client, mocker):
        data = {
            "name": "testupdate",
            "email": "updateduser@nofoobar.com",
            "role": "user"
        }
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            'routes.userRoutes.UserRepository.update_user',
            side_effect=Exception('There was an error')
        )

        # Query endpoint under test
        response = client.put("/users/3", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    def test_remove_user(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.delete("/users/3", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "The user was successfully removed"}

    def test_remove_user_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            'routes.userRoutes.UserRepository.remove_user',
            side_effect=Exception('There was an error')
        )

        # Query endpoint under test
        response = client.delete("/users/2", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"
