"""
In-Memory Agent Repository Implementation

Thread-safe in-memory implementation of AgentRepository.
"""

from threading import RLock
from typing import Optional, List
import copy

from core.repositories.agent_repository import AgentRepository
from core.domain.registered_agent import RegisteredAgent


class RepositoryError(Exception):
    """Exception raised for repository operation errors."""
    pass


class InMemoryAgentRepository(AgentRepository):
    """
    Thread-safe in-memory implementation of AgentRepository.

    Uses Python dictionaries for storage with RLock for thread safety.
    Suitable for development, testing, and single-instance deployments.

    Attributes:
        _agents_by_id: Dictionary mapping agent_id to RegisteredAgent
        _agents_by_name: Dictionary mapping agent_name to RegisteredAgent
        _lock: Reentrant lock for thread-safe operations
    """

    def __init__(self):
        """Initialize empty in-memory storage."""
        self._agents_by_id: dict[str, RegisteredAgent] = {}
        self._agents_by_name: dict[str, RegisteredAgent] = {}
        self._lock = RLock()

    def save(self, agent: RegisteredAgent) -> RegisteredAgent:
        """
        Save or update a registered agent.

        Thread-safe operation that stores agent by both ID and name.

        Args:
            agent: RegisteredAgent entity to save

        Returns:
            The saved RegisteredAgent instance

        Raises:
            ValueError: If agent is invalid or name conflict exists
            RepositoryError: If save operation fails
        """
        if not isinstance(agent, RegisteredAgent):
            raise ValueError(
                f"agent must be RegisteredAgent, got {type(agent)}"
            )

        agent_id = agent.get_agent_id()
        agent_name = agent.get_agent_name()

        with self._lock:
            # Check for name conflicts (different agent with same name)
            existing_by_name = self._agents_by_name.get(agent_name)
            if existing_by_name and existing_by_name.get_agent_id() != agent_id:
                raise ValueError(
                    f"Agent name '{agent_name}' already exists with different ID"
                )

            # Store by both ID and name
            self._agents_by_id[agent_id] = agent
            self._agents_by_name[agent_name] = agent

            return agent

    def find_by_id(self, agent_id: str) -> Optional[RegisteredAgent]:
        """
        Find an agent by its unique ID.

        Args:
            agent_id: Unique agent identifier

        Returns:
            RegisteredAgent if found, None otherwise
        """
        if not agent_id:
            return None

        with self._lock:
            agent = self._agents_by_id.get(agent_id)
            return copy.deepcopy(agent) if agent else None

    def find_by_name(self, agent_name: str) -> Optional[RegisteredAgent]:
        """
        Find an agent by its unique name.

        Args:
            agent_name: Unique agent name

        Returns:
            RegisteredAgent if found, None otherwise
        """
        if not agent_name:
            return None

        with self._lock:
            agent = self._agents_by_name.get(agent_name)
            return copy.deepcopy(agent) if agent else None

    def find_all(self) -> List[RegisteredAgent]:
        """
        Retrieve all registered agents.

        Returns:
            List of all RegisteredAgent entities
        """
        with self._lock:
            return [copy.deepcopy(agent) for agent in self._agents_by_id.values()]

    def find_active(self) -> List[RegisteredAgent]:
        """
        Retrieve all active agents.

        Returns:
            List of active RegisteredAgent entities
        """
        with self._lock:
            return [
                copy.deepcopy(agent)
                for agent in self._agents_by_id.values()
                if agent.is_active
            ]

    def exists(self, agent_id: str) -> bool:
        """
        Check if an agent exists by ID.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if agent exists, False otherwise
        """
        if not agent_id:
            return False

        with self._lock:
            return agent_id in self._agents_by_id

    def exists_by_name(self, agent_name: str) -> bool:
        """
        Check if an agent exists by name.

        Args:
            agent_name: Agent name to check

        Returns:
            True if agent exists, False otherwise
        """
        if not agent_name:
            return False

        with self._lock:
            return agent_name in self._agents_by_name

    def delete(self, agent_id: str) -> bool:
        """
        Delete an agent by ID.

        Removes agent from both ID and name indexes.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if agent was deleted, False if not found

        Raises:
            RepositoryError: If delete operation fails
        """
        if not agent_id:
            return False

        with self._lock:
            agent = self._agents_by_id.get(agent_id)
            if not agent:
                return False

            agent_name = agent.get_agent_name()

            try:
                del self._agents_by_id[agent_id]
                del self._agents_by_name[agent_name]
                return True
            except KeyError as e:
                raise RepositoryError(
                    f"Failed to delete agent {agent_id}: {str(e)}"
                ) from e

    def count(self) -> int:
        """
        Get the total number of registered agents.

        Returns:
            Count of all agents
        """
        with self._lock:
            return len(self._agents_by_id)

    def clear(self):
        """
        Remove all agents from storage.

        WARNING: This operation cannot be undone.

        Raises:
            RepositoryError: If clear operation fails
        """
        with self._lock:
            try:
                self._agents_by_id.clear()
                self._agents_by_name.clear()
            except Exception as e:
                raise RepositoryError(
                    f"Failed to clear repository: {str(e)}"
                ) from e

    def __len__(self) -> int:
        """Get the number of agents (for convenience)."""
        return self.count()

    def __contains__(self, agent_id: str) -> bool:
        """Check if agent exists (for convenience)."""
        return self.exists(agent_id)

    def __str__(self) -> str:
        """String representation for logging."""
        with self._lock:
            total = len(self._agents_by_id)
            active = sum(1 for agent in self._agents_by_id.values() if agent.is_active)
            return f"InMemoryAgentRepository(total={total}, active={active})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        with self._lock:
            agent_names = [agent.get_agent_name() for agent in self._agents_by_id.values()]
            return f"InMemoryAgentRepository(agents={agent_names})"
