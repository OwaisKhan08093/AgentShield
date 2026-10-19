"""Database schema definitions and migration management for SQLite persistence."""

import logging
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1

CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);
"""

CREATE_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    report_id TEXT UNIQUE NOT NULL,
    suite_id TEXT NOT NULL,
    suite_version INTEGER NOT NULL,
    evaluator_version TEXT NOT NULL,
    status TEXT NOT NULL,
    overall_outcome TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    total_scenarios INTEGER NOT NULL,
    passed_count INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    error_count INTEGER NOT NULL,
    not_run_count INTEGER NOT NULL,
    metrics_summary TEXT NOT NULL,
    report_payload TEXT NOT NULL
);
"""

CREATE_RUNS_INDICES = """
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_outcome ON runs(overall_outcome);
"""

CREATE_SCENARIO_EVALUATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS scenario_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    scenario_name TEXT NOT NULL,
    category TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    outcome TEXT NOT NULL,
    execution_status TEXT NOT NULL,
    actual_status TEXT,
    expected_status TEXT NOT NULL,
    attempt_detected INTEGER NOT NULL,
    violation_prevented INTEGER NOT NULL,
    data_exposed INTEGER NOT NULL,
    explanation TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    UNIQUE(run_id, scenario_id)
);
"""

CREATE_SCENARIO_EVALUATIONS_INDICES = """
CREATE INDEX IF NOT EXISTS idx_scenario_evals_run_id ON scenario_evaluations(run_id);
CREATE INDEX IF NOT EXISTS idx_scenario_evals_outcome ON scenario_evaluations(outcome);
CREATE INDEX IF NOT EXISTS idx_scenario_evals_category ON scenario_evaluations(category);
"""

CREATE_FINDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    outcome TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    evidence TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    UNIQUE(run_id, finding_id)
);
"""

CREATE_FINDINGS_INDICES = """
CREATE INDEX IF NOT EXISTS idx_findings_run_id ON findings(run_id);
CREATE INDEX IF NOT EXISTS idx_findings_scenario_id ON findings(scenario_id);
CREATE INDEX IF NOT EXISTS idx_findings_rule_id ON findings(rule_id);
CREATE INDEX IF NOT EXISTS idx_findings_outcome ON findings(outcome);
"""

CREATE_METRIC_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS metric_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    numerator INTEGER NOT NULL,
    denominator INTEGER NOT NULL,
    value REAL,
    display_value TEXT NOT NULL,
    description TEXT NOT NULL,
    formula TEXT NOT NULL,
    definition_version TEXT NOT NULL DEFAULT '1.0.0',
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    UNIQUE(run_id, metric_name)
);
"""

CREATE_METRIC_SNAPSHOTS_INDICES = """
CREATE INDEX IF NOT EXISTS idx_metric_snapshots_run_id ON metric_snapshots(run_id);
"""

CREATE_TRACE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS trace_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    tool_name TEXT,
    decision TEXT,
    is_denied INTEGER NOT NULL DEFAULT 0,
    sanitized_payload TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
    UNIQUE(run_id, scenario_id, sequence)
);
"""

CREATE_TRACE_EVENTS_INDICES = """
CREATE INDEX IF NOT EXISTS idx_trace_events_run_scenario ON trace_events(run_id, scenario_id);
CREATE INDEX IF NOT EXISTS idx_trace_events_event_type ON trace_events(event_type);
"""


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Initialize database tables, indices, and record schema version idempotently."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Schema version table
    cursor.execute(CREATE_SCHEMA_VERSION_TABLE)

    # 2. Runs table & indices
    cursor.execute(CREATE_RUNS_TABLE)
    for stmt in CREATE_RUNS_INDICES.strip().split(";"):
        if stmt.strip():
            cursor.execute(stmt)

    # 3. Scenario evaluations table & indices
    cursor.execute(CREATE_SCENARIO_EVALUATIONS_TABLE)
    for stmt in CREATE_SCENARIO_EVALUATIONS_INDICES.strip().split(";"):
        if stmt.strip():
            cursor.execute(stmt)

    # 4. Findings table & indices
    cursor.execute(CREATE_FINDINGS_TABLE)
    for stmt in CREATE_FINDINGS_INDICES.strip().split(";"):
        if stmt.strip():
            cursor.execute(stmt)

    # 5. Metric snapshots table & indices
    cursor.execute(CREATE_METRIC_SNAPSHOTS_TABLE)
    for stmt in CREATE_METRIC_SNAPSHOTS_INDICES.strip().split(";"):
        if stmt.strip():
            cursor.execute(stmt)

    # 6. Trace events table & indices
    cursor.execute(CREATE_TRACE_EVENTS_TABLE)
    for stmt in CREATE_TRACE_EVENTS_INDICES.strip().split(";"):
        if stmt.strip():
            cursor.execute(stmt)

    # 7. Record current schema version if not present
    cursor.execute("SELECT version FROM schema_version WHERE version = ?", (CURRENT_SCHEMA_VERSION,))
    row = cursor.fetchone()
    if row is None:
        now_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)",
            (CURRENT_SCHEMA_VERSION, now_utc, "Initial AgentShield SQLite schema"),
        )
    conn.commit()


def get_current_schema_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied schema version or 0 if uninitialized."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(version) FROM schema_version")
        row = cursor.fetchone()
        return row[0] if (row and row[0] is not None) else 0
    except sqlite3.OperationalError:
        return 0
