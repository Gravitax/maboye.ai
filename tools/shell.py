"""
Shell command execution for agent system

Provides safe command execution with timeout, output capture, and process management.
"""

from pathlib import Path
import subprocess
import os
from typing import Optional, Dict, Any, List
import time

from core.logger import logger


class ShellError(Exception):
    """Base exception for shell errors"""
    pass


class CommandTimeoutError(ShellError):
    """Command execution timeout"""
    pass


class CommandExecutionError(ShellError):
    """Command execution failed"""
    pass


class ShellResult:
    """Result of shell command execution"""

    def __init__(
        self,
        command: str,
        returncode: int,
        stdout: str,
        stderr: str,
        execution_time: float
    ):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.success = returncode == 0

    def __repr__(self):
        return (
            f"ShellResult(command={self.command!r}, "
            f"returncode={self.returncode}, "
            f"success={self.success})"
        )


def execute_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: Optional[int] = 120,
    env: Optional[Dict[str, str]] = None,
    shell: bool = True,
    capture_output: bool = True
) -> ShellResult:
    """
    Execute shell command

    Args:
        command: Command to execute
        cwd: Working directory (defaults to current)
        timeout: Timeout in seconds (None for no timeout)
        env: Environment variables (merges with current env)
        shell: Execute through shell
        capture_output: Capture stdout/stderr

    Returns:
        ShellResult with command output and status

    Raises:
        CommandTimeoutError: Command exceeded timeout
        CommandExecutionError: Command failed to execute
    """
    start_time = time.time()

    # Prepare environment
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)

    # Prepare working directory
    work_dir = Path(cwd).resolve() if cwd else Path.cwd()
    if not work_dir.exists():
        logger.error("SHELL", "Working directory not found", {
            "path": str(work_dir)
        })
        raise ShellError(f"Working directory not found: {cwd}")

    logger.info("SHELL", "Executing command", {
        "command": command,
        "cwd": str(work_dir),
        "timeout": timeout
    })

    try:
        # Execute command
        process = subprocess.Popen(
            command,
            shell=shell,
            cwd=str(work_dir),
            env=cmd_env,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True
        )

        # Wait for completion with timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Kill process on timeout
            process.kill()
            process.wait()
            execution_time = time.time() - start_time

            logger.error("SHELL", "Command timeout", {
                "command": command,
                "timeout": timeout,
                "execution_time": execution_time
            })

            raise CommandTimeoutError(
                f"Command exceeded timeout of {timeout}s: {command}"
            )

        execution_time = time.time() - start_time

        # Create result
        result = ShellResult(
            command=command,
            returncode=process.returncode,
            stdout=stdout or "",
            stderr=stderr or "",
            execution_time=execution_time
        )

        if result.success:
            logger.info("SHELL", "Command completed", {
                "command": command,
                "returncode": result.returncode,
                "execution_time": execution_time
            })
        else:
            logger.warning("SHELL", "Command failed", {
                "command": command,
                "returncode": result.returncode,
                "stderr": result.stderr[:200],
                "execution_time": execution_time
            })

        return result

    except CommandTimeoutError:
        # Re-raise timeout errors without wrapping
        raise

    except FileNotFoundError as e:
        logger.error("SHELL", "Command not found", {
            "command": command,
            "error": str(e)
        })
        raise CommandExecutionError(f"Command not found: {command}")

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error("SHELL", "Command execution failed", {
            "command": command,
            "error": str(e),
            "execution_time": execution_time
        })
        raise CommandExecutionError(f"Failed to execute command: {e}")


def run_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: Optional[int] = 120,
    env: Optional[Dict[str, str]] = None,
    check: bool = False
) -> ShellResult:
    """
    Run command and return result

    Args:
        command: Command to execute
        cwd: Working directory
        timeout: Timeout in seconds
        env: Environment variables
        check: Raise error if command fails

    Returns:
        ShellResult

    Raises:
        CommandExecutionError: If check=True and command fails
    """
    result = execute_command(
        command=command,
        cwd=cwd,
        timeout=timeout,
        env=env
    )

    if check and not result.success:
        raise CommandExecutionError(
            f"Command failed with code {result.returncode}: {command}\n"
            f"stderr: {result.stderr}"
        )

    return result


