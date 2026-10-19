"""Tests for evaluation run triggering, listing, and inspection REST API endpoints."""

from datetime import datetime, timezone
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from app.api.dependencies import get_evaluation_repository
from app.main import app
from app.models.event import ExecutionStatus
from app.models.finding import (
    EvaluationMetrics,
    EvaluationOutcome,
    EvaluationReport,
    Finding,
    MetricValue,
    ScenarioEvaluation,
    SummaryCounts,
)
from app.models.scenario import RiskLevel, ScenarioCategory, ScenarioExecutionStatus
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


def _make_metric_value(num: int, den: int, name: str = "Test Metric") -> MetricValue:
    val = (num / den) if den > 0 else None
    disp = f"{(val * 100):.1f}%" if val is not None else "N/A"
    return MetricValue(
        name=name,
        numerator=num,
        denominator=den,
        value=val,
        display_value=disp,
        description=f"Description of {name}",
        formula=f"{name} = num / den",
    )


def _make_sample_report_multi_outcome(run_id: str) -> EvaluationReport:
    """Helper to construct an EvaluationReport containing PASS, FAIL, and ERROR outcomes."""
    now = datetime.now(timezone.utc).isoformat()
    se_pass = ScenarioEvaluation(
        scenario_id="SCENARIO-PASS-001",
        scenario_name="Passing Scenario",
        category=ScenarioCategory.BENIGN_TASK,
        risk_level=RiskLevel.LOW,
        outcome=EvaluationOutcome.PASS,
        findings=[
            Finding(
                finding_id="fnd_p1",
                scenario_id="SCENARIO-PASS-001",
                rule_id="RULE-CTRL-001",
                rule_name="Positive Control Rule",
                outcome=EvaluationOutcome.PASS,
                severity=RiskLevel.LOW,
                message="Positive control task succeeded.",
                evidence={"status": "success"},
                timestamp=now,
            )
        ],
        execution_status=ScenarioExecutionStatus.COMPLETED,
        actual_status=ExecutionStatus.SUCCESS,
        expected_status=ExecutionStatus.SUCCESS,
        attempt_detected=False,
        violation_prevented=False,
        data_exposed=False,
        explanation="Task completed successfully.",
        evaluated_at=now,
    )
    se_fail = ScenarioEvaluation(
        scenario_id="SCENARIO-FAIL-001",
        scenario_name="Failing Scenario",
        category=ScenarioCategory.UNAUTHORIZED_ACCESS,
        risk_level=RiskLevel.HIGH,
        outcome=EvaluationOutcome.FAIL,
        findings=[
            Finding(
                finding_id="fnd_f1",
                scenario_id="SCENARIO-FAIL-001",
                rule_id="RULE-AUTHZ-001",
                rule_name="Authorization Rule",
                outcome=EvaluationOutcome.FAIL,
                severity=RiskLevel.HIGH,
                message="Tool was invoked without required authorization denial.",
                evidence={"status": "failed"},
                timestamp=now,
            )
        ],
        execution_status=ScenarioExecutionStatus.COMPLETED,
        actual_status=ExecutionStatus.SUCCESS,
        expected_status=ExecutionStatus.DENIED,
        attempt_detected=True,
        violation_prevented=False,
        data_exposed=True,
        explanation="Unauthorized action was allowed.",
        evaluated_at=now,
    )
    se_error = ScenarioEvaluation(
        scenario_id="SCENARIO-ERROR-001",
        scenario_name="Error Scenario",
        category=ScenarioCategory.MALFORMED_INPUT,
        risk_level=RiskLevel.MEDIUM,
        outcome=EvaluationOutcome.ERROR,
        findings=[
            Finding(
                finding_id="fnd_e1",
                scenario_id="SCENARIO-ERROR-001",
                rule_id="RULE-TRACE-001",
                rule_name="Trace Integrity Rule",
                outcome=EvaluationOutcome.ERROR,
                severity=RiskLevel.HIGH,
                message="Execution crashed before response.",
                evidence={"error": "runner crash"},
                timestamp=now,
            )
        ],
        execution_status=ScenarioExecutionStatus.ERROR,
        actual_status=None,
        expected_status=ExecutionStatus.ERROR,
        attempt_detected=False,
        violation_prevented=False,
        data_exposed=False,
        explanation="Runner encountered an unhandled exception.",
        evaluated_at=now,
    )
    metric_val = _make_metric_value(1, 3)
    metrics = EvaluationMetrics(
        overall_pass_rate=metric_val,
        attack_success_rate=_make_metric_value(1, 3, "Attack Success Rate"),
        unauthorized_prevention_rate=_make_metric_value(1, 3, "Unauthorized Prevention Rate"),
        sensitive_data_exposure_rate=_make_metric_value(1, 3, "Data Exposure Rate"),
        benign_task_success_rate=_make_metric_value(1, 3, "Benign Task Success Rate"),
        policy_enforcement_failure_rate=_make_metric_value(1, 3, "Policy Failure Rate"),
        run_completion_rate=_make_metric_value(2, 3, "Run Completion Rate"),
        security_score=metric_val,
    )
    return EvaluationReport(
        report_id=f"rpt_{run_id}",
        run_id=run_id,
        evaluator_version="1.0.0",
        suite_version=1,
        started_at=now,
        completed_at=now,
        overall_outcome=EvaluationOutcome.FAIL,
        summary_counts=SummaryCounts(
            total_scenarios=3,
            passed_count=1,
            failed_count=1,
            error_count=1,
            not_run_count=0,
        ),
        metrics=metrics,
        scenario_evaluations=[se_pass, se_fail, se_error],
        findings=se_pass.findings + se_fail.findings + se_error.findings,
    )


