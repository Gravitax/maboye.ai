"""
Memory management system for agent orchestration

Provides base memory class and specialized memory types for storing:
- User queries
- LLM contexts
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from core.logger import logger


class MemoryType(Enum):
    """Memory type identifiers for storage and retrieval"""
    CONVERSATION = "conversation"


class Memory:
    """
    Base memory class for storing and retrieving historical data

    Provides common interface for all memory types with automatic
    timestamping and configurable size limits.
    """

    def __init__(self, memory_type: MemoryType, max_size: int = 1000):
        """
        Initialize memory

        Args:
            memory_type: Type of memory being stored
            max_size: Maximum number of entries to keep
        """
        self._type = memory_type
        self._max_size = max_size
        self._data: List[Dict[str, Any]] = []

    def add(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add entry to memory

        Args:
            data: Data to store
            metadata: Optional metadata about the entry
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "metadata": metadata or {}
        }

        self._data.append(entry)

        # Enforce size limit
        if len(self._data) > self._max_size:
            removed = self._data.pop(0)
            logger.debug("MEMORY", f"Memory limit reached, removed oldest entry", {
                "type": self._type.value,
                "removed_timestamp": removed["timestamp"]
            })

        logger.debug("MEMORY", f"Entry added to {self._type.value}", {
            "total_entries": len(self._data)
        })

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all entries

        Returns:
            List of all memory entries
        """
        return self._data.copy()

    def get_last(self, count: int = 1) -> List[Dict[str, Any]]:
        """
        Get last N entries

        Args:
            count: Number of entries to retrieve

        Returns:
            List of last N entries
        """
        if count <= 0:
            return []

        return self._data[-count:].copy() if self._data else []

    def get_range(self, start: int, end: int) -> List[Dict[str, Any]]:
        """
        Get entries in range

        Args:
            start: Start index (inclusive)
            end: End index (exclusive)

        Returns:
            List of entries in range
        """
        return self._data[start:end].copy()

    def clear(self) -> None:
        """Clear all entries"""
        count = len(self._data)
        self._data.clear()

        logger.info("MEMORY", f"Memory cleared: {self._type.value}", {
            "entries_removed": count
        })

    def size(self) -> int:
        """
        Get number of entries

        Returns:
            Number of entries in memory
        """
        return len(self._data)

    def is_empty(self) -> bool:
        """
        Check if memory is empty

        Returns:
            True if memory has no entries
        """
        return len(self._data) == 0

    def get_type(self) -> MemoryType:
        """
        Get memory type

        Returns:
            Memory type identifier
        """
        return self._type


class ConversationMemory(Memory):
    """
    Memory for storing enriched conversation turns

    Stores complete interaction history including user queries, LLM responses,
    prompts, context, tool calls, and tool results.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize conversation memory

        Args:
            max_size: Maximum number of conversation turns to keep
        """
        super().__init__(MemoryType.CONVERSATION, max_size)

    def add_turn(
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
        Add enriched conversation turn

        Args:
            role: Role (user, assistant, tool)
            content: Turn content
            query: Original user query
            prompt: Full prompt sent to LLM
            context: Context information used
            tool_calls: List of tool calls made
            tool_results: List of tool execution results
            metadata: Optional turn metadata
        """
        turn_data = {
            "role": role,
            "content": content
        }

        if query is not None:
            turn_data["query"] = query

        if prompt is not None:
            turn_data["prompt"] = prompt

        if context is not None:
            turn_data["context"] = context

        if tool_calls is not None:
            turn_data["tool_calls"] = tool_calls

        if tool_results is not None:
            turn_data["tool_results"] = tool_results

        meta = metadata or {}
        meta["role"] = role

        self.add(turn_data, meta)

    def get_conversation_history(self, max_turns: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history formatted for LLM

        Args:
            max_turns: Maximum turns to retrieve

        Returns:
            List of conversation turns
        """
        entries = self.get_last(max_turns)
        return [entry["data"] for entry in entries]
