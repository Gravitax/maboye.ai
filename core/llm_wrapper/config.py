"""
Configuration for LLM wrapper.

Provides configuration management for LLM instances.
"""

import os
from dataclasses import dataclass, field


def get_env_str(key: str, default: str) -> str:
    """Get string environment variable."""
    return os.getenv(key, default)


def get_env_float(key: str, default: float) -> float:
    """Get float environment variable."""
    value = os.getenv(key)
    return float(value) if value else default


def get_env_int(key: str, default: int) -> int:
    """Get integer environment variable."""
    value = os.getenv(key)
    return int(value) if value else default


@dataclass
class LLMWrapperConfig:
    """Configuration for LLM wrapper."""

    base_url: str = field(default_factory=lambda: get_env_str("LLM_BASE_URL", "http://127.0.0.1:8000"))
    model: str = field(default_factory=lambda: get_env_str("LLM_MODEL", "gpt-4"))
    temperature: float = field(default_factory=lambda: get_env_float("LLM_TEMPERATURE", 0.7))
    max_tokens: int = field(default_factory=lambda: get_env_int("LLM_MAX_TOKENS", 1000))
    timeout: int = field(default_factory=lambda: get_env_int("LLM_TIMEOUT", 30))

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
