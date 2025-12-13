"""
Utility functions for the Backend Mock API.
"""
import os

def get_env_variable(key: str, default: str) -> str:
    """Get environment variable with default value."""
    return os.getenv(key, default)