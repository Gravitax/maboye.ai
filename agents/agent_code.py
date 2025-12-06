"""
Code Agent class with tool usage capabilities

Specialized agent for code-related tasks with access to file operations,
search, shell commands, and Git operations through the tool registry.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.logger import logger
from tools.tool_base import ToolRegistry, get_registry
from agents.agent import Agent, AgentError
from agents.config import AgentConfig
from LLM import LLM


class AgentCode(Agent):
    """
    Code agent with tool usage capabilities

    Extends base Agent with tool registry integration for code operations:
    - File operations (read, write, edit)
    - Search operations (glob, grep)
    - Shell command execution
    - Git operations

    Tools are executed through the registry with automatic tracking
    and logging.
    """

    def __init__(
        self,
        llm: LLM,
        config: Optional[AgentConfig] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        """
        Initialize code agent

        Args:
            llm: LLM instance for API calls
            config: Agent configuration (uses defaults if None)
            tool_registry: Tool registry (uses global if None)
        """
        super().__init__(llm, config)

        self._tool_registry = tool_registry or get_registry()
        self._tool_executions: List[Dict[str, Any]] = []

        if self._config.enable_logging:
            logger.info("AGENT_CODE", "Code agent initialized", {
                "name": self._config.name,
                "available_tools": len(self._tool_registry.list_tools())
            })

    def use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool by name

        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters

        Returns:
            Tool execution result

        Raises:
            AgentError: Tool execution failed
        """
        try:
            if self._config.enable_logging:
                logger.info("AGENT_CODE", "Using tool", {
                    "name": self._config.name,
                    "tool": tool_name,
                    "params": list(kwargs.keys())
                })

            result = self._tool_registry.execute(tool_name, **kwargs)

            # Track tool execution
            self._tool_executions.append({
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "params": kwargs,
                "success": True
            })

            return result

        except Exception as e:
            self._tool_executions.append({
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "params": kwargs,
                "success": False,
                "error": str(e)
            })

            if self._config.enable_logging:
                logger.error("AGENT_CODE", "Tool execution failed", {
                    "name": self._config.name,
                    "tool": tool_name,
                    "error": str(e)
                })

            raise AgentError(f"Tool execution failed: {e}")

    def list_available_tools(
        self,
        category: Optional[str] = None,
        include_dangerous: bool = False
    ) -> List[str]:
        """
        List available tools

        Args:
            category: Filter by category
            include_dangerous: Include dangerous tools

        Returns:
            List of tool names
        """
        return self._tool_registry.list_tools(
            category=category,
            include_dangerous=include_dangerous
        )

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get tool information

        Args:
            tool_name: Tool name

        Returns:
            Tool information dictionary
        """
        return self._tool_registry.get_tool_info(tool_name)

    def get_tool_executions(self) -> List[Dict[str, Any]]:
        """
        Get tool execution history

        Returns:
            List of tool execution records
        """
        return self._tool_executions.copy()

    def clear_tool_executions(self):
        """Clear tool execution history"""
        self._tool_executions.clear()

        if self._config.enable_logging:
            logger.debug("AGENT_CODE", "Tool executions cleared", {
                "name": self._config.name
            })

    def reset(self):
        """Reset agent state including tool executions"""
        super().reset()
        self._tool_executions.clear()

        if self._config.enable_logging:
            logger.info("AGENT_CODE", "Code agent reset", {
                "name": self._config.name
            })

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics including tool usage

        Returns:
            Statistics dictionary
        """
        base_stats = super().get_stats()

        # Add tool-specific stats
        base_stats.update({
            "tool_executions": len(self._tool_executions),
            "available_tools": len(self._tool_registry.list_tools()),
            "successful_tool_executions": sum(
                1 for e in self._tool_executions if e.get("success", False)
            ),
            "failed_tool_executions": sum(
                1 for e in self._tool_executions if not e.get("success", False)
            )
        })

        return base_stats
