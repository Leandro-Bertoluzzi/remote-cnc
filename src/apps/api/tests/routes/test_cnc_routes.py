def test_gateway_state(client, admin_headers, app_context):
    app_context.gateway.state = "idle"

    response = client.get("/cnc/gateway/state", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == {"state": "idle", "running": True}


def test_acquire_and_release_session(client, admin_headers, app_context):
    acquired = client.post(
        "/cnc/session", headers=admin_headers, json={"client_type": "desktop"}
    )

    assert acquired.status_code == 200
    session_id = acquired.json()["session_id"]
    assert acquired.json()["user_id"] == 2

    released = client.delete(
        "/cnc/session", headers={**admin_headers, "X-CNC-Session": session_id}
    )

    assert released.status_code == 200
    assert app_context.gateway.active_session is None


def test_acquire_session_rejects_unavailable_gateway(client, admin_headers, app_context):
    app_context.gateway.state = None

    response = client.post(
        "/cnc/session", headers=admin_headers, json={"client_type": "desktop"}
    )

    assert response.status_code == 503


def test_command_is_recorded_by_gateway_fake(client, admin_headers, app_context):
    session_id = app_context.gateway.acquire_session(2, "desktop")

    response = client.post(
        "/cnc/command",
        headers={**admin_headers, "X-CNC-Session": session_id},
        json={"command": "G0 X1"},
    )

    assert response.status_code == 200
    assert app_context.gateway.commands == [(session_id, "G0 X1")]
