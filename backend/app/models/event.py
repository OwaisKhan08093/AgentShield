"""Execution trace and agent request/response data models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TraceEventType(str, Enum):
    """Categorization for discrete trace events in an execution trace."""

    REQUEST = "request"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    RESPONSE = "response"


class ExecutionStatus(str, Enum):
    """High-level outcome status for an agent execution."""

    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"


class SupportAction(str, Enum):
    """Supported deterministic actions handled by the reference support agent."""

    LOOKUP_ORDER = "lookup_order"
    GET_REFUND_POLICY = "get_refund_policy"
    REQUEST_REFUND_APPROVAL = "request_refund_approval"


class SupportRequest(BaseModel):
    """Structured customer-support request submitted to the agent."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    customer_id: Optional[str] = Field(
        default=None,
        description="Synthetic customer identity submitting the request.",
    )
    action: str = Field(
        ...,
        description="The requested support action (e.g. 'lookup_order', 'get_refund_policy', 'request_refund_approval').",
    )
    order_id: Optional[str] = Field(
        default=None,
        description="Target order identifier for order-specific operations.",
    )
    amount: Optional[float] = Field(
        default=None,
        description="Monetary amount requested for refund approval operations.",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Explanation or customer reason for the action.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional category filter for refund policy lookup.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Safe metadata associated with the request.",
    )

    @field_validator("action", mode="after")
    @classmethod
    def validate_action_non_empty(cls, value: str) -> str:
        """Ensure action name is not empty or whitespace only."""
        if not value or not value.strip():
            raise ValueError("action cannot be empty or whitespace only.")
        return value.strip()


class TraceEvent(BaseModel):
    """An individual recorded event in an agent's execution timeline."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(
        ...,
        description="Unique identifier for this trace event.",
    )
    sequence: int = Field(
        ...,
        ge=1,
        description="Deterministic 1-based chronological sequence order.",
    )
    event_type: TraceEventType = Field(
        ...,
        description="Category of the event (request, tool_call, tool_result, response).",
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Name of the invoked tool, if applicable.",
    )
    decision: Optional[str] = Field(
        default=None,
        description="Authorization or execution decision (e.g., 'invoked', 'allowed', 'denied', 'error').",
    )
    is_denied: bool = Field(
        default=False,
        description="Flag indicating if this event represents an authorization denial.",
    )
    sanitized_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Safe sanitized payload containing no cross-customer secrets.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of event recording.",
    )


class ExecutionTrace(BaseModel):
    """Complete, ordered audit record of an agent run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_id: str = Field(
        ...,
        description="Unique identifier for the agent execution session.",
    )
    customer_id: Optional[str] = Field(
        default=None,
        description="Caller identity associated with this execution.",
    )
    action: str = Field(
        ...,
        description="The requested support action evaluated.",
    )
    status: ExecutionStatus = Field(
        ...,
        description="Overall outcome of the execution: success, denied, or error.",
    )
    summary: str = Field(
        ...,
        description="Safe, human-readable summary of the execution outcome.",
    )
    events: List[TraceEvent] = Field(
        default_factory=list,
        description="Chronological ordered list of events captured during execution.",
    )
    final_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Final sanitized output data if execution succeeded.",
    )
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when execution began.",
    )
    completed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when execution completed.",
    )


class AgentResponse(BaseModel):
    """Top-level structured result returned by the reference support agent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_id: str = Field(
        ...,
        description="Identifier matching the associated execution trace.",
    )
    status: ExecutionStatus = Field(
        ...,
        description="Final execution status (success, denied, error).",
    )
    summary: str = Field(
        ...,
        description="Safe message describing the outcome.",
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Sanitized data payload returned on success, or None on denial/error.",
    )
    trace: ExecutionTrace = Field(
        ...,
        description="Full structured execution trace containing ordered events.",
    )

    @property
    def is_success(self) -> bool:
        """Return True if execution succeeded."""
        return self.status == ExecutionStatus.SUCCESS

    @property
    def is_denied(self) -> bool:
        """Return True if execution was blocked by authorization controls."""
        return self.status == ExecutionStatus.DENIED

    @property
    def is_error(self) -> bool:
        """Return True if execution failed due to an error."""
        return self.status == ExecutionStatus.ERROR
