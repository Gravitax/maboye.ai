"""
Reset Command

Clear conversation history.
"""

from typing import List
from .base_command import BaseCommand
from core.logger import logger


class ResetCommand(BaseCommand):
    """Command to reset conversation history."""

    @property
    def description(self) -> str:
        """Command description."""
        return "Reset the conversation history."

    def execute(self, args: List[str]) -> bool:
        """Execute reset command."""
        self._orchestrator.reset_conversation()
        print("\nConversation history has been reset.\n")
        logger.info("CLI_COMMAND", "Conversation memory reset by user.")
        return True
