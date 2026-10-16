"""Base agent interface for AgentShield."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union
from app.models import AgentResponse, SupportRequest


class BaseAgent(ABC):
    """Abstract base class for simulated evaluation agents."""

    @abstractmethod
    def execute(self, request: Union[SupportRequest, Dict[str, Any]]) -> AgentResponse:
        """Process a structured support request and return a structured AgentResponse with trace."""
        pass
