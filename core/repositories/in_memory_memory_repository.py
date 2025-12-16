"""
In-Memory Memory Repository Implementation

Thread-safe in-memory implementation of MemoryRepository.
"""

from threading import RLock
from typing import Optional, List, Dict, Any
from datetime import datetime
import copy
from core.logger import logger
from core.repositories.memory_repository import MemoryRepository
from core.domain.conversation_context import ConversationContext
from core.domain.agent_identity import AgentIdentity


class RepositoryError(Exception):
    """Exception raised for repository operation errors."""
    pass


class InMemoryMemoryRepository(MemoryRepository):
    """
    Thread-safe in-memory implementation of MemoryRepository.

    Stores conversation history for each agent in isolated memory spaces.
    Uses RLock for thread-safe operations.

    Attributes:
        _memories: Dictionary mapping agent_id to list of conversation turns
        _lock: Reentrant lock for thread-safe operations
    """

    def __init__(self):
        """Initialize empty in-memory storage."""
        self._memories: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = RLock()

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
        """
        if not agent_id:
            raise ValueError("agent_id cannot be empty")

        if not role:
            raise ValueError("role cannot be empty")

        if role not in ['user', 'assistant', 'system', 'tool']:
            raise ValueError(
                f"role must be one of: user, assistant, system, tool; got '{role}'"
            )

        turn = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }

        if metadata:
            turn['metadata'] = metadata

        with self._lock:
            if agent_id not in self._memories:
                self._memories[agent_id] = []

            self._memories[agent_id].append(turn)
            return True

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
        """
        if not agent_id:
            return []

        with self._lock:
            history = self._memories.get(agent_id, [])

            if max_turns is not None and max_turns > 0:
                history = history[-max_turns:]

            return copy.deepcopy(history)

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
        """
        if not agent_id:
            return None

        with self._lock:
            if agent_id not in self._memories:
                return None

            history = self.get_conversation_history(agent_id, max_turns)

            # Create minimal agent identity for context
            # Note: In production, this should be fetched from AgentRepository
            identity = AgentIdentity(
                agent_id=agent_id,
                agent_name=f"Agent_{agent_id[:8]}",
                creation_timestamp=datetime.now()
            )

            metadata = {
                'agent_id': agent_id,
                'total_turns': len(history),
                'max_turns_requested': max_turns
            }

            return ConversationContext(
                agent_identity=identity,
                conversation_history=history,
                context_metadata=metadata,
                created_at=datetime.now()
            )

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
        """
        if not agent_id:
            raise ValueError("agent_id cannot be empty")

        if not isinstance(turns, list):
            raise ValueError(f"turns must be a list, got {type(turns)}")

        # Validate all turns before appending
        for idx, turn in enumerate(turns):
            if not isinstance(turn, dict):
                raise ValueError(f"Turn {idx} must be dict, got {type(turn)}")

            if 'role' not in turn:
                raise ValueError(f"Turn {idx} missing 'role' field")

            if 'content' not in turn:
                raise ValueError(f"Turn {idx} missing 'content' field")

        with self._lock:
            if agent_id not in self._memories:
                self._memories[agent_id] = []

            # Add timestamp to each turn if not present
            for turn in turns:
                if 'timestamp' not in turn:
                    turn['timestamp'] = datetime.now().isoformat()

            self._memories[agent_id].extend(copy.deepcopy(turns))
            return True

    def clear_agent_memory(self, agent_id: str) -> bool:
        """
        Clear all conversation history for an agent.

        Memory structure is preserved but all turns are removed.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if memory was cleared, False if agent has no memory
        """
        if not agent_id:
            return False

        with self._lock:
            if agent_id not in self._memories:
                return False

            self._memories[agent_id] = []
            return True

    def delete_agent_memory(self, agent_id: str) -> bool:
        """
        Permanently delete all memory for an agent.

        Memory structure is completely removed.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if memory was deleted, False if not found
        """
        if not agent_id:
            return False

        with self._lock:
            if agent_id not in self._memories:
                return False

            del self._memories[agent_id]
            return True

    def exists(self, agent_id: str) -> bool:
        """
        Check if an agent has any memory.

        Args:
            agent_id: Unique agent identifier

        Returns:
            True if agent has memory, False otherwise
        """
        if not agent_id:
            return False

        with self._lock:
            return agent_id in self._memories

    def get_turn_count(self, agent_id: str) -> int:
        """
        Get the number of conversation turns for an agent.

        Args:
            agent_id: Unique agent identifier

        Returns:
            Number of turns (0 if no memory)
        """
        if not agent_id:
            return 0

        with self._lock:
            return len(self._memories.get(agent_id, []))

    def get_all_agent_ids(self) -> List[str]:
        """
        Get list of all agent IDs that have memory.

        Returns:
            List of agent IDs
        """
        with self._lock:
            return list(self._memories.keys())

    def get_last_turn(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent conversation turn for an agent.

        Args:
            agent_id: Unique agent identifier

        Returns:
            Last turn dict, or None if no memory
        """
        if not agent_id:
            return None

        with self._lock:
            history = self._memories.get(agent_id, [])
            if not history:
                return None

            return copy.deepcopy(history[-1])

    def clear_all(self):
        """
        Clear all memory for all agents.

        WARNING: This operation cannot be undone.

        Raises:
            RepositoryError: If clear operation fails
        """
        with self._lock:
            try:
                self._memories.clear()
            except Exception as e:
                raise RepositoryError(
                    f"Failed to clear all memories: {str(e)}"
                ) from e

    def __len__(self) -> int:
        """Get the number of agents with memory (for convenience)."""
        with self._lock:
            return len(self._memories)

    def __contains__(self, agent_id: str) -> bool:
        """Check if agent has memory (for convenience)."""
        return self.exists(agent_id)

    def __str__(self) -> str:
        """String representation for logging."""
        with self._lock:
            total_agents = len(self._memories)
            total_turns = sum(len(turns) for turns in self._memories.values())
            return (
                f"InMemoryMemoryRepository("
                f"agents={total_agents}, total_turns={total_turns})"
            )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        with self._lock:
            agent_stats = {
                agent_id: len(turns)
                for agent_id, turns in self._memories.items()
            }
            return f"InMemoryMemoryRepository(agent_turns={agent_stats})"
