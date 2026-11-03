"""Abstract base class for all AI agents.

Placeholder for Fase 1: defines the common interface that every concrete
agent will have to implement in later phases.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Common interface shared by every agent in the system."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def run(self, input_data: Any) -> Any:
        """Execute the agent's main task on the given input."""
        raise NotImplementedError
