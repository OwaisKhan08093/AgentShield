"""Pytest configuration and shared fixtures for AgentShield tests."""

import pytest
from app.models import Customer, Order, ToolResult
from app.security import AuthorizationGuard
from app.tools import SupportTools
from tests.fixtures import (
    get_alice_customer,
    get_bob_customer,
    get_order_a100,
    get_order_b200,
    get_successful_tool_result,
    get_denied_tool_result,
    get_refund_tool_result,
    get_test_auth_guard,
)


@pytest.fixture
def alice_customer() -> Customer:
    """Fixture returning synthetic customer Alice."""
    return get_alice_customer()


@pytest.fixture
def bob_customer() -> Customer:
    """Fixture returning synthetic customer Bob."""
    return get_bob_customer()


@pytest.fixture
def order_a100() -> Order:
    """Fixture returning fictional order A-100 owned by Alice."""
    return get_order_a100()


@pytest.fixture
def order_b200() -> Order:
    """Fixture returning fictional order B-200 owned by Bob."""
    return get_order_b200()


@pytest.fixture
def successful_tool_result() -> ToolResult:
    """Fixture returning a successful tool result."""
    return get_successful_tool_result()


@pytest.fixture
def denied_tool_result() -> ToolResult:
    """Fixture returning an authorization-denied tool result."""
    return get_denied_tool_result()


@pytest.fixture
def refund_tool_result() -> ToolResult:
    """Fixture returning a tool result with non-negative monetary amount."""
    return get_refund_tool_result()


@pytest.fixture
def auth_guard() -> AuthorizationGuard:
    """Fixture returning an AuthorizationGuard pre-configured with synthetic test data."""
    return get_test_auth_guard()


@pytest.fixture
def support_tools(auth_guard: AuthorizationGuard) -> SupportTools:
    """Fixture returning SupportTools bound to test AuthorizationGuard."""
    return SupportTools(auth_guard)
