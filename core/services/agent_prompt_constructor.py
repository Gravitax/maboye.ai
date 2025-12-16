"""
Agent Prompt Constructor

Builds agent-specific prompts with caching.
"""

from typing import List, Optional

from core.domain.agent_capabilities import AgentCapabilities
from core.domain.conversation_context import ConversationContext
from core.services.agent_memory_coordinator import AgentMemoryCoordinator
from tools.tool_base import ToolRegistry
from agents.types import Message


class AgentPromptConstructor:
    """
    Constructs agent-specific prompts using Builder pattern.

    Responsibilities:
    - Build system prompt with agent capabilities
    - Integrate conversation history
    - Cache compiled prompts for performance

    Attributes:
        _capabilities: Agent capabilities defining role and tools
        _memory_coordinator: Coordinator for accessing agent memories
        _tool_registry: Registry of available tools
        _system_prompt_cache: Cached system prompt
    """

    def __init__(
        self,
        agent_capabilities: AgentCapabilities,
        memory_coordinator: AgentMemoryCoordinator,
        tool_registry: ToolRegistry
    ):
        """
        Initialize prompt constructor.

        Args:
            agent_capabilities: Capabilities of the agent
            memory_coordinator: Memory coordinator for context access
            tool_registry: Registry of available tools
        """
        self._capabilities = agent_capabilities
        self._memory_coordinator = memory_coordinator
        self._tool_registry = tool_registry
        self._system_prompt_cache: Optional[str] = None

    def build_system_prompt(self) -> str:
        """
        Build system prompt with caching.

        Format:
            {description}

            Capabilities:
            - Max reasoning turns: {max_reasoning_turns}
            - Max memory turns: {max_memory_turns}
            - Specializations: {tags}

            Available tools:
            - {tool_1}: {description}
            - {tool_2}: {description}

        Returns:
            Formatted system prompt
        """
        if self._system_prompt_cache is not None:
            return self._system_prompt_cache

        prompt = self._construct_system_prompt()
        self._system_prompt_cache = prompt
        return prompt

    def build_conversation_messages(
        self,
        conversation_context: ConversationContext
    ) -> List[Message]:
        """
        Build conversation messages from context.

        Args:
            conversation_context: Context with conversation history

        Returns:
            List of messages ready for LLM
        """
        messages: List[Message] = []

        # Add system prompt
        messages.append({
            "role": "system",
            "content": self.build_system_prompt()
        })

        # Add conversation history
        for turn in conversation_context.conversation_history:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", "")
            })

        return messages

    def invalidate_cache(self) -> None:
        """Invalidate cached system prompt."""
        self._system_prompt_cache = None

    def _construct_system_prompt(self) -> str:
        """
        Construct the complete system prompt.

        Returns:
            Formatted system prompt string
        """
        lines = []

        # Description
        lines.append(self._capabilities.description)
        lines.append("")

        # Capabilities section
        lines.append("Capabilities:")
        lines.append(f"- Max reasoning turns: {self._capabilities.max_reasoning_turns}")
        lines.append(f"- Max memory turns: {self._capabilities.max_memory_turns}")

        if self._capabilities.specialization_tags:
            tags = ", ".join(self._capabilities.specialization_tags)
            lines.append(f"- Specializations: {tags}")

        lines.append("")

        # Tools section
        lines.append("Available tools:")
        tools_section = self.format_tools_section()
        if tools_section:
            lines.append(tools_section)
        else:
            lines.append("- No tools available")

        return "\n".join(lines)

    def format_tools_section(self) -> str:
        """
        Format the tools section of the prompt.

        Returns:
            Formatted tools description
        """
        all_tools = self._tool_registry.get_all_tools_info()
        authorized_tools = self._capabilities.authorized_tools

        # Filter to authorized tools only
        if authorized_tools:
            filtered_tools = [
                tool for tool in all_tools
                if tool['name'] in authorized_tools
            ]
        else:
            # Empty list means all tools available
            filtered_tools = all_tools

        if not filtered_tools:
            return ""

        lines = []
        for tool in filtered_tools:
            tool_line = f"- {tool['name']}: {tool['description']}"
            lines.append(tool_line)

        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation for logging."""
        tool_count = len(self._capabilities.authorized_tools)
        return (
            f"AgentPromptConstructor("
            f"tools={tool_count}, "
            f"cached={self._system_prompt_cache is not None})"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"AgentPromptConstructor("
            f"capabilities={self._capabilities}, "
            f"has_cache={self._system_prompt_cache is not None})"
        )
