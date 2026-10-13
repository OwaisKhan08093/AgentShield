"""Main FastAPI application entrypoint for AgentShield."""

from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=settings.description,
)


@app.get("/")
def read_root():
    """Root endpoint returning project identity and status."""
    return {
        "name": settings.project_name,
        "status": "online",
        "description": settings.description,
        "version": settings.version,
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
