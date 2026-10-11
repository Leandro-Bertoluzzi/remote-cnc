def test_invalid_monitor_channel_is_rejected(client, user_headers):
    response = client.get("/monitor/stream/not-allowed", headers=user_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Canal no permitido: not-allowed"
