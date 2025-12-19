"""
System Command Manager

Handles execution of system shell commands (binaries) and shell builtins (cd)
directly from the CLI prompt.
"""

import os
import shutil
import subprocess
import shlex
from typing import List
from cli.cli_utils import Color, _print_formatted_message

class SystemCommandManager:
    """
    Manages detection and execution of system commands.
    """

    def __init__(self):
        """Initialize system command manager."""
        self._builtins = {'cd', 'clear'}

    def is_system_command(self, user_input: str) -> bool:
        """
        Check if the input starts with a system command or builtin.
        
        Args:
            user_input: The raw user input string.
            
        Returns:
            True if it looks like a system command.
        """
        if not user_input or not user_input.strip():
            return False
            
        try:
            # Use shlex to handle quotes correctly
            parts = shlex.split(user_input)
            if not parts:
                return False
                
            cmd = parts[0]
            
            # Check builtins
            if cmd in self._builtins:
                return True
                
            # Check binaries in PATH
            # We strictly check if the executable exists
            if shutil.which(cmd) is not None:
                return True
                
            return False
            
        except ValueError:
            # Malformed input (unclosed quotes etc)
            return False

    def execute(self, user_input: str) -> bool:
        """
        Execute the system command.
        
        Args:
            user_input: The command string to execute.
            
        Returns:
            True if command was executed (even if it failed with exit code != 0).
        """
        try:
            parts = shlex.split(user_input)
            cmd = parts[0]
            args = parts[1:]

            if cmd == 'cd':
                self._execute_cd(args)
            elif cmd == 'clear':
                os.system('clear')
            else:
                self._execute_external(user_input)
                
            return True
            
        except Exception as e:
            _print_formatted_message(f"Error executing system command '{user_input}': {e}", color=Color.RED)
            return False

    def _execute_cd(self, args: List[str]) -> None:
        """Handle cd command."""
        try:
            path = args[0] if args else os.path.expanduser("~")
            path = os.path.expanduser(path)
            
            # Store old PWD
            old_pwd = os.getcwd()
            
            # Change directory
            os.chdir(path)
            new_pwd = os.getcwd()
            
            # Update environment variables
            os.environ["OLDPWD"] = old_pwd
            os.environ["PWD"] = new_pwd
            
            # Print new directory for feedback
            _print_formatted_message(f"cwd: {new_pwd}", color=Color.BLUE, style=Color.BOLD)
        except FileNotFoundError:
            _print_formatted_message(f"cd: no such file or directory: {args[0] if args else ''}", color=Color.RED)
        except Exception as e:
            _print_formatted_message(f"cd: error: {e}", color=Color.RED)

    def _execute_external(self, user_input: str) -> None:
        """Execute external binary using system shell."""
        try:
            # Inject --color=auto for ls if not present
            stripped = user_input.strip()
            # Simple check to avoid parsing args again, assumes 'ls' is the command as detected by execute()
            if stripped == 'ls' or stripped.startswith('ls '):
                if '--color' not in stripped:
                    # Replace first occurrence of ls with ls --color=auto
                    user_input = 'ls --color=auto' + user_input[2:]

            # Run with shell=True to support env vars ($PATH), globs (*.py), pipes, etc.
            # Use user's SHELL or default to /bin/bash for consistency
            shell_exec = os.environ.get("SHELL", "/bin/bash")
            subprocess.run(user_input, shell=True, executable=shell_exec)
            
        except KeyboardInterrupt:
            # Allow Ctrl+C to stop the system command without killing the shell
            _print_formatted_message("\n^C", color=Color.YELLOW)
        except Exception as e:
            _print_formatted_message(f"Command error: {e}", color=Color.RED)
