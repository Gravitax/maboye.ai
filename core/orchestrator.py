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
        agents: Optional[List[Any]] = None,
    ):
        """
        Initializes the Orchestrator and all its components.

        Args:
            llm_config: Configuration for the LLM wrapper.
            agents: List of agents to use. If None, a default agent will be created.
        """
        self._llm: LLMWrapper
        self._memory_manager: MemoryManager
        self._tool_scheduler: ToolScheduler
        self._tool_registry: Any
        self._agents: List[Any] = []
        self._current_agent: Any = None

        self._llm_config = llm_config or LLMWrapperConfig()

        logger.info("ORCHESTRATOR", "Initializing all components...")
        self._setup_components()

        if agents:
            self._agents = agents
            self._current_agent = agents[0] if agents else None
            logger.info("ORCHESTRATOR", f"Using {len(agents)} provided agent(s).")
        else:
            logger.warning("ORCHESTRATOR", "No agents provided. Agent must be set later.")

        logger.info("ORCHESTRATOR", "All components initialized.")

    def _setup_components(self) -> None:
        """Sets up the LLM, Memory, Tools (shared components)."""

        # 1. Initialize Memory Manager (using default max_history_turns for now)
        self._memory_manager = MemoryManager(
            conversation_size=10  # Default value, can be overridden by agent config
        )
        logger.info("ORCHESTRATOR", "Memory manager initialized.")

        # 2. Register all tools and get the registry
        register_all_tools()
        self._tool_registry = get_registry()
        logger.info("ORCHESTRATOR", "Tools registered.", {"count": len(self._tool_registry.list_tools())})

        # 3. Initialize LLM Wrapper
        self._llm = LLMWrapper(self._llm_config)
        logger.info("ORCHESTRATOR", "LLM wrapper initialized.")

        # 4. Initialize Tool Scheduler
        self._tool_scheduler = ToolScheduler(registry=self._tool_registry)
        logger.info("ORCHESTRATOR", "Tool scheduler initialized.")

    def get_components(self) -> tuple:
        """
        Get shared components for agent creation.

        Returns:
            Tuple of (llm, tool_scheduler, tool_registry, memory_manager)
        """
        return (
            self._llm,
            self._tool_scheduler,
            self._tool_registry,
            self._memory_manager
        )

    def set_agents(self, agents: List[Any]):
        """
        Set the list of agents to use.

        Args:
            agents: List of agents to use
        """
        if not agents:
            logger.warning("ORCHESTRATOR", "Empty agent list provided.")
            return

        self._agents = agents
        self._current_agent = agents[0]
        logger.info("ORCHESTRATOR", f"Set {len(agents)} agent(s). Current agent: {agents[0]._config.name}")

    def process_user_input(self, user_input: str) -> AgentOutput:
        """
        Processes a user's input through the agent system.

        Args:
            user_input: The raw text input from the user.

        Returns:
            An AgentOutput object containing the agent's response and metadata.
        """
        if not self._current_agent:
            logger.error("ORCHESTRATOR", "No agent available to process input.")
            return AgentOutput(
                response="No agent is currently configured.",
                success=False,
                error="No agent available"
            )

        logger.info("ORCHESTRATOR", "Processing user input.", {"input": user_input})
        try:
            agent_output = self._current_agent.run(user_input)
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
        if not self._current_agent:
            return {"error": "No agent configured"}
        return self._current_agent._config.model_dump() # Assuming AgentConfig can be dumped or converted

    def get_tool_info(self) -> List[Dict[str, Any]]:
        """
        Retrieves information about all registered tools.

        Returns:
            A list of dictionaries, each describing a tool.
        """
        return get_registry().get_all_tools_info()

    def get_memory_content(self, memory_type_str: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves the content of a specific memory type.

        Args:
            memory_type_str: Memory type name (conversation)

        Returns:
            List of memory entries or None if invalid type
        """
        from core.memory import MemoryType

        memory_type_map = {
            "conversation": MemoryType.CONVERSATION
        }

        if memory_type_str.lower() not in memory_type_map:
            return None

        memory_type = memory_type_map[memory_type_str.lower()]
        memory = self._memory_manager.get(memory_type)
        return memory.get_all()