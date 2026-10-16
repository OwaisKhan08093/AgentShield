"""Comprehensive unit tests for deterministic security evaluation engine."""

import json
from typing import Any, Dict, List, Union
import pytest

from app.agent.base import BaseAgent
from app.evaluator import (
    EvaluationOutcome,
    EvaluationReport,
    Finding,
    ScenarioEvaluation,
    SecurityEvaluator,
    evaluate_scenario,
    evaluate_suite,
    make_metric,
)
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
    TraceEvent,
    TraceEventType,
)
from app.scenarios import (
    ScenarioRunner,
    get_scenario,
    list_scenarios,
)
from tests.fixtures import VulnerableAgent


# ==============================================================================
# 1. Individual Scenario Evaluation Tests (Canonical Reference Agent)
# ==============================================================================

def test_evaluate_positive_control_scenario(
    scenario_runner: ScenarioRunner,
    security_evaluator: SecurityEvaluator,
):
    """Verify evaluating an authorized positive control scenario yields PASS outcome."""
    scenario = get_scenario("BENIGN-ORDER-LOOKUP-001")
    assert scenario is not None

    runner_result = scenario_runner.run_scenario(scenario)
    evaluation = security_evaluator.evaluate_scenario(runner_result, scenario_definition=scenario)

    assert isinstance(evaluation, ScenarioEvaluation)
    assert evaluation.scenario_id == "BENIGN-ORDER-LOOKUP-001"
    assert evaluation.outcome == EvaluationOutcome.PASS
    assert evaluation.attempt_detected is False
    assert evaluation.violation_prevented is False
    assert evaluation.data_exposed is False
    assert len(evaluation.findings) >= 2

    # Check positive control rule check
    ctrl_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-CTRL-001"), None)
    assert ctrl_finding is not None
    assert ctrl_finding.outcome == EvaluationOutcome.PASS


def test_evaluate_unauthorized_cross_customer_scenario(
    scenario_runner: ScenarioRunner,
    security_evaluator: SecurityEvaluator,
):
    """Verify evaluating cross-customer scenario records PASS (blocked attempt) with no data exposure."""
    scenario = get_scenario("AUTHZ-CROSS-ORDER-001")
    assert scenario is not None

    runner_result = scenario_runner.run_scenario(scenario)
    evaluation = security_evaluator.evaluate_scenario(runner_result, scenario_definition=scenario)

    assert evaluation.scenario_id == "AUTHZ-CROSS-ORDER-001"
    assert evaluation.outcome == EvaluationOutcome.PASS
    assert evaluation.attempt_detected is True
    assert evaluation.violation_prevented is True
    assert evaluation.data_exposed is False

    # Check authorization enforcement rule
    auth_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-AUTHZ-001"), None)
    assert auth_finding is not None
    assert auth_finding.outcome == EvaluationOutcome.PASS

    # Check data exposure rule
    data_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-DATA-001"), None)
    assert data_finding is not None
    assert data_finding.outcome == EvaluationOutcome.PASS


def test_evaluate_simulated_refund_approval(
    scenario_runner: ScenarioRunner,
    security_evaluator: SecurityEvaluator,
):
    """Verify evaluating valid simulated refund records PASS and verifies simulation boundary."""
    scenario = get_scenario("BENIGN-REFUND-APPROVAL-001")
    assert scenario is not None

    runner_result = scenario_runner.run_scenario(scenario)
    evaluation = security_evaluator.evaluate_scenario(runner_result, scenario_definition=scenario)

    assert evaluation.outcome == EvaluationOutcome.PASS
    appr_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-APPR-001"), None)
    assert appr_finding is not None
    assert appr_finding.outcome == EvaluationOutcome.PASS


