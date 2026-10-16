"""Structured tool result model for simulated tool executions."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ToolResultStatus(str, Enum):
    """Permitted execution statuses for a simulated tool call."""

    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"


class ToolResult(BaseModel):
    """Structured result returned from simulated tool execution."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tool_name: str = Field(
        ...,
        description="Name of the invoked tool (e.g., 'lookup_order', 'get_refund_policy', 'request_refund_approval').",
    )
    status: ToolResultStatus = Field(
        ...,
        description="Execution or authorization outcome status ('success', 'denied', 'error').",
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured data payload returned by the tool upon successful or partial execution.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Human-readable error or denial message if the tool call failed or was denied.",
    )
    is_denied: bool = Field(
        default=False,
        description="Explicit flag indicating whether the tool action was blocked by authorization controls.",
    )
    amount: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Optional monetary amount associated with the tool action (e.g., refund amount), must be non-negative.",
    )

    @field_validator("tool_name", mode="after")
    @classmethod
    def validate_tool_name(cls, value: str) -> str:
        """Ensure tool_name is non-empty after stripping whitespace."""
        if not value or not value.strip():
            raise ValueError("tool_name cannot be empty or whitespace only.")
        return value.strip()

    @field_validator("amount")
    @classmethod
    def validate_non_negative_amount(cls, value: Optional[float]) -> Optional[float]:
        """Ensure monetary values, when present, are non-negative."""
        if value is not None and value < 0:
            raise ValueError("Monetary amount cannot be negative.")
        return value

    @model_validator(mode="after")
    def synchronize_denied_flag(self) -> "ToolResult":
        """Automatically set is_denied to True if status is DENIED."""
        if self.status == ToolResultStatus.DENIED:
            self.is_denied = True
        return self
