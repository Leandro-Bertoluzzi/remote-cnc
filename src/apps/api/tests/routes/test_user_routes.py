from core.domain.entities import User
from core.domain.exceptions import DuplicatedUserError


def test_list_users(client, app_context, admin_headers, test_user):
    app_context.user_service.get_all_users.return_value = [test_user]

    response = client.get("/users/", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": test_user.id,
            "name": test_user.name,
            "email": test_user.email,
            "role": test_user.role,
        }
    ]


def test_create_user(client, app_context, admin_headers):
    created_user = User(id=10, name="New", email="new@test.com", password="hashed", role="user")
    app_context.user_service.create_user.return_value = created_user

    response = client.post(
        "/users/",
        headers=admin_headers,
        json={
            "name": "New",
            "email": "new@test.com",
            "password": "Password1!",
            "role": "user",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 10
    app_context.user_service.create_user.assert_called_once_with(
        "New", "new@test.com", "Password1!", "user"
    )


def test_create_user_duplicate_email(client, app_context, admin_headers):
    app_context.user_service.create_user.side_effect = DuplicatedUserError("email already exists")

    response = client.post(
        "/users/",
        headers=admin_headers,
        json={
            "name": "New",
            "email": "new@test.com",
            "password": "Password1!",
            "role": "user",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "email already exists"


def test_update_user(client, app_context, admin_headers, test_user):
    app_context.user_service.update_user.return_value = test_user

    response = client.put(
        "/users/1",
        headers=admin_headers,
        json={"name": test_user.name, "email": test_user.email, "role": "user"},
    )

    assert response.status_code == 200
    app_context.user_service.update_user.assert_called_once_with(
        1, test_user.name, test_user.email, "user"
    )


def test_delete_user(client, app_context, admin_headers):
    response = client.delete("/users/3", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == {"success": "El usuario fue eliminado con éxito"}
    app_context.user_service.remove_user.assert_called_once_with(3)
