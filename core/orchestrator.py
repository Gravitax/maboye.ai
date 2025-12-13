"""
Orchestrator for managing agent workflows.

This module centralizes the setup and coordination of all core components:
LLM wrapper, Memory Manager, Tool Scheduler, Prompt Builder, and the Agent itself.
It provides a clean interface for the main application loop to interact with the agent system.
"""

import json
from typing import Optional, Dict, Any

from core.logger import logger
from core.llm_wrapper import LLMWrapper, LLMWrapperConfig
from core.tool_scheduler import ToolScheduler
from tools.tool_base import get_registry
from tools.implementations import register_all_tools
from agents.types import AgentOutput
from core.repositories import InMemoryMemoryRepository, InMemoryAgentRepository
from core.services import AgentMemoryCoordinator, LRUCache, AgentExecutionService, ExecutionOptions, AgentFactory


class Orchestrator:
    """
    Central coordinator for the multi-agent system.

    Manages repositories, services, and execution of agents using
    the domain-driven architecture.

    Attributes:
        _memory_repository: Memory persistence
        _agent_repository: Agent persistence
        _memory_coordinator: Memory coordination service
        _agent_factory: Agent instance creation
        _execution_service: Agent execution with metrics
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
        self._memory_coordinator: AgentMemoryCoordinator
        self._agent_factory: AgentFactory
        self._execution_service: AgentExecutionService

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
        self._memory_coordinator = AgentMemoryCoordinator(
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

        # 6. Initialize agent factory
        self._agent_factory = AgentFactory(
            llm=self._llm,
            tool_scheduler=self._tool_scheduler,
            tool_registry=self._tool_registry,
            memory_coordinator=self._memory_coordinator
        )
        logger.info("ORCHESTRATOR", "Agent factory initialized")

        # 7. Initialize execution service
        self._execution_service = AgentExecutionService(
            agent_repository=self._agent_repository,
            memory_coordinator=self._memory_coordinator,
            agent_factory=self._agent_factory
        )
        logger.info("ORCHESTRATOR", "Execution service initialized")

    def get_agent_repository(self) -> InMemoryAgentRepository:
        """Get the agent repository."""
        return self._agent_repository

    def get_memory_coordinator(self) -> AgentMemoryCoordinator:
        """Get the memory coordinator."""
        return self._memory_coordinator

    def get_execution_service(self) -> AgentExecutionService:
        """Get the execution service."""
        return self._execution_service

    def process_user_input(self, user_input: str) -> AgentOutput:
        """
        Process user input through the agent system.

        Routes to appropriate agent based on input content,
        then executes the selected agent.

        Args:
            user_input: User's message

        Returns:
            AgentOutput with response and metadata
        """
        logger.info("ORCHESTRATOR", "Processing user input", {
            "input_length": len(user_input)
        })

        # For now, always use the test workflow
        test_name = user_input.strip()
        logger.info("ORCHESTRATOR", f"Executing test plan: {test_name}")
        try:
            plan = self._llm.test(test_name)
            # For now, just return the plan as a string
            # In the future, this will trigger the plan execution workflow
            response_str = json.dumps(plan.model_dump(), indent=2)
            return AgentOutput(
                response=f"Received test plan '{test_name}':\n{response_str}",
                success=True
            )
        except Exception as e:
            logger.error("ORCHESTRATOR", "Test plan execution failed", {"error": str(e)})
            return AgentOutput(
                response=f"Error executing test plan: {e}",
                success=False,
                error=str(e)
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the orchestrator state.

        Returns:
            Dictionary with agents, memory, and execution stats
        """
        return {
            "agents": {
                "total": self._agent_repository.count(),
                "active": len(self._agent_repository.find_active())
            },
            "memory": self._memory_coordinator.get_memory_stats(),
            "execution": self._execution_service.get_execution_stats()
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics formatted for the /memory command.

        Returns:
            Dictionary with conversation stats
        """
        active_agents = self._agent_repository.find_active()

        if not active_agents:
            return {
                "conversation": {
                    "size": 0,
                    "is_empty": True
                }
            }

        agent = active_agents[0]
        agent_id = agent.get_agent_id()

        all_turns = self._memory_repository.get_conversation_history(
            agent_id=agent_id,
            max_turns=None
        )

        return {
            "conversation": {
                "size": len(all_turns),
                "is_empty": len(all_turns) == 0
            }
        }

    def reset_conversation(self) -> None:
        """Clear all conversation memory for active agents."""
        active_agents = self._agent_repository.find_active()

        for agent in active_agents:
            agent_id = agent.get_agent_id()
            self._memory_coordinator.clear_agent_memory(agent_id)
            logger.info("ORCHESTRATOR", f"Cleared memory for agent {agent.get_agent_name()}")

    def get_memory_content(self, mem_type: str) -> list:
        """
        Get memory content for a specific type.

        Args:
            mem_type: Type of memory to retrieve (e.g., 'conversation')

        Returns:
            List of memory entries
        """
        if mem_type != "conversation":
            return []

        active_agents = self._agent_repository.find_active()

        if not active_agents:
            return []

        agent = active_agents[0]
        agent_id = agent.get_agent_id()

        # Get all conversation turns
        turns = self._memory_repository.get_conversation_history(
            agent_id=agent_id,
            max_turns=None
        )

        # Format turns for display
        formatted_entries = []
        for turn in turns:
            formatted_entries.append({
                "timestamp": turn.get("timestamp", "N/A"),
                "data": {
                    "role": turn.get("role", "unknown"),
                    "content": turn.get("content", ""),
                    "context": turn.get("metadata", {})
                },
                "metadata": turn.get("metadata", {})
            })

        return formatted_entries