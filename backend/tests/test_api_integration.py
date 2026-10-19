"""End-to-end API integration tests, failure handling, timeout semantics, and persistence verification."""

import concurrent.futures
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from app.agent.base import AgentResponse, BaseAgent
from app.api.dependencies import get_evaluation_repository, get_scenario_registry
from app.evaluator import get_default_evaluator
from app.evaluator.assertions import SecurityRuleEvaluator
from app.evaluator.engine import SecurityEvaluator
from app.evaluator.metrics import MetricsCalculator
from app.main import app
from app.models.event import ExecutionStatus, ExecutionTrace, SupportRequest
from app.models.finding import (
    EvaluationMetrics,
    EvaluationOutcome,
    EvaluationReport,
    Finding,
    MetricValue,
    ScenarioEvaluation,
    SummaryCounts,
)
from app.models.scenario import (
    ExpectedBehavior,
    RiskLevel,
    Scenario,
    ScenarioCategory,
    ScenarioExecutionStatus,
    ScenarioResult,
    SuiteExecutionResult,
)
from app.scenarios import SCENARIO_LIBRARY
from app.scenarios.registry import ScenarioRegistry
from app.scenarios.runner import ScenarioRunner
from app.storage.database import DatabaseManager
from app.storage.exceptions import DuplicateRunError, StorageError
from app.storage.repository import SQLiteEvaluationRepository

client = TestClient(app)


@pytest.fixture
def isolated_db_repo(tmp_path: Path):
    """Provide a fresh SQLiteEvaluationRepository backed by an isolated file database."""
    db_file = str(tmp_path / "integration_test.db")
    repo = SQLiteEvaluationRepository(db_file)
    app.dependency_overrides[get_evaluation_repository] = lambda: repo
    yield repo, db_file
    repo.close()
    app.dependency_overrides.pop(get_evaluation_repository, None)


# ---------------------------------------------------------------------------
# Step 2: End-to-End API Integration Tests
# ---------------------------------------------------------------------------

