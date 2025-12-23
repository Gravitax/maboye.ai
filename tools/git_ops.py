"""
Git operations for agent system

Provides Git repository operations built on shell execution.
"""

from typing import Optional, List

from tools.shell import run_command, CommandExecutionError
from core.logger import logger


class GitError(Exception):
    """Base exception for Git errors"""
    pass


class GitNotRepositoryError(GitError):
    """Not a Git repository"""
    pass


class GitOperationError(GitError):
    """Git operation failed"""
    pass


def is_git_repository(path: str = ".") -> bool:
    """
    Check if directory is a Git repository

    Args:
        path: Directory to check

    Returns:
        True if Git repository
    """
    try:
        result = run_command(
            "git rev-parse --is-inside-work-tree",
            cwd=path,
            timeout=5
        )
        return result.success and result.stdout.strip() == "true"
    except Exception:
        return False


def git_init(path: str = ".") -> bool:
    """
    Initialize Git repository

    Args:
        path: Directory to initialize

    Returns:
        True if initialized

    Raises:
        GitOperationError: Init failed
    """
    try:
        result = run_command("git init", cwd=path, check=True)
        return True

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to initialize repository: {e}")


def git_status(path: str = ".", porcelain: bool = False) -> str:
    """
    Get Git status

    Args:
        path: Repository path
        porcelain: Use machine-readable format

    Returns:
        Status output

    Raises:
        GitNotRepositoryError: Not a Git repository
        GitOperationError: Status failed
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        cmd = "git status --porcelain" if porcelain else "git status"
        result = run_command(cmd, cwd=path, check=True)
        return result.stdout

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to get status: {e}")


def git_add(
    files: List[str],
    path: str = ".",
    all_files: bool = False
) -> bool:
    """
    Stage files for commit

    Args:
        files: List of files to add
        path: Repository path
        all_files: Add all files (ignores files list)

    Returns:
        True if staged

    Raises:
        GitNotRepositoryError: Not a Git repository
        GitOperationError: Add failed
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        if all_files:
            cmd = "git add -A"
        else:
            # Quote filenames for safety
            file_args = " ".join(f"'{f}'" for f in files)
            cmd = f"git add {file_args}"

        result = run_command(cmd, cwd=path, check=True)
        return True

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to stage files: {e}")


def git_commit(
    message: str,
    path: str = ".",
    author: Optional[str] = None
) -> str:
    """
    Create commit

    Args:
        message: Commit message
        path: Repository path
        author: Author string (format: "Name <email>")

    Returns:
        Commit hash

    Raises:
        GitNotRepositoryError: Not a Git repository
        GitOperationError: Commit failed
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        # Escape message for shell
        escaped_msg = message.replace("'", "'\\''")
        cmd = f"git commit -m '{escaped_msg}'"

        if author:
            escaped_author = author.replace("'", "'\\''")
            cmd += f" --author '{escaped_author}'"

        result = run_command(cmd, cwd=path, check=True)

        # Extract commit hash
        hash_result = run_command("git rev-parse HEAD", cwd=path, check=True)
        commit_hash = hash_result.stdout.strip()
        return commit_hash

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to create commit: {e}")


def git_diff(
    path: str = ".",
    staged: bool = False,
    files: Optional[List[str]] = None
) -> str:
    """
    Get diff

    Args:
        path: Repository path
        staged: Show staged changes
        files: Specific files to diff

    Returns:
        Diff output

    Raises:
        GitNotRepositoryError: Not a Git repository
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        cmd = "git diff --cached" if staged else "git diff"

        if files:
            file_args = " ".join(f"'{f}'" for f in files)
            cmd += f" -- {file_args}"

        result = run_command(cmd, cwd=path, check=True)
        return result.stdout

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to get diff: {e}")


