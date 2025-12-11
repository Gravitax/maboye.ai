"""
Think Loop Manager

Handles the core think-act-observe reasoning loop for agents.
"""

from typing import List, Dict, Any, Generator

from core.logger import logger
from agents.config import AgentConfig
from agents.types import Message, ToolCall
from agents.base_agent.llm_message_manager import LLMMessageAgentManager
from agents.base_agent.tools_manager import ToolsAgentManager


class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass


class ThinkLoopManager:
    """
    Manages the think-act-observe reasoning loop.

    Responsibilities:
    - Executing the core reasoning loop
    - Orchestrating LLM queries and tool executions
    - Yielding step information for observation
    """

    def __init__(
        self,
        llm_message_manager: LLMMessageAgentManager,
        tools_manager: ToolsAgentManager,
        config: AgentConfig
    ):
        """
        Initialize the think loop manager.

        Args:
            llm_message_manager: Manager for LLM message operations.
            tools_manager: Manager for tool execution.
            config: Agent configuration.
        """
        self._llm_message_manager = llm_message_manager
        self._tools_manager = tools_manager
        self._config = config

    def execute_thinking_loop(self, messages: List[Message]) -> None:
        """
        Execute the think-act-observe loop.

        Args:
            messages: The message list to process.
        """
        for step in self.think(messages, max_turns=self._config.max_agent_turns):
            logger.debug("AGENT_RUN", "Think step", {"step": step})

    def think(
        self, messages: List[Message], max_turns: int = 10
    ) -> Generator[Dict[str, Any], None, Message]:
        """
        Core reasoning loop implementing the Think-Act-Observe pattern.

        Orchestrates LLM interaction and tool usage through a generator,
        yielding each step for observation by the caller.

        Args:
            messages: The current conversation history.
            max_turns: Maximum number of turns to prevent infinite loops.

        Yields:
            Dictionary representing current step (llm_response, tool_call, tool_results).

        Returns:
            Final message from the LLM containing the answer.

        Raises:
            AgentError: If maximum turns exceeded.
        """
        for turn in range(max_turns):
            logger.info("AGENT", f"Starting turn {turn + 1}/{max_turns}")

            assistant_message = self._get_llm_response(messages)
            messages.append(assistant_message)
            yield {"llm_response": assistant_message}

            if not assistant_message.get("tool_calls"):
                logger.info("AGENT", "No tool calls requested. Final response received.")
                return assistant_message

            tool_calls: List[ToolCall] = assistant_message["tool_calls"]
            yield {"tool_calls": tool_calls}

            tool_results = self._tools_manager.execute_and_store_tools(tool_calls, messages)
            yield {"tool_results": tool_results}

        raise AgentError(f"Agent exceeded maximum turns ({max_turns}).")

    def _get_llm_response(self, messages: List[Message]) -> Message:
        """
        Get response from LLM and convert to internal message format.

        Args:
            messages: Current conversation history.

        Returns:
            Converted assistant message in internal format.
        """
        return self._llm_message_manager.get_llm_response(messages)
