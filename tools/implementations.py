"""
Tool implementations wrapping existing operations

Provides Tool class wrappers for file operations, search, shell, and git.
All implementations delegate to existing functions to avoid code duplication.
"""

import sys
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.tool_base import Tool, ToolMetadata, ToolParameter
from tools import file_ops
from tools import search
from tools import shell
from tools import git_ops


# File Operations Tools

class ReadFileTool(Tool):
    """Tool for reading files"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="read_file",
            description="Read file contents with optional offset and limit",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=str,
                    description="Path to file",
                    required=True
                ),
                ToolParameter(
                    name="offset",
                    type=int,
                    description="Line offset to start reading from",
                    required=False,
                    default=0
                ),
                ToolParameter(
                    name="limit",
                    type=int,
                    description="Maximum number of lines to read",
                    required=False,
                    default=None
                )
            ],
            category="file_operations"
        )

    def execute(self, file_path: str, offset: int = 0, limit: int = None) -> str:
        return file_ops.read_file(file_path, offset, limit)


class WriteFileTool(Tool):
    """Tool for writing files"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="write_file",
            description="Write content to file",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=str,
                    description="Path to file",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type=str,
                    description="Content to write",
                    required=True
                ),
                ToolParameter(
                    name="create_dirs",
                    type=bool,
                    description="Create parent directories if needed",
                    required=False,
                    default=True
                )
            ],
            category="file_operations",
            dangerous=True
        )

    def execute(self, file_path: str, content: str, create_dirs: bool = True) -> bool:
        return file_ops.write_file(file_path, content, create_dirs)


class EditFileTool(Tool):
    """Tool for editing files"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="edit_file",
            description="Edit file by replacing text",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=str,
                    description="Path to file",
                    required=True
                ),
                ToolParameter(
                    name="old_string",
                    type=str,
                    description="Text to find",
                    required=True
                ),
                ToolParameter(
                    name="new_string",
                    type=str,
                    description="Text to replace with",
                    required=True
                ),
                ToolParameter(
                    name="replace_all",
                    type=bool,
                    description="Replace all occurrences",
                    required=False,
                    default=False
                )
            ],
            category="file_operations",
            dangerous=True
        )

    def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False
    ) -> bool:
        return file_ops.edit_file(file_path, old_string, new_string, replace_all)


# Search Tools

class GlobFilesTool(Tool):
    """Tool for finding files by pattern"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="glob_files",
            description="Find files matching pattern",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type=str,
                    description="Glob pattern (e.g., '*.py')",
                    required=True
                ),
                ToolParameter(
                    name="path",
                    type=str,
                    description="Directory to search in",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="recursive",
                    type=bool,
                    description="Enable recursive search",
                    required=False,
                    default=True
                )
            ],
            category="search"
        )

    def execute(self, pattern: str, path: str = ".", recursive: bool = True):
        return search.glob_files(pattern, path, recursive)


class GrepContentTool(Tool):
    """Tool for searching file contents"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="grep_content",
            description="Search file contents for pattern",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type=str,
                    description="Regex pattern to search for",
                    required=True
                ),
                ToolParameter(
                    name="path",
                    type=str,
                    description="Directory to search in",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="file_pattern",
                    type=str,
                    description="File pattern filter",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="case_sensitive",
                    type=bool,
                    description="Case-sensitive search",
                    required=False,
                    default=True
                )
            ],
            category="search"
        )

    def execute(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = None,
        case_sensitive: bool = True
    ):
        return search.grep_content(pattern, path, file_pattern, case_sensitive)


# Shell Tools

class ExecuteCommandTool(Tool):
    """Tool for executing shell commands"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="execute_command",
            description="Execute shell command",
            parameters=[
                ToolParameter(
                    name="command",
                    type=str,
                    description="Command to execute",
                    required=True
                ),
                ToolParameter(
                    name="cwd",
                    type=str,
                    description="Working directory",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="timeout",
                    type=int,
                    description="Timeout in seconds",
                    required=False,
                    default=120
                )
            ],
            category="shell",
            dangerous=True
        )

    def execute(
        self,
        command: str,
        cwd: str = None,
        timeout: int = 120
    ) -> shell.ShellResult:
        return shell.execute_command(command, cwd, timeout)


# Git Tools

class GitStatusTool(Tool):
    """Tool for Git status"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_status",
            description="Get Git repository status",
            parameters=[
                ToolParameter(
                    name="path",
                    type=str,
                    description="Repository path",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="porcelain",
                    type=bool,
                    description="Use machine-readable format",
                    required=False,
                    default=False
                )
            ],
            category="git"
        )

    def execute(self, path: str = ".", porcelain: bool = False) -> str:
        return git_ops.git_status(path, porcelain)


class GitAddTool(Tool):
    """Tool for staging files"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_add",
            description="Stage files for commit",
            parameters=[
                ToolParameter(
                    name="files",
                    type=list,
                    description="List of files to add",
                    required=True
                ),
                ToolParameter(
                    name="path",
                    type=str,
                    description="Repository path",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="all_files",
                    type=bool,
                    description="Add all files",
                    required=False,
                    default=False
                )
            ],
            category="git",
            dangerous=True
        )

    def execute(self, files: list, path: str = ".", all_files: bool = False) -> bool:
        return git_ops.git_add(files, path, all_files)


class GitCommitTool(Tool):
    """Tool for creating commits"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_commit",
            description="Create Git commit",
            parameters=[
                ToolParameter(
                    name="message",
                    type=str,
                    description="Commit message",
                    required=True
                ),
                ToolParameter(
                    name="path",
                    type=str,
                    description="Repository path",
                    required=False,
                    default="."
                )
            ],
            category="git",
            dangerous=True
        )

    def execute(self, message: str, path: str = ".") -> str:
        return git_ops.git_commit(message, path)


def register_all_tools():
    """Register all tool implementations in global registry"""
    from tools.tool_base import register_tool

    # File operations
    register_tool(ReadFileTool())
    register_tool(WriteFileTool())
    register_tool(EditFileTool())

    # Search
    register_tool(GlobFilesTool())
    register_tool(GrepContentTool())

    # Shell
    register_tool(ExecuteCommandTool())

    # Git
    register_tool(GitStatusTool())
    register_tool(GitAddTool())
    register_tool(GitCommitTool())
