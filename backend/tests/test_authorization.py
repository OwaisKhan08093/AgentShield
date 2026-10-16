"""Unit tests for tool-level resource authorization guard."""

import pytest
from pydantic import ValidationError

from app.models import Customer, CustomerStatus, Order, OrderStatus
from app.security import (
    AuthReasonCode,
    AuthorizationDecision,
    AuthorizationGuard,
)


# ==============================================================================
# 1. Core Ownership and Allowed Paths
# ==============================================================================

def test_alice_accessing_own_order_a100_allowed(auth_guard: AuthorizationGuard):
    """Verify that Alice is authorized to access her own order A-100."""
    decision = auth_guard.check_order_access(customer_id="alice", order_id="A-100")
    assert decision.allowed is True
    assert decision.reason_code == AuthReasonCode.ALLOWED
    assert decision.customer_id == "alice"
    assert decision.order_id == "A-100"
    assert "granted" in decision.message.lower()


def test_bob_accessing_own_order_b200_allowed(auth_guard: AuthorizationGuard):
    """Verify that Bob is authorized to access his own order B-200."""
    decision = auth_guard.check_order_access(customer_id="bob", order_id="B-200")
    assert decision.allowed is True
    assert decision.reason_code == AuthReasonCode.ALLOWED
    assert decision.customer_id == "bob"
    assert decision.order_id == "B-200"
    assert "granted" in decision.message.lower()


def test_direct_model_instance_access_allowed(
    auth_guard: AuthorizationGuard,
    alice_customer: Customer,
    order_a100: Order,
):
    """Verify authorization succeeds when passing Customer and Order objects directly."""
    decision = auth_guard.check_order_access(customer=alice_customer, order=order_a100)
    assert decision.allowed is True
    assert decision.reason_code == AuthReasonCode.ALLOWED
    assert decision.customer_id == "alice"
    assert decision.order_id == "A-100"


# ==============================================================================
# 2. Cross-Customer Access and Data Leakage Prevention (Crucial Security Property)
# ==============================================================================

def test_alice_accessing_bob_order_b200_denied(
    auth_guard: AuthorizationGuard,
    bob_customer: Customer,
    order_b200: Order,
):
    """Verify Alice is denied access to Bob's order B-200 without leaking Bob's data."""
    decision = auth_guard.check_order_access(customer_id="alice", order_id="B-200")
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.OWNERSHIP_MISMATCH

    # Verify no sensitive or identifiable details from Bob or order B-200 are leaked
    msg = decision.message.lower()
    assert "bob" not in msg
    assert bob_customer.name.lower() not in msg
    assert bob_customer.email.lower() not in msg
    for item in order_b200.items:
        assert item.lower() not in msg
    if order_b200.notes:
        assert order_b200.notes.lower() not in msg


def test_bob_accessing_alice_order_a100_denied(
    auth_guard: AuthorizationGuard,
    alice_customer: Customer,
    order_a100: Order,
):
    """Verify Bob is denied access to Alice's order A-100 without leaking Alice's data."""
    decision = auth_guard.check_order_access(customer_id="bob", order_id="A-100")
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.OWNERSHIP_MISMATCH

    # Verify no sensitive details from Alice or order A-100 are leaked
    msg = decision.message.lower()
    assert "alice" not in msg
    assert alice_customer.name.lower() not in msg
    assert alice_customer.email.lower() not in msg
    for item in order_a100.items:
        assert item.lower() not in msg
    if order_a100.notes:
        assert order_a100.notes.lower() not in msg


def test_direct_model_instance_cross_customer_denied(
    auth_guard: AuthorizationGuard,
    alice_customer: Customer,
    order_b200: Order,
):
    """Verify cross-customer check fails when passing model objects directly."""
    decision = auth_guard.check_order_access(customer=alice_customer, order=order_b200)
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.OWNERSHIP_MISMATCH


# ==============================================================================
# 3. Unknown Customer and Unknown Order Tests
# ==============================================================================

def test_unknown_customer_denied(auth_guard: AuthorizationGuard):
    """Verify that an unknown customer identity cannot access existing orders."""
    decision = auth_guard.check_order_access(customer_id="charlie", order_id="A-100")
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.CUSTOMER_NOT_FOUND
    assert "alice" not in decision.message.lower()


def test_unknown_order_denied(auth_guard: AuthorizationGuard):
    """Verify that accessing a non-existent order ID is safely denied."""
    decision = auth_guard.check_order_access(customer_id="alice", order_id="NONEXISTENT-999")
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.ORDER_NOT_FOUND
    assert decision.order_id == "NONEXISTENT-999"


