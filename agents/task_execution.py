"""
Agent Execution Coordinator

Manages single-command execution workflow for agents.
Handles LLM querying, command parsing, and tool execution.
"""

import json
from typing import Optional, Dict, Any, TYPE_CHECKING
from core.logger import logger
from core.tool_scheduler import ToolScheduler
from core.services.context_manager import ContextManager
from agents.types import AgentOutput, ToolCall

if TYPE_CHECKING:
    from agents.agent import Agent


# Dangerous commands that require user confirmation
DANGEROUS_COMMANDS = {
    "write_file": "Write/overwrite file content",
    "edit_file": "Modify existing file content"
}

# Very dangerous bash commands patterns
VERY_DANGEROUS_BASH_PATTERNS = [
    "rm ",
    "rm\t",
    "del ",
    "rmdir ",
    "mv ",
    "rename "
]


class TaskExecution:
    """
    Coordinates single-command execution workflow for agents.

    Responsibilities:
    - Query LLM for next command
    - Parse LLM response to extract tool call
    - Execute single tool via ToolScheduler
    - Return execution result
    """

    def __init__(
        self,
        llm,
        tool_scheduler: ToolScheduler,
        context_manager: ContextManager
    ):
        """
        Initialize task execution coordinator.

        Args:
            llm: LLM wrapper for querying
            tool_scheduler: Scheduler for executing tools
            context_manager: Manager for conversation history
        """
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._context_manager = context_manager

    def __call__(
        self,
        agent: "Agent",
        user_prompt: str,
        system_prompt: str
    ) -> AgentOutput:
        """
        Execute single command workflow.

        Workflow:
        1. Build messages from conversation history
        2. Query LLM for next command
        3. Parse JSON response to extract tool_name and arguments
        4. Execute tool via ToolScheduler
        5. Return result with cmd field set

        Args:
            agent: Agent instance with identity and capabilities
            user_prompt: User query or context
            system_prompt: System prompt with instructions

        Returns:
            AgentOutput with execution result and cmd field
        """
        # Extract agent properties
        agent_id = agent.get_identity().agent_id
        capabilities = agent.get_capabilities()

        # Build messages with conversation history
        messages = self._context_manager.build_messages(
            agent_id=agent_id,
            system_prompt=system_prompt,
            max_turns=capabilities.max_memory_turns
        )

        logger.info("AGENT", "task", user_prompt)
        logger.info("AGENT", "input", messages)

        # Add current user prompt if provided
        if user_prompt:
            messages.append({
                "role": "user",
                "content": user_prompt
            })

        llm_response = self._llm.chat(
            messages,
            verbose=True,
            temperature=capabilities.llm_temperature,
            max_tokens=capabilities.llm_max_tokens,
            response_format=capabilities.llm_response_format
        )

        message = llm_response.choices[0].message if llm_response.choices else None
        if not message or not message.content:
            return AgentOutput(
                response="Error: No response from LLM",
                success=False,
                error="no_llm_response",
                cmd="llm_error",
                log="LLM returned no response"
            )

        # Parse JSON response
        tool_command = self._parse_tool_command(message.content)

        # If no tool command found, return the response directly (simple text response)
        if not tool_command or "tool_name" not in tool_command:
            # Check if the response might contain nested JSON with tool_name
            # This can happen when LLM wraps the command in a response field
            logger.warning("PARSE_WARNING", "No tool_name found at root level", {
                "content_preview": message.content[:200]
            })
            response_log = f"LLM returned direct response without tool execution."
            return AgentOutput(
                response=message.content,
                success=True,
                cmd="task_complete",
                log=response_log
            )

        tool_name = tool_command.get("tool_name")
        arguments = tool_command.get("arguments", {})

        # Check for task completion (accept both variants)
        if tool_name in ["task_complete", "task_completed"]:
            completion_log = f"Task completed: {arguments.get('message', 'No message provided')}"
            return AgentOutput(
                response=arguments.get("message", "Task completed successfully"),
                success=True,
                cmd="task_complete",
                log=completion_log
            )

        # Check if command is dangerous and needs confirmation
        is_dangerous = self._is_dangerous_command(tool_name, arguments)
        if is_dangerous:
            confirmation = self._ask_user_confirmation(tool_name, arguments)
            if not confirmation:
                cancel_log = f"User cancelled dangerous command: {tool_name}"
                return AgentOutput(
                    response=f"Command '{tool_name}' cancelled by user",
                    success=False,
                    error="user_cancelled",
                    cmd=tool_name,
                    log=cancel_log,
                    metadata={"tool_name": tool_name, "arguments": arguments}
                )

        # Execute tool
        exec_log = f"Executing tool: {tool_name} with arguments: {arguments}"

        tool_call = ToolCall(
            id=f"{tool_name}-exec",
            name=tool_name,
            args=arguments
        )

        tool_results = self._tool_scheduler.execute_tools([tool_call])
        tool_result = tool_results[0] if tool_results else None

        if not tool_result:
            error_log = f"Tool execution failed: {tool_name} - No result returned"
            return AgentOutput(
                response="Error: Tool execution failed",
                success=False,
                error="tool_execution_failed",
                cmd=tool_name,
                log=error_log
            )

        # Format response
        if tool_result["success"]:
            result_str = str(tool_result["result"])

            # Check if the result itself indicates failure (e.g., bash command failed)
            result_data = tool_result["result"]
            command_success = True

            # For bash and similar tools, check if the actual command succeeded
            if isinstance(result_data, dict) and "success" in result_data:
                command_success = result_data["success"]

            if command_success:
                success_log = f"Tool {tool_name} executed successfully. Result length: {len(result_str)} chars"
                return AgentOutput(
                    response=result_str,
                    success=True,
                    cmd=tool_name,
                    log=success_log,
                    metadata={"tool_name": tool_name, "arguments": arguments}
                )
            else:
                # Tool executed but command failed
                error_detail = result_data.get("stderr", "") or result_data.get("error", "Command failed")
                error_log = f"Tool {tool_name} command failed: {error_detail}"
                return AgentOutput(
                    response=result_str,
                    success=False,
                    error="command_failed",
                    cmd=tool_name,
                    log=error_log,
                    metadata={"tool_name": tool_name, "arguments": arguments}
                )
        else:
            error_detail = str(tool_result['result'])
            error_log = f"Tool {tool_name} failed: {error_detail}"
            return AgentOutput(
                response=f"Tool error: {error_detail}",
                success=False,
                error="tool_error",
                cmd=tool_name,
                log=error_log,
                metadata={"tool_name": tool_name, "error": error_detail}
            )

    def _parse_tool_command(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse tool command from JSON content.
        Handles both direct commands and commands nested in string fields.

        Args:
            content: JSON string with tool command

        Returns:
            Dict with tool_name and arguments, or None if invalid
        """
        try:
            content_stripped = content.strip()

            # Quick check: if content doesn't start with { or [, it's not JSON
            if not content_stripped.startswith('{') and not content_stripped.startswith('['):
                return None

            # Remove markdown code blocks if present
            import re
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content_stripped, re.DOTALL)
            if json_match:
                content_stripped = json_match.group(1).strip()

            command = json.loads(content_stripped)

            # Validate command structure
            if not isinstance(command, dict):
                return None

            # If tool_name found at root level, return immediately
            if "tool_name" in command:
                return command

            # Check for nested command JSON in common wrapper fields
            nested_fields = ["result", "response", "message", "command", "data"]
            for field in nested_fields:
                if field in command and isinstance(command[field], str):
                    # Try to parse the string as JSON
                    try:
                        nested_command = json.loads(command[field])
                        if isinstance(nested_command, dict) and "tool_name" in nested_command:
                            logger.info("PARSE_FIX", f"Extracted nested command from '{field}' field", {
                                "tool_name": nested_command.get("tool_name")
                            })
                            return nested_command
                    except json.JSONDecodeError:
                        # This field doesn't contain valid JSON, continue checking others
                        continue

            # No tool_name found at root or in nested fields
            return None

        except json.JSONDecodeError:
            # Not valid JSON, that's fine - might be plain text response
            return None
        except Exception as e:
            return None

    def _is_dangerous_command(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """
        Check if a command is dangerous and requires user confirmation.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            True if command is dangerous, False otherwise
        """
        # Check if tool is in dangerous commands list
        if tool_name in DANGEROUS_COMMANDS:
            return True

        # Special check for bash commands with destructive patterns
        if tool_name == "bash":
            command = arguments.get("command", "")
            for pattern in VERY_DANGEROUS_BASH_PATTERNS:
                if pattern in command:
                    return True

        return False

    def _ask_user_confirmation(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """
        Ask user for confirmation before executing dangerous command.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            True if user confirms, False otherwise
        """
        # Format arguments for display
        args_str = json.dumps(arguments, indent=2, ensure_ascii=False)

        # Display warning
        print("\n" + "=" * 70)
        print(f"⚠️  DANGEROUS COMMAND DETECTED: {tool_name}")
        print("=" * 70)

        # Show reason if available
        if tool_name in DANGEROUS_COMMANDS:
            print(f"Reason: {DANGEROUS_COMMANDS[tool_name]}")

        # Special message for bash with rm/mv/etc
        if tool_name == "bash":
            command = arguments.get("command", "")
            for pattern in VERY_DANGEROUS_BASH_PATTERNS:
                if pattern in command:
                    print(f"⚠️  WARNING: Command contains '{pattern.strip()}' - this can DELETE or MOVE files!")
                    break

        # Show arguments
        print(f"\nArguments:\n{args_str}")
        print("=" * 70)

        # Ask for confirmation
        while True:
            response = input("Execute this command? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")
