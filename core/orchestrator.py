"""
Orchestrator for managing agent workflows.

This module centralizes the setup and coordination of all core components:
LLM wrapper, Memory Manager, Tool Scheduler, Prompt Builder, and the Agent itself.
It provides a clean interface for the main application loop to interact with the agent system.
"""

import json
from typing import Optional, Dict, Any

from core.logger import logger
from tests.test_utils.mock_agent import MockAgent
from core.services.plan_execution_service import PlanExecutionService
from core.llm_wrapper import LLMWrapper, LLMWrapperConfig
from core.tool_scheduler import ToolScheduler
from tools.tool_base import get_registry
from tools.implementations import register_all_tools
from agents.types import AgentOutput
from core.repositories import InMemoryMemoryRepository, InMemoryAgentRepository
from core.domain import RegisteredAgent, ExecutionPlan, ExecutionStep, ActionStep
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

        # Persistent agent for execution (keeps conversation history)
        self._persistent_agent: Optional[MockAgent] = None

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
            agent_factory=self._agent_factory,
            llm=self._llm,
            tool_scheduler=self._tool_scheduler,
            tool_registry=self._tool_registry
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

    def _register_mock_agent(self, mock_agent: MockAgent) -> None:
        """Register MockAgent in repository for memory access.

        Args:
            mock_agent: MockAgent instance to register
        """
        # Create unique name using agent_id prefix to avoid conflicts
        agent_id = mock_agent._identity.agent_id
        unique_name = f"MockAgent_{agent_id[:8]}"

        # Update identity with unique name
        from core.domain import AgentIdentity
        unique_identity = AgentIdentity(
            agent_id=agent_id,
            agent_name=unique_name,
            creation_timestamp=mock_agent._identity.creation_timestamp
        )

        registered_agent = RegisteredAgent(
            agent_identity=unique_identity,
            agent_capabilities=mock_agent._capabilities,
            system_prompt=mock_agent._capabilities.system_prompt or "MockAgent for testing",
            is_active=True
        )

        # Save to repository
        self._agent_repository.save(registered_agent)

    def _generate_todolist(self, user_query: str) -> Optional[str]:
        """Generate TodoList using orchestrator agent.

        Returns:
            TodoList JSON string if applicable, None for simple queries
        """
        logger.info("ORCHESTRATOR", "Generating TodoList")

        agent_query = MockAgent(
            self._llm,
            self._tool_scheduler,
            self._tool_registry,
            self._memory_coordinator
        )
        # Register MockAgent in repository for memory access
        self._register_mock_agent(agent_query)

        result = agent_query.run(
            query=f"generate_todolist: {user_query}",
            mode="iterative",
            scenario="auto",
            max_iterations=1
        )
        if not result.success:
            return None
        response = result.response.strip()
        if response.startswith("{") and "todo_list" in response:
            return response
        else:
            return None

    def process_user_input(self, user_input: str) -> AgentOutput:
        """
        Process user input through supervised multi-agent workflow.

        Workflow:
        1. Orchestrator agent generates TodoList from input
        2. AgentExecutionService supervises execution of each step
        3. Each step is validated before proceeding
        4. Final aggregated result is returned

        Args:
            user_input: User input to process

        Returns:
            AgentOutput with final result
        """
        logger.info("ORCHESTRATOR", "Processing user input")

        user_input = user_input.strip()
        mock_agent = None

        try:
            todolist_json = self._generate_todolist(user_input)
            if todolist_json: # if todolist then supervized execution
                todolist = json.loads(todolist_json)

                logger.info("ORCHESTRATOR", "TodoList generated", {
                    "total_steps": todolist.get("total_steps", 0)
                })

                supervision_result = self._execution_service.run(todolist=todolist)
                return supervision_result
            logger.info("ORCHESTRATOR", "No TodoList")
            # if no todolist then default execution
            mock_agent = MockAgent(
                self._llm,
                self._tool_scheduler,
                self._tool_registry,
                self._memory_coordinator
            )
            self._register_mock_agent(mock_agent)

            result = mock_agent.run(user_input)
            return result
        except Exception as e:
            logger.error("ORCHESTRATOR", "Execution failed", {"error": str(e)})
            return AgentOutput(
                response=f"Error executing: {e}",
                success=False,
                error=str(e)
            )
        finally:
            if mock_agent:
                print("\n--- Memory ---")
                memory = self.get_memory_content("conversation", agent_id=mock_agent._identity.agent_id)
                for item in memory:
                    print(item)
                print("--------------------\n")

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
            Dictionary with conversation stats aggregated from all agents
        """
        active_agents = self._agent_repository.find_active()

        if not active_agents:
            return {
                "conversation": {
                    "size": 0,
                    "is_empty": True
                }
            }

        # Aggregate memory from all active agents, counting only user/assistant pairs
        total_pairs = 0
        for agent in active_agents:
            agent_id = agent.get_agent_id()
            turns = self._memory_repository.get_conversation_history(
                agent_id=agent_id,
                max_turns=None
            )
            # Count only user turns (each user turn represents a conversation pair)
            user_turns = sum(1 for turn in turns if turn.get("role") == "user")
            total_pairs += user_turns

        return {
            "conversation": {
                "size": total_pairs,
                "is_empty": total_pairs == 0
            }
        }

    def reset_conversation(self) -> None:
        """Clear all conversation memory for active agents."""
        active_agents = self._agent_repository.find_active()

        for agent in active_agents:
            agent_id = agent.get_agent_id()
            self._memory_coordinator.clear_agent_memory(agent_id)
            logger.info("ORCHESTRATOR", f"Cleared memory for agent {agent.get_agent_name()}")

        # Also clear memory for the mock agent used in tests
        self._memory_coordinator.clear_agent_memory("mock_agent")
        logger.info("ORCHESTRATOR", "Cleared memory for mock_agent")

    def get_memory_content(self, mem_type: str, agent_id: Optional[str] = None) -> list:
        """
        Get memory content for a specific type.

        Args:
            mem_type: Type of memory to retrieve (e.g., 'conversation')
            agent_id: Optional. The ID of the agent whose memory to retrieve.
                      If None, aggregates memory from all active agents.

        Returns:
            List of memory entries sorted by timestamp
        """
        if mem_type != "conversation":
            return []

        formatted_entries = []

        if agent_id:
            # Get memory for specific agent
            agent_ids = [agent_id]
        else:
            # Get memory for all active agents
            active_agents = self._agent_repository.find_active()
            if not active_agents:
                return []
            agent_ids = [agent.get_agent_id() for agent in active_agents]

        # Aggregate memory from all agents
        for aid in agent_ids:
            # Get agent name from repository
            agent = self._agent_repository.find_by_id(aid)
            agent_name = agent.get_agent_name() if agent else "Unknown"

            # Get all conversation turns for this agent
            turns = self._memory_repository.get_conversation_history(
                agent_id=aid,
                max_turns=None
            )

            # Format turns for display
            for turn in turns:
                # Add agent_name and system_prompt to context
                context = turn.get("metadata", {}).copy()
                context["agent_name"] = agent_name

                # Add system prompt from agent capabilities
                if agent and hasattr(agent, 'agent_capabilities'):
                    context["system_prompt"] = agent.agent_capabilities.system_prompt

                formatted_entries.append({
                    "timestamp": turn.get("timestamp", "N/A"),
                    "data": {
                        "role": turn.get("role", "unknown"),
                        "content": turn.get("content", ""),
                        "context": context
                    },
                    "metadata": turn.get("metadata", {})
                })

        # Sort by timestamp for chronological order
        formatted_entries.sort(key=lambda x: x["timestamp"])

        return formatted_entries
