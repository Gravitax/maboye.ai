"""
Memory management system for agent orchestration

Provides base memory class and specialized memory types for storing:
- User queries
- LLM contexts
"""

import sys
from pathlib import Path
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from srcs.logger import logger


class MemoryType(Enum):
    """Memory type identifiers for storage and retrieval"""
    QUERIES = "queries"
    CONTEXTS = "contexts"


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

        logger.debug("MEMORY", f"Memory initialized: {memory_type.value}", {
            "max_size": max_size
        })

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


class QueryMemory(Memory):
    """
    Memory for storing user queries

    Specialized for query-specific operations and formatting.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize query memory

        Args:
            max_size: Maximum number of queries to keep
        """
        super().__init__(MemoryType.QUERIES, max_size)


class ContextMemory(Memory):
    """
    Memory for storing LLM contexts

    Specialized for context-specific operations.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize context memory

        Args:
            max_size: Maximum number of contexts to keep
        """
        super().__init__(MemoryType.CONTEXTS, max_size)


class MemoryManager:
    """
    Central memory manager for all memory types

    Provides unified interface for accessing different memory types
    using enum-based identification.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize memory manager

        Args:
            max_size: Default maximum size for each memory type
        """
        self._memories: Dict[MemoryType, Memory] = {
            MemoryType.QUERIES: QueryMemory(max_size),
            MemoryType.CONTEXTS: ContextMemory(max_size)
        }

        logger.info("MEMORY", "Memory manager initialized", {
            "types": [t.value for t in MemoryType],
            "max_size": max_size
        })

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