def test_e2e_complete_evaluation_workflow(isolated_db_repo):
    """Test the complete API workflow from scenario listing to JSON report export."""
    repo, _ = isolated_db_repo

    # 1. List registered scenarios
    scenarios_resp = client.get("/api/v1/scenarios")
    assert scenarios_resp.status_code == 200
    scenarios = scenarios_resp.json()
    assert len(scenarios) == 16
    scenario_ids = [s["scenario_id"] for s in scenarios]
    assert "BENIGN-ORDER-LOOKUP-001" in scenario_ids
    assert "AUTHZ-CROSS-ORDER-001" in scenario_ids

    # 2. Trigger an evaluation run with a subset of scenarios
    selected_ids = ["BENIGN-ORDER-LOOKUP-001", "AUTHZ-CROSS-ORDER-001"]
    payload = {
        "suite_id": "support-agent-security-v1",
        "agent_id": "reference-agent",
        "scenario_ids": selected_ids,
        "options": {
            "continue_on_error": True,
            "record_trace": True,
            "timeout_seconds": 5.0,
        },
    }
    create_resp = client.post("/api/v1/runs", json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()

    run_id = created_data["run_id"]
    report_id = created_data["report_id"]
    assert run_id.startswith("run_")
    assert report_id.startswith("rpt_")
    assert created_data["status"] == "completed"
    assert created_data["total_scenarios"] == 2
    assert "metrics_summary" in created_data

    # 3. Verify run summary retrieval
    get_run_resp = client.get(f"/api/v1/runs/{run_id}")
    assert get_run_resp.status_code == 200
    run_record = get_run_resp.json()
    assert run_record["run_id"] == run_id
    assert run_record["total_scenarios"] == 2

    # 4. Verify per-scenario results retrieval
    results_resp = client.get(f"/api/v1/runs/{run_id}/results")
    assert results_resp.status_code == 200
    results = results_resp.json()
    assert len(results) == 2
    res_scenario_ids = [r["scenario_id"] for r in results]
    assert res_scenario_ids == selected_ids

    # 5. Verify ordered, sanitized execution traces
    trace_resp = client.get(f"/api/v1/runs/{run_id}/trace")
    assert trace_resp.status_code == 200
    trace_events = trace_resp.json()
    assert len(trace_events) > 0

    # 6. Verify single scenario trace filtering and sequential ordering
    benign_trace_resp = client.get(f"/api/v1/runs/{run_id}/trace?scenario_id=BENIGN-ORDER-LOOKUP-001")
    assert benign_trace_resp.status_code == 200
    benign_events = benign_trace_resp.json()
    assert len(benign_events) > 0
    assert all("event_id" in ev for ev in benign_events)
    benign_seqs = [ev["sequence"] for ev in benign_events]
    assert benign_seqs == sorted(benign_seqs)

    # 7. Export and validate complete JSON report
    report_resp = client.get(f"/api/v1/runs/{run_id}/report.json")
    assert report_resp.status_code == 200
    assert report_resp.headers["content-type"] == "application/json"
    assert f'filename="report_{run_id}.json"' in report_resp.headers["content-disposition"]
    export_payload = report_resp.json()
    assert export_payload["schema_version"] == "1.0.0"
    assert export_payload["report"]["run_id"] == run_id
    assert len(export_payload["report"]["scenario_evaluations"]) == 2


def test_file_backed_database_persistence_across_sessions(tmp_path: Path):
    """Confirm a run saved to a file-backed SQLite database remains fully queryable across new connections."""
    db_path = tmp_path / "cross_session_test.db"

    # Session 1: Create and execute a run
    repo1 = SQLiteEvaluationRepository(str(db_path))
    app.dependency_overrides[get_evaluation_repository] = lambda: repo1

    payload = {
        "suite_id": "support-agent-security-v1",
        "agent_id": "reference-agent",
        "scenario_ids": ["BENIGN-ORDER-LOOKUP-001"],
    }
    create_resp = client.post("/api/v1/runs", json=payload)
    assert create_resp.status_code == 201
    run_id = create_resp.json()["run_id"]

    repo1.close()
    app.dependency_overrides.pop(get_evaluation_repository, None)

    # Session 2: Connect a completely new repository instance to the same database file
    repo2 = SQLiteEvaluationRepository(str(db_path))
    app.dependency_overrides[get_evaluation_repository] = lambda: repo2

    # Verify run exists and is identical
    run_record = repo2.get_run_record(run_id)
    assert run_record is not None
    assert run_record.run_id == run_id
    assert run_record.total_scenarios == 1

    report = repo2.get_report(run_id)
    assert report is not None
    assert report.run_id == run_id
    assert len(report.scenario_evaluations) == 1

    trace_events = repo2.get_trace_events(run_id)
    assert len(trace_events) > 0

    # API query through new session
    api_resp = client.get(f"/api/v1/runs/{run_id}/results")
    assert api_resp.status_code == 200
    assert len(api_resp.json()) == 1

    repo2.close()
    app.dependency_overrides.pop(get_evaluation_repository, None)


def test_invalid_requests_and_safe_error_handling(isolated_db_repo):
    """Verify malformed requests return proper HTTP error codes and do not create invalid runs."""
    repo, _ = isolated_db_repo

    # 1. Malformed JSON
    bad_json_resp = client.post(
        "/api/v1/runs",
        content="not a json string",
        headers={"Content-Type": "application/json"},
    )
    assert bad_json_resp.status_code == 422

    # 2. Unsupported suite ID
    suite_resp = client.post(
        "/api/v1/runs",
        json={"suite_id": "unsupported-suite-99", "agent_id": "reference-agent"},
    )
    assert suite_resp.status_code == 400
    assert "Unknown suite ID" in suite_resp.json()["detail"]

    # 3. Unsupported agent ID
    agent_resp = client.post(
        "/api/v1/runs",
        json={"suite_id": "support-agent-security-v1", "agent_id": "unknown-llm"},
    )
    assert agent_resp.status_code == 400
    assert "Unsupported agent ID" in agent_resp.json()["detail"]

    # 4. Empty scenario IDs list
    empty_scenarios_resp = client.post(
        "/api/v1/runs",
        json={"suite_id": "support-agent-security-v1", "agent_id": "reference-agent", "scenario_ids": []},
    )
    assert empty_scenarios_resp.status_code == 400
    assert "empty list" in empty_scenarios_resp.json()["detail"]

    # 5. Non-existent scenario ID
    unknown_sid_resp = client.post(
        "/api/v1/runs",
        json={"suite_id": "support-agent-security-v1", "agent_id": "reference-agent", "scenario_ids": ["SEC-GHOST-001"]},
    )
    assert unknown_sid_resp.status_code == 400
    assert "was not found in the scenario registry" in unknown_sid_resp.json()["detail"]

    # 6. Unknown run ID lookups
    assert client.get("/api/v1/runs/non-existent-run").status_code == 404
    assert client.get("/api/v1/runs/non-existent-run/results").status_code == 404
    assert client.get("/api/v1/runs/non-existent-run/trace").status_code == 404
    assert client.get("/api/v1/runs/non-existent-run/report.json").status_code == 404

    # 7. Confirm no runs were created in database
    runs = repo.list_runs()
    assert len(runs) == 0


# ---------------------------------------------------------------------------
# Step 3: Runner Crash, Exception and Timeout Semantics
# ---------------------------------------------------------------------------

class SlowHangingAgent(BaseAgent):
    """Mock agent that simulates an execution hang or timeout."""

    def __init__(self, delay_seconds: float = 0.5):
        self.delay_seconds = delay_seconds

    def execute(self, request: Any) -> AgentResponse:
        time.sleep(self.delay_seconds)
        return AgentResponse(
            status=ExecutionStatus.SUCCESS,
            message="Completed after delay",
            data={},
            trace=ExecutionTrace(),
        )


class CrashingAgent(BaseAgent):
    """Mock agent that raises an unexpected unhandled exception."""

    def execute(self, request: Any) -> AgentResponse:
        raise RuntimeError("Simulated catastrophic agent crash!")


def test_real_runner_timeout_marks_scenario_error_never_pass():
    """Verify that a real execution timeout marks scenario as ERROR and is never counted as a security PASS."""
    slow_agent = SlowHangingAgent(delay_seconds=0.3)
    # Configure runner with 0.05s timeout
    runner = ScenarioRunner(agent=slow_agent, timeout_seconds=0.05)

    scenario = SCENARIO_LIBRARY[0]
    result = runner.run_scenario(scenario)

    assert result.execution_status == ScenarioExecutionStatus.ERROR
    assert result.actual_status == ExecutionStatus.ERROR
    assert result.agent_response is None
    assert "timed out after 0.05s" in (result.error_message or "")
    assert not result.matches_expected_status

    # Evaluate with security engine
    evaluator = get_default_evaluator()
    evaluation = evaluator.evaluate_scenario(result, scenario_definition=scenario)

    assert evaluation.outcome == EvaluationOutcome.ERROR
    assert not evaluation.violation_prevented
    assert "Execution error" in evaluation.explanation

    # Run in suite and evaluate metrics
    suite_res = SuiteExecutionResult(run_id="test_timeout_run", results=[result])
    report = evaluator.evaluate_suite(suite_res)

    assert report.overall_outcome == EvaluationOutcome.ERROR
    assert report.summary_counts.passed_count == 0
    assert report.summary_counts.error_count == 1
    assert report.metrics.overall_pass_rate.value == 0.0
    assert report.metrics.unauthorized_prevention_rate.numerator == 0


def test_runner_unexpected_exception_fails_closed():
    """Verify that when an agent raises an unhandled exception, runner fails closed with ERROR."""
    crashing_agent = CrashingAgent()
    runner = ScenarioRunner(agent=crashing_agent)

    scenario = SCENARIO_LIBRARY[0]
    result = runner.run_scenario(scenario)

    assert result.execution_status == ScenarioExecutionStatus.ERROR
    assert result.actual_status == ExecutionStatus.ERROR
    assert "Simulated catastrophic agent crash" in (result.error_message or "")

    evaluator = get_default_evaluator()
    evaluation = evaluator.evaluate_scenario(result, scenario_definition=scenario)
    assert evaluation.outcome == EvaluationOutcome.ERROR

    report = evaluator.evaluate_suite(SuiteExecutionResult(run_id="test_crash_run", results=[result]))
    assert report.overall_outcome == EvaluationOutcome.ERROR
    assert report.summary_counts.passed_count == 0
    assert report.summary_counts.error_count == 1


def test_runner_failure_before_all_scenarios_complete():
    """Verify that if runner crashes midway through batch, remaining scenarios are captured as INCOMPLETE/NOT_RUN."""
    runner = ScenarioRunner()
    scenarios = SCENARIO_LIBRARY[:3]

    # Patch run_scenario to fail on the second scenario
    orig_run_scenario = runner.run_scenario

    def mock_run_scenario(sc, timeout_seconds=None):
        if sc.scenario_id == scenarios[1].scenario_id:
            raise RuntimeError("Fatal hardware/process failure on scenario 2")
        return orig_run_scenario(sc, timeout_seconds=timeout_seconds)

    runner.run_scenario = mock_run_scenario

    suite_result = runner.run_scenarios(scenarios, run_id="run_interrupted")
    assert len(suite_result.results) == 3

    # Scenario 0 completed
    assert suite_result.results[0].execution_status == ScenarioExecutionStatus.COMPLETED
    # Scenario 1 crashed with ERROR
    assert suite_result.results[1].execution_status == ScenarioExecutionStatus.ERROR
    # Scenario 2 was skipped with INCOMPLETE
    assert suite_result.results[2].execution_status == ScenarioExecutionStatus.INCOMPLETE
    assert suite_result.results[2].agent_response is None

    # Evaluate suite
    evaluator = get_default_evaluator()
    report = evaluator.evaluate_suite(suite_result)

    assert report.summary_counts.total_scenarios == 3
    assert report.summary_counts.error_count == 1
    assert report.summary_counts.not_run_count == 1
    assert report.scenario_evaluations[2].outcome == EvaluationOutcome.NOT_RUN
    assert report.overall_outcome in (EvaluationOutcome.ERROR, EvaluationOutcome.FAIL)
    # The incomplete scenario must not be counted as PASS
    assert report.summary_counts.passed_count <= 1


def test_evaluator_failure_returns_safe_500_response(isolated_db_repo):
    """Verify an unexpected exception in the evaluation engine returns a safe 500 without leaking stack traces."""
    with patch("app.api.routes_runs.get_default_evaluator") as mock_get_evaluator:
        mock_eval = MagicMock()
        mock_eval.evaluate_suite.side_effect = RuntimeError("Internal math failure in metrics engine!")
        mock_get_evaluator.return_value = mock_eval

        payload = {
            "suite_id": "support-agent-security-v1",
            "agent_id": "reference-agent",
            "scenario_ids": ["BENIGN-ORDER-LOOKUP-001"],
        }
        resp = client.post("/api/v1/runs", json=payload)
        assert resp.status_code == 500
        error_detail = resp.json()["detail"]
        # Safe message, not raw exception or stack trace
        assert error_detail == "Security evaluation failed due to an internal engine error."
        assert "math failure" not in error_detail


def test_database_write_failure_rolls_back_atomic_transaction(tmp_path: Path):
    """Verify that a storage persistence failure triggers transaction rollback without leaving orphaned records."""
    db_file = tmp_path / "rollback_test.db"
    repo = SQLiteEvaluationRepository(str(db_file))
    app.dependency_overrides[get_evaluation_repository] = lambda: repo

    # Patch cursor.execute inside repository to fail after inserting into 'runs'
    orig_save_report = repo.save_report

    def failing_save_report(report, suite_result=None, allow_overwrite=False):
        # We simulate a database crash during the multi-table insert
        try:
            with repo.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO runs (run_id, report_id, suite_id, suite_version, evaluator_version, status, overall_outcome, started_at, completed_at, created_at, total_scenarios, passed_count, failed_count, error_count, not_run_count, metrics_summary, report_payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("run_corrupt_test", "rpt_test", "suite_v1", 1, "1.0.0", "completed", "pass", "2026-01-01", "2026-01-01", "2026-01-01", 1, 1, 0, 0, 0, "{}", "{}"),
                )
                # Raise exception before child tables are populated
                raise sqlite3.OperationalError("Simulated disk I/O error or constraint failure!")
        except Exception as exc:
            raise StorageError(f"Simulated write failure: {exc}") from exc

    repo.save_report = failing_save_report

    payload = {
        "suite_id": "support-agent-security-v1",
        "agent_id": "reference-agent",
        "scenario_ids": ["BENIGN-ORDER-LOOKUP-001"],
    }
    resp = client.post("/api/v1/runs", json=payload)
    assert resp.status_code == 500
    assert resp.json()["detail"] == "Failed to persist evaluation report to storage."

    # Verify that 'run_corrupt_test' was rolled back and is NOT present in database
    with repo.db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM runs WHERE run_id = 'run_corrupt_test'")
        count = cursor.fetchone()[0]
        assert count == 0

    repo.close()
    app.dependency_overrides.pop(get_evaluation_repository, None)


def test_distinct_outcomes_pass_fail_error_not_run():
    """Verify PASS, FAIL, ERROR, and NOT_RUN remain completely distinct in evaluation and metrics."""
    now = datetime.now(timezone.utc).isoformat()
    evaluations = [
        ScenarioEvaluation(
            scenario_id="S-PASS",
            scenario_name="Pass Scenario",
            category=ScenarioCategory.BENIGN_TASK,
            risk_level=RiskLevel.LOW,
            outcome=EvaluationOutcome.PASS,
            findings=[],
            execution_status=ScenarioExecutionStatus.COMPLETED,
            actual_status=ExecutionStatus.SUCCESS,
            expected_status=ExecutionStatus.SUCCESS,
            attempt_detected=False,
            violation_prevented=False,
            data_exposed=False,
            explanation="Passed",
            evaluated_at=now,
        ),
        ScenarioEvaluation(
            scenario_id="S-FAIL",
            scenario_name="Fail Scenario",
            category=ScenarioCategory.UNAUTHORIZED_ACCESS,
            risk_level=RiskLevel.HIGH,
            outcome=EvaluationOutcome.FAIL,
            findings=[],
            execution_status=ScenarioExecutionStatus.COMPLETED,
            actual_status=ExecutionStatus.SUCCESS,
            expected_status=ExecutionStatus.DENIED,
            attempt_detected=True,
            violation_prevented=False,
            data_exposed=True,
            explanation="Failed",
            evaluated_at=now,
        ),
        ScenarioEvaluation(
            scenario_id="S-ERROR",
            scenario_name="Error Scenario",
            category=ScenarioCategory.DIRECT_INJECTION,
            risk_level=RiskLevel.HIGH,
            outcome=EvaluationOutcome.ERROR,
            findings=[],
            execution_status=ScenarioExecutionStatus.ERROR,
            actual_status=ExecutionStatus.ERROR,
            expected_status=ExecutionStatus.DENIED,
            attempt_detected=True,
            violation_prevented=False,
            data_exposed=False,
            explanation="Error",
            evaluated_at=now,
        ),
        ScenarioEvaluation(
            scenario_id="S-NOTRUN",
            scenario_name="Not Run Scenario",
            category=ScenarioCategory.BENIGN_TASK,
            risk_level=RiskLevel.LOW,
            outcome=EvaluationOutcome.NOT_RUN,
            findings=[],
            execution_status=ScenarioExecutionStatus.INCOMPLETE,
            actual_status=None,
            expected_status=ExecutionStatus.SUCCESS,
            attempt_detected=False,
            violation_prevented=False,
            data_exposed=False,
            explanation="Incomplete",
            evaluated_at=now,
        ),
    ]

    counts = MetricsCalculator.calculate_summary_counts(evaluations)
    assert counts.total_scenarios == 4
    assert counts.passed_count == 1
    assert counts.failed_count == 1
    assert counts.error_count == 1
    assert counts.not_run_count == 1

    metrics = MetricsCalculator.calculate_metrics(evaluations)
    # Overall pass rate is 1/4 = 25%
    assert metrics.overall_pass_rate.value == 0.25
    # Run completion rate is 2/4 = 50% (only PASS and FAIL completed)
    assert metrics.run_completion_rate.value == 0.50
    # S-ERROR and S-NOTRUN were never counted as PASS
    assert metrics.overall_pass_rate.numerator == 1
