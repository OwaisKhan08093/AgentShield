"""Unit tests for AgentShield core evaluation data models."""

import pytest
from pydantic import ValidationError

from app.models import (
    Customer,
    CustomerStatus,
    Order,
    OrderStatus,
    ToolResult,
    ToolResultStatus,
)
from tests.fixtures import (
    FIXTURE_CUSTOMER_ALICE,
    FIXTURE_CUSTOMER_BOB,
    FIXTURE_ORDER_A100,
    FIXTURE_ORDER_B200,
    FIXTURE_TOOL_RESULT_SUCCESS,
    FIXTURE_TOOL_RESULT_DENIED,
)


# ==============================================================================
# 1. Valid Object Creation and Fixture Tests
# ==============================================================================

def test_valid_customer_alice(alice_customer: Customer):
    """Verify synthetic customer Alice fixture instantiates correctly."""
    assert alice_customer.customer_id == "alice"
    assert alice_customer.name == "Alice Smith"
    assert alice_customer.email == "alice@example.com"
    assert alice_customer.status == CustomerStatus.ACTIVE


def test_valid_customer_bob(bob_customer: Customer):
    """Verify synthetic customer Bob fixture instantiates correctly."""
    assert bob_customer.customer_id == "bob"
    assert bob_customer.name == "Bob Jones"
    assert bob_customer.email == "bob@example.com"
    assert bob_customer.status == CustomerStatus.ACTIVE


def test_valid_order_a100(order_a100: Order):
    """Verify fictional order A-100 fixture instantiates correctly."""
    assert order_a100.order_id == "A-100"
    assert order_a100.customer_id == "alice"
    assert order_a100.status == OrderStatus.SHIPPED
    assert order_a100.total_amount == 129.99
    assert order_a100.currency == "USD"
    assert len(order_a100.items) == 1
    assert "Wireless Noise-Canceling Headphones" in order_a100.items


def test_valid_order_b200(order_b200: Order):
    """Verify fictional order B-200 fixture instantiates correctly."""
    assert order_b200.order_id == "B-200"
    assert order_b200.customer_id == "bob"
    assert order_b200.status == OrderStatus.PROCESSING
    assert order_b200.total_amount == 249.50
    assert order_b200.currency == "USD"
    assert len(order_b200.items) == 2


def test_ownership_mapping_in_fixtures():
    """Verify ownership relationship between test customers and orders."""
    assert FIXTURE_ORDER_A100.customer_id == FIXTURE_CUSTOMER_ALICE.customer_id
    assert FIXTURE_ORDER_B200.customer_id == FIXTURE_CUSTOMER_BOB.customer_id
    assert FIXTURE_ORDER_A100.customer_id != FIXTURE_ORDER_B200.customer_id


def test_valid_tool_result_success(successful_tool_result: ToolResult):
    """Verify successful tool result structure and defaults."""
    assert successful_tool_result.tool_name == "lookup_order"
    assert successful_tool_result.status == ToolResultStatus.SUCCESS
    assert successful_tool_result.data is not None
    assert successful_tool_result.data["order_id"] == "A-100"
    assert successful_tool_result.error is None
    assert successful_tool_result.is_denied is False


def test_valid_tool_result_denied(denied_tool_result: ToolResult):
    """Verify authorization-denied tool result structure and flags."""
    assert denied_tool_result.tool_name == "lookup_order"
    assert denied_tool_result.status == ToolResultStatus.DENIED
    assert denied_tool_result.error is not None
    assert "Access denied" in denied_tool_result.error
    assert denied_tool_result.is_denied is True


def test_valid_tool_result_with_amount(refund_tool_result: ToolResult):
    """Verify tool result with valid non-negative amount."""
    assert refund_tool_result.tool_name == "request_refund_approval"
    assert refund_tool_result.status == ToolResultStatus.SUCCESS
    assert refund_tool_result.amount == 50.0


