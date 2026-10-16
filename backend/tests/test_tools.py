"""Unit tests for secure customer support mock tools."""

import pytest
from app.models import Customer, Order, ToolResult, ToolResultStatus
from app.security import AuthorizationGuard
from app.tools import (
    SYNTHETIC_REFUND_POLICY,
    SupportTools,
    get_refund_policy,
    lookup_order,
    request_refund_approval,
)


# ==============================================================================
# 1. lookup_order: Authorized Success Paths
# ==============================================================================

def test_lookup_order_alice_accessing_a100_success(support_tools: SupportTools):
    """Verify Alice can look up her own order A-100."""
    result = support_tools.lookup_order(customer_id="alice", order_id="A-100")
    assert isinstance(result, ToolResult)
    assert result.status == ToolResultStatus.SUCCESS
    assert result.is_denied is False
    assert result.error is None
    assert result.data is not None
    assert result.data["order_id"] == "A-100"
    assert result.data["customer_id"] == "alice"
    assert result.data["status"] == "shipped"
    assert result.data["total_amount"] == 129.99
    assert result.data["currency"] == "USD"
    assert "Wireless Noise-Canceling Headphones" in result.data["items"]
    assert "front porch" in result.data["notes"]


def test_lookup_order_bob_accessing_b200_success(support_tools: SupportTools):
    """Verify Bob can look up his own order B-200."""
    result = support_tools.lookup_order(customer_id="bob", order_id="B-200")
    assert isinstance(result, ToolResult)
    assert result.status == ToolResultStatus.SUCCESS
    assert result.is_denied is False
    assert result.error is None
    assert result.data is not None
    assert result.data["order_id"] == "B-200"
    assert result.data["customer_id"] == "bob"
    assert result.data["status"] == "processing"
    assert result.data["total_amount"] == 249.50
    assert result.data["currency"] == "USD"
    assert "Ergonomic Mechanical Keyboard" in result.data["items"]


def test_standalone_lookup_order_function(auth_guard: AuthorizationGuard):
    """Verify standalone lookup_order function works identically to class method."""
    result = lookup_order(customer_id="alice", order_id="A-100", auth_guard=auth_guard)
    assert result.status == ToolResultStatus.SUCCESS
    assert result.data["order_id"] == "A-100"


# ==============================================================================
# 2. lookup_order: Cross-Customer Denials and Zero Data Leakage
# ==============================================================================

def test_lookup_order_alice_accessing_bob_b200_denied(
    support_tools: SupportTools,
    bob_customer: Customer,
    order_b200: Order,
):
    """Verify Alice is denied looking up Bob's order B-200 and no Bob data leaks."""
    result = support_tools.lookup_order(customer_id="alice", order_id="B-200")
    assert isinstance(result, ToolResult)
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None
    assert result.error is not None

    # Check zero data leakage
    error_msg = result.error.lower()
    assert "bob" not in error_msg
    assert bob_customer.name.lower() not in error_msg
    assert bob_customer.email.lower() not in error_msg
    for item in order_b200.items:
        assert item.lower() not in error_msg
    if order_b200.notes:
        assert order_b200.notes.lower() not in error_msg


def test_lookup_order_bob_accessing_alice_a100_denied(
    support_tools: SupportTools,
    alice_customer: Customer,
    order_a100: Order,
):
    """Verify Bob is denied looking up Alice's order A-100 and no Alice data leaks."""
    result = support_tools.lookup_order(customer_id="bob", order_id="A-100")
    assert isinstance(result, ToolResult)
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None
    assert result.error is not None

    # Check zero data leakage
    error_msg = result.error.lower()
    assert "alice" not in error_msg
    assert alice_customer.name.lower() not in error_msg
    assert alice_customer.email.lower() not in error_msg
    for item in order_a100.items:
        assert item.lower() not in error_msg
    if order_a100.notes:
        assert order_a100.notes.lower() not in error_msg


# ==============================================================================
# 3. lookup_order: Unknown and Missing Identifiers
# ==============================================================================

def test_lookup_order_unknown_customer(support_tools: SupportTools):
    """Verify unknown customer cannot look up existing orders."""
    result = support_tools.lookup_order(customer_id="unknown_charlie", order_id="A-100")
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None


