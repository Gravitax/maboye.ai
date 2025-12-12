"""
Default Agent Implementation

This module provides a concrete implementation of the BaseAgent, inheriting all
core functionality including the memory-managed run loop and structured logging.
"""

from agents.base_agent import BaseAgent
from agents.config import AgentConfig
from agents.types import AgentOutput
from agents.log_manager import LogAgentManager
from core.llm_wrapper.llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from core.memory import MemoryManager
from tools.tool_base import ToolRegistry


class DefaultAgent(LogAgentManager, BaseAgent):
    """
    A default, concrete agent implementation that inherits its entire run
    loop and memory management from BaseAgent, and logging capabilities
    from LogAgentManager.

    This agent is specialized purely through the configuration and dependencies
    (system prompt, tools, etc.) it is initialized with.
    """

    def __init__(
        self,
        llm: LLMWrapper,
        tool_scheduler: ToolScheduler,
        tool_registry: ToolRegistry,
        memory_manager: MemoryManager,
        config: AgentConfig,
    ):
        """Initializes the DefaultAgent, passing all dependencies to the parent."""
        self._log_initialization_start(config)
        super().__init__(llm, tool_scheduler, tool_registry, memory_manager, config)
        self._log_initialization_complete(config)

    def run(self, user_prompt: str) -> AgentOutput:
        """
        Main entry point with logging of workflow stages.
        """
        self._log_run_start(user_prompt)
        output = super().run(user_prompt)
        self._log_run_complete(output)
        return output
