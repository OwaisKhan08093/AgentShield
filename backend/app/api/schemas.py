"""API request and response Pydantic schemas for AgentShield."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.event import ExecutionStatus
from app.models.finding import EvaluationOutcome, EvaluationReport, SummaryCounts
from app.models.scenario import (
    ExpectedBehavior,
    RiskLevel,
    ScenarioCategory,
    ScenarioExecutionStatus,
)


class ScenarioSummaryResponse(BaseModel):
    """Safe scenario summary without exposing internal fixture secrets or customer identities."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., description="Unique scenario identifier.")
    name: str = Field(..., description="Human-readable scenario name.")
    category: ScenarioCategory = Field(..., description="Scenario security attack category.")
    description: str = Field(..., description="Concise description of evaluated behavior.")
    security_objective: str = Field(..., description="Security boundary or policy under test.")
    risk_level: RiskLevel = Field(..., description="Risk severity rating.")
    tags: List[str] = Field(default_factory=list, description="Categorization tags.")
    version: int = Field(default=1, description="Scenario definition version.")
    enabled: bool = Field(default=True, description="Whether the scenario is enabled for evaluation.")


class ScenarioDetailResponse(BaseModel):
    """Detailed scenario definition for inspection."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., description="Unique scenario identifier.")
    name: str = Field(..., description="Human-readable scenario name.")
    category: ScenarioCategory = Field(..., description="Scenario security attack category.")
    description: str = Field(..., description="Concise description of evaluated behavior.")
    security_objective: str = Field(..., description="Security boundary or policy under test.")
    risk_level: RiskLevel = Field(..., description="Risk severity rating.")
    tags: List[str] = Field(default_factory=list, description="Categorization tags.")
    version: int = Field(default=1, description="Scenario definition version.")
    enabled: bool = Field(default=True, description="Whether the scenario is enabled for evaluation.")
    expected_behavior: ExpectedBehavior = Field(..., description="Expected behavior assertions.")
    success_condition: str = Field(..., description="Condition required for PASS verdict.")
    failure_condition: str = Field(..., description="Condition causing FAIL verdict.")


class RunOptions(BaseModel):
    """Configuration options for an evaluation run."""

    model_config = ConfigDict(extra="forbid")

    continue_on_error: bool = Field(
        default=True,
        description="Whether the runner should continue evaluating subsequent scenarios if one fails.",
    )
    record_trace: bool = Field(
        default=True,
        description="Whether to capture ordered trace events during agent execution.",
    )


class CreateRunRequest(BaseModel):
    """Request payload to initiate an evaluation run."""

    model_config = ConfigDict(extra="forbid")

    suite_id: str = Field(
        default="support-agent-security-v1",
        min_length=1,
        max_length=128,
        description="Target evaluation suite identifier.",
    )
    agent_id: str = Field(
        default="reference-agent",
        min_length=1,
        max_length=128,
        description="Target agent identifier to evaluate.",
    )
    scenario_ids: Optional[List[str]] = Field(
        default=None,
        max_length=50,
        description="Optional list of specific scenario IDs to execute. If omitted, all canonical scenarios are run.",
    )
    options: RunOptions = Field(
        default_factory=RunOptions,
        description="Run execution options.",
    )


class RunCreateResponse(BaseModel):
    """Summary response returned when a suite run is executed and persisted."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., description="Unique run identifier.")
    report_id: str = Field(..., description="Unique report identifier.")
    suite_id: str = Field(..., description="Suite identifier evaluated.")
    status: str = Field(..., description="Run execution status.")
    overall_outcome: EvaluationOutcome = Field(..., description="Overall evaluation verdict.")
    started_at: str = Field(..., description="ISO 8601 UTC timestamp when run began.")
    completed_at: str = Field(..., description="ISO 8601 UTC timestamp when run completed.")
    total_scenarios: int = Field(..., ge=0, description="Total executed scenarios.")
    passed_count: int = Field(..., ge=0, description="Total passed scenarios.")
    failed_count: int = Field(..., ge=0, description="Total failed scenarios.")
    error_count: int = Field(..., ge=0, description="Total error scenarios.")
    not_run_count: int = Field(..., ge=0, description="Total not-run scenarios.")
    summary_counts: SummaryCounts = Field(..., description="Detailed summary tally.")
    metrics_summary: Dict[str, Any] = Field(default_factory=dict, description="Key metric snapshot summary.")


class FindingSummaryResponse(BaseModel):
    """Concise summary of an evaluated security rule finding."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(..., description="Unique finding identifier.")
    rule_id: str = Field(..., description="Evaluated security rule ID.")
    rule_name: str = Field(..., description="Descriptive name of the security rule.")
    outcome: EvaluationOutcome = Field(..., description="Outcome of the rule check.")
    severity: RiskLevel = Field(..., description="Risk severity level.")
    message: str = Field(..., description="Explanation of the finding.")
    timestamp: str = Field(..., description="Timestamp of finding recording.")


class ScenarioResultResponse(BaseModel):
    """Detailed per-scenario evaluation result for a run."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., description="Unique scenario identifier.")
    scenario_name: str = Field(..., description="Human-readable scenario name.")
    category: ScenarioCategory = Field(..., description="Attack category.")
    risk_level: RiskLevel = Field(..., description="Risk severity level.")
    outcome: EvaluationOutcome = Field(..., description="Verdict: pass, fail, error, or not_run.")
    execution_status: ScenarioExecutionStatus = Field(..., description="Runner execution status.")
    actual_status: Optional[ExecutionStatus] = Field(default=None, description="Actual agent response status.")
    expected_status: ExecutionStatus = Field(..., description="Expected execution status.")
    attempt_detected: bool = Field(default=False, description="Whether an attack attempt was detected.")
    violation_prevented: bool = Field(default=False, description="Whether the violation was prevented.")
    data_exposed: bool = Field(default=False, description="Whether data was exposed.")
    explanation: str = Field(..., description="Evaluation summary explanation.")
    evaluated_at: str = Field(..., description="Evaluation timestamp.")
    duration_ms: Optional[float] = Field(default=None, description="Execution duration in milliseconds if available.")
    finding_count: int = Field(..., ge=0, description="Total count of findings for this scenario.")
    findings: List[FindingSummaryResponse] = Field(default_factory=list, description="List of rule finding summaries.")


class EvaluationReportExportResponse(BaseModel):
    """Export container for structured evaluation report with schema version metadata."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        default="1.0.0",
        description="Version of the AgentShield evaluation report export schema.",
    )
    exported_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when export was generated.",
    )
    report: EvaluationReport = Field(
        ...,
        description="Full structured evaluation report.",
    )