def test_evaluate_prompt_injection_resistance(
    scenario_runner: ScenarioRunner,
    security_evaluator: SecurityEvaluator,
):
    """Verify direct prompt injection scenario records PASS because external guard blocked attempt."""
    scenario = get_scenario("INJECT-DIRECT-OVERRIDE-REASON-001")
    assert scenario is not None

    runner_result = scenario_runner.run_scenario(scenario)
    evaluation = security_evaluator.evaluate_scenario(runner_result, scenario_definition=scenario)

    assert evaluation.outcome == EvaluationOutcome.PASS
    assert evaluation.attempt_detected is True
    assert evaluation.violation_prevented is True
    assert evaluation.data_exposed is False

    inject_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-INJECT-001"), None)
    assert inject_finding is not None
    assert inject_finding.outcome == EvaluationOutcome.PASS


# ==============================================================================
# 2. Violation Detection & Vulnerable Fixture Tests
# ==============================================================================

def test_evaluator_detects_vulnerable_agent_authorization_breach(
    vulnerable_agent: VulnerableAgent,
    security_evaluator: SecurityEvaluator,
):
    """Verify evaluator accurately detects authorization breach and data exposure from vulnerable agent."""
    vuln_runner = ScenarioRunner(agent=vulnerable_agent)
    scenario = get_scenario("AUTHZ-CROSS-ORDER-001")
    assert scenario is not None

    runner_result = vuln_runner.run_scenario(scenario)
    evaluation = security_evaluator.evaluate_scenario(runner_result, scenario_definition=scenario)

    # Must be evaluated as FAIL
    assert evaluation.outcome == EvaluationOutcome.FAIL
    assert evaluation.attempt_detected is True
    assert evaluation.violation_prevented is False
    assert evaluation.data_exposed is True

    # RULE-AUTHZ-001 must FAIL
    auth_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-AUTHZ-001"), None)
    assert auth_finding is not None
    assert auth_finding.outcome == EvaluationOutcome.FAIL
    assert auth_finding.severity == RiskLevel.CRITICAL

    # RULE-DATA-001 must FAIL
    data_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-DATA-001"), None)
    assert data_finding is not None
    assert data_finding.outcome == EvaluationOutcome.FAIL
    assert data_finding.severity == RiskLevel.CRITICAL


class FalsePositiveAgent(BaseAgent):
    """Agent that incorrectly refuses authorized operations."""

    def execute(self, request: Union[SupportRequest, Dict[str, Any]]) -> AgentResponse:
        trace = ExecutionTrace(
            execution_id="exec_fp_1",
            customer_id="alice",
            action="lookup_order",
            status=ExecutionStatus.DENIED,
            summary="Access denied incorrectly.",
            events=[
                TraceEvent(
                    event_id="evt_1",
                    sequence=1,
                    event_type=TraceEventType.REQUEST,
                    is_denied=False,
                ),
                TraceEvent(
                    event_id="evt_2",
                    sequence=2,
                    event_type=TraceEventType.RESPONSE,
                    decision="denied",
                    is_denied=True,
                ),
            ],
            final_result=None,
        )
        return AgentResponse(
            execution_id="exec_fp_1",
            status=ExecutionStatus.DENIED,
            summary=trace.summary,
            data=None,
            trace=trace,
        )


def test_evaluator_detects_false_positive_control_failure(security_evaluator: SecurityEvaluator):
    """Verify evaluator detects when an authorized request is falsely denied."""
    runner = ScenarioRunner(agent=FalsePositiveAgent())
    scenario = get_scenario("BENIGN-ORDER-LOOKUP-001")
    assert scenario is not None

    runner_result = runner.run_scenario(scenario)
    evaluation = security_evaluator.evaluate_scenario(runner_result, scenario_definition=scenario)

    assert evaluation.outcome == EvaluationOutcome.FAIL
    ctrl_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-CTRL-001"), None)
    assert ctrl_finding is not None
    assert ctrl_finding.outcome == EvaluationOutcome.FAIL

    auth_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-AUTHZ-001"), None)
    assert auth_finding is not None
    assert auth_finding.outcome == EvaluationOutcome.FAIL


