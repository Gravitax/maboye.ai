"""
Code operations for agent system.
"""

import ast
import sys

def check_syntax(file_path: str) -> str:
    """
    Checks the syntax of a Python file without executing it.
    
    Args:
        file_path: Path to the python file.
        
    Returns:
        "Syntax Valid." or error message with line number.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # AST Parsing
        ast.parse(source)
        return "Syntax Valid."
    except SyntaxError as e:
        return f"Syntax Error in {file_path} at line {e.lineno}:\n{e.msg}\n{e.text}"
    except Exception as e:
        return f"Error checking syntax: {str(e)}"

