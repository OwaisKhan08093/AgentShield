"""Evaluation run triggering, listing, results, trace, and report API endpoints."""

from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies import get_evaluation_repository, get_scenario_registry
from app.api.schemas import (
    CreateRunRequest,
    EvaluationReportExportResponse,
    FindingSummaryResponse,
    RunCreateResponse,
    ScenarioResultResponse,
)
from app.evaluator import get_default_evaluator
from app.models.event import TraceEvent
from app.models.run import EvaluationRunRecord
from app.scenarios.registry import ScenarioRegistry
from app.scenarios.runner import ScenarioRunner
from app.storage.exceptions import StorageError
from app.storage.repository import SQLiteEvaluationRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

SUPPORTED_SUITES = {"support-agent-security-v1", "default"}
SUPPORTED_AGENTS = {"reference-agent"}


@router.post(
    "",
    response_model=RunCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an evaluation run",
    description="Validate suite configuration, execute deterministic scenarios through the reference agent, evaluate security rules, and persist structured findings.",
    responses={
        400: {"description": "Invalid suite ID, unsupported agent ID, or invalid scenario IDs."},
        500: {"description": "Evaluation execution or persistence error."},
    },
)
def create_run(
    request: CreateRunRequest,
    registry: ScenarioRegistry = Depends(get_scenario_registry),
    repository: SQLiteEvaluationRepository = Depends(get_evaluation_repository),
) -> RunCreateResponse:
    """Trigger a suite evaluation run and return the structured outcome."""
    # 1. Validate suite ID
    clean_suite_id = request.suite_id.strip() if request.suite_id else ""
    if not clean_suite_id or clean_suite_id not in SUPPORTED_SUITES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unknown suite ID '{clean_suite_id}'. "
                f"Supported suites are: {sorted(list(SUPPORTED_SUITES))}."
            ),
        )

    # 2. Validate agent ID
    clean_agent_id = request.agent_id.strip() if request.agent_id else ""
    if not clean_agent_id or clean_agent_id not in SUPPORTED_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported agent ID '{clean_agent_id}'. "
                f"Supported agents are: {sorted(list(SUPPORTED_AGENTS))}."
            ),
        )

    # 3. Resolve and validate target scenarios
    if request.scenario_ids is not None:
        if len(request.scenario_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scenario_ids cannot be an empty list when explicitly provided.",
            )

        target_scenarios = []
        for sid in request.scenario_ids:
            clean_sid = sid.strip()
            scenario = registry.get(clean_sid)
            if scenario is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Scenario ID '{clean_sid}' was not found in the scenario registry.",
                )
            target_scenarios.append(scenario)
    else:
        target_scenarios = registry.list_all()

    # 4. Execute runner
    try:
        runner = ScenarioRunner()
        suite_result = runner.run_scenarios(target_scenarios)
    except Exception as e:
        logger.error("Runner execution failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution error during scenario run: {e}",
        )

    # 5. Evaluate results
    try:
        evaluator = get_default_evaluator()
        report = evaluator.evaluate_suite(suite_result, registry=registry)
    except Exception as e:
        logger.error("Evaluation engine failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation engine error: {e}",
        )

    # 6. Persist report and traces to SQLite
    try:
        repository.save_report(report, suite_result=suite_result)
    except StorageError as e:
        logger.error("Storage persistence failed for run %s: %s", report.run_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage persistence error: {e}",
        )

    metrics_summary = {
        "overall_pass_rate": report.metrics.overall_pass_rate.model_dump(),
        "security_score": report.metrics.security_score.model_dump(),
        "attack_success_rate": report.metrics.attack_success_rate.model_dump(),
        "unauthorized_prevention_rate": report.metrics.unauthorized_prevention_rate.model_dump(),
        "sensitive_data_exposure_rate": report.metrics.sensitive_data_exposure_rate.model_dump(),
        "benign_task_success_rate": report.metrics.benign_task_success_rate.model_dump(),
    }

    return RunCreateResponse(
        run_id=report.run_id,
        report_id=report.report_id,
        suite_id=clean_suite_id,
        status="completed",
        overall_outcome=report.overall_outcome,
        started_at=report.started_at,
        completed_at=report.completed_at,
        total_scenarios=report.summary_counts.total_scenarios,
        passed_count=report.summary_counts.passed_count,
        failed_count=report.summary_counts.failed_count,
        error_count=report.summary_counts.error_count,
        not_run_count=report.summary_counts.not_run_count,
        summary_counts=report.summary_counts,
        metrics_summary=metrics_summary,
    )


@router.get(
    "",
    response_model=List[EvaluationRunRecord],
    status_code=status.HTTP_200_OK,
    summary="List recent evaluation runs",
    description="Retrieve paginated summary records of completed evaluation runs, ordered newest first.",
)
def list_runs(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of evaluation runs to return.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of runs to skip for pagination.",
    ),
    repository: SQLiteEvaluationRepository = Depends(get_evaluation_repository),
) -> List[EvaluationRunRecord]:
    """Return paginated recent evaluation run records."""
    try:
        return repository.list_runs(limit=limit, offset=offset)
    except StorageError as e:
        logger.error("Failed to list runs from storage: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query evaluation runs from storage.",
        )


