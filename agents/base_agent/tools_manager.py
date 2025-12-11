"""
Tools Agent Manager

Handles all tool-related operations including tool execution,
result storage, and message management with config-based filtering.
"""

from typing import List

from core.logger import logger
from core.tool_scheduler import ToolScheduler
from core.memory import MemoryManager
from agents.config import AgentConfig
from agents.types import Message, ToolCall, ToolResult


class ToolsAgentManager:
    """
    Manages tool operations for agents.

    Responsibilities:
    - Filtering tool calls based on agent configuration
    - Executing tool calls via the scheduler
    - Storing tool results in memory
    - Appending tool results to message lists
    """

    def __init__(self, tool_scheduler: ToolScheduler, memory_manager: MemoryManager, config: AgentConfig):
        """
        Initialize the tools manager.

        Args:
            tool_scheduler: The component responsible for executing tools.
            memory_manager: The central memory system for storing results.
            config: Agent configuration containing allowed tools.
        """
        self._tool_scheduler = tool_scheduler
        self._memory_manager = memory_manager
        self._config = config

    def execute_and_store_tools(
        self, tool_calls: List[ToolCall], messages: List[Message]
    ) -> List[ToolResult]:
        """
        Execute tools and store their results in memory and messages.
        Only executes tools that are allowed in the agent's configuration.

        Args:
            tool_calls: List of tool calls to execute.
            messages: Message list to append results to.

        Returns:
            List of tool results (including rejection results for unauthorized tools).
        """
        # Filter tool calls based on agent configuration
        filtered_tool_calls = []
        rejected_results = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")

            # Check if tool is allowed in configuration
            if self._is_tool_allowed(tool_name):
                filtered_tool_calls.append(tool_call)
            else:
                # Create rejection result for unauthorized tool
                rejected_result = self._create_rejection_result(tool_call)
                rejected_results.append(rejected_result)
                logger.warning(
                    "TOOLS_MANAGER",
                    f"Tool '{tool_name}' rejected - not in agent configuration",
                    {"agent": self._config.name, "allowed_tools": self._config.get_tools()}
                )

        # Execute allowed tools
        tool_results = []
        if filtered_tool_calls:
            tool_results = self._tool_scheduler.execute_tools(filtered_tool_calls)

        # Combine executed and rejected results
        all_results = tool_results + rejected_results

        # Store and append all results
        for tool_result in all_results:
            self._store_single_tool_result(tool_result)
            self._append_tool_result_to_messages(tool_result, messages)

        return all_results

    def _is_tool_allowed(self, tool_name: str) -> bool:
        """
        Check if a tool is allowed based on agent configuration.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            True if tool is allowed or no tools configured (allow all), False otherwise.
        """
        # If no tools configured, allow all tools
        if not self._config.tools:
            return True

        # Check if tool is in allowed list
        return self._config.has_tool(tool_name)

    def _create_rejection_result(self, tool_call: ToolCall) -> ToolResult:
        """
        Create a rejection result for an unauthorized tool call.

        Args:
            tool_call: The rejected tool call.

        Returns:
            ToolResult indicating rejection.
        """
        tool_name = tool_call.get("name", "unknown")
        allowed_tools = ", ".join(self._config.get_tools()) if self._config.tools else "none"

        return {
            "tool_call_id": tool_call.get("id", ""),
            "tool_name": tool_name,
            "result": f"Error: Tool '{tool_name}' is not authorized for this agent. Allowed tools: [{allowed_tools}]",
            "success": False,
            "execution_time": 0.0
        }

    def _store_single_tool_result(self, tool_result: ToolResult) -> None:
        """
        Store a single tool result in memory.

        Args:
            tool_result: The tool result to store.
        """
        self._memory_manager.add_tool_result(
            tool_name=tool_result["tool_name"],
            result=tool_result["result"],
            success=tool_result["success"],
            execution_time=tool_result["execution_time"]
        )

    def _append_tool_result_to_messages(
        self, tool_result: ToolResult, messages: List[Message]
    ) -> None:
        """
        Append a tool result to the message list.

        Args:
            tool_result: The tool result to append.
            messages: The message list.
        """
        messages.append({
            "role": "tool",
            "tool_call_id": tool_result["tool_call_id"],
            "content": tool_result["result"],
        })
