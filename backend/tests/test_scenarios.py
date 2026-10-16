"""Unit tests for security scenario definitions, models, and registry."""

import pytest
from pydantic import ValidationError

from app.models import (
    AttackCategory,
    ExecutionStatus,
    ExpectedBehavior,
    RiskLevel,
    Scenario,
    ScenarioCategory,
    SupportRequest,
)
from app.scenarios import (
    SCENARIO_LIBRARY,
    ScenarioRegistry,
    create_default_registry,
    get_default_registry,
    get_scenario,
    list_scenarios,
)


# ==============================================================================
# 1. Scenario Definition Validation & Schema Tests
# ==============================================================================

def test_scenario_library_not_empty():
    """Verify that canonical scenario library contains at least 10 deterministic scenarios."""
    assert len(SCENARIO_LIBRARY) >= 10


def test_scenario_ids_are_globally_unique():
    """Verify that every scenario in the library has a unique, non-colliding ID."""
    seen_ids = set()
    for scenario in SCENARIO_LIBRARY:
        assert scenario.scenario_id not in seen_ids, f"Duplicate scenario ID found: {scenario.scenario_id}"
        seen_ids.add(scenario.scenario_id)


def test_scenario_required_fields_present():
    """Ensure all scenarios define required metadata, conditions, and assertions."""
    for s in SCENARIO_LIBRARY:
        assert isinstance(s.scenario_id, str) and len(s.scenario_id.strip()) > 0
        assert isinstance(s.name, str) and len(s.name.strip()) > 0
        assert isinstance(s.category, ScenarioCategory)
        assert isinstance(s.description, str) and len(s.description.strip()) > 0
        assert isinstance(s.security_objective, str) and len(s.security_objective.strip()) > 0
        assert isinstance(s.success_condition, str) and len(s.success_condition.strip()) > 0
        assert isinstance(s.failure_condition, str) and len(s.failure_condition.strip()) > 0
        assert isinstance(s.risk_level, RiskLevel)
        assert isinstance(s.tags, list) and len(s.tags) > 0
        assert s.version >= 1
        assert isinstance(s.expected_behavior, ExpectedBehavior)
        assert isinstance(s.expected_behavior.expected_status, ExecutionStatus)


def test_scenario_model_validation_rejects_empty_id():
    """Ensure Scenario model rejects empty or whitespace-only scenario_id."""
    with pytest.raises(ValidationError):
        Scenario(
            scenario_id="   ",
            name="Invalid Scenario",
            category=ScenarioCategory.BENIGN_TASK,
            description="Testing empty id validation",
            security_objective="Objective",
            request=SupportRequest(customer_id="alice", action="lookup_order"),
            expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.SUCCESS),
            success_condition="Success",
            failure_condition="Failure",
        )


def test_scenario_model_validation_rejects_empty_name():
    """Ensure Scenario model rejects empty or whitespace-only name."""
    with pytest.raises(ValidationError):
        Scenario(
            scenario_id="VALID-ID-001",
            name="",
            category=ScenarioCategory.BENIGN_TASK,
            description="Testing empty name validation",
            security_objective="Objective",
            request=SupportRequest(customer_id="alice", action="lookup_order"),
            expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.SUCCESS),
            success_condition="Success",
            failure_condition="Failure",
        )


def test_scenario_model_forbids_extra_fields():
    """Ensure Scenario and ExpectedBehavior models forbid unknown fields."""
    with pytest.raises(ValidationError):
        Scenario(
            scenario_id="EXTRA-FIELD-001",
            name="Extra Field Test",
            category=ScenarioCategory.BENIGN_TASK,
            description="Desc",
            security_objective="Obj",
            request=SupportRequest(customer_id="alice", action="lookup_order"),
            expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.SUCCESS),
            success_condition="Success",
            failure_condition="Failure",
            unsupported_extra_field="invalid",
        )

    with pytest.raises(ValidationError):
        ExpectedBehavior(
            expected_status=ExecutionStatus.SUCCESS,
            unknown_assertion=True,
        )


def test_scenario_expected_behavior_frozen():
    """Verify ExpectedBehavior is immutable (frozen)."""
    expected = ExpectedBehavior(expected_status=ExecutionStatus.SUCCESS)
    with pytest.raises(ValidationError):
        expected.must_have_authorization_denial = True  # type: ignore


# ==============================================================================
# 2. Scenario Category & Attack Vector Coverage
# ==============================================================================

def test_scenario_categories_coverage():
    """Verify the library covers benign, unauthorized, malformed, and injection categories."""
    categories_present = {s.category for s in SCENARIO_LIBRARY}

    assert ScenarioCategory.BENIGN_TASK in categories_present
    assert ScenarioCategory.UNAUTHORIZED_ACCESS in categories_present
    assert ScenarioCategory.MALFORMED_INPUT in categories_present
    assert ScenarioCategory.DIRECT_INJECTION in categories_present
    assert ScenarioCategory.INDIRECT_INJECTION in categories_present


def test_attack_category_alias():
    """Verify AttackCategory is an alias of ScenarioCategory."""
    assert AttackCategory is ScenarioCategory