# ==============================================================================
# 3. Execution Integrity & Trace Validation Tests
# ==============================================================================

class BrokenTraceAgent(BaseAgent):
    """Agent returning non-sequential event sequence in trace."""

    def execute(self, request: Union[SupportRequest, Dict[str, Any]]) -> AgentResponse:
        trace = ExecutionTrace(
            execution_id="exec_broken_1",
            customer_id="alice",
            action="lookup_order",
            status=ExecutionStatus.SUCCESS,
            summary="Broken sequence trace.",
            events=[
                TraceEvent(event_id="evt_1", sequence=1, event_type=TraceEventType.REQUEST),
                TraceEvent(event_id="evt_2", sequence=5, event_type=TraceEventType.RESPONSE),  # broken sequence
            ],
            final_result={"order_id": "A-100"},
        )
        return AgentResponse(
            execution_id="exec_broken_1",
            status=ExecutionStatus.SUCCESS,
            summary=trace.summary,
            data=trace.final_result,
            trace=trace,
        )


def test_evaluator_detects_broken_trace_sequence(security_evaluator: SecurityEvaluator):
    """Verify evaluator flags broken trace sequence as an integrity failure."""
    runner = ScenarioRunner(agent=BrokenTraceAgent())
    scenario = get_scenario("BENIGN-ORDER-LOOKUP-001")
    assert scenario is not None

    runner_result = runner.run_scenario(scenario)
    evaluation = security_evaluator.evaluate_scenario(runner_result, scenario_definition=scenario)

    assert evaluation.outcome == EvaluationOutcome.FAIL
    trace_finding = next((f for f in evaluation.findings if f.rule_id == "RULE-TRACE-001"), None)
    assert trace_finding is not None
    assert trace_finding.outcome == EvaluationOutcome.FAIL
    assert "broken at index 2" in trace_finding.message


def test_evaluator_handles_runner_exception_as_error(security_evaluator: SecurityEvaluator):
    """Verify runner exceptions are evaluated as ERROR and never treated as security passes."""
    crashed_result = ScenarioResult(
        scenario_id="AUTHZ-CROSS-ORDER-001",
        scenario_name="Cross-Customer Access",
        category=ScenarioCategory.UNAUTHORIZED_ACCESS,
        expected_behavior=ExpectedBehavior(
            expected_status=ExecutionStatus.DENIED,
            must_have_authorization_denial=True,
        ),
        actual_status=ExecutionStatus.ERROR,
        execution_status=ScenarioExecutionStatus.ERROR,
        agent_response=None,
        error_message="RuntimeError: Internal runner crash",
    )

    evaluation = security_evaluator.evaluate_scenario(crashed_result)

    assert evaluation.outcome == EvaluationOutcome.ERROR
    assert evaluation.attempt_detected is True
    # An exception must NEVER count as a prevented violation!
    assert evaluation.violation_prevented is False
    assert "Execution error" in evaluation.explanation


def test_evaluator_handles_incomplete_execution_as_not_run(security_evaluator: SecurityEvaluator):
    """Verify incomplete scenarios are evaluated as NOT_RUN."""
    incomplete_result = ScenarioResult(
        scenario_id="BENIGN-ORDER-LOOKUP-001",
        scenario_name="Lookup",
        category=ScenarioCategory.BENIGN_TASK,
        expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.SUCCESS),
        actual_status=None,
        execution_status=ScenarioExecutionStatus.INCOMPLETE,
        agent_response=None,
    )

    evaluation = security_evaluator.evaluate_scenario(incomplete_result)
    assert evaluation.outcome == EvaluationOutcome.NOT_RUN


# ==============================================================================
# 4. Suite Evaluation & Metrics Tests
# ==============================================================================

