"""
Orchestrator for managing agent workflows.

This module centralizes the setup and coordination of all core components:
LLM wrapper, Memory Manager, Tool Scheduler, Prompt Builder, and the Agent itself.
It provides a clean interface for the main application loop to interact with the agent system.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from core.logger import logger
from core.llm_wrapper import LLMWrapper, LLMWrapperConfig
from core.tool_scheduler import ToolScheduler
from tools.tool_base import get_registry
from tools.implementations import register_all_tools
from agents.types import AgentOutput
from core.repositories import InMemoryMemoryRepository, InMemoryAgentRepository
from core.services import MemoryManager, LRUCache, AgentFactory
from core.services.execution_manager import ExecutionManager
from core.services.memory_formatter import MemoryFormatter
from core.services.context_manager import ContextManager

class Orchestrator:
    """
    Central coordinator for the multi-agent system.

    Manages repositories, services, and execution of agents using
    the domain-driven architecture.

    Attributes:
        _memory_repository: Memory persistence
        _agent_repository: Agent persistence
        _memory_manager: Memory coordination service
        _agent_factory: Agent instance creation
    """

    def __init__(self, llm_config: Optional[LLMWrapperConfig] = None):
        """
        Initialize the orchestrator with all components.

        Args:
            llm_config: Configuration for the LLM wrapper
        """
        self._llm_config = llm_config or LLMWrapperConfig()

        # Core infrastructure
        self._llm: LLMWrapper
        self._tool_scheduler: ToolScheduler
        self._tool_registry: Any

        # Domain architecture components
        self._memory_repository: InMemoryMemoryRepository
        self._agent_repository: InMemoryAgentRepository
        self._memory_manager: MemoryManager
        self._memory_formatter: MemoryFormatter
        self._execution_manager: ExecutionManager
        self._context_manager: ContextManager

        logger.info("ORCHESTRATOR", "Initializing orchestrator components")
        self._setup_components()
        logger.info("ORCHESTRATOR", "Orchestrator initialized successfully")

    def _setup_components(self) -> None:
        """Setup all orchestrator components in correct order."""

        # 1. Initialize repositories
        self._memory_repository = InMemoryMemoryRepository()
        self._agent_repository = InMemoryAgentRepository()
        logger.info("ORCHESTRATOR", "Repositories initialized")

        # 2. Initialize memory coordinator with LRU cache
        cache_strategy = LRUCache(max_size=100)
        self._memory_manager = MemoryManager(
            memory_repository=self._memory_repository,
            cache_strategy=cache_strategy
        )
        logger.info("ORCHESTRATOR", "Memory coordinator initialized")

        # 3. Register tools
        register_all_tools()
        self._tool_registry = get_registry()
        logger.info("ORCHESTRATOR", "Tools registered", {
            "count": len(self._tool_registry.list_tools())
        })

        # 4. Initialize LLM wrapper
        self._llm = LLMWrapper(self._llm_config)
        logger.info("ORCHESTRATOR", "LLM wrapper initialized")

        # 5. Initialize tool scheduler
        self._tool_scheduler = ToolScheduler(registry=self._tool_registry)
        logger.info("ORCHESTRATOR", "Tool scheduler initialized")

        # Initialize context manager
        self._context_manager = ContextManager(self._memory_repository)
        logger.info("ORCHESTRATOR", "Context manager initialized")

        # ===== OPTION B: Initialize AgentFactory (commented for future use) =====
        # # 6. Initialize agent factory for creating specialized agents
        # from core.services import AgentFactory
        # self._agent_factory = AgentFactory(
        #     llm=self._llm,
        #     tool_scheduler=self._tool_scheduler,
        #     tool_registry=self._tool_registry,
        #     memory=self._memory_manager
        # )
        # logger.info("ORCHESTRATOR", "Agent factory initialized")
        # ========================================================================

        # Initialize execution manager
        self._execution_manager = ExecutionManager(
            llm=self._llm,
            tool_scheduler=self._tool_scheduler,
            tool_registry=self._tool_registry,
            memory_manager=self._memory_manager,
            context_manager=self._context_manager
            # agent_factory=self._agent_factory,  # Option B: pass factory for routing
            # agent_repository=self._agent_repository  # Option B: pass repository
        )
        logger.info("ORCHESTRATOR", "Execution manager initialized")

        # Initialize memory formatter
        self._memory_formatter = MemoryFormatter(self._memory_repository)
        logger.info("ORCHESTRATOR", "Memory formatter initialized")

    def get_agent_repository(self) -> InMemoryAgentRepository:
        """Get the agent repository."""
        return self._agent_repository

    def get_memory_manager(self) -> MemoryManager:
        """Get the memory coordinator."""
        return self._memory_manager

    def get_tool_info(self) -> list:
        """
        Get information about all registered tools.

        Returns:
            List of tool info dictionaries
        """
        return self._tool_registry.get_all_tools_info()

    def _save_orchestrator_output(self, result: AgentOutput, conversation_id: str = None) -> None:
        """
        Save orchestrator output to memory.

        Args:
            result: AgentOutput with orchestrator response
            conversation_id: ID of the conversation
        """
        metadata = result.metadata
        if conversation_id:
            metadata["conversation_id"] = conversation_id

        self._memory_manager.save_conversation_turn(
            agent_id="orchestrator",
            role="assistant",
            content=result.response,
            metadata=metadata
        )

    def process_user_input(self, user_input: str) -> AgentOutput:
        """
        Process user input through autonomous workflow with dynamic todolist.

        Workflow:
        1. Create StateManager and initialize todolist from user input
        2. ExecutionManager executes steps with dynamic todolist updates
        3. Each step can add/remove/modify todolist based on findings
        4. Loop continues until all steps completed
        5. Final aggregated result returned

        Args:
            user_input: User input to process

        Returns:
            AgentOutput with final result
        """
        logger.info("ORCHESTRATOR", "Processing user input with autonomous workflow")

        user_input = user_input.strip()
        # Get conversation context from orchestrator history
        context = self._context_manager.format_context_as_string(
            agent_id="orchestrator",
            max_turns=10
        )
        logger.info("ORCHESTRATOR", "context", {"context":context})

        # Generate unique conversation ID
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

        # Save user input in orchestrator memory
        self._memory_manager.save_conversation_turn(
            agent_id="orchestrator",
            role="user",
            content=user_input,
            metadata={"conversation_id": conversation_id}
        )

        try:
            # Execute autonomous workflow
            result = self._execution_manager.execute(user_input, context)
            self._save_orchestrator_output(result, conversation_id)
            return result

        except Exception as e:
            logger.error("ORCHESTRATOR", "Execution failed", {"error": str(e)})
            result = AgentOutput(
                response=f"Error executing: {e}",
                success=False,
                error=str(e)
            )
            # Save error output
            self._save_orchestrator_output(result, conversation_id)
            return result

    def get_memory_manager_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics formatted for the /memory command.

        Returns:
            Dictionary with conversation and agent stats
        """
        return {
            "conversation": self._memory_formatter.get_conversation_stats(),
            "agents": self._memory_formatter.get_agent_stats()
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Alias for get_memory_manager_stats() for backward compatibility.

        Returns:
            Dictionary with conversation and agent stats
        """
        return self.get_memory_manager_stats()

    def reset_conversation(self) -> None:
        """Clear all conversation memory for active agents."""
        active_agents = self._agent_repository.find_active()

        for agent in active_agents:
            agent_id = agent.get_agent_id()
            self._memory_manager.clear_agent_memory(agent_id)
            logger.info("ORCHESTRATOR", f"Cleared memory for agent {agent.get_agent_name()}")

        # Also clear memory for orchestrator and mock agent
        self._memory_manager.clear_agent_memory("orchestrator")
        self._memory_manager.clear_agent_memory("mock_agent")
        logger.info("ORCHESTRATOR", "Cleared memory for orchestrator and mock_agent")

    def get_memory_manager_content(self, mem_type: str, agent_id: Optional[str] = None) -> list:
        """
        Get memory content for a specific type.

        Args:
            mem_type: Type of memory to retrieve ('conversation' or 'agents')
            agent_id: Optional. Specific agent ID to retrieve details for

        Returns:
            List of formatted strings ready for display
        """
        if mem_type == "conversation":
            return self._memory_formatter.format_conversations()
        elif mem_type == "agents":
            if agent_id:
                # Get detail for specific agent
                detail = self._memory_formatter.get_agent_detail(agent_id)
                return [detail] if detail else []
            else:
                # Get list of all agents
                return self._memory_formatter.format_agents()
        else:
            return []

    def get_memory_content(self, mem_type: str, agent_id: Optional[str] = None) -> list:
        """
        Alias for get_memory_manager_content() for backward compatibility.

        Args:
            mem_type: Type of memory to retrieve ('conversation' or 'agents')
            agent_id: Optional. Specific agent ID to retrieve details for

        Returns:
            List of formatted strings ready for display
        """
        return self.get_memory_manager_content(mem_type, agent_id)
