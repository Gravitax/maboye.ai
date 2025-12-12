"""
CLI Commands Module

Contains all terminal command implementations.
"""

from typing import Dict, Callable

def get_all_commands() -> Dict[str, tuple]:
    """
    Get all available commands.

    Returns:
        Dictionary mapping command names to (handler, description) tuples
    """
    from .memory_command import MemoryCommand
    from .reset_command import ResetCommand
    from .tools_command import ToolsCommand
    from .agents_command import AgentsCommand

    commands = {}

    memory_cmd = MemoryCommand()
    commands["memory"] = (memory_cmd.execute, memory_cmd.description)

    reset_cmd = ResetCommand()
    commands["reset"] = (reset_cmd.execute, reset_cmd.description)

    tools_cmd = ToolsCommand()
    commands["tools"] = (tools_cmd.execute, tools_cmd.description)

    agents_cmd = AgentsCommand()
    commands["agents"] = (agents_cmd.execute, agents_cmd.description)

    return commands


__all__ = ["get_all_commands"]
