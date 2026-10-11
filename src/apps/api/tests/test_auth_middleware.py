from datetime import datetime, timedelta, timezone

import jwt


def test_auth_user_header(client, user_headers, app_context):
    response = client.get("/tools/", headers=user_headers)

    assert response.status_code == 200
    app_context.user_service.get_user_by_id.assert_called_once_with(1)


def test_auth_user_query_token(client, test_user, app_context):
    from core.utilities.security import generate_token

    response = client.get("/tools/", params={"token": generate_token(test_user.id)})

    assert response.status_code == 200
    app_context.user_service.get_user_by_id.assert_called_once_with(test_user.id)


def test_auth_token_missing(client):
    response = client.get("/tools/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized: Authentication Token is missing!"


def test_auth_expired_token(client):
    token = jwt.encode(
        {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
        "api-tests-secret-key-32-bytes-long",
        algorithm="HS256",
    )

    response = client.get("/tools/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Expired token, login to generate a new one"


def test_auth_invalid_signature(client):
    token = jwt.encode(
        {"user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "wrong-secret-key-that-is-over-32-bytes",
        algorithm="HS256",
    )

    response = client.get("/tools/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token, login to generate a new one"


def test_auth_unknown_user_returns_bad_request(client, app_context):
    token = jwt.encode(
        {"user_id": 500, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "api-tests-secret-key-32-bytes-long",
        algorithm="HS256",
    )

    response = client.get("/tools/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "User with ID 500 was not found"
    app_context.user_service.get_user_by_id.assert_called_once_with(500)


def test_auth_user_service_error_returns_bad_request(client, user_headers, app_context):
    app_context.user_service.get_user_by_id.side_effect = RuntimeError("service error")

    response = client.get("/tools/", headers=user_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "service error"


def test_admin_endpoint_rejects_user(client, user_headers):
    response = client.get("/users/", headers=user_headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized: This endpoint requires admin permission"


def test_admin_endpoint_accepts_admin(client, admin_headers, app_context):
    response = client.get("/users/", headers=admin_headers)

    assert response.status_code == 200
    app_context.user_service.get_user_by_id.assert_called_once_with(2)
