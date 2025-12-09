"""
Default Agent Implementation

This module provides a concrete implementation of the BaseAgent, inheriting all
core functionality including the memory-managed run loop.
"""

from agents.agent import BaseAgent, LLMWrapper
from agents.config import AgentConfig
from core.prompt_builder import PromptBuilder
from core.tool_scheduler import ToolScheduler
from core.memory import MemoryManager


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
        super().__init__(llm, tool_scheduler, prompt_builder, memory_manager, config)