def test_lookup_order_unknown_order(support_tools: SupportTools):
    """Verify looking up non-existent order is denied safely."""
    result = support_tools.lookup_order(customer_id="alice", order_id="NONEXISTENT-999")
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None


@pytest.mark.parametrize("invalid_customer", [None, "", "   ", "\t\n"])
def test_lookup_order_missing_customer_id(support_tools: SupportTools, invalid_customer: str | None):
    """Verify missing customer identity is denied."""
    result = support_tools.lookup_order(customer_id=invalid_customer, order_id="A-100")
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None


@pytest.mark.parametrize("invalid_order", [None, "", "   ", "\t\n"])
def test_lookup_order_missing_order_id(support_tools: SupportTools, invalid_order: str | None):
    """Verify missing order identifier is denied."""
    result = support_tools.lookup_order(customer_id="alice", order_id=invalid_order)
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None


# ==============================================================================
# 4. get_refund_policy: Public Synthetic Policy
# ==============================================================================

def test_get_refund_policy_default(support_tools: SupportTools):
    """Verify get_refund_policy returns the synthetic policy without requiring identity."""
    result = support_tools.get_refund_policy()
    assert isinstance(result, ToolResult)
    assert result.status == ToolResultStatus.SUCCESS
    assert result.is_denied is False
    assert result.error is None
    assert result.data is not None
    assert result.data["policy_version"] == SYNTHETIC_REFUND_POLICY["policy_version"]
    assert result.data["window_days"] == 30
    assert result.data["requested_category"] == "general"
    assert len(result.data["eligibility_rules"]) > 0


def test_get_refund_policy_with_category(support_tools: SupportTools):
    """Verify category parameter is acknowledged without leaking private data."""
    result = support_tools.get_refund_policy(category="electronics")
    assert result.status == ToolResultStatus.SUCCESS
    assert result.data["requested_category"] == "electronics"


def test_standalone_get_refund_policy():
    """Verify standalone get_refund_policy function works without auth_guard."""
    result = get_refund_policy(category="apparel")
    assert result.status == ToolResultStatus.SUCCESS
    assert result.data["requested_category"] == "apparel"


# ==============================================================================
# 5. request_refund_approval: Valid Simulated Requests
# ==============================================================================

def test_request_refund_approval_alice_a100_success(support_tools: SupportTools):
    """Verify Alice can request a simulated refund for her own order within limits."""
    result = support_tools.request_refund_approval(
        customer_id="alice",
        order_id="A-100",
        amount=50.0,
        reason="Item was not as expected",
    )
    assert isinstance(result, ToolResult)
    assert result.status == ToolResultStatus.SUCCESS
    assert result.is_denied is False
    assert result.error is None
    assert result.amount == 50.0
    assert result.data is not None
    assert result.data["order_id"] == "A-100"
    assert result.data["customer_id"] == "alice"
    assert result.data["requested_amount"] == 50.0
    assert result.data["currency"] == "USD"
    assert result.data["status"] == "simulated_approval_pending"
    assert "SIMULATION ONLY" in result.data["simulation_notice"]


def test_request_refund_approval_full_order_amount_success(support_tools: SupportTools):
    """Verify requesting refund equal to exact total amount succeeds as simulated request."""
    result = support_tools.request_refund_approval(
        customer_id="alice",
        order_id="A-100",
        amount=129.99,
        reason="Defective unit",
    )
    assert result.status == ToolResultStatus.SUCCESS
    assert result.amount == 129.99
    assert result.data["requested_amount"] == 129.99
    assert result.data["status"] == "simulated_approval_pending"


def test_standalone_request_refund_approval_function(auth_guard: AuthorizationGuard):
    """Verify standalone request_refund_approval function works identically."""
    result = request_refund_approval(
        customer_id="bob",
        order_id="B-200",
        amount=100.0,
        reason="Customer requested exchange",
        auth_guard=auth_guard,
    )
    assert result.status == ToolResultStatus.SUCCESS
    assert result.data["order_id"] == "B-200"


# ==============================================================================
# 6. request_refund_approval: Unauthorized and Cross-Customer Rejections
# ==============================================================================

