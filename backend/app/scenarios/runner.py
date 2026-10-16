"""Scenario execution runner for AgentShield.

Executes deterministic security scenarios through the ReferenceAgent,
captures execution traces, and records expected versus actual outcomes.
Never treats runner-level errors or incomplete executions as security passes.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Callable, Iterable, List, Optional
from app.agent import BaseAgent, ReferenceAgent
from app.models import (
    Customer,
    CustomerStatus,
    ExecutionStatus,
    Order,
    OrderStatus,
    Scenario,
    ScenarioCategory,
    ScenarioExecutionStatus,
    ScenarioResult,
    SuiteExecutionResult,
)
from app.scenarios.registry import ScenarioRegistry, get_default_registry
from app.security import AuthorizationGuard
from app.tools import SupportTools


def create_default_reference_agent() -> ReferenceAgent:
    """Create a fresh ReferenceAgent with canonical synthetic test data."""
    alice = Customer(
        customer_id="alice",
        name="Alice Smith",
        email="alice@example.com",
        status=CustomerStatus.ACTIVE,
    )
    bob = Customer(
        customer_id="bob",
        name="Bob Jones",
        email="bob@example.com",
        status=CustomerStatus.ACTIVE,
    )
    order_a100 = Order(
        order_id="A-100",
        customer_id="alice",
        status=OrderStatus.SHIPPED,
        total_amount=129.99,
        currency="USD",
        items=["Wireless Noise-Canceling Headphones"],
        notes="Leave package on front porch.",
    )
    order_b200 = Order(
        order_id="B-200",
        customer_id="bob",
        status=OrderStatus.PROCESSING,
        total_amount=249.50,
        currency="USD",
        items=["Ergonomic Mechanical Keyboard", "USB-C Cable"],
        notes="Sensitive order: handle with priority.",
    )
    guard = AuthorizationGuard(
        orders={"A-100": order_a100, "B-200": order_b200},
        customers={"alice": alice, "bob": bob},
    )
    tools = SupportTools(guard)
    return ReferenceAgent(tools)


class ScenarioRunner:
    """Deterministic runner for evaluating security scenarios against an agent."""

    def __init__(
        self,
        agent: Optional[BaseAgent] = None,
        agent_factory: Optional[Callable[[], BaseAgent]] = None,
    ):
        """Initialize the runner with an agent instance or factory.

        Args:
            agent: Pre-configured agent instance. If None and agent_factory is None,
                   a fresh default ReferenceAgent with synthetic data is created.
            agent_factory: Optional callable returning a fresh BaseAgent per run.
        """
        self._agent_factory = agent_factory
        if agent is not None:
            self._agent = agent
        elif agent_factory is not None:
            self._agent = agent_factory()
        else:
            self._agent = create_default_reference_agent()

    @property
    def agent(self) -> BaseAgent:
        """Return the current agent instance used by the runner."""
        return self._agent

    def get_fresh_agent(self) -> BaseAgent:
        """Return a fresh agent instance if factory is configured, or current agent."""
        if self._agent_factory is not None:
            return self._agent_factory()
        return self._agent

    def run_scenario(self, scenario: Scenario) -> ScenarioResult:
        """Execute a single scenario through the agent and capture trace evidence.

        Fails closed on unexpected exceptions: any unhandled error is recorded as
        ERROR execution status and never treated as a successful security outcome.

        Args:
            scenario: The Scenario definition to execute.

        Returns:
            ScenarioResult containing expected behavior, actual outcome, and trace.
        """
        started_at = datetime.now(timezone.utc).isoformat()
        start_time = time.perf_counter()

        actual_status: Optional[ExecutionStatus] = None
        execution_status: ScenarioExecutionStatus = ScenarioExecutionStatus.ERROR
        agent_response = None
        error_message: Optional[str] = None

        try:
            agent = self.get_fresh_agent()
            agent_response = agent.execute(scenario.request)
            actual_status = agent_response.status
            execution_status = ScenarioExecutionStatus.COMPLETED
        except Exception as exc:
            # Handle unexpected exceptions safely without treating them as passes
            actual_status = ExecutionStatus.ERROR
            execution_status = ScenarioExecutionStatus.ERROR
            error_message = f"Runner caught unexpected exception ({type(exc).__name__}): {str(exc)}"
            agent_response = None

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        completed_at = datetime.now(timezone.utc).isoformat()

        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            category=scenario.category,
            expected_behavior=scenario.expected_behavior,
            actual_status=actual_status,
            execution_status=execution_status,
            agent_response=agent_response,
            error_message=error_message,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )

    def run_scenarios(
        self,
        scenarios: Iterable[Scenario],
        run_id: Optional[str] = None,
    ) -> SuiteExecutionResult:
        """Execute multiple scenarios in predictable, deterministic sequence.

        Args:
            scenarios: Iterable of Scenario definitions to execute.
            run_id: Optional identifier for the run session.

        Returns:
            SuiteExecutionResult containing ordered individual results.
        """
        started_at = datetime.now(timezone.utc).isoformat()
        resolved_run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        results: List[ScenarioResult] = []

        for scenario in scenarios:
            result = self.run_scenario(scenario)
            results.append(result)

        completed_at = datetime.now(timezone.utc).isoformat()

        return SuiteExecutionResult(
            run_id=resolved_run_id,
            results=results,
            started_at=started_at,
            completed_at=completed_at,
        )

    def run_all(
        self,
        registry: Optional[ScenarioRegistry] = None,
        run_id: Optional[str] = None,
    ) -> SuiteExecutionResult:
        """Execute all scenarios in the registry in deterministic order.

        Args:
            registry: ScenarioRegistry to draw scenarios from (defaults to global registry).
            run_id: Optional identifier for the run session.

        Returns:
            SuiteExecutionResult containing results for all scenarios.
        """
        reg = registry or get_default_registry()
        return self.run_scenarios(reg.list_all(), run_id=run_id)

    def run_by_id(
        self,
        scenario_id: str,
        registry: Optional[ScenarioRegistry] = None,
    ) -> ScenarioResult:
        """Look up a scenario by ID and execute it.

        Raises:
            KeyError: If scenario_id is not found in the registry.
        """
        reg = registry or get_default_registry()
        scenario = reg.get_or_raise(scenario_id)
        return self.run_scenario(scenario)

    def run_by_category(
        self,
        category: ScenarioCategory,
        registry: Optional[ScenarioRegistry] = None,
        run_id: Optional[str] = None,
    ) -> SuiteExecutionResult:
        """Execute all scenarios belonging to a specific category.

        Args:
            category: ScenarioCategory to filter by.
            registry: Optional ScenarioRegistry (defaults to global registry).
            run_id: Optional run session identifier.

        Returns:
            SuiteExecutionResult containing results for matched scenarios.
        """
        reg = registry or get_default_registry()
        matching = reg.filter_by_category(category)
        return self.run_scenarios(matching, run_id=run_id)
