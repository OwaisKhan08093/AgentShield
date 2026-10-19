"""Tests for scenario listing and inspection REST API endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


def test_list_scenarios_returns_all_canonical_scenarios():
    """Verify GET /api/v1/scenarios returns safe summary list of all enabled scenarios."""
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 16

    # Verify summary fields are present and safe
    first = data[0]
    assert "scenario_id" in first
    assert "name" in first
    assert "category" in first
    assert "description" in first
    assert "security_objective" in first
    assert "risk_level" in first
    assert "tags" in first
    assert "version" in first
    assert "enabled" in first
    assert first["enabled"] is True

    # Verify internal secrets / full raw requests are NOT leaked in summary
    assert "request" not in first
    assert "expected_behavior" not in first


def test_list_scenarios_filter_by_category():
    """Verify filtering scenarios by attack category."""
    response = client.get("/api/v1/scenarios?category=unauthorized_access")
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0
    for item in data:
        assert item["category"] == "unauthorized_access"


def test_list_scenarios_filter_by_invalid_category():
    """Verify querying an invalid category returns 422 Unprocessable Entity."""
    response = client.get("/api/v1/scenarios?category=not_a_valid_category")
    assert response.status_code == 422


def test_list_scenarios_filter_by_tag():
    """Verify filtering scenarios by tag string."""
    response = client.get("/api/v1/scenarios?tag=prompt_injection")
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0
    for item in data:
        assert any("prompt_injection" in t.lower() for t in item["tags"])


def test_list_scenarios_filter_by_unknown_tag():
    """Verify filtering by non-existent tag returns empty list."""
    response = client.get("/api/v1/scenarios?tag=definitely-nonexistent-tag-xyz")
    assert response.status_code == 200
    assert response.json() == []


def test_get_scenario_detail_success():
    """Verify retrieving detailed scenario definition by ID."""
    response = client.get("/api/v1/scenarios/AUTHZ-CROSS-ORDER-001")
    assert response.status_code == 200

    data = response.json()
    assert data["scenario_id"] == "AUTHZ-CROSS-ORDER-001"
    assert data["name"] == "Cross-Customer Order Access Attempt"
    assert data["category"] == "unauthorized_access"
    assert "expected_behavior" in data
    assert data["expected_behavior"]["expected_status"] == "denied"
    assert data["expected_behavior"]["must_have_authorization_denial"] is True
    assert "success_condition" in data
    assert "failure_condition" in data


def test_get_scenario_detail_not_found():
    """Verify 404 response for unknown scenario ID."""
    response = client.get("/api/v1/scenarios/UNKNOWN-SCENARIO-999")
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error
    assert "UNKNOWN-SCENARIO-999" in error["detail"]