@router.get(
    "/{run_id}",
    response_model=EvaluationRunRecord,
    status_code=status.HTTP_200_OK,
    summary="Get evaluation run summary",
    description="Retrieve aggregate summary metrics for a specific evaluation run ID.",
    responses={
        404: {"description": "Run ID not found."},
        500: {"description": "Database query error."},
    },
)
def get_run(
    run_id: str,
    repository: SQLiteEvaluationRepository = Depends(get_evaluation_repository),
) -> EvaluationRunRecord:
    """Retrieve run summary by unique run_id."""
    clean_id = run_id.strip() if run_id else ""
    try:
        record = repository.get_run_record(clean_id)
    except StorageError as e:
        logger.error("Storage error retrieving run %s: %s", clean_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving evaluation run.",
        )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{clean_id}' was not found in storage.",
        )

    return record


@router.get(
    "/{run_id}/results",
    response_model=List[ScenarioResultResponse],
    status_code=status.HTTP_200_OK,
    summary="Get detailed per-scenario evaluation results",
    description="Retrieve detailed per-scenario results for an evaluation run in deterministic suite execution order.",
    responses={
        404: {"description": "Run ID not found."},
        500: {"description": "Storage retrieval error."},
    },
)
def get_run_results(
    run_id: str,
    repository: SQLiteEvaluationRepository = Depends(get_evaluation_repository),
) -> List[ScenarioResultResponse]:
    """Return detailed per-scenario evaluation records for the specified run."""
    clean_id = run_id.strip() if run_id else ""
    if not clean_id or not repository.run_exists(clean_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{clean_id}' was not found in storage.",
        )

    try:
        report = repository.get_report(clean_id)
    except StorageError as e:
        logger.error("Storage error retrieving report for run %s: %s", clean_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving evaluation report.",
        )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation report for run '{clean_id}' was not found in storage.",
        )

    results: List[ScenarioResultResponse] = []
    for se in report.scenario_evaluations:
        finding_summaries = [
            FindingSummaryResponse(
                finding_id=f.finding_id,
                rule_id=f.rule_id,
                rule_name=f.rule_name,
                outcome=f.outcome,
                severity=f.severity,
                message=f.message,
                timestamp=f.timestamp,
            )
            for f in se.findings
        ]
        results.append(
            ScenarioResultResponse(
                scenario_id=se.scenario_id,
                scenario_name=se.scenario_name,
                category=se.category,
                risk_level=se.risk_level,
                outcome=se.outcome,
                execution_status=se.execution_status,
                actual_status=se.actual_status,
                expected_status=se.expected_status,
                attempt_detected=se.attempt_detected,
                violation_prevented=se.violation_prevented,
                data_exposed=se.data_exposed,
                explanation=se.explanation,
                evaluated_at=se.evaluated_at,
                duration_ms=None,
                finding_count=len(se.findings),
                findings=finding_summaries,
            )
        )
    return results


@router.get(
    "/{run_id}/trace",
    response_model=List[TraceEvent],
    status_code=status.HTTP_200_OK,
    summary="Get sanitized execution traces",
    description="Retrieve chronological ordered execution trace events for an evaluation run with optional scenario filtering.",
    responses={
        404: {"description": "Run ID not found."},
        500: {"description": "Storage retrieval error."},
    },
)
def get_run_trace(
    run_id: str,
    scenario_id: Optional[str] = Query(
        default=None,
        description="Optional scenario identifier to filter trace events.",
    ),
    repository: SQLiteEvaluationRepository = Depends(get_evaluation_repository),
) -> List[TraceEvent]:
    """Return chronological ordered execution trace events for a run."""
    clean_id = run_id.strip() if run_id else ""
    if not clean_id or not repository.run_exists(clean_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{clean_id}' was not found in storage.",
        )

    clean_scenario_id = scenario_id.strip() if scenario_id else None
    try:
        events = repository.get_trace_events(clean_id, scenario_id=clean_scenario_id)
        return events
    except StorageError as e:
        logger.error("Storage error retrieving traces for run %s: %s", clean_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving execution trace events.",
        )


@router.get(
    "/{run_id}/report.json",
    response_model=EvaluationReportExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export full evaluation report",
    description="Export complete structured EvaluationReport with schema version metadata.",
    responses={
        404: {"description": "Run ID not found."},
        500: {"description": "Storage retrieval error."},
    },
)
def export_run_report(
    run_id: str,
    response: Response,
    repository: SQLiteEvaluationRepository = Depends(get_evaluation_repository),
) -> EvaluationReportExportResponse:
    """Export complete structured evaluation report JSON with schema version header and metadata."""
    clean_id = run_id.strip() if run_id else ""
    if not clean_id or not repository.run_exists(clean_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{clean_id}' was not found in storage.",
        )

    try:
        report = repository.get_report(clean_id)
    except StorageError as e:
        logger.error("Storage error retrieving report for run %s: %s", clean_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving evaluation report.",
        )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation report for run '{clean_id}' was not found in storage.",
        )

    response.headers["Content-Disposition"] = f'attachment; filename="report_{clean_id}.json"'

    return EvaluationReportExportResponse(
        schema_version="1.0.0",
        exported_at=datetime.now(timezone.utc).isoformat(),
        report=report,
    )
