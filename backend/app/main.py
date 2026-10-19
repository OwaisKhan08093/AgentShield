"""Main FastAPI application entrypoint for AgentShield."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import settings

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=settings.description,
)

# Enable CORS for local development and frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include business API routes
app.include_router(api_router)


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
