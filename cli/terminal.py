"""
Interactive terminal for agent system

Provides command-line interface with input loop and display functionality.
"""

import sys
import os
import atexit
from typing import Optional, Callable, Iterable

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.document import Document
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.key_binding import KeyBindings

from core.logger import logger
from cli.cli_utils import Color, _print_formatted_message, format_path_with_gradient
from cli.command_manager import CommandManager
from cli.completer import CLICompleter
from cli.system_command_manager import SystemCommandManager


class MaboyeCompleter(Completer):
    """
    Adapter to connect CLICompleter with prompt_toolkit.
    """
    def __init__(self, cli_completer: CLICompleter):
        self._cli_completer = cli_completer

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """
        Get completions for the current document.
        """
        text = document.text
        word_before_cursor = document.get_word_before_cursor(WORD=True) # WORD=True for broader word definition including /
        
        matches = self._cli_completer.get_matches(text, word_before_cursor)
        
        for match in matches:
            yield Completion(match, start_position=-len(word_before_cursor))


class Terminal:
    """
    Interactive terminal for user input and output.

    Provides continuous input loop, display functionality, and
    delegates command handling to CommandManager.
    """

    def __init__(
        self,
        orchestrator=None,
    ):
        """
        Initialize terminal.

        Args:
            orchestrator: Orchestrator instance for commands.
        """
        self.running = False
        self._orchestrator = orchestrator
        self._command_manager = CommandManager(orchestrator=orchestrator, terminal=self)
        self._system_command_manager = SystemCommandManager()
        
        # Setup key bindings
        self._bindings = KeyBindings()
        
        @self._bindings.add('c-c')
        def _(event):
            "Pressing Ctrl-C will exit the application if buffer is empty, else clear buffer."
            buff = event.current_buffer
            if buff.text:
                buff.reset()
            else:
                event.app.exit(exception=KeyboardInterrupt, style='class:aborting')

        @self._bindings.add('c-j')
        def _(event):
            "Insert a newline."
            event.current_buffer.insert_text('\n')

        @self._bindings.add('enter')
        def _(event):
            "Accept input."
            event.current_buffer.validate_and_handle()

        # Setup prompt_toolkit session
        histfile = os.path.join(os.path.expanduser("~"), ".maboye_ai_history")
        self._completer = CLICompleter(
            self._command_manager.get_all_commands,
            self._system_command_manager
        )
        self._pt_completer = MaboyeCompleter(self._completer)
        
        self._session = PromptSession(
            history=FileHistory(histfile),
            completer=self._pt_completer,
            complete_while_typing=False, # Less distracting, matches readline behavior somewhat
            color_depth=ColorDepth.DEPTH_24_BIT, # Force 24-bit colors (True Color)
            key_bindings=self._bindings,
            multiline=True # Enable multi-line input
        )

    @property
    def prompt(self) -> str:
        """Dynamically generate the prompt string based on the current working directory."""
        current_dir = os.getcwd()
        home_dir = os.path.expanduser("~")

        # Shorten path if it's within the home directory
        if current_dir.startswith(home_dir):
            display_dir = "~" + current_dir[len(home_dir):]
            if display_dir == "~": # If current_dir is exactly home_dir
                display_dir = "~/"
        else:
            display_dir = current_dir
            
        colored_path = format_path_with_gradient(display_dir)

        # Return raw ANSI string, prompt_toolkit handles it with ANSI() wrapper
        return f"{Color.BOLD}{colored_path}{Color.RESET} > "

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

        # 1. Internal Command (/command)
        command_data = self._command_manager.parse_command(user_input)
        if command_data:
            self._execute_parsed_command(command_data)
            return None

        # 2. System Command (ls, cd, etc.)
        if self._system_command_manager.is_system_command(user_input):
            self._system_command_manager.execute(user_input)
            return None

        # 3. Agent Input
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
        Read line from standard input using prompt_toolkit.

        Returns:
            Input line or None on EOF/error.
        """
        try:
            return self._session.prompt(ANSI(self.prompt))
        except EOFError:
            return self._handle_eof()
        except KeyboardInterrupt:
            # Custom key bindings raise this only on empty buffer -> Exit
            self.print_message("\nExiting...", color=Color.YELLOW)
            sys.exit(0)

    def _handle_eof(self) -> None:
        """
        Handle EOF signal.

        Returns:
            None to signal end of input.
        """
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
                # EOF reached
                break
                
            if not user_input:
                # Empty input (e.g. Enter or Ctrl+C handled via bindings)
                continue

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
        except KeyboardInterrupt:
            self.print_message("\nOrchestrator loop interrupted.", color=Color.YELLOW)
        except Exception as e:
            self._handle_input_error(e)

    def _handle_input_error(self, error: Exception) -> None:
        """
        Handle error from input handler.

        Args:
            error: The exception that occurred.
        """
        self.print_message(f"Error: {error}", color=Color.RED, style=Color.BOLD)

    def stop(self) -> None:
        """Stop the interactive loop."""
        self.running = False
        self._command_manager.stop()