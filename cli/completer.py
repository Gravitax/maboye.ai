"""
CLI Completer

Handles context-aware tab completion for the CLI.
- Command completion (starting with /)
- Path completion (files and directories)
- System command completion (binaries in PATH, builtins)
"""

import glob
import os
import shlex
from typing import Callable, Dict, List, Optional, Any

class CLICompleter:
    """
    Handles completion logic.
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
        self._path_cache: Optional[List[str]] = None

    def get_matches(self, document_text: str, word_before_cursor: str) -> List[str]:
        """
        Dispatch logic to determine which completion strategy to use.
        
        Args:
            document_text: The full text of the line buffer.
            word_before_cursor: The specific word being completed.
        """
        try:
            parts = shlex.split(document_text)
        except ValueError:
            # If shlex fails (e.g. unclosed quote), fall back to simple split
            parts = document_text.split()
            if not parts:
                parts = []
        
        is_command_token = False
        # Check if we are completing a command (first token starts with /)
        if (len(parts) <= 1 and document_text.lstrip().startswith("/")):
            is_command_token = True
            
        if is_command_token:
            return self._get_command_matches(word_before_cursor)
            
        if word_before_cursor: 
            path_matches = self._get_path_matches(word_before_cursor)
            system_matches = self._get_system_command_matches(word_before_cursor)
            return sorted(list(set(path_matches + system_matches)))
        elif not word_before_cursor and not is_command_token: 
            path_matches = self._get_path_matches("")
            system_matches = self._get_system_command_matches("")
            return sorted(list(set(path_matches + system_matches)))
            
        return []

    def _get_command_matches(self, text: str) -> List[str]:
        commands = list(self._command_provider().keys())
        if not text:
            return [f"/{cmd}" for cmd in sorted(commands)]
        prefix = text[1:] if text.startswith("/") else text
        matches = [f"/{cmd}" for cmd in commands if cmd.startswith(prefix)]
        return sorted(matches)

    def _get_path_matches(self, text: str) -> List[str]:
        try:
            expanded_text = os.path.expanduser(text)
            glob_pattern = f"{expanded_text}*"
            matches = glob.glob(glob_pattern)
            results = []
            for match in matches:
                if os.path.isdir(match):
                    match += os.sep
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
        
        # Initialize cache if needed
        if self._path_cache is None:
            self._path_cache = []
            path_dirs = os.environ.get('PATH', '').split(os.pathsep)
            for p_dir in path_dirs:
                if not os.path.isdir(p_dir): continue
                try:
                    for entry in os.listdir(p_dir):
                        self._path_cache.append(entry)
                except OSError:
                    continue
        
        # Filter from cache
        for entry in self._path_cache:
            if entry.startswith(text):
                matches.add(entry)
                
        return sorted(list(matches))