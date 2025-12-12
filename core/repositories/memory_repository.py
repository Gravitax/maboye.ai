"""
Memory Repository Interface

Abstract interface for conversation memory persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from core.domain.conversation_context import ConversationContext


class MemoryRepository(ABC):
    """
    Abstract repository interface for conversation memory persistence.

    Manages storage and retrieval of conversation history for agents.
    Each agent has isolated memory accessible by agent_id.

    Methods:
        save_turn: Store a conversation turn
        get_conversation_history: Retrieve conversation history
        get_context: Get full conversation context
        clear_agent_memory: Clear memory for specific agent
        delete_agent_memory: Permanently delete agent memory
        exists: Check if agent has memory
        get_turn_count: Get number of turns for agent
    """

    @abstractmethod
    def save_turn(
        self,
        agent_id: str,
        role: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a single conversation turn for an agent.

        Args:
            agent_id: Unique agent identifier
            role: Role of the speaker (user, assistant, system, tool)
            content: Content of the message
            metadata: Optional metadata about the turn

        Returns:
            True if save was successful

        Raises:
            ValueError: If parameters are invalid
            RepositoryError: If save operation fails

        Example:
            repository.save_turn(
                agent_id="agent-123",
                role="user",
                content="What is the weather?",
                metadata={"timestamp": "2024-01-15T10:30:00"}
            )
        """
        pass

    @abstractmethod
    def get_conversation_history(
        self,
        agent_id: str,
        max_turns: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for an agent.

        Args:
            agent_id: Unique agent identifier
            max_turns: Maximum number of recent turns to retrieve (None = all)

        Returns:
            List of conversation turns, most recent last

        Example:
            history = repository.get_conversation_history(
                agent_id="agent-123",
                max_turns=10
            )
            for turn in history:
                print(f"{turn['role']}: {turn['content']}")
        """
        pass

    @abstractmethod
    def get_context(
        self,
        agent_id: str,
        max_turns: Optional[int] = None
    ) -> Optional[ConversationContext]:
        """
        Get full conversation context for an agent.

        Args:
            agent_id: Unique agent identifier
            max_turns: Maximum number of recent turns (None = all)

        Returns:
            ConversationContext if agent has memory, None otherwise

        Example:
            context = repository.get_context("agent-123", max_turns=20)
            if context:
                print(f"Context has {context.get_turn_count()} turns")
        """
        pass

    @abstractmethod
    def append_turns(
        self,
        agent_id: str,
        turns: List[Dict[str, Any]]
    ) -> bool:
        """
        Append multiple conversation turns at once.

        Args:
            agent_id: Unique agent identifier
            turns: List of turn dictionaries with role and content

        Returns:
            True if append was successful

        Raises:
            ValueError: If turns are invalid
            RepositoryError: If append operation fails

        Example:
            repository.append_turns(
                agent_id="agent-123",
                turns=[
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"}
                ]
            )
        """
        pass

    @abstractmethod
    def clear_agent_memory(self, agent_id: str) -> bool:
        """
        Clear all conversation history for an agent.

        Memory structure is preserved but all turns are removed.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if memory was cleared, False if agent has no memory

        Example:
            if repository.clear_agent_memory("agent-123"):
                print("Memory cleared")
        """
        pass

    @abstractmethod
    def delete_agent_memory(self, agent_id: str) -> bool:
        """
        Permanently delete all memory for an agent.

        Memory structure is completely removed.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if memory was deleted, False if not found

        Example:
            repository.delete_agent_memory("agent-123")
        """
        pass

    @abstractmethod
    def exists(self, agent_id: str) -> bool:
        """
        Check if an agent has any memory.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if agent has memory, False otherwise

        Example:
            if repository.exists("agent-123"):
                print("Agent has conversation history")
        """
        pass

    @abstractmethod
    def get_turn_count(self, agent_id: str) -> int:
        """
        Get the number of conversation turns for an agent.

        Args:
            agent_id: Unique agent identifier

        Returns:
            Number of turns (0 if no memory)

        Example:
            count = repository.get_turn_count("agent-123")
            print(f"Agent has {count} conversation turns")
        """
        pass

    @abstractmethod
    def get_all_agent_ids(self) -> List[str]:
        """
        Get list of all agent IDs that have memory.

        Returns:
            List of agent IDs

        Example:
            agent_ids = repository.get_all_agent_ids()
            print(f"Memory exists for {len(agent_ids)} agents")
        """
        pass

    @abstractmethod
    def get_last_turn(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent conversation turn for an agent.

        Args:
            agent_id: Unique agent identifier

        Returns:
            Last turn dict, or None if no memory

        Example:
            last_turn = repository.get_last_turn("agent-123")
            if last_turn:
                print(f"Last message: {last_turn['content']}")
        """
        pass

    @abstractmethod
    def clear_all(self):
        """
        Clear all memory for all agents.

        WARNING: This operation cannot be undone.

        Raises:
            RepositoryError: If clear operation fails

        Example:
            repository.clear_all()  # Use with extreme caution
        """
        pass
