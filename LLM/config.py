"""
Configuration for LLM wrapper

Provides configuration management for LLM instances.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for LLM wrapper"""

    base_url: str = "http://127.0.0.1:8000"
    api_key: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30
    max_retries: int = 1
    retry_delay: float = 1.0

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
