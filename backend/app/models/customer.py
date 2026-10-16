"""Customer domain model for simulated customer-support evaluations."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomerStatus(str, Enum):
    """Permitted lifecycle and account states for a synthetic customer."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class Customer(BaseModel):
    """Synthetic customer entity used in evaluation scenarios."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    customer_id: str = Field(
        ...,
        description="Unique identifier for the synthetic customer (e.g., 'alice', 'bob').",
    )
    name: str = Field(
        ...,
        description="Fictional full name of the customer.",
    )
    email: Optional[str] = Field(
        default=None,
        description="Synthetic contact email address.",
    )
    status: CustomerStatus = Field(
        default=CustomerStatus.ACTIVE,
        description="Current account status.",
    )

    @field_validator("customer_id", "name", mode="after")
    @classmethod
    def validate_non_empty_identifier(cls, value: str) -> str:
        """Ensure required identifiers are non-empty after stripping whitespace."""
        if not value or not value.strip():
            raise ValueError("Field cannot be empty or whitespace only.")
        return value.strip()
