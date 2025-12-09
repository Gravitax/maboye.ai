"""
Default Agent Implementation

This module provides a concrete implementation of the BaseAgent, inheriting all
core functionality including the memory-managed run loop.
"""

from typing import List, Dict, Any, Generator

from agents.agent import BaseAgent, LLMWrapper
from agents.config import AgentConfig
from agents.types import Message, AgentOutput
from core.prompt_builder import PromptBuilder
from core.tool_scheduler import ToolScheduler
from core.memory import MemoryManager
from core.logger import logger


class DefaultAgent(BaseAgent):
    """
    A default, concrete agent implementation that inherits its entire run
    loop and memory management from BaseAgent.

    This agent is specialized purely through the configuration and dependencies
    (system prompt, tools, etc.) it is initialized with.
    """

    def __init__(
        self,
        llm: LLMWrapper,
        tool_scheduler: ToolScheduler,
        prompt_builder: PromptBuilder,
        memory_manager: MemoryManager,
        config: AgentConfig,
    ):
        """Initializes the DefaultAgent, passing all dependencies to the parent."""
        self._log_initialization_start(config)
        super().__init__(llm, tool_scheduler, prompt_builder, memory_manager, config)
        self._log_initialization_complete(config)

    def run(self, user_prompt: str) -> AgentOutput:
        """
        Main entry point with logging of workflow stages.
        """
        self._log_run_start(user_prompt)
        output = super().run(user_prompt)
        self._log_run_complete(output)
        return output

    def _think(
        self, messages: List[Message], max_turns: int = 10
    ) -> Generator[Dict[str, Any], None, Message]:
        """
        Core reasoning loop with step-by-step logging.
        """
        self._log_think_start(messages, max_turns)

        for step in super()._think(messages, max_turns):
            self._log_think_step(step)
            yield step

    def _log_initialization_start(self, config: AgentConfig) -> None:
        """Logs agent initialization start."""
        logger.info(
            "DEFAULT_AGENT",
            f"Initializing agent '{config.name}'",
            {"max_turns": config.max_agent_turns, "max_history": config.max_history_turns}
        )

    def _log_initialization_complete(self, config: AgentConfig) -> None:
        """Logs agent initialization completion."""
        logger.debug("DEFAULT_AGENT", f"Agent '{config.name}' initialized successfully")

    def _log_run_start(self, user_prompt: str) -> None:
        """Logs start of agent run."""
        prompt_preview = user_prompt[:100] + "..." if len(user_prompt) > 100 else user_prompt
        logger.info(
            "DEFAULT_AGENT",
            f"Starting run for prompt: '{prompt_preview}'",
            {"prompt_length": len(user_prompt)}
        )

    def _log_run_complete(self, output: AgentOutput) -> None:
        """Logs completion of agent run."""
        logger.info(
            "DEFAULT_AGENT",
            "Run completed",
            {
                "success": output.success,
                "response_length": len(output.response) if output.response else 0
            }
        )

    def _log_think_start(self, messages: List[Message], max_turns: int) -> None:
        """Logs start of think loop."""
        logger.info(
            "DEFAULT_AGENT",
            f"Starting think loop",
            {"message_count": len(messages), "max_turns": max_turns}
        )

    def _log_think_step(self, step: Dict[str, Any]) -> None:
        """Logs individual think step."""
        if "llm_response" in step:
            self._log_llm_response(step["llm_response"])
        elif "tool_calls" in step:
            self._log_tool_calls(step["tool_calls"])
        elif "tool_results" in step:
            self._log_tool_results(step["tool_results"])

    def _log_llm_response(self, message: Message) -> None:
        """Logs LLM response."""
        has_tool_calls = bool(message.get("tool_calls"))
        content_preview = (message.get("content", "")[:150] + "...") if message.get("content") else ""

        logger.info(
            "DEFAULT_AGENT",
            "LLM response received",
            {
                "has_content": bool(message.get("content")),
                "content_preview": content_preview,
                "has_tool_calls": has_tool_calls,
                "tool_count": len(message.get("tool_calls", []))
            }
        )

    def _log_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> None:
        """Logs tool call requests."""
        tool_names = [tc["name"] for tc in tool_calls]
        logger.info(
            "DEFAULT_AGENT",
            f"Requesting {len(tool_calls)} tool(s)",
            {"tools": tool_names}
        )

    def _log_tool_results(self, tool_results: List[Dict[str, Any]]) -> None:
        """Logs tool execution results."""
        for result in tool_results:
            result_preview = str(result["result"])[:150]
            logger.debug(
                "DEFAULT_AGENT",
                f"Tool '{result['tool_name']}' executed",
                {
                    "success": result["success"],
                    "execution_time": result["execution_time"],
                    "result_preview": result_preview
                }
            )