def test_evaluate_full_canonical_suite(
    scenario_runner: ScenarioRunner,
    security_evaluator: SecurityEvaluator,
):
    """Verify evaluating full scenario suite against ReferenceAgent produces clean 100% report."""
    suite_result = scenario_runner.run_all()
    report = security_evaluator.evaluate_suite(suite_result)

    assert isinstance(report, EvaluationReport)
    assert report.run_id == suite_result.run_id
    assert report.overall_outcome == EvaluationOutcome.PASS
    assert report.summary_counts.total_scenarios >= 10
    assert report.summary_counts.passed_count == report.summary_counts.total_scenarios
    assert report.summary_counts.failed_count == 0
    assert report.summary_counts.error_count == 0

    metrics = report.metrics

    # Check overall pass rate
    assert metrics.overall_pass_rate.value == 1.0
    assert metrics.overall_pass_rate.display_value == "100.0%"
    assert metrics.overall_pass_rate.denominator == report.summary_counts.total_scenarios

    # Check attack success rate: must be 0% for reference agent
    assert metrics.attack_success_rate.value == 0.0
    assert metrics.attack_success_rate.display_value == "0.0%"

    # Check unauthorized access prevention rate: must be 100%
    assert metrics.unauthorized_prevention_rate.value == 1.0
    assert metrics.unauthorized_prevention_rate.display_value == "100.0%"

    # Check sensitive data exposure rate: must be 0%
    assert metrics.sensitive_data_exposure_rate.value == 0.0

    # Check benign task success rate: must be 100%
    assert metrics.benign_task_success_rate.value == 1.0

    # Check run completion rate: must be 100%
    assert metrics.run_completion_rate.value == 1.0

    # Check security score: must be 100.0/100
    assert metrics.security_score.display_value == "100.0/100"

    # Check no security violations were recorded
    assert len(metrics.violations_by_rule) == 0

    # Check report helpers
    alice_eval = report.get_scenario_evaluation("BENIGN-ORDER-LOOKUP-001")
    assert alice_eval is not None
    assert alice_eval.outcome == EvaluationOutcome.PASS

    findings = report.get_findings_for_scenario("BENIGN-ORDER-LOOKUP-001")
    assert len(findings) >= 2


def test_evaluate_suite_with_vulnerable_agent(
    vulnerable_agent: VulnerableAgent,
    security_evaluator: SecurityEvaluator,
):
    """Verify evaluating suite with vulnerable agent correctly flags FAIL outcome and calculates metrics."""
    vuln_runner = ScenarioRunner(agent=vulnerable_agent)
    scenarios = [
        get_scenario("BENIGN-ORDER-LOOKUP-001"),
        get_scenario("AUTHZ-CROSS-ORDER-001"),
    ]
    suite_result = vuln_runner.run_scenarios(scenarios)  # type: ignore
    report = security_evaluator.evaluate_suite(suite_result)

    assert report.overall_outcome == EvaluationOutcome.FAIL
    assert report.summary_counts.failed_count >= 1

    # Attack Success Rate must be > 0%
    assert report.metrics.attack_success_rate.value is not None
    assert report.metrics.attack_success_rate.value > 0.0

    # Data exposure rate must be > 0%
    assert report.metrics.sensitive_data_exposure_rate.value is not None
    assert report.metrics.sensitive_data_exposure_rate.value > 0.0

    # Violations tracked by rule
    assert "RULE-AUTHZ-001" in report.metrics.violations_by_rule
    assert "RULE-DATA-001" in report.metrics.violations_by_rule


def test_metric_zero_denominator_safety():
    """Verify metrics calculation never divides by zero and reports N/A for empty denominator."""
    m = make_metric(
        name="Empty Metric",
        numerator=0,
        denominator=0,
        description="Zero denominator test",
        formula="0 / 0",
    )
    assert m.value is None
    assert m.display_value == "N/A"
    assert m.denominator == 0


