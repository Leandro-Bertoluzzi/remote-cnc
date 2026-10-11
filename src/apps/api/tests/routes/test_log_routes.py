def test_log_listing_uses_fake_storage(client, admin_headers, log_storage):
    log_storage.write_log("gateway.log", "gateway started\n")

    response = client.get("/logs/", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == [
        {"file_name": "gateway.log", "description": "Streaming de CNC gateway"}
    ]


def test_download_log_from_fake_storage(client, log_storage):
    log_storage.write_log("custom.log", "test log content\n")

    response = client.get("/logs/custom.log")

    assert response.status_code == 200
    assert response.text == "test log content\n"


def test_missing_log_returns_bad_request(client):
    response = client.get("/logs/missing.log")

    assert response.status_code == 400
    assert response.json()["detail"] == "El archivo no existe"
