"""
Tool base class and registry system

Provides a unified interface for all agent tools with parameter validation,
execution tracking, and a central registry.
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from core.logger import logger


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: type
    description: str
    required: bool = True
    default: Any = None


@dataclass
class ToolMetadata:
    """Tool metadata"""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    category: str = "general"
    dangerous: bool = False


class ToolError(Exception):
    """Base exception for tool errors"""
    pass


class ToolExecutionError(ToolError):
    """Tool execution failed"""
    pass


class ToolValidationError(ToolError):
    """Tool parameter validation failed"""
    pass


class Tool(ABC):
    """
    Base class for all tools

    Tools provide specific capabilities to agents (file operations,
    search, shell commands, etc.). Each tool must implement execute()
    and define metadata.
    """

    def __init__(self):
        self._metadata = self._define_metadata()
        self._validate_metadata()

    @abstractmethod
    def _define_metadata(self) -> ToolMetadata:
        """
        Define tool metadata

        Returns:
            ToolMetadata instance
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute tool with given parameters

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ToolExecutionError: Execution failed
        """
        pass

    def _validate_metadata(self):
        """Validate metadata is properly defined"""
        if not self._metadata.name:
            raise ToolError("Tool name not defined")
        if not self._metadata.description:
            raise ToolError("Tool description not defined")

    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and prepare parameters

        Args:
            params: Input parameters

        Returns:
            Validated parameters with defaults applied

        Raises:
            ToolValidationError: Parameter validation failed
        """
        validated = {}

        # Check all required parameters
        for param_def in self._metadata.parameters:
            if param_def.required and param_def.name not in params:
                raise ToolValidationError(
                    f"Missing required parameter: {param_def.name}"
                )

            # Get value or use default
            if param_def.name in params:
                value = params[param_def.name]

                # Type checking (basic)
                if value is not None and not isinstance(value, param_def.type):
                    # Try to convert
                    try:
                        value = param_def.type(value)
                    except (ValueError, TypeError):
                        raise ToolValidationError(
                            f"Invalid type for {param_def.name}: "
                            f"expected {param_def.type.__name__}, "
                            f"got {type(value).__name__}"
                        )

                validated[param_def.name] = value
            elif param_def.default is not None:
                validated[param_def.name] = param_def.default

        return validated

    def run(self, **kwargs) -> Any:
        """
        Run tool with parameter validation and logging

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ToolValidationError: Parameter validation failed
            ToolExecutionError: Execution failed
        """
        try:
            # Validate parameters
            validated_params = self.validate_parameters(kwargs)

            logger.debug("TOOL", f"Executing {self._metadata.name}", {
                "tool": self._metadata.name,
                "params": list(validated_params.keys())
            })

            # Execute tool
            result = self.execute(**validated_params)
            return result

        except ToolValidationError:
            raise
        except ToolExecutionError:
            raise
        except Exception as e:
            logger.error("TOOL", f"{self._metadata.name} failed", {
                "tool": self._metadata.name,
                "error": str(e)
            })
            raise ToolExecutionError(
                f"Tool {self._metadata.name} failed: {e}"
            )

    @property
    def name(self) -> str:
        """Get tool name"""
        return self._metadata.name

    @property
    def description(self) -> str:
        """Get tool description"""
        return self._metadata.description

    @property
    def metadata(self) -> ToolMetadata:
        """Get full metadata"""
        return self._metadata

    @property
    def is_dangerous(self) -> bool:
        """Check if tool is dangerous"""
        return self._metadata.dangerous


class ToolRegistry:
    """
    Central registry for all tools

    Manages tool registration, discovery, and retrieval.
    Provides a unified interface for agents to access tools.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool: Tool):
        """
        Register a tool

        Args:
            tool: Tool instance to register

        Raises:
            ToolError: Tool already registered
        """
        if tool.name in self._tools:
            logger.warning("TOOL_REGISTRY", f"Tool already registered: {tool.name}. Skipping registration.")
            return

        self._tools[tool.name] = tool

        # Add to category
        category = tool.metadata.category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool.name)

    def unregister(self, tool_name: str):
        """
        Unregister a tool

        Args:
            tool_name: Name of tool to unregister
        """
        if tool_name in self._tools:
            tool = self._tools[tool_name]
            category = tool.metadata.category

            del self._tools[tool_name]

            if category in self._categories:
                self._categories[category].remove(tool_name)
                if not self._categories[category]:
                    del self._categories[category]

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get tool by name

        Args:
            tool_name: Tool name

        Returns:
            Tool instance or None
        """
        return self._tools.get(tool_name)

    def has_tool(self, tool_name: str) -> bool:
        """
        Check if tool is registered

        Args:
            tool_name: Tool name

        Returns:
            True if registered
        """
        return tool_name in self._tools

    def list_tools(
        self,
        category: Optional[str] = None,
        include_dangerous: bool = True
    ) -> List[str]:
        """
        List all registered tools

        Args:
            category: Filter by category
            include_dangerous: Include dangerous tools

        Returns:
            List of tool names
        """
        if category:
            tools = self._categories.get(category, [])
        else:
            tools = list(self._tools.keys())

        if not include_dangerous:
            tools = [
                name for name in tools
                if not self._tools[name].metadata.dangerous
            ]

        return sorted(tools)

    def get_categories(self) -> List[str]:
        """
        Get all tool categories

        Returns:
            List of category names
        """
        return sorted(self._categories.keys())

    def execute(self, tool_name: str, **kwargs) -> Any:
        """
        Execute tool by name

        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ToolError: Tool not found
            ToolExecutionError: Execution failed
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolError(f"Tool not found: {tool_name}")

        return tool.run(**kwargs)

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get tool information

        Args:
            tool_name: Tool name

        Returns:
            Dictionary with tool information
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        return {
            "name": tool.name,
            "description": tool.description,
            "category": tool.metadata.category,
            "dangerous": tool.metadata.dangerous,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type.__name__,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in tool.metadata.parameters
            ]
        }

    def get_all_tools_info(self) -> List[Dict[str, Any]]:
        """
        Get information for all tools

        Returns:
            List of tool information dictionaries
        """
        return [
            self.get_tool_info(name)
            for name in self.list_tools()
        ]


# Global tool registry instance
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """
    Get global tool registry

    Returns:
        Global ToolRegistry instance
    """
    return _global_registry


def register_tool(tool: Tool):
    """
    Register tool in global registry

    Args:
        tool: Tool to register
    """
    _global_registry.register(tool)


def get_tool(tool_name: str) -> Optional[Tool]:
    """
    Get tool from global registry

    Args:
        tool_name: Tool name

    Returns:
        Tool instance or None
    """
    return _global_registry.get_tool(tool_name)
