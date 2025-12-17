"""
Agent Memory Coordinator

Coordinates memory access for multiple agents with caching and isolation.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from core.repositories.memory_repository import MemoryRepository
from core.domain.agent_identity import AgentIdentity
from core.domain.conversation_context import ConversationContext
from core.services.cache_strategy import CacheStrategy, LRUCache


class MemoryManager:
    """
    Coordinates memory access for multiple agents.

    Centralizes memory management logic with:
    - Per-agent memory isolation
    - Secure cross-agent context access
    - LRU caching for frequently accessed contexts
    - Automatic cleanup of inactive memories

    Attributes:
        _memory_repository: Repository for persistent memory storage
        _cache: Cache strategy for contexts
    """

    def __init__(
        self,
        memory_repository: MemoryRepository,
        cache_strategy: Optional[CacheStrategy] = None
    ):
        """
        Initialize memory.

        Args:
            memory_repository: Repository for memory persistence
            cache_strategy: Caching strategy (default: LRU with size 100)
        """
        self._memory_repository = memory_repository
        self._cache = cache_strategy or LRUCache(max_size=100)

    def get_conversation_context(
        self,
        agent_identity: AgentIdentity,
        max_turns: Optional[int] = None
    ) -> ConversationContext:
        """
        Get conversation context for an agent.

        Uses cache when possible for performance.

        Args:
            agent_identity: Identity of the agent
            max_turns: Maximum number of turns to retrieve

        Returns:
            ConversationContext with conversation history
        """
        agent_id = agent_identity.agent_id
        cache_key = f"context:{agent_id}:{max_turns}"

        # Check cache first
        cached_context = self._cache.get(cache_key)
        if cached_context is not None:
            return cached_context

        # Build context from repository
        context = ConversationContext.create_from_memory(
            agent_identity=agent_identity,
            memory_manager=self._memory_repository,
            max_turns=max_turns
        )

        # Cache the context
        self._cache.put(cache_key, context)

        return context

    def save_conversation_turn(
        self,
        agent_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save a conversation turn for an agent.

        Invalidates cache for this agent.

        Args:
            agent_id: Agent identifier
            role: Role of the speaker (user, assistant, system, tool)
            content: Content of the message
            metadata: Optional metadata

        Returns:
            True if save was successful
        """
        # Save to repository
        success = self._memory_repository.save_turn(
            agent_id=agent_id,
            role=role,
            content=content,
            metadata=metadata
        )

        if success:
            # Invalidate cache for this agent
            self._invalidate_agent_cache(agent_id)

        return success

    def clear_agent_memory(self, agent_id: str) -> bool:
        """
        Clear all memory for a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if memory was cleared
        """
        # Clear from repository
        success = self._memory_repository.clear_agent_memory(agent_id)

        if success:
            # Invalidate cache
            self._invalidate_agent_cache(agent_id)

        return success

    def cleanup_inactive_memories(
        self,
        inactive_threshold_hours: int = 24
    ) -> int:
        """
        Clean up memories of inactive agents.

        Memory management strategy for scalability.

        Args:
            inactive_threshold_hours: Hours of inactivity before cleanup

        Returns:
            Number of memories cleaned up
        """
        cleaned_count = 0
        threshold = datetime.now() - timedelta(hours=inactive_threshold_hours)

        # Get all agent IDs with memory
        all_agent_ids = self._memory_repository.get_all_agent_ids()

        for agent_id in all_agent_ids:
            # Get last turn to check activity
            last_turn = self._memory_repository.get_last_turn(agent_id)

            if last_turn is None:
                continue

            # Check if inactive
            last_timestamp_str = last_turn.get('timestamp')
            if last_timestamp_str:
                try:
                    last_timestamp = datetime.fromisoformat(last_timestamp_str)
                    if last_timestamp < threshold:
                        # Clear inactive memory
                        self.clear_agent_memory(agent_id)
                        cleaned_count += 1
                except (ValueError, TypeError):
                    pass  # Skip invalid timestamps

        return cleaned_count

    def get_memory_stats(self) -> Dict:
        """
        Get memory statistics.

        Returns:
            Dictionary with memory stats
        """
        return {
            'cache_stats': self._cache.get_stats(),
            'total_agents_with_memory': len(self._memory_repository.get_all_agent_ids())
        }

    def _invalidate_agent_cache(self, agent_id: str) -> None:
        """
        Invalidate all cache entries for an agent.

        Args:
            agent_id: Agent identifier
        """
        # We need to remove all cache keys that start with "context:{agent_id}:"
        # Since our cache doesn't support pattern matching, we'll clear the entire cache
        # In production, you might want a more sophisticated cache invalidation strategy
        self._cache.clear()

    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"Memory("
            f"cache={self._cache})"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"Memory("
            f"cache={repr(self._cache)})"
        )
