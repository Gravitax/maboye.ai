"""
Agent Command

Display agent configuration and information.
"""

from typing import List
from .base_command import BaseCommand


class AgentCommand(BaseCommand):
    """Command to show agent configuration."""

    @property
    def description(self) -> str:
        """Command description."""
        return "Show agent configuration."

    def execute(self, args: List[str]) -> bool:
        """Execute agent command."""
        agent_info = self._orchestrator.get_agent_info()
        print("\nAgent Information:")
        print("-" * 60)

        for key, value in agent_info.items():
            print(f"- {key}: {value}")

        print("-" * 60)
        print()
        return True
