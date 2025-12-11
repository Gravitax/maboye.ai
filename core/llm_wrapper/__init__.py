"""
LLM wrapper package.

Provides abstraction layer for LLM API interactions.
"""

from .config import LLMWrapperConfig
from .llm_wrapper import LLMWrapper, LLMWrapperError
from .llm_types import (
    LLMMessage,
    LLMChatRequest,
    LLMChatResponse,
    LLMChatChoice,
    LLMUsage,
    LLMModel,
    LLMModelsResponse
)

__all__ = [
    "LLMWrapper",
    "LLMWrapperConfig",
    "LLMWrapperError",
    "LLMMessage",
    "LLMChatRequest",
    "LLMChatResponse",
    "LLMChatChoice",
    "LLMUsage",
    "LLMModel",
    "LLMModelsResponse",
]

__version__ = "2.0.0"
