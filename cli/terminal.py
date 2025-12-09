"""
Interactive terminal for agent system

Provides command-line interface with command handling and input loop.
"""

import sys
from typing import Optional, Callable, Dict

from core.logger import logger

from cli.cli_utils import Color, Cursor, _print_formatted_message


class Terminal:
    """
    Interactive terminal with command handling

    Provides continuous input loop, command parsing, and help system.
    """

    def __init__(self, prompt: str = f"{Color.BLUE}{Color.BOLD}You:{Color.RESET} > "):
        """
        Initialize terminal

        Args:
            prompt: Prompt string to display
        """
        self.prompt = prompt
        self.commands: Dict[str, Callable] = {}
        self.running = False
        self._setup_default_commands()

        logger.info("TERMINAL", "Terminal initialized")

    def _print_message(
        self,
        message: str,
        prefix: str = "",
        color: str = "",
        style: str = "",
        stream=sys.stdout,
        end: str = "\n"
    ):
        """
        Unified method to print messages to the terminal, using formatted output.
        """
        _print_formatted_message(message, prefix, color, style, stream, end)

    def _display_ascii_title(self):
        """
        Displays an ASCII art title for the Gemini CLI.
        """
        ascii_art = rf"""
{Color.BRIGHT_MAGENTA}              ___.                               _____  .___{Color.RESET}
{Color.MAGENTA}  _____ _____ \_ |__   ____ ___.__. ____        /  _  \ |   |{Color.RESET}
{Color.BRIGHT_BLUE} /     \\__  \ | __ \ /  _ <   |  |/ __ \      /  /_\  \|   |{Color.RESET}
{Color.BLUE}|  Y Y  \/ __ \| \_\ (  <_> )___  \  ___/     /    |    \   |{Color.RESET}
{Color.BRIGHT_CYAN}|__|_|  (____  /___  /\____// ____|\___  > /\ \____|__  /___|{Color.RESET}
{Color.CYAN}      \/     \/    \/       \/         \/  \/         \/{Color.RESET}
"""
        self._print_message(ascii_art, style=Color.BOLD)
        self._print_message("Welcome to maboye.AI CLI!", color=Color.CYAN, style=Color.BOLD)
        self._print_message("Type /help for available commands.", color=Color.YELLOW)
        self._print_message("")

    def _setup_default_commands(self):
        """Setup default built-in commands"""
        self.register_command("help", self._cmd_help, "Show available commands")
        self.register_command("exit", self._cmd_exit, "Exit the application")
        self.register_command("quit", self._cmd_exit, "Exit the application")
        self.register_command("clear", self._cmd_clear, "Clear the screen")

    def register_command(
        self,
        name: str,
        handler: Callable,
        description: str = ""
    ):
        """
        Register command handler

        Args:
            name: Command name (without /)
            handler: Function to call when command is entered
            description: Help text for command
        """
        self.commands[name] = {
            "handler": handler,
            "description": description
        }

        logger.debug("TERMINAL", f"Registered command: /{name}")

    def _cmd_help(self, args: list) -> bool:
        """
        Show help for available commands

        Args:
            args: Command arguments (unused)

        Returns:
            True to continue running
        """
        self._print_message("\nAvailable commands:", style=Color.BOLD)
        self._print_message("-" * 60)

        for name, cmd in sorted(self.commands.items()):
            desc = cmd["description"] or "No description"
            self._print_message(f"  /{name:<15} {desc}")

        self._print_message("-" * 60)
        self._print_message("")
        return True

    def _cmd_exit(self, args: list) -> bool:
        """
        Exit the terminal

        Args:
            args: Command arguments (unused)

        Returns:
            False to stop running
        """
        self._print_message("\nExiting...", color=Color.YELLOW)
        logger.info("TERMINAL", "Exit command received")
        return False

    def _cmd_clear(self, args: list) -> bool:
        """
        Clear the terminal screen

        Args:
            args: Command arguments (unused)

        Returns:
            True to continue running
        """
        sys.stdout.write(Cursor.ERASE_DISPLAY)
        sys.stdout.flush()
        return True

    def process_input(self, user_input: str) -> Optional[str]:
        """
        Process user input and handle commands

        Args:
            user_input: Raw input from user

        Returns:
            Processed input (None if command was handled)
        """
        user_input = user_input.strip()

        if not user_input:
            return None

        # Check if input is a command
        if user_input.startswith("/"):
            parts = user_input[1:].split()
            cmd_name = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd_name in self.commands:
                logger.debug("TERMINAL", f"Executing command: /{cmd_name}")

                # Execute command
                continue_running = self.commands[cmd_name]["handler"](args)

                # Stop running if command returns False
                if not continue_running:
                    self.running = False

                return None
            else:
                self._print_message(
                    f"Unknown command: /{cmd_name}", color=Color.RED, style=Color.BOLD
                )
                self._print_message(
                    "Type /help for available commands", color=Color.YELLOW
                )
                return None

        # Regular input (not a command)
        return user_input

    def read_input(self) -> Optional[str]:
        """
        Read line from standard input

        Returns:
            Input line or None on EOF/error
        """
        try:
            return input(self.prompt)
        except EOFError:
            logger.info("TERMINAL", "EOF received")
            return None
        except KeyboardInterrupt:
            self._print_message("", end="")
            logger.info("TERMINAL", "Interrupted by user")
            return None

    def run(self, input_handler: Optional[Callable[[str], None]] = None):
        """
        Start interactive input loop

        Args:
            input_handler: Function to call with non-command input
        """
        self.running = True

        self._display_ascii_title()
        logger.info("TERMINAL", "Starting interactive loop")

        while self.running:
            user_input = self.read_input()

            if user_input is None:
                break

            processed = self.process_input(user_input)

            if processed and input_handler:
                try:
                    input_handler(processed)
                except Exception as e:
                    logger.error("TERMINAL", "Input handler error", {
                        "error": str(e)
                    })
                    self._print_message(f"Error: {e}", color=Color.RED, style=Color.BOLD)

        logger.info("TERMINAL", "Interactive loop stopped")

    def stop(self):
        """Stop the interactive loop"""
        self.running = False
