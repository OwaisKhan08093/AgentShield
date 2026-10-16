"""Tool-level authorization guard for simulated customer-support operations.

Enforces deterministic resource ownership boundaries independently of LLM reasoning,
prompts, or external services. Adheres to the principle that model instructions are not
a security boundary.
"""

from enum import Enum
from typing import Callable, Dict, Mapping, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from app.models import Customer, CustomerStatus, Order


class AuthReasonCode(str, Enum):
    """Standardized machine-readable reason codes for authorization decisions."""

    ALLOWED = "allowed"
    OWNERSHIP_MISMATCH = "ownership_mismatch"
    ORDER_NOT_FOUND = "order_not_found"
    CUSTOMER_NOT_FOUND = "customer_not_found"
    CUSTOMER_INACTIVE = "customer_inactive"
    INVALID_IDENTITY = "invalid_identity"
    INVALID_ORDER_ID = "invalid_order_id"
    AUTHORIZATION_ERROR = "authorization_error"


class AuthorizationDecision(BaseModel):
    """Structured, immutable evaluation outcome of an authorization check."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed: bool = Field(
        ...,
        description="Whether resource access is permitted.",
    )
    reason_code: AuthReasonCode = Field(
        ...,
        description="Standardized reason code explaining the outcome.",
    )
    message: str = Field(
        ...,
        description="Safe explanation containing no protected or cross-customer data.",
    )
    customer_id: Optional[str] = Field(
        default=None,
        description="The customer identity evaluated, if available.",
    )
    order_id: Optional[str] = Field(
        default=None,
        description="The order identifier evaluated, if available.",
    )


class AuthorizationGuard:
    """Deterministic authorization guard validating order resource ownership."""

    def __init__(
        self,
        orders: Optional[Mapping[str, Order]] = None,
        customers: Optional[Mapping[str, Customer]] = None,
        order_lookup: Optional[Callable[[str], Optional[Order]]] = None,
        customer_lookup: Optional[Callable[[str], Optional[Customer]]] = None,
    ):
        """Initialize the guard with optional in-memory stores or lookup hooks."""
        self._orders: Dict[str, Order] = dict(orders) if orders is not None else {}
        self._customers: Optional[Dict[str, Customer]] = (
            dict(customers) if customers is not None else None
        )
        self._order_lookup = order_lookup
        self._customer_lookup = customer_lookup

    def register_order(self, order: Order) -> None:
        """Register an order in the in-memory repository."""
        self._orders[order.order_id] = order

    def register_customer(self, customer: Customer) -> None:
        """Register a customer in the in-memory repository."""
        if self._customers is None:
            self._customers = {}
        self._customers[customer.customer_id] = customer

    def get_order(self, order_id: str) -> Optional[Order]:
        """Look up an order by ID via custom lookup hook or in-memory store."""
        if self._order_lookup is not None:
            return self._order_lookup(order_id)
        return self._orders.get(order_id)

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Look up a customer by ID via custom lookup hook or in-memory store."""
        if self._customer_lookup is not None:
            return self._customer_lookup(customer_id)
        if self._customers is not None:
            return self._customers.get(customer_id)
        return None

    def check_order_access(
        self,
        customer_id: Optional[str] = None,
        order_id: Optional[str] = None,
        customer: Optional[Customer] = None,
        order: Optional[Order] = None,
    ) -> AuthorizationDecision:
        """Evaluate whether a customer is authorized to access a given order.

        Fails closed on any ambiguity, missing identity, unknown resource, or error.
        Guarantees that denial messages never expose protected resource details.
        """
        resolved_customer_id: Optional[str] = None
        resolved_order_id: Optional[str] = None

        try:
            # 1. Resolve and validate customer identifier
            if customer is not None:
                resolved_customer_id = customer.customer_id
            elif customer_id is not None and isinstance(customer_id, str):
                resolved_customer_id = customer_id.strip() or None

            if not resolved_customer_id:
                return AuthorizationDecision(
                    allowed=False,
                    reason_code=AuthReasonCode.INVALID_IDENTITY,
                    message="Access denied: missing or invalid customer identifier.",
                    customer_id=None,
                    order_id=order.order_id if order else (order_id.strip() if isinstance(order_id, str) and order_id.strip() else None),
                )

            # 2. Verify customer existence and status if customer store is present
            evaluated_customer: Optional[Customer] = customer
            if evaluated_customer is None:
                evaluated_customer = self.get_customer(resolved_customer_id)

            if self._customers is not None or self._customer_lookup is not None:
                if evaluated_customer is None:
                    return AuthorizationDecision(
                        allowed=False,
                        reason_code=AuthReasonCode.CUSTOMER_NOT_FOUND,
                        message="Access denied: customer identity cannot be verified.",
                        customer_id=resolved_customer_id,
                        order_id=order.order_id if order else (order_id.strip() if isinstance(order_id, str) and order_id.strip() else None),
                    )
                if evaluated_customer.status != CustomerStatus.ACTIVE:
                    return AuthorizationDecision(
                        allowed=False,
                        reason_code=AuthReasonCode.CUSTOMER_INACTIVE,
                        message="Access denied: customer account is not active.",
                        customer_id=resolved_customer_id,
                        order_id=order.order_id if order else (order_id.strip() if isinstance(order_id, str) and order_id.strip() else None),
                    )

            # 3. Resolve and validate order identifier
            if order is not None:
                resolved_order_id = order.order_id
            elif order_id is not None and isinstance(order_id, str):
                resolved_order_id = order_id.strip() or None

            if not resolved_order_id:
                return AuthorizationDecision(
                    allowed=False,
                    reason_code=AuthReasonCode.INVALID_ORDER_ID,
                    message="Access denied: missing or invalid order identifier.",
                    customer_id=resolved_customer_id,
                    order_id=None,
                )

            # 4. Resolve order object
            resolved_order: Optional[Order] = order
            if resolved_order is None:
                resolved_order = self.get_order(resolved_order_id)

            if resolved_order is None:
                return AuthorizationDecision(
                    allowed=False,
                    reason_code=AuthReasonCode.ORDER_NOT_FOUND,
                    message="Access denied: requested order does not exist or is unknown.",
                    customer_id=resolved_customer_id,
                    order_id=resolved_order_id,
                )

            # 5. Check resource ownership
            if resolved_order.customer_id != resolved_customer_id:
                return AuthorizationDecision(
                    allowed=False,
                    reason_code=AuthReasonCode.OWNERSHIP_MISMATCH,
                    message="Access denied: caller does not own the requested order.",
                    customer_id=resolved_customer_id,
                    order_id=resolved_order_id,
                )

            # 6. Access granted
            return AuthorizationDecision(
                allowed=True,
                reason_code=AuthReasonCode.ALLOWED,
                message="Access granted: customer owns requested order.",
                customer_id=resolved_customer_id,
                order_id=resolved_order_id,
            )

        except Exception:
            # Always fail closed on unhandled errors
            return AuthorizationDecision(
                allowed=False,
                reason_code=AuthReasonCode.AUTHORIZATION_ERROR,
                message="Access denied: authorization service failure.",
                customer_id=resolved_customer_id,
                order_id=resolved_order_id,
            )
