"""Secure mock tools for the simulated customer-support agent.

Every protected tool delegates authorization to the AuthorizationGuard.
Model instructions or agent prompts never serve as a security boundary.
All operations are simulated; no external APIs, payments, or databases are contacted.
"""

from typing import Any, Dict, Optional
from app.models import ToolResult, ToolResultStatus
from app.security import AuthorizationGuard


SYNTHETIC_REFUND_POLICY: Dict[str, Any] = {
    "policy_version": "2026.1",
    "window_days": 30,
    "eligibility_rules": [
        "Item must be returned within 30 days of recorded delivery date.",
        "Item must be in original condition with all accessories and packaging.",
        "Proof of purchase and verified customer account required.",
        "Consumables and software license keys are non-refundable once opened.",
    ],
    "process": [
        "1. Request a simulated refund authorization via customer support.",
        "2. Support verifies account ownership and order status.",
        "3. Once approved, simulated credit is recorded within 3-5 business days.",
    ],
    "summary": "Standard 30-day synthetic return and refund policy for simulated customer support.",
}


def lookup_order(
    customer_id: Optional[str],
    order_id: Optional[str],
    auth_guard: AuthorizationGuard,
) -> ToolResult:
    """Retrieve fictional order details only after verifying customer ownership.

    Fails closed on missing identity, unknown order, ownership mismatch, or errors.
    Denial responses never expose protected order details or cross-customer data.
    """
    try:
        decision = auth_guard.check_order_access(customer_id=customer_id, order_id=order_id)
        if not decision.allowed:
            return ToolResult(
                tool_name="lookup_order",
                status=ToolResultStatus.DENIED,
                error=decision.message,
                is_denied=True,
                data=None,
            )

        order = auth_guard.get_order(order_id.strip() if order_id else "")
        if order is None:
            return ToolResult(
                tool_name="lookup_order",
                status=ToolResultStatus.DENIED,
                error="Access denied: requested order does not exist or is unknown.",
                is_denied=True,
                data=None,
            )

        order_data: Dict[str, Any] = {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "status": order.status.value,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "items": list(order.items),
        }
        if order.notes:
            order_data["notes"] = order.notes

        return ToolResult(
            tool_name="lookup_order",
            status=ToolResultStatus.SUCCESS,
            data=order_data,
            error=None,
            is_denied=False,
        )

    except Exception:
        return ToolResult(
            tool_name="lookup_order",
            status=ToolResultStatus.ERROR,
            error="Unexpected error occurred during order lookup.",
            is_denied=False,
            data=None,
        )


def get_refund_policy(category: Optional[str] = None) -> ToolResult:
    """Retrieve the fixed, non-sensitive synthetic refund policy.

    Does not access or expose customer-specific data.
    """
    try:
        policy_data = dict(SYNTHETIC_REFUND_POLICY)
        if category and isinstance(category, str) and category.strip():
            policy_data["requested_category"] = category.strip()
        else:
            policy_data["requested_category"] = "general"

        return ToolResult(
            tool_name="get_refund_policy",
            status=ToolResultStatus.SUCCESS,
            data=policy_data,
            error=None,
            is_denied=False,
        )
    except Exception:
        return ToolResult(
            tool_name="get_refund_policy",
            status=ToolResultStatus.ERROR,
            error="Unexpected error occurred while retrieving refund policy.",
            is_denied=False,
            data=None,
        )


def request_refund_approval(
    customer_id: Optional[str],
    order_id: Optional[str],
    amount: Optional[float],
    reason: Optional[str] = None,
    auth_guard: Optional[AuthorizationGuard] = None,
) -> ToolResult:
    """Create a simulated refund approval request after validating order ownership.

    Enforces:
    - Caller must own the order via AuthorizationGuard.
    - Amount must be strictly positive and within the order total.
    - Does NOT execute a real refund; records a simulated request state only.
    """
    if auth_guard is None:
        return ToolResult(
            tool_name="request_refund_approval",
            status=ToolResultStatus.ERROR,
            error="Authorization service unavailable.",
            is_denied=False,
            data=None,
        )

    # 1. Validate monetary amount parameter
    if amount is None or not isinstance(amount, (int, float)) or amount <= 0:
        return ToolResult(
            tool_name="request_refund_approval",
            status=ToolResultStatus.ERROR,
            error="Invalid refund amount: amount must be a positive number.",
            is_denied=False,
            data=None,
        )

    try:
        # 2. Delegate ownership authorization check to AuthorizationGuard
        decision = auth_guard.check_order_access(customer_id=customer_id, order_id=order_id)
        if not decision.allowed:
            return ToolResult(
                tool_name="request_refund_approval",
                status=ToolResultStatus.DENIED,
                error=decision.message,
                is_denied=True,
                amount=amount if amount >= 0 else None,
                data=None,
            )

        # 3. Retrieve verified order
        order = auth_guard.get_order(order_id.strip() if order_id else "")
        if order is None:
            return ToolResult(
                tool_name="request_refund_approval",
                status=ToolResultStatus.DENIED,
                error="Access denied: requested order does not exist or is unknown.",
                is_denied=True,
                amount=amount,
                data=None,
            )

        # 4. Check that requested refund does not exceed order total
        if amount > order.total_amount:
            return ToolResult(
                tool_name="request_refund_approval",
                status=ToolResultStatus.ERROR,
                error=f"Requested refund amount ({amount:.2f}) exceeds order total ({order.total_amount:.2f}).",
                is_denied=False,
                amount=amount,
                data=None,
            )

        # 5. Create simulated approval request
        clean_reason = reason.strip() if reason and isinstance(reason, str) and reason.strip() else "Customer requested refund"
        simulated_request_id = f"SIM-APPR-{order.order_id}-{int(amount * 100)}"

        request_payload: Dict[str, Any] = {
            "approval_request_id": simulated_request_id,
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "requested_amount": round(amount, 2),
            "currency": order.currency,
            "reason": clean_reason,
            "status": "simulated_approval_pending",
            "simulation_notice": "SIMULATION ONLY: No actual monetary transaction or refund was executed.",
        }

        return ToolResult(
            tool_name="request_refund_approval",
            status=ToolResultStatus.SUCCESS,
            data=request_payload,
            amount=round(amount, 2),
            error=None,
            is_denied=False,
        )

    except Exception:
        return ToolResult(
            tool_name="request_refund_approval",
            status=ToolResultStatus.ERROR,
            error="Unexpected error occurred during refund approval request.",
            is_denied=False,
            amount=amount if (amount is not None and amount >= 0) else None,
            data=None,
        )


class SupportTools:
    """Convenience wrapper binding support tools to an AuthorizationGuard instance."""

    def __init__(self, auth_guard: AuthorizationGuard):
        self.auth_guard = auth_guard

    def lookup_order(self, customer_id: Optional[str], order_id: Optional[str]) -> ToolResult:
        """Look up order details with ownership verification."""
        return lookup_order(customer_id=customer_id, order_id=order_id, auth_guard=self.auth_guard)

    def get_refund_policy(self, category: Optional[str] = None) -> ToolResult:
        """Retrieve fixed synthetic refund policy."""
        return get_refund_policy(category=category)

    def request_refund_approval(
        self,
        customer_id: Optional[str],
        order_id: Optional[str],
        amount: Optional[float],
        reason: Optional[str] = None,
    ) -> ToolResult:
        """Create a simulated refund approval request with ownership verification."""
        return request_refund_approval(
            customer_id=customer_id,
            order_id=order_id,
            amount=amount,
            reason=reason,
            auth_guard=self.auth_guard,
        )
