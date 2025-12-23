"""
JSON command parser

Parses LLM output into structured tool commands with error recovery.
"""

import json
import re
from typing import Optional, Dict, Any
from core.logger import logger


def parse_tool_command(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON command from LLM output.

    Handles:
    - Markdown code blocks
    - Single quotes instead of double quotes
    - Memory format detection (invalid output)
    - Nested JSON structures

    Args:
        content: Raw LLM output string

    Returns:
        Parsed command dict or None if parsing fails
    """
    try:
        # Clean markdown blocks and whitespace
        cleaned = _clean_markdown(content)

        # Detect memory format (invalid pattern)
        if _is_memory_format(cleaned):
            logger.warning("AGENT", "Detected memory format instead of JSON command", "Forcing retry")
            return None

        # Extract JSON boundaries
        json_str = _extract_json_string(cleaned)
        if not json_str:
            return None

        # Parse with error recovery
        data = _parse_with_recovery(json_str)
        if not data:
            return None

        # Normalize structure
        return _normalize_command_structure(data)

    except Exception:
        return None


def _clean_markdown(content: str) -> str:
    """
    Remove markdown code blocks and trim whitespace.

    Args:
        content: Raw content string

    Returns:
        Cleaned content
    """
    cleaned = re.sub(r'^```(json)?|```$', '', content.strip(), flags=re.MULTILINE)
    return cleaned.strip()


def _is_memory_format(content: str) -> bool:
    """
    Detect if content is memory format instead of JSON command.

    Memory format pattern: "{'arg': 'value'}\noutput: ...\nsuccess: True"

    Args:
        content: Cleaned content string

    Returns:
        True if memory format detected
    """
    return bool(re.match(r"^\s*\{.*?\}\s*output:", content, re.DOTALL))


def _extract_json_string(content: str) -> Optional[str]:
    """
    Extract JSON string from content by finding braces.

    Args:
        content: Content to search

    Returns:
        JSON string or None
    """
    start = content.find('{')
    end = content.rfind('}')

    if start != -1 and end != -1:
        return content[start:end+1]

    return None


def _parse_with_recovery(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON with automatic error recovery.

    Attempts:
    1. Direct parsing
    2. Fix single quotes and retry

    Args:
        json_str: JSON string to parse

    Returns:
        Parsed dict or None
    """
    # Try direct parsing first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Try fixing single quotes
    try:
        fixed_json = _fix_single_quotes(json_str)
        return json.loads(fixed_json)
    except json.JSONDecodeError:
        pass

    return None


def _fix_single_quotes(json_str: str) -> str:
    """
    Convert single quotes to double quotes for JSON compliance.

    Conservative strategy to avoid breaking apostrophes in strings.

    Args:
        json_str: JSON string with possible single quotes

    Returns:
        Fixed JSON string
    """
    return json_str.replace("'", '"')


def _normalize_command_structure(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize parsed data to standard command structure.

    Handles:
    - Standard format: {"tool_name": "...", "arguments": {...}}
    - OpenAI function format
    - Plain JSON data (for tasks agent)

    Args:
        data: Parsed JSON data

    Returns:
        Normalized command dict or None
    """
    # Standard format
    if "tool_name" in data:
        return data

    # OpenAI function format
    if "function" in data and "name" in data["function"]:
        func_args = data["function"]["arguments"]
        if isinstance(func_args, str):
            func_args = json.loads(func_args)

        return {
            "tool_name": data["function"]["name"],
            "arguments": func_args
        }

    # Plain JSON (e.g., tasks agent plan)
    # Let caller decide if valid
    return data