def run_commands(
    commands: List[str],
    cwd: Optional[str] = None,
    timeout: Optional[int] = 120,
    env: Optional[Dict[str, str]] = None,
    stop_on_error: bool = True
) -> List[ShellResult]:
    """
    Run multiple commands sequentially

    Args:
        commands: List of commands to execute
        cwd: Working directory
        timeout: Timeout per command
        env: Environment variables
        stop_on_error: Stop execution if a command fails

    Returns:
        List of ShellResult objects
    """
    results = []

    for command in commands:
        result = execute_command(
            command=command,
            cwd=cwd,
            timeout=timeout,
            env=env
        )
        results.append(result)

        if stop_on_error and not result.success:
            logger.warning("SHELL", "Stopping command sequence on error", {
                "command": command,
                "returncode": result.returncode
            })
            break

    return results


class BackgroundProcess:
    """Manage background process execution"""

    def __init__(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ):
        self.command = command
        self.cwd = cwd
        self.env = env
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[float] = None

    def start(self) -> bool:
        """
        Start background process

        Returns:
            True if started successfully
        """
        if self.process is not None:
            logger.warning("SHELL", "Process already running", {
                "command": self.command
            })
            return False

        # Prepare environment
        cmd_env = os.environ.copy()
        if self.env:
            cmd_env.update(self.env)

        # Prepare working directory
        work_dir = Path(self.cwd).resolve() if self.cwd else Path.cwd()

        try:
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                cwd=str(work_dir),
                env=cmd_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.start_time = time.time()

            logger.info("SHELL", "Background process started", {
                "command": self.command,
                "pid": self.process.pid
            })

            return True

        except Exception as e:
            logger.error("SHELL", "Failed to start background process", {
                "command": self.command,
                "error": str(e)
            })
            return False

    def is_running(self) -> bool:
        """Check if process is still running"""
        if self.process is None:
            return False
        return self.process.poll() is None

    def get_status(self) -> Dict[str, Any]:
        """
        Get process status

        Returns:
            Dictionary with process information
        """
        if self.process is None:
            return {
                "running": False,
                "pid": None,
                "returncode": None,
                "runtime": 0
            }

        runtime = time.time() - self.start_time if self.start_time else 0

        return {
            "running": self.is_running(),
            "pid": self.process.pid,
            "returncode": self.process.returncode,
            "runtime": runtime
        }

    def get_output(self, timeout: Optional[float] = None) -> ShellResult:
        """
        Get process output (waits for completion)

        Args:
            timeout: Wait timeout in seconds

        Returns:
            ShellResult with output
        """
        if self.process is None:
            raise ShellError("Process not started")

        try:
            stdout, stderr = self.process.communicate(timeout=timeout)
            execution_time = time.time() - self.start_time if self.start_time else 0

            result = ShellResult(
                command=self.command,
                returncode=self.process.returncode,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time
            )

            logger.info("SHELL", "Background process completed", {
                "command": self.command,
                "returncode": result.returncode,
                "execution_time": execution_time
            })

            return result

        except subprocess.TimeoutExpired:
            raise CommandTimeoutError(f"Process output timeout: {self.command}")

    def kill(self) -> bool:
        """
        Kill background process

        Returns:
            True if killed successfully
        """
        if self.process is None or not self.is_running():
            return False

        try:
            self.process.kill()
            self.process.wait(timeout=5)

            logger.info("SHELL", "Background process killed", {
                "command": self.command,
                "pid": self.process.pid
            })

            return True

        except Exception as e:
            logger.error("SHELL", "Failed to kill process", {
                "command": self.command,
                "pid": self.process.pid,
                "error": str(e)
            })
            return False

    def terminate(self) -> bool:
        """
        Gracefully terminate process

        Returns:
            True if terminated successfully
        """
        if self.process is None or not self.is_running():
            return False

        try:
            self.process.terminate()
            self.process.wait(timeout=5)

            logger.info("SHELL", "Background process terminated", {
                "command": self.command,
                "pid": self.process.pid
            })

            return True

        except subprocess.TimeoutExpired:
            # Force kill if graceful termination fails
            return self.kill()
        except Exception as e:
            logger.error("SHELL", "Failed to terminate process", {
                "command": self.command,
                "pid": self.process.pid,
                "error": str(e)
            })
            return False
