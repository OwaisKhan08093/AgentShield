"""Unit tests for deterministic ScenarioRunner and structured results."""

from typing import Any, Dict, Union
import pytest

from app.agent.base import BaseAgent
from app.models import (
    AgentResponse,
    ExecutionStatus,
    ExecutionTrace,
    ExpectedBehavior,
    RiskLevel,
    Scenario,
    ScenarioCategory,
    ScenarioExecutionStatus,
    ScenarioResult,
    SuiteExecutionResult,
    SupportRequest,
)
from app.scenarios import (
    ScenarioRegistry,
    ScenarioRunner,
    create_default_registry,
    get_scenario,
    list_scenarios,
)


# ==============================================================================
# 1. Individual Scenario Execution Tests
# ==============================================================================

def test_runner_executes_positive_control_scenario(scenario_runner: ScenarioRunner):
    """Verify executing positive-control scenario yields SUCCESS and matching status."""
    scenario = get_scenario("BENIGN-ORDER-LOOKUP-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)

    assert isinstance(result, ScenarioResult)
    assert result.scenario_id == "BENIGN-ORDER-LOOKUP-001"
    assert result.scenario_name == "Authorized Order Lookup (Positive Control)"
    assert result.category == ScenarioCategory.BENIGN_TASK
    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.SUCCESS
    assert result.matches_expected_status is True
    assert result.error_message is None
    assert result.duration_ms >= 0.0

    # Verify AgentResponse and ExecutionTrace are preserved
    assert result.agent_response is not None
    assert result.agent_response.status == ExecutionStatus.SUCCESS
    assert result.execution_trace is not None
    assert isinstance(result.execution_trace, ExecutionTrace)
    assert result.execution_trace.customer_id == "alice"
    assert len(result.execution_trace.events) == 4


def test_runner_executes_cross_customer_denial_scenario(scenario_runner: ScenarioRunner):
    """Verify executing unauthorized cross-customer scenario records DENIED status."""
    scenario = get_scenario("AUTHZ-CROSS-ORDER-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)

    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.DENIED
    assert result.matches_expected_status is True

    # Trace must document the authorization denial
    trace = result.execution_trace
    assert trace is not None
    assert trace.status == ExecutionStatus.DENIED
    denial_events = [e for e in trace.events if e.is_denied]
    assert len(denial_events) >= 1

    # Verify no Bob secrets exposed in result data or summary
    assert result.agent_response is not None
    assert result.agent_response.data is None
    assert "bob" not in result.agent_response.summary.lower()


def test_runner_executes_unauthorized_refund_scenario(scenario_runner: ScenarioRunner):
    """Verify unauthorized refund-approval scenario records DENIED outcome."""
    scenario = get_scenario("AUTHZ-CROSS-REFUND-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)

    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.DENIED
    assert result.matches_expected_status is True
    assert result.agent_response is not None
    assert result.agent_response.data is None


def test_runner_executes_unknown_customer_scenario(scenario_runner: ScenarioRunner):
    """Verify unknown customer attempting order access is blocked and recorded."""
    scenario = get_scenario("AUTHZ-UNKNOWN-CUSTOMER-ORDER-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)

    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.DENIED
    assert result.matches_expected_status is True


def test_runner_executes_unknown_order_scenario(scenario_runner: ScenarioRunner):
    """Verify lookup of unknown/nonexistent order is safely denied."""
    scenario = get_scenario("AUTHZ-UNKNOWN-ORDER-LOOKUP-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)

    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.DENIED
    assert result.matches_expected_status is True


def test_runner_executes_valid_simulated_refund(scenario_runner: ScenarioRunner):
    """Verify valid simulated refund approval request succeeds."""
    scenario = get_scenario("BENIGN-REFUND-APPROVAL-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)

    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.SUCCESS
    assert result.matches_expected_status is True
    assert result.agent_response is not None
    assert result.agent_response.data is not None
    assert result.agent_response.data.get("requested_amount") == 50.0
    assert result.agent_response.data.get("status") == "simulated_approval_pending"


# ==============================================================================
# 2. Multiple Scenarios & Batch Execution Tests
# ==============================================================================

def test_runner_executes_multiple_scenarios_in_predictable_order(scenario_runner: ScenarioRunner):
    """Verify run_scenarios preserves provided order and produces structured SuiteExecutionResult."""
    registry = create_default_registry()
    scenarios = [
        registry.get_or_raise("BENIGN-ORDER-LOOKUP-001"),
        registry.get_or_raise("AUTHZ-CROSS-ORDER-001"),
        registry.get_or_raise("BENIGN-REFUND-APPROVAL-001"),
        registry.get_or_raise("AUTHZ-CROSS-REFUND-001"),
    ]

    suite_result = scenario_runner.run_scenarios(scenarios, run_id="custom_batch_001")

    assert isinstance(suite_result, SuiteExecutionResult)
    assert suite_result.run_id == "custom_batch_001"
    assert suite_result.total_count == 4
    assert suite_result.completed_count == 4
    assert suite_result.error_count == 0
    assert suite_result.matches_expected_count == 4

    # Verify execution order is strictly preserved
    result_ids = [r.scenario_id for r in suite_result.results]
    expected_ids = [s.scenario_id for s in scenarios]
    assert result_ids == expected_ids


def test_runner_run_all_canonical_scenarios(scenario_runner: ScenarioRunner):
    """Verify run_all executes every canonical scenario in the default registry."""
    suite_result = scenario_runner.run_all()

    assert suite_result.total_count >= 10
    assert suite_result.completed_count == suite_result.total_count
    assert suite_result.error_count == 0
    assert suite_result.matches_expected_count == suite_result.total_count

    # Check lookup helper methods on SuiteExecutionResult
    lookup_res = suite_result.get_result("BENIGN-ORDER-LOOKUP-001")
    assert lookup_res is not None
    assert lookup_res.actual_status == ExecutionStatus.SUCCESS

    benign_results = suite_result.by_category(ScenarioCategory.BENIGN_TASK)
    assert len(benign_results) >= 3

    unauth_results = suite_result.by_category(ScenarioCategory.UNAUTHORIZED_ACCESS)
    assert len(unauth_results) >= 4


def test_runner_run_by_id(scenario_runner: ScenarioRunner):
    """Verify run_by_id executes specific scenario by ID."""
    result = scenario_runner.run_by_id("BENIGN-POLICY-LOOKUP-001")
    assert result.scenario_id == "BENIGN-POLICY-LOOKUP-001"
    assert result.actual_status == ExecutionStatus.SUCCESS


def test_runner_run_by_id_unknown_raises(scenario_runner: ScenarioRunner):
    """Verify run_by_id raises KeyError for unknown scenario."""
    with pytest.raises(KeyError):
        scenario_runner.run_by_id("NONEXISTENT-SCENARIO-999")


def test_runner_run_by_category(scenario_runner: ScenarioRunner):
    """Verify run_by_category executes only scenarios in selected category."""
    suite_result = scenario_runner.run_by_category(ScenarioCategory.DIRECT_INJECTION)
    assert suite_result.total_count >= 2
    for r in suite_result.results:
        assert r.category == ScenarioCategory.DIRECT_INJECTION


# ==============================================================================
# 3. Malformed Scenario Inputs & Boundary Conditions
# ==============================================================================

def test_runner_handles_malformed_missing_customer(scenario_runner: ScenarioRunner):
    """Verify missing customer ID is evaluated as DENIED by authorization guard."""
    scenario = get_scenario("MALFORMED-MISSING-CUSTOMER-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)
    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.DENIED
    assert result.matches_expected_status is True


def test_runner_handles_malformed_excess_refund(scenario_runner: ScenarioRunner):
    """Verify refund amount exceeding order total is rejected with ERROR status."""
    scenario = get_scenario("MALFORMED-EXCESS-REFUND-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)
    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.ERROR
    assert result.matches_expected_status is True


def test_runner_handles_malformed_negative_refund(scenario_runner: ScenarioRunner):
    """Verify negative refund amount is rejected with ERROR status."""
    scenario = get_scenario("MALFORMED-NEGATIVE-REFUND-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)
    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.ERROR
    assert result.matches_expected_status is True


def test_runner_handles_malformed_unknown_action(scenario_runner: ScenarioRunner):
    """Verify unsupported action is rejected by router with ERROR status."""
    scenario = get_scenario("MALFORMED-UNKNOWN-ACTION-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)
    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.ERROR
    assert result.matches_expected_status is True


def test_runner_handles_malformed_raw_dict_payload(scenario_runner: ScenarioRunner):
    """Verify agent schema validation failure is recorded as ERROR status."""
    scenario = get_scenario("MALFORMED-INVALID-DICT-PAYLOAD-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)
    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.ERROR
    assert result.matches_expected_status is True


def test_runner_handles_direct_prompt_injection(scenario_runner: ScenarioRunner):
    """Verify direct prompt injection attempt in reason field is blocked by guard."""
    scenario = get_scenario("INJECT-DIRECT-OVERRIDE-REASON-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)
    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.DENIED
    assert result.matches_expected_status is True


def test_runner_handles_action_append_injection(scenario_runner: ScenarioRunner):
    """Verify injected tokens in action name are rejected by router normalization."""
    scenario = get_scenario("INJECT-DIRECT-ACTION-APPEND-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)
    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.ERROR
    assert result.matches_expected_status is True


def test_runner_handles_indirect_injection_context(scenario_runner: ScenarioRunner):
    """Verify benign access succeeds even when context contains simulated hostile text."""
    scenario = get_scenario("INJECT-INDIRECT-ORDER-NOTES-001")
    assert scenario is not None

    result = scenario_runner.run_scenario(scenario)
    assert result.execution_status == ScenarioExecutionStatus.COMPLETED
    assert result.actual_status == ExecutionStatus.SUCCESS
    assert result.matches_expected_status is True


# ==============================================================================
# 4. Exception Handling & Fail-Closed Behavior
# ==============================================================================

class CrashingAgent(BaseAgent):
    """Mock agent that raises an unhandled exception on execution."""

    def execute(self, request: Union[SupportRequest, Dict[str, Any]]) -> AgentResponse:
        raise RuntimeError("Simulated internal agent crash or network failure.")


def test_runner_unexpected_exception_fails_closed():
    """Verify unhandled agent exceptions are recorded as ERROR and never as security passes."""
    crashing_runner = ScenarioRunner(agent=CrashingAgent())
    scenario = Scenario(
        scenario_id="ERROR-TEST-001",
        name="Error Handling Test",
        category=ScenarioCategory.MALFORMED_INPUT,
        description="Tests runner exception handling",
        security_objective="Verify fail-closed behavior on unhandled exceptions",
        request=SupportRequest(customer_id="alice", action="lookup_order", order_id="A-100"),
        expected_behavior=ExpectedBehavior(
            expected_status=ExecutionStatus.ERROR,
            description="Expected error",
        ),
        success_condition="Should handle exception safely",
        failure_condition="Should not treat exception as pass",
    )

    result = crashing_runner.run_scenario(scenario)

    assert result.execution_status == ScenarioExecutionStatus.ERROR
    assert result.actual_status == ExecutionStatus.ERROR
    assert result.agent_response is None
    assert result.execution_trace is None
    assert result.error_message is not None
    assert "RuntimeError" in result.error_message
    assert "Simulated internal agent crash" in result.error_message

    # CRITICAL: Even though expected_status was ERROR, an unhandled crash must NEVER match!
    assert result.matches_expected_status is False


def test_runner_batch_execution_with_crashing_agent():
    """Verify batch execution continues and marks crashing scenarios as ERROR without halting."""
    crashing_runner = ScenarioRunner(agent=CrashingAgent())
    scenarios = [
        Scenario(
            scenario_id=f"CRASH-BATCH-{i}",
            name=f"Crash Test {i}",
            category=ScenarioCategory.UNAUTHORIZED_ACCESS,
            description="Testing batch resilience",
            security_objective="Objective",
            request=SupportRequest(customer_id="alice", action="lookup_order", order_id="A-100"),
            expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.DENIED),
            success_condition="Success",
            failure_condition="Failure",
        )
        for i in range(3)
    ]

    suite_result = crashing_runner.run_scenarios(scenarios)

    assert suite_result.total_count == 3
    assert suite_result.completed_count == 0
    assert suite_result.error_count == 3
    assert suite_result.matches_expected_count == 0


# ==============================================================================
# 5. Determinism Across Repeated Runs
# ==============================================================================

def test_runner_deterministic_across_repeated_runs(scenario_runner: ScenarioRunner):
    """Verify repeated executions of the full scenario library yield identical outcomes."""
    scenarios = list_scenarios()

    run_1 = scenario_runner.run_scenarios(scenarios, run_id="repeat_run_1")
    run_2 = scenario_runner.run_scenarios(scenarios, run_id="repeat_run_2")
    run_3 = scenario_runner.run_scenarios(scenarios, run_id="repeat_run_3")

    statuses_1 = [r.actual_status for r in run_1.results]
    statuses_2 = [r.actual_status for r in run_2.results]
    statuses_3 = [r.actual_status for r in run_3.results]

    assert statuses_1 == statuses_2 == statuses_3

    matches_1 = [r.matches_expected_status for r in run_1.results]
    matches_2 = [r.matches_expected_status for r in run_2.results]
    matches_3 = [r.matches_expected_status for r in run_3.results]

    assert matches_1 == matches_2 == matches_3
    assert all(matches_1)


def test_runner_default_instantiation():
    """Verify ScenarioRunner can be instantiated without arguments and defaults to hermetic reference agent."""
    runner = ScenarioRunner()
    assert runner.agent is not None

    scenario = get_scenario("BENIGN-ORDER-LOOKUP-001")
    assert scenario is not None
    result = runner.run_scenario(scenario)
    assert result.actual_status == ExecutionStatus.SUCCESS


def test_runner_custom_agent_factory():
    """Verify ScenarioRunner supports agent factory for isolated runs."""
    from app.scenarios.runner import create_default_reference_agent

    factory_calls = 0

    def custom_factory():
        nonlocal factory_calls
        factory_calls += 1
        return create_default_reference_agent()

    runner = ScenarioRunner(agent_factory=custom_factory)
    scenario = get_scenario("BENIGN-ORDER-LOOKUP-001")
    assert scenario is not None

    result = runner.run_scenario(scenario)
    assert result.actual_status == ExecutionStatus.SUCCESS
    assert factory_calls >= 1


def test_runner_empty_scenarios_list(scenario_runner: ScenarioRunner):
    """Verify running empty list of scenarios produces a valid SuiteExecutionResult."""
    suite_result = scenario_runner.run_scenarios([])
    assert suite_result.total_count == 0
    assert suite_result.completed_count == 0
    assert suite_result.error_count == 0
    assert suite_result.matches_expected_count == 0
    assert suite_result.results == []


def test_evaluator_package_re_exports_runner():
    """Verify ScenarioRunner and models are accessible from app.evaluator and app.evaluator.runner."""
    from app.evaluator import (
        ScenarioExecutionStatus as EvalStatus,
        ScenarioResult as EvalResult,
        ScenarioRunner as EvalRunner,
        SuiteExecutionResult as EvalSuite,
    )
    from app.evaluator.runner import ScenarioRunner as RunnerRunner

    assert EvalRunner is ScenarioRunner
    assert RunnerRunner is ScenarioRunner
    assert EvalStatus is ScenarioExecutionStatus
    assert EvalResult is ScenarioResult
    assert EvalSuite is SuiteExecutionResult


def test_scenario_result_mismatch_status_handling():
    """Verify ScenarioResult.matches_expected_status is False when status diverges."""
    res = ScenarioResult(
        scenario_id="TEST-001",
        scenario_name="Mismatch Test",
        category=ScenarioCategory.UNAUTHORIZED_ACCESS,
        expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.DENIED),
        actual_status=ExecutionStatus.SUCCESS,
        execution_status=ScenarioExecutionStatus.COMPLETED,
        agent_response=None,  # No agent response
    )
    assert res.matches_expected_status is False

    res_incomplete = ScenarioResult(
        scenario_id="TEST-002",
        scenario_name="Incomplete Test",
        category=ScenarioCategory.UNAUTHORIZED_ACCESS,
        expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.DENIED),
        actual_status=ExecutionStatus.DENIED,
        execution_status=ScenarioExecutionStatus.INCOMPLETE,
        agent_response=None,
    )
    assert res_incomplete.matches_expected_status is False

