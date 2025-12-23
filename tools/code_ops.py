"""
Code operations for agent system.
"""

import ast
import sys
from pathlib import Path


class CodeError(Exception):
    """Base exception for code operations"""
    pass


def check_syntax(file_path: str) -> str:
    """
    Checks the syntax of a Python file without executing it.

    Args:
        file_path: Path to the python file.

    Returns:
        "Syntax Valid." or syntax error description with line number.

    Raises:
        FileNotFoundError: File does not exist
        CodeError: Failed to read or check file
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()

        # AST Parsing
        ast.parse(source)
        return "Syntax Valid."
    except SyntaxError as e:
        # Syntax errors are expected results, not tool failures
        return f"Syntax Error in {file_path} at line {e.lineno}:\n{e.msg}\n{e.text}"
    except PermissionError:
        raise CodeError(f"Permission denied: {file_path}")
    except Exception as e:
        raise CodeError(f"Failed to check syntax: {str(e)}")

