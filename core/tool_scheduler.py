"""
Tool Scheduler

This module is responsible for orchestrating the execution of tools based on
the agent's requests. It acts as an intermediary between the agent's reasoning
loop and the tool registry.
"""

from typing import List, Dict, Any
import time

from core.logger import logger
from tools.tool_base import ToolRegistry, get_registry, ToolError, ToolParameter
from agents.types import ToolCall, ToolResult


class ToolScheduler:
    """
    Manages the execution of tool calls requested by an agent.

    The ToolScheduler takes a list of tool calls, executes them using the
    provided ToolRegistry, and returns a list of corresponding results.
    Includes robust parameter validation and type coercion for LLM safety.
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

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            raw_args = tool_call.get("args", {})
            tool_call_id = tool_call.get("id", tool_name)  # Fallback to name if no id
            
            start_time = time.time()
            success = False
            result_str = ""

            try:
                if not self._registry.has_tool(tool_name):
                    raise ToolError(f"Tool '{tool_name}' not found.")

                # 1. Get tool instance to access actual metadata (including types)
                tool = self._registry.get_tool(tool_name)
                if not tool:
                    raise ToolError(f"Tool '{tool_name}' could not be retrieved.")

                # 2. Validation and Casting of arguments (Crucial for LLMs)
                validated_args = self._validate_and_coerce_args(raw_args, tool.metadata.parameters)

                # 3. Execution
                # The registry's execute method handles the full run cycle
                execution_result = self._registry.execute(tool_name, **validated_args)
                
                # Handle output
                # We preserve the original type (e.g. dict) to allow TaskExecution to inspect it
                # String conversion will happen at the boundary if needed
                result_data = execution_result
                
                success = True

            except ToolError as e:
                result_data = f"Tool Error: {str(e)}"
            except TypeError as e:
                result_data = f"Argument Error: {str(e)}"
            except Exception as e:
                logger.error("TOOL_EXEC", f"Crash in {tool_name}", str(e))
                result_data = f"System Error executing '{tool_name}': {str(e)}"

            # 4. Security truncation (prevent context saturation) - Only for strings
            MAX_OUTPUT_LEN = 4000
            if isinstance(result_data, str) and len(result_data) > MAX_OUTPUT_LEN:
                result_data = result_data[:MAX_OUTPUT_LEN] + f"\n... [Output truncated. Total length: {len(result_data)} chars]"

            execution_time = time.time() - start_time
            
            results.append({
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "result": result_data,
                "success": success,
                "execution_time": execution_time,
            })
            
        return results

    def _validate_and_coerce_args(self, args: Dict[str, Any], parameters: List[ToolParameter]) -> Dict[str, Any]:
        """
        Validates and converts arguments according to the types defined in metadata.
        Handles frequent cases where LLMs send "true" (str) for bool, or "10" (str) for int.
        """
        validated = {}
        
        # Create a map of expected parameters
        param_map = {p.name: p for p in parameters}
        
        # Verify provided arguments
        for key, value in args.items():
            if key not in param_map:
                # Ignore undocumented arguments
                continue
                
            expected_type = param_map[key].type
            
            # Intelligent casting attempt
            if expected_type == int and isinstance(value, str):
                if value.isdigit():
                    value = int(value)
            elif expected_type == bool and isinstance(value, str):
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
            
            validated[key] = value

        # Verify missing required fields and default values
        for param in parameters:
            name = param.name
            if name not in validated:
                if param.required:
                    # If a default value exists, use it, otherwise error
                    if param.default is not None:
                        validated[name] = param.default
                    else:
                        raise ToolError(f"Missing required argument: '{name}'")
                elif param.default is not None:
                     validated[name] = param.default

        return validated


def get_default_scheduler() -> ToolScheduler:
    """
    Returns a ToolScheduler initialized with the global tool registry.

    Returns:
        A default ToolScheduler instance.
    """
    return ToolScheduler(registry=get_registry())
