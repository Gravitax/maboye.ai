"""
Tool IDs Enum

Centralized enum for all tool identifiers in the system.
Used by agents to specify which tools they can access.
"""

from enum import Enum, unique
from typing import List


@unique
class ToolId(str, Enum):
    """
    Enum for tool identifiers.
    
    This ensures consistency and avoids magic strings when referencing tools.
    """
    # Core Tools
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    LIST_DIRECTORY = "list_directory"
    CODE_SEARCH = "code_search"
    EXECUTE_COMMAND = "execute_command"
    GIT_STATUS = "git_status"
    GIT_ADD = "git_add"
    GIT_COMMIT = "git_commit"
    GIT_DIFF = "git_diff"
    GIT_LOG = "git_log"

    # Control Flow Tools
    TASK_SUCCESS = "task_success"
    TASK_ERROR = "task_error"
    
    # ... potentially other tool IDs
    
    @staticmethod
    def dangerous_tools() -> List[str]:
        """Returns a list of tool IDs considered dangerous and requiring user confirmation."""
        return [
            ToolId.WRITE_FILE.value,
            ToolId.EDIT_FILE.value,
            ToolId.EXECUTE_COMMAND.value,
            ToolId.GIT_ADD.value,
            ToolId.GIT_COMMIT.value,
        ]
