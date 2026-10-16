"""Data models for evaluation outcomes, security findings, and metrics."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.event import ExecutionStatus
from app.models.scenario import RiskLevel, ScenarioCategory, ScenarioExecutionStatus


class EvaluationOutcome(str, Enum):
    """Discrete verdict for an evaluated security scenario or assertion."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    NOT_RUN = "not_run"


class Finding(BaseModel):
    """An individual security finding or rule check outcome with trace evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    finding_id: str = Field(
        ...,
        description="Unique identifier for this finding record.",
    )
    scenario_id: str = Field(
        ...,
        description="Scenario identifier associated with this finding.",
    )
    rule_id: str = Field(
        ...,
        description="Identifier of the evaluated security rule (e.g. RULE-AUTHZ-001).",
    )
    rule_name: str = Field(
        ...,
        description="Descriptive name of the evaluated security rule.",
    )
    outcome: EvaluationOutcome = Field(
        ...,
        description="Verdict for this rule check: pass, fail, error, or not_run.",
    )
    severity: RiskLevel = Field(
        ...,
        description="Risk severity level of the finding.",
    )
    message: str = Field(
        ...,
        description="Concise human-readable explanation of the finding.",
    )
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized evidence extracted from trace events or execution results.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when finding was generated.",
    )


class ScenarioEvaluation(BaseModel):
    """Comprehensive evaluation record for an individual scenario execution."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(
        ...,
        description="Scenario identifier.",
    )
    scenario_name: str = Field(
        ...,
        description="Scenario name.",
    )
    category: ScenarioCategory = Field(
        ...,
        description="Scenario attack category.",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Risk severity classification.",
    )
    outcome: EvaluationOutcome = Field(
        ...,
        description="Overall verdict for this scenario: pass, fail, error, or not_run.",
    )
    findings: List[Finding] = Field(
        default_factory=list,
        description="List of individual rule findings evaluated for this scenario.",
    )
    execution_status: ScenarioExecutionStatus = Field(
        ...,
        description="Runtime execution status from runner.",
    )
    actual_status: Optional[ExecutionStatus] = Field(
        default=None,
        description="Actual execution status returned by agent, if available.",
    )
    expected_status: ExecutionStatus = Field(
        ...,
        description="Expected execution status from scenario definition.",
    )
    attempt_detected: bool = Field(
        default=False,
        description="Whether an attack or policy violation attempt was observed in input/trace.",
    )
    violation_prevented: bool = Field(
        default=False,
        description="Whether an observed attempt was successfully blocked by security controls.",
    )
    data_exposed: bool = Field(
        default=False,
        description="Whether protected or cross-customer data leaked to output/trace.",
    )
    explanation: str = Field(
        ...,
        description="Summary explanation of the evaluation verdict.",
    )
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of evaluation.",
    )


class MetricValue(BaseModel):
    """A quantified metric with documented numerator, denominator, and formula."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., description="Human-readable name of the metric.")
    numerator: int = Field(..., ge=0, description="Numerator count.")
    denominator: int = Field(..., ge=0, description="Denominator count.")
    value: Optional[float] = Field(
        default=None,
        description="Float ratio (0.0 to 1.0) or None if denominator is zero.",
    )
    display_value: str = Field(
        ...,
        description="Formatted string representation (e.g. '100.0%' or 'N/A').",
    )
    description: str = Field(
        ...,
        description="Explanation of what this metric measures.",
    )
    formula: str = Field(
        ...,
        description="Mathematical formula defining the metric calculation.",
    )


class CategoryMetric(BaseModel):
    """Aggregated evaluation metrics for a single scenario category."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    category: ScenarioCategory
    total_count: int = Field(..., ge=0)
    passed_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    error_count: int = Field(..., ge=0)
    not_run_count: int = Field(..., ge=0)
    pass_rate: MetricValue


class RiskMetric(BaseModel):
    """Aggregated evaluation metrics for a single risk level."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    risk_level: RiskLevel
    total_count: int = Field(..., ge=0)
    passed_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    error_count: int = Field(..., ge=0)
    not_run_count: int = Field(..., ge=0)
    pass_rate: MetricValue


class SummaryCounts(BaseModel):
    """High-level tally of scenario evaluation outcomes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_scenarios: int = Field(..., ge=0)
    passed_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    error_count: int = Field(..., ge=0)
    not_run_count: int = Field(..., ge=0)


class EvaluationMetrics(BaseModel):
    """Comprehensive suite-level metrics for an evaluation report."""

    model_config = ConfigDict(extra="forbid")

    overall_pass_rate: MetricValue
    attack_success_rate: MetricValue
    unauthorized_prevention_rate: MetricValue
    sensitive_data_exposure_rate: MetricValue
    benign_task_success_rate: MetricValue
    policy_enforcement_failure_rate: MetricValue
    run_completion_rate: MetricValue
    security_score: MetricValue
    by_category: Dict[str, CategoryMetric] = Field(default_factory=dict)
    by_risk_level: Dict[str, RiskMetric] = Field(default_factory=dict)
    violations_by_rule: Dict[str, int] = Field(default_factory=dict)
    violations_by_severity: Dict[str, int] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    """Structured evaluation report containing verdicts, findings, and metrics."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., description="Unique report identifier.")
    run_id: str = Field(..., description="Identifier of the evaluated scenario run.")
    evaluator_version: str = Field(default="1.0.0", description="Version of the evaluation engine.")
    suite_version: int = Field(default=1, description="Version of the scenario suite evaluated.")
    started_at: str = Field(..., description="ISO 8601 UTC timestamp when evaluation began.")
    completed_at: str = Field(..., description="ISO 8601 UTC timestamp when evaluation finished.")
    overall_outcome: EvaluationOutcome = Field(
        ...,
        description="Overall suite evaluation status (pass, fail, error, or not_run).",
    )
    summary_counts: SummaryCounts = Field(..., description="Summary counts of scenario outcomes.")
    metrics: EvaluationMetrics = Field(..., description="Computed suite-level metrics.")
    scenario_evaluations: List[ScenarioEvaluation] = Field(
        default_factory=list,
        description="Ordered list of per-scenario evaluation records.",
    )
    findings: List[Finding] = Field(
        default_factory=list,
        description="All security findings identified across the evaluated scenarios.",
    )
    limitation_statement: str = Field(
        default=(
            "Evaluation results apply exclusively to the synthetic test suite and tested configuration. "
            "Passing synthetic scenarios does not certify that an AI agent is universally secure or resistant "
            "to novel or unrestricted real-world attacks."
        ),
        description="Explicit disclaimer on the scope and limitations of the evaluation.",
    )

    def get_scenario_evaluation(self, scenario_id: str) -> Optional[ScenarioEvaluation]:
        """Retrieve evaluation record for a specific scenario ID."""
        for se in self.scenario_evaluations:
            if se.scenario_id == scenario_id:
                return se
        return None

    def get_findings_for_scenario(self, scenario_id: str) -> List[Finding]:
        """Retrieve all findings associated with a specific scenario ID."""
        return [f for f in self.findings if f.scenario_id == scenario_id]
