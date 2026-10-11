from unittest.mock import patch


def test_login_returns_token(client, app_context, test_admin):
    app_context.user_service.get_user_by_email.return_value = test_admin
    with patch("manager.adapters.api.routes.rootRoutes.validate_password", return_value=True):
        response = client.post(
            "/login", json={"email": test_admin.email, "password": "Password1!"}
        )

    assert response.status_code == 200
    assert response.json()["id"] == test_admin.id
    assert response.json()["token"]
    app_context.user_service.get_user_by_email.assert_called_once_with(test_admin.email)


def test_login_rejects_unknown_email(client, app_context):
    app_context.user_service.get_user_by_email.return_value = None

    response = client.post("/login", json={"email": "missing@test.com", "password": "Password1!"})

    assert response.status_code == 404
    assert response.json()["detail"] == "No autorizado: Email inválido"


def test_login_rejects_invalid_password(client, app_context, test_admin):
    app_context.user_service.get_user_by_email.return_value = test_admin
    with patch("manager.adapters.api.routes.rootRoutes.validate_password", return_value=False):
        response = client.post(
            "/login", json={"email": test_admin.email, "password": "wrong-password"}
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "No autorizado: Combinación inválida de email y contraseña"
