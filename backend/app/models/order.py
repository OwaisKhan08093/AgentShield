"""Order domain model for simulated customer-support evaluations."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(str, Enum):
    """Permitted lifecycle states for a fictional customer order."""

    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(BaseModel):
    """Synthetic order entity used in evaluation scenarios."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    order_id: str = Field(
        ...,
        description="Unique identifier for the fictional order (e.g., 'A-100', 'B-200').",
    )
    customer_id: str = Field(
        ...,
        description="Identifier of the customer who owns this order.",
    )
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        description="Lifecycle status of the order.",
    )
    total_amount: float = Field(
        ...,
        ge=0.0,
        description="Total monetary value of the order, must be non-negative.",
    )
    currency: str = Field(
        default="USD",
        description="Currency code for the monetary amount.",
    )
    items: List[str] = Field(
        default_factory=list,
        description="List of item names or descriptions included in the order.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional synthetic order notes, potentially containing instructions or context.",
    )

    @field_validator("order_id", "customer_id", mode="after")
    @classmethod
    def validate_non_empty_identifiers(cls, value: str) -> str:
        """Ensure required identifiers are non-empty after stripping whitespace."""
        if not value or not value.strip():
            raise ValueError("Identifier cannot be empty or whitespace only.")
        return value.strip()

    @field_validator("total_amount")
    @classmethod
    def validate_non_negative_amount(cls, value: float) -> float:
        """Ensure monetary values are non-negative and properly formatted."""
        if value < 0:
            raise ValueError("Monetary amount cannot be negative.")
        return round(value, 2)
