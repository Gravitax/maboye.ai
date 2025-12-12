"""
Configuration for agent system

Provides configuration management for Agent instances.
"""

from typing import Optional, List, Union
from dataclasses import dataclass, field

from tools.tool_ids import ToolId


@dataclass
class AgentConfig:
    """
    Configuration for Agent

    Attributes:
        name: Unique identifier for the agent
        description: Role and purpose of the agent
        tools: List of tool IDs that the agent can use (ToolId enum values or strings)
            - None: No tools available
            - []: All tools available (default)
            - ["tool1", "tool2"]: Only specified tools available
        enable_logging: Enable/disable logging
        max_input_length: Maximum input length in characters
        max_output_length: Maximum output length in characters
        max_agent_turns: Maximum reasoning loop turns
        max_history_turns: Maximum conversation history turns to keep
        system_prompt: Custom system prompt for the agent
        metadata: Additional metadata for the agent
    """

    name: str = "BaseAgent"
    description: str = "A general-purpose AI agent"
    tools: Optional[List[Union[str, ToolId]]] = field(default_factory=list)
    enable_logging: bool = True
    max_input_length: int = 10000
    max_output_length: int = 10000
    max_agent_turns: int = 10
    max_history_turns: int = 10
    system_prompt: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.max_input_length <= 0:
            raise ValueError("Max input length must be positive")
        if self.max_output_length <= 0:
            raise ValueError("Max output length must be positive")
        if self.max_history_turns <= 0:
            raise ValueError("Max history turns must be positive")

        # Validate tools: must be None or a list
        if self.tools is not None and not isinstance(self.tools, list):
            raise ValueError("Tools must be None or a list")

        # Normalize tools to strings if not None
        if self.tools is not None:
            self.tools = [self._normalize_tool_id(tool) for tool in self.tools]

    def _normalize_tool_id(self, tool: Union[str, ToolId]) -> str:
        """
        Normalize a tool ID to string format.

        Args:
            tool: Tool ID as ToolId enum or string

        Returns:
            Tool ID as string
        """
        if isinstance(tool, ToolId):
            return tool.value
        return str(tool)

    def update(self, description: Optional[str] = None, tools: Optional[List[Union[str, ToolId]]] = None):
        """
        Update agent configuration with new description and/or tools.

        Args:
            description: New agent description
            tools: New list of tool IDs (ToolId enum or strings)
        """
        if description is not None:
            self.description = description

        if tools is not None:
            if not isinstance(tools, list):
                raise ValueError("Tools must be a list")
            self.tools = [self._normalize_tool_id(tool) for tool in tools]

    def has_tool(self, tool_id: Union[str, ToolId]) -> bool:
        """
        Check if a tool is available in the agent's configuration.

        Args:
            tool_id: The tool ID to check (ToolId enum or string)

        Returns:
            True if the tool is available, False otherwise
        """
        if self.tools is None:
            return False
        normalized_id = self._normalize_tool_id(tool_id)
        return normalized_id in self.tools

    def add_tool(self, tool_id: Union[str, ToolId]):
        """
        Add a tool to the agent's configuration.

        Args:
            tool_id: The tool ID to add (ToolId enum or string)

        Raises:
            ValueError: If tools is None (no tools allowed)
        """
        if self.tools is None:
            raise ValueError("Cannot add tool: this agent has no tool access (tools=None)")
        normalized_id = self._normalize_tool_id(tool_id)
        if normalized_id not in self.tools:
            self.tools.append(normalized_id)

    def remove_tool(self, tool_id: Union[str, ToolId]):
        """
        Remove a tool from the agent's configuration.

        Args:
            tool_id: The tool ID to remove (ToolId enum or string)
        """
        if self.tools is None:
            return  # Nothing to remove
        normalized_id = self._normalize_tool_id(tool_id)
        if normalized_id in self.tools:
            self.tools.remove(normalized_id)

    def get_tools(self) -> List[str]:
        """
        Get the list of tool IDs as strings.

        Returns:
            List of tool ID strings. Empty list if tools is None.
        """
        if self.tools is None:
            return []
        return self.tools.copy()
