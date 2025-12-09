"""
Tool Scheduler

This module is responsible for orchestrating the execution of tools based on
the agent's requests. It acts as an intermediary between the agent's reasoning
loop and the tool registry.
"""

from typing import List
import time

from core.logger import logger
from tools.tool_base import ToolRegistry, get_registry, ToolError
from agents.types import ToolCall, ToolResult


class ToolScheduler:
    """
    Manages the execution of tool calls requested by an agent.

    The ToolScheduler takes a list of tool calls, executes them using the
    provided ToolRegistry, and returns a list of corresponding results.
    """

    def __init__(self, registry: ToolRegistry):
        """
        Initializes the ToolScheduler.

        Args:
            registry: An instance of ToolRegistry containing the available tools.
        """
        self._registry = registry

    def execute_tools(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """
        Executes a list of tool calls and returns the results.

        Each tool call is executed sequentially. If a tool execution fails,
        an error message is captured in the result, but the scheduler continues
        to process the remaining tool calls.

        Args:
            tool_calls: A list of ToolCall dictionaries.

        Returns:
            A list of ToolResult dictionaries corresponding to each tool call.
        """
        results: List[ToolResult] = []

        if not tool_calls:
            return results

        logger.info("TOOL_SCHEDULER", f"Executing {len(tool_calls)} tool call(s)")

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call.get("id", tool_name)  # Fallback to name if no id
            start_time = time.time()
            
            try:
                if not self._registry.has_tool(tool_name):
                    raise ToolError(f"Tool '{tool_name}' not found in registry.")

                logger.debug("TOOL_SCHEDULER", "Executing tool", {
                    "tool": tool_name,
                    "args": tool_args
                })

                # The registry's execute method handles the full run cycle
                execution_result = self._registry.execute(tool_name, **tool_args)
                
                execution_time = time.time() - start_time
                result_str = str(execution_result)
                success = True

            except Exception as e:
                execution_time = time.time() - start_time
                result_str = f"Error executing tool '{tool_name}': {e}"
                success = False
                logger.error("TOOL_SCHEDULER", result_str)

            results.append({
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "result": result_str,
                "success": success,
                "execution_time": execution_time,
            })

        logger.info("TOOL_SCHEDULER", "Finished executing tool calls", {
            "call_count": len(tool_calls),
            "result_count": len(results),
        })
        return results


def get_default_scheduler() -> ToolScheduler:
    """
    Returns a ToolScheduler initialized with the global tool registry.

    Returns:
        A default ToolScheduler instance.
    """
    return ToolScheduler(registry=get_registry())
