"""
Base Command Class

Provides foundation for all CLI commands.
"""

from abc import ABC, abstractmethod
from typing import List


class BaseCommand(ABC):
    """
    Abstract base class for CLI commands.

    All commands must inherit from this class and implement execute method.
    """

    def __init__(self):
        """Initialize command."""
        self._orchestrator = None

    def set_orchestrator(self, orchestrator):
        """
        Set orchestrator reference.

        Args:
            orchestrator: Orchestrator instance
        """
        self._orchestrator = orchestrator

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Command description shown in help.

        Returns:
            Description string
        """
        pass

    @abstractmethod
    def execute(self, args: List[str]) -> bool:
        """
        Execute command.

        Args:
            args: Command arguments

        Returns:
            True to continue terminal loop, False to exit
        """
        pass