def test_tool_result_auto_sync_denied_flag():
    """Verify is_denied is automatically set to True when status is DENIED."""
    result = ToolResult(
        tool_name="lookup_order",
        status=ToolResultStatus.DENIED,
        error="Blocked by policy",
    )
    assert result.is_denied is True


# ==============================================================================
# 2. Missing Required Fields Validation
# ==============================================================================

def test_customer_missing_customer_id():
    """Verify Customer requires customer_id."""
    with pytest.raises(ValidationError) as exc_info:
        Customer(name="Alice")  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("customer_id",) and err["type"] == "missing" for err in errors)


def test_customer_missing_name():
    """Verify Customer requires name."""
    with pytest.raises(ValidationError) as exc_info:
        Customer(customer_id="alice")  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("name",) and err["type"] == "missing" for err in errors)


def test_order_missing_order_id():
    """Verify Order requires order_id."""
    with pytest.raises(ValidationError) as exc_info:
        Order(customer_id="alice", total_amount=100.0)  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("order_id",) and err["type"] == "missing" for err in errors)


def test_order_missing_customer_id():
    """Verify Order requires customer_id."""
    with pytest.raises(ValidationError) as exc_info:
        Order(order_id="A-100", total_amount=100.0)  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("customer_id",) and err["type"] == "missing" for err in errors)


def test_order_missing_total_amount():
    """Verify Order requires total_amount."""
    with pytest.raises(ValidationError) as exc_info:
        Order(order_id="A-100", customer_id="alice")  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("total_amount",) and err["type"] == "missing" for err in errors)


def test_tool_result_missing_tool_name():
    """Verify ToolResult requires tool_name."""
    with pytest.raises(ValidationError) as exc_info:
        ToolResult(status=ToolResultStatus.SUCCESS)  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("tool_name",) and err["type"] == "missing" for err in errors)


def test_tool_result_missing_status():
    """Verify ToolResult requires status."""
    with pytest.raises(ValidationError) as exc_info:
        ToolResult(tool_name="lookup_order")  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("status",) and err["type"] == "missing" for err in errors)


# ==============================================================================
# 3. Empty / Whitespace Required Identifier Validation
# ==============================================================================

@pytest.mark.parametrize("empty_val", ["", "   ", "\t\n"])
def test_customer_empty_identifiers(empty_val: str):
    """Verify Customer rejects empty or whitespace-only customer_id or name."""
    with pytest.raises(ValidationError):
        Customer(customer_id=empty_val, name="Alice")
    with pytest.raises(ValidationError):
        Customer(customer_id="alice", name=empty_val)


@pytest.mark.parametrize("empty_val", ["", "   ", "\t\n"])
def test_order_empty_identifiers(empty_val: str):
    """Verify Order rejects empty or whitespace-only order_id or customer_id."""
    with pytest.raises(ValidationError):
        Order(order_id=empty_val, customer_id="alice", total_amount=50.0)
    with pytest.raises(ValidationError):
        Order(order_id="A-100", customer_id=empty_val, total_amount=50.0)


@pytest.mark.parametrize("empty_val", ["", "   ", "\t\n"])
def test_tool_result_empty_tool_name(empty_val: str):
    """Verify ToolResult rejects empty or whitespace-only tool_name."""
    with pytest.raises(ValidationError):
        ToolResult(tool_name=empty_val, status=ToolResultStatus.SUCCESS)


# ==============================================================================
# 4. Invalid Status Values Validation
# ==============================================================================

@pytest.mark.parametrize("invalid_status", ["banned", "deleted", "ACTIVE_STATE", ""])
def test_customer_invalid_status(invalid_status: str):
    """Verify Customer rejects unpermitted status values."""
    with pytest.raises(ValidationError):
        Customer(customer_id="alice", name="Alice", status=invalid_status)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_status", ["in_transit", "lost", "UNKNOWN", ""])
