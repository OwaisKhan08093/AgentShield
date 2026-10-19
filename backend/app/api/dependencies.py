"""Dependency providers for AgentShield API routers."""

from app.scenarios.registry import ScenarioRegistry, get_default_registry
from app.storage.repository import SQLiteEvaluationRepository, get_default_repository


def get_scenario_registry() -> ScenarioRegistry:
    """Provide the default ScenarioRegistry singleton."""
    return get_default_registry()


def get_evaluation_repository() -> SQLiteEvaluationRepository:
    """Provide the default SQLiteEvaluationRepository singleton."""
    return get_default_repository()
