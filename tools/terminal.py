"""
Interactive terminal for agent system

Provides command-line interface with command handling and input loop.
"""

import sys
from pathlib import Path
from typing import Optional, Callable, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.logger import logger


class Terminal:
    """
    Interactive terminal with command handling

    Provides continuous input loop, command parsing, and help system.
    """

    def __init__(self, prompt: str = "> "):
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
        print("\nAvailable commands:")
        print("-" * 60)

        for name, cmd in sorted(self.commands.items()):
            desc = cmd["description"] or "No description"
            print(f"  /{name:<15} {desc}")

        print("-" * 60)
        print()
        return True

    def _cmd_exit(self, args: list) -> bool:
        """
        Exit the terminal

        Args:
            args: Command arguments (unused)

        Returns:
            False to stop running
        """
        print("\nExiting...")
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
        import os
        os.system('clear' if os.name == 'posix' else 'cls')
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
                print(f"Unknown command: /{cmd_name}")
                print("Type /help for available commands")
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
            print()
            logger.info("TERMINAL", "Interrupted by user")
            return None

    def print(self, message: str):
        """
        Print message to terminal

        Args:
            message: Message to print
        """
        print(message)

    def print_header(self, title: str):
        """
        Print formatted header

        Args:
            title: Header title
        """
        width = 60
        print()
        print("=" * width)
        print(f" {title}")
        print("=" * width)
        print()

    def print_separator(self):
        """Print separator line"""
        print("-" * 60)

    def run(self, input_handler: Optional[Callable[[str], None]] = None):
        """
        Start interactive input loop

        Args:
            input_handler: Function to call with non-command input
        """
        self.running = True

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
                    print(f"Error: {e}")

        logger.info("TERMINAL", "Interactive loop stopped")

    def stop(self):
        """Stop the interactive loop"""
        self.running = False