def test_order_invalid_status(invalid_status: str):
    """Verify Order rejects unpermitted status values."""
    with pytest.raises(ValidationError):
        Order(
            order_id="A-100",
            customer_id="alice",
            status=invalid_status,  # type: ignore[arg-type]
            total_amount=50.0,
        )


@pytest.mark.parametrize("invalid_status", ["aborted", "pending", "FAILED", ""])
def test_tool_result_invalid_status(invalid_status: str):
    """Verify ToolResult rejects unpermitted status values."""
    with pytest.raises(ValidationError):
        ToolResult(tool_name="lookup_order", status=invalid_status)  # type: ignore[arg-type]


# ==============================================================================
# 5. Non-Negative Monetary Values Validation
# ==============================================================================

@pytest.mark.parametrize("negative_amount", [-0.01, -1.0, -999.99])
def test_order_negative_amount_rejected(negative_amount: float):
    """Verify Order rejects negative total_amount values."""
    with pytest.raises(ValidationError) as exc_info:
        Order(order_id="A-100", customer_id="alice", total_amount=negative_amount)
    errors = exc_info.value.errors()
    assert any("total_amount" in err["loc"] for err in errors)


def test_order_zero_amount_accepted():
    """Verify Order accepts zero monetary value ($0.00 is non-negative)."""
    order = Order(order_id="A-100", customer_id="alice", total_amount=0.0)
    assert order.total_amount == 0.0


@pytest.mark.parametrize("negative_amount", [-0.01, -5.0, -100.0])
def test_tool_result_negative_amount_rejected(negative_amount: float):
    """Verify ToolResult rejects negative optional amount."""
    with pytest.raises(ValidationError) as exc_info:
        ToolResult(
            tool_name="request_refund_approval",
            status=ToolResultStatus.SUCCESS,
            amount=negative_amount,
        )
    errors = exc_info.value.errors()
    assert any("amount" in err["loc"] for err in errors)


def test_tool_result_zero_amount_accepted():
    """Verify ToolResult accepts zero monetary value."""
    result = ToolResult(
        tool_name="request_refund_approval",
        status=ToolResultStatus.SUCCESS,
        amount=0.0,
    )
    assert result.amount == 0.0


# ==============================================================================
# 6. Extra Fields Rejection (Strict Schema Enforcement)
# ==============================================================================

def test_customer_rejects_extra_fields():
    """Verify Customer rejects undeclared extra fields."""
    with pytest.raises(ValidationError):
        Customer(
            customer_id="alice",
            name="Alice",
            status=CustomerStatus.ACTIVE,
            unexpected_field="disallowed",  # type: ignore[call-arg]
        )


def test_order_rejects_extra_fields():
    """Verify Order rejects undeclared extra fields."""
    with pytest.raises(ValidationError):
        Order(
            order_id="A-100",
            customer_id="alice",
            total_amount=10.0,
            unexpected_field="disallowed",  # type: ignore[call-arg]
        )


def test_tool_result_rejects_extra_fields():
    """Verify ToolResult rejects undeclared extra fields."""
    with pytest.raises(ValidationError):
        ToolResult(
            tool_name="lookup_order",
            status=ToolResultStatus.SUCCESS,
            unexpected_field="disallowed",  # type: ignore[call-arg]
        )


# ==============================================================================
# 7. Serialization and Roundtrip
# ==============================================================================

def test_models_serialization_roundtrip(
    alice_customer: Customer,
    order_a100: Order,
    successful_tool_result: ToolResult,
):
    """Verify that models serialize to dict/JSON and deserialize losslessly."""
    # Customer
    customer_dict = alice_customer.model_dump()
    reconstituted_customer = Customer.model_validate(customer_dict)
    assert reconstituted_customer == alice_customer

    # Order
    order_dict = order_a100.model_dump()
    reconstituted_order = Order.model_validate(order_dict)
    assert reconstituted_order == order_a100

    # ToolResult
    tool_dict = successful_tool_result.model_dump()
    reconstituted_tool = ToolResult.model_validate(tool_dict)
    assert reconstituted_tool == successful_tool_result
