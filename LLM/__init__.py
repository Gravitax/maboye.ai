"""
LLM wrapper package

Provides abstraction layer for LLM API interactions.
"""

from LLM.config import LLMConfig
from LLM.llm import LLM, LLMError, LLMConnectionError, LLMAPIError
from LLM.types import (
    Message,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    ChatCompletionChoice,
    CompletionChoice,
    Usage,
    Model,
    ModelsResponse
)

__all__ = [
    # Classes
    "LLM",
    # Configuration
    "LLMConfig",
    # Exceptions
    "LLMError",
    "LLMConnectionError",
    "LLMAPIError",
    # Types
    "Message",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "CompletionRequest",
    "CompletionResponse",
    "ChatCompletionChoice",
    "CompletionChoice",
    "Usage",
    "Model",
    "ModelsResponse",
]

__version__ = "1.0.0"
