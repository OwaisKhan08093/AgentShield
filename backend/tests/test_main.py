"""Basic endpoint tests for AgentShield API."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Verify that root endpoint returns project name and status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AgentShield"
    assert data["status"] == "online"
    assert "version" in data


def test_health_check():
    """Verify that health check endpoint returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
