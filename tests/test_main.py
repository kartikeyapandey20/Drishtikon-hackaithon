from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_main():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Welcome to the Visually Impaired Assistant API" in response.json()["message"]


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "api_version": "1.0.0"} 