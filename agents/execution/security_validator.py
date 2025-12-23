"""
Security validation for dangerous commands

Detects potentially destructive operations that require user confirmation.
"""

import re
from typing import Dict, Any
from core.logger import logger
from tools.tool_ids import ToolId


# Regex to detect destructive commands in bash arguments
DANGEROUS_BASH_REGEX = re.compile(r'(^|[;\s|&])(rm|del|rmdir|mv|rename)(\s+|$)', re.IGNORECASE)


def is_dangerous_command(tool_name: str, arguments: Dict[str, Any]) -> bool:
    """
    Check if command is dangerous and requires user confirmation.

    Uses centralized ToolId dangerous tools list and regex validation for bash commands.

    Args:
        tool_name: Name of tool to execute
        arguments: Tool arguments

    Returns:
        True if command is dangerous and needs confirmation
    """
    # Check centralized dangerous tools list
    dangerous_tools = ToolId.dangerous_tools()

    if tool_name in dangerous_tools:
        # Special case for Bash: analyze internal command
        if tool_name == ToolId.EXECUTE_COMMAND.value or tool_name == "bash":
            cmd = arguments.get("command", "")
            if DANGEROUS_BASH_REGEX.search(cmd):
                logger.warning("SECURITY", "Dangerous Bash Pattern", cmd)
                return True
            # If just "ls" or "echo", could be safe, but EXECUTE_COMMAND is classified
            # as dangerous by default. Return True to force confirmation unless explicit
            # whitelist (optional)
            return True

        return True

    return False
