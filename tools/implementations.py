"""
Tool implementations wrapping existing operations

Provides Tool class wrappers for file operations, search, shell, and git.
All implementations delegate to existing functions to avoid code duplication.
"""

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


class ListDirectoryTool(Tool):
    """Tool for listing directory contents"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="list_directory",
            description="List directory contents with metadata",
            parameters=[
                ToolParameter(
                    name="path",
                    type=str,
                    description="Directory path to list",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="include_hidden",
                    type=bool,
                    description="Include hidden files",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="files_only",
                    type=bool,
                    description="List only files",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="dirs_only",
                    type=bool,
                    description="List only directories",
                    required=False,
                    default=False
                )
            ],
            category="search"
        )

    def execute(
        self,
        path: str = ".",
        include_hidden: bool = False,
        files_only: bool = False,
        dirs_only: bool = False
    ):
        return search.list_directory(path, include_hidden, files_only, dirs_only)


class CodeSearchTool(Tool):
    """Tool for high-performance code search using ripgrep"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="code_search",
            description="Search code with ripgrep for maximum performance",
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
                ),
                ToolParameter(
                    name="max_results",
                    type=int,
                    description="Maximum number of results",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="context_lines",
                    type=int,
                    description="Lines of context around matches",
                    required=False,
                    default=2
                )
            ],
            category="search"
        )

    def execute(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = None,
        case_sensitive: bool = True,
        max_results: int = None,
        context_lines: int = 2
    ):
        return search.code_search(
            pattern,
            path,
            file_pattern,
            case_sensitive,
            max_results,
            context_lines
        )


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


class GitDiffTool(Tool):
    """Tool for viewing Git diffs"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_diff",
            description="View Git diff of changes",
            parameters=[
                ToolParameter(
                    name="path",
                    type=str,
                    description="Repository path",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="staged",
                    type=bool,
                    description="Show staged changes",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="files",
                    type=list,
                    description="Specific files to diff",
                    required=False,
                    default=None
                )
            ],
            category="git"
        )

    def execute(
        self,
        path: str = ".",
        staged: bool = False,
        files: list = None
    ) -> str:
        return git_ops.git_diff(path, staged, files)


class GitLogTool(Tool):
    """Tool for viewing Git commit history"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_log",
            description="View Git commit history",
            parameters=[
                ToolParameter(
                    name="path",
                    type=str,
                    description="Repository path",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="max_count",
                    type=int,
                    description="Maximum commits to show",
                    required=False,
                    default=10
                ),
                ToolParameter(
                    name="oneline",
                    type=bool,
                    description="One line per commit",
                    required=False,
                    default=False
                )
            ],
            category="git"
        )

    def execute(
        self,
        path: str = ".",
        max_count: int = 10,
        oneline: bool = False
    ) -> str:
        return git_ops.git_log(path, max_count, oneline)


class TaskSuccessTool(Tool):
    """Tool to signal that the current task is completed successfully."""

    def _define_metadata(self) -> ToolMetadata:
        from tools.tool_ids import ToolId # Import here to avoid circular dependency
        return ToolMetadata(
            name=ToolId.TASK_SUCCESS.value,
            description="Signal that the current task is completed successfully and return the final result or message.",
            parameters=[
                ToolParameter(
                    name="message",
                    type=str,
                    description="The final message or result upon task completion.",
                    required=False,
                    default="Task completed successfully."
                )
            ],
            category="control_flow"
        )

    def execute(self, message: str = "Task completed successfully.") -> str:
        return message


class TaskErrorTool(Tool):
    """Tool to signal that the current task has failed."""

    def _define_metadata(self) -> ToolMetadata:
        from tools.tool_ids import ToolId # Import here to avoid circular dependency
        return ToolMetadata(
            name=ToolId.TASK_ERROR.value,
            description="Signal that the current task has encountered an unrecoverable error.",
            parameters=[
                ToolParameter(
                    name="error_message",
                    type=str,
                    description="A detailed message describing the error.",
                    required=True
                )
            ],
            category="control_flow",
            dangerous=True # Signalling an error might require careful handling
        )

    def execute(self, error_message: str) -> str:
        return f"Task failed: {error_message}"


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
    register_tool(ListDirectoryTool())
    register_tool(CodeSearchTool())

    # Shell
    register_tool(ExecuteCommandTool())

    # Git
    register_tool(GitStatusTool())
    register_tool(GitAddTool())
    register_tool(GitCommitTool())
    register_tool(GitDiffTool())
    register_tool(GitLogTool())
    
    # Control Flow
    register_tool(TaskSuccessTool())
    register_tool(TaskErrorTool())
