from api.app import app
from fastapi.testclient import TestClient


def test_healthcheck():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == "OK"
