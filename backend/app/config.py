"""Configuration settings for AgentShield."""

import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings schema and defaults."""

    project_name: str = "AgentShield"
    version: str = "0.1.0"
    description: str = "AI Agent Security Evaluation Platform"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    database_path: str = Field(
        default_factory=lambda: os.getenv("AGENTSHIELD_DATABASE_PATH", os.getenv("DATABASE_PATH", "agentshield.db")),
        description="Configurable path to SQLite database file.",
    )


settings = Settings()
