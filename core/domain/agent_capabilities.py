"""
Agent Capabilities Value Object

Defines what an agent can do and its operational constraints.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AgentCapabilities:
    """
    Immutable capabilities and constraints of an agent.

    Defines what the agent can do, which tools it can use,
    and its operational limits.

    Attributes:
        description: Role and purpose of the agent
        authorized_tools: List of tool IDs the agent can use
        max_reasoning_turns: Maximum iterations in think-act-observe loop
        max_memory_turns: Maximum conversation history to maintain
        specialization_tags: Domain expertise tags for routing
        llm_temperature: Temperature for LLM calls
        llm_max_tokens: Max tokens for LLM responses
        llm_timeout: Timeout in seconds for LLM calls
    """

    description: str
    system_prompt: str = ""
    authorized_tools: List[str] = field(default_factory=list)
    max_reasoning_turns: int = 10
    max_memory_turns: int = 10
    specialization_tags: List[str] = field(default_factory=list)
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000
    llm_timeout: int = 30

    def __post_init__(self):
        """
        Validate capabilities after initialization.

        Raises:
            ValueError: If validation fails
        """
        self._validate_description()
        self._validate_tools()
        self._validate_turn_limits()
        self._validate_tags()

    def _validate_description(self):
        """
        Validate agent description.

        Raises:
            ValueError: If description is invalid
        """
        if not self.description:
            raise ValueError("description cannot be empty")

        if not isinstance(self.description, str):
            raise ValueError(f"description must be a string, got {type(self.description)}")

        if len(self.description) < 10:
            raise ValueError(
                f"description too short: {len(self.description)} chars (minimum 10)"
            )

        if len(self.description) > 500:
            raise ValueError(
                f"description too long: {len(self.description)} chars (maximum 500)"
            )

    def _validate_tools(self):
        """
        Validate authorized tools list.

        Raises:
            ValueError: If tools list is invalid
        """
        if not isinstance(self.authorized_tools, list):
            raise ValueError(
                f"authorized_tools must be a list, got {type(self.authorized_tools)}"
            )

        for tool_id in self.authorized_tools:
            if not isinstance(tool_id, str):
                raise ValueError(f"Tool ID must be string, got {type(tool_id)}: {tool_id}")
            if not tool_id:
                raise ValueError("Tool ID cannot be empty string")

        # Check for duplicates
        if len(self.authorized_tools) != len(set(self.authorized_tools)):
            raise ValueError("authorized_tools contains duplicates")

    def _validate_turn_limits(self):
        """
        Validate turn limit values.

        Raises:
            ValueError: If limits are invalid
        """
        if not isinstance(self.max_reasoning_turns, int):
            raise ValueError(
                f"max_reasoning_turns must be int, got {type(self.max_reasoning_turns)}"
            )

        if not isinstance(self.max_memory_turns, int):
            raise ValueError(
                f"max_memory_turns must be int, got {type(self.max_memory_turns)}"
            )

        if self.max_reasoning_turns < 1:
            raise ValueError(
                f"max_reasoning_turns must be >= 1, got {self.max_reasoning_turns}"
            )

        if self.max_reasoning_turns > 100:
            raise ValueError(
                f"max_reasoning_turns too high: {self.max_reasoning_turns} (maximum 100)"
            )

        if self.max_memory_turns < 0:
            raise ValueError(
                f"max_memory_turns must be >= 0, got {self.max_memory_turns}"
            )

        if self.max_memory_turns > 1000:
            raise ValueError(
                f"max_memory_turns too high: {self.max_memory_turns} (maximum 1000)"
            )

    def _validate_tags(self):
        """
        Validate specialization tags.

        Raises:
            ValueError: If tags are invalid
        """
        if not isinstance(self.specialization_tags, list):
            raise ValueError(
                f"specialization_tags must be a list, got {type(self.specialization_tags)}"
            )

        for tag in self.specialization_tags:
            if not isinstance(tag, str):
                raise ValueError(f"Tag must be string, got {type(tag)}: {tag}")
            if not tag:
                raise ValueError("Tag cannot be empty string")
            if len(tag) > 50:
                raise ValueError(f"Tag too long: {len(tag)} chars (maximum 50)")

        # Check for duplicates
        if len(self.specialization_tags) != len(set(self.specialization_tags)):
            raise ValueError("specialization_tags contains duplicates")

    def can_use_tool(self, tool_id: str) -> bool:
        """
        Check if the agent is authorized to use a specific tool.

        Args:
            tool_id: Tool identifier to check

        Returns:
            True if tool is authorized, False otherwise

        Example:
            if capabilities.can_use_tool("read_file"):
                # Agent can read files
        """
        if not tool_id:
            return False

        # Empty authorized_tools means agent can use all tools
        if not self.authorized_tools:
            return True

        return tool_id in self.authorized_tools

    def has_specialization(self, tag: str) -> bool:
        """
        Check if the agent has a specific specialization.

        Args:
            tag: Specialization tag to check

        Returns:
            True if agent has the specialization, False otherwise

        Example:
            if capabilities.has_specialization("code"):
                # Agent is specialized in code
        """
        if not tag:
            return False

        return tag.lower() in [t.lower() for t in self.specialization_tags]

    def get_tool_count(self) -> int:
        """
        Get the number of authorized tools.

        Returns:
            Number of tools the agent can use
        """
        return len(self.authorized_tools)

    def is_unrestricted(self) -> bool:
        """
        Check if agent has unrestricted tool access.

        Returns:
            True if agent can use all tools, False if restricted
        """
        return len(self.authorized_tools) == 0

    def __str__(self) -> str:
        """String representation for logging."""
        tool_summary = (
            "all tools" if self.is_unrestricted()
            else f"{self.get_tool_count()} tools"
        )
        tags_summary = (
            ", ".join(self.specialization_tags[:3])
            if self.specialization_tags else "none"
        )

        return (
            f"AgentCapabilities(tools={tool_summary}, "
            f"specializations=[{tags_summary}])"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"AgentCapabilities("
            f"description='{self.description[:50]}...', "
            f"tools={self.get_tool_count()}, "
            f"max_reasoning={self.max_reasoning_turns}, "
            f"max_memory={self.max_memory_turns}, "
            f"tags={self.specialization_tags})"
        )
