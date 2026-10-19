"""Comprehensive unit tests for SQLite persistence of evaluation runs and reports."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import pytest

from app.evaluator import get_default_evaluator
from app.models.event import ExecutionStatus, TraceEvent, TraceEventType
from app.models.finding import (
    CategoryMetric,
    EvaluationMetrics,
    EvaluationOutcome,
    EvaluationReport,
    Finding,
    MetricValue,
    RiskMetric,
    ScenarioEvaluation,
    SummaryCounts,
)
from app.models.run import EvaluationRunRecord, RunStatus
from app.models.scenario import (
    ExpectedBehavior,
    RiskLevel,
    ScenarioCategory,
    ScenarioExecutionStatus,
    ScenarioResult,
    SuiteExecutionResult,
)
from app.scenarios.runner import ScenarioRunner
from app.storage import (
    CURRENT_SCHEMA_VERSION,
    DatabaseManager,
    DuplicateRunError,
    SQLiteEvaluationRepository,
    StorageError,
    get_current_schema_version,
)


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """Fixture returning an isolated temporary SQLite database file path."""
    return str(tmp_path / "test_agentshield.db")


@pytest.fixture
def repo(temp_db_path: str) -> SQLiteEvaluationRepository:
    """Fixture providing an initialized SQLiteEvaluationRepository with a temporary database."""
    repository = SQLiteEvaluationRepository(temp_db_path)
    yield repository
    repository.close()


@pytest.fixture
def canonical_report_and_suite():
    """Generate a canonical EvaluationReport and SuiteExecutionResult using the test runner."""
    runner = ScenarioRunner()
    suite_res = runner.run_all()
    evaluator = get_default_evaluator()
    report = evaluator.evaluate_suite(suite_res)
    return report, suite_res


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


def _make_sample_report(
    run_id: str,
    outcome: EvaluationOutcome = EvaluationOutcome.PASS,
    total: int = 1,
    passed: int = 1,
    failed: int = 0,
    error: int = 0,
    not_run: int = 0,
) -> EvaluationReport:
    """Helper to construct a deterministic, valid EvaluationReport with custom outcome."""
    now = datetime.now(timezone.utc).isoformat()
    sc_eval = ScenarioEvaluation(
        scenario_id="SCENARIO-001",
        scenario_name="Test Scenario",
        category=ScenarioCategory.UNAUTHORIZED_ACCESS,
        risk_level=RiskLevel.HIGH,
        outcome=outcome,
        findings=[
            Finding(
                finding_id="fnd_001",
                scenario_id="SCENARIO-001",
                rule_id="RULE-AUTHZ-001",
                rule_name="Tool Authorization",
                outcome=outcome,
                severity=RiskLevel.HIGH,
                message=f"Evaluation outcome was {outcome.value}",
                evidence={"test_key": "test_value", "outcome": outcome.value},
                timestamp=now,
            )
        ],
        execution_status=ScenarioExecutionStatus.COMPLETED if outcome != EvaluationOutcome.ERROR else ScenarioExecutionStatus.ERROR,
        actual_status=ExecutionStatus.DENIED if outcome == EvaluationOutcome.PASS else ExecutionStatus.SUCCESS,
        expected_status=ExecutionStatus.DENIED,
        attempt_detected=True,
        violation_prevented=(outcome == EvaluationOutcome.PASS),
        data_exposed=False,
        explanation=f"Sample explanation for {outcome.value}",
        evaluated_at=now,
    )
    metric_val = _make_metric_value(passed, total)
    metrics = EvaluationMetrics(
        overall_pass_rate=metric_val,
        attack_success_rate=_make_metric_value(failed, total, "Attack Success Rate"),
        unauthorized_prevention_rate=_make_metric_value(passed, total, "Unauthorized Prevention Rate"),
        sensitive_data_exposure_rate=_make_metric_value(0, total, "Data Exposure Rate"),
        benign_task_success_rate=_make_metric_value(passed, total, "Benign Task Success Rate"),
        policy_enforcement_failure_rate=_make_metric_value(failed, total, "Policy Failure Rate"),
        run_completion_rate=_make_metric_value(total - not_run, total, "Run Completion Rate"),
        security_score=metric_val,
    )
    return EvaluationReport(
        report_id=f"rpt_{run_id}",
        run_id=run_id,
        evaluator_version="1.0.0",
        suite_version=1,
        started_at=now,
        completed_at=now,
        overall_outcome=outcome,
        summary_counts=SummaryCounts(
            total_scenarios=total,
            passed_count=passed,
            failed_count=failed,
            error_count=error,
            not_run_count=not_run,
        ),
        metrics=metrics,
        scenario_evaluations=[sc_eval],
        findings=sc_eval.findings,
    )


# ==============================================================================
# 1. Database Initialization and Schema Creation
# ==============================================================================

def test_database_initialization_and_schema(temp_db_path: str):
    """Verify tables, indices, and schema version are correctly created."""
    db = DatabaseManager(temp_db_path)
    db.initialize()

    with db.connection() as conn:
        version = get_current_schema_version(conn)
        assert version == CURRENT_SCHEMA_VERSION

        # Verify all expected tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row["name"] for row in cursor.fetchall()}
        expected_tables = {
            "schema_version",
            "runs",
            "scenario_evaluations",
            "findings",
            "metric_snapshots",
            "trace_events",
        }
        assert expected_tables.issubset(tables)

    db.close()


def test_schema_initialization_is_idempotent(temp_db_path: str):
    """Verify running schema initialization multiple times does not destroy data or error."""
    db = DatabaseManager(temp_db_path)
    db.initialize()
    # Re-initialize multiple times
    db.initialize()
    db.initialize()

    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM schema_version")
        count = cursor.fetchone()[0]
        assert count == 1  # Only one record for version 1
    db.close()


def test_database_manager_auto_creates_parent_directories(tmp_path: Path):
    """Verify DatabaseManager automatically creates nested directories for db path."""
    nested_path = tmp_path / "deeply" / "nested" / "dir" / "agentshield.db"
    assert not nested_path.parent.exists()

    db = DatabaseManager(nested_path)
    db.initialize()
    assert nested_path.exists()
    db.close()


# ==============================================================================
# 2. Saving and Retrieving Evaluation Reports
# ==============================================================================

def test_save_and_retrieve_evaluation_report(repo: SQLiteEvaluationRepository, canonical_report_and_suite):
    """Verify saving a complete EvaluationReport and retrieving it by run_id."""
    report, suite_res = canonical_report_and_suite

    # Save report with trace events
    repo.save_report(report, suite_result=suite_res)

    # Verify run exists
    assert repo.run_exists(report.run_id) is True

    # Retrieve report
    retrieved = repo.get_report(report.run_id)
    assert retrieved is not None
    assert retrieved.run_id == report.run_id
    assert retrieved.report_id == report.report_id
    assert retrieved.overall_outcome == report.overall_outcome
    assert retrieved.evaluator_version == report.evaluator_version
    assert retrieved.suite_version == report.suite_version
    assert retrieved.started_at == report.started_at
    assert retrieved.completed_at == report.completed_at
    assert retrieved.limitation_statement == report.limitation_statement

    # Summary counts
    assert retrieved.summary_counts.total_scenarios == report.summary_counts.total_scenarios
    assert retrieved.summary_counts.passed_count == report.summary_counts.passed_count
    assert retrieved.summary_counts.failed_count == report.summary_counts.failed_count
    assert retrieved.summary_counts.error_count == report.summary_counts.error_count
    assert retrieved.summary_counts.not_run_count == report.summary_counts.not_run_count

    # Scenario evaluations and findings
    assert len(retrieved.scenario_evaluations) == len(report.scenario_evaluations)
    assert len(retrieved.findings) == len(report.findings)


def test_save_and_retrieve_run_record(repo: SQLiteEvaluationRepository, canonical_report_and_suite):
    """Verify retrieving run summary record matches report metadata."""
    report, _ = canonical_report_and_suite
    repo.save_report(report)

    record = repo.get_run_record(report.run_id)
    assert record is not None
    assert isinstance(record, EvaluationRunRecord)
    assert record.run_id == report.run_id
    assert record.report_id == report.report_id
    assert record.overall_outcome == report.overall_outcome
    assert record.total_scenarios == report.summary_counts.total_scenarios
    assert record.passed_count == report.summary_counts.passed_count
    assert "overall_pass_rate" in record.metrics_summary


# ==============================================================================
# 3. Round-Trip Serialization of Metrics, Findings, Scenarios, and Traces
# ==============================================================================

def test_round_trip_metrics_precision(repo: SQLiteEvaluationRepository, canonical_report_and_suite):
    """Verify metrics numerators, denominators, and values preserve exact precision."""
    report, _ = canonical_report_and_suite
    repo.save_report(report)

    retrieved = repo.get_report(report.run_id)
    assert retrieved is not None

    orig_m = report.metrics
    ret_m = retrieved.metrics

    assert ret_m.overall_pass_rate.numerator == orig_m.overall_pass_rate.numerator
    assert ret_m.overall_pass_rate.denominator == orig_m.overall_pass_rate.denominator
    assert ret_m.overall_pass_rate.value == orig_m.overall_pass_rate.value
    assert ret_m.overall_pass_rate.display_value == orig_m.overall_pass_rate.display_value

    assert ret_m.security_score.value == orig_m.security_score.value
    assert ret_m.unauthorized_prevention_rate.value == orig_m.unauthorized_prevention_rate.value


def test_round_trip_findings_and_evidence(repo: SQLiteEvaluationRepository, canonical_report_and_suite):
    """Verify findings and sanitized evidence dictionaries preserve exact structure."""
    report, _ = canonical_report_and_suite
    repo.save_report(report)

    findings = repo.get_findings(report.run_id)
    assert len(findings) == len(report.findings)

    orig_by_id = {f.finding_id: f for f in report.findings}
    for ret_f in findings:
        orig_f = orig_by_id[ret_f.finding_id]
        assert ret_f.scenario_id == orig_f.scenario_id
        assert ret_f.rule_id == orig_f.rule_id
        assert ret_f.outcome == orig_f.outcome
        assert ret_f.severity == orig_f.severity
        assert ret_f.message == orig_f.message
        assert ret_f.evidence == orig_f.evidence


def test_round_trip_scenario_evaluations(repo: SQLiteEvaluationRepository, canonical_report_and_suite):
    """Verify scenario evaluation flags (attempt_detected, violation_prevented, data_exposed)."""
    report, _ = canonical_report_and_suite
    repo.save_report(report)

    scenarios = repo.get_scenario_evaluations(report.run_id)
    assert len(scenarios) == len(report.scenario_evaluations)

    orig_map = {se.scenario_id: se for se in report.scenario_evaluations}
    for ret_se in scenarios:
        orig_se = orig_map[ret_se.scenario_id]
        assert ret_se.outcome == orig_se.outcome
        assert ret_se.attempt_detected == orig_se.attempt_detected
        assert ret_se.violation_prevented == orig_se.violation_prevented
        assert ret_se.data_exposed == orig_se.data_exposed
        assert ret_se.actual_status == orig_se.actual_status
        assert ret_se.expected_status == orig_se.expected_status
        assert len(ret_se.findings) == len(orig_se.findings)


def test_round_trip_trace_events(repo: SQLiteEvaluationRepository, canonical_report_and_suite):
    """Verify execution traces are persisted with sequence ordering and sanitized payloads."""
    report, suite_res = canonical_report_and_suite
    repo.save_report(report, suite_result=suite_res)

    traces = repo.get_trace_events(report.run_id)
    assert len(traces) > 0

    # Verify deterministic sequence ordering per scenario
    scenario_ids = {res.scenario_id for res in suite_res.results}
    for sc_id in scenario_ids:
        sc_traces = repo.get_trace_events(report.run_id, scenario_id=sc_id)
        sequences = [t.sequence for t in sc_traces]
        assert sequences == sorted(sequences)
        assert len(sequences) == len(set(sequences))  # All sequences unique per scenario


# ==============================================================================
# 4. Listing Runs and Deterministic Ordering
# ==============================================================================

def test_list_runs_predictable_order(repo: SQLiteEvaluationRepository):
    """Verify list_runs returns records ordered by newest first (created_at DESC)."""
    r1 = _make_sample_report("run_001", outcome=EvaluationOutcome.PASS)
    r2 = _make_sample_report("run_002", outcome=EvaluationOutcome.FAIL)
    r3 = _make_sample_report("run_003", outcome=EvaluationOutcome.ERROR)

    repo.save_report(r1)
    repo.save_report(r2)
    repo.save_report(r3)

    listed = repo.list_runs(limit=10)
    assert len(listed) == 3

    # Newest inserted should be first
    run_ids = [rec.run_id for rec in listed]
    assert run_ids == ["run_003", "run_002", "run_001"]


def test_list_runs_pagination(repo: SQLiteEvaluationRepository):
    """Verify limit and offset pagination."""
    for i in range(5):
        repo.save_report(_make_sample_report(f"run_page_{i:02d}"))

    page1 = repo.list_runs(limit=2, offset=0)
    page2 = repo.list_runs(limit=2, offset=2)
    page3 = repo.list_runs(limit=2, offset=4)

    assert len(page1) == 2
    assert len(page2) == 2
    assert len(page3) == 1

    # Verify no overlaps
    all_ids = [r.run_id for r in page1] + [r.run_id for r in page2] + [r.run_id for r in page3]
    assert len(all_ids) == 5
    assert len(set(all_ids)) == 5


# ==============================================================================
# 5. Handling Unknown Run IDs Cleanly
# ==============================================================================

def test_handling_unknown_run_ids(repo: SQLiteEvaluationRepository):
    """Verify repository returns None or empty results for non-existent run IDs without raising errors."""
    assert repo.get_report("unknown-run-id") is None
    assert repo.get_run_record("unknown-run-id") is None
    assert repo.run_exists("unknown-run-id") is False
    assert repo.get_trace_events("unknown-run-id") == []
    assert repo.get_findings("unknown-run-id") == []
    assert repo.get_scenario_evaluations("unknown-run-id") == []
    assert repo.delete_run("unknown-run-id") is False

    # Empty string or whitespace
    assert repo.get_report("") is None
    assert repo.get_report("   ") is None
    assert repo.run_exists("") is False


# ==============================================================================
# 6. Duplicate Run IDs and Overwrite Prevention
# ==============================================================================

def test_duplicate_run_id_prevents_overwrite_by_default(repo: SQLiteEvaluationRepository):
    """Verify DuplicateRunError is raised if a run ID already exists and allow_overwrite=False."""
    r1 = _make_sample_report("run_duplicate_test", outcome=EvaluationOutcome.PASS)
    repo.save_report(r1)

    r1_dup = _make_sample_report("run_duplicate_test", outcome=EvaluationOutcome.FAIL)
    with pytest.raises(DuplicateRunError) as exc_info:
        repo.save_report(r1_dup, allow_overwrite=False)

    assert "already exists in storage" in str(exc_info.value)

    # Verify original report was NOT modified
    saved = repo.get_report("run_duplicate_test")
    assert saved is not None
    assert saved.overall_outcome == EvaluationOutcome.PASS


def test_duplicate_run_id_allows_explicit_overwrite(repo: SQLiteEvaluationRepository):
    """Verify allow_overwrite=True replaces existing run and child records safely."""
    r1 = _make_sample_report("run_overwrite_test", outcome=EvaluationOutcome.PASS)
    repo.save_report(r1)

    r1_updated = _make_sample_report("run_overwrite_test", outcome=EvaluationOutcome.FAIL)
    repo.save_report(r1_updated, allow_overwrite=True)

    saved = repo.get_report("run_overwrite_test")
    assert saved is not None
    assert saved.overall_outcome == EvaluationOutcome.FAIL


# ==============================================================================
# 7. Persistence of FAIL, ERROR, and NOT_RUN Outcomes
# ==============================================================================

@pytest.mark.parametrize("outcome", [
    EvaluationOutcome.PASS,
    EvaluationOutcome.FAIL,
    EvaluationOutcome.ERROR,
    EvaluationOutcome.NOT_RUN,
])
def test_persistence_preserves_all_evaluation_outcomes(repo: SQLiteEvaluationRepository, outcome: EvaluationOutcome):
    """Verify PASS, FAIL, ERROR, and NOT_RUN outcomes are stored and retrieved without conversion."""
    run_id = f"run_outcome_{outcome.value}"
    report = _make_sample_report(run_id, outcome=outcome)

    repo.save_report(report)
    retrieved = repo.get_report(run_id)

    assert retrieved is not None
    assert retrieved.overall_outcome == outcome
    assert retrieved.scenario_evaluations[0].outcome == outcome
    assert retrieved.findings[0].outcome == outcome

    record = repo.get_run_record(run_id)
    assert record is not None
    assert record.overall_outcome == outcome


# ==============================================================================
# 8. Transaction Rollback on Failure
# ==============================================================================

def test_transaction_rollback_on_write_error(repo: SQLiteEvaluationRepository):
    """Verify transaction rolls back cleanly if database operation fails midway."""
    # Attempting to save a report with invalid data or broken connection
    with pytest.raises(StorageError):
        repo.save_report(None)  # type: ignore

    # Verify no corrupt or empty runs were inserted
    assert len(repo.list_runs()) == 0


def test_transaction_rollback_prevents_partial_save(repo: SQLiteEvaluationRepository, monkeypatch):
    """Verify that an exception during child rows insertion rolls back the entire run."""
    report = _make_sample_report("run_rollback_test")

    orig_transaction = repo.db.transaction

    from contextlib import contextmanager

    @contextmanager
    def failing_transaction():
        with orig_transaction() as real_conn:
            class FailingCursor:
                def __init__(self, cur):
                    self._cur = cur

                def __getattr__(self, name):
                    return getattr(self._cur, name)

                def execute(self, sql, params=()):
                    if "INSERT INTO findings" in sql:
                        raise sqlite3.OperationalError("Simulated write failure")
                    return self._cur.execute(sql, params)

                def fetchone(self):
                    return self._cur.fetchone()

                def fetchall(self):
                    return self._cur.fetchall()

            class ConnectionProxy:
                def __init__(self, conn):
                    self._conn = conn

                def __getattr__(self, name):
                    return getattr(self._conn, name)

                def cursor(self):
                    return FailingCursor(self._conn.cursor())

            yield ConnectionProxy(real_conn)

    monkeypatch.setattr(repo.db, "transaction", failing_transaction)

    with pytest.raises(StorageError) as exc_info:
        repo.save_report(report)

    assert "Simulated write failure" in str(exc_info.value) or "Database error" in str(exc_info.value)

    # After rollback, the run MUST NOT exist in runs table
    assert repo.run_exists("run_rollback_test") is False
    assert repo.get_report("run_rollback_test") is None


# ==============================================================================
# 9. Reopening Database and Retrieving Data Across Connections
# ==============================================================================

def test_reopening_database_file_preserves_all_data(temp_db_path: str, canonical_report_and_suite):
    """Verify closing database and opening a new repository connection retrieves identical data."""
    report, suite_res = canonical_report_and_suite

    # Session 1: Save data and close
    repo1 = SQLiteEvaluationRepository(temp_db_path)
    repo1.save_report(report, suite_result=suite_res)
    repo1.close()

    # Session 2: Fresh repository instance connecting to same database file
    repo2 = SQLiteEvaluationRepository(temp_db_path)
    retrieved = repo2.get_report(report.run_id)

    assert retrieved is not None
    assert retrieved.run_id == report.run_id
    assert retrieved.overall_outcome == report.overall_outcome
    assert len(retrieved.scenario_evaluations) == len(report.scenario_evaluations)

    traces = repo2.get_trace_events(report.run_id)
    assert len(traces) > 0

    findings = repo2.get_findings(report.run_id)
    assert len(findings) == len(report.findings)

    repo2.close()


# ==============================================================================
# 10. Deletion and Cascading Records
# ==============================================================================

def test_delete_run_cascades_all_child_records(repo: SQLiteEvaluationRepository, canonical_report_and_suite):
    """Verify deleting a run cascades and removes scenario evaluations, findings, metrics, and traces."""
    report, suite_res = canonical_report_and_suite
    repo.save_report(report, suite_result=suite_res)

    assert repo.run_exists(report.run_id) is True
    assert len(repo.get_trace_events(report.run_id)) > 0
    assert len(repo.get_findings(report.run_id)) > 0
    assert len(repo.get_scenario_evaluations(report.run_id)) > 0

    deleted = repo.delete_run(report.run_id)
    assert deleted is True

    # Verify everything is gone
    assert repo.run_exists(report.run_id) is False
    assert repo.get_report(report.run_id) is None
    assert repo.get_trace_events(report.run_id) == []
    assert repo.get_findings(report.run_id) == []
    assert repo.get_scenario_evaluations(report.run_id) == []
