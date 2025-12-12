"""
Agent Repository Interface

Abstract interface for agent persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from core.domain.registered_agent import RegisteredAgent


class AgentRepository(ABC):
    """
    Abstract repository interface for agent persistence.

    Defines the contract for storing and retrieving RegisteredAgent entities.
    Implementations can use in-memory storage, databases, or other persistence layers.

    Methods:
        save: Store or update an agent
        find_by_id: Retrieve agent by unique ID
        find_by_name: Retrieve agent by name
        find_all: Retrieve all registered agents
        find_active: Retrieve all active agents
        exists: Check if agent exists
        delete: Remove an agent from storage
        count: Get total number of agents
    """

    @abstractmethod
    def save(self, agent: RegisteredAgent) -> RegisteredAgent:
        """
        Save or update a registered agent.

        If an agent with the same ID exists, it will be updated.
        Otherwise, a new agent will be created.

        Args:
            agent: RegisteredAgent entity to save

        Returns:
            The saved RegisteredAgent instance

        Raises:
            ValueError: If agent is invalid
            RepositoryError: If save operation fails

        Example:
            saved_agent = repository.save(agent)
        """
        pass

    @abstractmethod
    def find_by_id(self, agent_id: str) -> Optional[RegisteredAgent]:
        """
        Find an agent by its unique ID.

        Args:
            agent_id: Unique agent identifier

        Returns:
            RegisteredAgent if found, None otherwise

        Example:
            agent = repository.find_by_id("550e8400-e29b-41d4-a716-446655440000")
            if agent:
                print(f"Found agent: {agent.get_agent_name()}")
        """
        pass

    @abstractmethod
    def find_by_name(self, agent_name: str) -> Optional[RegisteredAgent]:
        """
        Find an agent by its unique name.

        Args:
            agent_name: Unique agent name

        Returns:
            RegisteredAgent if found, None otherwise

        Example:
            agent = repository.find_by_name("CodeAgent")
        """
        pass

    @abstractmethod
    def find_all(self) -> List[RegisteredAgent]:
        """
        Retrieve all registered agents.

        Returns:
            List of all RegisteredAgent entities

        Example:
            all_agents = repository.find_all()
            print(f"Total agents: {len(all_agents)}")
        """
        pass

    @abstractmethod
    def find_active(self) -> List[RegisteredAgent]:
        """
        Retrieve all active agents.

        Returns:
            List of active RegisteredAgent entities

        Example:
            active_agents = repository.find_active()
        """
        pass

    @abstractmethod
    def exists(self, agent_id: str) -> bool:
        """
        Check if an agent exists by ID.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if agent exists, False otherwise

        Example:
            if repository.exists(agent_id):
                print("Agent already registered")
        """
        pass

    @abstractmethod
    def exists_by_name(self, agent_name: str) -> bool:
        """
        Check if an agent exists by name.

        Args:
            agent_name: Agent name to check

        Returns:
            True if agent exists, False otherwise

        Example:
            if repository.exists_by_name("CodeAgent"):
                raise ValueError("Agent name already taken")
        """
        pass

    @abstractmethod
    def delete(self, agent_id: str) -> bool:
        """
        Delete an agent by ID.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if agent was deleted, False if not found

        Raises:
            RepositoryError: If delete operation fails

        Example:
            if repository.delete(agent_id):
                print("Agent deleted successfully")
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get the total number of registered agents.

        Returns:
            Count of all agents

        Example:
            total = repository.count()
        """
        pass

    @abstractmethod
    def clear(self):
        """
        Remove all agents from storage.

        WARNING: This operation cannot be undone.

        Raises:
            RepositoryError: If clear operation fails

        Example:
            repository.clear()  # Use with caution
        """
        pass
