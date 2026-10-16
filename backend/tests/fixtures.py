"""Test fixtures for AgentShield evaluation models.

These fixtures provide isolated synthetic data for testing, keeping test data
strictly decoupled from production model definitions.
"""

from app.agent import ReferenceAgent
from app.models import Customer, CustomerStatus, Order, OrderStatus, ToolResult, ToolResultStatus
from app.security import AuthorizationGuard
from app.tools import SupportTools


def get_alice_customer() -> Customer:
    """Return a fresh instance of synthetic customer Alice."""
    return Customer(
        customer_id="alice",
        name="Alice Smith",
        email="alice@example.com",
        status=CustomerStatus.ACTIVE,
    )


def get_bob_customer() -> Customer:
    """Return a fresh instance of synthetic customer Bob."""
    return Customer(
        customer_id="bob",
        name="Bob Jones",
        email="bob@example.com",
        status=CustomerStatus.ACTIVE,
    )


def get_order_a100() -> Order:
    """Return a fresh instance of fictional order A-100 owned by Alice."""
    return Order(
        order_id="A-100",
        customer_id="alice",
        status=OrderStatus.SHIPPED,
        total_amount=129.99,
        currency="USD",
        items=["Wireless Noise-Canceling Headphones"],
        notes="Leave package on front porch.",
    )


def get_order_b200() -> Order:
    """Return a fresh instance of fictional order B-200 owned by Bob."""
    return Order(
        order_id="B-200",
        customer_id="bob",
        status=OrderStatus.PROCESSING,
        total_amount=249.50,
        currency="USD",
        items=["Ergonomic Mechanical Keyboard", "USB-C Cable"],
        notes="Sensitive order: handle with priority.",
    )


def get_successful_tool_result() -> ToolResult:
    """Return a valid successful tool result for order lookup."""
    return ToolResult(
        tool_name="lookup_order",
        status=ToolResultStatus.SUCCESS,
        data={
            "order_id": "A-100",
            "customer_id": "alice",
            "status": "shipped",
            "total_amount": 129.99,
        },
    )


def get_denied_tool_result() -> ToolResult:
    """Return a valid authorization-denied tool result."""
    return ToolResult(
        tool_name="lookup_order",
        status=ToolResultStatus.DENIED,
        error="Access denied: customer 'alice' is not authorized to access order 'B-200' owned by 'bob'",
        is_denied=True,
    )


def get_refund_tool_result() -> ToolResult:
    """Return a valid tool result with an associated monetary amount."""
    return ToolResult(
        tool_name="request_refund_approval",
        status=ToolResultStatus.SUCCESS,
        data={"approval_id": "APPR-1001", "order_id": "A-100"},
        amount=50.0,
    )


def get_test_auth_guard() -> AuthorizationGuard:
    """Return an AuthorizationGuard pre-configured with synthetic Alice and Bob data."""
    return AuthorizationGuard(
        orders={
            "A-100": get_order_a100(),
            "B-200": get_order_b200(),
        },
        customers={
            "alice": get_alice_customer(),
            "bob": get_bob_customer(),
        },
    )


def get_test_support_tools() -> SupportTools:
    """Return a SupportTools instance bound to the test AuthorizationGuard."""
    return SupportTools(get_test_auth_guard())


def get_test_reference_agent() -> ReferenceAgent:
    """Return a ReferenceAgent configured with synthetic tools and guard."""
    return ReferenceAgent(get_test_support_tools())


def get_test_scenario_registry() -> "ScenarioRegistry":
    """Return a fresh ScenarioRegistry with default test scenarios."""
    from app.scenarios import create_default_registry
    return create_default_registry()


def get_test_scenario_runner() -> "ScenarioRunner":
    """Return a ScenarioRunner configured with synthetic reference agent."""
    from app.scenarios import ScenarioRunner
    return ScenarioRunner(agent=get_test_reference_agent())


# Static reference instances for direct imports
FIXTURE_CUSTOMER_ALICE = get_alice_customer()
FIXTURE_CUSTOMER_BOB = get_bob_customer()
FIXTURE_ORDER_A100 = get_order_a100()
FIXTURE_ORDER_B200 = get_order_b200()
FIXTURE_TOOL_RESULT_SUCCESS = get_successful_tool_result()
FIXTURE_TOOL_RESULT_DENIED = get_denied_tool_result()
FIXTURE_AUTH_GUARD = get_test_auth_guard()
FIXTURE_SUPPORT_TOOLS = get_test_support_tools()
FIXTURE_REFERENCE_AGENT = get_test_reference_agent()

