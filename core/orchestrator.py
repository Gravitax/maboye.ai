"""
Orchestrator for managing agent workflows.

This module centralizes the setup and coordination of all core components:
LLM wrapper, Memory Manager, Tool Scheduler, Prompt Builder, and the Agent itself.
It provides a clean interface for the main application loop to interact with the agent system.
"""

from typing import Optional, Dict, Any, List

from core.logger import logger
from core.llm_wrapper import LLMWrapper, LLMWrapperConfig
from core.memory import MemoryManager
from core.tool_scheduler import ToolScheduler
from core.prompt_builder import PromptBuilder
from tools.tool_base import get_registry
from tools.implementations import register_all_tools
from agents.default_agent import DefaultAgent
from agents.config import AgentConfig
from agents.types import AgentOutput


class Orchestrator:
    """
    The central coordinator for the agent system.

    Manages the lifecycle and interaction between the LLM, Memory, Tools,
    Prompt Builder, and the Agent. It provides a simplified interface
    for external components (like the main application) to interact
    with the complex agent ecosystem.
    """

    def __init__(
        self,
        llm_config: Optional[LLMWrapperConfig] = None,
        agent_config: Optional[AgentConfig] = None,
    ):
        """
        Initializes the Orchestrator and all its components.

        Args:
            llm_config: Configuration for the LLM wrapper.
            agent_config: Configuration for the agent.
        """
        self._llm: LLMWrapper
        self._memory_manager: MemoryManager
        self._tool_scheduler: ToolScheduler
        self._prompt_builder: PromptBuilder
        self._agent: DefaultAgent # Can be made configurable for different agent types

        self._llm_config = llm_config or LLMWrapperConfig()
        self._agent_config = agent_config or AgentConfig()

        logger.info("ORCHESTRATOR", "Initializing all components...")
        self._setup_components()
        logger.info("ORCHESTRATOR", "All components initialized.")

    def _setup_components(self) -> None:
        """Sets up the LLM, Memory, Tools, Prompt Builder, and Agent."""

        # 1. Initialize Memory Manager
        self._memory_manager = MemoryManager(
            conversation_size=self._agent_config.max_history_turns
        )
        logger.info("ORCHESTRATOR", "Memory manager initialized.")

        # 2. Register all tools and get the registry
        register_all_tools()
        tool_registry = get_registry()
        logger.info("ORCHESTRATOR", "Tools registered.", {"count": len(tool_registry.list_tools())})

        # 3. Initialize LLM Wrapper
        self._llm = LLMWrapper(self._llm_config)
        logger.info("ORCHESTRATOR", "LLM wrapper initialized.")

        # 4. Initialize Tool Scheduler
        self._tool_scheduler = ToolScheduler(registry=tool_registry)
        logger.info("ORCHESTRATOR", "Tool scheduler initialized.")

        # 5. Initialize Prompt Builder
        self._prompt_builder = PromptBuilder(
            system_prompt=self._agent_config.system_prompt,
            tool_registry=tool_registry
        )
        logger.info("ORCHESTRATOR", "Prompt builder initialized.")

        # 6. Initialize the Agent
        self._agent = DefaultAgent(
            llm=self._llm,
            tool_scheduler=self._tool_scheduler,
            prompt_builder=self._prompt_builder,
            memory_manager=self._memory_manager,
            config=self._agent_config,
        )
        logger.info("ORCHESTRATOR", f"{self._agent_config.name} initialized.")

    def process_user_input(self, user_input: str) -> AgentOutput:
        """
        Processes a user's input through the agent system.

        Args:
            user_input: The raw text input from the user.

        Returns:
            An AgentOutput object containing the agent's response and metadata.
        """
        logger.info("ORCHESTRATOR", "Processing user input.", {"input": user_input[:100]})
        try:
            agent_output = self._agent.run(user_input)
            logger.info("ORCHESTRATOR", "User input processed successfully.")
            return agent_output
        except Exception as e:
            logger.error("ORCHESTRATOR", "Error processing user input.", {"error": str(e)})
            return AgentOutput(
                response=f"An internal orchestrator error occurred: {e}",
                success=False,
                error=str(e)
            )

    def reset_conversation(self) -> None:
        """Clears the conversation history in the memory manager."""
        logger.info("ORCHESTRATOR", "Resetting conversation.")
        self._memory_manager.clear_conversation()

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Retrieves statistics from the memory manager.

        Returns:
            A dictionary of memory statistics.
        """
        return self._memory_manager.get_stats()

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retrieves information about the configured agent.

        Returns:
            A dictionary containing agent configuration details.
        """
        return self._agent._config.model_dump() # Assuming AgentConfig can be dumped or converted

    def get_tool_info(self) -> List[Dict[str, Any]]:
        """
        Retrieves information about all registered tools.

        Returns:
            A list of dictionaries, each describing a tool.
        """
        return get_registry().get_all_tools_info()