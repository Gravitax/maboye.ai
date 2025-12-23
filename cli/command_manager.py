"""
Command Manager

Handles command registration, execution, and management for the CLI.
"""

import sys
import shlex
from typing import Optional, Callable, Dict, Tuple

from core.logger import logger
from cli.cli_utils import Color, Cursor
from cli.commands import get_all_commands


class CommandManager:
    """
    Manages CLI commands including registration and execution.

    Handles both built-in commands (help, exit, clear) and external
    commands loaded from the commands module.
    """

    def __init__(self, orchestrator=None, terminal=None):
        """
        Initialize command manager.

        Args:
            orchestrator: Orchestrator instance for external commands.
            terminal: Terminal instance for output operations.
        """
        self._commands: Dict[str, Dict] = {}
        self._orchestrator = orchestrator
        self._terminal = terminal
        self._running = True

        self._setup_built_in_commands()

        if orchestrator:
            self._load_external_commands()

    def _setup_built_in_commands(self) -> None:
        """Setup built-in commands."""
        self._register_command("help", self._execute_help, "Show available commands")
        self._register_command("exit", self._execute_exit, "Exit the application")
        self._register_command("quit", self._execute_exit, "Exit the application")
        self._register_command("clear", self._execute_clear, "Clear the screen")

    def _load_external_commands(self) -> None:
        """Load all commands from cli/commands module."""
        commands = get_all_commands()

        for cmd_name, (handler, description) in commands.items():
            self._configure_command_handler(handler)
            self._register_command(cmd_name, handler, description)

    def _configure_command_handler(self, handler: Callable) -> None:
        """
        Configure handler with orchestrator if needed.

        Args:
            handler: Command handler function.
        """
        if hasattr(handler, '__self__'):
            handler.__self__.set_orchestrator(self._orchestrator)

    def _register_command(
        self,
        name: str,
        handler: Callable,
        description: str = ""
    ) -> None:
        """
        Register a command handler.

        Args:
            name: Command name (without /).
            handler: Function to call when command is entered.
            description: Help text for command.
        """
        self._commands[name] = {
            "handler": handler,
            "description": description
        }

    def register_command(
        self,
        name: str,
        handler: Callable,
        description: str = ""
    ) -> None:
        """
        Public method to register a command.

        Args:
            name: Command name (without /).
            handler: Function to call when command is entered.
            description: Help text for command.
        """
        self._register_command(name, handler, description)

    def get_all_commands(self) -> Dict[str, Dict]:
        """
        Get all registered commands.

        Returns:
            Dictionary of command names to command data.
        """
        return self._commands.copy()

    def has_command(self, name: str) -> bool:
        """
        Check if a command exists.

        Args:
            name: Command name to check.

        Returns:
            True if command exists, False otherwise.
        """
        return name in self._commands

    def parse_command(self, user_input: str) -> Optional[Tuple[str, list]]:
        """
        Parse command from user input.

        Args:
            user_input: Raw user input string.

        Returns:
            Tuple of (command_name, args) or None if not a command.
        """
        if not self._is_command_input(user_input):
            return None

        try:
            # Use shlex to handle quoted arguments correctly
            parts = shlex.split(user_input[1:])
        except ValueError as e:
            if self._terminal:
                self._terminal.print_message(
                    f"Error parsing command: {e}",
                    color=Color.RED
                )
            return None

        if not parts:
            return None
            
        cmd_name = parts[0].lower()
        args = parts[1:]

        return (cmd_name, args)

    def _is_command_input(self, user_input: str) -> bool:
        """
        Check if input is a command.

        Args:
            user_input: User input string.

        Returns:
            True if input starts with /, False otherwise.
        """
        return user_input.startswith("/")

    def execute_command(self, cmd_name: str, args: list) -> bool:
        """
        Execute a registered command.

        Args:
            cmd_name: Name of the command to execute.
            args: Arguments to pass to the command.

        Returns:
            True to continue running, False to stop.
        """
        if not self.has_command(cmd_name):
            self._handle_unknown_command(cmd_name)
            return True

        continue_running = self._commands[cmd_name]["handler"](args)

        if not continue_running:
            self._running = False

        return continue_running

    def _handle_unknown_command(self, cmd_name: str) -> None:
        """
        Handle unknown command error.

        Args:
            cmd_name: The unknown command name.
        """
        if self._terminal:
            self._terminal.print_message(
                f"Unknown command: /{cmd_name}",
                color=Color.RED,
                style=Color.BOLD
            )
            self._terminal.print_message(
                "Type /help for available commands",
                color=Color.YELLOW
            )

    def is_running(self) -> bool:
        """
        Check if command manager is running.

        Returns:
            True if running, False otherwise.
        """
        return self._running

    def stop(self) -> None:
        """Stop the command manager."""
        self._running = False

    def _execute_help(self, args: list) -> bool:
        """
        Execute help command.

        Args:
            args: Command arguments (unused).

        Returns:
            True to continue running.
        """
        if not self._terminal:
            return True

        self._print_help_header()
        self._print_command_list()
        self._print_help_footer()

        return True

    def _print_help_header(self) -> None:
        """Print help command header."""
        if self._terminal:
            self._terminal.print_message("\nAvailable commands:", style=Color.BOLD)
            self._terminal.print_message("-" * 60)

    def _print_command_list(self) -> None:
        """Print list of all commands."""
        if not self._terminal:
            return

        for name, cmd in sorted(self._commands.items()):
            desc = cmd["description"] or "No description"
            self._terminal.print_message(f"  /{name:<15} {desc}")

    def _print_help_footer(self) -> None:
        """Print help command footer."""
        if self._terminal:
            self._terminal.print_message("-" * 60)
            self._terminal.print_message("")

    def _execute_exit(self, args: list) -> bool:
        """
        Execute exit command.

        Args:
            args: Command arguments (unused).

        Returns:
            False to stop running.
        """
        if self._terminal:
            self._terminal.print_message("\nExiting...", color=Color.YELLOW)

        return False

    def _execute_clear(self, args: list) -> bool:
        """
        Execute clear command.

        Args:
            args: Command arguments (unused).

        Returns:
            True to continue running.
        """
        sys.stdout.write(Cursor.ERASE_DISPLAY)
        sys.stdout.flush()
        return True
