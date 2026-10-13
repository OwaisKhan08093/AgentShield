"""Configuration settings for AgentShield."""

from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings schema and defaults."""

    project_name: str = "AgentShield"
    version: str = "0.1.0"
    description: str = "AI Agent Security Evaluation Platform"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000


settings = Settings()
