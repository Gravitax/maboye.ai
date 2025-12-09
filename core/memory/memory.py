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
    QUERIES = "queries"
    CONTEXTS = "contexts"
    CONVERSATION = "conversation"
    TOOL_RESULTS = "tool_results"
    PROMPTS = "prompts"
    CONTEXT_SERVICES = "context_services"


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


class ConversationMemory(Memory):
    """
    Memory for storing conversation history

    Used in iterative reasoning cycle to maintain context across
    multiple LLM calls and tool executions.
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
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add conversation turn

        Args:
            role: Role (user, assistant, tool)
            content: Turn content
            metadata: Optional turn metadata
        """
        turn_data = {
            "role": role,
            "content": content
        }

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


class ToolResultMemory(Memory):
    """
    Memory for storing tool execution results

    Stores results from tool calls during the reasoning cycle.
    """

    def __init__(self, max_size: int = 500):
        """
        Initialize tool result memory

        Args:
            max_size: Maximum number of tool results to keep
        """
        super().__init__(MemoryType.TOOL_RESULTS, max_size)

    def add_tool_result(
        self,
        tool_name: str,
        result: Any,
        success: bool,
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add tool execution result

        Args:
            tool_name: Name of executed tool
            result: Tool execution result
            success: Whether execution succeeded
            execution_time: Execution time in seconds
            metadata: Optional metadata
        """
        result_data = {
            "tool_name": tool_name,
            "result": result,
            "success": success,
            "execution_time": execution_time
        }

        meta = metadata or {}
        meta.update({
            "tool_name": tool_name,
            "success": success
        })

        self.add(result_data, meta)


class PromptMemory(Memory):
    """
    Memory for storing prompt building history

    Tracks prompts sent to LLM for debugging and optimization.
    """

    def __init__(self, max_size: int = 200):
        """
        Initialize prompt memory

        Args:
            max_size: Maximum number of prompts to keep
        """
        super().__init__(MemoryType.PROMPTS, max_size)

    def add_prompt(
        self,
        prompt: str,
        prompt_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add prompt to memory

        Args:
            prompt: Prompt text
            prompt_type: Type of prompt (system, user, tool)
            metadata: Optional metadata
        """
        prompt_data = {
            "prompt": prompt,
            "prompt_type": prompt_type
        }

        meta = metadata or {}
        meta["prompt_type"] = prompt_type

        self.add(prompt_data, meta)


class ContextServiceMemory(Memory):
    """
    Memory for storing context service data

    Stores context from services like git, file system, etc.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize context service memory

        Args:
            max_size: Maximum number of context entries to keep
        """
        super().__init__(MemoryType.CONTEXT_SERVICES, max_size)

    def add_service_context(
        self,
        service_name: str,
        context_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add context from service

        Args:
            service_name: Name of context service
            context_data: Context data from service
            metadata: Optional metadata
        """
        service_data = {
            "service_name": service_name,
            "context": context_data
        }

        meta = metadata or {}
        meta["service_name"] = service_name

        self.add(service_data, meta)

    def get_latest_context(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get latest context for specific service

        Args:
            service_name: Service name to filter by

        Returns:
            Latest context data or None
        """
        all_entries = self.get_all()

        for entry in reversed(all_entries):
            if entry["metadata"].get("service_name") == service_name:
                return entry["data"]["context"]

        return None
