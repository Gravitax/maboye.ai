"""
Agent Factory

Creates Agent instances from RegisteredAgent domain objects.
Bridges domain objects with executable agent instances.
"""

from typing import Optional

from core.logger import logger
from llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from tools.tool_base import ToolRegistry
from core.domain import RegisteredAgent
from core.services.memory_manager import MemoryManager


class AgentFactory:
    """
    Factory for creating agent instances from domain objects.

    Bridges RegisteredAgent domain objects with executable Agent instances.

    Responsibilities:
    - Create Agent instances from RegisteredAgent
    - Inject all required dependencies
    - Cache agent instances for reuse
    """

    def __init__(
        self,
        llm: LLMWrapper,
        tool_scheduler: ToolScheduler,
        tool_registry: ToolRegistry,
        memory: MemoryManager
    ):
        """
        Initialize agent factory.

        Args:
            llm: LLM wrapper instance
            tool_scheduler: Tool scheduler instance
            tool_registry: Tool registry instance
            memory: Memory coordinator for agent-specific memory
        """
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._tool_registry = tool_registry
        self._memory = memory

        # Cache of created agent instances (agent_id -> Agent)
        self._agent_instances: dict[str, 'Agent'] = {}

    def create_agent(
        self,
        registered_agent: RegisteredAgent,
        force_recreate: bool = False
    ) -> 'Agent':
        """
        Create an Agent instance from a RegisteredAgent domain object.

        Args:
            registered_agent: Domain object containing agent definition
            force_recreate: If True, recreate even if cached

        Returns:
            Agent instance ready for execution

        Raises:
            ValueError: If registered_agent is invalid
        """
        from agents.agent import Agent
        if not registered_agent:
            raise ValueError("registered_agent cannot be None")

        if not registered_agent.is_active:
            raise ValueError(f"Agent '{registered_agent.get_agent_name()}' is inactive")

        agent_id = registered_agent.get_agent_id()

        # Return cached instance if available
        if not force_recreate and agent_id in self._agent_instances:
            return self._agent_instances[agent_id]

        # Create Agent with domain objects directly
        agent_instance = Agent(
            agent_identity=registered_agent.agent_identity,
            agent_capabilities=registered_agent.agent_capabilities,
            llm=self._llm,
            tool_scheduler=self._tool_scheduler,
            tool_registry=self._tool_registry,
            memory_manager=self._memory
        )

        # Cache the instance
        self._agent_instances[agent_id] = agent_instance
        return agent_instance

    def get_cached_agent(self, agent_id: str) -> Optional['Agent']:
        """
        Get a cached agent instance by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Cached Agent instance or None if not cached
        """
        return self._agent_instances.get(agent_id)

    def clear_cache(self, agent_id: Optional[str] = None):
        """
        Clear cached agent instances.

        Args:
            agent_id: If provided, clear only this agent. Otherwise clear all.
        """
        if agent_id:
            if agent_id in self._agent_instances:
                del self._agent_instances[agent_id]
        else:
            count = len(self._agent_instances)
            self._agent_instances.clear()

    def get_cache_stats(self) -> dict:
        """
        Get statistics about cached agents.

        Returns:
            Dictionary with cache statistics
        """
        return {
            'cached_agents_count': len(self._agent_instances),
            'cached_agent_ids': list(self._agent_instances.keys())
        }

    def __str__(self) -> str:
        """String representation for logging."""
        return f"AgentFactory(cached_agents={len(self._agent_instances)})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"AgentFactory("
            f"llm={self._llm}, "
            f"cached_agents={len(self._agent_instances)})"
        )
