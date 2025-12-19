"""
LLM Wrapper Module - Simplified

Provides abstraction layer for LLM API calls with clean architecture.
"""

from .llm_wrapper import LLMWrapper
from .config import LLMWrapperConfig
from .errors import LLMWrapperError

# Export simplified types
from .types import (
    Message,
    ChatRequest,
    ChatResponse,
    Choice,
    Usage,
    Model,
    ModelsResponse,
    EmbeddingRequest,
    EmbeddingResponse
)

__all__ = [
    # Main class
    'LLMWrapper',
    # Configuration
    'LLMWrapperConfig',
    # Errors
    'LLMWrapperError',
    # Types
    'Message',
    'ChatRequest',
    'ChatResponse',
    'Choice',
    'Usage',
    'Model',
    'ModelsResponse',
    'EmbeddingRequest',
    'EmbeddingResponse'
]

__version__ = "3.0.0"