def test_unknown_customer_and_unknown_order_denied(auth_guard: AuthorizationGuard):
    """Verify denial when both customer and order are unknown."""
    decision = auth_guard.check_order_access(customer_id="unknown_user", order_id="UNKNOWN-000")
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.CUSTOMER_NOT_FOUND


# ==============================================================================
# 4. Missing or Blank Identifiers
# ==============================================================================

@pytest.mark.parametrize("invalid_customer", [None, "", "   ", "\t\n"])
def test_missing_or_blank_customer_id_denied(
    auth_guard: AuthorizationGuard,
    invalid_customer: str | None,
):
    """Verify missing or whitespace customer_id is rejected safely."""
    decision = auth_guard.check_order_access(customer_id=invalid_customer, order_id="A-100")
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.INVALID_IDENTITY


@pytest.mark.parametrize("invalid_order", [None, "", "   ", "\t\n"])
def test_missing_or_blank_order_id_denied(
    auth_guard: AuthorizationGuard,
    invalid_order: str | None,
):
    """Verify missing or whitespace order_id is rejected safely."""
    decision = auth_guard.check_order_access(customer_id="alice", order_id=invalid_order)
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.INVALID_ORDER_ID


def test_both_identifiers_missing_denied(auth_guard: AuthorizationGuard):
    """Verify that providing no identifiers is safely denied."""
    decision = auth_guard.check_order_access(customer_id=None, order_id=None)
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.INVALID_IDENTITY


# ==============================================================================
# 5. Customer Status Checks (Suspended / Inactive Accounts)
# ==============================================================================

def test_suspended_customer_denied_access(auth_guard: AuthorizationGuard):
    """Verify a suspended customer cannot access even their own order."""
    suspended_alice = Customer(
        customer_id="alice",
        name="Alice Smith",
        status=CustomerStatus.SUSPENDED,
    )
    decision = auth_guard.check_order_access(customer=suspended_alice, order_id="A-100")
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.CUSTOMER_INACTIVE


def test_inactive_customer_denied_access(auth_guard: AuthorizationGuard):
    """Verify an inactive customer cannot access even their own order."""
    inactive_bob = Customer(
        customer_id="bob",
        name="Bob Jones",
        status=CustomerStatus.INACTIVE,
    )
    decision = auth_guard.check_order_access(customer=inactive_bob, order_id="B-200")
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.CUSTOMER_INACTIVE


# ==============================================================================
# 6. Fail-Closed on Unexpected Errors
# ==============================================================================

def test_guard_fails_closed_on_lookup_exception():
    """Verify the authorization guard never grants access when an internal error occurs."""
    def buggy_order_lookup(order_id: str):
        raise RuntimeError("Database connection timed out")

    guard = AuthorizationGuard(
        orders={},
        customers={"alice": Customer(customer_id="alice", name="Alice Smith")},
        order_lookup=buggy_order_lookup,
    )

    decision = guard.check_order_access(customer_id="alice", order_id="A-100")
    assert decision.allowed is False
    assert decision.reason_code == AuthReasonCode.AUTHORIZATION_ERROR
    assert "failure" in decision.message.lower()


# ==============================================================================
# 7. Dynamic Registration and Repository Methods
# ==============================================================================

def test_guard_dynamic_registration():
    """Verify orders and customers can be registered dynamically."""
    guard = AuthorizationGuard()

    cust = Customer(customer_id="charlie", name="Charlie Brown")
    order = Order(
        order_id="C-300",
        customer_id="charlie",
        status=OrderStatus.PENDING,
        total_amount=75.0,
    )

    guard.register_customer(cust)
    guard.register_order(order)

    assert guard.get_customer("charlie") == cust
    assert guard.get_order("C-300") == order

    decision = guard.check_order_access(customer_id="charlie", order_id="C-300")
    assert decision.allowed is True
    assert decision.reason_code == AuthReasonCode.ALLOWED


# ==============================================================================
# 8. Immutability and Serialization
# ==============================================================================

def test_authorization_decision_immutability(auth_guard: AuthorizationGuard):
    """Verify that AuthorizationDecision instances are frozen and tamper-proof."""
    decision = auth_guard.check_order_access(customer_id="alice", order_id="A-100")
    with pytest.raises(ValidationError):
        decision.allowed = False  # type: ignore[misc]


def test_authorization_decision_serialization(auth_guard: AuthorizationGuard):
    """Verify AuthorizationDecision serializes and deserializes losslessly."""
    decision = auth_guard.check_order_access(customer_id="alice", order_id="A-100")
    dumped = decision.model_dump()
    restored = AuthorizationDecision.model_validate(dumped)
    assert restored == decision
    assert restored.allowed is True
    assert restored.reason_code == AuthReasonCode.ALLOWED