# ==============================================================================
# Run Creation and Listing Tests
# ==============================================================================

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


# ==============================================================================
# Endpoint A: GET /api/v1/runs/{run_id}/results Tests
# ==============================================================================

def test_get_run_results_multiple_scenarios():
    """Verify GET /api/v1/runs/{run_id}/results returns detailed scenario results."""
    create_resp = client.post("/api/v1/runs", json={
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["BENIGN-ORDER-LOOKUP-001", "AUTHZ-CROSS-ORDER-001"],
    })
    assert create_resp.status_code == 201
    run_id = create_resp.json()["run_id"]

    results_resp = client.get(f"/api/v1/runs/{run_id}/results")
    assert results_resp.status_code == 200

    results = results_resp.json()
    assert isinstance(results, list)
    assert len(results) == 2

    # Verify first scenario structure
    r0 = results[0]
    assert r0["scenario_id"] == "BENIGN-ORDER-LOOKUP-001"
    assert r0["scenario_name"] == "Authorized Order Lookup (Positive Control)"
    assert r0["category"] == "benign_task"
    assert r0["risk_level"] == "informational"
    assert r0["outcome"] == "pass"
    assert r0["execution_status"] == "completed"
    assert r0["actual_status"] == "success"
    assert r0["expected_status"] == "success"
    assert r0["explanation"] != ""
    assert r0["finding_count"] >= 1
    assert len(r0["findings"]) == r0["finding_count"]
    assert r0["duration_ms"] is None  # Does not manufacture unrecorded durations

    # Verify second scenario (attempt blocked)
    r1 = results[1]
    assert r1["scenario_id"] == "AUTHZ-CROSS-ORDER-001"
    assert r1["outcome"] == "pass"
    assert r1["attempt_detected"] is True
    assert r1["violation_prevented"] is True
    assert r1["data_exposed"] is False


def test_get_run_results_preserves_all_outcomes(override_repository: SQLiteEvaluationRepository):
    """Verify PASS, FAIL, and ERROR scenario outcomes are preserved with exact finding counts."""
    report = _make_sample_report_multi_outcome("run_multi_outcome_test")
    override_repository.save_report(report)

    response = client.get("/api/v1/runs/run_multi_outcome_test/results")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 3

    by_id = {r["scenario_id"]: r for r in results}
    assert by_id["SCENARIO-PASS-001"]["outcome"] == "pass"
    assert by_id["SCENARIO-PASS-001"]["finding_count"] == 1

    assert by_id["SCENARIO-FAIL-001"]["outcome"] == "fail"
    assert by_id["SCENARIO-FAIL-001"]["data_exposed"] is True
    assert by_id["SCENARIO-FAIL-001"]["finding_count"] == 1

    assert by_id["SCENARIO-ERROR-001"]["outcome"] == "error"
    assert by_id["SCENARIO-ERROR-001"]["actual_status"] is None
    assert by_id["SCENARIO-ERROR-001"]["finding_count"] == 1


def test_get_run_results_deterministic_ordering():
    """Verify scenario results are returned in deterministic execution order."""
    create_resp = client.post("/api/v1/runs", json={
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["AUTHZ-CROSS-ORDER-001", "BENIGN-ORDER-LOOKUP-001"],
    })
    run_id = create_resp.json()["run_id"]

    results = client.get(f"/api/v1/runs/{run_id}/results").json()
    assert [r["scenario_id"] for r in results] == ["AUTHZ-CROSS-ORDER-001", "BENIGN-ORDER-LOOKUP-001"]


def test_get_run_results_unknown_run_returns_404():
    """Verify 404 response when querying results for a non-existent run ID."""
    response = client.get("/api/v1/runs/unknown-run-12345/results")
    assert response.status_code == 404
    assert "unknown-run-12345" in response.json()["detail"]


# ==============================================================================
# Endpoint B: GET /api/v1/runs/{run_id}/trace Tests
# ==============================================================================

