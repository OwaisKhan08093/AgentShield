"""Repository interface and SQLite implementation for evaluation runs and reports."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Union

from app.models.event import ExecutionStatus, TraceEvent, TraceEventType
from app.models.finding import (
    EvaluationOutcome,
    EvaluationReport,
    Finding,
    ScenarioEvaluation,
)
from app.models.run import EvaluationRunRecord
from app.models.scenario import (
    RiskLevel,
    ScenarioCategory,
    ScenarioExecutionStatus,
    SuiteExecutionResult,
)
from app.storage.database import DatabaseManager
from app.storage.exceptions import DuplicateRunError, StorageError

logger = logging.getLogger(__name__)


class EvaluationRepository(ABC):
    """Abstract interface defining persistence operations for evaluation runs."""

    @abstractmethod
    def save_report(
        self,
        report: EvaluationReport,
        suite_result: Optional[SuiteExecutionResult] = None,
        allow_overwrite: bool = False,
    ) -> None:
        """Persist a completed evaluation report and optional trace evidence."""

    @abstractmethod
    def get_report(self, run_id: str) -> Optional[EvaluationReport]:
        """Retrieve an evaluation report by run_id, or None if not found."""

    @abstractmethod
    def list_runs(self, limit: int = 50, offset: int = 0) -> List[EvaluationRunRecord]:
        """List summary records of recent evaluation runs in reverse-chronological order."""

    @abstractmethod
    def run_exists(self, run_id: str) -> bool:
        """Check whether a run with the given run_id exists in storage."""

    @abstractmethod
    def delete_run(self, run_id: str) -> bool:
        """Delete an evaluation run and its associated records. Returns True if deleted."""

    @abstractmethod
    def get_trace_events(
        self, run_id: str, scenario_id: Optional[str] = None
    ) -> List[TraceEvent]:
        """Retrieve sanitized trace events for an evaluation run."""

    @abstractmethod
    def get_findings(
        self, run_id: str, scenario_id: Optional[str] = None
    ) -> List[Finding]:
        """Retrieve security findings for an evaluation run."""

    @abstractmethod
    def get_scenario_evaluations(self, run_id: str) -> List[ScenarioEvaluation]:
        """Retrieve scenario evaluation results for an evaluation run."""


class SQLiteEvaluationRepository(EvaluationRepository):
    """SQLite-backed implementation of EvaluationRepository."""

    def __init__(
        self,
        database: Union[str, Path, DatabaseManager] = "agentshield.db",
        auto_initialize: bool = True,
    ):
        """Initialize repository with a database path or DatabaseManager.

        Args:
            database: File path, ':memory:', or pre-configured DatabaseManager.
            auto_initialize: If True, automatically creates schema tables if missing.
        """
        if isinstance(database, DatabaseManager):
            self.db = database
        else:
            self.db = DatabaseManager(database)

        if auto_initialize:
            self.db.initialize()

    def save_report(
        self,
        report: EvaluationReport,
        suite_result: Optional[SuiteExecutionResult] = None,
        allow_overwrite: bool = False,
    ) -> None:
        """Save a completed EvaluationReport and optional suite trace evidence.

        Args:
            report: Validated EvaluationReport to persist.
            suite_result: Optional SuiteExecutionResult from runner containing sanitized traces.
            allow_overwrite: If False, raises DuplicateRunError when run_id already exists.

        Raises:
            StorageError: If report is invalid or database operations fail.
            DuplicateRunError: If run_id already exists and allow_overwrite is False.
        """
        if not isinstance(report, EvaluationReport):
            raise StorageError(f"Expected EvaluationReport instance, got {type(report).__name__}")

        run_id = report.run_id
        if not run_id or not run_id.strip():
            raise StorageError("Cannot save evaluation report with empty run_id.")

        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Check if run already exists
                cursor.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,))
                exists = cursor.fetchone() is not None

                if exists:
                    if not allow_overwrite:
                        raise DuplicateRunError(
                            f"Evaluation run '{run_id}' already exists in storage. Set allow_overwrite=True to replace."
                        )
                    # Delete existing run; cascading foreign keys remove child records
                    cursor.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))

                created_at = datetime.now(timezone.utc).isoformat()

                # Build summary metrics dictionary
                metrics_summary = {
                    "overall_pass_rate": report.metrics.overall_pass_rate.model_dump(),
                    "security_score": report.metrics.security_score.model_dump(),
                    "attack_success_rate": report.metrics.attack_success_rate.model_dump(),
                    "unauthorized_prevention_rate": report.metrics.unauthorized_prevention_rate.model_dump(),
                    "sensitive_data_exposure_rate": report.metrics.sensitive_data_exposure_rate.model_dump(),
                    "benign_task_success_rate": report.metrics.benign_task_success_rate.model_dump(),
                }

                # 1. Insert run record
                cursor.execute(
                    """
                    INSERT INTO runs (
                        run_id, report_id, suite_id, suite_version, evaluator_version,
                        status, overall_outcome, started_at, completed_at, created_at,
                        total_scenarios, passed_count, failed_count, error_count, not_run_count,
                        metrics_summary, report_payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        report.report_id,
                        f"suite_v{report.suite_version}",
                        report.suite_version,
                        report.evaluator_version,
                        report.overall_outcome.value,
                        report.overall_outcome.value,
                        report.started_at,
                        report.completed_at,
                        created_at,
                        report.summary_counts.total_scenarios,
                        report.summary_counts.passed_count,
                        report.summary_counts.failed_count,
                        report.summary_counts.error_count,
                        report.summary_counts.not_run_count,
                        json.dumps(metrics_summary),
                        report.model_dump_json(),
                    ),
                )

                # 2. Insert scenario evaluations
                for se in report.scenario_evaluations:
                    cursor.execute(
                        """
                        INSERT INTO scenario_evaluations (
                            run_id, scenario_id, scenario_name, category, risk_level,
                            outcome, execution_status, actual_status, expected_status,
                            attempt_detected, violation_prevented, data_exposed,
                            explanation, evaluated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run_id,
                            se.scenario_id,
                            se.scenario_name,
                            se.category.value if hasattr(se.category, "value") else str(se.category),
                            se.risk_level.value if hasattr(se.risk_level, "value") else str(se.risk_level),
                            se.outcome.value if hasattr(se.outcome, "value") else str(se.outcome),
                            se.execution_status.value if hasattr(se.execution_status, "value") else str(se.execution_status),
                            se.actual_status.value if (se.actual_status and hasattr(se.actual_status, "value")) else (se.actual_status or None),
                            se.expected_status.value if hasattr(se.expected_status, "value") else str(se.expected_status),
                            1 if se.attempt_detected else 0,
                            1 if se.violation_prevented else 0,
                            1 if se.data_exposed else 0,
                            se.explanation,
                            se.evaluated_at,
                        ),
                    )

                # 3. Insert individual findings
                for f in report.findings:
                    cursor.execute(
                        """
                        INSERT INTO findings (
                            finding_id, run_id, scenario_id, rule_id, rule_name,
                            outcome, severity, message, evidence, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f.finding_id,
                            run_id,
                            f.scenario_id,
                            f.rule_id,
                            f.rule_name,
                            f.outcome.value if hasattr(f.outcome, "value") else str(f.outcome),
                            f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                            f.message,
                            json.dumps(f.evidence),
                            f.timestamp,
                        ),
                    )

                # 4. Insert metric snapshots
                metric_entries = [
                    ("overall_pass_rate", report.metrics.overall_pass_rate),
                    ("attack_success_rate", report.metrics.attack_success_rate),
                    ("unauthorized_prevention_rate", report.metrics.unauthorized_prevention_rate),
                    ("sensitive_data_exposure_rate", report.metrics.sensitive_data_exposure_rate),
                    ("benign_task_success_rate", report.metrics.benign_task_success_rate),
                    ("policy_enforcement_failure_rate", report.metrics.policy_enforcement_failure_rate),
                    ("run_completion_rate", report.metrics.run_completion_rate),
                    ("security_score", report.metrics.security_score),
                ]
                for metric_name, mv in metric_entries:
                    cursor.execute(
                        """
                        INSERT INTO metric_snapshots (
                            run_id, metric_name, numerator, denominator, value,
                            display_value, description, formula, definition_version
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run_id,
                            metric_name,
                            mv.numerator,
                            mv.denominator,
                            mv.value,
                            mv.display_value,
                            mv.description,
                            mv.formula,
                            "1.0.0",
                        ),
                    )

                # 5. Insert trace events if suite_result is provided
                if suite_result is not None and hasattr(suite_result, "results"):
                    for res in suite_result.results:
                        trace = res.execution_trace
                        if trace and trace.events:
                            for ev in trace.events:
                                cursor.execute(
                                    """
                                    INSERT INTO trace_events (
                                        event_id, run_id, scenario_id, sequence, event_type,
                                        tool_name, decision, is_denied, sanitized_payload, timestamp
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        ev.event_id,
                                        run_id,
                                        res.scenario_id,
                                        ev.sequence,
                                        ev.event_type.value if hasattr(ev.event_type, "value") else str(ev.event_type),
                                        ev.tool_name,
                                        ev.decision,
                                        1 if ev.is_denied else 0,
                                        json.dumps(ev.sanitized_payload) if ev.sanitized_payload is not None else None,
                                        ev.timestamp,
                                    ),
                                )
        except DuplicateRunError:
            raise
        except sqlite3.Error as e:
            logger.error("Failed to save evaluation report for run_id %s: %s", run_id, e)
            raise StorageError(f"Database error saving evaluation report '{run_id}': {e}") from e
        except Exception as e:
            logger.error("Unexpected error saving evaluation report for run_id %s: %s", run_id, e)
            raise StorageError(f"Unexpected error saving evaluation report '{run_id}': {e}") from e

    def get_report(self, run_id: str) -> Optional[EvaluationReport]:
        """Retrieve the full structured EvaluationReport by run_id."""
        if not run_id or not run_id.strip():
            return None

        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT report_payload FROM runs WHERE run_id = ?", (run_id.strip(),))
                row = cursor.fetchone()
                if row is None:
                    return None

                payload_str = row["report_payload"]
                return EvaluationReport.model_validate_json(payload_str)
        except sqlite3.Error as e:
            logger.error("Database error retrieving report for run_id %s: %s", run_id, e)
            raise StorageError(f"Database error retrieving report '{run_id}': {e}") from e
        except Exception as e:
            logger.error("Failed to deserialize report for run_id %s: %s", run_id, e)
            raise StorageError(f"Failed to deserialize report for run_id '{run_id}': {e}") from e

    def get_run_record(self, run_id: str) -> Optional[EvaluationRunRecord]:
        """Retrieve an EvaluationRunRecord summary for a specific run_id."""
        if not run_id or not run_id.strip():
            return None

        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT run_id, report_id, evaluator_version, suite_version, status,
                           overall_outcome, started_at, completed_at, created_at,
                           total_scenarios, passed_count, failed_count, error_count, not_run_count,
                           metrics_summary
                    FROM runs
                    WHERE run_id = ?
                    """,
                    (run_id.strip(),),
                )
                row = cursor.fetchone()
                if row is None:
                    return None

                metrics_summary = json.loads(row["metrics_summary"]) if row["metrics_summary"] else {}
                return EvaluationRunRecord(
                    run_id=row["run_id"],
                    report_id=row["report_id"],
                    evaluator_version=row["evaluator_version"],
                    suite_version=row["suite_version"],
                    status=row["status"],
                    overall_outcome=EvaluationOutcome(row["overall_outcome"]),
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    created_at=row["created_at"],
                    total_scenarios=row["total_scenarios"],
                    passed_count=row["passed_count"],
                    failed_count=row["failed_count"],
                    error_count=row["error_count"],
                    not_run_count=row["not_run_count"],
                    metrics_summary=metrics_summary,
                )
        except sqlite3.Error as e:
            logger.error("Database error retrieving run record for %s: %s", run_id, e)
            raise StorageError(f"Database error retrieving run record '{run_id}': {e}") from e

    def list_runs(self, limit: int = 50, offset: int = 0) -> List[EvaluationRunRecord]:
        """List summary records of recent evaluation runs in reverse-chronological order."""
        if limit < 1:
            return []
        if offset < 0:
            offset = 0

        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT run_id, report_id, evaluator_version, suite_version, status,
                           overall_outcome, started_at, completed_at, created_at,
                           total_scenarios, passed_count, failed_count, error_count, not_run_count,
                           metrics_summary
                    FROM runs
                    ORDER BY created_at DESC, started_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )
                rows = cursor.fetchall()
                records: List[EvaluationRunRecord] = []
                for row in rows:
                    metrics_summary = json.loads(row["metrics_summary"]) if row["metrics_summary"] else {}
                    records.append(
                        EvaluationRunRecord(
                            run_id=row["run_id"],
                            report_id=row["report_id"],
                            evaluator_version=row["evaluator_version"],
                            suite_version=row["suite_version"],
                            status=row["status"],
                            overall_outcome=EvaluationOutcome(row["overall_outcome"]),
                            started_at=row["started_at"],
                            completed_at=row["completed_at"],
                            created_at=row["created_at"],
                            total_scenarios=row["total_scenarios"],
                            passed_count=row["passed_count"],
                            failed_count=row["failed_count"],
                            error_count=row["error_count"],
                            not_run_count=row["not_run_count"],
                            metrics_summary=metrics_summary,
                        )
                    )
                return records
        except sqlite3.Error as e:
            logger.error("Database error listing runs: %s", e)
            raise StorageError(f"Database error listing runs: {e}") from e

    def run_exists(self, run_id: str) -> bool:
        """Check whether a run with the given run_id exists in storage."""
        if not run_id or not run_id.strip():
            return False

        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id.strip(),))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error("Database error checking existence of run_id %s: %s", run_id, e)
            raise StorageError(f"Database error checking run existence: {e}") from e

    def delete_run(self, run_id: str) -> bool:
        """Delete an evaluation run and its associated records. Returns True if deleted."""
        if not run_id or not run_id.strip():
            return False

        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM runs WHERE run_id = ?", (run_id.strip(),))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error("Database error deleting run_id %s: %s", run_id, e)
            raise StorageError(f"Database error deleting run '{run_id}': {e}") from e

    def get_trace_events(
        self, run_id: str, scenario_id: Optional[str] = None
    ) -> List[TraceEvent]:
        """Retrieve sanitized trace events for an evaluation run, ordered chronologically."""
        if not run_id or not run_id.strip():
            return []

        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                if scenario_id:
                    cursor.execute(
                        """
                        SELECT event_id, sequence, event_type, tool_name, decision,
                               is_denied, sanitized_payload, timestamp
                        FROM trace_events
                        WHERE run_id = ? AND scenario_id = ?
                        ORDER BY sequence ASC
                        """,
                        (run_id.strip(), scenario_id.strip()),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT event_id, sequence, event_type, tool_name, decision,
                               is_denied, sanitized_payload, timestamp
                        FROM trace_events
                        WHERE run_id = ?
                        ORDER BY scenario_id ASC, sequence ASC
                        """,
                        (run_id.strip(),),
                    )
                rows = cursor.fetchall()
                events: List[TraceEvent] = []
                for row in rows:
                    payload = json.loads(row["sanitized_payload"]) if row["sanitized_payload"] else None
                    events.append(
                        TraceEvent(
                            event_id=row["event_id"],
                            sequence=row["sequence"],
                            event_type=TraceEventType(row["event_type"]),
                            tool_name=row["tool_name"],
                            decision=row["decision"],
                            is_denied=bool(row["is_denied"]),
                            sanitized_payload=payload,
                            timestamp=row["timestamp"],
                        )
                    )
                return events
        except sqlite3.Error as e:
            logger.error("Database error getting trace events for run_id %s: %s", run_id, e)
            raise StorageError(f"Database error getting trace events: {e}") from e

    def get_findings(
        self, run_id: str, scenario_id: Optional[str] = None
    ) -> List[Finding]:
        """Retrieve security findings for an evaluation run."""
        if not run_id or not run_id.strip():
            return []

        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                if scenario_id:
                    cursor.execute(
                        """
                        SELECT finding_id, scenario_id, rule_id, rule_name, outcome,
                               severity, message, evidence, timestamp
                        FROM findings
                        WHERE run_id = ? AND scenario_id = ?
                        ORDER BY id ASC
                        """,
                        (run_id.strip(), scenario_id.strip()),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT finding_id, scenario_id, rule_id, rule_name, outcome,
                               severity, message, evidence, timestamp
                        FROM findings
                        WHERE run_id = ?
                        ORDER BY scenario_id ASC, id ASC
                        """,
                        (run_id.strip(),),
                    )
                rows = cursor.fetchall()
                findings: List[Finding] = []
                for row in rows:
                    evidence = json.loads(row["evidence"]) if row["evidence"] else {}
                    findings.append(
                        Finding(
                            finding_id=row["finding_id"],
                            scenario_id=row["scenario_id"],
                            rule_id=row["rule_id"],
                            rule_name=row["rule_name"],
                            outcome=EvaluationOutcome(row["outcome"]),
                            severity=RiskLevel(row["severity"]),
                            message=row["message"],
                            evidence=evidence,
                            timestamp=row["timestamp"],
                        )
                    )
                return findings
        except sqlite3.Error as e:
            logger.error("Database error getting findings for run_id %s: %s", run_id, e)
            raise StorageError(f"Database error getting findings: {e}") from e

    def get_scenario_evaluations(self, run_id: str) -> List[ScenarioEvaluation]:
        """Retrieve scenario evaluation results for an evaluation run."""
        if not run_id or not run_id.strip():
            return []

        try:
            # Group findings by scenario_id
            all_findings = self.get_findings(run_id)
            findings_by_scenario: Dict[str, List[Finding]] = {}
            for f in all_findings:
                findings_by_scenario.setdefault(f.scenario_id, []).append(f)

            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT scenario_id, scenario_name, category, risk_level, outcome,
                           execution_status, actual_status, expected_status,
                           attempt_detected, violation_prevented, data_exposed,
                           explanation, evaluated_at
                    FROM scenario_evaluations
                    WHERE run_id = ?
                    ORDER BY id ASC
                    """,
                    (run_id.strip(),),
                )
                rows = cursor.fetchall()
                evaluations: List[ScenarioEvaluation] = []
                for row in rows:
                    actual_st = ExecutionStatus(row["actual_status"]) if row["actual_status"] else None
                    sc_id = row["scenario_id"]
                    evaluations.append(
                        ScenarioEvaluation(
                            scenario_id=sc_id,
                            scenario_name=row["scenario_name"],
                            category=ScenarioCategory(row["category"]),
                            risk_level=RiskLevel(row["risk_level"]),
                            outcome=EvaluationOutcome(row["outcome"]),
                            findings=findings_by_scenario.get(sc_id, []),
                            execution_status=ScenarioExecutionStatus(row["execution_status"]),
                            actual_status=actual_st,
                            expected_status=ExecutionStatus(row["expected_status"]),
                            attempt_detected=bool(row["attempt_detected"]),
                            violation_prevented=bool(row["violation_prevented"]),
                            data_exposed=bool(row["data_exposed"]),
                            explanation=row["explanation"],
                            evaluated_at=row["evaluated_at"],
                        )
                    )
                return evaluations
        except sqlite3.Error as e:
            logger.error("Database error getting scenario evaluations for run_id %s: %s", run_id, e)
            raise StorageError(f"Database error getting scenario evaluations: {e}") from e

    def close(self) -> None:
        """Close database connection."""
        self.db.close()


_DEFAULT_REPOSITORY: Optional[SQLiteEvaluationRepository] = None


def get_default_repository(database_path: Optional[str] = None) -> SQLiteEvaluationRepository:
    """Return default repository singleton or instantiate with custom database_path."""
    global _DEFAULT_REPOSITORY
    if database_path is not None:
        return SQLiteEvaluationRepository(database_path)
    if _DEFAULT_REPOSITORY is None:
        from app.config import settings
        _DEFAULT_REPOSITORY = SQLiteEvaluationRepository(settings.database_path)
    return _DEFAULT_REPOSITORY