def test_evaluate_empty_suite(security_evaluator: SecurityEvaluator):
    """Verify evaluating an empty suite returns NOT_RUN and handles zero denominators safely."""
    empty_suite = SuiteExecutionResult(run_id="empty_run", results=[])
    report = security_evaluator.evaluate_suite(empty_suite)

    assert report.overall_outcome == EvaluationOutcome.NOT_RUN
    assert report.summary_counts.total_scenarios == 0
    assert report.metrics.overall_pass_rate.display_value == "N/A"
    assert report.metrics.attack_success_rate.display_value == "N/A"
    assert report.metrics.security_score.display_value == "N/A"


# ==============================================================================
# 5. Category & Severity Grouping Tests
# ==============================================================================

def test_metrics_category_and_risk_breakdowns(
    scenario_runner: ScenarioRunner,
    security_evaluator: SecurityEvaluator,
):
    """Verify metrics compute correct breakdowns across categories and risk levels."""
    suite_result = scenario_runner.run_all()
    report = security_evaluator.evaluate_suite(suite_result)

    by_cat = report.metrics.by_category
    assert "benign_task" in by_cat
    assert by_cat["benign_task"].total_count >= 3
    assert by_cat["benign_task"].passed_count >= 3

    assert "unauthorized_access" in by_cat
    assert by_cat["unauthorized_access"].total_count >= 5

    by_risk = report.metrics.by_risk_level
    assert "high" in by_risk
    assert by_risk["high"].total_count >= 1


# ==============================================================================
# 6. Serialization & Determinism Tests
# ==============================================================================

def test_evaluation_report_serialization(
    scenario_runner: ScenarioRunner,
    security_evaluator: SecurityEvaluator,
):
    """Verify EvaluationReport serializes cleanly to JSON and roundtrips without data loss."""
    scenario = get_scenario("BENIGN-ORDER-LOOKUP-001")
    assert scenario is not None

    suite_result = scenario_runner.run_scenarios([scenario])
    report = security_evaluator.evaluate_suite(suite_result)

    json_str = report.model_dump_json()
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["report_id"] == report.report_id
    assert data["overall_outcome"] == "pass"
    assert "limitation_statement" in data

    # Roundtrip validation
    reloaded = EvaluationReport.model_validate(data)
    assert reloaded.report_id == report.report_id
    assert reloaded.summary_counts.passed_count == 1


def test_evaluator_deterministic_across_repeated_evaluations(
    scenario_runner: ScenarioRunner,
    security_evaluator: SecurityEvaluator,
):
    """Verify repeated evaluations on the same suite result produce identical findings and outcomes."""
    suite_result = scenario_runner.run_all()

    report_1 = security_evaluator.evaluate_suite(suite_result)
    report_2 = security_evaluator.evaluate_suite(suite_result)

    assert report_1.overall_outcome == report_2.overall_outcome
    assert report_1.summary_counts == report_2.summary_counts
    assert report_1.metrics.overall_pass_rate == report_2.metrics.overall_pass_rate
    assert report_1.metrics.security_score == report_2.metrics.security_score

    outcomes_1 = [se.outcome for se in report_1.scenario_evaluations]
    outcomes_2 = [se.outcome for se in report_2.scenario_evaluations]
    assert outcomes_1 == outcomes_2


def test_convenience_functions(scenario_runner: ScenarioRunner):
    """Verify module-level evaluate_scenario and evaluate_suite convenience functions."""
    scenario = get_scenario("BENIGN-ORDER-LOOKUP-001")
    assert scenario is not None

    res = scenario_runner.run_scenario(scenario)
    eval_res = evaluate_scenario(res, scenario_definition=scenario)
    assert eval_res.outcome == EvaluationOutcome.PASS

    suite_res = scenario_runner.run_scenarios([scenario])
    eval_suite = evaluate_suite(suite_res)
    assert eval_suite.overall_outcome == EvaluationOutcome.PASS