def git_log(
    path: str = ".",
    max_count: int = 10,
    oneline: bool = False
) -> str:
    """
    Get commit log

    Args:
        path: Repository path
        max_count: Maximum commits to show
        oneline: One line per commit

    Returns:
        Log output

    Raises:
        GitNotRepositoryError: Not a Git repository
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        cmd = f"git log -n {max_count}"
        if oneline:
            cmd += " --oneline"

        result = run_command(cmd, cwd=path, check=True)
        return result.stdout

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to get log: {e}")


def git_branch(
    path: str = ".",
    list_all: bool = False
) -> List[str]:
    """
    List branches

    Args:
        path: Repository path
        list_all: Include remote branches

    Returns:
        List of branch names

    Raises:
        GitNotRepositoryError: Not a Git repository
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        cmd = "git branch -a" if list_all else "git branch"
        result = run_command(cmd, cwd=path, check=True)

        # Parse branch list
        branches = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line:
                # Remove current branch marker (*)
                if line.startswith("* "):
                    line = line[2:]
                branches.append(line)
        return branches

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to list branches: {e}")


def git_checkout(
    branch: str,
    path: str = ".",
    create: bool = False
) -> str:
    """
    Checkout branch

    Args:
        branch: Branch name
        path: Repository path
        create: Create new branch

    Returns:
        Output message

    Raises:
        GitNotRepositoryError: Not a Git repository
        GitOperationError: Checkout failed
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        cmd = f"git checkout {'-b ' if create else ''}'{branch}'"
        result = run_command(cmd, cwd=path, check=True)
        return result.stdout or result.stderr or f"Switched to branch '{branch}'"

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to checkout branch: {e}")


def git_current_branch(path: str = ".") -> str:
    """
    Get current branch name

    Args:
        path: Repository path

    Returns:
        Current branch name

    Raises:
        GitNotRepositoryError: Not a Git repository
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        result = run_command("git branch --show-current", cwd=path, check=True)
        branch = result.stdout.strip()
        return branch

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to get current branch: {e}")


def git_pull(
    path: str = ".",
    remote: str = "origin",
    branch: Optional[str] = None
) -> bool:
    """
    Pull from remote

    Args:
        path: Repository path
        remote: Remote name
        branch: Branch name (defaults to current)

    Returns:
        True if pulled

    Raises:
        GitNotRepositoryError: Not a Git repository
        GitOperationError: Pull failed
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        cmd = f"git pull {remote}"
        if branch:
            cmd += f" {branch}"

        result = run_command(cmd, cwd=path, check=True, timeout=60)
        return True

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to pull: {e}")


def git_push(
    path: str = ".",
    remote: str = "origin",
    branch: Optional[str] = None,
    set_upstream: bool = False
) -> bool:
    """
    Push to remote

    Args:
        path: Repository path
        remote: Remote name
        branch: Branch name (defaults to current)
        set_upstream: Set upstream tracking

    Returns:
        True if pushed

    Raises:
        GitNotRepositoryError: Not a Git repository
        GitOperationError: Push failed
    """
    if not is_git_repository(path):
        raise GitNotRepositoryError(f"Not a Git repository: {path}")

    try:
        cmd = f"git push {'-u ' if set_upstream else ''}{remote}"
        if branch:
            cmd += f" {branch}"

        result = run_command(cmd, cwd=path, check=True, timeout=60)
        return True

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to push: {e}")


def git_clone(
    url: str,
    destination: str,
    branch: Optional[str] = None
) -> bool:
    """
    Clone repository

    Args:
        url: Repository URL
        destination: Destination path
        branch: Specific branch to clone

    Returns:
        True if cloned

    Raises:
        GitOperationError: Clone failed
    """
    try:
        cmd = f"git clone {url} '{destination}'"
        if branch:
            cmd += f" -b {branch}"

        result = run_command(cmd, check=True, timeout=120)
        return True

    except CommandExecutionError as e:
        raise GitOperationError(f"Failed to clone repository: {e}")
