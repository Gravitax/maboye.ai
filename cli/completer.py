"""
CLI Completer

Handles context-aware tab completion for the CLI.
- Command completion (starting with /)
- Path completion (files and directories)
- System command completion (binaries in PATH, builtins)
- History completion (general text)
"""

import readline
import glob
import os
import shlex
from typing import Callable, Dict, List, Optional, Any

class CLICompleter:
    """
    Handles completion logic for readline.
    
    Architecture:
    - Main entry point: complete(text, state)
    - Strategy dispatcher: _get_matches(text)
    - Strategies:
      - _get_command_matches: For inputs starting with '/'
      - _get_path_matches: For file system paths
      - _get_system_command_matches: For executables in PATH and builtins
      - _get_history_matches: For other inputs
    """

    def __init__(self, command_provider: Callable[[], Dict], system_command_manager: Any):
        """
        Initialize completer.

        Args:
            command_provider: Function that returns dictionary of available commands.
            system_command_manager: Instance of SystemCommandManager for checking builtins.
        """
        self._command_provider = command_provider
        self._system_command_manager = system_command_manager
        self._matches: List[str] = []

    def complete(self, text: str, state: int) -> Optional[str]:
        """
        Readline completer entry point.
        """
        if state == 0:
            self._matches = self._get_matches(text)
        
        if state < len(self._matches):
            return self._matches[state]
        return None

    def _get_matches(self, text: str) -> List[str]:
        """
        Dispatch logic to determine which completion strategy to use.
        """
        buffer = readline.get_line_buffer()
        
        try:
            parts = shlex.split(buffer)
        except ValueError: 
            return []
        
        is_command_token = False
        if (len(parts) == 1 and parts[0].startswith("/")) or (not parts and text.startswith("/")):
            is_command_token = True
            
        if is_command_token:
            return self._get_command_matches(text)
            
        if text: 
            path_matches = self._get_path_matches(text)
            system_matches = self._get_system_command_matches(text)
            history_matches = self._get_history_matches(text)
            return sorted(list(set(path_matches + system_matches + history_matches)))
        elif not text and not is_command_token: 
            path_matches = self._get_path_matches("")
            system_matches = self._get_system_command_matches("")
            return sorted(list(set(path_matches + system_matches)))
            
        return []

    def _get_command_matches(self, text: str) -> List[str]:
        commands = list(self._command_provider().keys())
        if not text:
            return [f"/{cmd} " for cmd in sorted(commands)]
        prefix = text[1:] if text.startswith("/") else text
        matches = [f"/{cmd} " for cmd in commands if cmd.startswith(prefix)]
        return sorted(matches)

    def _get_path_matches(self, text: str) -> List[str]:
        try:
            expanded_text = os.path.expanduser(text)
            glob_pattern = f"{expanded_text}*"
            matches = glob.glob(glob_pattern)
            results = []
            for match in matches:
                if os.path.isdir(match):
                    match += "/"
                results.append(match)
            return results
        except Exception:
            return []

    def _get_system_command_matches(self, text: str) -> List[str]:
        matches = set()
        
        # Builtins
        for builtin in self._system_command_manager._builtins:
            if builtin.startswith(text):
                matches.add(builtin)
        
        # PATH binaries
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        for p_dir in path_dirs:
            if not os.path.isdir(p_dir): continue
            try:
                # Basic optimization: only list if directory is readable
                for entry in os.listdir(p_dir):
                    if entry.startswith(text):
                        matches.add(entry)
            except OSError:
                continue
                
        return sorted(list(matches))

    def _get_history_matches(self, text: str) -> List[str]:
        matches = set()
        history_len = readline.get_current_history_length()
        for i in range(1, history_len + 1):
            item = readline.get_history_item(i)
            if item and item.startswith(text) and item != text:
                matches.add(item)
        return sorted(list(matches))