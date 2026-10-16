"""Data models for security scenarios and scenario execution results."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.event import AgentResponse, ExecutionStatus, ExecutionTrace, SupportRequest


class ScenarioCategory(str, Enum):
    """Standardized classification for evaluation scenarios and security vectors."""

    BENIGN_TASK = "benign_task"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    APPROVAL_BYPASS = "approval_bypass"
    DATA_EXPOSURE = "data_exposure"
    MALFORMED_INPUT = "malformed_input"
    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"


AttackCategory = ScenarioCategory


class RiskLevel(str, Enum):
    """Risk severity classification for a scenario."""

    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExpectedBehavior(BaseModel):
    """Specification of expected security behavior and observable assertions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_status: ExecutionStatus = Field(
        ...,
        description="Expected top-level execution status: success, denied, or error.",
    )
    must_have_authorization_denial: bool = Field(
        default=False,
        description="Whether the execution trace must record an authorization denial event.",
    )
    must_not_expose_resource_owner: Optional[str] = Field(
        default=None,
        description="Customer identifier whose data/ownership must NOT be disclosed.",
    )
    must_not_return_order_details: bool = Field(
        default=False,
        description="Whether order details must not be present in output data.",
    )
    expected_tool_name: Optional[str] = Field(
        default=None,
        description="Tool expected to be invoked during execution, if any.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the expected security outcome.",
    )


class Scenario(BaseModel):
    """A deterministic evaluation scenario defining inputs and expected outcomes."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(
        ...,
        description="Unique, stable identifier for the scenario (e.g. AUTHZ-CROSS-ORDER-001).",
    )
    name: str = Field(
        ...,
        description="Descriptive, human-readable name of the scenario.",
    )
    category: ScenarioCategory = Field(
        ...,
        description="Attack category or evaluation category.",
    )
    description: str = Field(
        ...,
        description="Short description of what the scenario evaluates.",
    )
    security_objective: str = Field(
        ...,
        description="Security property or authorization boundary being verified.",
    )
    request: Union[SupportRequest, Dict[str, Any]] = Field(
        ...,
        description="Structured request (or raw dict payload) submitted to the reference agent.",
    )
    expected_behavior: ExpectedBehavior = Field(
        ...,
        description="Expected security behavior and outcome assertions.",
    )
    success_condition: str = Field(
        ...,
        description="Explicit criteria for when this scenario is considered successful.",
    )
    failure_condition: str = Field(
        ...,
        description="Explicit criteria that indicate failure or security violation.",
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.MEDIUM,
        description="Risk severity level of the evaluated attack surface.",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Searchable tags (e.g. ['authorization', 'prompt-injection']).",
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Version number of the scenario definition.",
    )

    @field_validator("scenario_id", mode="after")
    @classmethod
    def validate_scenario_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("scenario_id cannot be empty or whitespace.")
        return clean

    @field_validator("name", mode="after")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("name cannot be empty or whitespace.")
        return clean


class ScenarioExecutionStatus(str, Enum):
    """Execution status of a scenario through the runner."""

    COMPLETED = "completed"
    ERROR = "error"
    INCOMPLETE = "incomplete"


class ScenarioResult(BaseModel):
    """Captures the execution outcome and trace evidence for a single scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(
        ...,
        description="Identifier of the executed scenario.",
    )
    scenario_name: str = Field(
        ...,
        description="Name of the executed scenario.",
    )
    category: ScenarioCategory = Field(
        ...,
        description="Attack category of the executed scenario.",
    )
    expected_behavior: ExpectedBehavior = Field(
        ...,
        description="Expected behavior recorded from scenario definition.",
    )
    actual_status: Optional[ExecutionStatus] = Field(
        default=None,
        description="Actual execution status from AgentResponse (SUCCESS, DENIED, ERROR), or None if execution failed before agent response.",
    )
    execution_status: ScenarioExecutionStatus = Field(
        ...,
        description="Runner execution status: COMPLETED, ERROR, or INCOMPLETE.",
    )
    agent_response: Optional[AgentResponse] = Field(
        default=None,
        description="Full AgentResponse captured from the agent, including execution trace.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Sanitized error diagnostic if runner encountered an unhandled exception.",
    )
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when scenario execution started.",
    )
    completed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when scenario execution completed.",
    )
    duration_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Execution duration in milliseconds.",
    )

    @property
    def execution_trace(self) -> Optional[ExecutionTrace]:
        """Convenience accessor for execution trace."""
        return self.agent_response.trace if self.agent_response else None

    @property
    def matches_expected_status(self) -> bool:
        """Return True if actual agent execution status matches expected status.

        Errors or exceptions at the runner level are never treated as matching or passes.
        """
        if self.execution_status != ScenarioExecutionStatus.COMPLETED or self.agent_response is None or self.actual_status is None:
            return False
        return self.actual_status == self.expected_behavior.expected_status


class SuiteExecutionResult(BaseModel):
    """Structured collection of scenario execution results from a runner session."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(
        ...,
        description="Unique identifier for this runner execution batch.",
    )
    results: List[ScenarioResult] = Field(
        default_factory=list,
        description="Ordered list of individual scenario execution results.",
    )
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when the suite execution began.",
    )
    completed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when the suite execution finished.",
    )

    @property
    def total_count(self) -> int:
        """Total number of scenarios executed."""
        return len(self.results)

    @property
    def completed_count(self) -> int:
        """Number of scenarios that completed execution successfully without runner errors."""
        return sum(1 for r in self.results if r.execution_status == ScenarioExecutionStatus.COMPLETED)

    @property
    def error_count(self) -> int:
        """Number of scenarios that encountered runner errors."""
        return sum(1 for r in self.results if r.execution_status == ScenarioExecutionStatus.ERROR)

    @property
    def matches_expected_count(self) -> int:
        """Number of completed scenarios where actual status matches expected status."""
        return sum(1 for r in self.results if r.matches_expected_status)

    def get_result(self, scenario_id: str) -> Optional[ScenarioResult]:
        """Look up a result by scenario ID."""
        for r in self.results:
            if r.scenario_id == scenario_id:
                return r
        return None

    def by_category(self, category: ScenarioCategory) -> List[ScenarioResult]:
        """Filter results by scenario category."""
        return [r for r in self.results if r.category == category]
