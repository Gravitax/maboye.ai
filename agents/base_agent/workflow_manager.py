"""
Workflow Manager

Handles agent execution lifecycle including message finalization,
validation, output creation, and error handling.
"""

from typing import List

from core.logger import logger
from core.memory import MemoryManager
from agents.config import AgentConfig
from agents.types import Message, AgentOutput
from agents.base_agent.llm_message_manager import LLMMessageAgentManager


class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass


class WorkflowManager:
    """
    Manages agent workflow and lifecycle operations.

    Responsibilities:
    - Retrieving and validating final messages
    - Creating agent outputs
    - Handling errors and creating error outputs
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        llm_message_manager: LLMMessageAgentManager,
        config: AgentConfig
    ):
        """
        Initialize the workflow manager.

        Args:
            memory_manager: The central memory system.
            llm_message_manager: Manager for LLM message operations.
            config: Agent configuration.
        """
        self._memory_manager = memory_manager
        self._llm_message_manager = llm_message_manager
        self._config = config

    def get_final_message(self, messages: List[Message]) -> Message:
        """
        Retrieve or generate the final message from the conversation.

        Args:
            messages: The complete message list.

        Returns:
            The final assistant message.

        Raises:
            AgentError: If the last message has an unexpected role.
        """
        last_message = messages[-1]

        if last_message["role"] == "tool":
            logger.info("AGENT_RUN", "Loop ended on tool result, querying for final response.")
            final_message = self._llm_message_manager.get_llm_response(messages)
            messages.append(final_message)
            return final_message

        if last_message["role"] == "assistant":
            return last_message

        raise AgentError(f"Loop ended unexpectedly with role: {last_message['role']}")

    def validate_final_message(self, final_message: Message) -> None:
        """
        Validate that the final message contains content.

        Args:
            final_message: The message to validate.

        Raises:
            AgentError: If the message is empty or has no content.
        """
        if not final_message or not final_message.get("content"):
            raise AgentError("Agent failed to produce a final content response.")

    def create_agent_output(self, final_message: Message, messages: List[Message]) -> AgentOutput:
        """
        Create the final agent output object.

        Args:
            final_message: The final assistant message.
            messages: The complete message list.

        Returns:
            The formatted agent output.
        """
        history = self._memory_manager.get_conversation_history(
            max_turns=self._config.max_history_turns
        )

        output = AgentOutput(
            response=final_message["content"],
            metadata={"turn_count": len(history) // 2}
        )
        logger.info("AGENT_RUN", "Agent run completed successfully.")
        return output

    def handle_error(self, error: Exception) -> AgentOutput:
        """
        Handle errors during agent execution.

        Args:
            error: The exception that occurred.

        Returns:
            An agent output object with error information.
        """
        logger.error("AGENT_RUN", f"Agent run failed: {error}")

        self._memory_manager.add_conversation_turn(
            role="assistant",
            content=f"An error occurred: {error}"
        )

        return AgentOutput(
            response=f"An error occurred: {error}",
            success=False,
            error=str(error)
        )
