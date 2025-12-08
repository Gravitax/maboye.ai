"""
Configuration for agent system

Provides configuration management for Agent instances.
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Configuration for Agent"""

    name: str = "BaseAgent"
    enable_logging: bool = True
    max_input_length: int = 10000
    max_output_length: int = 10000
    system_prompt: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.max_input_length <= 0:
            raise ValueError("Max input length must be positive")
        if self.max_output_length <= 0:
            raise ValueError("Max output length must be positive")
