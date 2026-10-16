"""Scenario module for AgentShield.

Provides versioned, deterministic security scenarios and an execution runner
for evaluating agent security posture, authorization enforcement, and execution traces.
"""

from app.models.scenario import (
    AttackCategory,
    ExpectedBehavior,
    RiskLevel,
    Scenario,
    ScenarioCategory,
    ScenarioExecutionStatus,
    ScenarioResult,
    SuiteExecutionResult,
)
from app.scenarios.definitions import SCENARIO_LIBRARY
from app.scenarios.registry import (
    ScenarioRegistry,
    create_default_registry,
    get_default_registry,
    get_scenario,
    list_scenarios,
)
from app.scenarios.runner import ScenarioRunner, create_default_reference_agent

__all__ = [
    "AttackCategory",
    "ExpectedBehavior",
    "RiskLevel",
    "SCENARIO_LIBRARY",
    "Scenario",
    "ScenarioCategory",
    "ScenarioExecutionStatus",
    "ScenarioRegistry",
    "ScenarioResult",
    "ScenarioRunner",
    "SuiteExecutionResult",
    "create_default_reference_agent",
    "create_default_registry",
    "get_default_registry",
    "get_scenario",
    "list_scenarios",
]