def test_request_refund_approval_alice_for_bob_order_denied(
    support_tools: SupportTools,
    bob_customer: Customer,
    order_b200: Order,
):
    """Verify Alice cannot request a refund for Bob's order B-200."""
    result = support_tools.request_refund_approval(
        customer_id="alice",
        order_id="B-200",
        amount=50.0,
        reason="Unauthorized refund attempt",
    )
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None
    assert result.error is not None

    # Check zero data leakage
    error_msg = result.error.lower()
    assert "bob" not in error_msg
    assert bob_customer.name.lower() not in error_msg
    assert bob_customer.email.lower() not in error_msg


def test_request_refund_approval_bob_for_alice_order_denied(
    support_tools: SupportTools,
    alice_customer: Customer,
    order_a100: Order,
):
    """Verify Bob cannot request a refund for Alice's order A-100."""
    result = support_tools.request_refund_approval(
        customer_id="bob",
        order_id="A-100",
        amount=25.0,
        reason="Unauthorized refund attempt",
    )
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None
    assert result.error is not None

    # Check zero data leakage
    error_msg = result.error.lower()
    assert "alice" not in error_msg
    assert alice_customer.name.lower() not in error_msg


def test_request_refund_approval_unknown_customer_denied(support_tools: SupportTools):
    """Verify unknown customer cannot request refunds."""
    result = support_tools.request_refund_approval(
        customer_id="stranger",
        order_id="A-100",
        amount=20.0,
    )
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None


def test_request_refund_approval_unknown_order_denied(support_tools: SupportTools):
    """Verify refund request for unknown order is denied."""
    result = support_tools.request_refund_approval(
        customer_id="alice",
        order_id="UNKNOWN-777",
        amount=20.0,
    )
    assert result.status == ToolResultStatus.DENIED
    assert result.is_denied is True
    assert result.data is None


# ==============================================================================
# 7. request_refund_approval: Amount Validation and Mock Limits
# ==============================================================================

@pytest.mark.parametrize("invalid_amount", [0.0, -0.01, -50.0, None])
def test_request_refund_approval_non_positive_amount_rejected(
    support_tools: SupportTools,
    invalid_amount: float | None,
):
    """Verify refund request rejects non-positive or missing amounts."""
    result = support_tools.request_refund_approval(
        customer_id="alice",
        order_id="A-100",
        amount=invalid_amount,  # type: ignore[arg-type]
    )
    assert result.status == ToolResultStatus.ERROR
    assert result.data is None
    assert "positive" in result.error.lower()


def test_request_refund_approval_amount_exceeding_total_rejected(support_tools: SupportTools):
    """Verify refund request is rejected when requested amount exceeds order total."""
    # Order A-100 total is 129.99; requesting 200.0 must be rejected
    result = support_tools.request_refund_approval(
        customer_id="alice",
        order_id="A-100",
        amount=200.0,
    )
    assert result.status == ToolResultStatus.ERROR
    assert result.data is None
    assert "exceeds order total" in result.error.lower()


# ==============================================================================
# 8. Fail-Closed Error Handling
# ==============================================================================

def test_lookup_order_fails_closed_on_guard_exception():
    """Verify lookup_order fails closed if an unexpected exception occurs."""
    def broken_lookup(order_id: str):
        raise RuntimeError("Network split simulation")

    guard = AuthorizationGuard(
        orders={},
        customers={},
        order_lookup=broken_lookup,
    )
    tools = SupportTools(guard)

    result = tools.lookup_order(customer_id="alice", order_id="A-100")
    assert result.status in (ToolResultStatus.DENIED, ToolResultStatus.ERROR)
    assert result.status != ToolResultStatus.SUCCESS
    assert result.data is None


def test_request_refund_approval_missing_guard():
    """Verify request_refund_approval fails safely if no auth_guard is provided."""
    result = request_refund_approval(
        customer_id="alice",
        order_id="A-100",
        amount=25.0,
        auth_guard=None,
    )
    assert result.status == ToolResultStatus.ERROR
    assert result.data is None


# ==============================================================================
# 9. ToolResult Serialization Roundtrip
# ==============================================================================

def test_tool_results_serialization(support_tools: SupportTools):
    """Verify tool results are valid Pydantic models that serialize cleanly."""
    success_res = support_tools.lookup_order("alice", "A-100")
    denied_res = support_tools.lookup_order("alice", "B-200")
    policy_res = support_tools.get_refund_policy()

    for res in [success_res, denied_res, policy_res]:
        dumped = res.model_dump()
        reconstituted = ToolResult.model_validate(dumped)
        assert reconstituted == res
