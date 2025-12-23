"""
Tool result formatting utilities

Converts raw tool execution results into human-readable messages for
agent execution history.
"""

from typing import Any, Dict


def format_tool_result(tool_name: str, result_data: Any, arguments: Dict[str, Any]) -> str:
    """
    Format tool result as readable message for execution history.

    Args:
        tool_name: Name of executed tool
        result_data: Data returned by tool
        arguments: Arguments passed to tool

    Returns:
        Formatted message in natural language
    """
    if isinstance(result_data, str):
        return result_data

    # Tool-specific formatting
    if tool_name == "read_file":
        return _format_read_file(result_data, arguments)
    elif tool_name == "write_file":
        return _format_write_file(arguments)
    elif tool_name == "edit_file":
        return _format_edit_file(arguments)
    elif tool_name in ["list_files", "list_directory"]:
        return _format_list_files(result_data, arguments)
    elif tool_name in ["execute_command", "bash"]:
        return _format_bash_output(result_data, arguments)
    elif tool_name in ["code_search", "grep"]:
        return _format_search_results(result_data, arguments)
    elif tool_name in ["glob_files", "find_file"]:
        return _format_find_file(result_data, arguments)
    elif tool_name == "git_status":
        return _format_git_status(result_data)
    elif tool_name == "git_diff":
        return _format_git_diff(result_data)

    # Generic formatting for structured data
    return _format_generic_result(result_data)


def _format_read_file(result_data: Any, arguments: Dict[str, Any]) -> str:
    """Format read_file tool result"""
    file_path = arguments.get('file_path', 'unknown')
    if isinstance(result_data, str):
        lines = len(result_data.split('\n'))
        chars = len(result_data)
        return f"Successfully read file '{file_path}' ({lines} lines, {chars} characters)"
    return f"Successfully read file '{file_path}'"


def _format_write_file(arguments: Dict[str, Any]) -> str:
    """Format write_file tool result"""
    file_path = arguments.get('file_path', 'unknown')
    return f"Successfully wrote to file '{file_path}'"


def _format_edit_file(arguments: Dict[str, Any]) -> str:
    """Format edit_file tool result"""
    file_path = arguments.get('file_path', 'unknown')
    return f"Successfully edited file '{file_path}'"


def _format_list_files(result_data: Any, arguments: Dict[str, Any]) -> str:
    """Format list_files/list_directory tool result"""
    if isinstance(result_data, list):
        count = len(result_data)
        directory = arguments.get('directory', arguments.get('path', '.'))
        files_count = sum(1 for item in result_data if isinstance(item, dict) and item.get('is_file', False))
        dirs_count = sum(1 for item in result_data if isinstance(item, dict) and item.get('is_dir', False))
        return f"Listed directory '{directory}': found {files_count} files and {dirs_count} directories ({count} total items)"
    return f"Listed directory '{arguments.get('directory', '.')}'"


def _format_bash_output(result_data: Any, arguments: Dict[str, Any]) -> str:
    """Format execute_command/bash tool result with stdout/stderr"""
    command = arguments.get('command', 'unknown')
    if isinstance(result_data, dict):
        # BashTool returns 'return_code' (with underscore)
        returncode = result_data.get('return_code', result_data.get('returncode', 0))
        stdout = result_data.get('stdout', '').strip()
        stderr = result_data.get('stderr', '').strip()

        # Build message with stdout/stderr
        parts = []
        if returncode == 0:
            parts.append(f"Command executed successfully: {command}")
        else:
            parts.append(f"Command failed (exit code {returncode}): {command}")

        # Always include stdout if exists
        if stdout:
            parts.append(f"\n--- STDOUT ---\n{stdout}")

        # Always include stderr if exists (especially for Python errors)
        if stderr:
            parts.append(f"\n--- STDERR ---\n{stderr}")

        # Mention if no output at all
        if not stdout and not stderr:
            parts.append("\n(No output)")

        return ''.join(parts)
    return f"Executed command: {command}"


def _format_search_results(result_data: Any, arguments: Dict[str, Any]) -> str:
    """Format code_search/grep tool result"""
    pattern = arguments.get('pattern', 'unknown')
    if isinstance(result_data, dict):
        matches = result_data.get('matches_found', 0)
        files = len(result_data.get('files_with_matches', []))
        return f"Found {matches} matches in {files} files for pattern '{pattern}'"
    return f"Searched for pattern '{pattern}'"


def _format_find_file(result_data: Any, arguments: Dict[str, Any]) -> str:
    """Format glob_files/find_file tool result with file paths"""
    # find_file uses 'name_pattern', glob_files uses 'pattern'
    pattern = arguments.get('name_pattern', arguments.get('pattern', 'unknown'))
    if isinstance(result_data, list):
        count = len(result_data)
        if count == 0:
            return f"No files found matching pattern '{pattern}'"
        elif count <= 10:
            # Complete list for small results
            files_list = '\n'.join(f"  - {path}" for path in result_data)
            return f"Found {count} file(s) matching pattern '{pattern}':\n{files_list}"
        else:
            # Sample for large results
            files_sample = '\n'.join(f"  - {path}" for path in result_data[:10])
            return f"Found {count} file(s) matching pattern '{pattern}' (showing first 10):\n{files_sample}\n  ... and {count - 10} more"
    return f"Searched for files matching '{pattern}'"


def _format_git_status(result_data: Any) -> str:
    """Format git_status tool result"""
    if isinstance(result_data, str):
        lines = len([l for l in result_data.split('\n') if l.strip()])
        return f"Git status retrieved ({lines} lines of output)"
    return "Git status retrieved"


def _format_git_diff(result_data: Any) -> str:
    """Format git_diff tool result"""
    if isinstance(result_data, str):
        lines = len(result_data.split('\n'))
        return f"Git diff retrieved ({lines} lines)"
    return "Git diff retrieved"


def _format_generic_result(result_data: Any) -> str:
    """Format generic structured result (dict/list)"""
    if isinstance(result_data, dict):
        # Try to extract meaningful message
        if 'message' in result_data:
            return result_data['message']
        if 'output' in result_data:
            return str(result_data['output'])
        # Compact summary
        keys = list(result_data.keys())[:3]
        return f"Operation completed (returned: {', '.join(keys)}{'...' if len(result_data) > 3 else ''})"

    if isinstance(result_data, list):
        return f"Operation completed (returned {len(result_data)} items)"

    # Fallback: simple conversion
    return str(result_data)
