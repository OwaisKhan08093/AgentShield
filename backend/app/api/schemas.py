"""API request and response Pydantic schemas for AgentShield."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.finding import EvaluationOutcome, SummaryCounts
from app.models.scenario import ExpectedBehavior, RiskLevel, ScenarioCategory


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
