"""Tests for evaluation run triggering, listing, and inspection REST API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from app.api.dependencies import get_evaluation_repository
from app.main import app
from app.storage.repository import SQLiteEvaluationRepository

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_repository(tmp_path: Path):
    """Override the evaluation repository dependency with an isolated temporary SQLite database."""
    test_db = str(tmp_path / "test_api_runs.db")
    repo = SQLiteEvaluationRepository(test_db)
    app.dependency_overrides[get_evaluation_repository] = lambda: repo
    yield repo
    repo.close()
    app.dependency_overrides.pop(get_evaluation_repository, None)


def test_create_run_all_canonical_scenarios():
    """Verify POST /api/v1/runs executes and persists an evaluation run for all scenarios."""
    payload = {
        "suite_id": "support-agent-security-v1",
        "agent_id": "reference-agent",
        "options": {
            "continue_on_error": True,
            "record_trace": True,
        },
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "run_id" in data
    assert "report_id" in data
    assert data["suite_id"] == "support-agent-security-v1"
    assert data["status"] == "completed"
    assert data["overall_outcome"] == "pass"
    assert data["total_scenarios"] >= 16
    assert data["passed_count"] == data["total_scenarios"]
    assert data["failed_count"] == 0
    assert data["error_count"] == 0
    assert "metrics_summary" in data
    assert "overall_pass_rate" in data["metrics_summary"]


def test_create_run_selected_scenarios_subset():
    """Verify POST /api/v1/runs with specific scenario_ids executes only the selected subset."""
    payload = {
        "suite_id": "support-agent-security-v1",
        "agent_id": "reference-agent",
        "scenario_ids": ["BENIGN-ORDER-LOOKUP-001", "AUTHZ-CROSS-ORDER-001"],
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["total_scenarios"] == 2
    assert data["passed_count"] == 2
    assert data["failed_count"] == 0


def test_create_run_unknown_suite_id_returns_400():
    """Verify 400 Bad Request when an invalid or unsupported suite_id is provided."""
    payload = {
        "suite_id": "unknown-suite-id-xyz",
        "agent_id": "reference-agent",
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 400
    assert "Unknown suite ID" in response.json()["detail"]


def test_create_run_unknown_agent_id_returns_400():
    """Verify 400 Bad Request when an unsupported agent_id is provided."""
    payload = {
        "suite_id": "support-agent-security-v1",
        "agent_id": "unsupported-custom-agent",
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 400
    assert "Unsupported agent ID" in response.json()["detail"]


def test_create_run_unknown_scenario_id_returns_400():
    """Verify 400 Bad Request when a non-existent scenario_id is submitted."""
    payload = {
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["NON-EXISTENT-SCENARIO-999"],
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 400
    assert "NON-EXISTENT-SCENARIO-999" in response.json()["detail"]


def test_create_run_empty_scenario_ids_list_returns_400():
    """Verify 400 Bad Request when scenario_ids is explicitly an empty list."""
    payload = {
        "suite_id": "support-agent-security-v1",
        "scenario_ids": [],
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 400
    assert "cannot be an empty list" in response.json()["detail"]


def test_list_runs_returns_recent_runs_ordered():
    """Verify GET /api/v1/runs returns recent runs in newest-first order."""
    # Initially empty
    empty_resp = client.get("/api/v1/runs")
    assert empty_resp.status_code == 200
    assert empty_resp.json() == []

    # Create two runs
    r1 = client.post("/api/v1/runs", json={
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["BENIGN-ORDER-LOOKUP-001"],
    }).json()

    r2 = client.post("/api/v1/runs", json={
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["AUTHZ-CROSS-ORDER-001"],
    }).json()

    # List runs
    list_resp = client.get("/api/v1/runs")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert len(runs) == 2

    # Newest first
    assert runs[0]["run_id"] == r2["run_id"]
    assert runs[1]["run_id"] == r1["run_id"]


def test_list_runs_pagination():
    """Verify limit and offset query parameters."""
    for sid in ["BENIGN-ORDER-LOOKUP-001", "AUTHZ-CROSS-ORDER-001", "INJECT-DIRECT-OVERRIDE-REASON-001"]:
        resp = client.post("/api/v1/runs", json={
            "suite_id": "support-agent-security-v1",
            "scenario_ids": [sid],
        })
        assert resp.status_code == 201

    page1 = client.get("/api/v1/runs?limit=2&offset=0").json()
    page2 = client.get("/api/v1/runs?limit=2&offset=2").json()

    assert len(page1) == 2
    assert len(page2) == 1
    assert page1[0]["run_id"] != page2[0]["run_id"]


def test_get_run_summary_by_id_success():
    """Verify GET /api/v1/runs/{run_id} returns run aggregate summary."""
    create_resp = client.post("/api/v1/runs", json={
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["BENIGN-ORDER-LOOKUP-001"],
    })
    run_id = create_resp.json()["run_id"]

    get_resp = client.get(f"/api/v1/runs/{run_id}")
    assert get_resp.status_code == 200

    data = get_resp.json()
    assert data["run_id"] == run_id
    assert data["overall_outcome"] == "pass"
    assert data["total_scenarios"] == 1
    assert data["passed_count"] == 1


def test_get_run_summary_not_found():
    """Verify 404 response for unknown run ID."""
    response = client.get("/api/v1/runs/non-existent-run-id-999")
    assert response.status_code == 404
    assert "non-existent-run-id-999" in response.json()["detail"]
