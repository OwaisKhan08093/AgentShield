"""Scenario registry for managing, validating, and querying evaluation scenarios."""

from typing import Dict, Iterable, List, Optional
from app.models.scenario import Scenario, ScenarioCategory
from app.scenarios.definitions import SCENARIO_LIBRARY


class ScenarioRegistry:
    """Registry maintaining a validated, unique collection of security scenarios."""

    def __init__(self, scenarios: Optional[Iterable[Scenario]] = None):
        """Initialize the registry with an optional collection of scenarios."""
        self._scenarios: Dict[str, Scenario] = {}
        if scenarios:
            for s in scenarios:
                self.register(s)

    def register(self, scenario: Scenario) -> None:
        """Register a scenario, enforcing unique scenario IDs.

        Raises:
            ValueError: If a scenario with the same ID is already registered.
        """
        sid = scenario.scenario_id.strip()
        if sid in self._scenarios:
            raise ValueError(f"Scenario ID '{sid}' is already registered.")
        self._scenarios[sid] = scenario

    def get(self, scenario_id: str) -> Optional[Scenario]:
        """Look up a scenario by ID, returning None if not found."""
        return self._scenarios.get(scenario_id.strip() if scenario_id else "")

    def get_or_raise(self, scenario_id: str) -> Scenario:
        """Look up a scenario by ID, raising KeyError if not found.

        Raises:
            KeyError: If scenario_id does not exist in the registry.
        """
        sid = scenario_id.strip() if scenario_id else ""
        if sid not in self._scenarios:
            raise KeyError(f"Scenario with ID '{sid}' was not found in the registry.")
        return self._scenarios[sid]

    def list_all(self) -> List[Scenario]:
        """Return all registered scenarios in deterministic registration order."""
        return list(self._scenarios.values())

    def filter_by_category(self, category: ScenarioCategory) -> List[Scenario]:
        """Return all scenarios matching a specific category."""
        return [s for s in self._scenarios.values() if s.category == category]

    def filter_by_tag(self, tag: str) -> List[Scenario]:
        """Return all scenarios tagged with the specified tag."""
        clean_tag = tag.strip().lower()
        return [s for s in self._scenarios.values() if clean_tag in [t.lower() for t in s.tags]]

    def categories(self) -> List[ScenarioCategory]:
        """Return a sorted list of unique categories present in the registry."""
        return sorted(list(set(s.category for s in self._scenarios.values())), key=lambda c: c.value)

    def __len__(self) -> int:
        """Return the count of registered scenarios."""
        return len(self._scenarios)

    def __contains__(self, scenario_id: str) -> bool:
        """Return True if scenario_id is registered."""
        return (scenario_id.strip() if scenario_id else "") in self._scenarios


def create_default_registry() -> ScenarioRegistry:
    """Create a fresh ScenarioRegistry loaded with the canonical SCENARIO_LIBRARY."""
    return ScenarioRegistry(SCENARIO_LIBRARY)


_DEFAULT_REGISTRY: Optional[ScenarioRegistry] = None


def get_default_registry() -> ScenarioRegistry:
    """Return the global default scenario registry instance."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = create_default_registry()
    return _DEFAULT_REGISTRY


def get_scenario(scenario_id: str) -> Optional[Scenario]:
    """Convenience lookup for a scenario by ID from the default registry."""
    return get_default_registry().get(scenario_id)


def list_scenarios() -> List[Scenario]:
    """Convenience method returning all canonical scenarios from the default registry."""
    return get_default_registry().list_all()