def test_get_run_trace_ordering_and_scenario_filtering():
    """Verify GET /api/v1/runs/{run_id}/trace preserves event ordering and supports scenario filter."""
    create_resp = client.post("/api/v1/runs", json={
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["BENIGN-ORDER-LOOKUP-001", "AUTHZ-CROSS-ORDER-001"],
    })
    run_id = create_resp.json()["run_id"]

    # 1. Full run trace
    full_resp = client.get(f"/api/v1/runs/{run_id}/trace")
    assert full_resp.status_code == 200
    all_events = full_resp.json()
    assert isinstance(all_events, list)
    assert len(all_events) > 0

    # 2. Filtered by specific scenario
    filtered_resp = client.get(f"/api/v1/runs/{run_id}/trace?scenario_id=AUTHZ-CROSS-ORDER-001")
    assert filtered_resp.status_code == 200
    scenario_events = filtered_resp.json()
    assert len(scenario_events) > 0
    assert len(scenario_events) < len(all_events)

    # Verify chronological sequence ordering: 1, 2, 3...
    sequences = [ev["sequence"] for ev in scenario_events]
    assert sequences == sorted(sequences)
    assert sequences[0] == 1


def test_get_run_trace_sanitization_no_secrets():
    """Verify trace events do not expose raw secrets, unauthorized order notes, or API credentials."""
    create_resp = client.post("/api/v1/runs", json={
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["AUTHZ-CROSS-ORDER-001"],
    })
    run_id = create_resp.json()["run_id"]

    trace_resp = client.get(f"/api/v1/runs/{run_id}/trace")
    assert trace_resp.status_code == 200
    events = trace_resp.json()

    for ev in events:
        assert "event_id" in ev
        assert "sequence" in ev
        assert "event_type" in ev
        payload = ev.get("sanitized_payload")
        if payload:
            payload_str = str(payload).lower()
            # Ensure no credentials or sensitive tokens leaked
            assert "secret" not in payload_str
            assert "password" not in payload_str
            assert "api_key" not in payload_str
            # In cross-customer unauthorized attempt, Bob's sensitive note must not be exposed
            assert "sensitive order" not in payload_str


def test_get_run_trace_unknown_run_returns_404():
    """Verify 404 response when querying trace for non-existent run ID."""
    response = client.get("/api/v1/runs/non-existent-run-trace-999/trace")
    assert response.status_code == 404
    assert "non-existent-run-trace-999" in response.json()["detail"]


# ==============================================================================
# Endpoint C: GET /api/v1/runs/{run_id}/report.json Tests
# ==============================================================================

def test_export_report_json_success():
    """Verify GET /api/v1/runs/{run_id}/report.json exports full report with schema version metadata."""
    create_resp = client.post("/api/v1/runs", json={
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["BENIGN-ORDER-LOOKUP-001"],
    })
    run_id = create_resp.json()["run_id"]

    export_resp = client.get(f"/api/v1/runs/{run_id}/report.json")
    assert export_resp.status_code == 200

    # Header check
    disposition = export_resp.headers.get("Content-Disposition", "")
    assert f'filename="report_{run_id}.json"' in disposition

    data = export_resp.json()
    assert "schema_version" in data
    assert data["schema_version"] == "1.0.0"
    assert "exported_at" in data

    # Verify nested report integrity
    report = data["report"]
    assert report["run_id"] == run_id
    assert report["overall_outcome"] == "pass"
    assert "metrics" in report
    assert "summary_counts" in report
    assert "scenario_evaluations" in report
    assert "findings" in report
    assert "limitation_statement" in report
    assert len(report["scenario_evaluations"]) == 1
    assert len(report["findings"]) >= 1


def test_export_report_json_unknown_run_returns_404():
    """Verify 404 response when exporting report for non-existent run ID."""
    response = client.get("/api/v1/runs/unknown-report-export-999/report.json")
    assert response.status_code == 404
    assert "unknown-report-export-999" in response.json()["detail"]


# ==============================================================================
# Persistence Across Process / Repository Reopening
# ==============================================================================

def test_retrieval_after_closing_and_reopening_file_database(tmp_path: Path):
    """Verify results, traces, and report export work after closing and reopening database."""
    file_db = str(tmp_path / "persistent_api_test.db")

    # Session 1: Create and execute run
    repo1 = SQLiteEvaluationRepository(file_db)
    app.dependency_overrides[get_evaluation_repository] = lambda: repo1

    create_resp = client.post("/api/v1/runs", json={
        "suite_id": "support-agent-security-v1",
        "scenario_ids": ["BENIGN-ORDER-LOOKUP-001", "AUTHZ-CROSS-ORDER-001"],
    })
    run_id = create_resp.json()["run_id"]
    repo1.close()

    # Session 2: Connect via brand new repository instance to the same file
    repo2 = SQLiteEvaluationRepository(file_db)
    app.dependency_overrides[get_evaluation_repository] = lambda: repo2

    # Check results
    res_resp = client.get(f"/api/v1/runs/{run_id}/results")
    assert res_resp.status_code == 200
    assert len(res_resp.json()) == 2

    # Check trace
    trace_resp = client.get(f"/api/v1/runs/{run_id}/trace")
    assert trace_resp.status_code == 200
    assert len(trace_resp.json()) > 0

    # Check report export
    export_resp = client.get(f"/api/v1/runs/{run_id}/report.json")
    assert export_resp.status_code == 200
    assert export_resp.json()["report"]["run_id"] == run_id

    repo2.close()
