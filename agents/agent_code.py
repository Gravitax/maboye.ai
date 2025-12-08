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
from srcs.logger import logger
from tools.tool_base import ToolRegistry, get_registry
from agents.agent import Agent, AgentError
from agents.config import AgentConfig
from agents.types import AgentInput, AgentOutput
from LLM import LLM


class AgentCode(Agent):
    """
    Code agent with tool usage capabilities

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

            return result

        except Exception as e:
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
