"""Scenario inspection and listing API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_scenario_registry
from app.api.schemas import ScenarioDetailResponse, ScenarioSummaryResponse
from app.models.scenario import ScenarioCategory
from app.scenarios.registry import ScenarioRegistry

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


@router.get(
    "",
    response_model=List[ScenarioSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List evaluation scenarios",
    description="Retrieve safe summaries of evaluation scenarios with optional category and tag filtering.",
)
def list_scenarios(
    category: Optional[ScenarioCategory] = Query(
        default=None,
        description="Filter scenarios by attack or evaluation category.",
    ),
    tag: Optional[str] = Query(
        default=None,
        description="Filter scenarios by tag string.",
    ),
    registry: ScenarioRegistry = Depends(get_scenario_registry),
) -> List[ScenarioSummaryResponse]:
    """Return filtered or complete collection of registered scenarios."""
    scenarios = registry.list_all()

    if category is not None:
        scenarios = [s for s in scenarios if s.category == category]

    if tag is not None and tag.strip():
        clean_tag = tag.strip().lower()
        scenarios = [s for s in scenarios if clean_tag in [t.lower() for t in s.tags]]

    return [
        ScenarioSummaryResponse(
            scenario_id=s.scenario_id,
            name=s.name,
            category=s.category,
            description=s.description,
            security_objective=s.security_objective,
            risk_level=s.risk_level,
            tags=s.tags,
            version=s.version,
            enabled=True,
        )
        for s in scenarios
    ]


@router.get(
    "/{scenario_id}",
    response_model=ScenarioDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get scenario detail",
    description="Retrieve detailed security scenario definition by its unique identifier.",
    responses={
        404: {"description": "Scenario ID not found."},
    },
)
def get_scenario(
    scenario_id: str,
    registry: ScenarioRegistry = Depends(get_scenario_registry),
) -> ScenarioDetailResponse:
    """Retrieve full scenario definition by unique ID."""
    clean_id = scenario_id.strip() if scenario_id else ""
    scenario = registry.get(clean_id)

    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{clean_id}' was not found in the registry.",
        )

    return ScenarioDetailResponse(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        category=scenario.category,
        description=scenario.description,
        security_objective=scenario.security_objective,
        risk_level=scenario.risk_level,
        tags=scenario.tags,
        version=scenario.version,
        enabled=True,
        expected_behavior=scenario.expected_behavior,
        success_condition=scenario.success_condition,
        failure_condition=scenario.failure_condition,
    )
