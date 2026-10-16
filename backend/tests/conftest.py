"""Pytest configuration and shared fixtures for AgentShield tests."""

import pytest
from app.agent import ReferenceAgent
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
    get_test_reference_agent,
    get_test_support_tools,
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


@pytest.fixture
def reference_agent(support_tools: SupportTools) -> ReferenceAgent:
    """Fixture returning a ReferenceAgent bound to test SupportTools."""
    return ReferenceAgent(support_tools)


@pytest.fixture
def scenario_registry():
    """Fixture returning a fresh ScenarioRegistry."""
    from tests.fixtures import get_test_scenario_registry
    return get_test_scenario_registry()


@pytest.fixture
def scenario_runner(reference_agent: ReferenceAgent):
    """Fixture returning a ScenarioRunner bound to the test reference agent."""
    from app.scenarios import ScenarioRunner
    return ScenarioRunner(agent=reference_agent)


@pytest.fixture
def security_evaluator():
    """Fixture returning a fresh SecurityEvaluator instance."""
    from app.evaluator import SecurityEvaluator
    return SecurityEvaluator()


@pytest.fixture
def vulnerable_agent():
    """Fixture returning a deliberately vulnerable test agent for testing violation detection."""
    from tests.fixtures import VulnerableAgent
    return VulnerableAgent()


