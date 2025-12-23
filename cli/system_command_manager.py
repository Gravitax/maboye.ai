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
            
        cmd = None
        try:
            # Use shlex to handle quotes correctly
            parts = shlex.split(user_input)
            if parts:
                cmd = parts[0]
        except ValueError:
            # Malformed input (e.g. unclosed quotes). 
            # Fallback to simple split to check the first token.
            parts = user_input.split()
            if parts:
                cmd = parts[0]
        
        if not cmd:
            return False
            
        # Check builtins
        if cmd in self._builtins:
            return True
            
        # Check binaries in PATH
        if shutil.which(cmd) is not None:
            return True
            
        return False

    def execute(self, user_input: str) -> bool:
        """
        Execute the system command.
        
        Args:
            user_input: The command string to execute.
            
        Returns:
            True if command was executed (even if it failed with exit code != 0).
        """
        # specialized handling for builtins that need parsing
        try:
            parts = shlex.split(user_input)
            cmd = parts[0] if parts else ""
            args = parts[1:]
            
            if cmd == 'cd':
                self._execute_cd(args)
                return True
            elif cmd == 'clear':
                os.system('clear')
                return True
                
        except ValueError:
            # parsing failed, but it might be a complex shell command
            # let _execute_external handle it (it uses raw input)
            pass
        except Exception as e:
            _print_formatted_message(f"Error preparing command: {e}", color=Color.RED)
            return False

        # If not a handled builtin, pass raw input to shell
        self._execute_external(user_input)
        return True

    def _execute_cd(self, args: List[str]) -> None:
        """Handle cd command."""
        try:
            target_path = args[0] if args else os.path.expanduser("~")
            
            # Handle 'cd -'
            if target_path == "-":
                old_pwd = os.environ.get("OLDPWD")
                if not old_pwd:
                    _print_formatted_message("cd: OLDPWD not set", color=Color.RED)
                    return
                target_path = old_pwd
                # Print the directory we are switching to, standard 'cd -' behavior
                print(target_path)

            target_path = os.path.expanduser(target_path)
            
            # Store current PWD as the new OLDPWD before changing
            current_pwd = os.getcwd()
            
            # Change directory
            os.chdir(target_path)
            
            # Update environment variables
            os.environ["OLDPWD"] = current_pwd
            os.environ["PWD"] = os.getcwd()
            
        except FileNotFoundError:
            _print_formatted_message(f"cd: no such file or directory: {args[0] if args else ''}", color=Color.RED)
        except Exception as e:
            _print_formatted_message(f"cd: error: {e}", color=Color.RED)

    def _execute_external(self, user_input: str) -> None:
        """
        Execute external binary using system shell.
        
        Handles complex commands including pipes and redirects by passing
        the full string to the shell.
        """
        try:
            # Inject --color=auto for ls to restore colors (aliases are not loaded in non-interactive shell)
            # --color=auto is safe for pipes as it disables color if stdout is not a TTY
            stripped = user_input.strip()
            if (stripped == 'ls' or stripped.startswith('ls ')) and '--color' not in stripped:
                if stripped == 'ls':
                    user_input = 'ls --color=auto'
                else:
                    user_input = 'ls --color=auto ' + stripped[3:]

            # Use user's SHELL or default to /bin/bash for consistency
            shell_exec = os.environ.get("SHELL", "/bin/bash")
            
            # Run with shell=True to support env vars ($PATH), globs (*.py), pipes, etc.
            subprocess.run(user_input, shell=True, executable=shell_exec)
            
        except KeyboardInterrupt:
            # Allow Ctrl+C to stop the system command without killing the shell
            _print_formatted_message("\n^C", color=Color.YELLOW)
        except Exception as e:
            _print_formatted_message(f"Command error: {e}", color=Color.RED)
