"""
Bash and Git execution tools

Provides safe execution of shell commands and Git operations.
Includes security measures like command whitelisting and timeout handling.
"""

from typing import List, Dict, Any

from tools.tool_base import Tool, ToolMetadata, ToolParameter
from tools import shell, git_ops
from tools.security_constants import DANGEROUS_SHELL_COMMANDS


class BashTool(Tool):
    """
    Execute bash commands safely

    Executes shell commands with security checks. Commands are validated
    against whitelist/blacklist and run with timeout protection.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="bash",
            description="Execute shell command with security checks and timeout",
            parameters=[
                ToolParameter(
                    name="command",
                    type=str,
                    description="Command to execute (will be validated for safety)",
                    required=True
                ),
                ToolParameter(
                    name="working_directory",
                    type=str,
                    description="Working directory for command execution",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="timeout",
                    type=int,
                    description="Timeout in seconds (default: 30, max: 300)",
                    required=False,
                    default=30
                )
            ],
            category="shell",
            dangerous=True
        )

    def execute(
        self,
        command: str,
        working_directory: str = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute bash command safely

        Args:
            command: Command to execute
            working_directory: Working directory
            timeout: Command timeout

        Returns:
            Dictionary with stdout, stderr, return_code

        Raises:
            ToolExecutionError: Command is dangerous or execution failed
        """
        # Validate command safety
        self._validate_command_safety(command)

        # Enforce maximum timeout
        timeout = min(timeout, 300)

        # Execute command
        result = shell.execute_command(command, working_directory, timeout)

        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode,
            'success': result.returncode == 0
        }

    def _validate_command_safety(self, command: str):
        """
        Validate command against security rules

        Args:
            command: Command string to validate

        Raises:
            ToolExecutionError: Command is deemed dangerous
        """
        from tools.tool_base import ToolExecutionError

        # Extract base command (first word)
        base_cmd = command.strip().split()[0] if command.strip() else ""

        # Check blacklist
        if base_cmd in DANGEROUS_SHELL_COMMANDS:
            raise ToolExecutionError(
                f"Command '{base_cmd}' is blacklisted for safety reasons"
            )

        # Check for dangerous patterns
        dangerous_patterns = ['rm -rf', '> /dev/', 'dd if=', 'mkfs.']
        for pattern in dangerous_patterns:
            if pattern in command:
                raise ToolExecutionError(
                    f"Command contains dangerous pattern: '{pattern}'"
                )


class GitStatusTool(Tool):
    """
    Get Git repository status

    Shows current branch, modified files, staged changes, and untracked files.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_status",
            description="Get Git repository status (branch, changes, staged files)",
            parameters=[
                ToolParameter(
                    name="repository_path",
                    type=str,
                    description="Path to Git repository (default: current directory)",
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

    def execute(
        self,
        repository_path: str = ".",
        porcelain: bool = False
    ) -> str:
        """
        Execute git status

        Args:
            repository_path: Repository path
            porcelain: Use porcelain format

        Returns:
            Git status output
        """
        return git_ops.git_status(repository_path, porcelain)


class GitDiffTool(Tool):
    """
    View Git diff of changes

    Shows differences between working directory and index (staged),
    or between index and HEAD (committed).
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_diff",
            description="View Git diff of changes (unstaged or staged)",
            parameters=[
                ToolParameter(
                    name="repository_path",
                    type=str,
                    description="Path to Git repository",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="staged",
                    type=bool,
                    description="Show staged changes (default: unstaged)",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="files",
                    type=list,
                    description="Specific files to diff (default: all files)",
                    required=False,
                    default=None
                )
            ],
            category="git"
        )

    def execute(
        self,
        repository_path: str = ".",
        staged: bool = False,
        files: List[str] = None
    ) -> str:
        """
        Execute git diff

        Args:
            repository_path: Repository path
            staged: Show staged changes
            files: Specific files

        Returns:
            Git diff output
        """
        return git_ops.git_diff(repository_path, staged, files)


class GitLogTool(Tool):
    """
    View Git commit history

    Shows recent commits with author, date, and message.
    Supports limiting number of commits and oneline format.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_log",
            description="View Git commit history",
            parameters=[
                ToolParameter(
                    name="repository_path",
                    type=str,
                    description="Path to Git repository",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="max_count",
                    type=int,
                    description="Maximum number of commits to show",
                    required=False,
                    default=10
                ),
                ToolParameter(
                    name="oneline",
                    type=bool,
                    description="Show one line per commit",
                    required=False,
                    default=False
                )
            ],
            category="git"
        )

    def execute(
        self,
        repository_path: str = ".",
        max_count: int = 10,
        oneline: bool = False
    ) -> str:
        """
        Execute git log

        Args:
            repository_path: Repository path
            max_count: Maximum commits
            oneline: Oneline format

        Returns:
            Git log output
        """
        return git_ops.git_log(repository_path, max_count, oneline)


class GitAddTool(Tool):
    """
    Stage files for commit

    Adds files to the Git staging area in preparation for commit.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_add",
            description="Stage files for commit",
            parameters=[
                ToolParameter(
                    name="files",
                    type=list,
                    description="List of file paths to stage",
                    required=True
                ),
                ToolParameter(
                    name="repository_path",
                    type=str,
                    description="Path to Git repository",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="all_files",
                    type=bool,
                    description="Stage all modified and new files",
                    required=False,
                    default=False
                )
            ],
            category="git",
            dangerous=True
        )

    def execute(
        self,
        files: List[str],
        repository_path: str = ".",
        all_files: bool = False
    ) -> bool:
        """
        Execute git add

        Args:
            files: Files to stage
            repository_path: Repository path
            all_files: Stage all files

        Returns:
            True if successful
        """
        return git_ops.git_add(files, repository_path, all_files)


class GitCommitTool(Tool):
    """
    Create Git commit

    Creates a new commit with the given message for all staged changes.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_commit",
            description="Create Git commit with staged changes",
            parameters=[
                ToolParameter(
                    name="message",
                    type=str,
                    description="Commit message",
                    required=True
                ),
                ToolParameter(
                    name="repository_path",
                    type=str,
                    description="Path to Git repository",
                    required=False,
                    default="."
                )
            ],
            category="git",
            dangerous=True
        )

    def execute(
        self,
        message: str,
        repository_path: str = "."
    ) -> str:
        """
        Execute git commit

        Args:
            message: Commit message
            repository_path: Repository path

        Returns:
            Commit result message
        """
        return git_ops.git_commit(message, repository_path)


class GitCheckoutTool(Tool):
    """Tool for managing branches"""
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_checkout",
            description="Switch branch or create new one",
            parameters=[
                ToolParameter(name="branch_name", type=str, description="Name of the branch", required=True),
                ToolParameter(name="create_new", type=bool, description="Create new branch (-b)", default=False),
                ToolParameter(name="path", type=str, description="Repo path", default=".")
            ],
            category="git",
            dangerous=True
        )

    def execute(self, branch_name: str, create_new: bool = False, path: str = ".") -> str:
        return git_ops.git_checkout(branch_name, create_new, path)
