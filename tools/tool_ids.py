"""
Tool IDs Enum

Centralized enum for all tool identifiers in the system.
Used by agents to specify which tools they can access.
"""

from enum import Enum, unique


@unique
class ToolId(str, Enum):
    """
    Enum of all available tool identifiers.

    Each tool in the system must have a unique ID defined here.
    Agents reference these IDs in their configuration to specify available tools.
    """

    # File operations
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    LIST_DIRECTORY = "list_directory"

    # Search operations
    GLOB_FILES = "glob_files"
    GREP_CONTENT = "grep_content"
    CODE_SEARCH = "code_search"

    # Shell operations
    EXECUTE_COMMAND = "execute_command"

    # Git operations
    GIT_STATUS = "git_status"
    GIT_ADD = "git_add"
    GIT_COMMIT = "git_commit"
    GIT_DIFF = "git_diff"
    GIT_LOG = "git_log"

    def __str__(self) -> str:
        """Return the string value of the enum"""
        return self.value

    @classmethod
    def all_tools(cls) -> list:
        """
        Get all available tool IDs.

        Returns:
            List of all tool ID values
        """
        return [tool.value for tool in cls]

    @classmethod
    def file_tools(cls) -> list:
        """
        Get all file operation tool IDs.

        Returns:
            List of file operation tool IDs
        """
        return [
            cls.READ_FILE.value,
            cls.WRITE_FILE.value,
            cls.EDIT_FILE.value,
            cls.LIST_DIRECTORY.value,
        ]

    @classmethod
    def search_tools(cls) -> list:
        """
        Get all search tool IDs.

        Returns:
            List of search tool IDs
        """
        return [
            cls.GLOB_FILES.value,
            cls.GREP_CONTENT.value,
            cls.CODE_SEARCH.value,
        ]

    @classmethod
    def shell_tools(cls) -> list:
        """
        Get all shell tool IDs.

        Returns:
            List of shell tool IDs
        """
        return [cls.EXECUTE_COMMAND.value]

    @classmethod
    def git_tools(cls) -> list:
        """
        Get all git tool IDs.

        Returns:
            List of git tool IDs
        """
        return [
            cls.GIT_STATUS.value,
            cls.GIT_ADD.value,
            cls.GIT_COMMIT.value,
            cls.GIT_DIFF.value,
            cls.GIT_LOG.value,
        ]

    @classmethod
    def safe_tools(cls) -> list:
        """
        Get read-only/safe tool IDs (no writes, no execution).

        Returns:
            List of safe tool IDs
        """
        return [
            cls.READ_FILE.value,
            cls.LIST_DIRECTORY.value,
            cls.GLOB_FILES.value,
            cls.GREP_CONTENT.value,
            cls.CODE_SEARCH.value,
            cls.GIT_STATUS.value,
            cls.GIT_DIFF.value,
            cls.GIT_LOG.value,
        ]

    @classmethod
    def dangerous_tools(cls) -> list:
        """
        Get potentially dangerous tool IDs (writes, execution).

        Returns:
            List of dangerous tool IDs
        """
        return [
            cls.WRITE_FILE.value,
            cls.EDIT_FILE.value,
            cls.EXECUTE_COMMAND.value,
            cls.GIT_ADD.value,
            cls.GIT_COMMIT.value,
        ]
