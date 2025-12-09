"""
Memory manager for centralized memory access

Provides unified interface for all memory types using enum-based identification.
"""

from typing import Any, Dict, List, Optional

from core.logger import logger
from .memory import (
    MemoryType,
    Memory,
    QueryMemory,
    ContextMemory,
    ConversationMemory,
    ToolResultMemory,
    PromptMemory,
    ContextServiceMemory
)


class MemoryManager:
    """
    Central memory manager for all memory types

    Provides unified interface for accessing different memory types
    using enum-based identification.
    """

    def __init__(
        self,
        max_size: int = 1000,
        conversation_size: int = 100,
        tool_results_size: int = 500,
        prompts_size: int = 200,
        context_services_size: int = 100
    ):
        """
        Initialize memory manager

        Args:
            max_size: Default maximum size for queries and contexts
            conversation_size: Maximum conversation turns to keep
            tool_results_size: Maximum tool results to keep
            prompts_size: Maximum prompts to keep
            context_services_size: Maximum context service entries to keep
        """
        self._memories: Dict[MemoryType, Memory] = {
            MemoryType.QUERIES: QueryMemory(max_size),
            MemoryType.CONTEXTS: ContextMemory(max_size),
            MemoryType.CONVERSATION: ConversationMemory(conversation_size),
            MemoryType.TOOL_RESULTS: ToolResultMemory(tool_results_size),
            MemoryType.PROMPTS: PromptMemory(prompts_size),
            MemoryType.CONTEXT_SERVICES: ContextServiceMemory(context_services_size)
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
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add turn to conversation memory

        Args:
            role: Role (user, assistant, tool)
            content: Turn content
            metadata: Optional metadata
        """
        conversation_memory = self.get(MemoryType.CONVERSATION)
        if isinstance(conversation_memory, ConversationMemory):
            conversation_memory.add_turn(role, content, metadata)

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
            tool_name: Tool name
            result: Execution result
            success: Success flag
            execution_time: Execution time
            metadata: Optional metadata
        """
        tool_memory = self.get(MemoryType.TOOL_RESULTS)
        if isinstance(tool_memory, ToolResultMemory):
            tool_memory.add_tool_result(
                tool_name,
                result,
                success,
                execution_time,
                metadata
            )

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
            prompt_type: Prompt type
            metadata: Optional metadata
        """
        prompt_memory = self.get(MemoryType.PROMPTS)
        if isinstance(prompt_memory, PromptMemory):
            prompt_memory.add_prompt(prompt, prompt_type, metadata)

    def add_service_context(
        self,
        service_name: str,
        context_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add context from service

        Args:
            service_name: Service name
            context_data: Context data
            metadata: Optional metadata
        """
        context_memory = self.get(MemoryType.CONTEXT_SERVICES)
        if isinstance(context_memory, ContextServiceMemory):
            context_memory.add_service_context(
                service_name,
                context_data,
                metadata
            )

    def get_service_context(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get latest context for service

        Args:
            service_name: Service name

        Returns:
            Latest context or None
        """
        context_memory = self.get(MemoryType.CONTEXT_SERVICES)
        if isinstance(context_memory, ContextServiceMemory):
            return context_memory.get_latest_context(service_name)
        return None

    def get_recent_tool_results(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent tool results

        Args:
            count: Number of results to retrieve

        Returns:
            List of recent tool results
        """
        tool_memory = self.get(MemoryType.TOOL_RESULTS)
        entries = tool_memory.get_last(count)
        return [entry["data"] for entry in entries]

    def clear_conversation(self) -> None:
        """Clear conversation memory only"""
        conversation_memory = self.get(MemoryType.CONVERSATION)
        conversation_memory.clear()
        logger.info("MEMORY", "Conversation memory cleared")