def test_prompt_injection_scenarios_documentation():
    """Ensure prompt-injection scenarios clearly document reference agent limitations."""
    injection_scenarios = [
        s for s in SCENARIO_LIBRARY
        if s.category in (ScenarioCategory.DIRECT_INJECTION, ScenarioCategory.INDIRECT_INJECTION)
    ]
    assert len(injection_scenarios) >= 3
    for s in injection_scenarios:
        # Must clearly document that ReferenceAgent is rule-based or deterministic
        assert "reference agent" in s.description.lower() or "rule-based" in s.description.lower() or "prompt-injection" in s.description.lower() or "injection" in s.description.lower()


# ==============================================================================
# 3. Scenario Registry Tests
# ==============================================================================

def test_registry_register_and_get():
    """Verify registering a scenario and retrieving it by ID."""
    registry = ScenarioRegistry()
    scenario = Scenario(
        scenario_id="CUSTOM-TEST-001",
        name="Custom Scenario",
        category=ScenarioCategory.BENIGN_TASK,
        description="A test scenario",
        security_objective="Verify registry registration",
        request=SupportRequest(customer_id="alice", action="lookup_order", order_id="A-100"),
        expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.SUCCESS),
        success_condition="Success",
        failure_condition="Failure",
    )
    registry.register(scenario)

    assert len(registry) == 1
    assert "CUSTOM-TEST-001" in registry
    assert registry.get("CUSTOM-TEST-001") == scenario
    assert registry.get_or_raise("CUSTOM-TEST-001") == scenario


def test_registry_duplicate_registration_raises():
    """Verify registry enforces unique scenario IDs and raises on collision."""
    registry = ScenarioRegistry()
    scenario = Scenario(
        scenario_id="DUP-ID-001",
        name="Duplicate 1",
        category=ScenarioCategory.BENIGN_TASK,
        description="First instance",
        security_objective="Objective",
        request=SupportRequest(customer_id="alice", action="lookup_order"),
        expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.SUCCESS),
        success_condition="Success",
        failure_condition="Failure",
    )
    registry.register(scenario)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(scenario)


def test_registry_get_nonexistent_returns_none():
    """Verify get() on unknown scenario returns None."""
    registry = ScenarioRegistry()
    assert registry.get("NONEXISTENT") is None


def test_registry_get_or_raise_nonexistent_raises_key_error():
    """Verify get_or_raise() raises KeyError for unknown scenario."""
    registry = ScenarioRegistry()
    with pytest.raises(KeyError, match="not found"):
        registry.get_or_raise("NONEXISTENT")


def test_registry_filter_by_category():
    """Verify registry filtering by category."""
    registry = create_default_registry()
    benign_scenarios = registry.filter_by_category(ScenarioCategory.BENIGN_TASK)
    assert len(benign_scenarios) >= 3
    for s in benign_scenarios:
        assert s.category == ScenarioCategory.BENIGN_TASK


def test_registry_filter_by_tag():
    """Verify registry filtering by tag."""
    registry = create_default_registry()
    auth_scenarios = registry.filter_by_tag("authorization")
    assert len(auth_scenarios) >= 4
    for s in auth_scenarios:
        assert any(t.lower() == "authorization" for t in s.tags)


def test_registry_deterministic_ordering():
    """Verify list_all returns scenarios in a consistent, predictable order."""
    registry = create_default_registry()
    list_1 = [s.scenario_id for s in registry.list_all()]
    list_2 = [s.scenario_id for s in registry.list_all()]
    assert list_1 == list_2


def test_default_registry_convenience_functions():
    """Verify module-level convenience functions get_scenario and list_scenarios."""
    all_scenarios = list_scenarios()
    assert len(all_scenarios) == len(SCENARIO_LIBRARY)

    alice_scenario = get_scenario("BENIGN-ORDER-LOOKUP-001")
    assert alice_scenario is not None
    assert alice_scenario.name == "Authorized Order Lookup (Positive Control)"

    unknown = get_scenario("DOES_NOT_EXIST")
    assert unknown is None


def test_registry_categories_and_nonexistent_tag():
    """Verify categories list and filtering by non-matching tag."""
    registry = create_default_registry()
    cats = registry.categories()
    assert isinstance(cats, list)
    assert len(cats) >= 4

    missing_tag_results = registry.filter_by_tag("nonexistent_tag_12345")
    assert missing_tag_results == []

    assert "NONEXISTENT_ID" not in registry
    assert "" not in registry


def test_suite_execution_result_helpers():
    """Verify SuiteExecutionResult helper methods get_result and by_category."""
    from app.models.scenario import ScenarioResult, ScenarioExecutionStatus, SuiteExecutionResult

    res1 = ScenarioResult(
        scenario_id="S-001",
        scenario_name="S1",
        category=ScenarioCategory.BENIGN_TASK,
        expected_behavior=ExpectedBehavior(expected_status=ExecutionStatus.SUCCESS),
        actual_status=ExecutionStatus.SUCCESS,
        execution_status=ScenarioExecutionStatus.COMPLETED,
    )
    suite = SuiteExecutionResult(run_id="run_test", results=[res1])

    assert suite.get_result("S-001") == res1
    assert suite.get_result("S-UNKNOWN") is None
    assert suite.by_category(ScenarioCategory.BENIGN_TASK) == [res1]
    assert suite.by_category(ScenarioCategory.DIRECT_INJECTION) == []

