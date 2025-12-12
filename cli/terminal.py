"""
Interactive terminal for agent system

Provides command-line interface with input loop and display functionality.
"""

import sys
from typing import Optional, Callable

from core.logger import logger
from cli.cli_utils import Color, _print_formatted_message
from cli.command_manager import CommandManager


class Terminal:
    """
    Interactive terminal for user input and output.

    Provides continuous input loop, display functionality, and
    delegates command handling to CommandManager.
    """

    def __init__(
        self,
        orchestrator=None,
        prompt: str = f"{Color.BLUE}{Color.BOLD}You:{Color.RESET} > "
    ):
        """
        Initialize terminal.

        Args:
            orchestrator: Orchestrator instance for commands.
            prompt: Prompt string to display.
        """
        self.prompt = prompt
        self.running = False
        self._orchestrator = orchestrator
        self._command_manager = CommandManager(orchestrator=orchestrator, terminal=self)

        logger.info("TERMINAL", "Terminal initialized")

    def print_message(
        self,
        message: str,
        prefix: str = "",
        color: str = "",
        style: str = "",
        stream=sys.stdout,
        end: str = "\n"
    ) -> None:
        """
        Print formatted message to the terminal.

        Args:
            message: Message text to display.
            prefix: Optional prefix string.
            color: Color code for the message.
            style: Style code for the message.
            stream: Output stream to write to.
            end: String appended after the message.
        """
        _print_formatted_message(message, prefix, color, style, stream, end)

    def _display_ascii_title(self) -> None:
        """Display ASCII art title for the CLI."""
        ascii_art = rf"""
{Color.BRIGHT_MAGENTA}              ___.                               _____  .___{Color.RESET}
{Color.MAGENTA}  _____ _____ \_ |__   ____ ___.__. ____        /  _  \ |   |{Color.RESET}
{Color.BRIGHT_BLUE} /     \\__  \ | __ \ /  _ <   |  |/ __ \      /  /_\  \|   |{Color.RESET}
{Color.BLUE}|  Y Y  \/ __ \| \_\ (  <_> )___  \  ___/     /    |    \   |{Color.RESET}
{Color.BRIGHT_CYAN}|__|_|  (____  /___  /\____// ____|\___  > /\ \____|__  /___|{Color.RESET}
{Color.CYAN}      \/     \/    \/       \/         \/  \/         \/{Color.RESET}
"""
        self.print_message(ascii_art, style=Color.BOLD)
        self.print_message("Welcome to maboye.AI CLI!", color=Color.CYAN, style=Color.BOLD)
        self.print_message("Type /help for available commands.", color=Color.YELLOW)
        self.print_message("")

    def register_command(
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
        self._command_manager.register_command(name, handler, description)

    def process_input(self, user_input: str) -> Optional[str]:
        """
        Process user input and handle commands.

        Args:
            user_input: Raw input from user.

        Returns:
            Processed input (None if command was handled).
        """
        user_input = self._sanitize_input(user_input)

        if not user_input:
            return None

        command_data = self._command_manager.parse_command(user_input)

        if command_data:
            self._execute_parsed_command(command_data)
            return None

        return user_input

    def _sanitize_input(self, user_input: str) -> str:
        """
        Sanitize user input.

        Args:
            user_input: Raw user input.

        Returns:
            Sanitized input string.
        """
        return user_input.strip()

    def _execute_parsed_command(self, command_data: tuple) -> None:
        """
        Execute a parsed command.

        Args:
            command_data: Tuple of (command_name, args).
        """
        cmd_name, args = command_data
        continue_running = self._command_manager.execute_command(cmd_name, args)

        if not continue_running:
            self.running = False

    def read_input(self) -> Optional[str]:
        """
        Read line from standard input.

        Returns:
            Input line or None on EOF/error.
        """
        try:
            return input(self.prompt)
        except EOFError:
            return self._handle_eof()
        except KeyboardInterrupt:
            return self._handle_keyboard_interrupt()

    def _handle_eof(self) -> None:
        """
        Handle EOF signal.

        Returns:
            None to signal end of input.
        """
        logger.info("TERMINAL", "EOF received")
        return None

    def _handle_keyboard_interrupt(self) -> None:
        """
        Handle keyboard interrupt signal.

        Returns:
            None to signal interrupted input.
        """
        self.print_message("", end="")
        logger.info("TERMINAL", "Interrupted by user")
        return None

    def run(self, input_handler: Optional[Callable[[str], None]] = None) -> None:
        """
        Start interactive input loop.

        Args:
            input_handler: Function to call with non-command input.
        """
        self._initialize_loop()
        self._display_ascii_title()
        self._execute_input_loop(input_handler)
        self._finalize_loop()

    def _initialize_loop(self) -> None:
        """Initialize the input loop."""
        self.running = True

    def _execute_input_loop(self, input_handler: Optional[Callable[[str], None]]) -> None:
        """
        Execute the main input loop.

        Args:
            input_handler: Function to call with non-command input.
        """
        while self.running:
            user_input = self.read_input()

            if user_input is None:
                break

            processed = self.process_input(user_input)

            if processed and input_handler:
                self._handle_user_input(processed, input_handler)

    def _handle_user_input(
        self,
        processed_input: str,
        input_handler: Callable[[str], None]
    ) -> None:
        """
        Handle processed user input with the handler.

        Args:
            processed_input: The processed input string.
            input_handler: Function to call with the input.
        """
        try:
            input_handler(processed_input)
        except Exception as e:
            self._handle_input_error(e)

    def _handle_input_error(self, error: Exception) -> None:
        """
        Handle error from input handler.

        Args:
            error: The exception that occurred.
        """
        logger.error("TERMINAL", "Input handler error", {"error": str(error)})
        self.print_message(f"Error: {error}", color=Color.RED, style=Color.BOLD)

    def _finalize_loop(self) -> None:
        """Finalize the input loop."""
        logger.info("TERMINAL", "Interactive loop stopped")

    def stop(self) -> None:
        """Stop the interactive loop."""
        self.running = False
        self._command_manager.stop()
