"""
Log Agent Manager

Provides structured logging capabilities for agents.
Agents can inherit from this class to get comprehensive logging support.
"""

from typing import List, Dict, Any

from core.logger import logger
from agents.config import AgentConfig
from agents.types import AgentOutput, Message


class LogAgentManager:
    """
    Base class providing structured logging for agents.

    Agents that inherit from this class gain access to standardized
    logging methods for initialization, execution, and think loop operations.
    """

    def _log_initialization_start(self, config: AgentConfig) -> None:
        """
        Log agent initialization start.

        Args:
            config: Agent configuration being used.
        """
        logger.info(
            "AGENT_LOG",
            f"Initializing agent '{config.name}'",
            {"max_turns": config.max_agent_turns, "max_history": config.max_history_turns}
        )

    def _log_initialization_complete(self, config: AgentConfig) -> None:
        """
        Log agent initialization completion.

        Args:
            config: Agent configuration that was initialized.
        """
        logger.debug("AGENT_LOG", f"Agent '{config.name}' initialized successfully")

    def _log_run_start(self, user_prompt: str) -> None:
        """
        Log start of agent run.

        Args:
            user_prompt: The user's input prompt.
        """
        logger.info(
            "AGENT_LOG",
            f"Starting run for prompt: '{user_prompt}'",
            {"prompt_length": len(user_prompt)}
        )

    def _log_run_complete(self, output: AgentOutput) -> None:
        """
        Log completion of agent run.

        Args:
            output: The agent's output result.
        """
        logger.info(
            "AGENT_LOG",
            "Run completed",
            {
                "success": output.success,
                "response_length": len(output.response) if output.response else 0
            }
        )

    def _log_think_start(self, messages: List[Message], max_turns: int) -> None:
        """
        Log start of think loop.

        Args:
            messages: Current message history.
            max_turns: Maximum number of turns allowed.
        """
        logger.info(
            "AGENT_LOG",
            "Starting think loop",
            {"message_count": len(messages), "max_turns": max_turns}
        )

    def _log_think_step(self, step: Dict[str, Any]) -> None:
        """
        Log individual think step.

        Args:
            step: Dictionary containing step information.
        """
        if "llm_response" in step:
            self._log_llm_response(step["llm_response"])
        elif "tool_calls" in step:
            self._log_tool_calls(step["tool_calls"])
        elif "tool_results" in step:
            self._log_tool_results(step["tool_results"])

    def _log_llm_response(self, message: Message) -> None:
        """
        Log LLM response.

        Args:
            message: The LLM's response message.
        """
        has_tool_calls = bool(message.get("tool_calls"))
        content = message.get("content", "") or ""

        logger.info(
            "AGENT_LOG",
            "LLM response received",
            {
                "has_content": bool(message.get("content")),
                "content": content,
                "has_tool_calls": has_tool_calls,
                "tool_count": len(message.get("tool_calls", []))
            }
        )

    def _log_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> None:
        """
        Log tool call requests.

        Args:
            tool_calls: List of tool calls being requested.
        """
        tool_names = [tc["name"] for tc in tool_calls]
        logger.info(
            "AGENT_LOG",
            f"Requesting {len(tool_calls)} tool(s)",
            {"tools": tool_names}
        )

    def _log_tool_results(self, tool_results: List[Dict[str, Any]]) -> None:
        """
        Log tool execution results.

        Args:
            tool_results: List of tool execution results.
        """
        for result in tool_results:
            logger.debug(
                "AGENT_LOG",
                f"Tool '{result['tool_name']}' executed",
                {
                    "success": result["success"],
                    "execution_time": result["execution_time"],
                    "result": str(result["result"])
                }
            )
