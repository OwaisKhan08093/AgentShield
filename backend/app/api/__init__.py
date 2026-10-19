"""API package exporting routers and dependencies for AgentShield."""

from fastapi import APIRouter

from app.api.routes_runs import router as runs_router
from app.api.routes_scenarios import router as scenarios_router

api_router = APIRouter()
api_router.include_router(scenarios_router)
api_router.include_router(runs_router)

__all__ = [
    "api_router",
    "runs_router",
    "scenarios_router",
]
