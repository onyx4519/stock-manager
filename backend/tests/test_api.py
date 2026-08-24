from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["mock_mode"] is True


def test_quote_is_marked_mock():
    response = client.get("/api/v1/market/quotes/NVDA")
    assert response.status_code == 200
    assert response.json()["data_status"] == "MOCK"
