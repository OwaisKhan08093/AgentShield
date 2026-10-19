"""Data models for evaluation runs and storage records."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.finding import EvaluationOutcome


class RunStatus(str, Enum):
    """Execution status for an evaluation suite run."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationRunRecord(BaseModel):
    """Summary record for a persisted evaluation run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(..., description="Unique run identifier.")
    report_id: str = Field(..., description="Unique evaluation report identifier.")
    evaluator_version: str = Field(default="1.0.0", description="Evaluator engine version.")
    suite_version: int = Field(default=1, description="Scenario suite version.")
    status: str = Field(..., description="Run status or outcome string.")
    overall_outcome: EvaluationOutcome = Field(
        ..., description="Discrete overall outcome: pass, fail, error, or not_run."
    )
    started_at: str = Field(..., description="ISO 8601 UTC timestamp when run started.")
    completed_at: str = Field(..., description="ISO 8601 UTC timestamp when run completed.")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when record was saved to storage.",
    )
    total_scenarios: int = Field(..., ge=0, description="Total evaluated scenarios.")
    passed_count: int = Field(..., ge=0, description="Count of passed scenarios.")
    failed_count: int = Field(..., ge=0, description="Count of failed scenarios.")
    error_count: int = Field(..., ge=0, description="Count of error scenarios.")
    not_run_count: int = Field(..., ge=0, description="Count of unexecuted scenarios.")
    metrics_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key summary metrics (e.g. overall_pass_rate, security_score).",
    )
