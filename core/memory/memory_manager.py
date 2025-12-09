"""
Memory manager for centralized memory access

Provides unified interface for all memory types using enum-based identification.
"""

from typing import Any, Dict, List, Optional

from core.logger import logger
from .memory import (
    MemoryType,
    Memory,
    ConversationMemory
)


class MemoryManager:
    """
    Central memory manager for all memory types

    Provides unified interface for accessing different memory types
    using enum-based identification.
    """

    def __init__(self, conversation_size: int = 100):
        """
        Initialize memory manager

        Args:
            conversation_size: Maximum conversation turns to keep
        """
        self._memories: Dict[MemoryType, Memory] = {
            MemoryType.CONVERSATION: ConversationMemory(conversation_size)
        }

    def get(self, memory_type: MemoryType) -> Memory:
        """
        Get memory by type

        Args:
            memory_type: Type of memory to retrieve

        Returns:
            Memory instance

        Raises:
            ValueError: Invalid memory type
        """
        if memory_type not in self._memories:
            raise ValueError(f"Invalid memory type: {memory_type}")

        return self._memories[memory_type]

    def set(self, memory_type: MemoryType, data: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add data to memory by type

        Args:
            memory_type: Type of memory to add to
            data: Data to store
            metadata: Optional metadata

        Raises:
            ValueError: Invalid memory type
        """
        if memory_type not in self._memories:
            raise ValueError(f"Invalid memory type: {memory_type}")

        self._memories[memory_type].add(data, metadata)

    def clear_all(self) -> None:
        """Clear all memory types"""
        for memory in self._memories.values():
            memory.clear()

        logger.info("MEMORY", "All memory cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all memory types

        Returns:
            Statistics dictionary
        """
        stats = {}
        for mem_type, memory in self._memories.items():
            stats[mem_type.value] = {
                "size": memory.size(),
                "is_empty": memory.is_empty()
            }

        return stats

    def add_conversation_turn(
        self,
        role: str,
        content: str,
        query: Optional[str] = None,
        prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add enriched turn to conversation memory

        Args:
            role: Role (user, assistant, tool)
            content: Turn content
            query: Original user query
            prompt: Full prompt sent to LLM
            context: Context information used
            tool_calls: List of tool calls made
            tool_results: List of tool execution results
            metadata: Optional metadata
        """
        conversation_memory = self.get(MemoryType.CONVERSATION)
        if isinstance(conversation_memory, ConversationMemory):
            conversation_memory.add_turn(
                role, content, query, prompt, context, tool_calls, tool_results, metadata
            )

    def get_conversation_history(self, max_turns: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history

        Args:
            max_turns: Maximum turns to retrieve

        Returns:
            List of conversation turns
        """
        conversation_memory = self.get(MemoryType.CONVERSATION)
        if isinstance(conversation_memory, ConversationMemory):
            return conversation_memory.get_conversation_history(max_turns)
        return []

    def clear_conversation(self) -> None:
        """Clear conversation memory only"""
        conversation_memory = self.get(MemoryType.CONVERSATION)
        conversation_memory.clear()
        logger.info("MEMORY", "Conversation memory cleared")